"""Web page + WebSocket bridge.

The page receives every MQTT message under the prefix as {"topic": "<sub>", "payload": ...}
and may publish to "cmd" (controls) and "in/..." (simulator), exactly like a hardware subnode.
"""
import asyncio
import json
import logging
from pathlib import Path

from aiohttp import WSMsgType, web

log = logging.getLogger("web")
HIGH_RATE = {"meter", "light", "event"}


class Web:
    def __init__(self, bus, port, root):
        self.bus = bus
        self.port = port
        self.root = Path(root)
        self.clients = set()
        self.cache = {}
        bus.on("#", self._from_bus)

    def _from_bus(self, sub, payload):
        msg = json.dumps({"topic": sub, "payload": payload}, separators=(",", ":"))
        if sub not in HIGH_RATE:
            self.cache[sub] = msg
        for ws in list(self.clients):
            asyncio.ensure_future(self._send(ws, msg))

    async def _send(self, ws, msg):
        try:
            await ws.send_str(msg)
        except Exception:
            self.clients.discard(ws)

    async def _ws(self, request):
        ws = web.WebSocketResponse(heartbeat=20)
        await ws.prepare(request)
        for msg in list(self.cache.values()):
            await ws.send_str(msg)
        self.clients.add(ws)
        try:
            async for msg in ws:
                if msg.type != WSMsgType.TEXT:
                    continue
                try:
                    d = json.loads(msg.data)
                except ValueError:
                    continue
                topic = str(d.get("topic", ""))
                if topic == "cmd" or topic.startswith("in/"):
                    if topic == "cmd":          # who changed what (several pages can be open at once)
                        log.info("cmd from %s (%s): %s", request.remote,
                                 request.headers.get("Referer", "?").split("/")[-1] or "home", d.get("payload"))
                    self.bus.publish(topic, d.get("payload"))
        finally:
            self.clients.discard(ws)
        return ws

    async def start(self):
        @web.middleware
        async def no_cache(request, handler):     # the page and its scripts always fresh (no stale app.js after edits)
            resp = await handler(request)
            if request.path == "/" or request.path.startswith("/static/"):
                resp.headers["Cache-Control"] = "no-cache"
            return resp

        app = web.Application(middlewares=[no_cache])
        app.router.add_get("/", lambda r: web.FileResponse(self.root / "index.html"))
        app.router.add_get("/ws", self._ws)
        app.router.add_static("/static/", self.root)
        self.runner = web.AppRunner(app, access_log=None)
        await self.runner.setup()
        await web.TCPSite(self.runner, "0.0.0.0", self.port).start()
        log.info("web page on http://localhost:%d", self.port)

    async def stop(self):
        for ws in list(self.clients):       # open pages would otherwise hold the shutdown
            await ws.close()
        await self.runner.shutdown()
        await self.runner.cleanup()
