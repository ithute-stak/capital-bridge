import unittest
from uuid import UUID
from api.erp_tenant_policy import (
    DeploymentMode, TenantSpecification, TenantStatus,
    require_tenant_active, validate_transition,
)


ID = UUID("11111111-1111-4111-8111-111111111111")


class TenantPolicyTests(unittest.TestCase):
    def test_valid_spec(self):
        spec = TenantSpecification(ID, "Lesotho PostBank", "lesotho-postbank", DeploymentMode.DEDICATED_STACK)
        self.assertEqual(spec.company_id, ID)

    def test_reject_invalid_slug_and_zero_id(self):
        for slug in ("LPB", "bad space", "-tenant", "ab", "a" * 64):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                TenantSpecification(ID, "Company", slug, DeploymentMode.SHARED_DATABASE)
        with self.assertRaises(ValueError):
            TenantSpecification(UUID(int=0), "Company", "company-one", DeploymentMode.SHARED_DATABASE)

    def test_reject_empty_legal_name_and_mode(self):
        with self.assertRaises(ValueError):
            TenantSpecification(ID, " ", "company-one", DeploymentMode.SHARED_DATABASE)
        with self.assertRaises(ValueError):
            TenantSpecification(ID, "Company", "company-one", "shared_database")

    def test_allowed_transitions(self):
        for source, target in (
            (TenantStatus.PENDING, TenantStatus.ACTIVE),
            (TenantStatus.PENDING, TenantStatus.RETIRED),
            (TenantStatus.ACTIVE, TenantStatus.SUSPENDED),
            (TenantStatus.SUSPENDED, TenantStatus.ACTIVE),
            (TenantStatus.SUSPENDED, TenantStatus.RETIRED),
        ):
            with self.subTest(source=source, target=target):
                validate_transition(source, target)

    def test_denied_transitions(self):
        for source in TenantStatus:
            for target in TenantStatus:
                if (source, target) not in (
                    (TenantStatus.PENDING, TenantStatus.ACTIVE),
                    (TenantStatus.PENDING, TenantStatus.RETIRED),
                    (TenantStatus.ACTIVE, TenantStatus.SUSPENDED),
                    (TenantStatus.SUSPENDED, TenantStatus.ACTIVE),
                    (TenantStatus.SUSPENDED, TenantStatus.RETIRED),
                ):
                    with self.subTest(source=source, target=target), self.assertRaises(ValueError):
                        validate_transition(source, target)
        with self.assertRaises(ValueError):
            validate_transition("active", TenantStatus.SUSPENDED)

    def test_status_gate(self):
        require_tenant_active(TenantStatus.ACTIVE)
        for status in (TenantStatus.PENDING, TenantStatus.SUSPENDED, TenantStatus.RETIRED):
            with self.subTest(status=status), self.assertRaises(PermissionError):
                require_tenant_active(status)


if __name__ == "__main__":
    unittest.main()
