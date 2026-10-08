-- CapitalBridge ONE accounting schema (PostgreSQL 16+)
-- Run with a dedicated migration owner, not the application runtime role.
BEGIN;
CREATE SCHEMA IF NOT EXISTS cb;
CREATE TABLE cb.companies (
 id uuid PRIMARY KEY,
 legal_name text NOT NULL,
 base_currency char(3) NOT NULL DEFAULT 'LSL',
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE cb.memberships (
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 user_id uuid NOT NULL,
 role text NOT NULL CHECK(role IN ('director','accountant','finance_clerk','auditor')),
 PRIMARY KEY(company_id,user_id)
);
CREATE TABLE cb.accounts (
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 code text NOT NULL,
 name text NOT NULL,
 kind text NOT NULL CHECK(kind IN ('asset','liability','equity','revenue','expense')),
 active boolean NOT NULL DEFAULT true,
 PRIMARY KEY(company_id,code)
);
CREATE TABLE cb.periods (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 starts_on date NOT NULL,
 ends_on date NOT NULL,
 closed boolean NOT NULL DEFAULT false,
 CHECK(starts_on <= ends_on),
 UNIQUE(id,company_id)
);
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE cb.periods ADD CONSTRAINT no_company_period_overlap EXCLUDE USING gist (
 company_id WITH =,
 daterange(starts_on, ends_on, '[]') WITH &&
);
CREATE TABLE cb.journals (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 period_id uuid NOT NULL,
 posted_on date NOT NULL,
 reference text NOT NULL,
 description text NOT NULL,
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','posted')),
 reversal_of uuid NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(company_id,reference),
 UNIQUE(id,company_id),
 FOREIGN KEY(period_id,company_id) REFERENCES cb.periods(id,company_id),
 FOREIGN KEY(reversal_of,company_id) REFERENCES cb.journals(id,company_id),
 UNIQUE(company_id,reversal_of)
);
CREATE TABLE cb.journal_lines (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 company_id uuid NOT NULL,
 journal_id uuid NOT NULL,
 account_code text NOT NULL,
 division text NOT NULL,
 debit_minor bigint NOT NULL DEFAULT 0,
 credit_minor bigint NOT NULL DEFAULT 0,
 FOREIGN KEY(journal_id,company_id) REFERENCES cb.journals(id,company_id),
 FOREIGN KEY(company_id,account_code) REFERENCES cb.accounts(company_id,code),
 CHECK(debit_minor >= 0 AND credit_minor >= 0),
 CHECK ((debit_minor > 0 AND credit_minor=0) OR (credit_minor > 0 AND debit_minor=0))
);
CREATE INDEX journal_lines_lookup ON cb.journal_lines(company_id,journal_id);
CREATE INDEX journals_company_date ON cb.journals(company_id,posted_on);
-- Database-level rules catch direct SQL access and malformed postings.
CREATE FUNCTION cb.guard_journal() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE p record;
BEGIN
 IF TG_OP='DELETE' THEN
  IF OLD.status='posted' THEN RAISE EXCEPTION 'posted journal cannot be deleted'; END IF;
  RETURN OLD;
 END IF;
 IF TG_OP='UPDATE' THEN
  IF OLD.status='posted' THEN RAISE EXCEPTION 'posted journal cannot be modified'; END IF;
  IF NEW.company_id IS DISTINCT FROM OLD.company_id OR
     NEW.period_id IS DISTINCT FROM OLD.period_id OR
     NEW.posted_on IS DISTINCT FROM OLD.posted_on OR
     NEW.reference IS DISTINCT FROM OLD.reference OR
     NEW.reversal_of IS DISTINCT FROM OLD.reversal_of THEN
    RAISE EXCEPTION 'journal identity cannot be modified';
  END IF;
 END IF;
 SELECT starts_on,ends_on,closed INTO p FROM cb.periods
  WHERE id=NEW.period_id AND company_id=NEW.company_id FOR UPDATE;
 IF NOT FOUND OR p.closed OR NEW.posted_on NOT BETWEEN p.starts_on AND p.ends_on THEN
  RAISE EXCEPTION 'journal requires an open period containing posting date';
 END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER guard_journal BEFORE INSERT OR UPDATE OR DELETE ON cb.journals
 FOR EACH ROW EXECUTE FUNCTION cb.guard_journal();
CREATE FUNCTION cb.guard_line() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE j record;
BEGIN
 SELECT status INTO j FROM cb.journals
  WHERE id=COALESCE(NEW.journal_id,OLD.journal_id)
   AND company_id=COALESCE(NEW.company_id,OLD.company_id) FOR UPDATE;
 IF NOT FOUND OR j.status='posted' THEN
  RAISE EXCEPTION 'posted journal lines are immutable';
 END IF;
 IF TG_OP='UPDATE' AND (OLD.journal_id,OLD.company_id) IS DISTINCT FROM (NEW.journal_id,NEW.company_id) THEN
  RAISE EXCEPTION 'journal line cannot move to another journal';
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER guard_line BEFORE INSERT OR UPDATE OR DELETE ON cb.journal_lines
 FOR EACH ROW EXECUTE FUNCTION cb.guard_line();
CREATE FUNCTION cb.validate_posting() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE debits numeric; credits numeric; line_count integer;
BEGIN
 IF NEW.status='posted' AND OLD.status='draft' THEN
  SELECT COALESCE(SUM(debit_minor),0),COALESCE(SUM(credit_minor),0),COUNT(*)
   INTO debits,credits,line_count FROM cb.journal_lines
   WHERE company_id=NEW.company_id AND journal_id=NEW.id;
  IF line_count < 2 OR debits<>credits OR debits<=0 THEN
   RAISE EXCEPTION 'journal must have at least two balanced lines';
  END IF;
 END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER validate_posting BEFORE UPDATE OF status ON cb.journals
 FOR EACH ROW EXECUTE FUNCTION cb.validate_posting();

-- RLS is a second boundary, in addition to explicit application authorization.
-- Only a trusted backend may set these transaction-local values, using a DB role
-- that cannot be used directly by end users. Never expose arbitrary SQL execution.
CREATE FUNCTION cb.authorized_company() RETURNS uuid LANGUAGE sql STABLE AS $$
 SELECT NULLIF(current_setting('app.company_id',true),'')::uuid
$$;
CREATE FUNCTION cb.authorized_user() RETURNS uuid LANGUAGE sql STABLE AS $$
 SELECT NULLIF(current_setting('app.user_id',true),'')::uuid
$$;
CREATE FUNCTION cb.has_company_access(target uuid) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path=cb,pg_temp AS $$
 SELECT EXISTS(SELECT 1 FROM cb.memberships m
  WHERE m.company_id=target AND m.user_id=cb.authorized_user())
$$;
REVOKE ALL ON FUNCTION cb.has_company_access(uuid) FROM PUBLIC;
-- Membership reads are granted separately only to the trusted application role.
ALTER TABLE cb.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.journals ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.journal_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.companies FORCE ROW LEVEL SECURITY;
ALTER TABLE cb.accounts FORCE ROW LEVEL SECURITY;
ALTER TABLE cb.periods FORCE ROW LEVEL SECURITY;
ALTER TABLE cb.journals FORCE ROW LEVEL SECURITY;
ALTER TABLE cb.journal_lines FORCE ROW LEVEL SECURITY;
ALTER TABLE cb.memberships FORCE ROW LEVEL SECURITY;
CREATE POLICY company_visible ON cb.companies FOR SELECT USING(id=cb.authorized_company() AND cb.has_company_access(id));
CREATE POLICY membership_visible ON cb.memberships FOR SELECT USING(company_id=cb.authorized_company() AND user_id=cb.authorized_user());
CREATE POLICY account_scoped ON cb.accounts USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY period_scoped ON cb.periods USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY journal_scoped ON cb.journals USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY line_scoped ON cb.journal_lines USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
COMMIT;
