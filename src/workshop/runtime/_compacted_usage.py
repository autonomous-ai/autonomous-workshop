"""Bounded-memory validator for an oversized native compaction.

The outer record must be a compaction or visual custom-tool result. All JSON syntax and duplicate keys
are checked; bodies are discarded. Only the bounded latest_token_usage_record
inside its payload can survive, for corroboration rather than new consumption.
Other oversized kinds remain rejected.
"""
import codecs
import json
import re

CHUNK_BYTES = 64 * 1024
MAX_DEPTH = 64
MAX_OBJECT_KEYS = 4096
MAX_KEY_BYTES = 4096
MAX_ATOM_BYTES = 128
MAX_USAGE_METADATA_BYTES = 16 * 1024
STRING_RUN = re.compile(rb'[^"\\\x00-\x1f]+')
NUMBER = re.compile(rb'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?')
SPACE = b' \t\r\n'
DELIMITERS = SPACE + b',]}'


class InvalidRecord(ValueError):
    pass


class IncompleteRecord(Exception):
    pass


class Reader:
    def __init__(self, prefix, stream, remaining):
        self.buffer = prefix
        self.position = 0
        self.stream = stream
        self.remaining = remaining
        self.complete = prefix.endswith(b'\n')
        self.record_type = None
        self.payload_type = None
        self.latest_usage_present = False
        self.latest_usage = None
        self.captured_metadata = None
        self.capture_start = 0

    def capture_consumed(self):
        if self.captured_metadata is None:
            return
        length = self.position - self.capture_start
        if len(self.captured_metadata) + length > MAX_USAGE_METADATA_BYTES:
            raise InvalidRecord('compacted usage metadata exceeds safe bounds')
        self.captured_metadata.extend(self.buffer[self.capture_start:self.position])
        self.capture_start = self.position

    def peek(self):
        if self.position < len(self.buffer):
            return self.buffer[self.position]
        if self.complete or self.remaining == 0:
            return None
        self.capture_consumed()
        self.buffer = self.stream.readline(min(CHUNK_BYTES, self.remaining))
        self.position = 0
        self.capture_start = 0
        if not self.buffer:
            raise InvalidRecord('native usage file shrank during read')
        self.remaining -= len(self.buffer)
        self.complete = self.buffer.endswith(b'\n')
        return self.buffer[0]

    def take(self):
        result = self.peek()
        if result is None:
            raise IncompleteRecord()
        self.position += 1
        return result

    def expect(self, wanted):
        if self.take() != wanted:
            raise InvalidRecord('malformed compacted record')

    def space(self):
        while self.peek() is not None and self.peek() in SPACE:
            self.position += 1

    def string(self, capture_limit=None):
        self.expect(34)
        captured = bytearray(b'"') if capture_limit is not None else None
        decoder = codecs.getincrementaldecoder('utf-8')('strict')

        def capture(raw):
            if captured is not None:
                if len(captured) + len(raw) + 1 > capture_limit:
                    raise InvalidRecord('compacted metadata exceeds safe bounds')
                captured.extend(raw)

        while True:
            ch = self.peek()
            if ch is None:
                raise IncompleteRecord()
            if ch == 34:
                self.position += 1
                decoder.decode(b'', final=True)
                if captured is not None:
                    captured.append(34)
                    return json.loads(captured)
                return None
            if ch == 92:
                self.position += 1
                # A raw UTF-8 character may not be split by a JSON escape.
                decoder.decode(b'', final=True)
                decoder = codecs.getincrementaldecoder('utf-8')('strict')
                escaped = self.take()
                raw = bytes((92, escaped))
                if escaped == 117:
                    digits = bytes(self.take() for _ in range(4))
                    if any(c not in b'0123456789abcdefABCDEF' for c in digits):
                        raise InvalidRecord('malformed compacted Unicode escape')
                    raw += digits
                elif escaped not in b'"\\/bfnrt':
                    raise InvalidRecord('malformed compacted string escape')
                capture(raw)
                continue
            if ch < 32:
                raise InvalidRecord('unescaped control in compacted string')
            run = STRING_RUN.match(self.buffer, self.position)
            assert run is not None
            raw = run.group()
            self.position = run.end()
            # The decoder validates raw non-ASCII sequences across read chunks.
            # Its temporary output is bounded by the prefix/chunk size.
            decoder.decode(raw, final=False)
            capture(raw)

    def atom(self):
        raw = bytearray()
        while self.peek() is not None and self.peek() not in DELIMITERS:
            if len(raw) >= MAX_ATOM_BYTES:
                raise InvalidRecord('compacted atom exceeds safe bounds')
            raw.append(self.take())
        value = bytes(raw)
        if value not in (b'true', b'false', b'null') and NUMBER.fullmatch(value) is None:
            if not self.complete and self.peek() is None:
                raise IncompleteRecord()
            raise InvalidRecord('malformed compacted atom')

    def value(self, depth, capture=False, payload=False):
        if depth > MAX_DEPTH:
            raise InvalidRecord('compacted nesting exceeds safe bounds')
        self.space()
        ch = self.peek()
        if ch is None:
            raise IncompleteRecord()
        if ch == 34:
            return self.string(MAX_ATOM_BYTES if capture else None)
        if ch == 123:
            return self.object(depth + 1, payload=payload)
        if ch == 91:
            self.array(depth + 1)
            return None
        self.atom()
        return None

    def usage_metadata(self, depth):
        """Capture one small value while the normal parser validates every byte."""
        self.captured_metadata = bytearray()
        self.capture_start = self.position
        try:
            self.value(depth)
            self.capture_consumed()
            value = json.loads(self.captured_metadata)
        finally:
            self.captured_metadata = None
        if value is not None and not isinstance(value, dict):
            raise InvalidRecord('compacted usage metadata must be an object or null')
        return value

    def object(self, depth=0, root=False, payload=False):
        if depth > MAX_DEPTH:
            raise InvalidRecord('compacted nesting exceeds safe bounds')
        self.expect(123)
        keys = set()
        record_type = None
        self.space()
        if self.peek() == 125:
            self.position += 1
            return record_type
        while True:
            self.space()
            key = self.string(MAX_KEY_BYTES)
            if key in keys:
                raise InvalidRecord('duplicate native usage JSON key')
            keys.add(key)
            if len(keys) > MAX_OBJECT_KEYS:
                raise InvalidRecord('compacted object exceeds safe bounds')
            self.space()
            self.expect(58)
            if payload and key == 'latest_token_usage_record':
                self.latest_usage = self.usage_metadata(depth)
                self.latest_usage_present = True
                value = None
            else:
                value = self.value(
                    depth, capture=(root or payload) and key == 'type',
                    payload=root and key == 'payload',
                )
            if payload and key == 'type':
                self.payload_type = value
            if root and key == 'type':
                record_type = value
                self.record_type = value
            self.space()
            end = self.take()
            if end == 125:
                return record_type
            if end != 44:
                raise InvalidRecord('malformed compacted object')

    def array(self, depth):
        if depth > MAX_DEPTH:
            raise InvalidRecord('compacted nesting exceeds safe bounds')
        self.expect(91)
        self.space()
        if self.peek() == 93:
            self.position += 1
            return
        while True:
            self.value(depth)
            self.space()
            end = self.take()
            if end == 93:
                return
            if end != 44:
                raise InvalidRecord('malformed compacted array')


def consume_compacted_record(prefix, stream, remaining):
    """Return (minimal record or None for a partial append, unread snapshot bytes)."""
    reader = Reader(prefix, stream, remaining)
    try:
        reader.space()
        kind = reader.object(root=True)
        reader.space()
        if reader.peek() is not None:
            raise InvalidRecord('trailing compacted record data')
        supported = (
            kind == 'compacted'
            or (
                kind == 'response_item'
                and reader.payload_type == 'custom_tool_call_output'
            )
        )
        if not reader.complete:
            if not supported:
                raise InvalidRecord('native usage record exceeds safe bounds')
            return None, reader.remaining
        if not supported:
            raise InvalidRecord('native usage record exceeds safe bounds')
        result = {'type': kind}
        if kind == 'compacted' and reader.latest_usage_present:
            result['payload'] = {'latest_token_usage_record': reader.latest_usage}
        return result, reader.remaining
    except IncompleteRecord:
        supported = (
            reader.record_type == 'compacted'
            or (
                reader.record_type == 'response_item'
                and reader.payload_type == 'custom_tool_call_output'
            )
        )
        if not reader.complete and supported:
            return None, reader.remaining
        raise InvalidRecord('incomplete compacted JSON') from None
    except UnicodeError:
        raise InvalidRecord('malformed compacted UTF-8') from None
