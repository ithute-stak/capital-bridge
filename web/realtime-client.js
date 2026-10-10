"use strict";

/**
 * Browser notification adapter for authenticated same-origin SSE.
 *
 * The server must mount /api/v1/realtime/events with cookie authentication,
 * tenant authorization, Origin enforcement and Last-Event-ID replay.
 * Never send bearer tokens or company identifiers in URLs.
 *
 * This is a reusable client, not activated on the illustrative demo UI.
 */
export function createRealtimeClient({
  url = "/api/v1/realtime/events",
  onNotification,
  onConnectionChange = () => {},
  EventSourceImpl = globalThis.EventSource,
} = {}) {
  if (url !== "/api/v1/realtime/events") {
    throw new Error("Realtime endpoint must be the trusted same-origin route");
  }
  if (typeof onNotification !== "function") {
    throw new TypeError("onNotification callback required");
  }
  if (typeof EventSourceImpl !== "function") {
    throw new Error("EventSource is unavailable");
  }

  let source = null;
  let closed = false;
  const seen = new Set();
  const MAX_SEEN = 500;

  function start() {
    if (closed || source) return;
    source = new EventSourceImpl(url, { withCredentials: false });
    source.addEventListener("open", () => onConnectionChange("connected"));
    source.addEventListener("error", () => onConnectionChange("reconnecting"));
    source.addEventListener("notification", event => {
      let notification;
      try {
        notification = JSON.parse(event.data);
      } catch {
        onConnectionChange("invalid-event");
        return;
      }
      const eventId = event.lastEventId;
      if (!/^[a-f\d]{8}-(?:[a-f\d]{4}-){3}[a-f\d]{12}$/i.test(eventId)) return;
      if (!notification || notification.EventID !== eventId) return;
      if (seen.has(eventId)) return;
      seen.add(eventId);
      if (seen.size > MAX_SEEN) seen.delete(seen.values().next().value);
      // The application must re-fetch authorized records instead of trusting
      // the notification payload as canonical financial state.
      onNotification(notification);
    });
  }

  function stop() {
    closed = true;
    if (source) source.close();
    source = null;
    seen.clear();
    onConnectionChange("disconnected");
  }

  return { start, stop };
}
