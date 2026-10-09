"use strict";
/*
 * Finance read integration contract.
 * The deployment's authenticated host MUST provide a function that makes an
 * authorized, same-origin API request. Tokens are never entered, logged or
 * stored by this demonstration page.
 */
(function () {
  const status = document.getElementById("live-status");
  const message = document.getElementById("live-message");
  const panel = document.getElementById("live-result");
  const button = document.getElementById("load-finance");
  const dateInput = document.getElementById("report-as-of");
  if (!button || !status || !message || !panel || !dateInput) return;
  dateInput.value = new Date().toLocaleDateString("en-CA");
  const money = minor => new Intl.NumberFormat("en-LS", {
    style: "currency", currency: "LSL"
  }).format(minor / 100);
  const companySelect = document.getElementById("finance-company");
  let selectionVersion = 0;
  let requestVersion = 0;
  let approvedCompany = null;
  function clearLiveResult() {
    panel.classList.add("hidden");
    ["live-revenue", "live-expenses", "live-result-total"].forEach(id => {
      document.getElementById(id).textContent = "—";
    });
  }
  async function loadCompanies() {
    const provider = window.capitalBridgeFinanceSession;
    if (!companySelect || !provider || typeof provider.listCompanies !== "function") return;
    try {
      const companies = await provider.listCompanies();
      companySelect.replaceChildren(new Option("Select company", ""));
      companies.forEach(company => companySelect.add(new Option(company.name, company.id)));
      status.textContent = "Sign-in verified";
    } catch (_) {
      companySelect.replaceChildren(new Option("Sign in required", ""));
      status.textContent = "Not connected";
    }
  }
  if (companySelect) companySelect.addEventListener("change", async () => {
    const provider = window.capitalBridgeFinanceSession;
    const version = ++selectionVersion;
    ++requestVersion;
    approvedCompany = null;
    clearLiveResult();
    if (!companySelect.value || !provider) return;
    try {
      const requestedCompany = companySelect.value;
      await provider.selectCompany(requestedCompany);
      if (version !== selectionVersion || companySelect.value !== requestedCompany) return;
      approvedCompany = requestedCompany;
      status.textContent = "Company selected";
    } catch (_) {
      if (version !== selectionVersion) return;
      status.textContent = "Access denied";
      companySelect.value = "";
      approvedCompany = null;
    }
  });
  loadCompanies();
  button.addEventListener("click", async () => {
    // This callback is deliberately absent until a secure authenticated host
    // provides session management and an approved company selection.
    const provider = window.capitalBridgeFinanceSession;
    if (!provider || typeof provider.getFinanceOverview !== "function") {
      status.textContent = "Not connected";
      message.textContent = "A secure company sign-in and same-origin session integration are not configured. Demonstration data remains separate.";
      panel.classList.add("hidden");
      return;
    }
    if (!approvedCompany || !/^\\d{4}-\\d{2}-\\d{2}$/.test(dateInput.value)) {
      status.textContent = "Select an authorised company and date";
      clearLiveResult();
      return;
    }
    const version = ++requestVersion;
    const reportCompany = approvedCompany;
    clearLiveResult();
    button.disabled = true;
    status.textContent = "Loading";
    try {
      const data = await provider.getFinanceOverview({ asOf: dateInput.value });
      if (version !== requestVersion || reportCompany !== approvedCompany) return;
      if (!data || data.company_id !== reportCompany || data.currency !== "LSL" ||
          !["revenue_minor", "expense_minor", "operating_result_minor"].every(
             key => Number.isSafeInteger(data[key]))) {
        throw new Error("Unexpected finance response");
      }
      document.getElementById("live-revenue").textContent = money(data.revenue_minor);
      document.getElementById("live-expenses").textContent = money(data.expense_minor);
      document.getElementById("live-result-total").textContent = money(data.operating_result_minor);
      status.textContent = "Connected";
      message.textContent = "Authenticated posted-journal summary as of " + String(data.as_of || dateInput.value) + ". Separate from sample cards.";
      panel.classList.remove("hidden");
    } catch (error) {
      if (version !== requestVersion) return;
      status.textContent = "Unavailable";
      message.textContent = "Financial data could not be loaded. Please verify your session, permissions and connectivity.";
      panel.classList.add("hidden");
    } finally {
      button.disabled = false;
    }
  });
})();
