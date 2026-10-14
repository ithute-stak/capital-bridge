"""Isolated interoperability smoke tests for Java, C++ and Rust prototypes.

These are subprocess contract checks, not production financial posting routes.
Compilation happens in CI. All values are nonnegative exact minor units.
"""
import hashlib
import subprocess
import unittest

def run(*args, data=None):
    return subprocess.run(args, input=data, text=True, capture_output=True, timeout=15)

class SpecializedServiceContracts(unittest.TestCase):
    def test_java_approval_boundary(self):
        self.assertEqual(run("java", "-cp", "/tmp/cb-java", "ApprovalPolicy", "10000", "10000").stdout.strip(), "DUAL_REVIEW")
        self.assertEqual(run("java", "-cp", "/tmp/cb-java", "ApprovalPolicy", "9999", "10000").stdout.strip(), "STANDARD_REVIEW")
        self.assertNotEqual(run("java", "-cp", "/tmp/cb-java", "ApprovalPolicy", "-1", "10000").returncode, 0)

    def test_cpp_minor_unit_allocation(self):
        for due, paid, expected in [(10000,12500,"10000,2500"), (10000,2000,"2000,0"), (0,0,"0,0")]:
            with self.subTest(due=due,paid=paid):
                result=run("/tmp/cb-payment",str(due),str(paid))
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(result.stdout.strip(),expected)
        self.assertNotEqual(run("/tmp/cb-payment","-1","200").returncode,0)

    def test_rust_digest_exact_bytes(self):
        for value in ("abc", "tenant-a:invoice-1", "tenant-b:invoice-1"):
            with self.subTest(value=value):
                result=run("/tmp/cb-audit",data=value)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(result.stdout.strip(),hashlib.sha256(value.encode()).hexdigest())
        self.assertNotEqual(hashlib.sha256(b"tenant-a:invoice-1").digest(),hashlib.sha256(b"tenant-b:invoice-1").digest())

if __name__=="__main__":
    unittest.main()
