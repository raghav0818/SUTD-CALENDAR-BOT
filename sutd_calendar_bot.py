# Copyright (C) 2024 Itsskiip
# Copyright (C) 2025 raghav0818
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License v3

import subprocess
import sys
import os
import time
import importlib.util

# --- PART 1: SELF-INSTALLER & DEPENDENCY CHECK ---
# This section runs BEFORE any external libraries are imported.
# It ensures the environment is ready for the bot.

REQUIRED_PACKAGES = {
    # format: "import_name": "pip_install_name"
    "selenium": "selenium>=4.0.0",
    "customtkinter": "customtkinter>=5.2.0",
    "ics": "ics>=0.7",
    "arrow": "arrow",
    "requests": "requests>=2.31.0",
    "urllib3": "urllib3==1.26.18",
    "webdriver_manager": "webdriver-manager",
    "packaging": "packaging"
}

def check_and_install_dependencies():
    """Checks if required packages are installed. If not, installs them."""
    missing = []
    
    for import_name, install_name in REQUIRED_PACKAGES.items():
        try:
            importlib.util.find_spec(import_name)
        except ImportError:
             missing.append(install_name)
        except Exception:
             # Fallback for weird edge cases
             if importlib.util.find_spec(import_name) is None:
                 missing.append(install_name)

    if missing:
        print("==================================================")
        print("   SUTD Calendar Bot - First Run Setup")
        print("==================================================")
        print(f"Missing dependencies detected: {', '.join(missing)}")
        print("Installing them now... (This may take a minute)")
        print("")

        try:
            # Construct pip install command
            cmd = [sys.executable, "-m", "pip", "install"] + missing
            
            # Mac/Linux often needs --user to avoid permission errors
            if sys.platform != "win32":
                cmd.append("--user")

            subprocess.check_call(cmd)
            print("\n[SUCCESS] Dependencies installed!")
            print("Restarting the bot to apply changes...")
            print("==================================================")
            time.sleep(2)
            
            # Restart the script to load new libraries
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
        except subprocess.CalledProcessError as e:
            print(f"\n[ERROR] Auto-install failed with error code {e.returncode}.")
            print("Please try running this command manually:")
            # Generate the manual command string
            pkg_str = " ".join(REQUIRED_PACKAGES.values())
            print(f"   {sys.executable} -m pip install {pkg_str}")
            input("Press Enter to exit...")
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] Unexpected setup error: {e}")
            input("Press Enter to exit...")
            sys.exit(1)

# Run the check immediately
check_and_install_dependencies()

# --- PART 2: MAIN APPLICATION ---

import re
import json
import arrow
import threading
import logging
import requests
import webbrowser
import customtkinter as ctk
from tkinter import messagebox
from datetime import date, timedelta, datetime, time as dt_time
from typing import List, Dict, Optional, Any

# Lazy-loaded imports: selenium, webdriver-manager, ics
# These are imported inside functions to speed up initial launch.

# --- LOGGING CONFIGURATION ---
def get_log_path():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'sutd_bot.log')

logging.basicConfig(
    filename=get_log_path(),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- CONFIGURATION ---
OUTPUT_ICS = "SUTD_Calendar.ics"
CONFIG_FILE = "sutd_bot_config.json"
TIMEZONE = "Asia/Singapore"

# UI THEME
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue") 

# TYPE MAPPING
TYPE_MAPPING = {
    "CBL": "Cohort Class",
    "LEC": "Lecture",
    "LAB": "Lab",
    "TUT": "Tutorial",
    "REC": "Recitation",
    "TES": "Test/Exam"
}

# --- 3. DYNAMIC HOLIDAY API ---
SG_HOLIDAYS = set() # Global empty set, populated in background

def load_singapore_holidays():
    """Fetches PH from API in background, falls back to hardcoded list on error."""
    global SG_HOLIDAYS
    years = [date.today().year, date.today().year + 1]
    
    logging.info("Fetching Public Holidays from API...")
    
    new_holidays = set()
    for year in years:
        try:
            url = f"https://date.nager.at/api/v3/publicholidays/{year}/SG"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            for item in data:
                h_date = arrow.get(item['date']).date()
                new_holidays.add(h_date)
            logging.info(f"Loaded {len(data)} holidays for {year}.")
        except Exception as e:
            logging.error(f"Failed to fetch API holidays for {year}: {e}")
            if year == 2025:
                new_holidays.update({date(2025, 1, 1), date(2025, 1, 29), date(2025, 1, 30), date(2025, 8, 9), date(2025, 12, 25)})
    
    SG_HOLIDAYS.update(new_holidays)
    logging.info("Holiday data updated.")


class SUTDCalendarBot:
    def __init__(self, log_callback=None):
        self.driver: Any = None
        self.wait: Any = None
        self.weekday_map = ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')
        self.log_callback = log_callback
        
        # Start holiday fetch in background
        threading.Thread(target=load_singapore_holidays, daemon=True).start()

    def log(self, message):
        logging.info(message) 
        if self.log_callback:
            self.log_callback(message) 
        else:
            print(message)
# ... [rest of SUTDCalendarBot methods unchanged] ...

    def log(self, message):
        logging.info(message) 
        if self.log_callback:
            self.log_callback(message) 
        else:
            print(message)

    def _get_chrome_options(self, headless=True):
        from selenium import webdriver
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # Optimization: Block images/CSS in headless mode?
        # Maybe too risky for Single-Page Apps (React/Angular) that depend on loading state.
        if headless:
            options.add_argument("--headless=new")
        return options

    def start_login_and_scrape(self) -> str:
        """
        OPTIMIZED FLOW:
        1. Open Visible Window (User Logs In)
        2. Detect Login -> Minimize Window (Pseudo-Headless)
        3. Scrape in same session (Fastest)
        """
        # Lazy imports
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException
        from webdriver_manager.chrome import ChromeDriverManager

        self.log("Launching Browser...")
        try:
            service = Service(ChromeDriverManager().install())
            # Start VISIBLE so user can see what's happening
            self.driver = webdriver.Chrome(service=service, options=self._get_chrome_options(headless=False))
            self.wait = WebDriverWait(self.driver, 300)

            self.log("Please log in via the browser window...")
            self.driver.get("https://ease.sutd.edu.sg/app/sutd_myportal_1/exk3pseb8o4VxzQF85d7/sso/saml")

            # Wait for Login (Presence of Portal Element)
            try:
                # Wait for the "Student" or "Oracle" link which appears after MFA
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "PSHYPERLINKNOUL")))
                self.log("Login detected!")
                
                # OPTIMIZATION: Minimize window instead of closing/restarting
                self.driver.minimize_window()
                self.log("Browser hidden. Starting extraction...")
                
            except TimeoutException:
                raise TimeoutException("Login timed out. Did you close the window?")

            # Reuse the SAME driver for scraping (Faster than restarting)
            # Re-click the menu items to ensure frame loads correctly
            # Note: We are already on the portal page or close to it.
            
            # Click "Student" / Portal Link if needed
            try:
                self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "PSHYPERLINKNOUL"))).click()
            except:
                pass # Already clicked or on page
            
            self.wait.until(EC.element_to_be_clickable((By.ID, "ADMN_S20160108140638335703604"))).click()
            self.log("Accessing Weekly Schedule...")

            self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "ptifrmtgtframe")))

            # Click List View
            list_view_xpath = "//input[@type='radio' and @value='L' and starts-with(@id, 'DERIVED_REGFRM1_SSR_SCHED_FORMAT')]"
            radio = self.wait.until(EC.element_to_be_clickable((By.XPATH, list_view_xpath)))
            radio.click()
            self.log("Switched to List View...")

            # Smart Wait for Content
            # Wait for the table to change or loading overlay to vanish
            time.sleep(1.5) # Short sleep IS safer than complex AJAX waits here for now
            
            body_element = self.driver.find_element(By.TAG_NAME, "body")
            body_text = body_element.text
            
            self.log("Schedule data extracted.")
            return body_text

        except Exception as e:
            logging.error(f"Scraping Error: {e}", exc_info=True)
            raise e
        finally:
            self.close()

    def parse_raw_data(self, raw_text: str) -> List[Dict]:
        self.log("Parsing schedule data...")
        flags = re.DOTALL + re.MULTILINE
        
        time_re = r'\d\d?:\d\d(?:[AP]M)?'
        # Date regex: some systems use 02/04/2025, just ensuring robustness
        date_re = r'\d\d\/\d\d\/\d{4}'
        
        type_data_re = (
            r'(?P<day>\w{2}) '
            fr'(?P<start_time>{time_re}) - (?P<end_time>{time_re})\s+'
            r'(?P<loc>[^\n]+)\s+'
            r'(?P<lecturers>^.*?)\s+'
            fr'(?P<start_date>{date_re}) - (?P<end_date>{date_re})\W+'
        )
        
        course_data_re = r'(?:\d{4})\s+(?:[A-Z]{2}\d\d)\s+(?P<type>[^\n]+)\s+(?P<type_data>(?:' + type_data_re + ')+)'
        courses_re = r'(?P<code>\d{2} .\d{3}\w*) - (?P<course>[^\n]+).+?(?P<course_data>(?:' + course_data_re + ')+)'

        course_matches = re.finditer(courses_re, raw_text, flags)
        courses = []

        for course_match in course_matches:
            course = {
                'code': course_match['code'].replace(' ', ''), 
                'name': course_match['course'],
                'type': {}
            }
            
            course_type_matches = re.finditer(course_data_re, course_match['course_data'], flags)
            
            for type_match in course_type_matches:
                class_matches = re.finditer(type_data_re, type_match['type_data'], flags)
                class_data_list = []

                for m in class_matches:
                    d = m.groupdict()
                    d['lecturers'] = [name.strip().removesuffix(',') for name in d['lecturers'].splitlines() if name.strip()]
                    d['start_date'] = self._parse_date_str(d['start_date'])
                    d['end_date'] = self._parse_date_str(d['end_date'])
                    try:
                        d['day_idx'] = self.weekday_map.index(d['day'])
                    except ValueError:
                        continue
                    d['start_time'] = self._parse_time_str(d['start_time'])
                    d['end_time'] = self._parse_time_str(d['end_time'])
                    class_data_list.append(d)

                if class_data_list:
                    course['type'][type_match['type']] = class_data_list
            
            courses.append(course)

        if not courses:
            # We don't raise error immediately, maybe it's recess week? 
            # But usually list view shows empty table. 
            self.log("Warning: No courses found in text.")
            # raise ValueError("No courses found. Are you sure the schedule is released?")
        
        self.log(f"Found {len(courses)} courses.")
        return courses

    def expand_events(self, courses: List[Dict], reminder_minutes: int = 15) -> List[Dict]:
        self.log("Generating weekly events...")
        final_events = []

        all_dates = []
        for c in courses:
            for types in c['type'].values():
                for cls in types:
                    all_dates.append(cls['start_date'])
        
        if not all_dates:
             return []

        term_start = min(all_dates)
        # self.log(f"Term assumed to start on: {term_start}")

        for course in courses:
            display_name = course['name']
            multi_type = len(course['type']) > 1

            for class_type, classes in course['type'].items():
                friendly_type = TYPE_MAPPING.get(class_type, class_type)
                
                for c in classes:
                    current_date = c['start_date']
                    days_ahead = (c['day_idx'] - current_date.weekday()) % 7
                    current_date += timedelta(days=days_ahead)

                    while current_date <= c['end_date']:
                        if current_date in SG_HOLIDAYS:
                            # self.log(f"Skipping Holiday: {current_date}")
                            current_date += timedelta(weeks=1)
                            continue

                        # Recess Week Logic? (Usually Week 7)
                        # The original code has a weird "Week 7" check that skips if date didn't change?
                        # Re-implementing original logic safely:
                        weeks_since_start = ((current_date - term_start).days // 7) + 1
                        if weeks_since_start == 7:
                            # If it's literally recess week, we skip? 
                            # Or is "Recess Week" handled by the portal not outputting date ranges?
                            # The portal usually gives specific date ranges that EXCLUDE recess week if broken up.
                            # But if it's one continuous block, we might need to manually skip using the "Week 7" rule.
                            # Existing logic:
                            if current_date != c['start_date']: 
                                current_date += timedelta(weeks=1)
                                continue

                        raw_loc = c['loc']
                        final_loc = raw_loc
                        
                        loc_match = re.search(r'(\d)\.(\d)(\d{2})', raw_loc)
                        if loc_match:
                            bldg, level, room = loc_match.groups()
                            final_loc = f"Building {bldg}, Level {level} ({raw_loc})"

                        subject = display_name
                        if multi_type:
                            subject += f" {friendly_type}"

                        start_dt_str = f"{current_date.isoformat()} {c['start_time'].strftime('%H:%M')}"
                        end_dt_str = f"{current_date.isoformat()} {c['end_time'].strftime('%H:%M')}"
                        
                        try:
                            start_arrow = arrow.get(start_dt_str, 'YYYY-MM-DD HH:mm').replace(tzinfo=TIMEZONE)
                            end_arrow = arrow.get(end_dt_str, 'YYYY-MM-DD HH:mm').replace(tzinfo=TIMEZONE)
                            
                            description = ', '.join(c['lecturers'])

                            final_events.append({
                                'Subject': subject,
                                'Start': start_arrow,
                                'End': end_arrow,
                                'Location': final_loc,
                                'Description': description,
                                'Reminder': reminder_minutes
                            })
                        except Exception as e:
                            logging.error(f"Event Gen Error: {e}")
                        
                        current_date += timedelta(weeks=1)
        
        return final_events

    def generate_outputs(self, events: List[Dict], filename: str = OUTPUT_ICS):
        if not events:
            self.log("No events to write.")
            return

        self.log(f"Writing to {filename}...")
        
        from ics import Calendar, Event
        from ics.alarm import DisplayAlarm
        
        cal = Calendar()
        
        for ev in events:
            e = Event()
            e.name = ev['Subject']
            e.begin = ev['Start']
            e.end = ev['End']
            e.location = ev['Location']
            e.description = ev['Description']
            
            if ev['Reminder'] > 0:
                alarm = DisplayAlarm(trigger=timedelta(minutes=-ev['Reminder']))
                e.alarms.append(alarm)

            cal.events.add(e)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(cal.serialize())
            self.log(f"Success: File saved.")
        except PermissionError:
            raise PermissionError(f"Cannot write to {filename}. The file is open in another program.")

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        self.driver = None

    @staticmethod
    def _parse_date_str(date_str) -> date:
        return date(*map(int, date_str.split('/')[::-1]))

    @staticmethod
    def _parse_time_str(time_str) -> dt_time:
        fmt = "%I:%M%p" if "M" in time_str.upper() else "%H:%M"
        t = time.strptime(time_str, fmt)
        return dt_time(t.tm_hour, t.tm_min)

# --- 4. MODERN UI (Wizard Style) ---

try:
    from packaging import version
except ImportError:
    pass # Handle gracefully or rely on self-installer

class UpdateChecker:
    REPO_API = "https://api.github.com/repos/raghav0818/SUTD-CALENDAR-BOT/releases/latest"
    CURRENT_VERSION = "2.0.0" 

    @staticmethod
    def check_for_updates():
        """Returns (has_update, new_version_tag, download_url) or (False, None, None)"""
        try:
            resp = requests.get(UpdateChecker.REPO_API, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                latest_tag = data.get("tag_name", "0.0.0").lstrip("v")
                
                # Simple version compare
                try:
                    if version.parse(latest_tag) > version.parse(UpdateChecker.CURRENT_VERSION):
                        return True, latest_tag, data.get("html_url", "")
                except:
                    pass # 'packaging' might not be available or tags malformed
        except:
            pass
        return False, None, None

class SUTDCalendarWizard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"SUTD Calendar Bot v{UpdateChecker.CURRENT_VERSION}")
        self.geometry("800x600")
        
        self.bot = SUTDCalendarBot(log_callback=self.log_callback)
        self.courses_data = [] # Stores parsed data
        self.cookies = None    # Stores session cookies
        
        # Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Main Content area grows

        # 1. HEADER
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        
        self.title_lbl = ctk.CTkLabel(self.header, text="SUTD CALENDAR BOT", font=("Roboto Medium", 18))
        self.title_lbl.pack(side="left", padx=20, pady=15)
        
        self.step_lbl = ctk.CTkLabel(self.header, text="Step 1 of 4", font=("Roboto", 12), text_color="gray")
        self.step_lbl.pack(side="right", padx=20)

        # 2. MAIN CONTENT CONTAINER
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        # 3. FOOTER (Logs & Nav)
        self.footer = ctk.CTkFrame(self, height=40, fg_color="transparent")
        self.footer.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        self.status_lbl = ctk.CTkLabel(self.footer, text="Ready", text_color="gray", anchor="w")
        self.status_lbl.pack(side="left", fill="x", expand=True)

        # Initialize Steps
        self.show_step_1_welcome()
        
        # Check updates in background
        threading.Thread(target=self.run_update_check, daemon=True).start()

    def log_callback(self, msg):
        # Update status bar safely
        self.after(0, lambda: self.status_lbl.configure(text=msg))

    def run_update_check(self):
        has_update, new_ver, url = UpdateChecker.check_for_updates()
        if has_update:
            msg = f"Update Available (v{new_ver})!"
            self.after(0, lambda: self.show_update_btn(msg, url))

    def show_update_btn(self, msg, url):
        btn = ctk.CTkButton(self.header, text=msg, fg_color="#E63946", hover_color="#D62828",
                            command=lambda: webbrowser.open(url))
        btn.pack(side="right", padx=10)

    def set_step(self, num, title):
        self.step_lbl.configure(text=f"Step {num} of 4: {title}")
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # --- STEP 1: WELCOME ---
    def show_step_1_welcome(self):
        self.set_step(1, "Start")
        
        # Hero Section
        ctk.CTkLabel(self.main_frame, text="Generate your SUTD Calendar", font=("Roboto", 24, "bold")).pack(pady=(40, 10))
        
        info_text = (
            "This bot will:\n"
            "1. Securely log you into the SUTD Portal.\n"
            "2. Extract your class schedule automatically.\n"
            "3. Generate an .ics file for Google/Apple Calendar."
        )
        ctk.CTkLabel(self.main_frame, text=info_text, font=("Roboto", 14), justify="left").pack(pady=10)
        
        # --- TERM AND CLASS INPUTS ---
        input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        input_frame.pack(pady=20)
        
        ctk.CTkLabel(input_frame, text="Required Information:", font=("Roboto", 14, "bold")).pack(pady=(0, 10))
        
        fields_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        fields_row.pack()
        
        ctk.CTkLabel(fields_row, text="Term:", font=("Roboto", 12)).pack(side="left", padx=5)
        self.term_var = ctk.StringVar()
        ctk.CTkEntry(fields_row, textvariable=self.term_var, width=60, placeholder_text="5").pack(side="left", padx=5)
        
        ctk.CTkLabel(fields_row, text="Class:", font=("Roboto", 12)).pack(side="left", padx=(15, 5))
        self.class_var = ctk.StringVar()
        ctk.CTkEntry(fields_row, textvariable=self.class_var, width=60, placeholder_text="03").pack(side="left", padx=5)
        
        # Action
        start_btn = ctk.CTkButton(self.main_frame, text="GET STARTED >", width=200, height=50, 
                                  font=("Roboto", 14, "bold"), command=self.validate_and_continue)
        start_btn.pack(pady=30)

        ctk.CTkLabel(self.main_frame, text="Requires 'One-Stop' portal access.", text_color="gray").pack()

    def validate_and_continue(self):
        """Validate inputs before proceeding to login"""
        term = self.term_var.get().strip()
        cls = self.class_var.get().strip()
        
        if not term or not cls:
            messagebox.showwarning("Missing Information", "Please enter both your Term and Class number before continuing.")
            return
        
        self.show_step_2_login()


    # --- STEP 2: LOGIN ---
    def show_step_2_login(self):
        self.set_step(2, "Secure Login")
        
        ctk.CTkLabel(self.main_frame, text="Authentication Required", font=("Roboto", 20, "bold")).pack(pady=(20, 10))
        
        instr_frame = ctk.CTkFrame(self.main_frame)
        instr_frame.pack(fill="x", padx=40, pady=20)
        
        instr = (
            "1. Click the button below to open a browser window.\n"
            "2. Log in with your SUTD ID and perform 2FA.\n"
            "3. Wait for the window to close automatically."
        )
        ctk.CTkLabel(instr_frame, text=instr, font=("Roboto", 14), justify="left", padx=20, pady=20).pack(anchor="w")

        self.login_btn = ctk.CTkButton(self.main_frame, text="AUTHENTICATE WITH SUTD", width=250, height=50,
                                       font=("Roboto", 14, "bold"), command=self.start_login_process)
        self.login_btn.pack(pady=10)

        self.loading_spinner = ctk.CTkProgressBar(self.main_frame, width=300, mode="indeterminate")
        # Hidden by default

    def start_login_process(self):
        self.login_btn.configure(state="disabled", text="WAITING FOR LOGIN...")
        self.loading_spinner.pack(pady=20)
        self.loading_spinner.start()
        
        threading.Thread(target=self.thread_login_task, daemon=True).start()

    def thread_login_task(self):
        try:
            # 1. Login & Scrape (Single Session)
            self.bot.log("Waiting for user login...")
            raw_text = self.bot.start_login_and_scrape()
            
            # 2. Parse
            courses = self.bot.parse_raw_data(raw_text)
            
            # 3. Success -> UI
            self.after(0, self.show_step_3_review, courses)
            
        except Exception as e:
            self.bot.log(f"Error: {e}")
            self.after(0, lambda: messagebox.showerror("Login/Scan Error", f"An error occurred:\n{e}\n\nPlease try again."))
            self.after(0, self.reset_step_2)

    def reset_step_2(self):
        self.login_btn.configure(state="normal", text="AUTHENTICATE WITH SUTD")
        self.loading_spinner.stop()
        self.loading_spinner.pack_forget()

    # --- STEP 3: REVIEW ---
    def show_step_3_review(self, courses):
        self.courses_data = courses
        self.set_step(3, "Review & Customize")
        
        # Load Config for defaults
        saved_config = {}
        if os.path.exists(CONFIG_FILE):
             try:
                 with open(CONFIG_FILE, 'r') as f:
                     saved_config = json.load(f).get("courses", {})
             except: pass
        
        
        # Top Controls
        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(top_frame, text="Found Courses:", font=("Roboto", 14, "bold")).pack(side="left")
        
        self.selection_vars = {}
        self.name_vars = {}

        # Scroll Area
        scroll = ctk.CTkScrollableFrame(self.main_frame, label_text="Uncheck classes you don't want")
        scroll.pack(fill="both", expand=True, pady=10)

        for i, course in enumerate(courses):
            c_code = course['code']
            c_name = course['name']
            
            # Default name from config?
            default_name = saved_config.get(c_code, {}).get("custom_name", c_name)
            
            card = ctk.CTkFrame(scroll)
            card.pack(fill="x", padx=5, pady=5)
            
            # Header
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(header, text=c_code, width=80, anchor="w", font=("Roboto", 12, "bold")).pack(side="left")
            
            # Rename Field
            name_var = ctk.StringVar(value=default_name)
            self.name_vars[i] = name_var
            ctk.CTkEntry(header, textvariable=name_var, height=28).pack(side="left", fill="x", expand=True, padx=5)

            # Checkboxes
            chk_frame = ctk.CTkFrame(card, fg_color="transparent")
            chk_frame.pack(fill="x", padx=10, pady=2)
            
            for type_code in course['type'].keys():
                friendly = TYPE_MAPPING.get(type_code, type_code)
                var = ctk.BooleanVar(value=True)
                self.selection_vars[(i, type_code)] = var
                ctk.CTkCheckBox(chk_frame, text=friendly, variable=var).pack(side="left", padx=10)

        # Bottom Bar
        bot_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        bot_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(bot_frame, text="Reminder (min):").pack(side="left")
        self.rem_var = ctk.StringVar(value="15")
        ctk.CTkEntry(bot_frame, textvariable=self.rem_var, width=50).pack(side="left", padx=5)

        ctk.CTkButton(bot_frame, text="GENERATE .ICS FILE", width=200, height=40, font=("Roboto", 13, "bold"),
                      command=self.generate_course_files).pack(side="right")

    def generate_course_files(self):
        filtered_courses = []
        config_to_save = {}
        
        for i, course in enumerate(self.courses_data):
            # 1. Update Name
            custom_name = self.name_vars[i].get()
            
            # 2. Filter Types
            selected_types = {}
            for t_code, t_data in course['type'].items():
                if self.selection_vars[(i, t_code)].get():
                    selected_types[t_code] = t_data
            
            if selected_types:
                new_c = course.copy()
                new_c['name'] = custom_name
                new_c['type'] = selected_types
                filtered_courses.append(new_c)
                
                config_to_save[course['code']] = {"custom_name": custom_name}

        # Save Config
        try:
            full_config = {"courses": config_to_save, "settings": {"default_reminder": int(self.rem_var.get())}}
            with open(CONFIG_FILE, 'w') as f:
                json.dump(full_config, f, indent=4)
        except: pass
        
        # Determine Filename
        term = self.term_var.get().strip()
        cls_val = self.class_var.get().strip()
        
        final_filename = OUTPUT_ICS 
        if term and cls_val:
            # SUTD_Term_5_Class_03.ics
            final_filename = f"SUTD_Term_{term}_Class_{cls_val}.ics"
        
        # Generate
        try:
             events = self.bot.expand_events(filtered_courses, reminder_minutes=int(self.rem_var.get()))
             self.bot.generate_outputs(events, filename=final_filename)
             self.show_step_4_success(final_filename)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- STEP 4: SUCCESS ---
    def show_step_4_success(self, filename: str):
        self.set_step(4, "All Done!")
        
        icon_lbl = ctk.CTkLabel(self.main_frame, text="✔️", font=("Arial", 60), text_color="#4CAF50")
        icon_lbl.pack(pady=(40, 10))
        
        ctk.CTkLabel(self.main_frame, text="Calendar Generated Successfully!", font=("Roboto", 20, "bold")).pack()
        
        path = os.path.abspath(filename)
        
        # File info box
        file_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        file_frame.pack(pady=10)
        ctk.CTkLabel(file_frame, text="Saved to:", text_color="gray").pack()
        ctk.CTkLabel(file_frame, text=path, font=("Consolas", 10), wraplength=700).pack()
        
        # Actions
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=40)
        
        ctk.CTkButton(btn_frame, text="Open Folder", command=self.open_output_folder).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Exit", fg_color="gray", command=self.quit).pack(side="left", padx=10)

    def open_output_folder(self):
        path = os.path.abspath(".")
        if os.name == 'nt':
            os.startfile(path)
        else:
            # mac/linux fallback
            import subprocess
            try:
                subprocess.call(['open', path])
            except: pass

if __name__ == "__main__":
    app = SUTDCalendarWizard()
    app.mainloop()
