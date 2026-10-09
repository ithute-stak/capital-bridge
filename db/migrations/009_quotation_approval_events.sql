BEGIN;
CREATE TABLE cb.quotation_status_events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 company_id uuid NOT NULL,
 quotation_id uuid NOT NULL,
 actor_user_id uuid NOT NULL,
 from_status text NOT NULL,
 to_status text NOT NULL,
 changed_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(company_id,quotation_id) REFERENCES cb.quotations(company_id,id)
);
CREATE INDEX quotation_events_company_quotation ON cb.quotation_status_events(company_id,quotation_id,changed_at);
ALTER TABLE cb.quotation_status_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.quotation_status_events FORCE ROW LEVEL SECURITY;
CREATE POLICY quotation_events_read ON cb.quotation_status_events FOR SELECT
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY quotation_events_insert ON cb.quotation_status_events FOR INSERT
 WITH CHECK(company_id=cb.authorized_company() AND actor_user_id=cb.authorized_user()
 AND cb.has_company_access(company_id));
COMMIT;
