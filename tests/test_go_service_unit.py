import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
class GoServiceUnitTests(unittest.TestCase):
 def test_systemd_unit_has_required_isolation(self):
  unit=(ROOT/"deploy/systemd/capitalbridge-go-ingress.service").read_text()
  for token in ("User=capitalbridge-ingress","EnvironmentFile=/etc/capitalbridge/go-ingress.env",
                "NoNewPrivileges=true","ProtectSystem=strict","PrivateTmp=true","Restart=on-failure",
                "ExecStart=/opt/capitalbridge/bin/capitalbridge-go-ingress"):
   self.assertIn(token,unit)
  self.assertNotIn("User=root",unit)
 def test_configuration_is_not_committed(self):
  directory=ROOT/"deploy/systemd"
  self.assertFalse((directory/"go-ingress.env").exists())
if __name__=="__main__":unittest.main()
