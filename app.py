import sys
import os
import shutil
import time
import json
from pathlib import Path
from pypdf import PdfReader
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QInputDialog, QMessageBox, QFrame, 
    QGraphicsDropShadowEffect, QTableWidget, QTableWidgetItem, 
    QHeaderView, QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QColor, QDesktopServices, QIcon
import qtawesome as qta

from config import TARGET_BASE

RULES_FILE = Path(__file__).parent / "rules.json"

# --- JSON RULES MANAGER ---
def load_rules():
    if not RULES_FILE.exists():
        default_rules = {
            "Softwaretechnik": ["softwaretechnik", "dudenhefner", "entwurfsmuster"],
            "CS101_Algorithms": ["algorithm", "cs101", "complexity"],
            "Math201_LinearAlgebra": ["matrix", "vector", "linear algebra"],
            "CS202_WebDev": ["javascript", "css", "html", "react"]
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

# --- MAIN APP UI ---
class StudyOrganizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.course_rules = load_rules()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("StudySpace | Automated File Organizer")
        self.resize(920, 580)
        self.setMinimumSize(850, 500)
        self.setAcceptDrops(True)
        
        # Premium Dark Palette (Catppuccin Mocha Inspired)
        self.setStyleSheet("""
            QWidget {
                background-color: #0f111a;
                color: #cdd6f4;
                font-family: 'Segoe UI', Inter, sans-serif;
            }

            /* Sidebar Panel */
            QFrame#Sidebar {
                background-color: #161824;
                border-right: 1px solid #1e2030;
            }

            /* Header Section */
            QLabel#AppHeader {
                font-size: 22px;
                font-weight: 800;
                color: #cba6f7;
                padding-bottom: 2px;
            }
            QLabel#AppSubheader {
                font-size: 11px;
                color: #6c7086;
                font-weight: 500;
            }

            /* Main Drop Zone */
            QFrame#DropFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #181a26, stop:1 #12141d);
                border: 2px dashed #3b4261;
                border-radius: 20px;
            }

            /* Table Styling */
            QTableWidget {
                background-color: #161824;
                color: #cdd6f4;
                gridline-color: #1e2030;
                border: 1px solid #232538;
                border-radius: 12px;
                font-size: 13px;
                selection-background-color: #313244;
            }
            QHeaderView::section {
                background-color: #1e2030;
                color: #b4befe;
                font-weight: 700;
                font-size: 12px;
                padding: 10px;
                border: none;
                text-transform: uppercase;
            }

            /* History Activity Feed */
            QListWidget#HistoryList {
                background-color: #161824;
                border: 1px solid #232538;
                border-radius: 12px;
                padding: 6px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #1e2030;
                border-radius: 6px;
            }

            /* Buttons */
            QPushButton {
                background-color: #232538;
                color: #cdd6f4;
                border: 1px solid #3b4261;
                border-radius: 10px;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2a2d43;
                border-color: #89b4fa;
            }
            QPushButton#AccentBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #cba6f7, stop:1 #89b4fa);
                color: #11111b;
                border: none;
                font-weight: 700;
            }
            QPushButton#AccentBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ddb6f2, stop:1 #b4befe);
            }
            QPushButton#DeleteBtn {
                background-color: #31232e;
                color: #f38ba8;
                border: 1px solid #452937;
                border-radius: 6px;
                padding: 4px 10px;
            }
            QPushButton#DeleteBtn:hover {
                background-color: #f38ba8;
                color: #11111b;
            }
        """)

        # Main Layout (Split Sidebar & Right Dashboard)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -------------------------------------------------------------------
        # LEFT SIDEBAR: LOGS & QUICK ACTIONS
        # -------------------------------------------------------------------
        sidebar = QFrame(self)
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 25, 20, 25)
        sidebar_layout.setSpacing(15)

        # App Branding Header
        brand_layout = QVBoxLayout()
        header_title = QLabel("StudySpace", self)
        header_title.setObjectName("AppHeader")
        header_sub = QLabel("AUTOMATED SORTING HUB", self)
        header_sub.setObjectName("AppSubheader")
        brand_layout.addWidget(header_title)
        brand_layout.addWidget(header_sub)
        sidebar_layout.addLayout(brand_layout)

        # Action Buttons
        self.open_folder_btn = QPushButton(" Open Archive Folder", self)
        self.open_folder_btn.setIcon(qta.icon('fa5s.folder-open', color='#cdd6f4'))
        self.open_folder_btn.clicked.connect(self.open_target_folder)
        sidebar_layout.addWidget(self.open_folder_btn)

        # Recent Activity Feed Title
        history_title = QLabel("Recent Activity Log", self)
        history_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #a6adc8; margin-top: 10px;")
        sidebar_layout.addWidget(history_title)

        # Recent Activity List Widget
        self.history_list = QListWidget(self)
        self.history_list.setObjectName("HistoryList")
        sidebar_layout.addWidget(self.history_list)

        main_layout.addWidget(sidebar, stretch=3)

        # -------------------------------------------------------------------
        # RIGHT CONTENT AREA: DROP ZONE & MODULE EDITOR TABLE
        # -------------------------------------------------------------------
        content_frame = QFrame(self)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(20)

        # Drop Zone Frame
        self.drop_frame = QFrame(self)
        self.drop_frame.setObjectName("DropFrame")
        self.drop_frame.setMinimumHeight(180)

        drop_layout = QVBoxLayout(self.drop_frame)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.drop_icon = QLabel(self)
        self.drop_icon.setPixmap(qta.icon('fa5s.cloud-upload-alt', color='#89b4fa').pixmap(54, 54))
        self.drop_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(self.drop_icon)

        self.drop_label = QLabel("Drag & Drop Study Files Here", self)
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #cdd6f4; margin-top: 8px;")
        drop_layout.addWidget(self.drop_label)

        self.status_label = QLabel("PDF & Document Auto-Classifier Active", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #6c7086;")
        drop_layout.addWidget(self.status_label)

        content_layout.addWidget(self.drop_frame)

        # Modules Manager Header + Add Button
        table_header_layout = QHBoxLayout()
        table_title = QLabel("Configured Modules", self)
        table_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #f5e0dc;")
        table_header_layout.addWidget(table_title)
        table_header_layout.addStretch()

        self.add_mod_btn = QPushButton(" Add Module", self)
        self.add_mod_btn.setObjectName("AccentBtn")
        self.add_mod_btn.setIcon(qta.icon('fa5s.plus', color='#11111b'))
        self.add_mod_btn.clicked.connect(self.add_module)
        table_header_layout.addWidget(self.add_mod_btn)

        content_layout.addLayout(table_header_layout)

        # Rules Table
        self.rules_table = QTableWidget(self)
        self.rules_table.setColumnCount(3)
        self.rules_table.setHorizontalHeaderLabels(["Module Category", "Assigned Keywords", "Action"])
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.rules_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.rules_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.rules_table.setColumnWidth(0, 190)
        self.rules_table.setColumnWidth(2, 75)
        content_layout.addWidget(self.rules_table)

        main_layout.addWidget(content_frame, stretch=7)

        # Load data into table
        self.load_table_data()

    # --- TABLE MANAGEMENT LOGIC ---
    def load_table_data(self):
        self.course_rules = load_rules()
        self.rules_table.setRowCount(len(self.course_rules))

        for row, (module, keywords) in enumerate(self.course_rules.items()):
            # Module Name
            mod_item = QTableWidgetItem(module)
            mod_item.setFlags(mod_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.rules_table.setItem(row, 0, mod_item)

            # Keywords
            kw_item = QTableWidgetItem(", ".join(keywords))
            kw_item.setFlags(kw_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.rules_table.setItem(row, 1, kw_item)

            # Delete Action
            del_btn = QPushButton("🗑", self)
            del_btn.setObjectName("DeleteBtn")
            del_btn.clicked.connect(lambda _, m=module: self.delete_module(m))
            self.rules_table.setCellWidget(row, 2, del_btn)

    def add_module(self):
        module_name, ok1 = QInputDialog.getText(self, "New Module", "Enter Module/Folder Name:")
        if not ok1 or not module_name.strip():
            return
        module_name = module_name.strip()

        keywords_str, ok2 = QInputDialog.getText(
            self, "Module Keywords", 
            f"Enter keywords for '{module_name}' (separated by commas):"
        )
        if not ok2 or not keywords_str.strip():
            return

        new_keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]

        rules = load_rules()
        if module_name in rules:
            existing = set(rules[module_name])
            existing.update(new_keywords)
            rules[module_name] = list(existing)
        else:
            rules[module_name] = new_keywords

        save_rules(rules)
        self.load_table_data()
        self.add_history_entry(f"Updated module rules for '{module_name}'", success=True)

    def delete_module(self, module_name):
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete module '{module_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            rules = load_rules()
            if module_name in rules:
                del rules[module_name]
                save_rules(rules)
                self.load_table_data()
                self.add_history_entry(f"Deleted module '{module_name}'")

    def open_target_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(TARGET_BASE)))

    def add_history_entry(self, message, success=True):
        timestamp = time.strftime("%H:%M:%S")
        item = QListWidgetItem(f"[{timestamp}] {message}")
        if success:
            item.setForeground(QColor("#a6e3a1"))
        else:
            item.setForeground(QColor("#f38ba8"))
        self.history_list.insertItem(0, item)

    # --- DRAG & DROP EVENT HANDLERS ---
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_frame.setStyleSheet("""
                QFrame#DropFrame {
                    background-color: #1e2030;
                    border: 2px dashed #a6e3a1;
                    border-radius: 20px;
                }
            """)
            self.drop_icon.setPixmap(qta.icon('fa5s.cloud-download-alt', color='#a6e3a1').pixmap(54, 54))
            self.drop_label.setText("Release File to Sort")
            self.drop_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #a6e3a1; margin-top: 8px;")

    def dragLeaveEvent(self, event):
        self.drop_frame.setStyleSheet("""
            QFrame#DropFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #181a26, stop:1 #12141d);
                border: 2px dashed #3b4261;
                border-radius: 20px;
            }
        """)
        self.drop_icon.setPixmap(qta.icon('fa5s.cloud-upload-alt', color='#89b4fa').pixmap(54, 54))
        self.drop_label.setText("Drag & Drop Study Files Here")
        self.drop_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #cdd6f4; margin-top: 8px;")

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
            self.add_history_entry(f"Ignored temporary file '{filename}'", success=False)
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
            self.status_label.setText(f"Last sorted: {filename} ➔ {target_category}")
            self.status_label.setStyleSheet("font-size: 12px; color: #a6e3a1; font-weight: 600;")
            self.add_history_entry(f"Sorted '{filename}' to /{target_category}", success=True)
        except Exception as e:
            self.status_label.setText(f"Error moving file: {e}")
            self.status_label.setStyleSheet("font-size: 12px; color: #f38ba8;")
            self.add_history_entry(f"Error moving '{filename}'", success=False)

if __name__ == "__main__":
    os.makedirs(TARGET_BASE, exist_ok=True)
    app = QApplication(sys.argv)
    ex = StudyOrganizerApp()
    ex.show()
    sys.exit(app.exec())