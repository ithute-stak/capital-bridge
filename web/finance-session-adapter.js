"use strict";
/*
 * Bridge to a trusted OIDC login host.
 * The host must expose window.capitalBridgeIdentity.getAccessToken() which
 * returns a short-lived access token in memory, never in localStorage.
 * This adapter must be deployed same-origin with the API.
 */
(function () {
  const identity = window.capitalBridgeIdentity;
  if (!identity || typeof identity.getAccessToken !== "function") return;

  let selectedCompany = null;
  const base = "/api/v1";
  async function authorizedGet(path) {
    const token = await identity.getAccessToken();
    if (typeof token !== "string" || !token) throw Error("Authentication required");
    const response = await fetch(base + path, {
      headers: {Authorization: "Bearer " + token, Accept: "application/json"},
      credentials: "same-origin",
      cache: "no-store",
      redirect: "error"
    });
    if (!response.ok) throw Error("Financial report access denied or unavailable");
    return response.json();
  }

  window.capitalBridgeFinanceSession = Object.freeze({
    async listCompanies() {
      const response = await authorizedGet("/me/companies");
      if (!response || !Array.isArray(response.companies)) throw Error("Invalid company response");
      return response.companies;
    },
    async selectCompany(companyId) {
      const companies = await this.listCompanies();
      if (!companies.some(company => company.id === companyId))
        throw Error("Company not available to this user");
      selectedCompany = companyId;
    },
    async getFinanceOverview({asOf}) {
      if (!selectedCompany) throw Error("Select an authorised company first");
      if (!/^\d{4}-\d{2}-\d{2}$/.test(asOf)) throw Error("Invalid report date");
      const result = await authorizedGet("/companies/" + encodeURIComponent(selectedCompany) +
        "/finance/overview?as_of=" + encodeURIComponent(asOf));
      if (result.company_id !== selectedCompany) throw Error("Company mismatch");
      return result;
    }
  });
})();
