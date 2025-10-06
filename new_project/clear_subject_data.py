"""
Clear all Module02 subject data
"""
import shutil
from pathlib import Path
import json

# Project root
project_root = Path(__file__).parent

# subject_info directory
subject_info_dir = project_root / 'data' / 'subject_info'

print(f"Clearing subject_info directory: {subject_info_dir}")

if subject_info_dir.exists():
    # Delete entire directory
    shutil.rmtree(subject_info_dir)
    print("DONE: Deleted subject_info directory")

    # Recreate directory structure
    subject_info_dir.mkdir(parents=True, exist_ok=True)
    (subject_info_dir / 'control').mkdir(exist_ok=True)
    (subject_info_dir / 'mci').mkdir(exist_ok=True)
    (subject_info_dir / 'ad').mkdir(exist_ok=True)

    # Create empty index.json files
    for group in ['control', 'mci', 'ad']:
        index_file = subject_info_dir / group / 'index.json'
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump({'subjects': []}, f, ensure_ascii=False, indent=2)

    print("DONE: Recreated subject_info directory structure")
    print("  - control/")
    print("  - mci/")
    print("  - ad/")
    print("\nAll subject data cleared. You can now re-import V1 and V2 data.")
else:
    print("subject_info directory does not exist, nothing to clear")
