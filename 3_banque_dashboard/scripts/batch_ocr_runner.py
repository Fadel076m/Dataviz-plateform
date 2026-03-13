import subprocess
import json
from pathlib import Path
import sys

# Config
BATCH_SIZE = 5
PDF_2021_2023 = r"c:\Users\admin\OneDrive - ASHOKA\Pictures\12-Master 2\Data Viz\3_banque_dashboard\data\pdf\2021-2023\bilans_2021_2023.pdf"
PDF_2019_2021 = r"c:\Users\admin\OneDrive - ASHOKA\Pictures\12-Master 2\Data Viz\3_banque_dashboard\data\pdf\2019-2021\bilans_2019_2021.pdf"
ROBUST_OCR_SCRIPT = r"c:\Users\admin\OneDrive - ASHOKA\Pictures\12-Master 2\Data Viz\3_banque_dashboard\scripts\robust_ocr.py"
REPORT_FILE = "batch_ocr_report.json"

sys.path.append(r"c:\Users\admin\OneDrive - ASHOKA\Pictures\12-Master 2\Data Viz\3_banque_dashboard")
from config.database import MongoDBConnection

def clear_db():
    print("Clearing all data in dev collection 'performances_bancaires'...")
    mongo = MongoDBConnection(environment='dev')
    if mongo.connect():
        coll = mongo.get_collection()
        res = coll.delete_many({})
        print(f"Deleted {res.deleted_count} documents.")
        mongo.close()

def run_batch(start, end, pdf_file):
    print(f"\n>>> Processing {Path(pdf_file).name}: Pages {start+1} to {end}")
    cmd = [
        "python", 
        ROBUST_OCR_SCRIPT, 
        "--start", str(start), 
        "--end", str(end),
        "--file", pdf_file,
        "--force-senegal"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error in batch {start}-{end}: {e.stderr}")
        return e.stderr

def main():
    clear_db()
    all_reports = []
    
    tasks = [
        (PDF_2019_2021, 246, 314), # Senegal: 247 to 314
        (PDF_2021_2023, 256, 324)  # Senegal: 257 to 324
    ]
    
    for pdf_path, start, end in tasks:
        print(f"\n=== Starting OCR for {Path(pdf_path).name} ===")
        for i in range(start, end, BATCH_SIZE):
            out = run_batch(i, min(i + BATCH_SIZE, end), pdf_path)
            all_reports.append({
                "file": Path(pdf_path).name,
                "batch": f"{i}-{i+BATCH_SIZE}", 
                "output": out
            })
        
    with open(REPORT_FILE, "w", encoding='utf-8') as f:
        json.dump(all_reports, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Full Batch OCR completed. Report saved in {REPORT_FILE}")

if __name__ == "__main__":
    main()
