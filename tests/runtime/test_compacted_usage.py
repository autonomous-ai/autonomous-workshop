import io
import json
import random
import unittest
from unittest import mock

import workshop.runtime._compacted_usage as parser


def consume(raw, prefix_bytes=32, tail=b''):
    stream = io.BytesIO(raw+tail)
    prefix = stream.readline(prefix_bytes)
    remaining = len(raw)+len(tail)-len(prefix)
    result, unread = parser.consume_compacted_record(prefix, stream, remaining)
    return result, unread, stream.read()


class CompactedRecordTest(unittest.TestCase):
    def record(self, **changes):
        return json.dumps({'type': 'compacted', 'message': 'summary',
                           'replacement_history': [{'nested': [None, True, False, -3.5e6, '\\quote"☃']}],
                           **changes}, ensure_ascii=False).encode()+b'\n'

    def test_drops_body_and_leaves_next_line_unread(self):
        tail = b'{"type":"event_msg"}\n'
        result, remaining, rest = consume(self.record(message='x'*(5*1024*1024)), tail=tail)
        self.assertEqual(result, {'type': 'compacted'})
        self.assertEqual(remaining, len(tail))
        self.assertEqual(rest, tail)

    def test_fragmentation_and_utf8_boundaries_preserve_result(self):
        raw = self.record(message='🦊\\"héllo'*9)
        for chunk in (1, 7, 64*1024):
            with mock.patch.object(parser, 'CHUNK_BYTES', chunk):
                for prefix in range(1, min(len(raw), 80)):
                    with self.subTest(chunk=chunk, prefix=prefix):
                        self.assertEqual(consume(raw, prefix)[0], {'type': 'compacted'})

    def test_complete_prefix_and_reordered_keys(self):
        raw = b'{"message":"x","replacement_history":[],"type":"compacted"}\r\n'
        for prefix in (1, len(raw), len(raw)+100):
            self.assertEqual(consume(raw, prefix)[0], {'type': 'compacted'})

    def test_partial_compaction_at_snapshot_end_is_ignored(self):
        for raw in (b'{"type":"compacted","message":"unfinished',
                    b'{"type":"compacted","replacement_history":[{"x":',
                    self.record()[:-1]):
            self.assertEqual(consume(raw)[0], None)

    def test_unknown_or_usage_records_are_not_skipped(self):
        for raw in (b'{"type":"event_msg","payload":{"type":"token_count"}}\n',
                    b'{"type":"response_item","payload":"unfinished',
                    b'{"message":"unfinished',
                    b'{"type":42}\n'):
            with self.subTest(raw=raw), self.assertRaises(parser.InvalidRecord):
                consume(raw)

    def test_duplicate_and_escaped_duplicate_keys_rejected(self):
        for raw in (b'{"type":"compacted","type":"compacted"}\n',
                    b'{"type":"compacted","replacement_history":{"a":1,"a":2}}\n',
                    b'{"type":"compacted","replacement_history":{"a":1,"\\u0061":2}}\n'):
            with self.subTest(raw=raw), self.assertRaisesRegex(parser.InvalidRecord, 'duplicate'):
                consume(raw)

    def test_malformed_json_rejected(self):
        values = [b'trueX', b'01', b'+1', b'1.', b'.1', b'NaN', b'Infinity', b'[1,]', b'{"x":1,}',
                  b'"bad\\q"', b'"bad\\u12XY"', b'"raw\x01"', b'"\xff"', b'"\xe2\\n"', b'"unfinished']
        for value in values:
            raw = b'{"type":"compacted","data":'+value+b'}\n'
            with self.subTest(value=value), self.assertRaises((parser.InvalidRecord, UnicodeError)):
                consume(raw)
        with self.assertRaises(parser.InvalidRecord):
            consume(self.record()[:-1]+b' garbage\n')

    def test_incomplete_complete_line_is_rejected(self):
        for raw in (b'{"type":"compacted","message":"unfinished\n',
                    b'{"type":"compacted","data":[1,2\n'):
            with self.assertRaises(parser.InvalidRecord):
                consume(raw)

    def test_declared_snapshot_shrink_is_rejected(self):
        prefix = b'{"type":"compacted","message":"'
        with self.assertRaisesRegex(parser.InvalidRecord, 'shrank'):
            parser.consume_compacted_record(prefix, io.BytesIO(), 100)

    def test_new_bounds_fail_closed(self):
        values = [b'['*(parser.MAX_DEPTH+1)+b'0'+b']'*(parser.MAX_DEPTH+1),
                  b'{'+b','.join(b'"k'+str(i).encode()+b'":0' for i in range(parser.MAX_OBJECT_KEYS+1))+b'}',
                  b'{"'+b'k'*(parser.MAX_KEY_BYTES+1)+b'":0}',
                  b'1'*(parser.MAX_ATOM_BYTES+1)]
        for value in values:
            with self.subTest(bytes=len(value)), self.assertRaisesRegex(parser.InvalidRecord, 'bounds'):
                consume(b'{"type":"compacted","data":'+value+b'}\n')

    def test_encoded_key_limit_includes_both_quotes(self):
        key = b'k'*(parser.MAX_KEY_BYTES-2)
        raw = b'{"type":"compacted","data":{"'+key+b'":0}}\n'
        self.assertEqual(consume(raw)[0], {'type': 'compacted'})
        with self.assertRaisesRegex(parser.InvalidRecord, 'bounds'):
            consume(b'{"type":"compacted","data":{"'+key+b'k":0}}\n')

    def test_seeded_json_corpus_matches_standard_decoder(self):
        rng = random.Random(682)
        def value(depth=0):
            if depth < 4:
                choice = rng.randrange(5)
                if choice == 0:
                    return [value(depth+1) for _ in range(rng.randrange(5))]
                if choice == 1:
                    return {'key'+str(i): value(depth+1) for i in range(rng.randrange(5))}
            return rng.choice([None, True, False, 0, -2, 1.75e-3, 'x\\"☃🦊\n\t\u0000'])
        for _ in range(200):
            document = {'type': 'compacted', 'replacement_history': value()}
            raw = json.dumps(document, ensure_ascii=rng.choice([True, False]), separators=(',', ':')).encode()+b'\n'
            self.assertEqual(json.loads(raw), document)
            self.assertEqual(consume(raw, rng.randrange(1, 40))[0], {'type': 'compacted'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
