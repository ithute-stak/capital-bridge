BEGIN;
-- Reliable notification *intent* is stored in the same transaction as the
-- consultation. Delivery is performed by a separately authorised worker.
CREATE TABLE cb.consultation_notification_outbox (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 enquiry_id uuid NOT NULL,
 event_type text NOT NULL CHECK(event_type IN ('consultation.received','consultation.status_changed')),
 created_at timestamptz NOT NULL DEFAULT now(),
 sent_at timestamptz,
 attempts integer NOT NULL DEFAULT 0,
 FOREIGN KEY(enquiry_id,company_id) REFERENCES cb.consultation_enquiries(id,company_id)
);
CREATE UNIQUE INDEX consultation_outbox_event_once
 ON cb.consultation_notification_outbox(company_id,enquiry_id,event_type)
 WHERE event_type='consultation.received';
REVOKE ALL ON cb.consultation_notification_outbox FROM PUBLIC;
ALTER TABLE cb.consultation_notification_outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.consultation_notification_outbox FORCE ROW LEVEL SECURITY;
CREATE FUNCTION cb.enqueue_consultation_received()
 RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=cb,pg_temp AS $$
BEGIN
 INSERT INTO cb.consultation_notification_outbox(company_id,enquiry_id,event_type)
 VALUES(NEW.company_id,NEW.id,'consultation.received');
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION cb.enqueue_consultation_received() FROM PUBLIC;
CREATE TRIGGER consultation_received_outbox AFTER INSERT ON cb.consultation_enquiries
 FOR EACH ROW EXECUTE FUNCTION cb.enqueue_consultation_received();
COMMIT;
