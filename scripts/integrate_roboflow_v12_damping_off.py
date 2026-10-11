import csv
import shutil
from pathlib import Path

STAGING_DIR = Path("mirchi_new_data/Damping_Off/field_collection/approved_candidates/roboflow_v12")
FORM_CSV = STAGING_DIR / "expert_review_form.csv"
TARGET_CLEAN_DIR = Path("src/data_clean/Chilli__Damping_Off")

def main():
    print("==================================================================")
    print(" Mirchi Rakshak — Damping Off Roboflow v12 Integration Pipeline ")
    print("==================================================================")
    
    if not FORM_CSV.exists():
        print(f"ERROR: Review form not found at {FORM_CSV}")
        return

    approved_count = 0
    pending_count = 0
    rejected_count = 0

    with open(FORM_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} entries from expert review form.\n")

    for row in rows:
        img_id = row["image_id"]
        filename = row["filename"]
        decision = row.get("decision", "").strip()
        src_img_path = STAGING_DIR / filename

        if decision == "APPROVED_FOR_CLEAN_DATASET":
            approved_count += 1
            if not src_img_path.exists():
                print(f"[!] Warning: Image file {filename} missing in staging directory.")
                continue
            
            # Destination path in clean dataset
            dest_img_path = TARGET_CLEAN_DIR / filename
            if dest_img_path.exists():
                print(f"[=] Skipped (already in clean dataset): {filename}")
            else:
                # Target dir check
                TARGET_CLEAN_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_img_path, dest_img_path)
                print(f"[+] Successfully integrated: {filename} -> {dest_img_path}")
        elif decision == "AWAITING_EXPERT_VERIFICATION" or decision == "":
            pending_count += 1
            print(f"[?] Pending expert verification: {filename}")
        else:
            rejected_count += 1
            print(f"[-] Rejected by expert ({decision}): {filename}")

    print("\n------------------------------------------------------------------")
    print(f"Integration Summary:")
    print(f"  - Total candidates evaluated : {len(rows)}")
    print(f"  - Approved & Integrated      : {approved_count}")
    print(f"  - Pending verification       : {pending_count}")
    print(f"  - Rejected                   : {rejected_count}")
    print("------------------------------------------------------------------")
    if pending_count > 0:
        print("\nNote: Candidates with decision 'AWAITING_EXPERT_VERIFICATION' remain safely isolated in the staging folder.")

if __name__ == "__main__":
    main()
