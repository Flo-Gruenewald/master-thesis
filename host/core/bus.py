"""MQTT: the embedded broker (optional) and the host's own client.

[mqtt] mode = "embedded" starts a broker inside the host (default, nothing to install);
mode = "external" connects to another broker, e.g. Home Assistant's Mosquitto (see Prototype/Demo/Plan/Migration_HA.md).

All events, state and commands travel as JSON under one topic prefix (see README.md).
Incoming messages are handed to handlers on the asyncio loop.
"""
import json
import logging

import paho.mqtt.client as mqtt
from amqtt.broker import Broker

log = logging.getLogger("bus")


async def start_broker(port):
    logging.getLogger("amqtt").setLevel(logging.WARNING)
    logging.getLogger("transitions").setLevel(logging.WARNING)
    broker = Broker({
        "listeners": {"default": {"type": "tcp", "bind": f"0.0.0.0:{port}"}},
        "plugins": {"amqtt.plugins.authentication.AnonymousAuthPlugin": {"allow_anonymous": True}},
    })
    await broker.start()
    log.info("MQTT broker on port %d", port)
    return broker


class Bus:
    def __init__(self, prefix, port, loop, host="127.0.0.1", username=None, password=None):
        self.prefix = prefix
        self.port = port
        self.host = host
        self.loop = loop
        self.handlers = []
        self.connected = False
        self.on_connect_hooks = []      # called (on the asyncio loop) after every (re)connect
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="easteregged-host")
        if username:
            self.client.username_pw_set(username, password or None)
        self.client.reconnect_delay_set(1, 10)
        self.client.on_disconnect = self._on_disconnect
        self.client.will_set(self.topic("status/host"), "offline", retain=True)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def topic(self, sub):
        return f"{self.prefix}/{sub}"

    def start(self):
        self.client.connect_async(self.host, self.port)     # retries by itself if the broker isn't up yet
        self.client.loop_start()

    def stop(self):
        self.client.publish(self.topic("status/host"), "offline", retain=True)
        self.client.loop_stop()
        self.client.disconnect()

    def on(self, sub, fn):
        """fn(sub_topic, payload) runs on the asyncio loop for every message matching sub."""
        self.handlers.append((self.topic(sub), fn))

    def publish(self, sub, payload, retain=False):
        self.publish_raw(self.topic(sub), payload, retain)

    def publish_raw(self, topic, payload, retain=False):
        """Publish outside the prefix (e.g. Home Assistant discovery)."""
        data = payload if isinstance(payload, str) else json.dumps(payload, separators=(",", ":"))
        self.client.publish(topic, data, retain=retain)

    def _on_connect(self, client, userdata, flags, reason, props=None):
        if getattr(reason, "is_failure", False):
            log.error("MQTT connect to %s:%d refused: %s", self.host, self.port, reason)
            return
        self.connected = True
        log.info("MQTT connected to %s:%d", self.host, self.port)
        client.subscribe(f"{self.prefix}/#")
        client.publish(self.topic("status/host"), "online", retain=True)
        for fn in self.on_connect_hooks:
            self.loop.call_soon_threadsafe(fn)

    def _on_disconnect(self, client, userdata, flags, reason, props=None):
        self.connected = False
        log.warning("MQTT disconnected (%s), reconnecting", reason)

    def _on_message(self, client, userdata, msg):
        raw = msg.payload.decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else None
        except ValueError:
            payload = raw
        self.loop.call_soon_threadsafe(self._dispatch, msg.topic, payload)

    def _dispatch(self, topic, payload):
        sub = topic[len(self.prefix) + 1:]
        for flt, fn in self.handlers:
            if mqtt.topic_matches_sub(flt, topic):
                try:
                    fn(sub, payload)
                except Exception:
                    log.exception("handler for %s failed", topic)
