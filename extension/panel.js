/* The panel. Lives in a shadow root so the portal's stylesheet cannot reach it,
 * and attaches to <html> rather than <body> because PeopleSoft rewrites body
 * content on every AJAX update.
 *
 * Shares scope with content.js - they are one content script entry.
 */

const IS_TOP = window.top === window;
let claimedByFrame = false;
let host = null;
let root = null;
let state = null;

const PANEL_CSS = `
:host { all: initial; }
* { box-sizing: border-box; }

.wrap {
  position: fixed; top: 0; right: 0; bottom: 0;
  width: 400px; max-width: 100vw;
  display: flex; flex-direction: column;
  background: var(--surface);
  color: var(--text);
  font: 400 13.5px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  border-left: 1px solid var(--line);
  box-shadow: -18px 0 48px rgba(12, 16, 24, .16);
  z-index: 2147483647;
  --surface: #ffffff;
  --raise:   #f7f8fa;
  --text:    #14161a;
  --muted:   #676e7b;
  --line:    #e6e8ec;
  --accent:  #c8102e;
  --accent-hover: #a60d26;
  --accent-soft:  #fdeaed;
  --ok: #0a7d4f;
}
@media (prefers-color-scheme: dark) {
  .wrap {
    --surface: #16181d;
    --raise:   #1e2128;
    --text:    #e9ecf1;
    --muted:   #9aa3b2;
    --line:    #2a2e37;
    --accent:  #ff5a70;
    --accent-hover: #ff7e90;
    --accent-soft:  #2a1418;
    --ok: #34d399;
  }
}

header {
  display: flex; align-items: center; gap: 10px;
  padding: 16px 18px; border-bottom: 1px solid var(--line);
}
.mark {
  width: 26px; height: 26px; border-radius: 7px; flex: none;
  background: var(--accent); color: #fff;
  display: grid; place-items: center;
  font-size: 13px; font-weight: 700;
}
h1 { margin: 0; font-size: 14.5px; font-weight: 640; letter-spacing: -.01em; }
.sub { margin: 1px 0 0; font-size: 11.5px; color: var(--muted); }
.x {
  margin-left: auto; border: 0; background: transparent; cursor: pointer;
  color: var(--muted); font-size: 19px; line-height: 1; padding: 4px 6px;
  border-radius: 6px;
}
.x:hover { background: var(--raise); color: var(--text); }

.body { flex: 1; overflow-y: auto; padding: 18px; }
footer { padding: 14px 18px; border-top: 1px solid var(--line); background: var(--raise); }

h2 { margin: 0 0 6px; font-size: 15px; font-weight: 620; letter-spacing: -.01em; }
p  { margin: 0 0 12px; color: var(--muted); }
.note { font-size: 11.5px; color: var(--muted); margin-top: 10px; }

button.primary {
  width: 100%; padding: 11px 14px; border: 0; border-radius: 9px;
  background: var(--accent); color: #fff; font-size: 13.5px; font-weight: 600;
  cursor: pointer; font-family: inherit;
}
button.primary:hover { background: var(--accent-hover); }
button.primary:disabled { opacity: .5; cursor: default; }
button.ghost {
  width: 100%; padding: 9px 14px; margin-top: 8px;
  border: 1px solid var(--line); border-radius: 9px;
  background: transparent; color: var(--text);
  font-size: 13px; cursor: pointer; font-family: inherit;
}
button.ghost:hover { background: var(--raise); }
button:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.bar { height: 5px; border-radius: 99px; background: var(--line); overflow: hidden; margin: 14px 0 8px; }
.bar > i { display: block; height: 100%; background: var(--accent); transition: width .3s ease; }
.count { font-size: 12px; color: var(--muted); display: flex; justify-content: space-between; }

.card { border: 1px solid var(--line); border-radius: 11px; padding: 13px; margin-bottom: 11px; background: var(--surface); }
.chip {
  display: inline-block; padding: 2px 7px; border-radius: 5px;
  background: var(--accent-soft); color: var(--accent);
  font-size: 11px; font-weight: 640; letter-spacing: .01em;
}
.cname { font-weight: 560; margin: 7px 0 9px; }
.types { display: flex; flex-wrap: wrap; gap: 6px 14px; }
label.tick { display: flex; align-items: center; gap: 7px; font-size: 12.5px; cursor: pointer; }
input[type=checkbox] { accent-color: var(--accent); width: 15px; height: 15px; cursor: pointer; }

.opt { border: 1px solid var(--line); border-radius: 10px; padding: 11px; margin-bottom: 8px; }
.opt .when { font-size: 12px; color: var(--muted); margin-top: 3px; }
.opt button { width: 100%; margin-top: 9px; padding: 8px; border-radius: 8px;
  border: 1px solid var(--accent); background: transparent; color: var(--accent);
  font-weight: 600; font-size: 12.5px; cursor: pointer; font-family: inherit; }
.opt button:hover { background: var(--accent); color: #fff; }

.rem { display: flex; align-items: center; gap: 9px; margin-top: 14px; font-size: 13px; }
.rem input { width: 62px; padding: 7px 9px; border: 1px solid var(--line); border-radius: 8px;
  background: var(--surface); color: var(--text); font: inherit; }

ol { margin: 10px 0 0; padding-left: 19px; color: var(--muted); }
ol li { margin-bottom: 7px; }
.tick-big { width: 42px; height: 42px; border-radius: 50%; background: var(--ok); color: #fff;
  display: grid; place-items: center; font-size: 21px; margin-bottom: 12px; }
code { background: var(--raise); padding: 1.5px 5px; border-radius: 5px; font-size: 12px;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
.err { color: var(--accent); }
`;

// One integer, remembered per portal origin. Page localStorage does this with
// no extension permission at all, which is one less thing for store review to
// weigh. It can throw where site data is blocked, hence the guards.
const REMINDER_KEY = "sutd-calendar-bot-reminder";

function loadReminder() {
  try {
    const raw = localStorage.getItem(REMINDER_KEY);
    if (raw === null) return 15;
    const v = Number(raw);
    return Number.isFinite(v) && v >= 0 ? v : 15;
  } catch (e) {
    return 15;
  }
}

function saveReminder(v) {
  try {
    localStorage.setItem(REMINDER_KEY, String(v));
  } catch (e) {
    /* site data blocked; the setting just will not stick */
  }
}

function el(tag, attrs, kids) {
  const n = document.createElement(tag);
  if (attrs) {
    for (const k of Object.keys(attrs)) {
      if (k === "text") n.textContent = attrs[k];
      else if (k.startsWith("on")) n.addEventListener(k.slice(2), attrs[k]);
      else n.setAttribute(k, attrs[k]);
    }
  }
  for (const kid of kids || []) if (kid) n.appendChild(kid);
  return n;
}

function openPanel(initial) {
  if (host) {
    host.style.display = "";
    return;
  }
  host = document.createElement("div");
  host.id = "sutd-calendar-bot-host";
  root = host.attachShadow({ mode: "open" });
  root.appendChild(el("style", { text: PANEL_CSS }));
  root.appendChild(el("div", { class: "wrap", role: "dialog", "aria-label": "SUTD Calendar Bot" }));
  document.documentElement.appendChild(host);

  // PeopleSoft rewrites large parts of the DOM on every AJAX update. If the
  // panel gets swept up in that, put it back.
  new MutationObserver(() => {
    if (host && !host.isConnected) document.documentElement.appendChild(host);
  }).observe(document.documentElement, { childList: true, subtree: false });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && host && state && state.screen !== "scanning") closePanel();
  });

  state = { screen: initial || "start", progress: null, scan: null, clashes: [], clashIdx: 0,
            choices: {}, enabledTypes: {}, reminder: loadReminder(), error: null };
  render();
}

function closePanel() {
  if (host) host.remove();
  host = null;
  root = null;
  state = null;
}

function shell(title, sub, bodyKids, footerKids) {
  const wrap = root.querySelector(".wrap");
  wrap.textContent = "";
  wrap.appendChild(
    el("header", null, [
      el("div", { class: "mark", text: "S" }),
      el("div", null, [el("h1", { text: title }), el("p", { class: "sub", text: sub })]),
      el("button", { class: "x", "aria-label": "Close", onclick: closePanel, text: "×" }),
    ])
  );
  wrap.appendChild(el("div", { class: "body" }, bodyKids));
  if (footerKids) wrap.appendChild(el("footer", null, footerKids));
}

/* ------------------------------------------------------------------ screens */

function render() {
  if (!state) return;
  const s = state.screen;
  if (s === "wrongpage") return renderWrongPage();
  if (s === "start") return renderStart();
  if (s === "scanning") return renderScanning();
  if (s === "clash") return renderClash();
  if (s === "courses") return renderCourses();
  if (s === "done") return renderDone();
  if (s === "error") return renderError();
}

function renderWrongPage() {
  shell("SUTD Calendar Bot", "Not on the timetable page", [
    el("h2", { text: "Open your Weekly Schedule first" }),
    el("p", { text: "This works on the page that shows your timetable as a week grid." }),
    el("ol", null, [
      el("li", { text: "In the portal, go to Manage Classes." }),
      el("li", { text: "Open View My Weekly Schedule." }),
      el("li", { text: "Make sure the calendar grid is showing, then click the extension icon again." }),
    ]),
  ]);
}

function renderStart() {
  shell("SUTD Calendar Bot", "Ready", [
    el("h2", { text: "Turn this timetable into a calendar" }),
    el("p", { text: "Reads every week of your term straight off this page and builds a calendar file you can import into Google Calendar or Apple Calendar." }),
    el("p", { class: "note", text: "Takes about a minute. The page will flick through the weeks on its own - let it run and do not close this tab." }),
  ], [
    el("button", { class: "primary", text: "Scan my timetable", onclick: startScan }),
  ]);
}

function renderScanning() {
  const p = state.progress || { week: 0, max: 16, found: 0 };
  const pct = Math.round((p.week / p.max) * 100);
  shell("SUTD Calendar Bot", "Scanning", [
    el("h2", { text: "Reading your timetable" }),
    el("p", { text: "Leave this tab alone until it finishes." }),
    el("div", { class: "bar" }, [el("i", { style: "width:" + pct + "%" })]),
    el("div", { class: "count" }, [
      el("span", { text: "Week " + p.week + " of " + p.max }),
      el("span", { text: p.found + " classes found" }),
    ]),
  ]);
}

function renderClash() {
  const c = state.clashes[state.clashIdx];
  const n = state.clashes.length;
  const label = (ev) =>
    el("div", null, [
      el("span", { class: "chip", text: ev.code + " " + ev.section }),
      el("div", { class: "cname", text: ev.title }),
      el("div", { class: "when", text: (TYPE_MAPPING[ev.type] || ev.type) + " · " + ev.start_time + " - " + ev.end_time }),
      el("div", { class: "when", text: ev.location }),
    ]);

  const pick = (choice) => () => {
    state.choices[c.key] = choice;
    state.clashIdx++;
    state.screen = state.clashIdx >= n ? "courses" : "clash";
    if (state.screen === "courses") prepareCourses();
    render();
  };

  shell("SUTD Calendar Bot", "Clash " + (state.clashIdx + 1) + " of " + n, [
    el("h2", { text: "Two classes overlap" }),
    el("p", { text: "This happens on " + c.dates.length + " date" + (c.dates.length === 1 ? "" : "s") + " this term. Pick once and it applies to all of them." }),
    el("div", { class: "opt" }, [label(c.a), el("button", { text: "Keep this one", onclick: pick("a") })]),
    el("div", { class: "opt" }, [label(c.b), el("button", { text: "Keep this one", onclick: pick("b") })]),
  ], [
    el("button", { class: "ghost", text: "Keep both", onclick: pick("both") }),
  ]);
}

function prepareCourses() {
  state.enabledTypes = {};
  for (const course of state.scan.courses) {
    for (const t of course.types) state.enabledTypes[course.code + "|" + t] = true;
  }
}

function renderCourses() {
  const cards = state.scan.courses.map((course) =>
    el("div", { class: "card" }, [
      el("span", { class: "chip", text: course.code }),
      el("div", { class: "cname", text: course.name }),
      el("div", { class: "types" }, [...course.types].map((t) => {
        const key = course.code + "|" + t;
        const box = el("input", { type: "checkbox" });
        box.checked = state.enabledTypes[key] !== false;
        box.addEventListener("change", () => { state.enabledTypes[key] = box.checked; });
        return el("label", { class: "tick" }, [box, el("span", { text: TYPE_MAPPING[t] || t })]);
      })),
    ])
  );

  const remInput = el("input", { type: "number", min: "0", max: "120", id: "rem" });
  remInput.value = state.reminder;
  remInput.addEventListener("change", () => {
    state.reminder = Math.max(0, Number(remInput.value) || 0);
    saveReminder(state.reminder);
  });

  shell("SUTD Calendar Bot", state.scan.events.length + " classes · " + state.scan.weeksScanned + " weeks", [
    el("h2", { text: "Found " + state.scan.courses.length + " modules" }),
    el("p", { text: "Untick anything you do not want in your calendar." }),
    ...cards,
    el("div", { class: "rem" }, [
      el("label", { for: "rem", text: "Remind me" }),
      remInput,
      el("span", { text: "minutes before" }),
    ]),
    el("p", { class: "note", text: "Set to 0 for no reminders." }),
  ], [
    el("button", { class: "primary", text: "Download calendar", onclick: download }),
  ]);
}

// Builds "text <code>bit</code> text" without an innerHTML sink anywhere in
// the extension - nothing scraped from the portal can ever become markup.
function line(tag, cls, parts) {
  const n = el(tag, cls ? { class: cls } : null);
  for (const p of parts) {
    n.appendChild(typeof p === "string" ? document.createTextNode(p) : el("code", { text: p.code }));
  }
  return n;
}

function renderDone() {
  shell("SUTD Calendar Bot", "Done", [
    el("div", { class: "tick-big", text: "✓" }),
    el("h2", { text: "Calendar downloaded" }),
    line("p", null, ["Saved to your Downloads folder as ", { code: "SUTD_Calendar.ics" }, "."]),
    el("h2", { text: "Add it to Google Calendar" }),
    el("ol", null, [
      line("li", null, ["Open ", { code: "calendar.google.com" }, " on a computer."]),
      el("li", { text: "Click the gear icon, top right, then Settings." }),
      el("li", { text: "In the left menu click Import & export." }),
      line("li", null, ["Choose the ", { code: "SUTD_Calendar.ics" }, " file, pick which calendar to add it to, then click Import."]),
    ]),
    el("p", { class: "note", text: "On iPhone or Mac, just open the file and Apple Calendar will offer to add it." }),
  ], [
    el("button", { class: "ghost", text: "Close", onclick: closePanel }),
  ]);
}

function renderError() {
  shell("SUTD Calendar Bot", "Something went wrong", [
    el("h2", { class: "err", text: "Could not read your timetable" }),
    el("p", { text: state.error || "" }),
    el("p", { class: "note", text: "Make sure the weekly grid is on screen, then try again. If it keeps failing the portal layout may have changed." }),
  ], [
    el("button", { class: "primary", text: "Try again", onclick: () => { state.screen = "start"; render(); } }),
  ]);
}

/* ------------------------------------------------------------------ actions */

async function startScan() {
  state.screen = "scanning";
  state.progress = { week: 0, max: MAX_WEEKS, found: 0 };
  render();

  try {
    const scan = await scanTerm((p) => {
      state.progress = p;
      render();
    });

    if (!scan.events.length) {
      state.error = "No classes were found on this timetable. If this term is empty, page back to a term where you had classes and try again.";
      state.screen = "error";
      return render();
    }

    state.scan = scan;
    state.clashes = findClashes(scan.events);
    state.clashIdx = 0;
    state.choices = {};
    state.screen = state.clashes.length ? "clash" : "courses";
    if (state.screen === "courses") prepareCourses();
    render();
  } catch (err) {
    state.error = String((err && err.message) || err);
    state.screen = "error";
    render();
  }
}

function download() {
  const kept = applyClashChoices(state.scan.events, state.choices, state.clashes);
  const filtered = kept.filter((ev) => state.enabledTypes[ev.code + "|" + ev.type] !== false);
  if (!filtered.length) {
    state.error = "Everything is unticked, so there is nothing to export.";
    state.screen = "error";
    return render();
  }
  downloadIcs(buildIcs(filtered, state.reminder), "SUTD_Calendar.ics");
  state.screen = "done";
  render();
}

/* -------------------------------------------------------- frame arbitration */

// The toolbar click reaches every frame. Only the frame holding the schedule
// grid should act; the top frame waits to see whether anyone claimed it, and
// explains what to do if nobody did.
window.addEventListener("message", (e) => {
  if (e.data && e.data.__sutd === "claimed") claimedByFrame = true;
});

chrome.runtime.onMessage.addListener((msg) => {
  if (!msg || msg.type !== "SUTD_OPEN_PANEL") return;
  if (isScheduleFrame()) {
    try {
      window.top.postMessage({ __sutd: "claimed" }, "*");
    } catch (e) {
      /* cross-origin top frame; harmless */
    }
    openPanel();
  } else if (IS_TOP) {
    claimedByFrame = false;
    setTimeout(() => {
      if (!claimedByFrame) openPanel("wrongpage");
    }, 500);
  }
});
