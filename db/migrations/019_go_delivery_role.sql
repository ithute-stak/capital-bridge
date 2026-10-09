-- The migration owner provisions a dedicated login role WITHOUT credentials.
-- Operations must provision credentials separately with TLS requirements.
BEGIN;
DO $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='cb_go_delivery') THEN
   CREATE ROLE cb_go_delivery LOGIN NOINHERIT NOBYPASSRLS;
 END IF;
END $$;
REVOKE ALL ON SCHEMA cb FROM cb_go_delivery;
GRANT USAGE ON SCHEMA cb TO cb_go_delivery;
REVOKE ALL ON ALL TABLES IN SCHEMA cb FROM cb_go_delivery;
GRANT INSERT ON cb.finance_event_receipts TO cb_go_delivery;
DROP POLICY IF EXISTS go_delivery_receipt_insert ON cb.finance_event_receipts;
CREATE POLICY go_delivery_receipt_insert ON cb.finance_event_receipts
 FOR INSERT TO cb_go_delivery
 WITH CHECK(company_id=cb.authorized_company());
COMMIT;
