# SUTD Calendar Bot

A smart, automated desktop application for **SUTD students**.

Easily scrape your class schedule from the **MyPortal** website and convert it into a calendar-ready **.ics** file — with **smart holiday detection** built in.

---

## 📖 Table of Contents

* [Features](#-features)
* [Prerequisites](#-prerequisites)
* [Installation & Usage](#-installation--usage)

  * [Windows](#-for-windows-users-easiest-method)
  * [macOS](#-for-mac-users-source-code-method)
* [How It Works](#-how-it-works)
* [Configuration](#-configuration)
* [Troubleshooting](#-troubleshooting)
* [License](#-license)

---

## 🌟 Features

### 🔐 Automated Extraction

* Logs into the SUTD portal via:

  * **Chrome** (Windows & macOS)
  * **Safari** (macOS fallback)
* Automatically retrieves your class schedule.

### 📅 Smart Date Logic

* Automatically detects and **skips Recess Week (Week 7)**.
* Fetches **live Singapore Public Holiday** data and excludes classes on those days.

### 🎛 User-Friendly Customization

* **Rename Classes**: Change codes like `10.009` to `The Digital World`.
* **Filter Types**: Uncheck specific class types (e.g. *Optional Lab*).
* **Memory**: Remembers your custom names and preferences for the next term.

### 🛡 Robust Design

* Self-healing dependency installation.
* Error logging and auto-recovery.

---

## 🛠 Prerequisites

### 🌐 Web Browser

* **Windows**: Google Chrome
* **macOS**: Google Chrome *(preferred)* or Safari

### 🐍 Python (macOS Users Only)

* Python **3.10+** must be installed.

---

## 📦 Installation & Usage

### 🪟 For Windows Users (Easiest Method)

No installation required!

1. Download the latest `sutd_calendar_bot.exe` from the **Releases** page.
2. Double-click the `.exe` to run it.
3. If you see a warning:

   * Click **More Info** → **Run Anyway**.

---

### 🍎 For macOS Users (Source Code Method)

Since `.exe` files do not run on macOS:

1. Download this repository (**Code → Download ZIP**) and unzip it.
2. Open **Terminal**.
3. Type:

   ```bash
   python3
   ```

   *(Make sure there is a space after `python3`)*
4. Drag `sutd_calendar_bot.py` into the Terminal window.
5. Press **Enter**.

> 💡 The script includes a **self-installer**. On first run, it automatically installs all required dependencies.

---

## 🚀 How It Works

1. **Login & Scan**

   * Click **START LOGIN & SCAN**.
   * A browser window opens — log in to the SUTD portal manually.
   * The bot waits patiently for you.

2. **Customize**

   * Once logged in, the browser closes automatically.
   * Rename subjects and uncheck classes you don’t want.

3. **Generate**

   * Click **GENERATE CALENDAR FILES**.
   * A folder opens containing `SUTD_Calendar.ics`.

4. **Import**

   * Drag the `.ics` file into **Google Calendar**, **Outlook**, or **Apple Calendar**.

---

## ⚙ Configuration

After the first run, the bot creates:

```
sutd_bot_config.json
```

**What it does:**

* Stores renamed courses and user preferences.

> ⚠️ You do **not** need to edit this file manually.

---

## 🐞 Troubleshooting

| Issue                           | Solution                                                                                            |
| ------------------------------- | --------------------------------------------------------------------------------------------------- |
| **macOS Safari Error**          | Safari → Settings → Advanced → Enable **Show Develop menu** → Develop → **Allow Remote Automation** |
| **Browser closed unexpectedly** | Do not close the browser manually. Let the bot close it.                                            |
| **Cannot write to file**        | Ensure `SUTD_Calendar.ics` is not open elsewhere.                                                   |
| **Crashes**                     | Check `sutd_bot.log` in the app folder for details.                                                 |

---

## 📄 License

This project is licensed under the **GNU General Public License v3**.

**Disclaimer:**
This is a **student-made project** and is **not officially endorsed by SUTD**. Please use it responsibly.
