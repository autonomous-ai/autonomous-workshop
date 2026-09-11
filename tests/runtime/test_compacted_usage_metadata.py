"""Oversized compaction keeps only bounded usage corroboration metadata."""

import copy
import io
import json
import unittest
from unittest import mock

import workshop.runtime._compacted_usage as parser


def consume(raw, prefix_bytes=32, tail=b''):
    stream = io.BytesIO(raw + tail)
    prefix = stream.readline(prefix_bytes)
    return parser.consume_compacted_record(
        prefix, stream, len(raw) + len(tail) - len(prefix)
    ), stream.read()


def metadata():
    counters = {
        'input_tokens': 100, 'cached_input_tokens': 50,
        'cache_write_input_tokens': 0, 'output_tokens': 10,
        'reasoning_output_tokens': 5, 'total_tokens': 110,
    }
    return {
        'thread_id': '01a0795e-0efd-76e2-91a9-aa019980ede0',
        'turn_id': '01a07960-0000-7000-8000-000000000001',
        'session_id': '01a0795e-0efd-76e2-91a9-aa019980ede0',
        'root_turn_id': '01a07960-0000-7000-8000-000000000001',
        'response_id': 'resp_compaction',
        'usage': dict(counters), 'turn_token_usage': dict(counters),
        'thread_token_usage': dict(counters),
    }


def record(value, *, body='discarded', reverse=False):
    payload = {'message': body, 'latest_token_usage_record': value,
               'replacement_history': [{'body': body}]}
    document = {'type': 'compacted', 'payload': payload, 'message': body}
    if reverse:
        document = dict(reversed(list(document.items())))
        payload = dict(reversed(list(payload.items())))
        document['payload'] = payload
    return json.dumps(document, ensure_ascii=False).encode() + b'\n'


class CompactedUsageMetadataTest(unittest.TestCase):
    def test_retains_only_metadata_and_leaves_next_record_unread(self):
        value = metadata()
        tail = b'{"type":"token_usage_record","payload":{}}\n'
        expected = {'type': 'compacted', 'payload': {'latest_token_usage_record': value}}
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                (result, remaining), rest = consume(
                    record(value, body='private-body' * 500000, reverse=reverse), tail=tail,
                )
                self.assertEqual(result, expected)
                self.assertEqual(remaining, len(tail))
                self.assertEqual(rest, tail)
                self.assertNotIn('private-body', json.dumps(result))

    def test_null_is_preserved_but_absent_and_embedded_fields_are_not_created(self):
        result, _ = consume(record(None))
        self.assertEqual(result[0], {'type': 'compacted', 'payload': {'latest_token_usage_record': None}})
        value = metadata()
        for document in (
            {'type': 'compacted'},
            {'type': 'compacted', 'payload': {'message': 'discarded'}},
            {'type': 'compacted', 'latest_token_usage_record': value},
            {'type': 'compacted', 'payload': {'nested': {'latest_token_usage_record': value}}},
            {'type': 'compacted', 'replacement_history': [
                {'type': 'compacted', 'payload': {'latest_token_usage_record': value}},
            ]},
        ):
            with self.subTest(document=document):
                result, _ = consume(json.dumps(document).encode() + b'\n')
                self.assertEqual(result[0], {'type': 'compacted'})

    def test_fragmentation_utf8_and_reordered_keys_preserve_metadata(self):
        value = metadata()
        # Parsing/size checks belong here; ID semantics belong to the ledger.
        value['response_id'] = 'resp_🦊\\"héllo'
        raw = record(value, reverse=True)
        expected = {'type': 'compacted', 'payload': {'latest_token_usage_record': value}}
        for chunk in (1, 7, 64 * 1024):
            with mock.patch.object(parser, 'CHUNK_BYTES', chunk):
                for prefix in (1, 17, 83, len(raw), len(raw) + 10):
                    with self.subTest(chunk=chunk, prefix=prefix):
                        result, _ = consume(raw, prefix)
                        self.assertEqual(result[0], expected)

    def test_invalid_metadata_type_is_rejected(self):
        for value in (True, False, 0, 'not metadata', [], [metadata()]):
            with self.subTest(value=value), self.assertRaisesRegex(parser.InvalidRecord, 'object or null'):
                consume(record(value))

    def test_metadata_byte_limit_is_enforced_across_read_boundaries(self):
        value = metadata()
        value['response_id'] = ''
        empty = json.dumps(value, separators=(',', ':')).encode()
        value['response_id'] = 'x' * (parser.MAX_USAGE_METADATA_BYTES - len(empty))
        exact = json.dumps(value, separators=(',', ':')).encode()
        self.assertEqual(len(exact), parser.MAX_USAGE_METADATA_BYTES)
        prefix = b'{"type":"compacted","payload":{"latest_token_usage_record":'
        for chunk in (7, 64 * 1024):
            with mock.patch.object(parser, 'CHUNK_BYTES', chunk):
                result, _ = consume(prefix + exact + b'}}\n')
                self.assertEqual(result[0]['payload']['latest_token_usage_record'], value)
                too_large = copy.deepcopy(value)
                too_large['response_id'] += 'x'
                with self.assertRaisesRegex(parser.InvalidRecord, 'usage metadata exceeds safe bounds'):
                    consume(prefix + json.dumps(too_large, separators=(',', ':')).encode() + b'}}\n')
                with self.assertRaisesRegex(parser.InvalidRecord, 'usage metadata exceeds safe bounds'):
                    consume(prefix + b' ' + exact + b'}}\n')

    def test_partial_metadata_and_partial_later_body_are_not_returned(self):
        raw = record(metadata())
        start = raw.index(b'"latest_token_usage_record"')
        for end in (start + 32, start + 180, len(raw) - 1):
            with self.subTest(end=end):
                result, _ = consume(raw[:end])
                self.assertIsNone(result[0])
        raw = b'{"type":"compacted","payload":{"latest_token_usage_record":' + json.dumps(metadata()).encode()
        raw += b',"message":"' + b'x' * (2 * parser.CHUNK_BYTES)
        self.assertIsNone(consume(raw)[0][0])

    def test_duplicate_metadata_keys_and_late_body_errors_are_still_rejected(self):
        value = json.dumps(metadata()).encode()
        beginning = b'{"type":"compacted","payload":{"latest_token_usage_record":'
        duplicate = value[:-1] + b',"response_id":"again"}'
        escaped_duplicate = value[:-1] + b',"response_\\u0069d":"again"}'
        invalid = (
            beginning + duplicate + b'}}\n',
            beginning + escaped_duplicate + b'}}\n',
            beginning + value + b',"latest_token_usage_record":null}}\n',
            beginning + value + b',"message":"' + b'x' * (2 * parser.CHUNK_BYTES)
            + b'","replacement_history":[{"duplicate":1,"duplicate":2}]}}\n',
            beginning + value + b',"message":"' + b'x' * (2 * parser.CHUNK_BYTES)
            + b'","replacement_history":[1,]}}\n',
            beginning + value + b'},"type":"compacted"}\n',
        )
        for raw in invalid:
            with self.subTest(tail=raw[-90:]), self.assertRaises(parser.InvalidRecord):
                consume(raw)

    def test_captured_metadata_does_not_authorize_an_oversized_noncompaction(self):
        raw = record(metadata()).replace(b'"type": "compacted"', b'"type": "event_msg"', 1)
        with self.assertRaisesRegex(parser.InvalidRecord, 'record exceeds safe bounds'):
            consume(raw)


if __name__ == '__main__':
    unittest.main()
