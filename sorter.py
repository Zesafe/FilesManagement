import os
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pypdf import PdfReader
from config import SORTING_FOLDER, TARGET_BASE


# Map course/category subfolders to relevant keywords.
# Order matters: top categories take precedence.
COURSE_RULES = {
    "Module1": ["SubModule1_1", "SubModule1_2", "SubModule1_3", "SubModule1_4", "SubModule1_5"],
    "Module2": ["SubModule2_1", "SubModule2_2", "SubModule2_3", "SubModule2_4", "SubModule2_5"],
    "Module3": ["SubModule3_1", "SubModule3_2", "SubModule3_3", "SubModule3_4", "SubModule3_5", "SubModule3_6"],
    "Module4": ["SubModule4_1", "SubModule4_2", "SubModule4_3", "SubModule4_4"]
}

# -------------------------------------------------------------------
# CLASSIFICATION LOGIC
# -------------------------------------------------------------------
def extract_pdf_text(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages[:2]:
            extracted = page.extract_text()
            if extracted:
                text += extracted.lower()
        return text
    except Exception:
        return ""

def determine_category(file_path):
    filename_lower = os.path.basename(file_path).lower()
    
    # Check 1: Filename Keyword Match
    for category, keywords in COURSE_RULES.items():
        if any(kw in filename_lower for kw in keywords):
            return category

    # Check 2: Deep PDF Content Scan
    if filename_lower.endswith(".pdf"):
        pdf_text = extract_pdf_text(file_path)
        for category, keywords in COURSE_RULES.items():
            if any(kw in pdf_text for kw in keywords):
                return category

    # FALLBACK: Return "Random" instead of None
    return "Random"

def process_file(file_path):
    filename = os.path.basename(file_path)

    # Ignore hidden/temporary browser files
    if filename.startswith(".") or filename.endswith((".tmp", ".crdownload", ".part")):
        return

    time.sleep(1)

    # Get the target category (will be "Random" if no keyword matches)
    target_category = determine_category(file_path)

    # Build target directory path (e.g., StudySpace/Random/)
    destination_dir = os.path.join(TARGET_BASE, target_category)
    os.makedirs(destination_dir, exist_ok=True)

    target_path = os.path.join(destination_dir, filename)
    if os.path.exists(target_path):
        base, ext = os.path.splitext(filename)
        target_path = os.path.join(destination_dir, f"{base}_{int(time.time())}{ext}")

    try:
        shutil.move(file_path, target_path)
        print(f"Successfully Moved: {filename} -> StudySpace/{target_category}/")
    except Exception as e:
        print(f"Error moving {filename}: {e}")

class StudyFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            process_file(event.src_path)

if __name__ == "__main__":
    # Convert Path objects to strings if needed by watchdog/os
    os.makedirs(SORTING_FOLDER, exist_ok=True)
    os.makedirs(TARGET_BASE, exist_ok=True)

    event_handler = StudyFolderHandler()
    observer = Observer()
    observer.schedule(event_handler, str(SORTING_FOLDER), recursive=False)

    print(f"Watching '{SORTING_FOLDER}'...")
    print(f"Sorted files will move to '{TARGET_BASE}'")
    print("Press Ctrl+C to stop.")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()