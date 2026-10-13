BEGIN;
-- Public enquiries remain private until explicitly assigned to an approved company.
-- No PUBLIC INSERT privileges or unauthenticated HTTP ingestion in this phase.
CREATE TABLE cb.consultation_enquiries (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 contact_name varchar(120) NOT NULL CHECK (length(btrim(contact_name)) BETWEEN 2 AND 120),
 contact_email varchar(254) NOT NULL CHECK (length(btrim(contact_email)) BETWEEN 3 AND 254),
 contact_phone varchar(30),
 service text NOT NULL CHECK(service IN (
  'Management & Business Consultancy','Information Technology',
  'Engineering & Technical Advisory','Training & Capacity Building',
  'Business Support & Events','Immigration & Global Mobility')),
 message text NOT NULL CHECK(length(btrim(message)) BETWEEN 10 AND 2000),
 consent_at timestamptz NOT NULL,
 status text NOT NULL DEFAULT 'new'
  CHECK(status IN ('new','in_review','responded','closed')),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(company_id,id)
);
CREATE INDEX consultation_enquiries_queue_idx
 ON cb.consultation_enquiries(company_id,status,created_at DESC,id);
ALTER TABLE cb.consultation_enquiries ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.consultation_enquiries FORCE ROW LEVEL SECURITY;
CREATE POLICY consultation_enquiries_company_select
 ON cb.consultation_enquiries FOR SELECT
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY consultation_enquiries_company_insert
 ON cb.consultation_enquiries FOR INSERT
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY consultation_enquiries_company_update
 ON cb.consultation_enquiries FOR UPDATE
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
REVOKE ALL ON cb.consultation_enquiries FROM PUBLIC;
COMMIT;
