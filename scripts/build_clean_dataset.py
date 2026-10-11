import os
import re
import json
import shutil
import hashlib
import random
from pathlib import Path
from PIL import Image
import numpy as np
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DATASET = ROOT / "src" / "data"
TARGET_DATASET = ROOT / "src" / "data_clean"

if TARGET_DATASET.exists():
    shutil.rmtree(TARGET_DATASET)

SUPPORTED = {".jpg", ".jpeg", ".png"}

# 1. Collect all raw images
print("Step 1: Collecting all raw images from source dataset...")
all_raw_files = []
split_names = ["train", "valid", "test"]

for split in split_names:
    split_dir = SOURCE_DATASET / split
    if not split_dir.exists():
        continue
    for class_dir in split_dir.iterdir():
        if class_dir.is_dir():
            for fpath in class_dir.iterdir():
                if fpath.suffix.lower() in SUPPORTED:
                    all_raw_files.append({
                        "path": fpath,
                        "name": fpath.name,
                        "class": class_dir.name,
                        "split": split,
                        "rel_path": str(fpath.relative_to(SOURCE_DATASET)).replace("\\", "/")
                    })

total_original_images = len(all_raw_files)
print(f"Total original raw images collected: {total_original_images}")

# 2. Extract base stem and compute fingerprints
def extract_base_stem(filename):
    stem = Path(filename).stem
    # Remove prefix patterns: ROTATE10-, ROTATE20-, ROTATE340-, ROTATE350-, ROTATE-, FLIPV-, FLIPH-, AUG-, COPY-
    stem = re.sub(r'^(ROTATE\d*-|FLIPV?-|FLIPH?-|AUG-|COPY-)', '', stem, flags=re.IGNORECASE)
    # Remove Veinal Mottle Virus augmentation suffixes: _bright_123, _zoomed_123, etc.
    stem = re.sub(r'_(bright|sheared|shifted|zoomed|rotated|flipped)_\d+', '', stem, flags=re.IGNORECASE)
    # Remove Roboflow hash pattern
    stem = re.sub(r'\.rf\.[a-f0-9]{32}', '', stem, flags=re.IGNORECASE)
    return stem.strip(" -_").lower()

print("Computing SHA-256 hashes and dHash perceptual fingerprints...")
def dhash(image, hash_size=8):
    img = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(img, dtype=np.int32)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return diff.flatten()

for item in all_raw_files:
    item["base_stem"] = extract_base_stem(item["name"])
    data = item["path"].read_bytes()
    item["sha256"] = hashlib.sha256(data).hexdigest()
    try:
        with Image.open(item["path"]) as img:
            item["dhash"] = dhash(img)
    except Exception as e:
        print(f"Warning: could not compute dhash for {item['name']}: {e}")
        item["dhash"] = None

# 3. Disjoint Set Union (Union-Find) for Logical Grouping
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
    def find(self, i):
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]
    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j

uf = UnionFind(len(all_raw_files))

# Merge Rule 1: Exact SHA-256 hash match
sha_map = {}
exact_hash_duplicates_count = 0
for idx, item in enumerate(all_raw_files):
    s = item["sha256"]
    if s in sha_map:
        uf.union(idx, sha_map[s])
        exact_hash_duplicates_count += 1
    else:
        sha_map[s] = idx

# Merge Rule 2: Base stem match within same class
stem_map = {}
for idx, item in enumerate(all_raw_files):
    key = (item["class"], item["base_stem"])
    if key in stem_map:
        uf.union(idx, stem_map[key])
    else:
        stem_map[key] = idx

# Merge Rule 3: Perceptual dHash <= 2 (global across dataset to eliminate cross-class and within-class contamination)
print("Clustering near-duplicate images using dHash (Hamming distance <= 2)...")
n = len(all_raw_files)
near_duplicate_pairs = 0
for i in range(n):
    if all_raw_files[i]["dhash"] is None:
        continue
    for j in range(i + 1, n):
        if all_raw_files[j]["dhash"] is not None:
            dist = np.count_nonzero(all_raw_files[i]["dhash"] != all_raw_files[j]["dhash"])
            if dist <= 2:
                if all_raw_files[i]["sha256"] != all_raw_files[j]["sha256"]:
                    near_duplicate_pairs += 1
                uf.union(i, j)

# 4. Gather Logical Groups
groups_dict = defaultdict(list)
for idx, item in enumerate(all_raw_files):
    root_id = uf.find(idx)
    groups_dict[root_id].append(item)

total_unique_groups = len(groups_dict)
print(f"Total unique logical image groups identified: {total_unique_groups}")

# Count groups that contain near-duplicate pairs
near_duplicate_groups_count = 0
for gid, items in groups_dict.items():
    unique_shas = set(it["sha256"] for it in items)
    if len(unique_shas) > 1:
        # has multiple distinct images merged (e.g. near-duplicates)
        near_duplicate_groups_count += 1

# 5. Choose Exactly ONE Representative Image per Group (Step 3)
def select_representative(items):
    def score(item):
        name = item["name"].upper()
        penalty = 0
        # Heavily penalize offline augmentation prefixes
        if any(name.startswith(p) for p in ["ROTATE", "FLIP", "AUG", "COPY"]):
            penalty += 1000
        # Penalize Veinal Mottle Virus augmentation suffixes
        if any(tok in name.lower() for tok in ["_bright_", "_sheared_", "_shifted_", "_zoomed_", "_rotated_", "_flipped_"]):
            penalty += 500
        # Penalize Roboflow augmented tokens
        if ".RF." in name:
            penalty += 200
        if "COPY" in name:
            penalty += 100
        # Prefer original / cleaner / shorter filenames
        penalty += len(item["name"])
        return penalty
    
    sorted_items = sorted(items, key=lambda it: (score(it), it["name"]))
    return sorted_items[0]

representatives_by_class = defaultdict(list)
all_clean_representatives = []

for group_id, items in groups_dict.items():
    # Assign group to majority class
    class_counts = Counter(it["class"] for it in items)
    assigned_class = sorted(class_counts.items(), key=lambda x: (-x[1], x[0]))[0][0]
    
    rep = select_representative(items)
    rep_entry = {
        "group_id": f"GROUP_{group_id}",
        "assigned_class": assigned_class,
        "representative": rep,
        "all_members": items,
        "member_count": len(items)
    }
    representatives_by_class[assigned_class].append(rep_entry)
    all_clean_representatives.append(rep_entry)

# Calculate removal counts
number_removed_exact = exact_hash_duplicates_count
number_removed_augmented = total_original_images - total_unique_groups - number_removed_exact
if number_removed_augmented < 0:
    number_removed_augmented = 0

print(f"Exact duplicates removed: {number_removed_exact}")
print(f"Augmented & near-duplicate copies removed: {total_original_images - total_unique_groups}")

# 6. Group-level 80% Train / 10% Validation / 10% Test Stratified Split (Step 4)
rng = random.Random(42)

for split_name in ["train", "validation", "test"]:
    for cname in sorted(representatives_by_class.keys()):
        (TARGET_DATASET / split_name / cname).mkdir(parents=True, exist_ok=True)

class_distribution = []
per_class_counts = {}
per_class_percentages = {}
group_mapping = {}

used_filenames_by_split_class = defaultdict(set)

for cname in sorted(representatives_by_class.keys()):
    groups = list(representatives_by_class[cname])
    # Deterministic shuffle
    rng.shuffle(groups)
    
    total_grp = len(groups)
    if total_grp >= 3:
        n_val = max(1, int(round(total_grp * 0.10)))
        n_test = max(1, int(round(total_grp * 0.10)))
        n_train = total_grp - n_val - n_test
    elif total_grp == 2:
        n_train = 1
        n_val = 1
        n_test = 0
    else:
        n_train = 1
        n_val = 0
        n_test = 0
        
    train_grps = groups[:n_train]
    val_grps = groups[n_train:n_train + n_val]
    test_grps = groups[n_train + n_val:]
    
    def copy_group_rep(grp_list, split_label):
        for grp in grp_list:
            rep = grp["representative"]
            dest_name = rep["name"]
            # Ensure unique filename if collision occurs within destination split and class
            if dest_name in used_filenames_by_split_class[(split_label, cname)]:
                stem = Path(dest_name).stem
                suffix = Path(dest_name).suffix
                dest_name = f"{stem}_{grp['group_id']}{suffix}"
            used_filenames_by_split_class[(split_label, cname)].add(dest_name)
            
            dest_path = TARGET_DATASET / split_label / cname / dest_name
            shutil.copy2(rep["path"], dest_path)
            
            rel_path = f"{split_label}/{cname}/{dest_name}"
            group_mapping[rel_path] = {
                "group_id": grp["group_id"],
                "split": split_label,
                "class": cname,
                "original_source_file": rep["rel_path"],
                "total_group_members": grp["member_count"]
            }
            
    copy_group_rep(train_grps, "train")
    copy_group_rep(val_grps, "validation")
    copy_group_rep(test_grps, "test")
    
    c_train = len(train_grps)
    c_val = len(val_grps)
    c_test = len(test_grps)
    
    per_class_counts[cname] = {
        "train": c_train,
        "validation": c_val,
        "test": c_test,
        "total": total_grp
    }
    
    per_class_percentages[cname] = {
        "train": round((c_train / total_grp) * 100, 2) if total_grp else 0,
        "validation": round((c_val / total_grp) * 100, 2) if total_grp else 0,
        "test": round((c_test / total_grp) * 100, 2) if total_grp else 0
    }
    
    class_distribution.append({
        "class_name": cname,
        "train_count": c_train,
        "validation_count": c_val,
        "test_count": c_test,
        "train_percentage": per_class_percentages[cname]["train"],
        "validation_percentage": per_class_percentages[cname]["validation"],
        "test_percentage": per_class_percentages[cname]["test"],
        "total_group_count": total_grp
    })

total_clean_train = sum(d["train_count"] for d in class_distribution)
total_clean_val = sum(d["validation_count"] for d in class_distribution)
total_clean_test = sum(d["test_count"] for d in class_distribution)

# 7. Generate Dataset Report (Step 6)
dataset_report = {
    "total_original_images": total_original_images,
    "total_unique_logical_groups": total_unique_groups,
    "number_removed_exact_duplicates": number_removed_exact,
    "number_removed_offline_augmented_duplicates": total_original_images - total_unique_groups,
    "number_of_near_duplicate_groups": near_duplicate_groups_count,
    "train_count": total_clean_train,
    "validation_count": total_clean_val,
    "test_count": total_clean_test,
    "per_class_counts": per_class_counts,
    "per_class_percentages": per_class_percentages,
    "class_distribution": class_distribution
}

dist_file = TARGET_DATASET / "dataset_distribution.json"
dist_file.write_text(json.dumps(dataset_report, indent=2), encoding="utf-8")

# Save group mapping for the audit script
group_map_file = TARGET_DATASET / "group_mapping.json"
group_map_file.write_text(json.dumps(group_mapping, indent=2), encoding="utf-8")

print(f"\nClean dataset successfully built at {TARGET_DATASET}!")
print(f"Distribution report saved to {dist_file}")

print("\n" + "=" * 80)
print(f"{'Class Name':<32} | {'Train (80%)':<12} | {'Val (10%)':<10} | {'Test (10%)':<10} | {'Total Groups':<12}")
print("-" * 80)
for d in class_distribution:
    print(f"{d['class_name']:<32} | {d['train_count']:<12} | {d['validation_count']:<10} | {d['test_count']:<10} | {d['total_group_count']:<12}")
print("-" * 80)
print(f"{'TOTAL':<32} | {total_clean_train:<12} | {total_clean_val:<10} | {total_clean_test:<10} | {total_unique_groups:<12}")
print("=" * 80)
