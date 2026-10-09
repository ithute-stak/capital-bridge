import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class DashboardSafetyTests(unittest.TestCase):
 def test_previous_company_result_cleared(self):
  js=(ROOT/"web/finance-connection.js").read_text()
  self.assertIn("++requestVersion",js)
  self.assertIn("clearLiveResult()",js)
  self.assertIn("reportCompany !== approvedCompany",js)
  self.assertIn("data.company_id !== reportCompany",js)
 def test_live_data_never_replaces_demonstration_metrics(self):
  js=(ROOT/"web/finance-connection.js").read_text()
  self.assertNotIn('document.getElementById("metric-invoiced")',js)
  self.assertIn('"live-revenue"',js)
 def test_live_panel_explicitly_marked_separate(self):
  html=(ROOT/"web/index.html").read_text()
  self.assertIn("EXAMPLE DATA",html)
  self.assertIn("Authenticated financial reporting",html)

if __name__=="__main__":unittest.main()
