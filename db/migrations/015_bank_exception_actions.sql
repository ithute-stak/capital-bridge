BEGIN;
CREATE TABLE cb.bank_exception_actions (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 company_id uuid NOT NULL,
 exception_id uuid NOT NULL,
 actor_user_id uuid NOT NULL,
 from_status text NOT NULL,
 to_status text NOT NULL CHECK(to_status IN ('investigating','resolved')),
 action_note text NOT NULL CHECK(length(btrim(action_note)) BETWEEN 8 AND 2000),
 performed_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(company_id,exception_id) REFERENCES cb.bank_import_exceptions(company_id,id)
);
ALTER TABLE cb.bank_import_exceptions ADD CONSTRAINT bank_exception_company_identity UNIQUE(company_id,id);
ALTER TABLE cb.bank_exception_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.bank_exception_actions FORCE ROW LEVEL SECURITY;
CREATE POLICY bank_exception_actions_tenant ON cb.bank_exception_actions
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND actor_user_id=cb.authorized_user()
 AND cb.has_company_access(company_id));
COMMIT;
