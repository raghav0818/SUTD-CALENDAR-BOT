import subprocess
import sys
import os

def install():
    print("==================================================")
    print("   SUTD Calendar Bot - Dependency Installer")
    print("==================================================")
    print(f"Detected OS: {sys.platform}")
    print(f"Python Executable: {sys.executable}")
    print("")

    # Ensure we are in the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"[ERROR] '{requirements_file}' not found in {script_dir}")
        print("Please unzip the entire folder before running this script.")
        input("\nPress Enter to exit...")
        return

    print("Installing dependencies...")
    
    # Construct the command: [python_executable, "-m", "pip", "install", "-r", "requirements.txt"]
    # Using 'python -m pip' is safer than calling 'pip' directly as it ensures 
    # libraries are installed for the EXACT python version currently running.
    cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]
    
    # Mac/Linux often requires '--user' if not in a venv
    if sys.platform != "win32":
        cmd.append("--user")

    try:
        subprocess.check_call(cmd)
        print("\n[SUCCESS] All dependencies installed successfully!")
        print("You can now run the bot:")
        if sys.platform == "win32":
            print("   Run 'sutd_calendar_bot.py'")
        else:
            print("   Run: python3 sutd_calendar_bot.py")
            
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Installation failed with error code {e.returncode}.")
        print("Please try running this command manually in your terminal:")
        print(f"   {' '.join(cmd)}")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    install()