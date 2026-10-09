"use strict";
// Same-origin authenticated invalidation channel. No authentication tokens in URLs
// or storage; sockets depend on server-managed session cookies.
(function (root) {
  function subscribe({companyId, onInvalidate, onStatus, socketFactory, schedule, cancel}) {
    if (typeof companyId !== "string" || !/^[0-9a-f-]{36}$/i.test(companyId))
      throw new Error("Valid company ID required");
    if (typeof onInvalidate !== "function") throw new Error("Refresh callback required");
    const makeSocket = socketFactory || (url => new WebSocket(url));
    const later = schedule || ((fn, ms) => setTimeout(fn, ms));
    const stopTimer = cancel || (handle => clearTimeout(handle));
    let socket = null, timer = null, stopped = false, reconnects = 0;
    let lastEvent = null;
    function status(message) { if (typeof onStatus === "function") onStatus(message); }
    function connect() {
      if (stopped) return;
      const scheme = location.protocol === "https:" ? "wss:" : "ws:";
      if (scheme !== "wss:" && location.hostname !== "localhost")
        throw new Error("Secure connection required");
      socket = makeSocket(scheme + "//" + location.host +
        "/api/v1/companies/" + encodeURIComponent(companyId) + "/realtime/ws");
      socket.onopen = () => { reconnects = 0; status("Connected"); onInvalidate("resynchronise"); };
      socket.onmessage = event => {
        let message;
        try { message = JSON.parse(event.data); } catch { return; }
        if (!message || message.company_id !== companyId || message.type !== "finance.changed") return;
        if (typeof message.event_id !== "string" || !message.event_id || message.event_id === lastEvent) return;
        lastEvent = message.event_id;
        onInvalidate("finance.changed");
      };
      socket.onclose = () => {
        if (stopped) return;
        status("Reconnecting");
        const backoff = Math.min(30000, 1000 * (2 ** Math.min(reconnects++, 5)));
        timer = later(connect, backoff);
      };
      socket.onerror = () => status("Connection unavailable");
    }
    connect();
    return {stop() {
      stopped = true;
      if (timer !== null) stopTimer(timer);
      if (socket) socket.close();
    }};
  }
  root.CapitalBridgeRealtime = Object.freeze({subscribe});
})(typeof window !== "undefined" ? window : globalThis);
