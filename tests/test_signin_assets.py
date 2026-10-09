import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
class SignInTests(unittest.TestCase):
 def test_accessible_login_page(self):
  html=(ROOT/"web/signin.html").read_text()
  self.assertIn('role="status"',html)
  self.assertIn('id="sign-in" type="button" disabled',html)
  self.assertIn("signin.css",html)
  self.assertIn("signin.js",html)
  self.assertNotIn('type="password"',html)
 def test_no_client_side_enablement(self):
  js=(ROOT/"web/signin.js").read_text()
  self.assertIn("button.disabled = true",js)
  self.assertNotIn("localStorage.setItem",js)
 def test_clear_demo_separation(self):
  html=(ROOT/"web/signin.html").read_text()
  self.assertIn("demonstration workspace",html)
if __name__=="__main__":unittest.main()
