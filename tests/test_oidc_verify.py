import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from api.oidc_verify import verify_id_token

class FakeJWK:
    def __init__(self,key): self.key=key

class OidcTokenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        cls.issuer="https://idp.example.test"
        cls.client_id="capitalbridge-public"
        cls.nonce="expected-random-nonce"

    def token(self, **overrides):
        now=datetime.now(timezone.utc)
        claims={"iss":self.issuer,"sub":"user-123","aud":self.client_id,
                "iat":now,"exp":now+timedelta(minutes=5),"nonce":self.nonce}
        claims.update(overrides)
        return jwt.encode(claims,self.key,algorithm="RS256",headers={"kid":"test-key"})

    def verify(self,token,**changes):
        params={"issuer":self.issuer,"client_id":self.client_id,
                "jwks_url":self.issuer+"/keys","expected_nonce":self.nonce}
        params.update(changes)
        with patch("api.oidc_verify.PyJWKClient") as client:
            client.return_value.get_signing_key_from_jwt.return_value=FakeJWK(self.key.public_key())
            return verify_id_token(token,**params)

    def test_valid_token(self):
        actual=self.verify(self.token())
        self.assertEqual(actual.subject,"user-123")
        self.assertEqual(actual.issuer,self.issuer)

    def test_nonce_mismatch(self):
        with self.assertRaises(ValueError):
            self.verify(self.token(nonce="other"))

    def test_wrong_issuer_audience_and_expired(self):
        for changed in ({"iss":"https://fake.example.test"},
                        {"aud":"other-client"},
                        {"exp":datetime.now(timezone.utc)-timedelta(minutes=3)}):
            with self.assertRaises(ValueError):
                self.verify(self.token(**changed))

    def test_missing_critical_claims(self):
        for key in ("nonce","sub","exp","iat"):
            now=datetime.now(timezone.utc)
            claims={"iss":self.issuer,"sub":"user-123","aud":self.client_id,
                    "iat":now,"exp":now+timedelta(minutes=5),"nonce":self.nonce}
            del claims[key]
            with self.assertRaises(ValueError):
                self.verify(jwt.encode(claims,self.key,algorithm="RS256",headers={"kid":"test-key"}))

    def test_wrong_key_rejected(self):
        other=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        with self.assertRaises(ValueError):
            self.verify(jwt.encode({"iss":self.issuer,"sub":"abc","aud":self.client_id,
                "iat":datetime.now(timezone.utc),
                "exp":datetime.now(timezone.utc)+timedelta(minutes=5),
                "nonce":self.nonce},other,algorithm="RS256",headers={"kid":"test-key"}))

    def test_untrusted_jwks_origin_rejected(self):
        with self.assertRaises(ValueError):
            self.verify(self.token(),jwks_url="https://attacker.example.test/keys")

    def test_multiple_audiences_require_azp(self):
        with self.assertRaises(ValueError):
            self.verify(self.token(aud=[self.client_id,"second"]))
        valid=self.verify(self.token(aud=[self.client_id,"second"],azp=self.client_id))
        self.assertEqual(valid.subject,"user-123")

if __name__=="__main__":
    unittest.main()
