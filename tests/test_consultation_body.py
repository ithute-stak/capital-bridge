import asyncio
import unittest

from api.consultation_body import IntakeBodyError, read_bounded_intake_body
from api.consultation_abuse_guard import MAX_BODY_BYTES


async def chunks(*items):
    for item in items:
        yield item


class BoundedIntakeBodyTests(unittest.TestCase):
    def read(self, *items, declared_length=None):
        return asyncio.run(read_bounded_intake_body(
            chunks(*items), declared_length=declared_length
        ))

    def test_valid_split_payload(self):
        self.assertEqual(self.read(b'{"hello":', b'true}', declared_length=14),
                         b'{"hello":true}')

    def test_large_actual_body_rejected_despite_small_declared_length(self):
        with self.assertRaises(IntakeBodyError):
            self.read(b"x" * MAX_BODY_BYTES, b"x", declared_length=1)

    def test_over_limit_declared_size_rejected(self):
        with self.assertRaises(IntakeBodyError):
            self.read(b"x", declared_length=MAX_BODY_BYTES + 1)

    def test_empty_body_and_mismatch_rejected(self):
        for items, declared in (((), 0), ((b"abc",), 2)):
            with self.subTest(items=items), self.assertRaises(IntakeBodyError):
                self.read(*items, declared_length=declared)

    def test_exact_boundary_accepted(self):
        self.assertEqual(len(self.read(b"x" * MAX_BODY_BYTES)), MAX_BODY_BYTES)
