import unittest
from api.invoice_posting_policy import validate_invoice_posting,InvoicePostingError

VALID=dict(actor_role="accountant",invoice_status="draft",period_open=True,
 date_in_period=True,line_count=2,subtotal_minor=100000,
 calculated_subtotal_minor=100000,tax_minor=15000,
 receivable_account_active=True,revenue_account_active=True,
 tax_account_active=True)
class InvoicePostingPolicyTests(unittest.TestCase):
 def test_balanced_accounting_journal_amounts(self):
  result=validate_invoice_posting(**VALID)
  self.assertEqual(result.receivable_debit_minor,115000)
  self.assertEqual(result.revenue_credit_minor+result.tax_credit_minor,115000)
 def test_reject_unapproved_or_closed_or_unbalanced_posting(self):
  for override in (
   dict(actor_role="finance_clerk"),dict(actor_role="auditor"),
   dict(invoice_status="issued"),dict(period_open=False),
   dict(date_in_period=False),dict(line_count=0),
   dict(calculated_subtotal_minor=99999),dict(receivable_account_active=False),
   dict(revenue_account_active=False),dict(tax_account_active=False),
   dict(tax_minor=-1),dict(tax_minor=9223372036854775807),
  ):
   with self.subTest(override=override),self.assertRaises(InvoicePostingError):
    validate_invoice_posting(**{**VALID,**override})
 def test_no_tax_requires_no_tax_account(self):
  result=validate_invoice_posting(**{**VALID,"tax_minor":0,"tax_account_active":False})
  self.assertEqual(result.amount_minor,100000)
if __name__=="__main__":unittest.main()
