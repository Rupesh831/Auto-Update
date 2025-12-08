import os
import time
import requests
import subprocess
import psutil
import sys
from threading import Thread, Event

# Fix for PyInstaller EXE - get correct executable directory
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVER_VERSION_URL = "http://127.0.0.1:5000/version"
SERVER_DOWNLOAD_URL = "http://127.0.0.1:5000/download"

stop_event = Event()

def is_tracker_running():
    """Check if tracker is running."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and 'tracker' in proc.info['name'].lower():
                return True
        except:
            pass
    return False

def get_current_tracker_file():
    """Get tracker exe file - exclude client_agent variants."""
    exclude = {'client_agent.exe', 'client_agent_service.exe'}
    try:
        for f in os.listdir(BASE_DIR):
            if f.endswith(".exe") and f.lower() not in exclude:
                return f
    except:
        pass
    return None

def get_local_version():
    """Extract version from filename."""
    tracker_file = get_current_tracker_file()
    if not tracker_file:
        return 0.0
    try:
        v = tracker_file.lower().replace("tracker_v", "").replace(".exe", "")
        return float(v)
    except:
        return 0.0

def kill_tracker():
    """Kill tracker processes."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and 'tracker' in proc.info['name'].lower():
                proc.kill()
        except:
            pass

def download_update(server_filename):
    """Download new tracker - FIXED for your server."""
    target_path = os.path.join(BASE_DIR, server_filename)
    
    # Your server expects: GET /download (no filename param)
    url = SERVER_DOWNLOAD_URL  # http://127.0.0.1:5000/download
    
    try:
        resp = requests.get(url, stream=True, timeout=30)
        if resp.status_code == 200:
            with open(target_path, "wb") as f:
                for chunk in resp.iter_content(1024*1024):
                    if chunk:
                        f.write(chunk)
            return True
    except:
        pass
    return False

def delete_old_tracker(old_file):
    """Delete ONLY old tracker exe file."""
    if old_file:
        path = os.path.join(BASE_DIR, old_file)
        try:
            if os.path.exists(path):
                os.remove(path)
        except:
            pass

def run_tracker(filename):
    """Start tracker silently."""
    filepath = os.path.join(BASE_DIR, filename)
    if os.path.exists(filepath):
        try:
            subprocess.Popen([filepath], cwd=BASE_DIR,
                           creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
            return True
        except:
            pass
    return False

def monitor_tracker():
    """Keep tracker always running - check every 10s."""
    while not stop_event.is_set():
        try:
            if not is_tracker_running():
                tracker_file = get_current_tracker_file()
                if tracker_file and os.path.exists(os.path.join(BASE_DIR, tracker_file)):
                    run_tracker(tracker_file)
                else:
                    update_tracker()
            time.sleep(10)
        except:
            time.sleep(10)

def update_tracker():
    """Check for updates."""
    try:
        local_version = get_local_version()
        resp = requests.get(SERVER_VERSION_URL, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            
            # Handle both response formats from your server
            if "version" in data and data.get("update", True):
                server_version = float(data["version"])
                server_filename = data["filename"]
            else:
                return  # No update available
            
            if server_version > local_version:
                kill_tracker()
                time.sleep(3)  # Wait for clean shutdown
                old_file = get_current_tracker_file()
                delete_old_tracker(old_file)  # ONLY deletes old tracker.exe
                if download_update(server_filename):
                    time.sleep(2)
                    run_tracker(server_filename)
    except:
        pass

def main_loop():
    """Main silent loop - STARTS TRACKER IMMEDIATELY."""
    
    # IMMEDIATE TRACKER START
    if not is_tracker_running():
        tracker_file = get_current_tracker_file()
        if tracker_file:
            run_tracker(tracker_file)
        else:
            update_tracker()
    
    # Start monitor thread
    monitor_thread = Thread(target=monitor_tracker, daemon=True)
    monitor_thread.start()
    
    # Update checks
    while not stop_event.is_set():
        update_tracker()
        time.sleep(30)

if __name__ == '__main__':
    # Works perfectly in Windows Startup folder!
    if len(sys.argv) == 1:
        main_loop()
    else:
        # Service mode (optional)
        try:
            import win32serviceutil
            import win32service
            import win32event
            import servicemanager
            
            class ClientAgentService(win32serviceutil.ServiceFramework):
                _svc_name_ = "ClientAgent"
                _svc_display_name_ = "Client Agent"
                _svc_description_ = "Tracker Monitor"

                def __init__(self, args):
                    win32serviceutil.ServiceFramework.__init__(self, args)
                    self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

                def SvcStop(self):
                    self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                    win32event.SetEvent(self.hWaitStop)
                    stop_event.set()

                def SvcDoRun(self):
                    main_loop()

            win32serviceutil.HandleCommandLine(ClientAgentService)
        except ImportError:
            main_loop()
