BEGIN;
CREATE TABLE cb.realtime_notifications (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 event_type text NOT NULL CHECK(event_type IN ('invoice.issued','payment.posted','payment.allocated','bank.matched')),
 aggregate_id uuid NOT NULL,
 received_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(company_id,id)
);
CREATE INDEX realtime_notifications_tenant_cursor ON cb.realtime_notifications(company_id,received_at,id);
ALTER TABLE cb.realtime_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.realtime_notifications FORCE ROW LEVEL SECURITY;
CREATE POLICY realtime_notifications_tenant ON cb.realtime_notifications
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
COMMIT;
