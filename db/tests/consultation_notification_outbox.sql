BEGIN;
INSERT INTO cb.companies(id,legal_name) VALUES
 ('ef000000-0000-4000-8000-000000000001','Outbox Enquiry Test');
INSERT INTO cb.consultation_enquiries(id,company_id,contact_name,contact_email,
 service,message,consent_at) VALUES
 ('ef000000-0000-4000-8000-000000000002',
  'ef000000-0000-4000-8000-000000000001',
  'Outbox Test','outbox@example.com','Information Technology',
  'Please contact us about our development requirements.',now());
DO $$
BEGIN
 IF (SELECT count(*) FROM cb.consultation_notification_outbox
     WHERE enquiry_id='ef000000-0000-4000-8000-000000000002'
     AND event_type='consultation.received') <> 1 THEN
  RAISE EXCEPTION 'Consultation insert did not atomically enqueue notification';
 END IF;
END $$;
ROLLBACK;
