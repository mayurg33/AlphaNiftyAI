import os
from pathlib import Path
from datetime import datetime, timedelta

# Start and end months
start_month = datetime.strptime("2024-03", "%Y-%m")
end_month = datetime.strptime("2025-05", "%Y-%m")

# Base directory to store all the folders
base_dir = Path("data/macro")
base_dir.mkdir(parents=True, exist_ok=True)

current = start_month
while current <= end_month:
    folder_name = current.strftime("%Y-%m")
    folder_path = base_dir / folder_name
    folder_path.mkdir(exist_ok=True)

    # Create an empty text file inside the folder
    summary_file = folder_path / "summary.txt"
    summary_file.touch()  # Creates an empty file

    print(f"[ok] Created folder and file for {folder_name}")
    # Move to next month
    if current.month == 12:
        current = current.replace(year=current.year + 1, month=1)
    else:
        current = current.replace(month=current.month + 1)
