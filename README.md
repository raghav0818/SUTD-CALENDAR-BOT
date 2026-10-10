# SUTD Calendar Bot

Turn your SUTD weekly timetable into a calendar file you can import into Google Calendar or
Apple Calendar. No copying, no typing, no spreadsheet.

It is a browser extension. It reads the timetable page you are already looking at, builds the
calendar file on your own computer, and that is the whole story — there is no server and
nothing is uploaded anywhere.

## Using it

1. Log into the portal as you normally would, in whatever browser you use.
2. Open **Manage Classes → View My Weekly Schedule**, so the calendar grid is on screen.
3. Click the extension icon in your toolbar.
4. Press **Scan my timetable** and leave the tab alone for about a minute.
5. Pick what to do about any clashing classes, untick anything you do not want, then
   **Download calendar**.

The panel then shows you exactly how to import the file into Google Calendar.

## Installing

The Chrome Web Store listing is pending review. Until it is live, install it manually — this
works in Chrome and Edge:

1. Click **Code → Download ZIP** at the top of this page, then unzip it.
2. Go to `chrome://extensions` and turn on **Developer mode** (top right).
3. Click **Load unpacked** and select the `extension` folder.

## What is in here

| | |
|---|---|
| `extension/` | The extension. `content.js` is the parser and calendar builder, `panel.js` is the interface. |
| `docs/` | The landing page and privacy policy, served by GitHub Pages. |
| `test-parser.html` | The tests. Open it in a browser — it must be a real browser, not a headless DOM. |
| `desktop-legacy/` | The original Python + Selenium version. Superseded; see its `NOTE.md`. |

## Running the tests

Open `test-parser.html` in Chrome or Edge. It prints a pass/fail line per check.

One test is skipped unless you provide a real page to parse. To enable it, open your weekly
schedule on a week that has classes, press <kbd>Ctrl</kbd>+<kbd>S</kbd>, choose **Webpage,
Complete** — not "HTML Only", the stylesheet is needed because day columns are matched by
position — and save it as `schedule-sample.html` in this folder. **Delete your name and
student ID from it first.** It is gitignored and will not be committed.

## How the parsing works, and why

The portal shows one week at a time, so the extension clicks through the term week by week
and reads each grid as it renders.

It deliberately does **not** use the List View, even though that shows the whole term on one
page. The list view gives a date *range* (`Mo 09:00AM - 10:30AM ... 13/01/2025 - 25/04/2025`),
which means turning it into real events requires guessing which weeks do not happen — recess
week, public holidays. An earlier version of this project did exactly that, with the recess
week hardcoded. Guess wrong and every date after it shifts by a week. The grid never guesses:
if no cell is drawn, there is no class.

Two details the parser depends on, both of which will silently break everything if changed:

- It reads cells with `innerText`, not `textContent`. The parser works line by line, anchoring
  on the line that holds the time range and reading the title, type and room by their offset
  from it. `textContent` collapses the line breaks and every cell parses as empty.
- Day columns are matched by pixel position, not by column index, because `rowspan` in the
  grid makes `cellIndex` point at the wrong day.

## Limitations

- Scanning starts from whichever week the page is showing and goes forward, up to 16 weeks.
  Run it at the start of term. Run it in week 8 and you get weeks 8 onwards only.
- It depends on the portal's current HTML. If SUTD changes the schedule page, the parser will
  need updating — `test-parser.html` with a fresh `schedule-sample.html` is how you find out.

## Licence

MIT. Not affiliated with or endorsed by SUTD.
