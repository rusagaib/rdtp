import os
import time
import shutil
import threading
import queue
import requests
from flask import Flask, jsonify
from elutil import Elutil as El
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

load_dotenv()

# ================= CONFIG =================
WATCH_DIR_CONFIG=os.getenv("WATCH_DIR")
# WATCH_DIR = fr'\\{WATCH_DIR_CONFIG}'
WATCH_DIR = fr'{WATCH_DIR_CONFIG}'
BACKUP_DIR_CONFIG = os.getenv("BACKUP_DIR")
BACKUP_DIR = fr'{BACKUP_DIR_CONFIG}'
FAILED_DIR_CONFIG = os.getenv("FAILED_DIR")
FAILED_DIR = fr'{FAILED_DIR_CONFIG}'
ORTHANC_URL = os.getenv("ORTHANC_URL", "")
USER_PACS = os.getenv("PACSLITE_USER", "") 
PASS_PACS = os.getenv("PACSLITE_PASS", "")
# ================= QUEUE =================
# file_queue = queue.Queue(maxsize=1000)
# file_queue = queue.Queue(maxsize=10)
file_queue = queue.Queue(maxsize=100)


# ================= FLASK APP =================
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "service": "RDTP DICOM Sync",
        "queue_size": file_queue.qsize(),
        "timestamp": time.time()
    }), 200

def run_flask():
    # Run Flask di port 5000 (atau sesuaikan)
    # host='0.0.0.0' supaya bisa diakses dari host network (Monitoring: Grafana, Uptime Kuma etc..)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# ================= UTIL =================
def wait_until_file_ready(path, timeout=180):
    last_size = -1
    start = time.time()

    while True:
        if not os.path.exists(path):
            return False

        size = os.path.getsize(path)

        if size == last_size:
            return True

        last_size = size

        if time.time() - start > timeout:
            return False

        time.sleep(1)


def upload_with_retry(file_path, retries=3):
    for attempt in range(1, retries + 1):
        try:
            with open(file_path, 'rb') as f:
                r = requests.post(
                    ORTHANC_URL,
                    data=f.read(),
                    auth=(USER_PACS, PASS_PACS),
                    timeout=(5, 30)
                )

            if r.status_code == 200:
                print(f"[OK] {os.path.basename(file_path)} uploaded (attempt {attempt})", flush=True)
                move_to_backup(file_path)
                return
            else:
                print(f"[ERROR] {r.status_code} (attempt {attempt})", flush=True)

        except Exception as e:
            print(f"[RETRY {attempt}] {str(e)}", flush=True)

        time.sleep(3)

    print(f"[FAILED] {os.path.basename(file_path)}", flush=True)
    move_to_failed(file_path)


def move_to_backup(file_path):
    safe_move(file_path, BACKUP_DIR, "[MOVE] -> Backup")


def move_to_failed(file_path):
    safe_move(file_path, FAILED_DIR, "[MOVE] -> FAILED")


def safe_move(src, dst_dir, message):
    try:
        os.makedirs(dst_dir, exist_ok=True)

        dest_path = os.path.join(dst_dir, os.path.basename(src))

        if os.path.exists(dest_path):
            os.remove(dest_path)

        shutil.move(src, dest_path)
        print(message, flush=True)

    except Exception as e:
        print(f"[MOVE ERROR] {str(e)}", flush=True)

def load_existing_files(event_handler):
    print("[INIT] Scanning existing DICOM...", flush=True)

    for file in os.listdir(WATCH_DIR):

        if not file.lower().endswith(".dcm"):
            continue

        path = os.path.join(WATCH_DIR, file)

        if not os.path.isfile(path):
            continue

        with event_handler.lock:
            if path in event_handler.processed_files:
                continue
            event_handler.processed_files.add(path)

        print(f"[INIT QUEUE] {file}", flush=True)
        file_queue.put(path)

# ================= WORKER =================
def process_file(file_path):
    print(f"[PROCESS] {os.path.basename(file_path)}", flush=True)

    if wait_until_file_ready(file_path):
        upload_with_retry(file_path)
    else:
        print("[SKIP] Anomali File tidak stabil / timeout.", flush=True)


def worker():
    while True:
        file_path = file_queue.get()

        try:
            process_file(file_path)
        except Exception as e:
            print(f"[WORKER ERROR] {str(e)}", flush=True)

        file_queue.task_done()


# ================= HANDLER =================
class DICOMImporterSync(FileSystemEventHandler):
    def __init__(self):
        self.processed_files = set()
        self.lock = threading.Lock()

    def on_created(self, event):
        if event.is_directory:
            return

        if not event.src_path.lower().endswith('.dcm'):
            return

        file_path = event.src_path

        with self.lock:
            if file_path in self.processed_files:
                return
            self.processed_files.add(file_path)

        print(f"\n[QUEUE] {os.path.basename(file_path)}", flush=True)
        file_queue.put(file_path)


# ================= MAIN =================
if __name__ == "__main__":
    if not os.path.exists(WATCH_DIR):
        print("Directory tidak ditemukan!", flush=True)
        exit()

    print("===========================================")
    print(" RDTP - DICOM to PACS Sync + (Status Page)")
    print(" RDTP (Radiology DICOM To Pacs)") 
    print("===========================================")
    El.launch_anime()

    # START FLASK
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # START WORKERS
    NUM_WORKERS = 3
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    # START WATCHDOG (observer)
    event_handler = DICOMImporterSync()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    load_existing_files(event_handler)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[SHUTDOWN] Stopping service...", flush=True)

    observer.join()
