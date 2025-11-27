
# **SUTD Calendar Bot**

A simple, automated desktop tool for SUTD students.
It logs into MyPortal, extracts your class timetable, and converts it into a calendar-ready `.ics` file — with smart holiday detection included.

<img width="2880" height="1706" alt="image" src="https://github.com/user-attachments/assets/953ff768-92c0-4957-8b51-69d20b18f23f" />
<img width="2764" height="1418" alt="image" src="https://github.com/user-attachments/assets/5524a45e-4435-4782-a3df-bd9f49b67775" />

---

## **✨ Features**

* **Automatic Schedule Extraction** via browser automation
* **One-click Calendar File Generation** (`.ics`)
* **Rename & Filter Classes** before export
* **Saves Preferences Automatically** (`sutd_bot_config.json`)
* **Works on Windows & macOS**

---

## **🛠 Prerequisites**

Make sure you have:

* **Python 3.10 or higher**
  **Windows users:** Select **“Add Python to PATH”** during installation.

---

## **📦 Installation**

### **1. Download the Bot**

* Click **Code → Download ZIP**
* Extract the ZIP

### **2. Install Required Libraries**

Run `install.py` using *any* of the following methods:

#### **Option A — Using VS Code / IDE**

* Open `install.py`
* Click **Run**

#### **Option B — Windows Only**

* Double-click `install.py`

#### **Option C — Using Terminal**

**Windows:**

```
python install.py
```

**Mac:**

```
python3 install.py
```

Wait for the **“Success”** message.

---

## **🚀 How to Use the Bot**

### **1. Launch the app**

**Option A — IDE**
Run `sutd_calendar_bot.py`

**Option B — Windows Command Prompt**

```
python sutd_calendar_bot.py
```

**Option C — Mac Terminal**

```
python3 sutd_calendar_bot.py
```

---

### **2. Login & Scan**

1. Click **START LOGIN & SCAN**
2. A browser window will open
3. Log in manually to MyPortal (including 2FA)
4. Wait—**do not close the browser**
5. The bot closes it automatically once done
6. The app expands and your schedule appears

---

### **3. Customize**

* **Rename courses** by editing the text boxes
* **Uncheck** classes you want to exclude

---

### **4. Generate Calendar File**

* Click **GENERATE CALENDAR FILES**
* A folder will open containing:

  ```
  SUTD_Calendar.ics
  ```

---

# **📅 How to Import the .ics File (Step by step guide)**

Below are step-by-step instructions for the 3 major calendar apps.

---

# **📌 Importing into Google Calendar (Desktop)**

### **Method 1 — Drag and Drop (Easiest)**

1. Open **Google Calendar** in a browser
2. Open the folder containing `SUTD_Calendar.ics`
3. Drag the `.ics` file into the Google Calendar window
4. Google will ask which calendar to add it to
5. Click **Add to calendar**

---

### **Method 2 — Import Menu**

1. Go to **Google Calendar**
2. On the left, click the **gear icon → Settings**
3. Select **Import & Export**
4. Under *Import*, click **Select file from your computer**
5. Choose `SUTD_Calendar.ics`
6. Choose which calendar to import into
7. Click **Import**

Done!

---

# **🍎 Importing into Apple Calendar (Mac)**

### **Method 1 — Double-click (Easiest)**

1. Double-click `SUTD_Calendar.ics`
2. Apple Calendar will open
3. Choose which calendar to add it to
4. Click **OK**

---

### **Method 2 — From Within Apple Calendar**

1. Open **Calendar** app
2. Click **File → Import…**
3. Select `SUTD_Calendar.ics`
4. Choose the target calendar
5. Click **Import**

---

# **📧 Importing into Outlook**

### **Outlook Desktop App (Windows/Mac)**

1. Open **Outlook**
2. Go to **File → Open & Export**
3. Click **Import/Export**
4. Choose **Import an iCalendar (.ics)**
5. Select `SUTD_Calendar.ics`
6. Choose:

   * **Open as New** (recommended)
   * or **Import** into an existing calendar
7. Click **OK**

---

### **Outlook Web (Outlook.com)**

1. Go to **Outlook.com → Calendar**
2. On the left, click **Add calendar**
3. Select **Upload from file**
4. Choose `SUTD_Calendar.ics`
5. Select calendar destination
6. Click **Import**

---

## **⚙ Configuration File**

The bot automatically creates:

```
sutd_bot_config.json
```

It stores:

* Renamed module titles
* Filter settings

You **don’t need to modify** this manually.

---

## **🐞 Troubleshooting**

### **Mac Safari Automation Error**

1. Safari → Settings → Advanced
2. Check **Show Develop menu**
3. Develop → **Allow Remote Automation**

### **“Browser closed unexpectedly”**

Do **not** close the browser manually.

### **“Cannot write to file”**

Close any app currently using the `.ics` file.

### **Crashes**

Open `sutd_bot.log` for details.

---

## **📄 License**

GNU GPLv3 License
*This is a student-made project and is not officially affiliated with SUTD.*

Credits: @Itsskiip on github for inspo and code

Credits: @Itsskiip on github for inspo and code
https://github.com/Itsskiip/SUTDCalendarConverter/blob/main/convert.py