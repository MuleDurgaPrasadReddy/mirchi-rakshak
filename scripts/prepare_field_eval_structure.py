import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELD_EVAL_DIR = ROOT / "src" / "data_field_eval"

CLASSES = [
    "Chilli __Whitefly",
    "Chilli __Yellowish",
    "Chilli__Anthracnos",
    "Chilli__Damping_Off",
    "Chilli__Leaf_Curl_Virus",
    "Chilli__Leaf_Spot",
    "Chilli__Veinal_Mottle_Virus",
    "Chilli___healthy"
]

def main():
    print("==========================================================")
    print("  MIRCHI RAKSHAK — FIELD EVALUATION STRUCTURE PREPARATION ")
    print("==========================================================")
    
    FIELD_EVAL_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Create class subdirectories
    for cname in CLASSES:
        cdir = FIELD_EVAL_DIR / cname
        cdir.mkdir(parents=True, exist_ok=True)
        print(f"[+] Created directory: {cdir.relative_to(ROOT)}")
        
    # 2. Create README.md
    readme_path = FIELD_EVAL_DIR / "README.md"
    readme_content = """# Mirchi Rakshak — Independent Field Evaluation Dataset

## Overview
This repository contains the independent field-evaluation dataset structure for real-world out-of-distribution pathology validation of the **Mirchi Rakshak** classification models.

- **Isolation Rule:** All images in `src/data_field_eval/` are strictly isolated from `src/data_clean` (Train, Validation, and Test splits).
- **Target Coverage:** 50–100 independent images per class (prioritizing `Chilli__Leaf_Curl_Virus` and `Chilli__Damping_Off`).

---

## 8 Official Disease Classes
1. `Chilli __Whitefly`
2. `Chilli __Yellowish`
3. `Chilli__Anthracnos`
4. `Chilli__Damping_Off`
5. `Chilli__Leaf_Curl_Virus`
6. `Chilli__Leaf_Spot`
7. `Chilli__Veinal_Mottle_Virus`
8. `Chilli___healthy`

---

## Manifest Schema (`field_eval_manifest.csv`)
- `image_id`: Unique ID (e.g. `fe_leaf_curl_001`)
- `filename`: Local image file name
- `class_label`: Official disease class name
- `image_source`: Field source / collection origin
- `capture_group`: Camera session / physical group ID (for group-level deduplication)
- `host_verified`: Host plant identity confirmation (`Yes` / `No` / `Pending`)
- `disease_verified`: Pathology symptom confirmation (`Yes` / `No` / `Pending`)
- `verification_status`: Status (`AWAITING_VERIFICATION`, `APPROVED_FIELD_EVAL`, `EXCLUDED`)
- `sha256`: Cryptographic hash
- `dhash`: Perceptual fingerprint
- `review_notes`: Expert pathology notes
"""
    readme_path.write_text(readme_content, encoding="utf-8")
    print(f"[+] Created README: {readme_path.relative_to(ROOT)}")

    # 3. Create field_eval_manifest.csv Template
    csv_path = FIELD_EVAL_DIR / "field_eval_manifest.csv"
    fieldnames = [
        "image_id", "filename", "class_label", "image_source", "capture_group",
        "host_verified", "disease_verified", "verification_status",
        "sha256", "dhash", "review_notes"
    ]
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    print(f"[+] Created CSV Manifest template: {csv_path.relative_to(ROOT)}")

    # 4. Create field_eval_manifest.json Template
    json_path = FIELD_EVAL_DIR / "field_eval_manifest.json"
    manifest_meta = {
        "dataset_name": "Mirchi Rakshak Independent Field Evaluation Set",
        "status": "PREPARATION_PHASE",
        "target_per_class": "50-100 independent images per class",
        "class_labels": CLASSES,
        "total_images": 0,
        "verified_images": 0,
        "per_class_counts": {c: 0 for c in CLASSES},
        "images": []
    }
    json_path.write_text(json.dumps(manifest_meta, indent=2), encoding="utf-8")
    print(f"[+] Created JSON Manifest template: {json_path.relative_to(ROOT)}")

    print("\n[+] Field Evaluation dataset structure successfully prepared!")

if __name__ == "__main__":
    main()
