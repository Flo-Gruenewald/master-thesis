"""Scenario 1 · Morning Jam (active).

wake    a sunrise on the ground level, the spotlight opens on the table
jam     the beat runs and the table mic (table unit, [netmic]) is recorded loop by loop. A loop with something
        in it (a tap, a cup, humming, a word) becomes a row and comes back at the same place in every loop.
        Feedback: while you play, the spotlight brightens with your sound; a new row flashes the spotlight
        and the table edge; every row glows softly on the table when it comes round again.
outro   always 1:30 after the start (end_s, 20.10.2026: the same length in every demo) or when Stop is pressed:
        piano outro at once (a second Stop cuts it); light settles, rows fade
"""
import time

from core.scenario import Scenario as Base


class Scenario(Base):
    name = "morning_jam"
    title = "Morning Jam"
    order = 1
    ending = False                      # set by the first Stop
    hints = {"wake": "Good morning: the room wakes up",
             "jam": "Tap, ding a cup, hum or talk: it comes back in the loop", "outro": "The jam winds down"}

    async def run(self):
        c, a, li = self.cfg, self.audio, self.light
        rows = self.host.rows
        wake = float(c["wake_seconds"])
        self.ending = False
        self.t_run = time.monotonic()                   # 1:30 counts from here (the web page's timer starts here too)

        self.moment("wake")
        li.ground(self.color("dawn"), 0.35, fade=wake * 0.6, breath=0.0)
        a.oneshot("SFX_Tablet_Offer", gain=0.5)
        await self.sleep(wake * 0.6)
        li.ground(self.color("warm"), 0.4, fade=wake * 0.4, breath=0.2)
        li.spotlight(self.color("peach"), 0.5, width=0.9, fade=wake * 0.4)
        await self.sleep(wake * 0.4)

        self.moment("jam")
        a.oneshot("MJ_Intro", gain=0.8)
        a.start_bed("MJ_BeatLoop", gain=0.8, fade=0.5)
        li.spotlight(self.color("peach"), 0.6, width=0.35, fade=a.loop_seconds)  # narrows onto the table
        if rows is None:
            self.host.event({"type": "note", "text": "no table mic ([netmic] off): nothing is recorded"})
        else:
            rows.active = True
        self.started = self.last_activity = time.monotonic()
        shaker = False
        while not self._should_end():
            await self.sleep(0.5)
            if not shaker and len(a.layers) >= c["host_layer_after"]:      # the host joins in
                a.start_bed("MJ_Shaker", gain=0.45, fade=a.loop_seconds)
                shaker = True

        self.moment("outro")
        if rows is not None:
            rows.active = False
        self.host.keep_trace("jam", a.snapshot_layers())   # for Spring Cleaning's "Rewind?"
        await self.sleep(0.0)                                   # Stop or 1:30: the outro right away
        a.stop_beds(fade=1.0)
        a.oneshot("MJ_PianoOutro", gain=0.8)
        li.spotlight(self.color("peach"), 0.0, width=1.0, fade=4.0)
        li.ground(self.color("peach"), 0.3, fade=2.0, breath=0.0)
        await self.sleep(3.0)
        a.clear_layers(fade=3.0)
        li.release(fade=4.0)            # back to the room's own light
        await self.sleep(4.0)

    def _should_end(self):
        c, now = self.cfg, time.monotonic()
        return self.ending or now - self.t_run >= float(c.get("end_s", 90))

    def wind_down(self):
        if self.ending or self.host.moment not in ("wake", "jam"):
            return False                # second Stop, or already in the outro: cut
        self.ending = True              # Stop → the jam ends at once and the outro plays
        return True

    def on_onset(self, ev):
        pass                            # the table mic answers here (host loop), not the laptop's mic

    def on_row(self, ev):
        if self.host.moment != "jam":
            return {"accepted": False, "reason": "not listening"}
        res = self.audio.add_row(ev["buf"])
        if res.get("accepted"):
            self.last_activity = time.monotonic()
            top = next((s for s in self.host.spots if s.get("moment")), None)
            if top is not None:
                self.light.pulse(top["id"], self.color("bone"), amp=0.9, decay=2.5)   # "your loop is in"
            self.light.accent(self.color("bone"), 0.6, seconds=1.5)
        return res

    def on_layer_play(self, t, spot, kind):
        self.light.pulse(spot, self.color("peach"), amp=0.35, decay=4.0)       # a row comes round again
