📅 SUTD Calendar Bot

A smart, automated desktop application for SUTD students to convert their class schedules from the MyPortal website into a calendar-ready .ics format.

✨ Features

Automated Extraction: Logs into the SUTD portal via Chrome (Windows/Mac) or Safari (Mac Fallback).

Smart Date Logic: * Automatically detects and skips Recess Week (Week 7).

Fetches live Singapore Public Holiday data to skip classes on holidays.

User-Friendly Customization:

Rename Classes: Rename "10.009" to "Digital World" easily.

Filter Types: Uncheck specific class types (e.g., "Optional Lab") you don't want.

Persistent Memory: Remembers your custom names for the next term.

Modern UI: Built with CustomTkinter for a clean, dark-mode compatible interface.

Robustness: Includes error logging, file permission checks, and auto-recovery if the browser closes unexpectedly.

🛠️ Prerequisites

Before running the bot, ensure you have the following installed:

Python 3.10 or higher: Download Here

Browser:

Windows: Google Chrome.

Mac: Google Chrome (Preferred) or Safari.

📦 Installation

Clone the repository (or download the ZIP):

git clone [https://github.com/YOUR_USERNAME/SUTD-Calendar-Bot.git](https://github.com/YOUR_USERNAME/SUTD-Calendar-Bot.git)
cd SUTD-Calendar-Bot


Install dependencies:

pip install -r requirements.txt


🚀 How to Use

Run the script:

python sutd_calendar_bot.py


Login:

Click "START LOGIN & SCAN".

A browser window will open. Manually log in to the SUTD portal and complete 2FA.

Note: The bot waits for you to finish logging in.

Customize:

Once the bot detects the schedule, the browser window will close.

The app window will expand to show your classes.

Rename any subjects (e.g., change codes to names).

Uncheck any classes you don't want to import.

Generate:

Set your preferred Reminder time (default is 15 mins before class).

Click "GENERATE CALENDAR FILES".

The folder containing your SUTD_Calendar.ics file will open automatically.

Import:

Drag and drop the .ics file into Google Calendar, Outlook, or Apple Calendar.

⚙️ Configuration

The bot creates a sutd_bot_config.json file after the first run. This file stores your:

Renamed courses

Default reminder settings

You do not need to edit this manually; the App handles it.

🐞 Troubleshooting

Mac Users (Safari Error): If using Safari, you must enable automation permissions once:

Open Safari > Settings > Advanced.

Check "Show Develop menu in menu bar".

Click Develop in the top menu bar > Allow Remote Automation.

"Browser window closed unexpectedly": Do not close the browser manually while it is navigating. Wait for the bot to close it.

"Cannot write to file": Ensure SUTD_Calendar.ics is not currently open in another program.

Check the Logs: If the app crashes, check sutd_bot.log in the same folder for detailed error messages.

📄 License

This project is licensed under the MIT License.

Disclaimer: This tool is a student-made project and is not officially endorsed by SUTD. Use it responsibly.