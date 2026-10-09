BEGIN;
ALTER TABLE cb.finance_outbox
 ADD COLUMN next_attempt_at timestamptz NOT NULL DEFAULT now(),
 ADD COLUMN claimed_until timestamptz,
 ADD COLUMN claim_token uuid,
 ADD COLUMN last_error text;
CREATE INDEX finance_outbox_due ON cb.finance_outbox(next_attempt_at,created_at)
 WHERE delivered_at IS NULL;
COMMIT;
