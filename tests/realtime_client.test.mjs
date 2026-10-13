import assert from "node:assert/strict";
import test from "node:test";
import { createRealtimeClient } from "../web/realtime-client.js";

class FakeEventSource {
  static latest;
  constructor(url, options) {
    this.url = url;
    this.options = options;
    this.listeners = new Map();
    this.closed = false;
    FakeEventSource.latest = this;
  }
  addEventListener(type, cb) { this.listeners.set(type, cb); }
  emit(type, payload) { this.listeners.get(type)?.(payload); }
  close() { this.closed = true; }
}

test("receives resumable notification once and cleans up on stop", () => {
  const updates = [];
  const states = [];
  const client = createRealtimeClient({
    EventSourceImpl: FakeEventSource,
    onNotification: event => updates.push(event),
    onConnectionChange: status => states.push(status),
  });
  client.start();
  const stream = FakeEventSource.latest;
  assert.equal(stream.url, "/api/v1/realtime/events");
  assert.equal(stream.options.withCredentials, false);
  stream.emit("open", {});
  const id = "11111111-1111-4111-8111-111111111111";
  const payload = { EventID: id, CompanyID: "22222222-2222-4222-8222-222222222222" };
  for (let i = 0; i < 2; i++) {
    stream.emit("notification", { lastEventId: id, data: JSON.stringify(payload) });
  }
  stream.emit("notification", { lastEventId: "bad", data: JSON.stringify(payload) });
  stream.emit("notification", { lastEventId: id, data: "{not-json" });
  assert.equal(updates.length, 1);
  assert.deepEqual(states, ["connected", "invalid-event"]);
  client.stop();
  assert.equal(stream.closed, true);
  assert.equal(states.at(-1), "disconnected");
});

test("disallows arbitrary origins and missing callback", () => {
  assert.throws(() => createRealtimeClient({ url: "https://attacker.example/events", onNotification() {} }));
  assert.throws(() => createRealtimeClient({ EventSourceImpl: FakeEventSource }));
});
