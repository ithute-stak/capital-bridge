from uuid import UUID
import unittest
from api.erp_tenant_policy import TenantSpecification, DeploymentMode
from api.erp_tenant_admin import register_pending_tenant

TENANT = UUID("11111111-1111-4111-8111-111111111111")
OPERATOR = UUID("22222222-2222-4222-8222-222222222222")

class FakeConn:
    def __init__(self, row):
        self.row=row
        self.calls=[]
    def execute(self, sql, params):
        self.calls.append((sql,params))
        return self
    def fetchone(self):
        return self.row

class TenantAdminTests(unittest.TestCase):
    def test_pending_registration_only(self):
        conn=FakeConn((TENANT,"pending"))
        spec=TenantSpecification(TENANT,"Lesotho PostBank","lesotho-postbank",DeploymentMode.DEDICATED_STACK)
        result=register_pending_tenant(conn,spec=spec,operator_id=OPERATOR)
        self.assertEqual(result.status,"pending")
        self.assertEqual(conn.calls[0][1],(OPERATOR,TENANT,"Lesotho PostBank","lesotho-postbank","dedicated_stack"))

    def test_invalid_identity_fails_before_sql(self):
        conn=FakeConn(None)
        spec=TenantSpecification(TENANT,"LPB","postbank",DeploymentMode.DEDICATED_STACK)
        with self.assertRaises(ValueError):
            register_pending_tenant(conn,spec=spec,operator_id=UUID(int=0))
        self.assertFalse(conn.calls)

    def test_unconfirmed_registration_fails_closed(self):
        spec=TenantSpecification(TENANT,"LPB","postbank",DeploymentMode.DEDICATED_STACK)
        for row in (None,(TENANT,"active"),(UUID(int=3),"pending")):
            with self.subTest(row=row), self.assertRaises(RuntimeError):
                register_pending_tenant(FakeConn(row),spec=spec,operator_id=OPERATOR)

if __name__=="__main__":
    unittest.main()
