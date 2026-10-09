"use strict";
// Live-only client directory. The host identity bridge must come from trusted
// same-origin application bootstrap; no token or company ID is stored in browser storage.
(async () => {
  const companySelect = document.getElementById("company");
  const refresh = document.getElementById("refresh");
  const status = document.getElementById("status");
  const rows = document.getElementById("client-rows");
  const identity = window.capitalBridgeIdentity;
  let version = 0;
  let selected = "";
  let liveSubscription = null;
  let refreshQueued = false;
  function scheduleRefresh() {
    if (refreshQueued || !selected) return;
    refreshQueued = true;
    queueMicrotask(() => { refreshQueued = false; if (selected) load(); });
  }
  function stopLive() {
    if (liveSubscription) liveSubscription.stop();
    liveSubscription = null;
  }
  function startLive() {
    stopLive();
    if (!selected || !window.CapitalBridgeRealtime) return;
    // This route uses the server-managed session cookie, never the bearer token in a URL.
    liveSubscription = window.CapitalBridgeRealtime.subscribe({
      companyId: selected,
      onInvalidate: scheduleRefresh,
      onStatus: message => { if (message === "Connection unavailable") status.textContent = "Live updates unavailable. Use Refresh clients."; }
    });
  }

  function clear(message) {
    rows.replaceChildren();
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 5;
    td.textContent = message;
    tr.appendChild(td);
    rows.appendChild(tr);
  }
  async function get(path) {
    if (!identity || typeof identity.getAccessToken !== "function") throw Error("Ithute sign-in is not connected");
    const token = await identity.getAccessToken();
    if (typeof token !== "string" || !token) throw Error("Secure sign-in required");
    const res = await fetch("/api/v1" + path, {
      headers: {Authorization: "Bearer " + token, Accept: "application/json"},
      credentials: "same-origin", cache: "no-store", redirect: "error"
    });
    if (!res.ok) throw Error("Access denied or server unavailable");
    return res.json();
  }
  async function load() {
    const request = ++version;
    const company = selected;
    clear("Loading authorised clients…");
    status.textContent = "Loading clients…";
    try {
      if (!company) throw Error("Select an authorised company");
      const result = await get("/companies/" + encodeURIComponent(company) + "/clients?limit=100");
      if (request !== version || company !== selected) return;
      if (result.company_id !== company || !Array.isArray(result.clients)) throw Error("Company response mismatch");
      clear(result.clients.length ? "" : "No registered clients for this company.");
      if (result.clients.length) rows.replaceChildren();
      for (const client of result.clients) {
        const tr = document.createElement("tr");
        for (const key of ["code", "name", "email", "phone", "status"]) {
          const td = document.createElement("td");
          td.textContent = String(client[key] ?? "—");
          tr.appendChild(td);
        }
        rows.appendChild(tr);
      }
      status.textContent = result.clients.length + " client(s) loaded";
    } catch (err) {
      if (request !== version) return;
      clear("No client records displayed.");
      status.textContent = err.message || "Unable to load clients";
    }
  }
  companySelect.addEventListener("change", () => {
    selected = companySelect.value;
    version++;
    refresh.disabled = !selected;
    startLive();
    load();
  });
  window.addEventListener("pagehide", stopLive);
  window.addEventListener("pageshow", event => {
    if (selected && event.persisted) { startLive(); scheduleRefresh(); }
  });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && selected) scheduleRefresh();
  });
  refresh.addEventListener("click", load);
  try {
    const response = await get("/me/companies");
    if (!response || !Array.isArray(response.companies)) throw Error("Invalid company list");
    companySelect.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Select authorised company";
    companySelect.appendChild(placeholder);
    for (const company of response.companies) {
      if (typeof company.id !== "string" || typeof company.name !== "string") continue;
      const option = document.createElement("option");
      option.value = company.id;
      option.textContent = company.name;
      companySelect.appendChild(option);
    }
    companySelect.disabled = false;
    status.textContent = "Choose a company to view its live clients.";
  } catch (err) {
    companySelect.disabled = true;
    refresh.disabled = true;
    clear("Sign in through Ithute Auth to access client records.");
    status.textContent = "Secure client directory unavailable.";
  }
})();
