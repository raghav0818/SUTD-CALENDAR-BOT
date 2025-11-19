SUTD Calendar Bot

A smart, automated desktop application for SUTD students to convert their class schedules from the MyPortal website into a calendar-ready .ics format.

Features

Automated Extraction
Logs into the SUTD portal via Chrome (Windows/Mac) or Safari (Mac Fallback) to retrieve your schedule.

Smart Date Logic

Automatically detects and skips Recess Week (Week 7).

Fetches live Singapore Public Holiday data to exclude classes falling on holidays.

User-Friendly Customization

Rename Classes: Change course codes (e.g., "10.009") to readable names (e.g., "The Digital World").

Filter Types: Exclude specific class types (e.g., "Optional Lab") that you do not wish to import.

Persistent Memory: The application saves your custom names and settings for the next term.

Robustness
Includes error logging, file permission checks, and auto-recovery mechanisms.

Prerequisites

Before running the bot, ensure you have the following installed:

Python 3.10 or higher

Download from python.org.

Windows Users: Ensure you check "Add Python to PATH" during the installation process.

Web Browser

Windows: Google Chrome.

Mac: Google Chrome (Preferred) or Safari.

Installation

Download this repository (Code > Download ZIP) and Unzip it to a folder of your choice.

Open the extracted folder.

For Windows Users

Double-click the setup_windows.bat file. This script will automatically install all necessary Python libraries for you.

For Mac Users

Open your Terminal app.

Type sh  (ensure there is a space after "sh").

Drag and drop the setup_mac.sh file from Finder into the Terminal window.

Press Enter to run the installation script.

How to Use

1. Run the Application

Windows: Double-click run_bot.bat (if available) or open a command prompt and type:

python sutd_calendar_bot.py


Mac: Open a terminal and type:

python3 sutd_calendar_bot.py


2. Login

Click the "START LOGIN & SCAN" button. A browser window will open. Manually log in to the SUTD portal and complete your 2FA verification. The bot will wait until it detects a successful login.

3. Customize Schedule

Once the schedule is detected, the browser will close, and the application window will expand.

Rename: Edit the text fields to rename your subjects.

Filter: Uncheck any classes or class types you do not wish to include in your calendar.

4. Generate Files

Set your preferred reminder time (default is 15 minutes). Click "GENERATE CALENDAR FILES". The folder containing your new SUTD_Calendar.ics file will open automatically.

5. Import to Calendar

Drag and drop the generated .ics file into Google Calendar, Outlook, or Apple Calendar to import your schedule.

Configuration

The application creates a sutd_bot_config.json file after the first run. This file stores your renamed courses and default settings. You do not need to edit this file manually.

Troubleshooting

Mac Users (Safari Error)
If the bot attempts to use Safari, you must enable automation permissions once:

Open Safari > Settings > Advanced.

Check "Show Develop menu in menu bar".

Click Develop in the top menu bar and check Allow Remote Automation.

"Browser closed unexpectedly"
Do not close the browser window manually while the bot is navigating. Wait for the application to close it automatically.

"Cannot write to file"
Ensure SUTD_Calendar.ics is not currently open in another program.

Crash / Unknown Error
Check the sutd_bot.log file generated in the same folder for detailed error messages.

License

This project is licensed under the MIT License.

Disclaimer: This tool is a student-made project and is not officially endorsed by SUTD. Use it responsibly.