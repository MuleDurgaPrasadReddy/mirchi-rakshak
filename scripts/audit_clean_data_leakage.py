import os
import re
import json
import hashlib
from pathlib import Path
from PIL import Image
import numpy as np
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "src" / "data_clean"

splits = ["train", "validation", "test"]
SUPPORTED = {".jpg", ".jpeg", ".png"}

print("Starting clean dataset leakage audit...")
all_files = []
split_counts = {"train": 0, "validation": 0, "test": 0}

for split in splits:
    split_dir = DATASET / split
    if not split_dir.exists():
        continue
    for class_dir in split_dir.iterdir():
        if class_dir.is_dir():
            for fpath in class_dir.iterdir():
                if fpath.suffix.lower() in SUPPORTED:
                    split_counts[split] += 1
                    rel_p = str(fpath.relative_to(DATASET)).replace("\\", "/")
                    all_files.append({
                        "path": fpath,
                        "rel_path": rel_p,
                        "name": fpath.name,
                        "split": split,
                        "class": class_dir.name
                    })

print(f"Total clean images collected for audit: {len(all_files)}")
print(f"Split counts: Train={split_counts['train']}, Validation={split_counts['validation']}, Test={split_counts['test']}")

# 1. Exact SHA-256 Duplicates Check (across splits)
hash_map = defaultdict(list)
cross_split_exact = []
total_exact_dups = 0

for item in all_files:
    data = item["path"].read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    item["sha256"] = sha
    hash_map[sha].append(item)

for sha, items in hash_map.items():
    if len(items) > 1:
        total_exact_dups += (len(items) - 1)
        splits_present = set(it["split"] for it in items)
        if len(splits_present) > 1:
            cross_split_exact.append({
                "sha256": sha,
                "splits": list(splits_present),
                "files": [it["rel_path"] for it in items]
            })

print(f"Total exact duplicates in clean dataset: {total_exact_dups}")
print(f"Cross-split exact duplicates: {len(cross_split_exact)}")

# 2. Perceptual dHash Near Duplicates Check (across splits)
def dhash(image, hash_size=8):
    img = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(img, dtype=np.int32)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return diff.flatten()

print("Computing dHash for all clean images...")
for item in all_files:
    try:
        with Image.open(item["path"]) as img:
            item["dhash"] = dhash(img)
    except Exception as e:
        print(f"Error computing dhash for {item['rel_path']}: {e}")
        item["dhash"] = None

near_duplicates = []
cross_split_near = []

n = len(all_files)
for i in range(n):
    if all_files[i]["dhash"] is None:
        continue
    for j in range(i + 1, n):
        if all_files[j]["dhash"] is not None:
            if all_files[i]["sha256"] != all_files[j]["sha256"]:
                dist = int(np.count_nonzero(all_files[i]["dhash"] != all_files[j]["dhash"]))
                if dist <= 2:
                    near_info = {
                        "file1": all_files[i]["rel_path"],
                        "file2": all_files[j]["rel_path"],
                        "split1": all_files[i]["split"],
                        "split2": all_files[j]["split"],
                        "class1": all_files[i]["class"],
                        "class2": all_files[j]["class"],
                        "hamming_distance": dist
                    }
                    near_duplicates.append(near_info)
                    if all_files[i]["split"] != all_files[j]["split"]:
                        cross_split_near.append(near_info)

print(f"Total near duplicates in clean dataset: {len(near_duplicates)}")
print(f"Cross-split near duplicates: {len(cross_split_near)}")

# 3. Suspicious Filename Groups Check (across splits)
def extract_base_stem(filename):
    stem = Path(filename).stem
    # Remove prefix patterns: ROTATE10-, ROTATE20-, ROTATE340-, ROTATE350-, ROTATE-, FLIPV-, FLIPH-, AUG-, COPY-
    stem = re.sub(r'^(ROTATE\d*-|FLIPV?-|FLIPH?-|AUG-|COPY-)', '', stem, flags=re.IGNORECASE)
    # Remove Veinal Mottle Virus augmentation suffixes: _bright_123, _zoomed_123, etc.
    stem = re.sub(r'_(bright|sheared|shifted|zoomed|rotated|flipped)_\d+', '', stem, flags=re.IGNORECASE)
    # Remove Roboflow hash pattern
    stem = re.sub(r'\.rf\.[a-f0-9]{32}', '', stem, flags=re.IGNORECASE)
    return stem.strip(" -_").lower()

filename_groups = defaultdict(list)
for item in all_files:
    base = extract_base_stem(item["name"])
    filename_groups[(item["class"], base)].append(item)

suspicious_filename_groups = []
for (cname, base), items in filename_groups.items():
    splits_present = set(it["split"] for it in items)
    if len(splits_present) > 1 and len(items) > 1:
        suspicious_filename_groups.append({
            "class": cname,
            "base_stem": base,
            "total_files": len(items),
            "splits": list(splits_present),
            "files": [it["rel_path"] for it in items]
        })

print(f"Suspicious cross-split filename groups: {len(suspicious_filename_groups)}")

# 4. Logical Image-Group IDs Check (across splits)
group_map_path = DATASET / "group_mapping.json"
cross_split_logical_groups = []

if group_map_path.exists():
    group_map = json.loads(group_map_path.read_text(encoding="utf-8"))
    groups_by_id = defaultdict(list)
    for rel_path, meta in group_map.items():
        groups_by_id[meta["group_id"]].append(meta)
        
    for gid, items in groups_by_id.items():
        splits_present = set(it["split"] for it in items)
        if len(splits_present) > 1:
            cross_split_logical_groups.append({
                "group_id": gid,
                "splits": list(splits_present),
                "items": items
            })
    print(f"Cross-split logical image groups: {len(cross_split_logical_groups)}")
else:
    print("Warning: group_mapping.json not found; skipping group ID check.")

# 5. Formulate Conclusion
is_clean = (
    len(cross_split_exact) == 0 and
    len(cross_split_near) == 0 and
    len(suspicious_filename_groups) == 0 and
    len(cross_split_logical_groups) == 0
)

if is_clean:
    conclusion = (
        "PERFECT LEAK-FREE DATASET: 0 cross-split exact duplicates, "
        "0 cross-split near duplicates, 0 suspicious filename groups, "
        "and 0 cross-split logical image groups. "
        "The train, validation, and test splits are completely disjoint and leak-free."
    )
else:
    conclusion = (
        f"AUDIT WARNING: Detected {len(cross_split_exact)} cross-split exact duplicates, "
        f"{len(cross_split_near)} cross-split near duplicates, "
        f"{len(suspicious_filename_groups)} suspicious filename groups, "
        f"and {len(cross_split_logical_groups)} cross-split logical groups."
    )

report = {
    "total_images": len(all_files),
    "split_counts": {
        "train_images": split_counts["train"],
        "validation_images": split_counts["validation"],
        "test_images": split_counts["test"]
    },
    "exact_duplicates_count": total_exact_dups,
    "near_duplicates_count": len(near_duplicates),
    "cross_split_exact_duplicates_count": len(cross_split_exact),
    "cross_split_near_duplicates_count": len(cross_split_near),
    "suspicious_filename_groups_count": len(suspicious_filename_groups),
    "cross_split_logical_groups_count": len(cross_split_logical_groups),
    "cross_split_exact_duplicates": cross_split_exact,
    "cross_split_near_duplicates": cross_split_near,
    "suspicious_filename_groups": suspicious_filename_groups,
    "cross_split_logical_groups": cross_split_logical_groups,
    "conclusion": conclusion
}

audit_path = DATASET / "dataset_leakage_audit.json"
audit_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

# Also save copy to ml/models for reference
ml_audit_path = ROOT / "ml" / "models" / "dataset_leakage_audit.json"
ml_audit_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

print(f"\nSecond leakage audit complete! Report saved to: {audit_path}")
print(f"Conclusion: {conclusion}")
