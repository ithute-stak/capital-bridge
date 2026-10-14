BEGIN;
INSERT INTO cb.companies(id,legal_name) VALUES
 ('e9000000-0000-4000-8000-000000000001','Notifier Authorized'),
 ('e9000000-0000-4000-8000-000000000002','Notifier Other');
INSERT INTO cb.consultation_intake_config(singleton,company_id)
 VALUES(true,'e9000000-0000-4000-8000-000000000001');
INSERT INTO cb.consultation_enquiries(id,company_id,contact_name,contact_email,service,message,consent_at)
 VALUES
 ('e9000000-0000-4000-8000-000000000011','e9000000-0000-4000-8000-000000000001','Authorized Customer','first@example.com','Information Technology','Consultation from first tenant.',now()),
 ('e9000000-0000-4000-8000-000000000012','e9000000-0000-4000-8000-000000000002','Other Customer','second@example.com','Information Technology','Consultation from another tenant.',now());
SET LOCAL ROLE cb_consultation_notifier;
DO $$
BEGIN
 IF (SELECT count(*) FROM cb.consultation_notification_outbox) <> 1 THEN
  RAISE EXCEPTION 'Notifier must only see events for approved tenant';
 END IF;
 IF (SELECT count(*) FROM cb.consultation_enquiries) <> 1 THEN
  RAISE EXCEPTION 'Notifier must only see enquiries for approved tenant';
 END IF;
 UPDATE cb.consultation_notification_outbox SET attempts=attempts+1
 WHERE enquiry_id='e9000000-0000-4000-8000-000000000011';
 IF (SELECT attempts FROM cb.consultation_notification_outbox
 WHERE enquiry_id='e9000000-0000-4000-8000-000000000011') <> 1 THEN
  RAISE EXCEPTION 'Notifier cannot acknowledge approved delivery';
 END IF;
END $$;
RESET ROLE;
ROLLBACK;
