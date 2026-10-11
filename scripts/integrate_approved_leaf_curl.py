import os
import csv
import json
import shutil
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEAF_CURL_DIR = ROOT / "mirchi_new_data" / "Leaf_Curl_Virus"
TARGET_DIR = ROOT / "src" / "data_clean" / "train" / "Chilli__Leaf_Curl_Virus"
DISTRIBUTION_JSON = ROOT / "src" / "data_clean" / "dataset_distribution.json"

def get_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("==========================================================")
    print("  MIRCHI RAKSHAK — LEAF CURL VIRUS CANDIDATE INTEGRATION ")
    print("==========================================================")
    
    indep_csv = LEAF_CURL_DIR / "independence_audit.csv"
    if not indep_csv.exists():
        raise FileNotFoundError(f"Missing audit CSV: {indep_csv}")

    with open(indep_csv, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Existing clean train hashes
    train_files = list(TARGET_DIR.glob("*"))
    train_hashes = {get_sha256(f): f.name for f in train_files if f.is_file()}

    print(f"Current train count in Chilli__Leaf_Curl_Virus : {len(train_files)}")

    integrated_count = 0
    skipped_existing_count = 0
    skipped_excluded_count = 0
    missing_count = 0

    for r in rows:
        fn = r["new_filename"]
        rec = r["recommended_action"]
        src_path = LEAF_CURL_DIR / fn

        if rec == "ACCEPT_CLEAN_INDEPENDENT":
            if not src_path.exists():
                missing_count += 1
                continue

            sha = get_sha256(src_path)
            if sha in train_hashes:
                skipped_existing_count += 1
                continue

            dest_path = TARGET_DIR / fn
            shutil.copy2(src_path, dest_path)
            integrated_count += 1
            print(f"[+] Integrated ({integrated_count}/79): {fn} -> {dest_path}")
        else:
            skipped_excluded_count += 1

    final_train_files = list(TARGET_DIR.glob("*"))
    final_count = len(final_train_files)

    print("\n----------------------------------------------------------")
    print("INTEGRATION EXECUTION SUMMARY:")
    print(f"  - Newly Integrated Candidates           : {integrated_count}")
    print(f"  - Total Clean Train Leaf Curl Count     : {final_count}")
    print("----------------------------------------------------------")

    # Update dataset_distribution.json
    if DISTRIBUTION_JSON.exists():
        dist_data = json.loads(DISTRIBUTION_JSON.read_text(encoding="utf-8"))
        
        if "per_class_counts" in dist_data and "Chilli__Leaf_Curl_Virus" in dist_data["per_class_counts"]:
            dist_data["per_class_counts"]["Chilli__Leaf_Curl_Virus"]["train"] = final_count
            val_c = dist_data["per_class_counts"]["Chilli__Leaf_Curl_Virus"].get("validation", 8)
            test_c = dist_data["per_class_counts"]["Chilli__Leaf_Curl_Virus"].get("test", 8)
            dist_data["per_class_counts"]["Chilli__Leaf_Curl_Virus"]["total"] = final_count + val_c + test_c
            
        if "class_distribution" in dist_data:
            for item in dist_data["class_distribution"]:
                if item["class_name"] == "Chilli__Leaf_Curl_Virus":
                    item["train_count"] = final_count
                    item["total_group_count"] = final_count + item.get("validation_count", 8) + item.get("test_count", 8)
                    
        total_train = sum(len(list((ROOT / "src" / "data_clean" / "train" / d).glob("*"))) for d in os.listdir(ROOT / "src" / "data_clean" / "train") if (ROOT / "src" / "data_clean" / "train" / d).is_dir())
        dist_data["train_count"] = total_train
        
        DISTRIBUTION_JSON.write_text(json.dumps(dist_data, indent=2), encoding="utf-8")
        print(f"Updated dataset_distribution.json successfully.")

if __name__ == "__main__":
    main()
