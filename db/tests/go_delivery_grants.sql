-- Verify the Go replay role can only insert scoped receipts.
DO $$
BEGIN
 IF NOT has_schema_privilege('cb_go_delivery','cb','USAGE') THEN
  RAISE EXCEPTION 'Go role lacks schema access';
 END IF;
 IF NOT has_table_privilege('cb_go_delivery','cb.finance_event_receipts','INSERT') THEN
  RAISE EXCEPTION 'Go role lacks event receipt insert';
 END IF;
 IF has_table_privilege('cb_go_delivery','cb.finance_event_receipts','SELECT') OR
    has_table_privilege('cb_go_delivery','cb.finance_event_receipts','UPDATE') OR
    has_table_privilege('cb_go_delivery','cb.finance_event_receipts','DELETE') THEN
  RAISE EXCEPTION 'Go role has excessive receipt privileges';
 END IF;
 IF has_table_privilege('cb_go_delivery','cb.journals','SELECT') OR
    has_table_privilege('cb_go_delivery','cb.journals','INSERT') OR
    has_table_privilege('cb_go_delivery','cb.client_payments','SELECT') THEN
  RAISE EXCEPTION 'Go delivery role can access financial records';
 END IF;
END $$;
