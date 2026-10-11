import os
import json
import hashlib
from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "src" / "data_stratified"

splits = ["train", "valid", "test"]
SUPPORTED = {".jpg", ".jpeg", ".png"}

# 1. Collect all files with metadata
all_files = []
split_counts = {"train": 0, "valid": 0, "test": 0}

for split in splits:
    split_dir = DATASET / split
    for class_dir in split_dir.iterdir():
        if class_dir.is_dir():
            for fpath in class_dir.iterdir():
                if fpath.suffix.lower() in SUPPORTED:
                    split_counts[split] += 1
                    all_files.append({
                        "path": fpath,
                        "rel_path": str(fpath.relative_to(DATASET)),
                        "name": fpath.name,
                        "split": split,
                        "class": class_dir.name
                    })

print(f"Total images collected for audit: {len(all_files)}")
print(f"Split counts: Train={split_counts['train']}, Validation={split_counts['valid']}, Test={split_counts['test']}")

# 2. Exact hash check (SHA-256)
hash_map = {}
exact_duplicates = []
cross_split_exact = []

for item in all_files:
    data = item["path"].read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    item["sha256"] = sha
    
    if sha in hash_map:
        prev = hash_map[sha]
        dup_info = {
            "file1": prev["rel_path"],
            "file2": item["rel_path"],
            "split1": prev["split"],
            "split2": item["split"],
            "class1": prev["class"],
            "class2": item["class"]
        }
        exact_duplicates.append(dup_info)
        if prev["split"] != item["split"]:
            cross_split_exact.append(dup_info)
    else:
        hash_map[sha] = item

print(f"Exact duplicates found total: {len(exact_duplicates)}")
print(f"Cross-split exact duplicates found: {len(cross_split_exact)}")

# 3. Perceptual hash (dHash - difference hash) for near duplicates
def dhash(image, hash_size=8):
    img = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(img, dtype=np.int32)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return diff.flatten()

phash_map = []
for item in all_files:
    try:
        with Image.open(item["path"]) as img:
            ph = dhash(img)
            item["dhash"] = ph
            phash_map.append(item)
    except Exception as e:
        print(f"Error reading image {item['rel_path']}: {e}")

near_duplicates = []
cross_split_near = []

# Compare perceptual hashes (Hamming distance <= 2 out of 64 bits = ~97%+ perceptual identity)
n = len(phash_map)
print("Computing perceptual hash similarities across dataset...")

for i in range(n):
    for j in range(i + 1, n):
        item1 = phash_map[i]
        item2 = phash_map[j]
        if item1["sha256"] != item2["sha256"]:
            dist = int(np.count_nonzero(item1["dhash"] != item2["dhash"]))
            if dist <= 2:
                near_info = {
                    "file1": item1["rel_path"],
                    "file2": item2["rel_path"],
                    "split1": item1["split"],
                    "split2": item2["split"],
                    "class1": item1["class"],
                    "class2": item2["class"],
                    "hamming_distance": dist
                }
                near_duplicates.append(near_info)
                if item1["split"] != item2["split"]:
                    cross_split_near.append(near_info)

print(f"Near duplicates found total: {len(near_duplicates)}")
print(f"Cross-split near duplicates found: {len(cross_split_near)}")

# 4. Filename prefix / pattern grouping audit for capture sessions
filename_groups = {}
for item in all_files:
    stem = item["path"].stem
    prefix = stem.rsplit("_", 1)[0] if "_" in stem else stem
    if prefix not in filename_groups:
        filename_groups[prefix] = []
    filename_groups[prefix].append(item)

suspicious_filename_groups = []
for prefix, items in filename_groups.items():
    splits_present = set(it["split"] for it in items)
    if len(splits_present) > 1 and len(items) > 1:
        suspicious_filename_groups.append({
            "prefix": prefix,
            "total_files": len(items),
            "splits": list(splits_present),
            "files": [it["rel_path"] for it in items[:10]]
        })

print(f"Suspicious filename groups found across splits: {len(suspicious_filename_groups)}")

# 5. Combine cross-split duplicates
all_cross_split_duplicates = cross_split_exact + cross_split_near

# 6. Formulate conclusion
if len(cross_split_exact) == 0 and len(cross_split_near) == 0:
    conclusion = "NO MEANINGFUL DATA LEAKAGE DETECTED. Train, validation, and test splits are completely disjoint with zero exact or near-duplicate cross-split image pairs."
else:
    conclusion = f"DETECTED {len(cross_split_exact)} exact cross-split duplicates and {len(cross_split_near)} near-duplicate cross-split pairs across the dataset splits."

report = {
    "total_images": len(all_files),
    "split_counts": {
        "train_images": split_counts["train"],
        "validation_images": split_counts["valid"],
        "test_images": split_counts["test"]
    },
    "exact_duplicates_count": len(exact_duplicates),
    "near_duplicates_count": len(near_duplicates),
    "cross_split_exact_duplicates_count": len(cross_split_exact),
    "cross_split_near_duplicates_count": len(cross_split_near),
    "suspicious_filename_groups_count": len(suspicious_filename_groups),
    "exact_duplicates": exact_duplicates[:50],
    "near_duplicates": near_duplicates[:50],
    "suspicious_filename_groups": suspicious_filename_groups[:50],
    "cross_split_duplicate_pairs": all_cross_split_duplicates[:50],
    "conclusion": conclusion
}

audit_path_ml = ROOT / "ml" / "models" / "dataset_leakage_audit.json"
audit_path_ds = DATASET / "dataset_leakage_audit.json"

audit_path_ml.write_text(json.dumps(report, indent=2), encoding="utf-8")
audit_path_ds.write_text(json.dumps(report, indent=2), encoding="utf-8")

print(f"\nAudit complete! Report saved to {audit_path_ml}")
print(f"Conclusion: {conclusion}")
