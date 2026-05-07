# SUTD Calendar Bot

> Automatically generate a personal calendar from your SUTD Weekly Schedule — no copy-pasting required.

<img width="100%" height="100%" alt="SUTD Calendar Bot demo" src="https://github.com/user-attachments/assets/67a01a4a-429d-4b50-ae1e-01352976c7be" />

---

## 🚀 Getting Started

The easiest way to run the bot is directly from your code editor.

**Prerequisites:** Python must be installed on your machine. That's it.

1. **Download** — Clone or download this repository.
2. **Open** — Open `sutd_bot.py` in any editor (VS Code, PyCharm, IDLE, etc.).
3. **Run** — Hit the Run button.
4. **Login** — Login in the pop up browser
5. **Sit and watch** — The bot automatically looks through your weekly schedule and generates csv file.
REMEMBER NOT TO TOUCH ANYTHING WHILE BOT IS WORKING

---

## ✨ Features

**Visual Grid Scraping**
Navigates your SUTD Weekly Calendar view week-by-week, capturing accurate dates and automatically skipping recess weeks.

**Smart Conflict Resolution**
When two classes overlap (shown as an orange "Time Conflict" block), a pop-up lets you choose which class to keep — no guesswork.

**Fully Customizable**
Review your extracted schedule, rename course titles, and filter out unwanted class types (e.g. skip all lectures) before exporting.

**Dual Export**
Generates both a `.csv` spreadsheet and an `.ics` calendar file, saved directly to your Desktop and compatible with Google Calendar and Apple Calendar.
