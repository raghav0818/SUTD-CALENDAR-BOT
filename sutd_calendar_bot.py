import re
import csv
import os
import sys
import time
import json
import arrow
import threading
import logging
import requests
import subprocess
import customtkinter as ctk
from tkinter import messagebox
from datetime import date, timedelta, datetime, time as dt_time
from typing import List, Dict, Optional

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

# --- 1. LOGGING CONFIGURATION ---
logging.basicConfig(
    filename='sutd_bot.log',
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

# --- 2. EXECUTABLE PATH HELPER ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- 3. DYNAMIC HOLIDAY API ---
def get_singapore_holidays() -> set[date]:
    """Fetches PH from API, falls back to hardcoded list on error."""
    holidays = set()
    years = [date.today().year, date.today().year + 1]
    
    logging.info("Fetching Public Holidays from API...")
    
    for year in years:
        try:
            url = f"https://date.nager.at/api/v3/publicholidays/{year}/SG"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            for item in data:
                h_date = arrow.get(item['date']).date()
                holidays.add(h_date)
            logging.info(f"Loaded {len(data)} holidays for {year}.")
        except Exception as e:
            logging.error(f"Failed to fetch API holidays for {year}: {e}")
            if year == 2025:
                holidays.update({date(2025, 1, 1), date(2025, 1, 29), date(2025, 1, 30), date(2025, 8, 9), date(2025, 12, 25)})
    
    return holidays

SG_HOLIDAYS = get_singapore_holidays()


class SUTDCalendarBot:
    def __init__(self, log_callback=None):
        # Using generic Remote driver to support both Chrome and Safari
        self.driver: Optional[webdriver.Remote] = None
        self.wait: Optional[WebDriverWait] = None
        self.weekday_map = ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')
        self.log_callback = log_callback

    def log(self, message):
        logging.info(message) 
        if self.log_callback:
            self.log_callback(message) 
        else:
            print(message)

    def start_browser(self):
        self.log("Starting Browser...")
        
        # --- 1. Try Chrome First (Windows & Mac Preferred) ---
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

        # --- 2. Fallback to Safari (macOS Only) ---
        if sys.platform == "darwin":
            self.log("Attempting to launch Safari...")
            try:
                self.driver = webdriver.Safari()
                self.driver.maximize_window()
                self.wait = WebDriverWait(self.driver, 15)
                self.log("Safari started successfully.")
                return
            except SessionNotCreatedException:
                # Common error: User hasn't enabled automation in Safari
                error_msg = (
                    "Safari Automation is not enabled.\n\n"
                    "Please enable it:\n"
                    "1. Open Safari > Settings > Advanced\n"
                    "2. Check 'Show Develop menu in menu bar'\n"
                    "3. Click 'Develop' in the top menu bar\n"
                    "4. Select 'Allow Remote Automation'"
                )
                logging.error(error_msg)
                raise RuntimeError(error_msg)
            except Exception as e:
                logging.error(f"Safari failed: {e}")
                raise RuntimeError(f"Safari failed to start. Error: {e}")

        # --- 3. No browser found ---
        raise RuntimeError("Could not find Google Chrome. Please install Chrome (or enable Safari automation if on Mac).")

    def login_and_navigate(self) -> str:
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

            list_view_xpath = "//input[@type='radio' and @value='L' and starts-with(@id, 'DERIVED_REGFRM1_SSR_SCHED_FORMAT')]"
            self.wait.until(EC.element_to_be_clickable((By.XPATH, list_view_xpath))).click()
            self.log("Switched to List View...")

            time.sleep(2) 

            body_element = self.driver.find_element(By.TAG_NAME, "body")
            body_text = body_element.text
            
            if not body_text:
                raise ValueError("Extracted body text is empty.")
                
            self.log("Success: Schedule extracted.")
            return body_text

        except TimeoutException:
            raise TimeoutException("Login timed out. Please try again and ensure you complete 2FA.")
        except WebDriverException as e:
            if "no such window" in str(e).lower():
                raise RuntimeError("Browser window was closed unexpectedly.")
            raise e
        except Exception as e:
            logging.error(f"Navigation Error: {e}", exc_info=True)
            self.log(f"Error: {e}")
            raise

    def parse_raw_data(self, raw_text: str) -> List[Dict]:
        self.log("Parsing schedule data...")
        flags = re.DOTALL + re.MULTILINE
        
        time_re = r'\d\d?:\d\d(?:[AP]M)?'
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
            raise ValueError("No courses found.")
        
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
        
        term_start = min(all_dates) if all_dates else date.today()
        self.log(f"Term assumed to start on: {term_start}")

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
                            self.log(f"SKIPPING Holiday: {current_date}")
                            current_date += timedelta(weeks=1)
                            continue

                        weeks_since_start = ((current_date - term_start).days // 7) + 1
                        if weeks_since_start == 7:
                            if current_date != c['start_date']: 
                                current_date += timedelta(weeks=1)
                                continue

                        raw_loc = c['loc']
                        final_loc = raw_loc
                        desc_extras = ""
                        
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
                            
                            description = ', '.join(c['lecturers']) + desc_extras

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
                            self.log(f"Skipped event due to error: {e}")
                        
                        current_date += timedelta(weeks=1)
        
        return final_events

    def generate_outputs(self, events: List[Dict]):
        if not events:
            self.log("No events to write.")
            return

        self.log("Writing files...")
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

        # --- ROBUSTNESS: File Permission Check ---
        try:
            with open(OUTPUT_ICS, 'w', encoding='utf-8') as f:
                f.write(cal.serialize())
            self.log(f"Saved: {OUTPUT_ICS}")
        except PermissionError:
            raise PermissionError(f"Cannot write to {OUTPUT_ICS}. The file is open in another program.\nPlease close it and try again.")

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    @staticmethod
    def _parse_date_str(date_str) -> date:
        return date(*map(int, date_str.split('/')[::-1]))

    @staticmethod
    def _parse_time_str(time_str) -> dt_time:
        fmt = "%I:%M%p" if "M" in time_str.upper() else "%H:%M"
        t = time.strptime(time_str, fmt)
        return dt_time(t.tm_hour, t.tm_min)

# --- 4. MODERN UI (CustomTkinter) ---

class CalendarApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SUTD Schedule Export")
        self.geometry("750x850") 
        
        self.bot = SUTDCalendarBot(log_callback=self.update_log)
        self.courses_data = []
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
        
        self.subtitle_lbl = ctk.CTkLabel(self.header_frame, text="Smart .ics Generator", font=("Roboto", 12), text_color="gray")
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
        
        # Load default reminder from config or default to 15
        saved_reminder = self.config_data.get("settings", {}).get("default_reminder", 15)
        self.reminder_var = ctk.StringVar(value=str(saved_reminder))
        self.rem_entry = ctk.CTkEntry(self.bottom_frame, textvariable=self.reminder_var, width=50)
        self.rem_entry.pack(side="left")

        self.gen_btn = ctk.CTkButton(self.bottom_frame, text="GENERATE CALENDAR FILES", 
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
        config = self.config_data # Load existing to preserve other keys if any
        
        # Save Global Settings
        if "settings" not in config: config["settings"] = {}
        config["settings"]["default_reminder"] = reminder_val

        # Save Course Preferences
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
            raw_text = self.bot.login_and_navigate()
            courses = self.bot.parse_raw_data(raw_text)
            self.bot.close()
            
            try:
                self.after(0, lambda: self.state('zoomed'))
            except: pass

            self.after(0, self.show_selection_ui, courses)
        except Exception as e:
            logging.error(f"Selenium Task Error: {e}", exc_info=True)
            self.after(0, messagebox.showerror, "Error", str(e))
            self.after(0, self.reset_ui)
            if self.bot.driver: self.bot.close()

    def show_selection_ui(self, courses):
        self.courses_data = courses
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

        # --- ROBUSTNESS: Handle Empty Course List ---
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
            
            # Load saved name from new config structure
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
                friendly_name = TYPE_MAPPING.get(type_code, type_code)
                var = ctk.BooleanVar(value=True)
                chk = ctk.CTkCheckBox(chk_frame, text=friendly_name, variable=var)
                chk.pack(side="left", padx=10)
                self.selection_vars[(i, type_code)] = var

    def toggle_all(self, state):
        for var in self.selection_vars.values():
            var.set(state)

    def generate_files(self):
        filtered_courses = []
        for i, course in enumerate(self.courses_data):
            new_course = course.copy()
            
            custom_name = self.name_vars[i].get()
            if custom_name:
                new_course['name'] = custom_name

            new_course['type'] = {}
            has_selected_type = False
            
            for type_name, type_data in course['type'].items():
                if self.selection_vars.get((i, type_name)).get():
                    new_course['type'][type_name] = type_data
                    has_selected_type = True
            
            if has_selected_type:
                filtered_courses.append(new_course)

        self.update_log(f"Processing {len(filtered_courses)} courses...")
        
        try:
            try:
                rem_mins = int(self.reminder_var.get())
            except ValueError:
                rem_mins = 15
            
            # Save Config before work (Robustness)
            self.save_config(filtered_courses, rem_mins)

            events = self.bot.expand_events(filtered_courses, reminder_minutes=rem_mins)
            self.bot.generate_outputs(events)
            
            self.withdraw()
            
            # --- USER FRIENDLY: Auto-Open Folder ---
            output_dir = os.path.abspath(".")
            if os.name == 'nt': # Windows
                os.startfile(output_dir)
            elif os.name == 'posix': # MacOS/Linux
                try:
                    subprocess.call(['open', output_dir])
                except:
                    pass

            messagebox.showinfo("Success", f"Calendar generated!\n\nFile saved to:\n{os.path.join(output_dir, OUTPUT_ICS)}")
            self.destroy()

        except Exception as e:
            logging.error(f"Generation Failed: {e}", exc_info=True)
            messagebox.showerror("Generation Error", str(e))

    def reset_ui(self):
        self.start_btn.configure(state="normal")

if __name__ == "__main__":
    app = CalendarApp()
    app.mainloop()