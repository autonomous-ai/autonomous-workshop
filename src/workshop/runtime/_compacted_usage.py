"""Bounded-memory validator for an oversized native compaction.

The outer record must have type=compacted. All JSON syntax and duplicate keys
are checked; bodies are discarded. This record carries no top-level token_count
event in the frozen native protocol. Other oversized kinds remain rejected.
"""
import codecs
import json
import re

CHUNK_BYTES = 64 * 1024
MAX_DEPTH = 64
MAX_OBJECT_KEYS = 4096
MAX_KEY_BYTES = 4096
MAX_ATOM_BYTES = 128
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

    def peek(self):
        if self.position < len(self.buffer):
            return self.buffer[self.position]
        if self.complete or self.remaining == 0:
            return None
        self.buffer = self.stream.readline(min(CHUNK_BYTES, self.remaining))
        self.position = 0
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

    def value(self, depth, capture=False):
        if depth > MAX_DEPTH:
            raise InvalidRecord('compacted nesting exceeds safe bounds')
        self.space()
        ch = self.peek()
        if ch is None:
            raise IncompleteRecord()
        if ch == 34:
            return self.string(MAX_ATOM_BYTES if capture else None)
        if ch == 123:
            return self.object(depth + 1)
        if ch == 91:
            self.array(depth + 1)
            return None
        self.atom()
        return None

    def object(self, depth=0, root=False):
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
            value = self.value(depth, capture=root and key == 'type')
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
        if not reader.complete:
            if reader.record_type != 'compacted':
                raise InvalidRecord('native usage record exceeds safe bounds')
            return None, reader.remaining
        if kind != 'compacted':
            raise InvalidRecord('native usage record exceeds safe bounds')
        return {'type': 'compacted'}, reader.remaining
    except IncompleteRecord:
        if not reader.complete and reader.record_type == 'compacted':
            return None, reader.remaining
        raise InvalidRecord('incomplete compacted JSON') from None
    except UnicodeError:
        raise InvalidRecord('malformed compacted UTF-8') from None
