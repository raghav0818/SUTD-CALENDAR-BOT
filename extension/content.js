/* SUTD Calendar Bot - runs inside the tab you are already logged into.
 *
 * Ported from the Selenium version (desktop-legacy/sutd_calendar_bot.py).
 * The parsing algorithm is unchanged and deliberately so - it is the part that
 * was proven against the real portal. What changed is that every DOM read here
 * is free and synchronous, where in Selenium each one was a network round trip.
 */

/* ---------------------------------------------------------------- constants */

const TYPE_MAPPING = {
  CBL: "Cohort Class",
  LEC: "Lecture",
  LAB: "Lab",
  TUT: "Tutorial",
  REC: "Recitation",
  TES: "Test/Exam",
};

const TIME_RE = /\d{1,2}:\d{2}[AP]M\s*-\s*\d{1,2}:\d{2}[AP]M/;
const TIME_PAIR_RE = /(\d{1,2}:\d{2}[AP]M)\s*-\s*(\d{1,2}:\d{2}[AP]M)/;
const CODE_RE = /^(\d{2}\s*\.\d{3})\s*-\s*(\w+)/;
const WEEK_RE = /Week of\s*(\d{1,2}\/\d{1,2}\/\d{4})/;
const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

// PeopleSoft appends a generated index to some ids (DERIVED_..._REFRESH_CAL$38$).
// Match on the stable prefix rather than pinning the suffix the way the Python did.
const SEL = {
  nextWeek: '[id^="DERIVED_CLASS_S_SSR_NEXT_WEEK"]',
  refresh: '[id^="DERIVED_CLASS_S_SSR_REFRESH_CAL"]',
  showTitle: '[id^="DERIVED_CLASS_S_SSR_DISP_TITLE"]',
  showInstr: '[id^="DERIVED_CLASS_S_SHOW_INSTR"]',
};

const MAX_WEEKS = 16;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ------------------------------------------------------------------- dates */

// Day arithmetic anchored at noon: midnight plus setDate() shifts a whole day
// in any timezone that runs DST. Singapore does not, but a student's laptop
// may be set to somewhere that does.
function addDays(date, n) {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 12);
  d.setDate(d.getDate() + n);
  return d;
}

function weekStartText(doc) {
  const d = doc || document;
  const m = WEEK_RE.exec((d.body && d.body.innerText) || "");
  return m ? m[1] : null;
}

function weekStartDate(doc) {
  const t = weekStartText(doc);
  if (!t) return null;
  const parts = t.split("/").map(Number);
  return new Date(parts[2], parts[1] - 1, parts[0], 12);
}

// "9:00AM" -> minutes since midnight
function toMinutes(t) {
  const m = /^(\d{1,2}):(\d{2})([AP])M$/.exec(String(t).trim());
  if (!m) return null;
  const h = (Number(m[1]) % 12) + (m[3] === "P" ? 12 : 0);
  return h * 60 + Number(m[2]);
}

/* ------------------------------------------------------------------ parsing */

// Day columns are matched by pixel geometry because rowspan makes cellIndex
// lie about which column a cell is actually sitting in.
function dayColumns(root) {
  const scope = root || document;
  const cols = [];
  for (const th of scope.querySelectorAll("th")) {
    const text = (th.innerText || "").trim();
    if (!DAY_NAMES.some((d) => text.includes(d))) continue;
    const r = th.getBoundingClientRect();
    if (r.width > 0) cols.push({ x: r.left, width: r.width });
  }
  cols.sort((a, b) => a.x - b.x);
  const out = [];
  for (const c of cols) {
    if (!out.length || Math.abs(c.x - out[out.length - 1].x) > 10) out.push(c);
  }
  return out;
}

function nearestDayIndex(td, cols) {
  const r = td.getBoundingClientRect();
  const centre = r.left + r.width / 2;
  let best = 0;
  let min = Infinity;
  cols.forEach((c, i) => {
    const dist = Math.abs(centre - (c.x + c.width / 2));
    if (dist < min) {
      min = dist;
      best = i;
    }
  });
  return best;
}

// One grid cell can hold two overlapping classes; PeopleSoft separates them
// with the literal words "Time Conflict".
function parseCellText(text, date) {
  const events = [];
  const chunks = String(text).split(/\bTime Conflict\b/i);
  for (const chunk of chunks) {
    const lines = chunk.split("\n").map((s) => s.trim()).filter(Boolean);
    if (!lines.length) continue;

    const timeIdx = lines.findIndex((l) => TIME_RE.test(l));
    // Need "code - section" and a type line sitting above the time line.
    if (timeIdx < 2) continue;

    const codeMatch = CODE_RE.exec(lines[0]);
    if (!codeMatch) continue;

    const times = TIME_PAIR_RE.exec(lines[timeIdx]);
    if (!times) continue;

    let instructors = lines.slice(timeIdx + 2).join(" ");
    if (instructors.indexOf("Instructors:") !== -1) {
      instructors = instructors
        .replace("Instructors:", "")
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
        .join(", ");
    }

    events.push({
      code: codeMatch[1].replace(/\s/g, ""),
      section: codeMatch[2],
      title: timeIdx > 2 ? lines.slice(1, timeIdx - 1).join(" ") : "Unknown Course",
      type: lines[timeIdx - 1],
      date: date,
      start_time: times[1],
      end_time: times[2],
      location: lines[timeIdx + 1] || "Unknown Location",
      instructors: instructors.trim() || "Staff",
    });
  }
  return events;
}

function parseCurrentWeek(root) {
  const scope = root || document;
  const start = weekStartDate(scope.ownerDocument || scope);
  if (!start) return null;

  const cols = dayColumns(scope);
  const events = [];
  // Broad `td` sweep, same as the Python. Nested cells get counted twice and
  // are removed by the dedupe below - cheaper and safer than guessing which
  // table on a PeopleSoft page is the real one.
  for (const td of scope.querySelectorAll("td")) {
    const text = (td.innerText || "").trim();
    if (!TIME_RE.test(text)) continue;
    const date = addDays(start, cols.length ? nearestDayIndex(td, cols) : 0);
    events.push(...parseCellText(text, date));
  }
  return { weekStart: start, events: events, dayColumns: cols.length };
}

function dedupe(events) {
  const seen = new Set();
  const out = [];
  for (const ev of events) {
    const key = [ev.code, ev.type, ev.date.toDateString(), ev.start_time].join("|");
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(ev);
  }
  return out;
}

function summariseCourses(events) {
  const courses = {};
  for (const ev of events) {
    if (!courses[ev.code]) {
      courses[ev.code] = { code: ev.code, name: ev.title, types: new Set() };
    }
    // A cell with no title line can land first; prefer a real name over the
    // placeholder rather than letting "Unknown Course" label the whole module.
    if (courses[ev.code].name === "Unknown Course" && ev.title !== "Unknown Course") {
      courses[ev.code].name = ev.title;
    }
    courses[ev.code].types.add(ev.type);
  }
  return Object.keys(courses)
    .sort()
    .map((k) => courses[k]);
}

/* --------------------------------------------------------------- navigation */

function isScheduleFrame() {
  return !!document.querySelector(SEL.nextWeek + ", " + SEL.refresh);
}

// PeopleSoft swaps content in with its own AJAX and fires no event we can hook,
// so wait for the DOM to stop changing instead of guessing a fixed sleep.
async function waitForSettle({ timeout = 20000, quiet = 600 } = {}) {
  const start = Date.now();
  let last = "";
  let lastChange = Date.now();
  while (Date.now() - start < timeout) {
    const now = document.body.innerHTML.length + "|" + (weekStartText() || "");
    if (now !== last) {
      last = now;
      lastChange = Date.now();
    } else if (Date.now() - lastChange > quiet) {
      return true;
    }
    await sleep(120);
  }
  return false;
}

// The grid only renders course titles and instructor names when these two boxes
// are ticked, and the parser reads both by line position - without them every
// cell is missing the lines the parser anchors on.
async function ensureDetailsShown() {
  let changed = false;
  for (const sel of [SEL.showTitle, SEL.showInstr]) {
    const box = document.querySelector(sel);
    if (box && !box.checked) {
      box.click();
      changed = true;
      await waitForSettle({ quiet: 400 });
    }
  }
  if (changed) {
    const refresh = document.querySelector(SEL.refresh);
    if (refresh) {
      refresh.click();
      await waitForSettle({ quiet: 500 });
    }
  }
}

async function gotoNextWeek() {
  const before = weekStartText();
  const btn = document.querySelector(SEL.nextWeek);
  if (!btn) return false;
  btn.click();
  const start = Date.now();
  while (Date.now() - start < 20000) {
    await sleep(150);
    const now = weekStartText();
    if (now && now !== before) {
      await waitForSettle({ quiet: 400 });
      return true;
    }
  }
  return false;
}

async function scanTerm(onProgress) {
  await ensureDetailsShown();

  const all = [];
  let emptyRun = 0;
  let weeksScanned = 0;

  for (let i = 0; i < MAX_WEEKS; i++) {
    const week = parseCurrentWeek();
    if (!week) break;

    weeksScanned++;
    all.push(...week.events);
    onProgress({
      week: i + 1,
      max: MAX_WEEKS,
      found: dedupe(all).length,
      weekStart: week.weekStart,
    });

    // The old stop condition asked whether Next Week was disabled. It never is,
    // so every run walked past the end of term. Two blank weeks is the real end.
    emptyRun = week.events.length ? 0 : emptyRun + 1;
    if (emptyRun >= 2) break;

    if (i < MAX_WEEKS - 1) {
      const moved = await gotoNextWeek();
      if (!moved) break;
    }
  }

  const events = dedupe(all);
  return { events: events, courses: summariseCourses(events), weeksScanned: weeksScanned };
}

/* ---------------------------------------------------------------- conflicts */

function overlaps(a, b) {
  const s1 = toMinutes(a.start_time);
  const e1 = toMinutes(a.end_time);
  const s2 = toMinutes(b.start_time);
  const e2 = toMinutes(b.end_time);
  if (s1 === null || e1 === null || s2 === null || e2 === null) return false;
  return s1 < e2 && s2 < e1;
}

// The desktop version asked once per overlapping *session*, so a clash that
// repeats every week produced fourteen identical dialogs. Group by the pair of
// classes instead: ask once, apply the answer to every date.
function findClashes(events) {
  const groups = new Map();
  for (let i = 0; i < events.length; i++) {
    for (let j = i + 1; j < events.length; j++) {
      const a = events[i];
      const b = events[j];
      if (a.code === b.code && a.type === b.type) continue;
      if (a.date.getTime() !== b.date.getTime()) continue;
      if (!overlaps(a, b)) continue;

      const ka = a.code + "|" + a.type;
      const kb = b.code + "|" + b.type;
      const first = ka < kb;
      const key = first ? ka + "::" + kb : kb + "::" + ka;
      if (!groups.has(key)) {
        groups.set(key, { key: key, a: first ? a : b, b: first ? b : a, dates: [] });
      }
      groups.get(key).dates.push(a.date);
    }
  }
  return [...groups.values()];
}

// Drops the losing class only on the dates it actually clashes on. Dropping it
// outright would delete perfectly good sessions: a lab that collides with a
// lecture twice in a term still meets the other twelve weeks.
function applyClashChoices(events, choices, clashes) {
  const stamp = (ev) => ev.code + "|" + ev.type + "|" + ev.date.toDateString();
  const drop = new Set();
  for (const c of clashes || []) {
    const choice = choices[c.key];
    if (!choice || choice === "both") continue;
    const loser = choice === "a" ? c.b : c.a;
    for (const d of c.dates) drop.add(loser.code + "|" + loser.type + "|" + d.toDateString());
  }
  return events.filter((ev) => !drop.has(stamp(ev)));
}

/* --------------------------------------------------------------------- ics */

function icsEscape(s) {
  return String(s)
    .replace(/\\/g, "\\\\")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,")
    .replace(/\r?\n/g, "\\n");
}

// RFC 5545 caps a content line at 75 octets; longer lines continue with a
// leading space. Google tolerates over-long lines, other clients do not.
function fold(line) {
  if (line.length <= 73) return line;
  const rest = line.slice(73).match(/.{1,72}/g) || [];
  return [line.slice(0, 73), ...rest.map((s) => " " + s)].join("\r\n");
}

// Singapore has been UTC+8 with no daylight saving since 1982, so the offset is
// a constant. Emitting plain UTC skips the whole VTIMEZONE block and any
// timezone library, and is read correctly by every calendar app.
function toUtcStamp(date, timeStr) {
  const mins = toMinutes(timeStr);
  const utc = new Date(
    Date.UTC(
      date.getFullYear(),
      date.getMonth(),
      date.getDate(),
      Math.floor(mins / 60) - 8,
      mins % 60
    )
  );
  return utc.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

function buildIcs(events, reminderMinutes) {
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//SUTD Calendar Bot//EN",
    "CALSCALE:GREGORIAN",
  ];

  events.forEach((ev, i) => {
    const friendly = TYPE_MAPPING[ev.type] || ev.type;
    lines.push("BEGIN:VEVENT");
    lines.push("UID:sutd-" + i + "-" + toUtcStamp(ev.date, ev.start_time) + "@sutd-calendar-bot");
    lines.push("DTSTAMP:" + stamp);
    lines.push("DTSTART:" + toUtcStamp(ev.date, ev.start_time));
    lines.push("DTEND:" + toUtcStamp(ev.date, ev.end_time));
    lines.push(fold("SUMMARY:" + icsEscape(ev.title + " (" + friendly + ")")));
    lines.push(fold("LOCATION:" + icsEscape(ev.location)));
    lines.push(
      fold(
        "DESCRIPTION:" +
          icsEscape("Course: " + ev.code + " " + ev.section + "\nInstructors: " + ev.instructors)
      )
    );
    if (reminderMinutes > 0) {
      lines.push("BEGIN:VALARM");
      lines.push("TRIGGER:-PT" + reminderMinutes + "M");
      lines.push("ACTION:DISPLAY");
      lines.push(fold("DESCRIPTION:" + icsEscape(ev.title)));
      lines.push("END:VALARM");
    }
    lines.push("END:VEVENT");
  });

  lines.push("END:VCALENDAR");
  return lines.join("\r\n") + "\r\n";
}

function downloadIcs(text, filename) {
  const blob = new Blob([text], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

// Exposed so test-parser.html can exercise the logic without a live portal.
window.__SUTD = {
  parseCellText: parseCellText,
  parseCurrentWeek: parseCurrentWeek,
  dedupe: dedupe,
  summariseCourses: summariseCourses,
  findClashes: findClashes,
  applyClashChoices: applyClashChoices,
  buildIcs: buildIcs,
  toMinutes: toMinutes,
  addDays: addDays,
  overlaps: overlaps,
  TYPE_MAPPING: TYPE_MAPPING,
};
