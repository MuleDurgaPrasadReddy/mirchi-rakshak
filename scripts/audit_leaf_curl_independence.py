import os
import csv
import json
import hashlib
import numpy as np
from PIL import Image
import imagehash
from datasets import load_dataset
from concurrent.futures import ThreadPoolExecutor

DATA_CLEAN_DIR = os.path.join("src", "data_clean")
NEW_DATA_DIR = os.path.join("mirchi_new_data", "Leaf_Curl_Virus")
METADATA_PATH = os.path.join(NEW_DATA_DIR, "metadata.csv")
AUDIT_CSV_PATH = os.path.join(NEW_DATA_DIR, "independence_audit.csv")
SUMMARY_JSON_PATH = os.path.join(NEW_DATA_DIR, "independence_audit_summary.json")
GROUP_MAPPING_PATH = os.path.join(DATA_CLEAN_DIR, "group_mapping.json")
DATASET_NAME = "Project-AgML/chili_leaf_curl_detection"

NEAR_DUPLICATE_THRESHOLD = 6  # Hamming distance threshold for 64-bit perceptual hashes

def get_sha256(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def hash_to_bool_array(hash_obj):
    return hash_obj.hash.flatten()

def laplacian_variance(gray_arr):
    padded = np.pad(gray_arr, 1, mode='reflect')
    lap = (padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:] - 4 * padded[1:-1, 1:-1])
    return float(np.var(lap))

def evaluate_quality(img):
    flags = []
    width, height = img.size
    
    if width < 100 or height < 100:
        flags.append("Low Resolution")

    gray = np.array(img.convert("L"), dtype=np.float32)
    mean_bright = float(np.mean(gray))
    std_dev = float(np.std(gray))
    lap_var = laplacian_variance(gray)

    if mean_bright < 30.0:
        flags.append("Extremely Dark")
    elif mean_bright > 225.0:
        flags.append("Overexposed")

    if std_dev < 15.0:
        flags.append("Low Contrast / Monochromatic")

    if lap_var < 45.0:
        flags.append("Blurry")

    return (", ".join(flags)) if flags else "Clean"

def process_existing_file(full_path):
    rel_path = os.path.relpath(full_path, DATA_CLEAN_DIR)
    try:
        sha = get_sha256(full_path)
        with Image.open(full_path) as img:
            w, h = img.size
            fmt = img.format or "JPEG"
            dh = imagehash.dhash(img)
            ph = imagehash.phash(img)
        return {
            "rel_path": rel_path,
            "sha": sha,
            "dim": f"{w}x{h}",
            "fmt": fmt,
            "dhash": hash_to_bool_array(dh),
            "phash": hash_to_bool_array(ph)
        }
    except Exception as e:
        print(f"Error processing {full_path}: {e}", flush=True)
        return None

def main():
    print("=== Step 1: Inventorying Existing Clean Dataset & Group Mapping ===", flush=True)
    existing_files = []
    for root, _, files in os.walk(DATA_CLEAN_DIR):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
                existing_files.append(os.path.join(root, file))

    print(f"Found {len(existing_files)} existing image files. Processing in parallel...", flush=True)
    
    existing_sha256_map = {}
    existing_paths = []
    existing_dhashes = []
    existing_phashes = []
    existing_dimensions = set()
    existing_formats = set()

    with ThreadPoolExecutor(max_workers=16) as executor:
        results = list(executor.map(process_existing_file, existing_files))

    for res in results:
        if res:
            existing_sha256_map[res["sha"]] = res["rel_path"]
            existing_paths.append(res["rel_path"])
            existing_dhashes.append(res["dhash"])
            existing_phashes.append(res["phash"])
            existing_dimensions.add(res["dim"])
            existing_formats.add(res["fmt"])

    ex_dhash_mat = np.array(existing_dhashes, dtype=bool) if existing_dhashes else np.empty((0, 64), dtype=bool)
    ex_phash_mat = np.array(existing_phashes, dtype=bool) if existing_phashes else np.empty((0, 64), dtype=bool)

    group_count = None
    if os.path.exists(GROUP_MAPPING_PATH):
        try:
            with open(GROUP_MAPPING_PATH, "r", encoding="utf-8") as f:
                gmap = json.load(f)
                group_count = len(gmap)
        except Exception as e:
            print(f"Error reading group_mapping.json: {e}", flush=True)

    print(f"Existing images total count: {len(existing_paths)}", flush=True)
    print(f"Existing logical groups count: {group_count}", flush=True)
    print(f"Existing image dimensions sample: {list(existing_dimensions)[:5]}", flush=True)
    print(f"Existing image formats: {list(existing_formats)}", flush=True)

    print("\n=== Step 2: Inventorying New Candidate Images ===", flush=True)
    candidates_metadata = []
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                candidates_metadata.append(row)
    else:
        print(f"Error: Metadata file not found at {METADATA_PATH}", flush=True)
        return

    candidate_dimensions = set()
    candidate_formats = set()
    candidate_records = []

    for item in candidates_metadata:
        filename = item["new_filename"]
        filepath = os.path.join(NEW_DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Warning: File {filepath} listed in metadata does not exist.", flush=True)
            continue

        sha = get_sha256(filepath)
        with Image.open(filepath) as img:
            w, h = img.size
            fmt = img.format or "JPEG"
            dh = imagehash.dhash(img)
            ph = imagehash.phash(img)
            quality_flag = evaluate_quality(img)

        candidate_dimensions.add(f"{w}x{h}")
        candidate_formats.add(fmt)

        candidate_records.append({
            "metadata": item,
            "filepath": filepath,
            "filename": filename,
            "sha256": sha,
            "dhash_arr": hash_to_bool_array(dh),
            "phash_arr": hash_to_bool_array(ph),
            "quality_flag": quality_flag,
            "width": w,
            "height": h
        })

    print(f"New candidate images count: {len(candidate_records)}", flush=True)
    print(f"Candidate image dimensions sample: {list(candidate_dimensions)[:5]}", flush=True)
    print(f"Candidate image formats: {list(candidate_formats)}", flush=True)

    print("\n=== Step 3: Loading Original Dataset for Object Category Inspection ===", flush=True)
    hf_dataset = load_dataset(DATASET_NAME, split="train")
    cat_names = ["Healthy", "Mites", "Virus"]
    if "objects" in hf_dataset.features and "categories" in hf_dataset.features["objects"]:
        cat_feat = hf_dataset.features["objects"]["categories"]
        if hasattr(cat_feat, "feature") and hasattr(cat_feat.feature, "names"):
            cat_names = cat_feat.feature.names

    print(f"Dataset category mapping: {cat_names}", flush=True)

    print("\n=== Step 4: Performing Vectorized Exact & Near Duplicate Audits & Label Inspection ===", flush=True)
    audit_rows = []
    
    exact_duplicates_count = 0
    near_duplicates_count = 0
    quality_flagged_count = 0
    review_required_count = 0
    virus_only_count = 0
    virus_multi_category_count = 0
    clean_independent_count = 0

    for cand in candidate_records:
        filename = cand["filename"]
        orig_idx = int(cand["metadata"]["original_index"])
        sha = cand["sha256"]
        c_dh = cand["dhash_arr"]
        c_ph = cand["phash_arr"]
        quality_flag = cand["quality_flag"]

        # Exact Duplicate Check
        exact_duplicate = False
        matching_existing_file = ""
        if sha in existing_sha256_map:
            exact_duplicate = True
            matching_existing_file = existing_sha256_map[sha]
            exact_duplicates_count += 1

        # Near Duplicate Check via Vectorized Hamming Distance
        near_duplicate = False
        nearest_existing_file = ""
        min_distance = 999

        if len(existing_paths) > 0:
            d_dists = np.sum(c_dh != ex_dhash_mat, axis=1)
            p_dists = np.sum(c_ph != ex_phash_mat, axis=1)
            min_dists = np.minimum(d_dists, p_dists)

            min_idx = int(np.argmin(min_dists))
            min_distance = int(min_dists[min_idx])
            nearest_existing_file = existing_paths[min_idx]

        if min_distance <= NEAR_DUPLICATE_THRESHOLD:
            near_duplicate = True
            near_duplicates_count += 1
        elif exact_duplicate:
            min_distance = 0
            near_duplicate = True

        # Object category check
        hf_row = hf_dataset[orig_idx]
        cats = hf_row.get("objects", {}).get("categories", [])
        cat_set = set(cats)
        
        cat_labels = [cat_names[c] for c in cat_set if 0 <= c < len(cat_names)]
        
        if set(cat_labels) == {"Virus"}:
            obj_categories_str = "Virus Only"
            virus_only_count += 1
        else:
            other_cats = [c for c in cat_labels if c != "Virus"]
            obj_categories_str = f"Virus + {', '.join(other_cats)}" if other_cats else "Virus Only"
            virus_multi_category_count += 1

        if quality_flag != "Clean":
            quality_flagged_count += 1

        # Decision & Action Logic
        review_required = False
        recommended_action = "ACCEPT"

        if exact_duplicate:
            review_required = True
            recommended_action = "REJECT_EXACT_DUPLICATE"
        elif near_duplicate:
            review_required = True
            recommended_action = "REJECT_NEAR_DUPLICATE"
        elif quality_flag != "Clean":
            review_required = True
            recommended_action = f"REVIEW_QUALITY ({quality_flag})"
        elif obj_categories_str != "Virus Only":
            review_required = True
            recommended_action = "REVIEW_MULTI_CATEGORY"
        else:
            recommended_action = "ACCEPT_CLEAN_INDEPENDENT"
            clean_independent_count += 1

        if review_required:
            review_required_count += 1

        audit_rows.append({
            "new_filename": filename,
            "original_index": orig_idx,
            "source_dataset": cand["metadata"]["source_dataset"],
            "original_label": cand["metadata"]["original_label"],
            "exact_duplicate": exact_duplicate,
            "matching_existing_file": matching_existing_file,
            "near_duplicate": near_duplicate,
            "nearest_existing_file": nearest_existing_file,
            "perceptual_distance": min_distance,
            "quality_flag": quality_flag,
            "object_categories": obj_categories_str,
            "review_required": review_required,
            "recommended_action": recommended_action
        })

    # Save independence_audit.csv
    csv_fieldnames = [
        "new_filename",
        "original_index",
        "source_dataset",
        "original_label",
        "exact_duplicate",
        "matching_existing_file",
        "near_duplicate",
        "nearest_existing_file",
        "perceptual_distance",
        "quality_flag",
        "object_categories",
        "review_required",
        "recommended_action"
    ]
    with open(AUDIT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fieldnames)
        writer.writeheader()
        writer.writerows(audit_rows)

    # Save independence_audit_summary.json
    summary = {
        "total_candidates": len(candidate_records),
        "exact_duplicates": exact_duplicates_count,
        "near_duplicates": near_duplicates_count,
        "quality_flagged": quality_flagged_count,
        "review_required": review_required_count,
        "clean_independent_candidates": clean_independent_count,
        "virus_only_candidates": virus_only_count,
        "virus_plus_other_category_candidates": virus_multi_category_count
    }
    with open(SUMMARY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Print Report
    print("\n" + "="*60, flush=True)
    print("        INDEPENDENCE & QUALITY AUDIT FINAL REPORT        ", flush=True)
    print("="*60, flush=True)
    print(f"Total Candidate Images Audited  : {len(candidate_records)}", flush=True)
    print(f"Existing Clean Images Inventory : {len(existing_paths)}", flush=True)
    print(f"Existing Logical Groups Count   : {group_count}", flush=True)
    print("----------------------------------------------------------", flush=True)
    print(f"Exact Duplicates Found          : {exact_duplicates_count}", flush=True)
    print(f"Near Duplicates Found           : {near_duplicates_count}", flush=True)
    print(f"Quality Flagged Images          : {quality_flagged_count}", flush=True)
    print(f"Virus Only Candidates           : {virus_only_count}", flush=True)
    print(f"Virus + Other Categories        : {virus_multi_category_count}", flush=True)
    print(f"Review Required Total           : {review_required_count}", flush=True)
    print(f"Clean Independent Candidates    : {clean_independent_count}", flush=True)
    print("="*60, flush=True)
    print(f"Audit CSV generated             : {AUDIT_CSV_PATH}", flush=True)
    print(f"Summary JSON generated          : {SUMMARY_JSON_PATH}", flush=True)
    print("="*60 + "\n", flush=True)

if __name__ == "__main__":
    main()
