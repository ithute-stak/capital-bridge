import unittest
from api.quotation_approval_policy import validate_transition, QuotationTransitionError

DEFAULT = dict(line_count=1, subtotal_minor=12500, calculated_minor=12500,
               issued_on_present=True, valid_until_present=True)

class QuotationApprovalPolicyTests(unittest.TestCase):
    def test_director_approves_reconciled_draft(self):
        result = validate_transition("draft","approved","director",**DEFAULT)
        self.assertEqual(result.new_status,"approved")

    def test_finance_clerk_cannot_approve(self):
        with self.assertRaises(QuotationTransitionError):
            validate_transition("draft","approved","finance_clerk",**DEFAULT)

    def test_auditor_cannot_dispatch_or_accept(self):
        for start,end in (("approved","sent"),("sent","accepted")):
            with self.subTest(start=start,end=end),self.assertRaises(QuotationTransitionError):
                validate_transition(start,end,"auditor",**DEFAULT)

    def test_cannot_skip_approval_or_modify_terminal_state(self):
        for start,end in (("draft","sent"),("draft","accepted"),("accepted","approved")):
            with self.subTest(start=start,end=end),self.assertRaises(QuotationTransitionError):
                validate_transition(start,end,"director",**DEFAULT)

    def test_reject_unreconciled_or_incomplete_quotations(self):
        cases=[dict(calculated_minor=12000),dict(line_count=0),dict(issued_on_present=False),
               dict(valid_until_present=False)]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(QuotationTransitionError):
                validate_transition("draft","approved","director",**{**DEFAULT,**change})

if __name__ == "__main__":
    unittest.main()
