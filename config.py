import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Read from .env, or fall back to home directory defaults
SORTING_FOLDER = Path(os.getenv("SORTING_FOLDER", Path.home() / "SortingFolder"))
TARGET_BASE = Path(os.getenv("TARGET_BASE", Path.home() / "StudySpace"))