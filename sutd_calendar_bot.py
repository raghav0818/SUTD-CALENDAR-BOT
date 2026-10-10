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
    "selenium": "selenium>=4.0.0",
    "customtkinter": "customtkinter>=5.2.0",
    "ics": "ics>=0.7",
    "arrow": "arrow",
    "requests": "requests>=2.31.0",
    "urllib3": "urllib3==1.26.18" # Specific version for stability
}

def check_and_install_dependencies():
    """Checks if required packages are installed. If not, installs them."""
    missing = []
    for package_name, install_name in REQUIRED_PACKAGES.items():
        if importlib.util.find_spec(package_name) is None:
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
            print(f"   {sys.executable} -m pip install -r requirements.txt")
            input("Press Enter to exit...")
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] Unexpected setup error: {e}")
            input("Press Enter to exit...")
            sys.exit(1)

# Run the check immediately
check_and_install_dependencies()

# --- PART 2: MAIN APPLICATION ---
# Now that dependencies are guaranteed, we can import them safely.

import re
import json
import csv
import arrow
import threading
import logging
import requests
import customtkinter as ctk
from tkinter import messagebox
from datetime import date, timedelta, datetime, time as dt_time
from typing import List, Dict, Optional, Tuple

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, SessionNotCreatedException

# ICS Library Imports
from ics import Calendar, Event
from ics.alarm import DisplayAlarm


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
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
OUTPUT_ICS = os.path.join(DESKTOP_PATH, "SUTD_Calendar.ics")
OUTPUT_CSV = os.path.join(DESKTOP_PATH, "SUTD_Schedule.csv")
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

class SUTDCalendarBot:
    def __init__(self, log_callback=None):
        self.driver: Optional[webdriver.Remote] = None
        self.wait: Optional[WebDriverWait] = None
        self.log_callback = log_callback

    def log(self, message):
        logging.info(message) 
        if self.log_callback:
            self.log_callback(message) 
        else:
            print(message)

    def start_browser(self):
        self.log("Starting Browser...")
        
        try:
            options = webdriver.ChromeOptions()
            options.add_experimental_option("detach", True)
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 15)
            self.log("Google Chrome started successfully.")
            return
        except Exception as e:
            logging.warning(f"Chrome failed to start: {e}")
            self.log("Chrome not found or failed. Checking for alternatives...")

        if sys.platform == "darwin":
            self.log("Attempting to launch Safari...")
            try:
                self.driver = webdriver.Safari()
                self.driver.maximize_window()
                self.wait = WebDriverWait(self.driver, 15)
                self.log("Safari started successfully.")
                return
            except Exception as e:
                logging.error(f"Safari failed: {e}")
                raise RuntimeError(f"Safari failed to start. Error: {e}")

        raise RuntimeError("Could not find Google Chrome. Please install Chrome (or enable Safari automation if on Mac).")

    def login_and_prepare_grid(self):
        """Logs in and clicks the necessary checkboxes to display Title and Instructors."""
        if not self.driver or not self.wait:
            raise RuntimeError("Browser not started!")

        try:
            self.log("Navigating to portal...")
            self.driver.get("https://ease.sutd.edu.sg/app/sutd_myportal_1/exk3pseb8o4VxzQF85d7/sso/saml")

            self.log("Waiting for Manual Login...")
            self.log("ACTION REQUIRED: Log in & do 2FA in the browser window.")
            
            mfa_wait = WebDriverWait(self.driver, 120) 
            mfa_wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "PSHYPERLINKNOUL"))).click()
            self.log("Login detected! Proceeding...")

            self.wait.until(EC.element_to_be_clickable((By.ID, "ADMN_S20160108140638335703604"))).click()
            self.log("Opened Weekly Schedule...")

            self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "ptifrmtgtframe")))

            # 1. Check Title Box
            title_checkbox = self.wait.until(EC.presence_of_element_located((By.ID, "DERIVED_CLASS_S_SSR_DISP_TITLE")))
            if not title_checkbox.is_selected():
                title_checkbox.click()
                time.sleep(0.5) 
            
            # 2. Check Instructor Box
            instr_checkbox = self.wait.until(EC.presence_of_element_located((By.ID, "DERIVED_CLASS_S_SHOW_INSTR")))
            if not instr_checkbox.is_selected():
                instr_checkbox.click()
                time.sleep(0.5)
            
            # 3. Click Refresh Calendar
            self.log("Refreshing Grid Details...")
            refresh_btn = self.driver.find_element(By.ID, "DERIVED_CLASS_S_SSR_REFRESH_CAL$38$")
            refresh_btn.click()
            
            # Wait for reload
            time.sleep(3)
            self.log("Calendar grid ready for extraction.")

        except TimeoutException:
            raise TimeoutException("Login timed out. Please try again and ensure you complete 2FA.")
        except Exception as e:
            logging.error(f"Navigation Error: {e}", exc_info=True)
            self.log(f"Error preparing grid: {e}")
            raise

    def scrape_calendar_grid(self) -> Tuple[List[Dict], List[Dict]]:
        """Paginates through the weeks, extracts cell data via Visual Geometry & Line Parsing, and returns courses & raw events."""
        driver = self.driver
        if driver is None:
            raise RuntimeError("Browser not started!")

        all_events = []
        courses_summary = {}

        # Max 16 weeks to prevent infinite loops (standard term + recess)
        for week_idx in range(16):
            self.log(f"Scraping Week {week_idx + 1}...")
            
            # 1. Get the current week's starting date
            body_text = driver.find_element(By.TAG_NAME, "body").text
            week_match = re.search(r"Week of\s*(\d{1,2}/\d{1,2}/\d{4})", body_text)
            
            if week_match:
                week_start_str = week_match.group(1)
                week_start_date = arrow.get(week_start_str, ["D/M/YYYY", "DD/MM/YYYY"]).date()
            else:
                self.log("Could not detect week start date. Finished scraping.")
                break

            # 2. Map Day Headers by X-Coordinate to bypass HTML rowspan issues
            day_headers = driver.find_elements(By.XPATH, "//th[contains(., 'Monday') or contains(., 'Tuesday') or contains(., 'Wednesday') or contains(., 'Thursday') or contains(., 'Friday') or contains(., 'Saturday') or contains(., 'Sunday')]")
            
            day_coords = []
            for header in day_headers:
                text = header.text.strip()
                # Ensure it's actually a day header
                if any(day in text for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
                    day_coords.append({
                        'x': header.location['x'],
                        'width': header.size['width']
                    })
            
            # Sort left-to-right and remove duplicates (sometimes hidden elements exist)
            day_coords.sort(key=lambda d: d['x'])
            unique_day_coords = []
            for dc in day_coords:
                if not unique_day_coords or abs(dc['x'] - unique_day_coords[-1]['x']) > 10:
                    unique_day_coords.append(dc)

            if len(unique_day_coords) < 7:
                self.log(f"Warning: Only found {len(unique_day_coords)} day columns. Grid parsing might be slightly off.")

            # 3. Scan EVERY cell in the table body visually
            all_tds = driver.find_elements(By.XPATH, "//td")
            for td in all_tds:
                cell_text = td.get_attribute("innerText").strip()
                
                # Fast filter: Does it contain a time format? If not, skip it.
                if not re.search(r'\d{1,2}:\d{2}[AP]M\s*-\s*\d{1,2}:\d{2}[AP]M', cell_text):
                    continue

                # 4. Map cell to date using X-Coordinate geometry
                cell_center = td.location['x'] + (td.size['width'] / 2)
                matched_day_idx = 0
                min_dist = float('inf')
                
                for i, day in enumerate(unique_day_coords):
                    day_center = day['x'] + (day['width'] / 2)
                    dist = abs(cell_center - day_center)
                    if dist < min_dist:
                        min_dist = dist
                        matched_day_idx = i
                
                current_date = week_start_date + timedelta(days=matched_day_idx)

                # 5. Parse cell text Line-by-Line (Safely handling 'Time Conflict')
                chunks = re.split(r'\bTime Conflict\b', cell_text, flags=re.IGNORECASE)
                for chunk in chunks:
                    lines = [line.strip() for line in chunk.split('\n') if line.strip()]
                    if not lines: continue
                    
                    # Find the time line index to anchor our parsing
                    time_line_idx = -1
                    for idx, line in enumerate(lines):
                        if re.search(r'\d{1,2}:\d{2}[AP]M\s*-\s*\d{1,2}:\d{2}[AP]M', line):
                            time_line_idx = idx
                            break
                    
                    # Ensure we have enough context lines (Code/Section, Type, Time)
                    if time_line_idx >= 2:
                        # Extract Code & Section (Line 0)
                        code_sec_match = re.match(r'(?P<code>\d{2}\s*\.\d{3})\s*-\s*(?P<section>\w+)', lines[0])
                        if not code_sec_match: continue
                        
                        code = code_sec_match.group('code').replace(' ', '')
                        section = code_sec_match.group('section')
                        
                        # Extract Type and Title
                        ctype = lines[time_line_idx - 1]
                        title = " ".join(lines[1:time_line_idx - 1]) if time_line_idx > 2 else "Unknown Course"
                        
                        # Extract Times
                        time_str = lines[time_line_idx]
                        time_match = re.search(r'(?P<start>\d{1,2}:\d{2}[AP]M)\s*-\s*(?P<end>\d{1,2}:\d{2}[AP]M)', time_str)
                        if not time_match: continue
                        start_time = time_match.group('start')
                        end_time = time_match.group('end')
                        
                        # Extract Location & Instructors
                        location = lines[time_line_idx + 1] if time_line_idx + 1 < len(lines) else "Unknown Location"
                        
                        instructors_str = " ".join(lines[time_line_idx + 2:])
                        if "Instructors:" in instructors_str:
                            instructors_str = instructors_str.replace("Instructors:", "").strip()
                            instructors_str = ", ".join([i.strip() for i in instructors_str.split(',') if i.strip()])
                        elif not instructors_str:
                            instructors_str = "Staff"

                        event = {
                            'code': code,
                            'section': section,
                            'title': title,
                            'type': ctype,
                            'date': current_date,
                            'start_time': start_time,
                            'end_time': end_time,
                            'location': location,
                            'instructors': instructors_str
                        }
                        all_events.append(event)
                        
                        # Add to UI Summary Dictionary
                        if code not in courses_summary:
                            courses_summary[code] = {'code': code, 'name': title, 'type': {}}
                        if ctype not in courses_summary[code]['type']:
                            courses_summary[code]['type'][ctype] = True

            # 6. Click Next Week Button
            try:
                next_btn = None
                try:
                    next_btn = driver.find_element(By.ID, "DERIVED_CLASS_S_SSR_NEXT_WEEK")
                except:
                    next_btn = driver.find_element(By.XPATH, "//*[@value='Next Week >>' or @title='Next Week >>']")
                
                if not next_btn or not next_btn.is_enabled():
                    break
                    
                next_btn.click()
                time.sleep(2) # Give PeopleSoft time to reload the grid via AJAX
                
            except Exception as e:
                self.log("Reached end of schedule or 'Next Week' not found.")
                break

        courses_list = list(courses_summary.values())
        self.log(f"Completed! Found {len(courses_list)} unique courses across {len(all_events)} sessions.")
        return courses_list, all_events

    def generate_outputs(self, events: List[Dict], reminder_minutes: int = 15):
        if not events:
            self.log("No events to write.")
            return

        self.log(f"Writing ICS and CSV files to Desktop...")
        cal = Calendar()
        
        # Prepare CSV configuration
        csv_keys = ["Date", "Course Code", "Section", "Title", "Type", "Start Time", "End Time", "Location", "Instructors"]
        csv_data = []
        
        for ev in events:
            # Add to CSV row list
            csv_data.append({
                "Date": ev['date'].strftime('%Y-%m-%d'),
                "Course Code": ev['code'],
                "Section": ev['section'],
                "Title": ev['title'],
                "Type": ev['type'],
                "Start Time": ev['start_time'],
                "End Time": ev['end_time'],
                "Location": ev['location'],
                "Instructors": ev['instructors']
            })

            # Add to ICS Event
            e = Event()
            friendly_type = TYPE_MAPPING.get(ev['type'], ev['type'])
            e.name = f"{ev['title']} ({friendly_type})"
            
            start_str = f"{ev['date'].isoformat()} {ev['start_time']}"
            end_str = f"{ev['date'].isoformat()} {ev['end_time']}"
            
            e.begin = arrow.get(start_str, ['YYYY-MM-DD h:mmA', 'YYYY-MM-DD H:mm']).replace(tzinfo=TIMEZONE)
            e.end = arrow.get(end_str, ['YYYY-MM-DD h:mmA', 'YYYY-MM-DD H:mm']).replace(tzinfo=TIMEZONE)
            e.location = ev['location']
            e.description = f"Course: {ev['code']} {ev['section']}\nInstructors: {ev['instructors']}"
            
            if reminder_minutes > 0:
                e.alarms.append(DisplayAlarm(trigger=timedelta(minutes=-reminder_minutes)))

            cal.events.add(e)

        try:
            with open(OUTPUT_ICS, 'w', encoding='utf-8') as f:
                f.write(cal.serialize())
                
            with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as output_file:
                dict_writer = csv.DictWriter(output_file, fieldnames=csv_keys)
                dict_writer.writeheader()
                dict_writer.writerows(csv_data)
                
            self.log(f"Saved Calendar: {OUTPUT_ICS}")
            self.log(f"Saved Excel Data: {OUTPUT_CSV}")
        except PermissionError:
            raise PermissionError(f"Cannot write files. Ensure they are not open in Excel/Calendar and try again.")

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


# --- 4. MODERN UI (CustomTkinter) ---

class ConflictDialog(ctk.CTkToplevel):
    """A custom modal dialog to resolve time conflicts."""
    def __init__(self, parent, ev1, ev2):
        super().__init__(parent)
        self.title("⚠️ Time Conflict")
        self.geometry("650x420")
        self.attributes("-topmost", True)
        self.choice = "both"
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Center the window dynamically over the parent application
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - (650 // 2)
            y = parent.winfo_y() + (parent.winfo_height() // 2) - (420 // 2)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass
        
        lbl_warn = ctk.CTkLabel(self, text="⚠️ Time Conflict Detected!", font=("Roboto", 20, "bold"), text_color="#ff9800")
        lbl_warn.pack(pady=(20, 5))
        
        date_str = ev1['date'].strftime('%A, %d %b %Y')
        lbl_info = ctk.CTkLabel(self, text=f"Date: {date_str}\nOverlap near {ev1['start_time']} - {ev1['end_time']}", font=("Roboto", 14))
        lbl_info.pack(pady=10)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # --- Class A Card ---
        frame_a = ctk.CTkFrame(btn_frame)
        frame_a.pack(side="left", fill="both", expand=True, padx=10)
        ctk.CTkLabel(frame_a, text="OPTION A", font=("Roboto", 12, "bold"), text_color="gray").pack(pady=(10, 0))
        ctk.CTkLabel(frame_a, text=f"{ev1['code']} - {ev1['section']}", font=("Roboto", 14, "bold")).pack()
        ctk.CTkLabel(frame_a, text=f"{ev1['title']}", font=("Roboto", 12), wraplength=250).pack(pady=5)
        ctk.CTkLabel(frame_a, text=f"{ev1['type']}\n{ev1['start_time']} - {ev1['end_time']}\n{ev1['location']}", font=("Roboto", 12)).pack(pady=5)
        
        btn_a = ctk.CTkButton(frame_a, text="Keep Class A", command=lambda: self.set_choice('ev1'), fg_color="#2ecc71", hover_color="#27ae60")
        btn_a.pack(pady=15, side="bottom")
        
        # --- Class B Card ---
        frame_b = ctk.CTkFrame(btn_frame)
        frame_b.pack(side="right", fill="both", expand=True, padx=10)
        ctk.CTkLabel(frame_b, text="OPTION B", font=("Roboto", 12, "bold"), text_color="gray").pack(pady=(10, 0))
        ctk.CTkLabel(frame_b, text=f"{ev2['code']} - {ev2['section']}", font=("Roboto", 14, "bold")).pack()
        ctk.CTkLabel(frame_b, text=f"{ev2['title']}", font=("Roboto", 12), wraplength=250).pack(pady=5)
        ctk.CTkLabel(frame_b, text=f"{ev2['type']}\n{ev2['start_time']} - {ev2['end_time']}\n{ev2['location']}", font=("Roboto", 12)).pack(pady=5)
        
        btn_b = ctk.CTkButton(frame_b, text="Keep Class B", command=lambda: self.set_choice('ev2'), fg_color="#3498db", hover_color="#2980b9")
        btn_b.pack(pady=15, side="bottom")
        
        # --- Keep Both Button ---
        btn_both = ctk.CTkButton(self, text="Keep Both (Ignore)", command=lambda: self.set_choice('both'), fg_color="gray", hover_color="#555")
        btn_both.pack(pady=15)
        
        # Make the window modal to intercept user interaction
        self.grab_set()

    def set_choice(self, choice):
        self.choice = choice
        self.grab_release()
        self.destroy()

    def on_close(self):
        # Default to keeping both if they force-close the window via 'X'
        self.set_choice('both')


class CalendarApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SUTD Schedule Export")
        self.geometry("750x850") 
        
        self.bot = SUTDCalendarBot(log_callback=self.update_log)
        self.courses_data = []
        self.all_events = [] # Stores all raw scheduled sessions across the term
        
        self.selection_vars = {} 
        self.name_vars = {} 
        self.config_data = self.load_config() 

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) 

        # 1. HEADER
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        self.title_lbl = ctk.CTkLabel(self.header_frame, text="SUTD CALENDAR BOT", font=("Roboto Medium", 20))
        self.title_lbl.pack(side="left")
        
        self.subtitle_lbl = ctk.CTkLabel(self.header_frame, text="Smart .ics & .csv Generator", font=("Roboto", 12), text_color="gray")
        self.subtitle_lbl.pack(side="left", padx=10, pady=(8,0))

        # 2. CONTROL PANEL
        self.ctrl_frame = ctk.CTkFrame(self)
        self.ctrl_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        
        self.instr_lbl = ctk.CTkLabel(self.ctrl_frame, 
                                      text="STEP 1: Click 'Start Login & Scan' to begin.", 
                                      font=("Roboto", 14), anchor="w")
        self.instr_lbl.pack(fill="x", padx=15, pady=(15, 5))

        self.start_btn = ctk.CTkButton(self.ctrl_frame, text="START LOGIN & SCAN", 
                                       command=self.start_process, 
                                       font=("Roboto", 12, "bold"), height=40)
        self.start_btn.pack(side="left", padx=15, pady=15)

        self.status_lbl = ctk.CTkLabel(self.ctrl_frame, text="Ready", text_color="gray")
        self.status_lbl.pack(side="left", padx=15)

        # 3. LIST FRAME (Scrollable)
        self.list_lbl_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_lbl_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        
        self.list_header = ctk.CTkFrame(self.list_lbl_frame, height=30, fg_color="transparent")
        self.list_header.pack(fill="x")
        ctk.CTkLabel(self.list_header, text="DETECTED COURSES", font=("Roboto", 12, "bold")).pack(side="left")
        
        self.btn_all = ctk.CTkButton(self.list_header, text="Select All", width=60, height=20, font=("Roboto", 10), command=lambda: self.toggle_all(True))
        self.btn_all.pack(side="right", padx=5)
        self.btn_none = ctk.CTkButton(self.list_header, text="Select None", width=60, height=20, font=("Roboto", 10), command=lambda: self.toggle_all(False))
        self.btn_none.pack(side="right")

        self.scroll_area = ctk.CTkScrollableFrame(self.list_lbl_frame, label_text="Course List")
        self.scroll_area.pack(fill="both", expand=True)

        # 4. SETTINGS & GENERATE
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=20)

        ctk.CTkLabel(self.bottom_frame, text="Reminder (min):").pack(side="left", padx=(15, 5))
        
        saved_reminder = self.config_data.get("settings", {}).get("default_reminder", 15)
        self.reminder_var = ctk.StringVar(value=str(saved_reminder))
        self.rem_entry = ctk.CTkEntry(self.bottom_frame, textvariable=self.reminder_var, width=50)
        self.rem_entry.pack(side="left")

        self.gen_btn = ctk.CTkButton(self.bottom_frame, text="GENERATE CSV & ICS FILES", 
                                     command=self.generate_files, 
                                     font=("Roboto", 14, "bold"), 
                                     height=50, state="disabled")
        self.gen_btn.pack(side="right", padx=15, pady=15, fill="x", expand=True)
        
        # 5. LOG BOX
        self.log_box = ctk.CTkTextbox(self, height=80, font=("Consolas", 10))
        self.log_box.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.log_box.insert("0.0", "System Ready. Config loaded.\n")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config(self, processed_courses, reminder_val):
        config = self.config_data
        
        if "settings" not in config: config["settings"] = {}
        config["settings"]["default_reminder"] = reminder_val

        if "courses" not in config: config["courses"] = {}
        for c in processed_courses:
            config["courses"][c['code']] = {
                "custom_name": c['name'],
            }
            
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            self.update_log("Preferences saved.")
        except Exception as e:
            self.update_log(f"Failed to save config: {e}")

    def update_log(self, message):
        self.after(0, self._append_log, message)

    def _append_log(self, message):
        self.status_lbl.configure(text=message) 
        self.log_box.insert("end", f"> {message}\n")
        self.log_box.see("end")

    def start_process(self):
        self.start_btn.configure(state="disabled")
        threading.Thread(target=self.run_selenium_task, daemon=True).start()

    def run_selenium_task(self):
        try:
            self.bot.start_browser()
            self.bot.login_and_prepare_grid()
            courses, all_events = self.bot.scrape_calendar_grid()
            self.bot.close()
            
            try:
                self.after(0, lambda: self.state('zoomed'))
            except: pass

            # Intecept with the conflict resolver instead of going straight to the UI
            self.after(0, self.start_conflict_resolution, courses, all_events)
        except Exception as e:
            logging.error(f"Selenium Task Error: {e}", exc_info=True)
            self.after(0, messagebox.showerror, "Error", str(e))
            self.after(0, self.reset_ui)
            if self.bot.driver: self.bot.close()

    @staticmethod
    def _times_overlap(start1_str, end1_str, start2_str, end2_str):
        """Helper function to calculate if two 12-hour time intervals overlap."""
        fmt = "%I:%M%p"
        try:
            s1 = datetime.strptime(start1_str, fmt).time()
            e1 = datetime.strptime(end1_str, fmt).time()
            s2 = datetime.strptime(start2_str, fmt).time()
            e2 = datetime.strptime(end2_str, fmt).time()
            return s1 < e2 and s2 < e1
        except Exception:
            return False

    def start_conflict_resolution(self, courses, all_events):
        self.courses_data = courses
        self.all_events = all_events
        
        # 1. Deduplicate the raw scrape first to prevent false alarms
        unique_events = []
        seen = set()
        for ev in self.all_events:
            ev_tuple = (ev['code'], ev['type'], ev['date'], ev['start_time'])
            if ev_tuple not in seen:
                seen.add(ev_tuple)
                unique_events.append(ev)
        self.all_events = unique_events

        # 2. Iterate through events and resolve conflicts interactively
        ignored_pairs = set()
        
        while True:
            conflict_pair = None
            
            # Scan for the first active conflict
            for i in range(len(self.all_events)):
                for j in range(i + 1, len(self.all_events)):
                    ev1 = self.all_events[i]
                    ev2 = self.all_events[j]
                    
                    pair_id = frozenset([id(ev1), id(ev2)])
                    if pair_id in ignored_pairs:
                        continue
                        
                    # If it's the exact same course/type (edge case), ignore as conflict
                    if ev1['code'] == ev2['code'] and ev1['type'] == ev2['type']:
                        continue
                        
                    if ev1['date'] == ev2['date'] and self._times_overlap(ev1['start_time'], ev1['end_time'], ev2['start_time'], ev2['end_time']):
                        conflict_pair = (i, j, pair_id)
                        break
                if conflict_pair:
                    break
                    
            # If no conflicts found, break the while loop and move to final UI
            if not conflict_pair:
                break 
                
            i, j, pair_id = conflict_pair
            ev1 = self.all_events[i]
            ev2 = self.all_events[j]
            
            self.update_log(f"Resolving clash: {ev1['code']} vs {ev2['code']}")
            
            # Spawn modal and wait for user response
            dialog = ConflictDialog(self, ev1, ev2)
            self.wait_window(dialog)
            
            # Apply user decision
            if dialog.choice == 'ev1':
                self.all_events.pop(j) # Destroy Class B
            elif dialog.choice == 'ev2':
                self.all_events.pop(i) # Destroy Class A
            else:
                ignored_pairs.add(pair_id) # Remember that they wanted to keep both

        # 3. Finished resolving! Proceed to normal selection UI
        self.show_selection_ui(self.courses_data, self.all_events)

    def show_selection_ui(self, courses, all_events):
        self.courses_data = courses
        self.all_events = all_events
        self.start_btn.configure(text="RESCAN", state="normal", fg_color="#333")
        self.gen_btn.configure(state="normal")
        
        instructions = (
            "STEP 2: CUSTOMIZE\n"
            "• Rename: Edit text boxes.\n"
            "• Filter: Uncheck unwanted classes.\n"
            "• Finalize: Click Generate."
        )
        self.instr_lbl.configure(text=instructions)

        for widget in self.scroll_area.winfo_children():
            widget.destroy()
            
        self.selection_vars = {}
        self.name_vars = {}
        
        self.update_log("Review courses and generate.")

        if not courses:
             ctk.CTkLabel(self.scroll_area, text="No courses found in schedule!", text_color="red").pack(pady=20)
             self.gen_btn.configure(state="disabled")
             return

        for i, course in enumerate(courses):
            card = ctk.CTkFrame(self.scroll_area)
            card.pack(fill="x", padx=5, pady=5)
            
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(header, text=course['code'], font=("Roboto", 12, "bold"), text_color="gray").pack(side="left")
            
            saved_courses = self.config_data.get("courses", {})
            saved_info = saved_courses.get(course['code'], {})
            default_name = saved_info.get("custom_name", course['name'])

            name_var = ctk.StringVar(value=default_name)
            self.name_vars[i] = name_var
            
            name_entry = ctk.CTkEntry(header, textvariable=name_var, height=28)
            name_entry.pack(side="left", fill="x", expand=True, padx=10)
            
            chk_frame = ctk.CTkFrame(card, fg_color="transparent")
            chk_frame.pack(fill="x", padx=10, pady=5)

            for type_code in course['type'].keys():
                friendly_name = str(TYPE_MAPPING.get(type_code) or type_code)
                var = ctk.BooleanVar(value=True)
                chk = ctk.CTkCheckBox(chk_frame, text=friendly_name, variable=var)
                chk.pack(side="left", padx=10)
                self.selection_vars[(i, type_code)] = var

    def toggle_all(self, state):
        for var in self.selection_vars.values():
            var.set(state)

    def generate_files(self):
        filtered_events = []
        
        # 1. Map out which (course index, type) are checked
        allowed_types = {}
        for (i, t), var in self.selection_vars.items():
            allowed_types[(i, t)] = var.get()
            
        # 2. Get the custom renamed text
        custom_names = {}
        for i, course in enumerate(self.courses_data):
            custom_names[course['code']] = self.name_vars[i].get() or course['name']

        # 3. Filter the massive raw events list based on UI selections
        for ev in self.all_events:
            course_idx = next((i for i, c in enumerate(self.courses_data) if c['code'] == ev['code']), -1)
            
            if course_idx != -1 and allowed_types.get((course_idx, ev['type']), False):
                ev_copy = ev.copy()
                ev_copy['title'] = custom_names[ev['code']]
                filtered_events.append(ev_copy)

        self.update_log(f"Processing {len(filtered_events)} class sessions...")
        
        try:
            try:
                rem_mins = int(self.reminder_var.get())
            except ValueError:
                rem_mins = 15
            
            # Save configs
            processed_courses = [{'code': c['code'], 'name': custom_names[c['code']]} for c in self.courses_data]
            self.save_config(processed_courses, rem_mins)

            # Generate outputs
            self.bot.generate_outputs(filtered_events, reminder_minutes=rem_mins)
            
            self.withdraw()
            output_dir = DESKTOP_PATH
            if os.name == 'nt':
                os.startfile(output_dir)
            elif os.name == 'posix':
                try:
                    subprocess.call(['open', output_dir])
                except:
                    pass

            messagebox.showinfo("Success", f"Calendar files generated successfully!\n\nSaved to:\n{output_dir}")
            self.destroy()

        except Exception as e:
            logging.error(f"Generation Failed: {e}", exc_info=True)
            messagebox.showerror("Generation Error", str(e))

    def reset_ui(self):
        self.start_btn.configure(state="normal")

if __name__ == "__main__":
    app = CalendarApp()
    app.mainloop()