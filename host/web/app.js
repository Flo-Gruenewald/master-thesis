// Room host · interface v3 — Home · Node · Scenarios · Turn off (Mars Rust bento).
// One WebSocket mirrors the host's MQTT topics (state 2 Hz, meter 20 Hz, light 15 Hz, events);
// the page sends commands like any other subnode ({"topic": "cmd", "payload": {...}}).
"use strict";
const $ = (id) => document.getElementById(id);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const C = { top: "#E37156", middle: "#76DBD8", ground: "#F2EAE3", alert: "#D0273F", text3: "#8A7A6C", border: "#3A2C24",
  tealD: "#3F7573", rust: "#A14530", rustD: "#783526", peach: "#F2AD9D" };
// colour temperature drawn in the Mars Rust palette: deep rust (night) → sand → peach → bone (daylight); blue → teal
const KSTOPS = [[1800, "#783526"], [2200, "#A14530"], [2700, "#E37156"], [3500, "#F2AD9D"], [4600, "#F2EAE3"]];
const NS = "http://www.w3.org/2000/svg";
let ws, S = null, L = null, M = null, dragging = null, page = "home";

// ------------------------------------------------------------------ labels
const LABEL = {
  crickets: "Crickets", rain: "Rain", birds: "Birds", wind: "Wind", winter: "Winter wind", room_tone: "Room tone", fire: "Fire",
  bird_cross: "Bird", bee_pass: "Bee", cat_meow: "Cat", wind_gust: "Gust", rain_pass: "Rain shower", thunder_far: "Thunder",
  sun_ray: "Sun ray", cloud: "Cloud",
  MJ_BeatLoop: "Beat", MJ_Shaker: "Shaker", MJ_Intro: "Intro", MJ_PianoOutro: "Piano outro", SFX_Tablet_Offer: "Offer chime",
  rain_window: "Rain on the window", rain_soft: "Rain (travelling)", movie_room: "Movie murmur", music: "Music",
  lena_01: "Lena (Earth)", cat_purr: "Purr", cat_meow_2: "Cat", chime: "Chime", rewind: "Rewind", arrive: "Postcard chime",
  invite: "Invitation chime", screen_wake: "Screen", trace: "Trace",
};
const label = (n) => LABEL[n] || String(n).replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
const cap = (t) => (t ? t[0].toUpperCase() + t.slice(1) : "");
const SCEN = {
  morning_jam: "Tap, ding a cup, hum or talk at the table: each loop you fill comes back in the beat.",
  spring_cleaning: "Come closer: the season wakes up around you. Step away: it rests.",
  miss_you_sis: "A postcard from Earth. Hold it: Lena’s evening in Rome fills the room.",
};
// the opening of each scenario tab: where it happens · what it answers · the direction (Pollini, notes 16), then a short story
const STORY = {      // [mission day (booklet), story = the title, framing]
  morning_jam: ["Day 140 · Wednesday morning", "The same table, the same faces, the same breakfast. Then someone taps a rhythm.",
    "Table · Monotony · Moments of connection · Bottom-up"],
  spring_cleaning: ["Day 445 · on the way home", "The corridor has been winter for weeks, until someone walks through it.",
    "Corridor · Detachment & Confinement · Transition · Top-down"],
  miss_you_sis: ["Day 455 · Friday, late evening", "Night in the sleeping pod. Earth is a pale dot behind the window. Then a postcard arrives.",
    "Sleeping pod · Isolation & Connection to home · Bottom-up"],
};
// what matters to try out in each scenario
const SPRING_LABEL = { winter: "Winter wind", gust: "Wind gust", rain: "Rain", birds: "Birds", bees: "Bees", song: "Here Comes the Sun",
  cat: "Cat", frog: "Frog", crickets: "Crickets", birdcall: "Bird call" , wind: "Autumn wind", shower: "Rain shower", fire: "Fireplace" };
// the season icons of our logo (same as clock.html)
const SEASON_ICON = {
  spring: '<path d="M12 21v-8"/><path d="M12 13C12 9 9.5 6.5 5 6.5 5 11 8 13 12 13z"/><path d="M12 11c0-3.2 2.4-5.5 6.5-5.5 0 3.7-2.6 5.5-6.5 5.5z"/>',
  summer: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M5.3 18.7l1.8-1.8M16.9 7.1l1.8-1.8"/>',
  autumn: '<path d="M5 19C5 11 11 5 20 5c0 9-6 15-14 15z"/><path d="M5 19l8.5-8.5"/>',
  winter: '<path d="M12 2.5v19M3.8 7.2l16.4 9.6M3.8 16.8l16.4-9.6"/><path d="M9.5 4.5 12 7l2.5-2.5M9.5 19.5 12 17l2.5 2.5"/>',
};
const seasonIcon = (n) => SEASON_ICON[n] ? `<svg class="s-ic" viewBox="0 0 24 24">${SEASON_ICON[n]}</svg>` : "";
// the S2 sound switches as a table: columns = seasons, rows = ground (general) and accent
function soundTable(sp) {
  const chip = (k) => `<button class="btn${sp.sounds[k] ? " primary" : ""}" data-snd="${k}">${SPRING_LABEL[k] || k}</button>`;
  const cell = (list) => `<div class="st-cell">${list.map(chip).join("")}</div>`;
  return `<div class="stable"><span></span><span class="st-k">Ground</span><span class="st-k">Accent</span>` +
    sp.rows.map((r) => `<span class="st-h">${seasonIcon(r.season)}${cap(r.season)}</span>${cell(r.general)}${cell(r.accent)}`).join("") + `</div>`;
}
// the pointer on the booklet timeline (web/mission_timeline.svg): x = X0 + day * PX in the drawing (W wide)
let TLX = { x0: 277, px: 2.1853, w: 1684 };
function tlMove(el, startDay, day) {
  const pc = (d) => `${(((TLX.x0 + Math.max(0, Math.min(611, d)) * TLX.px) / TLX.w) * 100).toFixed(3)}%`;
  const trail = el.querySelector(".tl-trail"), here = el.querySelector(".tl-hereh");
  trail.style.left = pc(startDay); trail.style.width = `calc(${pc(day)} - ${pc(startDay)})`;
  here.style.left = pc(day);
}
// colour temperature → rgb (approximation, enough for the curve's colour)
function kRGB(k) {
  const t = k / 100;
  const r = t <= 66 ? 255 : 329.7 * Math.pow(t - 60, -0.1332);
  const g = t <= 66 ? 99.47 * Math.log(t) - 161.12 : 288.12 * Math.pow(t - 60, -0.0755);
  const b = t >= 66 ? 255 : t <= 19 ? 0 : 138.52 * Math.log(t - 10) - 305.04;
  const c = (v) => Math.round(Math.max(0, Math.min(255, v)));
  return `rgb(${c(r)},${c(g)},${c(b)})`;
}
const SIMS = {
  morning_jam: [["clear", "Clear rows"]],
  spring_cleaning: [["someone", "Someone passes"], ["empty", "No one there"], ["pass", "Next phase"], ["season", "Next season"]],
  miss_you_sis: [["postcard", "Postcard from Earth"], ["hold", "Hold the card (on/off)"]],
};

// room screen (kellerkind, ?kiosk=1): no live light/meter redraws, they cost a Pi 3B most of its CPU
const KIOSK = new URLSearchParams(location.search).has("kiosk");
if (KIOSK) document.documentElement.classList.add("kiosk");

// ------------------------------------------------------------------ connection
function connect() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onopen = () => { $("conn").classList.add("ok"); $("conn").title = "host connected"; };
  ws.onclose = () => { $("conn").classList.remove("ok"); $("conn").title = "host offline, retrying"; setTimeout(connect, 1500); };
  ws.onmessage = (e) => {
    const { topic, payload } = JSON.parse(e.data);
    if (KIOSK && (topic === "meter" || topic === "light")) return;   // room screen: skip the 15–20 Hz streams
    if (topic === "state") onState(payload);
    else if (topic === "meter") onMeter(payload);
    else if (topic === "light") onLight(payload);
    else if (topic === "event") onEvent(payload);
  };
}
const send = (topic, payload) => { if (ws && ws.readyState === 1) ws.send(JSON.stringify({ topic, payload })); };
const cmd = (c, v) => send("cmd", v === undefined ? { cmd: c } : { cmd: c, value: v });
function sim(k) {
  if (k === "arrive" || k === "leave") send("in/presence", { present: k === "arrive", src: "sim" });
  else if (k === "hit" || k === "hum") send("in/sound", { kind: k });
  else if (k === "postcard") cmd("postcard");
  else if (k === "clear") cmd("clear_layers");
  else if (k === "pass") cmd("spring_pass");
  else if (k === "skip") cmd("spring_skip");
  else if (k === "season") cmd("spring_season");
  else if (k === "someone") cmd("spring_someone");
  else if (k === "empty") cmd("spring_empty");
  else if (k === "mode" && S && S.spring) cmd("spring_mode", S.spring.mode === "scripted" ? "interactive" : "scripted");
  else if (k === "hold") cmd("postcard_hold");
}

function setHTML(el, html) { if (el && el._h !== html) { el.innerHTML = html; el._h = html; } }
function svgEl(tag, attrs, parent, text) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (text !== undefined) e.textContent = text;
  if (parent) parent.appendChild(e);
  return e;
}

// ------------------------------------------------------------------ routing
const PAGES = { home: "Home", node: "Node", s1: "Morning Jam", s2: "Spring Cleaning", s3: "I Miss You, Sis", radar: "Radar" };
const SCEN_TAB = { s1: "morning_jam", s2: "spring_cleaning", s3: "miss_you_sis" };   // one tab = one scenario, full screen
function route() {
  const h = location.hash.slice(1);
  page = h === "scenarios" ? "s1" : h in PAGES ? h : "home";
  for (const p of ["home", "node", "radar"]) $("page-" + p).classList.toggle("on", p === page);
  $("page-scenarios").classList.toggle("on", page in SCEN_TAB);
  $("cards").dataset.only = SCEN_TAB[page] || "";
  for (const n in CARD) CARD[n].el.classList.toggle("sel", n === SCEN_TAB[page]);
  $$(".rail a").forEach((a) => a.classList.toggle("on", a.dataset.page === page));
  $("page-title").textContent = PAGES[page];
  if (S) scenState(S);
  const rf = $("radar-frame");           // the radar view connects only while its page is open
  if (page === "radar" && !rf.src) rf.src = rf.dataset.src;
  else if (page !== "radar" && rf.src) rf.removeAttribute("src");
  requestAnimationFrame(() => { if (L) onLight(L); if (S) drawCurve(S.room); });
}
window.addEventListener("hashchange", route);

// ------------------------------------------------------------------ generic controls
document.addEventListener("change", (e) => {
  const el = e.target;
  if (el.matches("input[type=checkbox][data-cmd]")) cmd(el.dataset.cmd, el.checked);
});
const timers = {};
const fillPill = (el) => el.style.setProperty("--p", el.value * 100 + "%");
document.addEventListener("input", (e) => {
  const el = e.target;
  if (!el.matches("input[type=range][data-cmd]")) return;
  const k = el.dataset.cmd;
  fillPill(el);
  $$(`[data-out="${k}"]`).forEach((o) => (o.textContent = Math.round(el.value * 100)));
  clearTimeout(timers[k]);
  timers[k] = setTimeout(() => cmd(k, parseFloat(el.value)), 70);
});
document.addEventListener("pointerdown", (e) => { if (e.target.matches("input[type=range][data-cmd]")) dragging = e.target.dataset.cmd; });
document.addEventListener("pointerup", () => (dragging = null));

function syncControls(s) {
  const checks = { auto: s.auto, ground: s.room.ground, middle: s.room.middle };
  $$("input[type=checkbox][data-cmd]").forEach((el) => { if (el.dataset.cmd in checks) el.checked = !!checks[el.dataset.cmd]; });
  const ranges = { volume: s.volume, ambient_volume: s.ambient_volume, brightness: s.brightness, sensitivity: s.sensitivity };
  $$("input[type=range][data-cmd]").forEach((el) => {
    const k = el.dataset.cmd;
    if (k in ranges && dragging !== k) { el.value = ranges[k]; fillPill(el); }
  });
  for (const k in ranges) if (dragging !== k) $$(`[data-out="${k}"]`).forEach((o) => (o.textContent = Math.round(ranges[k] * 100)));
}

// ------------------------------------------------------------------ helpers
function cctArr(k) {
  const t = k / 100;
  let r = t <= 66 ? 255 : 329.698727446 * Math.pow(t - 60, -0.1332047592);
  let g = t <= 66 ? 99.4708025861 * Math.log(t) - 161.1195681661 : 288.1221695283 * Math.pow(t - 60, -0.0755148492);
  let b = t >= 66 ? 255 : t <= 19 ? 0 : 138.5177312231 * Math.log(t - 10) - 305.0447927307;
  [r, g, b] = [r, g, b].map((v) => Math.max(0, Math.min(255, v)));
  const m = Math.max(r, g, b) || 1;
  return [r / m, g / m, b / m];
}
const rgbStr = (a, f = 1) => `rgb(${a.map((v) => Math.round(Math.max(0, Math.min(1, v * f)) * 255)).join(",")})`;
const cct = (k) => rgbStr(cctArr(k));
const hexArr = (h) => [1, 3, 5].map((i) => parseInt(h.substr(i, 2), 16) / 255);
const mix = (a, b, f) => a.map((v, i) => v + (b[i] - v) * f);
// the room's light in palette colours: K along KSTOPS, the morning blue pulls toward Kolibri blue
function roomColour(k, blue) {
  let i = 0;
  while (i < KSTOPS.length - 2 && k > KSTOPS[i + 1][0]) i++;
  const [k0, c0] = KSTOPS[i], [k1, c1] = KSTOPS[i + 1];
  const base = mix(hexArr(c0), hexArr(c1), Math.max(0, Math.min(1, (k - k0) / (k1 - k0))));
  return mix(base, hexArr(C.middle), Math.min(0.75, blue * 0.75));
}
const fmtH = (h) => `${String(Math.floor(((h % 24) + 24) % 24)).padStart(2, "0")}:${String(Math.floor((h % 1) * 60)).padStart(2, "0")}`;
const mmss = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
// phase of the circadian day at hour h (see core/room.py day())
function phaseAt(r, h) {
  const wake = r.dawn_h, sleep = r.sleep_h || 22.5, dusk = r.dusk_h;
  if (h >= sleep || h < wake - 0.5) return "Night";
  if (h < wake) return "Dawn simulation";
  if (h < wake + 1) return "Post-sleep";
  if (r.blue > 0.05 && h < 13) return "Blue morning";
  if (h >= sleep - 3) return "Pre-sleep";
  if (h >= dusk - 1) return "Golden evening";
  return "Day";
}

// ------------------------------------------------------------------ state
let sigScen = "";
function onState(s) {
  S = s;
  $("off").hidden = s.power !== false;
  $("moment-chip").textContent = s.power === false ? "off" : s.running ? `${s.title} · ${s.moment}` : "idle";
  $("moment-chip").classList.toggle("run", !!s.running);
  $("hdr-clock").textContent = s.room.clock;
  homeState(s); nodeState(s); scenState(s); syncControls(s);
  if (!feedInit) { feedInit = true; (s.recent || []).forEach((e) => { if (e.type !== "onset") events.unshift(e); }); renderFeed(); }
}

// ================================================================== HOME
let curveSig = "", curveDrag = false;
function homeState(s) {
  const r = s.room;
  if (curveDrag === false) $("clock").textContent = r.clock;
  const off = (((r.hour - r.real_hour) % 24) + 24) % 24;
  $("clock-info").textContent = (r.day_minutes > 0 ? `simulated · a day lasts ${r.day_minutes} min` :
    Math.min(off, 24 - off) < 0.05 ? "real time" : `shifted · real time ${fmtH(r.real_hour)}`) +
    (r.date_real === false ? " · date set by hand" : "");
  $$("#speeds button").forEach((b) => b.classList.toggle("on", parseFloat(b.dataset.v) === r.day_minutes));
  if (r.date) {
    const d = new Date(r.date + "T12:00:00");
    setHTML($("sim-date"), `Day ${r.mission_day}<small>${d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "long", year: "numeric" })}</small>`);
  }
  drawCurve(r);
  wheelState(r);
  const col = roomColour(r.k, r.blue || 0);
  $("now-swatch").style.background = rgbStr(col, 0.45 + 0.55 * Math.min(1, r.level / 0.55));
  $("now-phase").textContent = r.ground ? phaseAt(r, r.hour) : "Circadian light off";

}
$("speeds").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) cmd("day_minutes", parseFloat(b.dataset.v)); });
// the light value sits on the curve, at the room's dot
function curveNow(r, h, X, Y, lvAt) {
  const el = $("curve-now"), fx = X(h) / CW;
  el.textContent = r.ground ? `${r.k} K · ${Math.round(r.level * 100)} %${r.blue > 0.01 ? ` · blue ${Math.round(r.blue * 100)} %` : ""}${r.top ? " · dimmed" : ""}` : "off";
  el.style.left = `${(fx * 100).toFixed(2)}%`;
  el.style.top = `${((Y(lvAt(h)) / CH) * 100).toFixed(2)}%`;
  el.classList.toggle("r", fx > 0.85); el.classList.toggle("l", fx < 0.12);
}
$("now-btn").onclick = () => cmd("now");

// ---- circadian curve
const CW = 960, CH = 260;
// the circadian day (home page and S2): the curve, night/pre-sleep/post-sleep bands, blue morning; p = id prefix
const maxComfy = (v) => Math.min(1, v / 0.9);          // the comfy hill's height (winter = full)
function curveMarkup(r, X, Y, p) {
  const n = r.curve.length, sleep = r.sleep_h || 22.5, wake = r.dawn_h;
  const pts = r.curve.map((c, i) => [X((24 * i) / n), Y(c[0])]);
  pts.push([CW, Y(r.curve[0][0])]);
  const line = pts.map((q, i) => (i ? "L" : "M") + q[0].toFixed(1) + " " + q[1].toFixed(1)).join(" ");
  const bpts = r.curve.map((c, i) => [X((24 * i) / n), Y(c[0] * (c[2] || 0))]);
  const blue = `M0 ${CH} ` + bpts.map((q) => `L${q[0].toFixed(1)} ${q[1].toFixed(1)}`).join(" ") + ` L${CW} ${CH} Z`;
  // the comfy (pre-sleep) light: a soft orange hill, like the blue morning; nothing where it is 0 (no strip along the day)
  const cpts = r.curve.map((c, i) => [X((24 * i) / n), (c[3] || 0) > 0.005 ? Y(0.45 * maxComfy(c[3])) : CH]);
  const comfy = `M0 ${CH} ` + cpts.map((q) => `L${q[0].toFixed(1)} ${q[1].toFixed(1)}`).join(" ") + ` L${CW} ${CH} Z`;
  const stops = r.curve.filter((_, i) => i % 2 === 0).map((c, i, a) => `<stop offset="${(i / (a.length - 1)).toFixed(3)}" stop-color="${rgbStr(roomColour(c[1], c[2] || 0))}"/>`).join("");
  return `<defs><linearGradient id="${p}kg" x1="0" x2="1">${stops}</linearGradient>
      <linearGradient id="${p}fade" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".85"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
      <mask id="${p}fm"><rect width="${CW}" height="${CH}" fill="url(#${p}fade)"/></mask>
      <linearGradient id="${p}bg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${C.middle}" stop-opacity=".75"/><stop offset="1" stop-color="${C.tealD}" stop-opacity=".35"/></linearGradient>
      <linearGradient id="${p}cg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${C.top}" stop-opacity=".75"/><stop offset="1" stop-color="${C.rustD}" stop-opacity=".35"/></linearGradient></defs>
      <rect x="0" width="${X(wake - 0.5)}" height="${CH}" fill="#000" opacity=".22"/>
      <rect x="${X(sleep)}" width="${CW - X(sleep)}" height="${CH}" fill="#000" opacity=".22"/>
      <rect x="${X(sleep - 3)}" width="${X(3)}" height="${CH}" fill="${C.rust}" opacity=".16"/>
      <rect x="${X(wake)}" width="${X(1)}" height="${CH}" fill="${C.rust}" opacity=".16"/>
      ${[6, 12, 18].map((h) => `<line x1="${X(h)}" x2="${X(h)}" y1="0" y2="${CH}" stroke="${C.border}" stroke-width="1" vector-effect="non-scaling-stroke"/>`).join("")}
      <path d="${line} L${CW} ${CH} L0 ${CH} Z" fill="url(#${p}kg)" opacity=".26" mask="url(#${p}fm)"/>
      <path d="${blue}" fill="url(#${p}bg)"/>
      <path d="${comfy}" fill="url(#${p}cg)"/>
      <path d="${line}" fill="none" stroke="url(#${p}kg)" stroke-width="3" vector-effect="non-scaling-stroke"/>
      <line id="${p}real-mk" y1="0" y2="${CH}" stroke="${C.text3}" stroke-dasharray="4 5" stroke-width="1.5" vector-effect="non-scaling-stroke"/>
      <line id="${p}room-mk" y1="0" y2="${CH}" stroke="${C.ground}" stroke-width="1.5" vector-effect="non-scaling-stroke"/>
      <ellipse id="${p}room-dot" rx="7" ry="7" fill="${C.ground}" stroke="#211C17" stroke-width="3" vector-effect="non-scaling-stroke"/>`;
}
// phases as HTML labels (text in a stretched SVG would be distorted)
function curveLabels(r) {
  const n = r.curve.length, sleep = r.sleep_h || 22.5, wake = r.dawn_h;
  const bl = r.curve.map((c, i) => [(24 * i) / n, c[2] || 0]).filter((x) => x[1] > 0.05);
  const pct = (h) => `${((h / 24) * 100).toFixed(2)}%`;
  const labels = [
    [Math.max(1.6, (wake - 0.5) / 2), "night", ""], ...(24 - sleep > 2.5 ? [[(sleep + 24) / 2, "night", ""]] : []),
    [sleep - 1.5, "pre-sleep", "w"], [wake + 0.5, "post-sleep", "w"],
    ...(bl.length ? [[Math.max(wake + 3.2, (bl[0][0] + bl[bl.length - 1][0]) / 2), "blue morning", "b"]] : []),
    [wake, `dawn ${fmtH(wake)}`, "mk"], [r.dusk_h, `dusk ${fmtH(r.dusk_h)}`, "mk"],
  ];
  return labels.map(([h, t, c]) => `<span class="${c}" style="left:${pct(h)}">${t}</span>`).join("");
}
function drawCurve(r) {
  const svg = $("curve"), n = r.curve.length;
  const maxL = Math.max(0.05, ...r.curve.map((c) => c[0])) * 1.08;
  const X = (h) => (h / 24) * CW, Y = (lv) => CH - 6 - (lv / maxL) * (CH - 40);
  const sleep = r.sleep_h || 22.5, wake = r.dawn_h;
  const sig = JSON.stringify([r.curve, sleep, wake, r.dusk_h]);
  if (sig !== curveSig) {
    curveSig = sig;
    svg.innerHTML = curveMarkup(r, X, Y, "");
    setHTML($("curve-labels"), curveLabels(r));
  }
  const b = svg.getBoundingClientRect(), sx = b.width ? CW / b.width : 1, sy = b.height ? CH / b.height : 1;
  const dot = $("room-dot"); dot.setAttribute("rx", 6 * sx); dot.setAttribute("ry", 6 * sy);
  const lvAt = (h) => r.curve[Math.floor((h / 24) * n) % n][0];
  const h = curveDrag !== false ? curveDrag : r.hour;
  $("room-mk").setAttribute("x1", X(h)); $("room-mk").setAttribute("x2", X(h));
  dot.setAttribute("cx", X(h)); dot.setAttribute("cy", Y(lvAt(h)));
  $("real-mk").setAttribute("x1", X(r.real_hour)); $("real-mk").setAttribute("x2", X(r.real_hour));
  $("ev-mk").style.left = `${((h / 24) * 100).toFixed(3)}%`;
  if (curveDrag === false) curveNow(r, h, X, Y, lvAt);
  syncLine(h);
}
// one line from the curve down into the events: drawn across the gap when both tiles share the same x-range
function syncLine(h) {
  const sy = $("sync"), grid = document.querySelector(".home-grid"), a = $("curve").getBoundingClientRect(), b = $("feed").getBoundingClientRect();
  if (!a.width || !b.width || Math.abs(a.left - b.left) > 2 || Math.abs(a.width - b.width) > 2 || b.top < a.bottom) { sy.style.display = "none"; return; }
  const g = grid.getBoundingClientRect();
  sy.style.display = "block";
  sy.style.left = `${a.left - g.left + (h / 24) * a.width}px`;
  sy.style.top = `${a.bottom - g.top}px`;
  sy.style.height = `${b.top - a.bottom}px`;
}
(function curveInput() {
  const svg = $("curve");
  const lockKey = "easteregged:clock-drag";
  const tabId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const lockMs = 120000;
  let pointerId = null, pointerEl = null, resetTimer = 0;
  const hourAt = (e) => { const b = svg.getBoundingClientRect(); return Math.max(0, Math.min(23.99, ((e.clientX - b.left) / b.width) * 24)); };
  const readLock = () => {
    try { return JSON.parse(localStorage.getItem(lockKey) || "null"); }
    catch { return null; }
  };
  const ownsLock = () => readLock()?.owner === tabId;
  const claimLock = () => {
    try {
      const lock = readLock();
      if (lock && lock.owner !== tabId && Date.now() - lock.at < lockMs) return false;
      localStorage.setItem(lockKey, JSON.stringify({ owner: tabId, at: Date.now() }));
      return ownsLock();
    } catch { return false; }
  };
  const refreshLock = () => {
    if (ownsLock()) localStorage.setItem(lockKey, JSON.stringify({ owner: tabId, at: Date.now() }));
  };
  const releaseLock = () => {
    if (ownsLock()) localStorage.removeItem(lockKey);
  };
  const preview = (e) => {
    curveDrag = hourAt(e);
    if (S) drawCurve(S.room);
    $("clock").textContent = fmtH(curveDrag);
  };
  const finish = (e, sendFinal) => {
    if (pointerId === null || e.pointerId !== pointerId) return;
    if (sendFinal && ownsLock()) {
      preview(e);
      cmd("clock", Number(curveDrag.toFixed(2)));
    }
    const el = pointerEl, id = pointerId;
    pointerId = pointerEl = null;
    releaseLock();
    if (el?.hasPointerCapture(id)) el.releasePointerCapture(id);
    clearTimeout(resetTimer);
    resetTimer = setTimeout(() => { curveDrag = false; if (S) drawCurve(S.room); }, 700);
  };
  // drag on the curve or on the events: both are the same day axis
  for (const el of [svg, $("feed")]) {
    el.addEventListener("pointerdown", (e) => {
      if (e.button !== 0 || pointerId !== null || !claimLock()) return;
      e.preventDefault();
      pointerId = e.pointerId;
      pointerEl = el;
      el.setPointerCapture(pointerId);
      preview(e);
    });
    el.addEventListener("pointermove", (e) => {
      if (e.pointerId !== pointerId || !(e.buttons & 1) || !ownsLock()) return;
      refreshLock();
      preview(e);
    });
    el.addEventListener("pointerup", (e) => finish(e, true));
    el.addEventListener("pointercancel", (e) => finish(e, false));
    el.addEventListener("lostpointercapture", (e) => finish(e, false));
  }
})();

// ---- seasons wheel: the Habitat Halo logo is the mission's season diagram.
// Inner ring = Earth's seasons, outer ring = Mars's seasons, over an opposition-class mission
// (launch April 2033, ~600 days). Each piece between two white ticks is one season.
// Angles: degrees in SVG space (y down), the mission runs from the left end anticlockwise.
const RING = {
  earth: { cx: 282, cy: 297, r: 125, stops: [[0, "#8AE6E2"], [0.55, "#4E9C99"], [1, "#2C6260"]],
    ticks: [193.6, 157, 119, 81, 44.7, 7, -32],
    segs: [["spring", 196.9, 157, "Apr–Jun 2033 · launch"], ["summer", 157, 119, "Jun–Sep 2033 · outbound"],
           ["autumn", 119, 81, "Sep–Dec 2033 · at Mars"], ["winter", 81, 44.7, "Dec 2033–Mar 2034 · way home"],
           ["spring", 44.7, 7, "Mar–Jun 2034 · way home"], ["summer", 7, -32, "Jun–Sep 2034 · way home"],
           ["autumn", -32, -56.6, "Sep 2034 · back on Earth"]] },
  mars: { cx: 284, cy: 292, r: 190, stops: [[0, "#EB8F7A"], [0.3, "#E37156"], [0.65, "#A14530"], [1, "#783526"]],
    ticks: [174.5, 91.5, 25, -34.6],
    segs: [["summer", 199.8, 174.5, "at launch"], ["autumn", 174.5, 91.5, "outbound"], ["winter", 91.5, 25, "surface stay"],
           ["spring", 25, -34.6, "way home"], ["summer", -34.6, -52, "at return"]] },
};
// first day of each Earth segment in the mission (launch 15 Apr 2033; seasons start 20/21 Mar, Jun, Sep, Dec)
const EARTH_START = ["2033-04-15", "2033-06-21", "2033-09-22", "2033-12-21", "2034-03-20", "2034-06-21", "2034-09-22"];
const MISSION_END = "2034-12-06";     // ~day 600 (opposition class)
// where a date sits on the rings: inside its Earth segment, proportional between the season's start and end
function dateAngle(date) {
  let i = 0;
  while (i < EARTH_START.length - 1 && date >= EARTH_START[i + 1]) i++;
  const t = (s) => new Date(s + "T12:00:00").getTime();
  const end = i < EARTH_START.length - 1 ? EARTH_START[i + 1] : MISSION_END;
  const f = Math.max(0, Math.min(1, (t(date) - t(EARTH_START[i])) / (t(end) - t(EARTH_START[i]))));
  const [, a0, a1] = RING.earth.segs[i];
  return a0 + (a1 - a0) * f;
}
const ICON = {
  spring: '<path d="M12 21v-8"/><path d="M12 13C12 9 9.5 6.5 5 6.5 5 11 8 13 12 13z"/><path d="M12 11c0-3.2 2.4-5.5 6.5-5.5 0 3.7-2.6 5.5-6.5 5.5z"/>',
  summer: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M5.3 18.7l1.8-1.8M16.9 7.1l1.8-1.8"/>',
  autumn: '<path d="M5 19C5 11 11 5 20 5c0 9-6 15-14 15z"/><path d="M5 19l8.5-8.5"/>',
  winter: '<path d="M12 2.5v19M3.8 7.2l16.4 9.6M3.8 16.8l16.4-9.6"/><path d="M9.5 4.5 12 7l2.5-2.5M9.5 19.5 12 17l2.5 2.5"/>',
};
const pt = (g, r, deg) => [g.cx + r * Math.cos((deg * Math.PI) / 180), g.cy + r * Math.sin((deg * Math.PI) / 180)];
function arcD(g, r, a0, a1) {
  const [x0, y0] = pt(g, r, a0), [x1, y1] = pt(g, r, a1);
  return `M${x0.toFixed(2)} ${y0.toFixed(2)} A${r} ${r} 0 ${Math.abs(a0 - a1) > 180 ? 1 : 0} 0 ${x1.toFixed(2)} ${y1.toFixed(2)}`;
}
function lerpHex(stops, t) {
  let i = 0;
  while (i < stops.length - 2 && t > stops[i + 1][0]) i++;
  const [t0, c0] = stops[i], [t1, c1] = stops[i + 1], f = Math.max(0, Math.min(1, (t - t0) / (t1 - t0)));
  const p = (c) => [1, 3, 5].map((k) => parseInt(c.substr(k, 2), 16));
  const a = p(c0), b = p(c1);
  return `rgb(${a.map((v, k) => Math.round(v + (b[k] - v) * f)).join(",")})`;
}
let wheelSel = null, wheelHover = null, wheelNote = null, hereHover = false;
const NOTES = {
  earth: ["Planet", "Earth", "inner ring · Earth's seasons", "launch April 2033 · back autumn 2034"],
  mars: ["Planet", "Mars", "outer ring · Mars's seasons", "arrival around day 200"],
  stay: ["Mars", "Surface stay", "about 30 sols on the surface", "opposition class · Mars winter"],
};
function noteWheel(k) {
  wheelNote = k;
  $$("#wheel [data-p]").forEach((p) => p.classList.toggle("on", p.dataset.p === k));
  if (S) wheelState(S.room);
}
try { wheelSel = localStorage.getItem("wheelSel"); } catch (e) { /* private window */ }
function buildWheel() {
  const svg = $("wheel");
  svg.innerHTML = `<defs>
    <linearGradient id="p-mars" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#E37156"/><stop offset="1" stop-color="#7D3E2F"/></linearGradient>
    <linearGradient id="p-earth" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#76DBD8"/><stop offset="1" stop-color="#3F7573"/></linearGradient>
    <linearGradient id="stay" x1="443" y1="426" x2="399.5" y2="391" gradientUnits="userSpaceOnUse"><stop stop-color="#E37156"/><stop offset="1" stop-color="#F2EAE3"/></linearGradient></defs>`;
  for (const ring of ["mars", "earth"]) {
    const g = RING[ring], total = g.segs[0][1] - g.segs[g.segs.length - 1][2];
    g.segs.forEach(([season, a0, a1, when], i) => {
      const mid = (a0 + a1) / 2, t = (g.segs[0][1] - mid) / total, col = lerpHex(g.stops, t);
      const grp = svgEl("g", { class: "seg", "data-key": ring + i, "data-season": season,
        style: `--dx:${Math.cos((mid * Math.PI) / 180).toFixed(3)};--dy:${Math.sin((mid * Math.PI) / 180).toFixed(3)}` }, svg);
      grp._info = { ring, season, when };
      svgEl("path", { class: "arc", d: arcD(g, g.r, a0, a1), stroke: col, "stroke-width": 40, fill: "none" }, grp);
      if (i === 0) svgEl("circle", { cx: pt(g, g.r, a0)[0], cy: pt(g, g.r, a0)[1], r: 20, fill: col }, grp);
      if (i === g.segs.length - 1) svgEl("circle", { cx: pt(g, g.r, a1)[0], cy: pt(g, g.r, a1)[1], r: 20, fill: col }, grp);
      const span = Math.abs(a0 - a1);
      if (span > 14) {
        const [ix, iy] = pt(g, g.r, mid), dark = t > 0.5;
        const ico = svgEl("g", { class: "ico", transform: `translate(${(ix - 11).toFixed(1)} ${(iy - 11).toFixed(1)}) scale(.92)`,
          fill: "none", stroke: dark ? "#F2EAE3" : "#171310", "stroke-width": 2.3, "stroke-linecap": "round", "stroke-linejoin": "round" }, grp);
        ico.innerHTML = ICON[season];
      }
      grp.addEventListener("mouseenter", () => { wheelHover = grp; if (S) wheelState(S.room); });
      grp.addEventListener("mouseleave", () => { wheelHover = null; if (S) wheelState(S.room); });
      grp.addEventListener("click", () => {
        wheelNote = null;
        wheelSel = grp.dataset.key;
        try { localStorage.setItem("wheelSel", wheelSel); } catch (e) { /* ignore */ }
        if (ring === "earth") cmd("date", EARTH_START[i]);   // the date carries the season
        else cmd("season", season);
        if (S) wheelState(S.room, season);
      });
    });
    for (const a of g.ticks) {
      const [x0, y0] = pt(g, g.r - 20, a), [x1, y1] = pt(g, g.r + 21, a);
      svgEl("path", { class: "tick", d: `M${x0} ${y0}L${x1} ${y1}`, stroke: "#171310", "stroke-width": 3 }, svg);
    }
  }
  // the surface stay on Mars (opposition class: ~30 sols) — its own piece, it lifts off the ring
  const sa = 41.6 * Math.PI / 180;
  const stay = svgEl("g", { class: "stay-g", "data-p": "stay", style: `--dx:${Math.cos(sa).toFixed(3)};--dy:${Math.sin(sa).toFixed(3)}` }, svg);
  svgEl("path", { class: "stay", d: "M433.077 410.105C428.618 415.749 423.842 421.134 418.773 426.235", stroke: "url(#stay)", "stroke-width": 40, "stroke-linecap": "round", fill: "none" }, stay);
  stay.addEventListener("click", () => noteWheel("stay"));
  for (const [k, cx, cy, r, f] of [["mars", 144, 136, 11, "url(#p-mars)"], ["earth", 190, 181, 16, "url(#p-earth)"]]) {
    svgEl("circle", { cx, cy, r: r + 10, fill: "transparent", class: "planet-hit" }, svg).addEventListener("click", () => noteWheel(k));
    svgEl("circle", { cx, cy, r, fill: f, class: "planet", "data-p": k }, svg).addEventListener("click", () => noteWheel(k));
  }
  const here = svgEl("g", { id: "w-here" }, svg);
  svgEl("path", { id: "w-here-line", stroke: "#F2EAE3", "stroke-width": 4, "stroke-linecap": "round" }, here);
  svgEl("circle", { id: "w-here-dot", r: 7, fill: "#F2EAE3", stroke: "#211C17", "stroke-width": 3 }, here);
  svgEl("path", { id: "w-here-hit", stroke: "transparent", "stroke-width": 26, "stroke-linecap": "round" }, here);
  here.addEventListener("mouseenter", () => { hereHover = true; if (S) wheelState(S.room); });
  here.addEventListener("mouseleave", () => { hereHover = false; if (S) wheelState(S.room); });
}
function wheelState(r, pending) {
  const svg = $("wheel");
  if (!svg.firstChild) buildWheel();
  const season = pending || r.season;
  if (r.date_real && wheelSel) { wheelSel = null; try { localStorage.removeItem("wheelSel"); } catch (e) { /* ignore */ } }
  let sel = wheelSel && svg.querySelector(`.seg[data-key="${wheelSel}"]`);
  if (!pending && r.date && (!sel || sel.dataset.key.startsWith("earth"))) {   // the Earth segment that holds the room's date
    let i = 0;
    while (i < EARTH_START.length - 1 && r.date >= EARTH_START[i + 1]) i++;
    const byDate = svg.querySelector(`.seg[data-key="earth${i}"]`);
    if (byDate && byDate.dataset.season === season) sel = byDate;
  }
  if (!sel || sel.dataset.season !== season) sel = svg.querySelector(`.seg[data-key^="earth"][data-season="${season}"]`);
  $$(".seg", svg).forEach((g) => g.classList.toggle("sel", g === sel));
  svg.classList.toggle("has-sel", !!sel);
  if (r.date) {                                   // the room's date as a line across both rings
    const a = dateAngle(r.date), E = RING.earth, Mr = RING.mars;
    const [x0, y0] = pt(E, E.r - 26, a), [x1, y1] = pt(Mr, Mr.r + 28, a), [dx, dy] = pt(Mr, Mr.r + 36, a);
    $("w-here-line").setAttribute("d", `M${x0.toFixed(1)} ${y0.toFixed(1)}L${x1.toFixed(1)} ${y1.toFixed(1)}`);
    $("w-here-dot").setAttribute("cx", dx.toFixed(1)); $("w-here-dot").setAttribute("cy", dy.toFixed(1));
    $("w-here-hit").setAttribute("d", $("w-here-line").getAttribute("d"));
  }
  if (hereHover && r.date) {
    const d = new Date(r.date + "T12:00:00");
    $("w-sub").textContent = "You are here";
    $("w-name").textContent = `Day ${r.mission_day}`;
    $("w-sub2").textContent = d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "long", year: "numeric" });
    $("w-sub3").textContent = `${cap(r.season)} in the room${r.date_real ? " · today" : " · date set by hand"}`;
    return;
  }
  if (wheelNote && !wheelHover) {
    const [a, b, c, d] = NOTES[wheelNote];
    $("w-sub").textContent = a; $("w-name").textContent = b; $("w-sub2").textContent = c; $("w-sub3").textContent = d;
    return;
  }
  $$("#wheel [data-p]").forEach((p) => p.classList.remove("on"));
  const show = wheelHover || sel;
  if (!show) return;
  const i = show._info, isSel = show === sel;
  $("w-sub").textContent = i.ring === "earth" ? "Earth season" : "Mars season";
  $("w-name").textContent = cap(i.season);
  $("w-sub2").textContent = i.when;
  $("w-sub3").textContent = isSel ? `in the room · dawn ${fmtH(r.dawn_h)} · dusk ${fmtH(r.dusk_h)}` : "click: set the room's season";
}

// ---- events: a small timeline, oldest left → newest right
const events = [];
let feedInit = false, lastEv = null;
function evText(e) {
  switch (e.type) {
    case "accent": return [C.middle, label(e.name)];
    case "moment": return [C.top, e.moment];
    case "start": return [C.top, `start · ${e.reason}`];
    case "stop": return [C.alert, "stop"];
    case "presence": return [C.ground, e.present ? "someone came" : "nobody here"];
    case "hit": case "hum": return [C.top, e.accepted ? `${e.type} → layer` : e.type];
    case "tap": return [C.top, "tap"];
    case "scenario": return [C.text3, label(e.name)];
    case "trace": return [C.text3, `jam kept · ${e.layers}`];
    case "power": return [e.on ? C.middle : C.alert, e.on ? "room on" : "room off"];
    case "note": return [C.text3, e.text];
    default: return [C.text3, e.type];
  }
}
function onEvent(e) {
  if (e.type === "onset") return;
  events.unshift(e);
  events.length = Math.min(events.length, 24);
  lastEv = e;
  renderFeed();
}
// events sit on the same 0–24 h axis as the circadian curve (room clock); labels alternate above/below,
// a label that has no room is left out (the dot stays, its text is the tooltip)
function evHour(e) {
  if (e.h != null) return e.h;
  const d = new Date(e.at * 1000), real = d.getHours() + d.getMinutes() / 60;
  return S ? (((real + S.room.hour - S.room.real_hour) % 24) + 24) % 24 : real;
}
function renderFeed() {
  const list = $("ev-list"), W = list.offsetWidth || 600, now = Date.now() / 1000;
  const items = events.filter((e) => now - e.at < 86400).map((e) => ({ e, h: evHour(e) })).sort((a, b) => a.h - b.h);
  const end = [-1e9, -1e9];
  const html = items.map(({ e, h }) => {
    const [col, txt] = evText(e), x = (h / 24) * W, w = txt.length * 6.4 + 34;
    const t = new Date(e.at * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
    let row = end[0] <= end[1] ? 0 : 1;
    if (end[row] > x - w / 2 + 4) row = -1;
    if (row >= 0) end[row] = x + w / 2;
    const lab = row >= 0 ? `<span>${txt}<small>${fmtH(h)}</small></span>` : "";
    const edge = x < w / 2 ? " el" : x > W - w / 2 ? " er" : "";     // labels at the edges grow inwards
    return `<div class="ev r${row}${edge}${e === lastEv ? " new" : ""}" style="left:${((h / 24) * 100).toFixed(3)}%" title="${fmtH(h)} room · ${t} real · ${txt}"><i class="dot" style="background:${col}"></i>${lab}</div>`;
  }).join("");
  setHTML(list, html);
}
let evOff = false;
try { evOff = localStorage.getItem("evOff") === "1"; } catch (e) { /* private window */ }
$("ev-off").checked = evOff;
$("feed").classList.toggle("ev-hidden", evOff);
$("ev-off").addEventListener("change", (e) => {
  evOff = e.target.checked;
  $("feed").classList.toggle("ev-hidden", evOff);
  try { localStorage.setItem("evOff", evOff ? "1" : "0"); } catch (err) { /* ignore */ }
});

// ================================================================== NODE
// The room node (node_mvp.svg, booklet p. 42, wall piece as built): hover / tap a piece -> what it does.
// online / offline is only a small line; the drawing never changes with it.
const NODE_PARTS = {
  wall: { t: "Ground", sub: "Wall piece", dev: "wall",
    d: "A 3D-printed light row on an aluminium rail that rises right behind the table: wall and table are one piece. Its light follows the room’s day and the seasons, the calm ground every scenario builds on. The tablet on its ledge shows the room clock; inside, the wall unit carries a second radar." },
  table: { t: "Middle", sub: "Table edge", dev: "strip1",
    d: "LEDs along the table edge carry the accents: weather, sounds and the colour of the season. A microphone in the table listens; in Morning Jam it records the crew’s rhythm." },
  ring: { t: "Top", sub: "Ring lamp", dev: "top",
    d: "The spotlight for moments. Its radar senses how close people are: the closer you come, the more the room answers." },
};
const NODE_INTRO = `<h3>One room, one node</h3><p>Three layers of light: the <b>ground</b> on the wall, the <b>middle</b> on the table edge, the <b>top</b> in the ring lamp.</p>
  <p class="muted">The host laptop runs light, sound, sensors and this page over its own Wi-Fi. Hover or tap a piece.</p>`;
let nodeHover = null, nodeLock = null;
function nodeStatus(p) {
  const w = p.dev && S && (S.devices.wled || []).find((x) => x.id === p.dev);
  return w ? `<p class="node-st${w.ok ? "" : " down"}"><i></i>${w.ok ? "online" : "offline"}</p>` : "";
}
function renderNode() {
  const k = nodeHover || nodeLock, p = NODE_PARTS[k];
  $$("#node-art [data-part]").forEach((e) => e.classList.toggle("on", e.dataset.part === k));
  setHTML($("node-info"), p ? `<h3>${p.t} · <span class="muted">${p.sub}</span></h3><p>${p.d}</p>${nodeStatus(p)}` : NODE_INTRO);
}
function nodeState() { if (page === "node") renderNode(); }
fetch("/static/node_mvp.svg?v=50").then((r) => r.text()).then((t) => {
  const art = $("node-art");
  art.innerHTML = t;
  $$("[data-part]", art).forEach((e) => {
    const k = e.dataset.part;
    e.addEventListener("mouseenter", () => { nodeHover = k; renderNode(); });
    e.addEventListener("mouseleave", () => { nodeHover = null; renderNode(); });
    e.addEventListener("click", (ev) => { ev.stopPropagation(); nodeLock = nodeLock === k ? null : k; renderNode(); });
  });
  document.addEventListener("click", (e) => { if (nodeLock && !e.target.closest("#node-art")) { nodeLock = null; renderNode(); } });
  renderNode();
}).catch(() => {});

// ================================================================== SCENARIOS
// Playing a scenario turns its card into a stage (¾ of the page): where it is (moments), the loop
// (beat grid, taps and hums as they join, the playhead), what plays — the other cards step aside.
const CARD = {};
const PLAY = '<svg viewBox="0 0 24 24"><path d="M8 5.5v13l10-6.5z"/></svg>', STOP = '<svg viewBox="0 0 24 24"><rect x="6.5" y="6.5" width="11" height="11" rx="2"/></svg>';
function buildCards(s) {
  const box = $("cards");
  box.innerHTML = "";
  s.scenarios.forEach((sc, i) => {
    const c = document.createElement("div");
    c.className = "tile card";
    const sims = (SIMS[sc.name] || []).map(([k, t]) => `<button class="btn" data-sim="${k}">${t}</button>`).join("");
    c.innerHTML = `<div class="card-top"><div class="num">${i + 1}</div><button class="play" data-act="toggle" title="Start">${PLAY}</button></div>
      <h2>${sc.title}</h2><div class="desc">${SCEN[sc.name] || ""}</div><div class="stat"></div>
      <div class="stage">
        <div class="story"><b>${(STORY[sc.name] || [])[0] || ""}</b><p>${(STORY[sc.name] || [])[1] || ""}</p><span>${(STORY[sc.name] || [])[2] || ""}</span></div>
        <div class="phases"></div>
        <div class="bigloop"><div class="bl-beats"></div><div class="bl-rows"></div>
          <div class="bl-live"><svg viewBox="0 0 ${LIVE_N} 1" preserveAspectRatio="none"></svg></div><div class="playhead"></div>
          <div class="bl-empty">no loop in this moment</div></div>
        <div class="season-view"></div>
        <div class="bl-info"><span class="bl-left"></span><span class="bl-right"></span></div>
      </div>
      <div class="try"><div class="label">Try it</div><div class="row">${sims}</div></div><div class="extra"></div>`;
    box.appendChild(c);
    const extra = c.querySelector(".extra");
    if (sc.name === "morning_jam") {
      extra.innerHTML = `<div class="gate-head"><span>Table mic</span><span class="rec">● joins the loop</span></div>
        <div class="gate" title="Drag the line: anything louder joins the loop"><i></i><b></b>
          <input type="range" min="0" max="1" step="0.002" aria-label="Table mic threshold"></div>
        <div class="gate-hint">louder than the line joins the loop · drag it left to catch humming and talking</div>`;
      const g = extra.querySelector(".gate input");
      g.addEventListener("input", () => { gateDrag = true; cmd("mic_threshold", gateVal(+g.value)); extra.querySelector(".gate b").style.left = g.value * 100 + "%"; });
      g.addEventListener("change", () => (gateDrag = false));
    } else if (sc.name === "spring_cleaning") {
      extra.innerHTML = `<div class="spring-sounds"></div>`;
    } else if (sc.name === "miss_you_sis") {
      extra.innerHTML = `<div>Postcards are released from Earth — here: by you.</div>`;
    }
    c.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b || !S) return;
      if (b.dataset.sim) return sim(b.dataset.sim);
      if (b.dataset.snd && S && S.spring) return cmd("spring_sound", { name: b.dataset.snd, on: !S.spring.sounds[b.dataset.snd] });
      if (b.dataset.act !== "toggle") return;
      if (S.running && S.scenario === sc.name) return cmd("stop");
      if (S.scenario !== sc.name) { cmd("scenario", sc.name); setTimeout(() => cmd("start"), S.running ? 2800 : 300); }
      else cmd("start");
    });
    const q = (sel) => c.querySelector(sel);
    CARD[sc.name] = { el: c, stat: q(".stat"), play: q(".play"), snd: q(".spring-sounds"), gate: q(".gate"), rec: q(".rec"),
      phases: q(".phases"), loop: q(".bigloop"), beats: q(".bl-beats"), rows: q(".bl-rows"), live: q(".bl-live svg"),
      empty: q(".bl-empty"), season: q(".season-view"), left: q(".bl-left"), right: q(".bl-right") };
  });
}
function seasonView(c, s) {        // Spring Cleaning: one card per season with its sounds (18.10: stripped to the effect)
  const sp = s.spring;
  if (!sp) return;
  const order = (sp.rows || []).map((r) => r.season), cur = Math.max(0, order.indexOf(sp.season));
  const hh = `${String(Math.floor(sp.h)).padStart(2, "0")}:${String(Math.floor((sp.h % 1) * 60)).padStart(2, "0")}`;
  const act = sp.near || 0, here = act > 0.05;      // activation from the radars: 0 nobody near … 1 up close
  const chip = (k) => `<button class="btn${sp.sounds[k] ? " primary" : ""}" data-snd="${k}">${SPRING_LABEL[k] || k}</button>`;
  if (!c.sv) {                         // built once; afterwards only classes, texts and the chips change
    c.sv = { passes: sp.passes };
    c.season.innerHTML = `<div class="si">
      <div class="si-top"><span class="si-hint"></span><span class="si-clock"><span class="si-day"></span><span class="si-time"></span></span></div>
      <div class="si-cards">${sp.rows.map((r) => `<div class="si-card" data-season="${r.season}"><div class="si-halo"></div>
        <div class="si-head">${seasonIcon(r.season)}<span>${cap(r.season)}</span></div>
        ${(sp.phases || {})[r.season] ? `<div class="si-phases">${sp.phases[r.season].map((ph) => `<span>${ph}</span>`).join("")}</div>` : ""}
        <div class="si-k">Ground</div><div class="si-chips" data-g></div>
        <div class="si-k">Accent</div><div class="si-chips" data-a></div></div>`).join("")}</div>
      <div class="si-rescue"><button class="btn si-mode" data-sim="mode"></button>${(SIMS.spring_cleaning || []).map(([k, lab]) => `<button class="btn" data-sim="${k}">${lab}</button>`).join("")}</div></div>`;
    for (const k of ["hint", "day", "time"]) c.sv[k] = c.season.querySelector(".si-" + k);
    c.sv.root = c.season.querySelector(".si"); c.sv.cards = [...c.season.querySelectorAll(".si-card")];
  }
  const v = c.sv;
  v.cards.forEach((el, k) => {
    const on = k === cur;
    if (on && sp.passes > v.passes) { el.classList.remove("pass"); void el.offsetWidth; el.classList.add("pass"); }
    el.classList.toggle("on", on); el.classList.toggle("done", k < cur);
    el.querySelectorAll(".si-phases span").forEach((ph, n) => { ph.classList.toggle("on", on && n === sp.phase); ph.classList.toggle("done", k < cur || (on && n < sp.phase)); });
    el.style.setProperty("--act", on ? act.toFixed(2) : "0");
    setHTML(el.querySelector("[data-g]"), sp.rows[k].general.map(chip).join(""));
    setHTML(el.querySelector("[data-a]"), sp.rows[k].accent.map(chip).join(""));
  });
  v.passes = sp.passes;
  v.root.classList.toggle("sim", !!sp.sim);
  const scripted = sp.mode === "scripted";
  const mb = c.season.querySelector(".si-mode");
  if (mb) { mb.textContent = scripted ? "Mode: Scripted" : "Mode: Interactive"; mb.classList.toggle("primary", scripted); }
  c.season.querySelectorAll('.si-rescue [data-sim="someone"], .si-rescue [data-sim="empty"]').forEach((b) => (b.hidden = scripted));
  v.hint.textContent = `${sp.hint || ""}${sp.sim ? " · days are passing …" : act > 0.7 ? "" : here ? " · come closer" : " · resting"}${sp.staged && !scripted ? " · held" : sp.armed ? " · waiting for the radar to clear" : ""}${scripted && sp.script_left != null ? ` · scripted ${sp.script_left} s` : ""}`;
  v.day.textContent = `Mission day ${sp.mission_day}`;
  v.time.textContent = hh;
}
function postcardView(c, s) {        // I Miss You, Sis: a simple postcard view (18.10, first draft)
  const pc = s.postcard || {}, run = s.running && s.scenario === "miss_you_sis";
  const steps = [["arrived", "Arrived"], ["rome", "Rome"], ["lena", "Lena"], ["home", "Home"]];
  const cur = run ? steps.findIndex(([k]) => k === s.moment) : -1;
  const text = !run ? "Waiting for a postcard from Earth" : { arrived: "A postcard from Earth. Pick it up and hold it",
    rome: "Hold it: Lena's evening in Rome", lena: "Lena", home: "Back in the habitat" }[s.moment] || "";
  if (!c.pv) {
    c.pv = true;
    c.season.innerHTML = `<div class="pv"><div class="pv-card"><div class="pv-stamp">Earth</div>
      <svg viewBox="0 0 24 24" class="pv-icon"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
      <div class="pv-text"></div><div class="pv-bar"><b></b></div><div class="pv-held"></div></div>
      <div class="pv-steps"></div>
      <div class="si-rescue">${(SIMS.miss_you_sis || []).map(([k, lab]) => `<button class="btn" data-sim="${k}">${lab}</button>`).join("")}</div></div>`;
  }
  const q = (x) => c.season.querySelector(x);
  q(".pv").classList.toggle("on", run);
  q(".pv-text").textContent = text;
  q(".pv-bar b").style.width = `${Math.round((pc.rome || 0) * 100)}%`;
  q(".pv-held").textContent = run ? (pc.held ? "the card is held" : "the card lies on the table") : "";
  setHTML(q(".pv-steps"), steps.map(([, lab], i) => `<span class="${i === cur ? "on" : i < cur ? "done" : ""}">${lab}</span>`).join("<i></i>"));
}
function stageState(c, sc, s) {
  c.el.classList.toggle("seasonal", sc.name === "spring_cleaning" || sc.name === "miss_you_sis");
  if (sc.name === "spring_cleaning") seasonView(c, s);
  c.el.classList.toggle("postal", sc.name === "miss_you_sis");
  if (sc.name === "miss_you_sis") postcardView(c, s);
  const moments = sc.moments || [], cur = moments.indexOf(s.moment);
  const icon = (m) => (sc.name === "spring_cleaning" ? seasonIcon(m) : "");
  setHTML(c.phases, moments.map((m, i) => `<div class="ph${i === cur ? " on" : i < cur ? " done" : ""}"><i></i><span>${icon(m)}${m}</span></div>`).join("") +
    `<div class="ph-time">${mmss(s.elapsed)}</div>`);
  const hasLoop = s.beds.length > 0 || s.layers.length > 0;
  c.loop.classList.toggle("idle", !hasLoop);
  c.loop.style.setProperty("--beats", s.beats || 8);
  setHTML(c.beats, Array.from({ length: s.beats || 8 }, (_, i) => `<span style="left:${((i / (s.beats || 8)) * 100).toFixed(3)}%">${i + 1}</span>`).join(""));
  // rows: one recorded loop each, drawn as its waveform (newest at the bottom); the live lane below it
  // shows what the table mic hears in the loop now playing
  const rows = s.layers.filter((l) => l.env);
  const strip = (l) => {
    const n = l.env.length, top = [], bot = [];
    l.env.forEach((e, i) => { const h = Math.max(0.015, e * 0.48); top.push(`${i + 0.5},${(0.5 - h).toFixed(3)}`); bot.unshift(`${i + 0.5},${(0.5 + h).toFixed(3)}`); });
    const op = l.fading ? 0.25 : 1 - Math.min(0.6, (Math.max(0, l.age) / Math.max(1, l.life)) * 0.6);
    return `<div class="bl-row${l.age < 1 ? " new" : ""}" style="opacity:${op.toFixed(2)}"><b>${l.id}</b>` +
      `<svg viewBox="0 0 ${n} 1" preserveAspectRatio="none"><path d="M0,0.5 L${top.join(" L")} L${n},0.5 L${bot.join(" L")} Z"/></svg></div>`;
  };
  setHTML(c.rows, rows.slice(-10).map(strip).join(""));
  const top = ((s.sounds || {}).top || []).map((x) => label(x.name));
  c.left.textContent = hasLoop ? `${s.bpm} BPM · ${s.beats} beats · ${rows.length} row${rows.length === 1 ? "" : "s"}` : (s.hint || "");
  c.right.textContent = top.length ? `playing: ${top.join(", ")}` : "";
}
function scenState(s) {
  const sig = JSON.stringify(s.scenarios);
  if (sig !== sigScen) { sigScen = sig; buildCards(s); }
  $("cards").classList.toggle("focus", !!s.running && !$("cards").dataset.only);
  for (const sc of s.scenarios) {
    const c = CARD[sc.name];
    if (!c) continue;
    const running = s.running && s.scenario === sc.name;
    c.el.classList.toggle("run", running);
    setHTML(c.stat, running ? `<b>${s.moment}</b> · ${mmss(s.elapsed)}<br>${s.hint || ""}` : s.scenario === sc.name ? "selected · ready" : "ready");
    setHTML(c.play, running ? STOP : PLAY);
    c.play.title = running ? "Stop" : "Start";
    c.el.classList.toggle("sel", sc.name === $("cards").dataset.only);
    if (running || c.el.classList.contains("sel")) stageState(c, sc, s);
    if (c.snd && s.spring) setHTML(c.snd, soundTable(s.spring));
  }
}

// ------------------------------------------------------------------ meter + light
// table mic: level and threshold on one log scale (0.0003 … 0.1 RMS), so quiet humming and loud taps both fit
const GATE_LO = 0.0003, GATE_HI = 0.1, LIVE_N = 160;
const gatePos = (x) => Math.max(0, Math.min(1, Math.log(Math.max(x, 1e-9) / GATE_LO) / Math.log(GATE_HI / GATE_LO)));
const gateVal = (p) => GATE_LO * Math.pow(GATE_HI / GATE_LO, p);
let gateDrag = false, live = { bins: new Float32Array(LIVE_N), last: -1 };
function liveLane(c, m) {
  if (!c.live) return;
  if (m.pos == null || !m.cap) { live.bins.fill(0); live.last = -1; setHTML(c.live, ""); return; }
  const i = Math.min(LIVE_N - 1, Math.floor(m.pos * LIVE_N));
  if (i < live.last) live.bins.fill(0);                      // a new loop starts: a fresh lane
  for (let j = live.last < 0 || i < live.last ? i : live.last + 1; j <= i; j++) live.bins[j] = m.lvl;
  live.last = i;
  let html = "";
  live.bins.forEach((v, j) => { if (v > 0) { const h = Math.max(0.03, gatePos(v)) * 0.48; html += `<rect x="${j}" y="${(0.5 - h).toFixed(3)}" width="0.9" height="${(2 * h).toFixed(3)}"${v > m.gate ? ' class="over"' : ""}/>`; } });
  c.live.innerHTML = html;
}
function onMeter(m) {
  M = m;
  const jam = CARD.morning_jam;
  if (jam && jam.gate && m.lvl != null) {
    const over = m.cap && m.lvl > m.gate;
    jam.gate.querySelector("i").style.width = gatePos(m.lvl) * 100 + "%";
    if (!gateDrag) { jam.gate.querySelector("b").style.left = gatePos(m.gate) * 100 + "%"; jam.gate.querySelector("input").value = gatePos(m.gate); }
    jam.gate.classList.toggle("over", over); jam.rec.classList.toggle("on", over);
    liveLane(jam, m);
  }
  $$(".loop .playhead, .bigloop .playhead").forEach((p) => { p.style.display = m.pos == null ? "none" : "block"; if (m.pos != null) p.style.left = m.pos * 100 + "%"; });
}
function onLight(l) {
  L = l;
}

// ------------------------------------------------------------------ turn off
$("power-btn").onclick = () => { if (S && S.power === false) return; $("confirm").hidden = false; };
$("confirm-no").onclick = () => ($("confirm").hidden = true);
$("confirm-restart").onclick = () => { $("confirm").hidden = true; cmd("restart_units", true); };
$("confirm-yes").onclick = () => { $("confirm").hidden = true; cmd("power", false); };
$("turn-on").onclick = () => cmd("power", true);
document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("confirm").hidden = true; });
window.addEventListener("resize", () => { if (L) onLight(L); if (S) drawCurve(S.room); renderFeed(); });

route();
connect();
