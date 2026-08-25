import sys
import os
import shutil
import time
import json
from pathlib import Path
from pypdf import PdfReader
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QInputDialog, QMessageBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QColor, QDesktopServices
import qtawesome as qta

from config import TARGET_BASE

RULES_FILE = Path(__file__).parent / "rules.json"

# --- JSON RULES MANAGER ---
def load_rules():
    if not RULES_FILE.exists():
        default_rules = {
            "Softwaretechnik": ["softwaretechnik", "dudenhefner"],
            "CS101_Algorithms": ["algorithm", "cs101"]
        }
        save_rules(default_rules)
        return default_rules
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_rules(rules):
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=4)

# --- BACKEND LOGIC ---
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

def determine_category(file_path, course_rules):
    filename_lower = os.path.basename(file_path).lower()
    
    for category, keywords in course_rules.items():
        if any(kw.lower() in filename_lower for kw in keywords):
            return category

    if filename_lower.endswith(".pdf"):
        pdf_text = extract_pdf_text(file_path)
        for category, keywords in course_rules.items():
            if any(kw.lower() in pdf_text for kw in keywords):
                return category

    return "Random"

# --- MAIN MODERN GUI ---
class FileDropperApp(QWidget):
    def __init__(self):
        super().__init__()
        self.course_rules = load_rules()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Study File Organizer")
        self.setFixedSize(450, 420)
        self.setAcceptDrops(True)
        
        # Modern Dark Theme Stylesheet (Catppuccin Mocha Palette)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
            }
            QFrame#DropFrame {
                background-color: #181825;
                border: 2px dashed #89b4fa;
                border-radius: 16px;
            }
            QFrame#DropFrame:hover {
                border-color: #a6e3a1;
                background-color: #1e1e2e;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 10px;
                padding: 10px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }
            QPushButton#PrimaryBtn {
                background-color: #89b4fa;
                color: #11111b;
                border: none;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #b4befe;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)

        # Header Title
        self.title_label = QLabel("Study Workspace", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 700; color: #f5e0dc;")
        layout.addWidget(self.title_label)

        # Drop Zone Container
        self.drop_frame = QFrame(self)
        self.drop_frame.setObjectName("DropFrame")
        
        # Shadow effect for Drop Frame
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setYOffset(4)
        self.drop_frame.setGraphicsEffect(shadow)

        drop_layout = QVBoxLayout(self.drop_frame)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Drop Icon
        icon_label = QLabel(self)
        icon_label.setPixmap(qta.icon('fa5s.file-upload', color='#89b4fa').pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(icon_label)

        # Drop Text
        self.drop_label = QLabel("Drag & Drop Files Here", self)
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #a6adc8; margin-top: 8px;")
        drop_layout.addWidget(self.drop_label)

        layout.addWidget(self.drop_frame, stretch=1)

        # Status Bar
        self.status_label = QLabel("Ready to process...", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #a6adc8;")
        layout.addWidget(self.status_label)

        # Action Buttons Layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # Add Module Button
        self.add_btn = QPushButton(" ➕ Add Module", self)
        self.add_btn.setObjectName("PrimaryBtn")
        self.add_btn.clicked.connect(self.add_new_module)
        btn_layout.addWidget(self.add_btn)

        # Open StudySpace Folder Button
        self.open_folder_btn = QPushButton(" 📁 Open Archive", self)
        self.open_folder_btn.clicked.connect(self.open_target_folder)
        btn_layout.addWidget(self.open_folder_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def open_target_folder(self):
        """Opens the desktop StudySpace directory directly in Windows Explorer."""
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(TARGET_BASE)))

    def add_new_module(self):
        module_name, ok1 = QInputDialog.getText(self, "New Module", "Enter Module/Folder Name:")
        if not ok1 or not module_name.strip():
            return
        module_name = module_name.strip()

        keywords_str, ok2 = QInputDialog.getText(
            self, "Module Keywords", 
            f"Enter keywords for '{module_name}'\n(Separated by commas):"
        )
        if not ok2 or not keywords_str.strip():
            return

        new_keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]

        if module_name in self.course_rules:
            existing = set(self.course_rules[module_name])
            existing.update(new_keywords)
            self.course_rules[module_name] = list(existing)
        else:
            self.course_rules[module_name] = new_keywords

        save_rules(self.course_rules)
        QMessageBox.information(
            self, "Updated", 
            f"Saved module '{module_name}' with keywords:\n" + ", ".join(self.course_rules[module_name])
        )

    # Drag & Drop Events
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_frame.setStyleSheet("""
                QFrame#DropFrame {
                    background-color: #313244;
                    border: 2px dashed #a6e3a1;
                    border-radius: 16px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.drop_frame.setStyleSheet("""
            QFrame#DropFrame {
                background-color: #181825;
                border: 2px dashed #89b4fa;
                border-radius: 16px;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.dragLeaveEvent(None)
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if os.path.isfile(file_path):
                self.process_file(file_path)

    def process_file(self, file_path):
        filename = os.path.basename(file_path)

        if filename.startswith(".") or filename.endswith((".tmp", ".crdownload", ".part")):
            self.status_label.setText("Ignored temporary file.")
            self.status_label.setStyleSheet("color: #f9e2af;")
            return

        target_category = determine_category(file_path, self.course_rules)
        destination_dir = os.path.join(TARGET_BASE, target_category)
        os.makedirs(destination_dir, exist_ok=True)

        target_path = os.path.join(destination_dir, filename)
        if os.path.exists(target_path):
            base, ext = os.path.splitext(filename)
            target_path = os.path.join(destination_dir, f"{base}_{int(time.time())}{ext}")

        try:
            shutil.move(file_path, target_path)
            self.status_label.setText(f"Moved to: StudySpace/{target_category}/")
            self.status_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        except Exception as e:
            self.status_label.setText(f"Error moving file: {e}")
            self.status_label.setStyleSheet("color: #f38ba8;")

if __name__ == "__main__":
    os.makedirs(TARGET_BASE, exist_ok=True)
    app = QApplication(sys.argv)
    ex = FileDropperApp()
    ex.show()
    sys.exit(app.exec())