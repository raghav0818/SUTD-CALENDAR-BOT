SUTD Calendar Bot

A smart, automated desktop application for SUTD students.
Easily scrape your class schedule from the MyPortal website and convert it into a calendar-ready .ics format with smart holiday detection.

<img width="2880" height="1715" alt="Screenshot 2025-11-20 091557" src="https://github.com/user-attachments/assets/096ce116-43af-4fbe-9676-d542e4cf1b59" />

Automated Extraction
Logs into the SUTD portal via Chrome (Windows/Mac) or Safari (Mac Fallback) to retrieve your schedule automatically.

🛠 Prerequisites

Before running the bot, ensure you have the following installed:

Python 3.10 or higher

Windows Users: Check "Add Python to PATH" during installation.


📦 FIRST TIME Installation

Download this repository (Code > Download ZIP) and Unzip it.

Open the extracted folder.

* For Windows Users

    Double-click the setup_windows.bat file.

* For Mac Users

    * Open your Terminal.

    * Type sh  (with a space).

    * Drag and drop the setup_mac.sh file into the terminal.

    * Press Enter.

This will automatically install all required libraries.


🚀 How to Use

1. Run the Application

Windows: Double-click run_bot.bat (if created) or run in cmd:

    python sutd_calendar_bot.py


Mac: Run in terminal:

    python3 sutd_calendar_bot.py


2. Login & Scan

Click "START LOGIN & SCAN".

A browser window will open.

Manually log in to the SUTD portal and complete 2FA.

Note: The bot waits for you to finish logging in.

3. Customize

Once the schedule is detected, the browser closes and the app expands.

Rename: Edit text boxes to rename subjects.

Filter: Uncheck classes you don't want.

4. Generate

Click "GENERATE CALENDAR FILES".

The folder containing your SUTD_Calendar.ics file will open automatically.

Drag this file into Google Calendar, Outlook, or Apple Calendar.

⚙ Configuration

The bot creates a sutd_bot_config.json file after the first run.

What it does: Stores your renamed courses and settings.

Note: You do not need to edit this manually.

🐞 Troubleshooting

* Mac Safari Error

Open Safari > Settings > Advanced > Check "Show Develop menu" > Click Develop > Check Allow Remote Automation.

* "Browser closed unexpectedly"

Do not close the browser manually. Wait for the bot to close it.

* "Cannot write to file"

Ensure SUTD_Calendar.ics is not open in another program.

* Crashes

Check sutd_bot.log in the folder for error details.

📄 License

This project is licensed under the MIT License.

Disclaimer: This tool is a student-made project and is not officially endorsed by SUTD. Use it responsibly.
