import unittest
from pydantic import ValidationError
from api.consultation_schema import ConsultationEnquiry

VALID = {
 "name": "Maseru Consulting",
 "email": "team@example.com",
 "service": "Management & Business Consultancy",
 "message": "Please contact us about consultancy.",
 "consent": True,
}

class ConsultationSchemaTests(unittest.TestCase):
 def test_valid_enquiry(self):
  enquiry=ConsultationEnquiry.model_validate(VALID)
  self.assertEqual(enquiry.email,"team@example.com")
  self.assertTrue(enquiry.consent)

 def test_consent_is_mandatory(self):
  for value in (False, None):
   with self.subTest(value=value), self.assertRaises(ValidationError):
    ConsultationEnquiry.model_validate({**VALID,"consent":value})

 def test_unknown_service_and_unknown_fields_rejected(self):
  for payload in ({**VALID,"service":"Fraud services"},{**VALID,"company_id":"not-authorized"}):
   with self.assertRaises(ValidationError):
    ConsultationEnquiry.model_validate(payload)

 def test_oversized_or_short_content_rejected(self):
  for message in ("short","A"*2001,"normal text\x00hidden"):
   with self.assertRaises(ValidationError):
    ConsultationEnquiry.model_validate({**VALID,"message":message})

 def test_invalid_email_rejected(self):
  with self.assertRaises(ValidationError):
   ConsultationEnquiry.model_validate({**VALID,"email":"not-an-email"})
