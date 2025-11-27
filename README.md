Here is a **cleaned-up, clearer, more structured, and more user-friendly** version of your README.
I kept all your original information, but rewrote it for maximum readability, flow, and ease of use.

---

# **SUTD Calendar Bot**

A simple, automated desktop tool for SUTD students.
It logs into MyPortal, extracts your class timetable, and converts it into a calendar-ready `.ics` file — with smart holiday detection included.

---

## **✨ Features**

* **Automatic Schedule Extraction**
  Logs into MyPortal via Chrome (Windows/Mac) or Safari (Mac fallback).
* **Calendar File Generation**
  Exports your schedule into `.ics`, which works with Google Calendar, Outlook, and Apple Calendar.
* **Smart Customization**
  Rename modules and deselect classes before generating your calendar.
* **Automatic Config Saving**
  Course names and settings are remembered for future use.

---

## **🛠 Prerequisites**

Before running the bot, make sure you have:

* **Python 3.10 or higher**
  **Windows users:** Select **“Add Python to PATH”** during installation.

---

## **📦 Installation**

1. **Download the repository**
   Click *Code → Download ZIP* and extract it.

2. **Open the extracted folder**

3. **Install required libraries (Universal Installer)**
   You can run `install.py` in any of these ways:

   **Option A: Through an IDE (VS Code, PyCharm, etc.)**

   * Open `install.py`
   * Click Run

   **Option B: Double-click (Windows only)**

   * Double-click `install.py`

   **Option C: From Terminal**

   **Windows:**

   ```
   python install.py
   ```

   **Mac:**

   ```
   python3 install.py
   ```

   Wait until you see the **“Success”** message.

---

## **🚀 How to Use**

### **1. Run the Application**

**Option A: IDE**
Run `sutd_calendar_bot.py`

**Option B: Command Line**

**Windows:**

```
python sutd_calendar_bot.py
```

**Mac:**

```
python3 sutd_calendar_bot.py
```

---

### **2. Login & Scan**

* Click **“START LOGIN & SCAN”**
* A browser window will open
* Log in to MyPortal manually and complete 2FA
  *(The bot waits for you—just log in normally)*

Once your timetable is detected, the bot will:

* Close the browser automatically
* Expand the app window to show your timetable

---

### **3. Customize Your Schedule**

* **Rename modules** by editing the text fields
* **Uncheck** any classes you want to exclude

---

### **4. Generate Calendar**

Click **“GENERATE CALENDAR FILES”**

The folder containing **SUTD_Calendar.ics** will open automatically.

Drag the `.ics` file into:

* Google Calendar
* Apple Calendar
* Outlook
  or any other calendar app.

---

## **⚙ Configuration File**

A file named `sutd_bot_config.json` is created after your first run.

It stores:

* Renamed module titles
* Saved preferences

No manual editing is needed — the bot handles everything.

---

## **🐞 Troubleshooting**

### **Mac Safari Automation Error**

1. Open **Safari → Settings → Advanced**
2. Enable **“Show Develop menu”**
3. Go to **Develop → Allow Remote Automation**

### **“Browser closed unexpectedly”**

Do **not** close the browser manually.
Let the bot close it after scanning.

### **“Cannot write to file”**

Close any app currently using `SUTD_Calendar.ics` (Google Calendar, Outlook, etc.).

### **Crashes**

Check `sutd_bot.log` in the project folder for details.

---

## **📄 License**

This project is released under the **MIT License**.

**Disclaimer:** This is a student-made tool and is *not* officially affiliated with SUTD. Please use it responsibly.


