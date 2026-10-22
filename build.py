"""
Script di build per Render: estrae json_output.zip e costruisce dnd.db.
"""
import zipfile
from pathlib import Path

zip_path = Path("json_output.zip")
if zip_path.exists():
    print(f"Extracting {zip_path}...")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(".")
    print("Extraction complete.")
else:
    print(f"WARNING: {zip_path} not found, assuming json_output/ already exists.")

import build_db
build_db.build(Path("json_output"), Path("dnd.db"))
