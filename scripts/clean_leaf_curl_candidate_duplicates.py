import os
import glob
import json
import csv
import hashlib
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CLEAN_DIR = ROOT / "src" / "data_clean"
CANDIDATE_DIR = ROOT / "mirchi_new_data" / "Leaf_Curl_Virus"

AUDIT_JSON_IN = CANDIDATE_DIR / "leakage_audit.json"
POST_AUDIT_JSON_OUT = CANDIDATE_DIR / "leakage_audit_post_cleanup.json"
POST_AUDIT_CSV_OUT = CANDIDATE_DIR / "leakage_audit_post_cleanup.csv"

def compute_dhash(pil_img, hash_size=8):
    img = pil_img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
    pixels = np.array(img, dtype=float)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return diff.flatten()

def hamming_distance(hash1, hash2):
    return int(np.sum(hash1 != hash2))

def main():
    print("==================================================")
    print("  LEAF CURL CANDIDATE POOL DUPLICATE CLEANUP     ")
    print("==================================================")
    
    # 1. Read Leakage Audit JSON
    with open(AUDIT_JSON_IN, "r", encoding="utf-8") as f:
        audit_data = json.load(f)
        
    suspicious_items = audit_data["audit_summary"]["suspicious_files"]
    print(f"Loaded {len(suspicious_items)} suspicious files flagged in initial audit.")
    
    initial_candidate_files = sorted(list(CANDIDATE_DIR.glob("**/*")))
    initial_candidate_files = [f for f in initial_candidate_files if f.suffix.lower() in [".jpg", ".jpeg", ".png"]]
    initial_count = len(initial_candidate_files)
    print(f"Candidates before cleanup: {initial_count}")
    
    removed_files = []
    
    # Process files to remove
    for item in suspicious_items:
        rel_path = item["filename"]
        abs_path = ROOT / rel_path
        
        if abs_path.exists():
            # Confirm it is an internal duplicate (not touching src/data_clean!)
            if "src/data_clean" in str(abs_path).replace("\\", "/"):
                print(f"PROTECTION TRIGGERED: Skipping deletion of clean dataset file {abs_path}")
                continue
                
            abs_path.unlink()
            removed_files.append(rel_path)
            print(f"Removed duplicate candidate: {rel_path}")
            
    print(f"\nSuccessfully removed {len(removed_files)} duplicate candidate files.")
    
    # Re-audit candidates post cleanup
    remaining_candidate_files = sorted(list(CANDIDATE_DIR.glob("**/*")))
    remaining_candidate_files = [f for f in remaining_candidate_files if f.suffix.lower() in [".jpg", ".jpeg", ".png"]]
    remaining_count = len(remaining_candidate_files)
    
    print(f"Candidates remaining post cleanup: {remaining_count}")
    
    # Inventory existing clean dataset images
    clean_files = sorted(list(CLEAN_DIR.glob("**/*")))
    clean_files = [f for f in clean_files if f.suffix.lower() in [".jpg", ".jpeg", ".png"]]
    
    existing_hashes = {}
    existing_dhashes = []
    existing_filenames = set()
    
    for fpath in clean_files:
        rel_path = str(fpath.relative_to(ROOT)).replace("\\", "/")
        existing_filenames.add(fpath.name)
        content = fpath.read_bytes()
        md5_h = hashlib.md5(content).hexdigest()
        sha256_h = hashlib.sha256(content).hexdigest()
        existing_hashes[md5_h] = (rel_path, "MD5")
        existing_hashes[sha256_h] = (rel_path, "SHA256")
        
        try:
            pil_img = Image.open(fpath)
            dh = compute_dhash(pil_img)
            split = "train" if "/train/" in rel_path else ("validation" if "/validation/" in rel_path else "test")
            existing_dhashes.append((rel_path, dh, split))
        except Exception:
            pass
            
    # Post-Cleanup Audit
    post_records = []
    post_suspicious = []
    
    post_exact_dups = 0
    post_near_dups = 0
    post_train_overlaps = 0
    post_val_overlaps = 0
    post_test_overlaps = 0
    post_internal_dups = 0
    
    post_candidate_hash_map = {}
    post_candidate_dhashes = []
    
    for cpath in remaining_candidate_files:
        c_rel_path = str(cpath.relative_to(ROOT)).replace("\\", "/")
        c_fname = cpath.name
        
        is_susp = False
        reasons = []
        matched_file = None
        sim_score = 0.0
        recommended_action = "keep_candidate"
        
        content = cpath.read_bytes()
        c_md5 = hashlib.md5(content).hexdigest()
        c_sha256 = hashlib.sha256(content).hexdigest()
        
        try:
            pil_img = Image.open(cpath)
            width, height = pil_img.size
        except Exception as e:
            is_susp = True
            reasons.append(f"Corrupted image file: {e}")
            recommended_action = "exclude_corrupted"
            width, height = 0, 0
            
        # Check against existing clean dataset
        if c_md5 in existing_hashes or c_sha256 in existing_hashes:
            is_susp = True
            matched_file = existing_hashes.get(c_md5, existing_hashes.get(c_sha256))[0]
            reasons.append("Exact duplicate of existing dataset image")
            sim_score = 1.0
            post_exact_dups += 1
            if "/train/" in matched_file:
                post_train_overlaps += 1
            elif "/validation/" in matched_file:
                post_val_overlaps += 1
            elif "/test/" in matched_file:
                post_test_overlaps += 1
            recommended_action = "exclude_exact_duplicate"
            
        if c_md5 in post_candidate_hash_map:
            is_susp = True
            matched_file = post_candidate_hash_map[c_md5]
            reasons.append("Internal exact duplicate within candidate dataset")
            sim_score = 1.0
            post_internal_dups += 1
            recommended_action = "exclude_internal_duplicate"
        else:
            post_candidate_hash_map[c_md5] = c_rel_path
            
        if width > 0 and height > 0:
            c_dh = compute_dhash(pil_img)
            for e_rel_path, e_dh, e_split in existing_dhashes:
                dist = hamming_distance(c_dh, e_dh)
                if dist <= 6:
                    is_susp = True
                    matched_file = e_rel_path
                    sim_score = round(1.0 - (dist / 64.0), 4)
                    reasons.append(f"Near-duplicate of existing dataset image (dHash distance {dist}/64)")
                    post_near_dups += 1
                    if e_split == "train":
                        post_train_overlaps += 1
                    elif e_split == "validation":
                        post_val_overlaps += 1
                    elif e_split == "test":
                        post_test_overlaps += 1
                    recommended_action = "exclude_near_duplicate"
                    break
                    
            for int_rel_path, int_dh in post_candidate_dhashes:
                dist = hamming_distance(c_dh, int_dh)
                if dist <= 4:
                    is_susp = True
                    matched_file = int_rel_path
                    sim_score = round(1.0 - (dist / 64.0), 4)
                    reasons.append(f"Internal near-duplicate of candidate (dHash distance {dist}/64)")
                    post_internal_dups += 1
                    recommended_action = "exclude_internal_near_duplicate"
                    break
                    
            post_candidate_dhashes.append((c_rel_path, c_dh))
            
        category = cpath.parent.name
        record = {
            "filename": c_rel_path,
            "category": category,
            "width": width,
            "height": height,
            "md5_hash": c_md5,
            "is_suspicious": is_susp,
            "audit_status": "SUSPICIOUS" if is_susp else "SAFE",
            "reasons": "; ".join(reasons) if reasons else "None - Completely Independent",
            "matched_existing_file": matched_file if matched_file else "None",
            "similarity_score": sim_score,
            "recommended_action": recommended_action
        }
        post_records.append(record)
        
        if is_susp:
            post_suspicious.append(record)
            
        post_verdict = "PASS" if len(post_suspicious) == 0 else "FAIL"
        
    post_summary = {
        "verdict": post_verdict,
        "candidates_before_cleanup": initial_count,
        "files_removed": len(removed_files),
        "duplicate_groups_resolved": len(suspicious_items),
        "candidates_remaining": remaining_count,
        "exact_internal_duplicates_remaining": post_internal_dups,
        "near_duplicates_remaining": post_near_dups,
        "existing_dataset_overlaps": post_train_overlaps + post_val_overlaps + post_test_overlaps,
        "train_overlaps": post_train_overlaps,
        "validation_overlaps": post_val_overlaps,
        "test_overlaps": post_test_overlaps,
        "suspicious_files": post_suspicious
    }
    
    post_output_json = {
        "audit_summary": post_summary,
        "candidate_audits": post_records
    }
    
    with open(POST_AUDIT_JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(post_output_json, f, indent=2)
    print(f"Saved post-cleanup JSON leakage audit to {POST_AUDIT_JSON_OUT}")
    
    fieldnames = [
        "filename",
        "category",
        "width",
        "height",
        "md5_hash",
        "is_suspicious",
        "audit_status",
        "reasons",
        "matched_existing_file",
        "similarity_score",
        "recommended_action"
    ]
    with open(POST_AUDIT_CSV_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(post_records)
    print(f"Saved post-cleanup CSV leakage audit to {POST_AUDIT_CSV_OUT}")
    
    print("\n" + "=" * 65)
    print("      POST-CLEANUP CANDIDATE LEAKAGE AUDIT REPORT        ")
    print("=" * 65)
    print(f"VERDICT                         : {post_verdict}")
    print(f"Candidates Before Cleanup       : {initial_count}")
    print(f"Files Removed                   : {len(removed_files)}")
    print(f"Duplicate Groups Resolved       : {len(suspicious_items)}")
    print(f"Candidates Remaining            : {remaining_count}")
    print("-" * 65)
    print(f"Exact Internal Duplicates       : {post_internal_dups}")
    print(f"Near Duplicates                 : {post_near_dups}")
    print(f"Existing Dataset Overlaps       : {post_summary['existing_dataset_overlaps']}")
    print(f"  - Train Overlaps              : {post_train_overlaps}")
    print(f"  - Validation Overlaps         : {post_val_overlaps}")
    print(f"  - Test Overlaps               : {post_test_overlaps}")
    print("=" * 65)

if __name__ == "__main__":
    main()
