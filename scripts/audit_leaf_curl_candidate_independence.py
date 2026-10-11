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

JSON_OUT = CANDIDATE_DIR / "leakage_audit.json"
CSV_OUT = CANDIDATE_DIR / "leakage_audit.csv"

def compute_dhash(pil_img, hash_size=8):
    """Compute 64-bit dHash of PIL image."""
    img = pil_img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
    pixels = np.array(img, dtype=float)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return diff.flatten()

def hamming_distance(hash1, hash2):
    return int(np.sum(hash1 != hash2))

def main():
    print("==================================================")
    print("  LEAF CURL CANDIDATE INDEPENDENCE & LEAKAGE AUDIT ")
    print("==================================================")
    
    # 1. Inventory Existing Clean Dataset
    clean_files = sorted(list(CLEAN_DIR.glob("**/*")))
    clean_files = [f for f in clean_files if f.suffix.lower() in [".jpg", ".jpeg", ".png"]]
    print(f"Total existing clean dataset images: {len(clean_files)}")
    
    existing_hashes = {}      # md5 -> relative_path
    existing_dhashes = []     # (relative_path, dhash_array, split_type)
    existing_filenames = set()# filename -> relative_path
    
    for fpath in clean_files:
        rel_path = str(fpath.relative_to(ROOT)).replace("\\", "/")
        fname = fpath.name
        existing_filenames.add(fname)
        
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
            
    # 2. Inventory Candidate Dataset
    candidate_files = sorted(list(CANDIDATE_DIR.glob("**/*")))
    candidate_files = [f for f in candidate_files if f.suffix.lower() in [".jpg", ".jpeg", ".png"]]
    print(f"Total candidate images to audit: {len(candidate_files)}")
    
    candidate_records = []
    suspicious_files = []
    
    exact_duplicates_count = 0
    near_duplicates_count = 0
    train_overlaps_count = 0
    val_overlaps_count = 0
    test_overlaps_count = 0
    internal_duplicates_count = 0
    
    candidate_hash_map = {}  # md5 -> candidate_rel_path
    candidate_dhashes = []   # (candidate_rel_path, dhash_array)
    
    for cpath in candidate_files:
        c_rel_path = str(cpath.relative_to(ROOT)).replace("\\", "/")
        c_fname = cpath.name
        
        is_suspicious = False
        reasons = []
        matched_file = None
        sim_score = None
        recommended_action = "keep_candidate"
        
        try:
            pil_img = Image.open(cpath)
            width, height = pil_img.size
            pil_img.verify() # Integrity check
            pil_img = Image.open(cpath) # Reopen after verify
        except Exception as e:
            is_suspicious = True
            reasons.append(f"Corrupted image file: {e}")
            recommended_action = "exclude_corrupted"
            width, height = 0, 0
            
        content = cpath.read_bytes()
        c_md5 = hashlib.md5(content).hexdigest()
        c_sha256 = hashlib.sha256(content).hexdigest()
        
        # Check 1: Exact Duplicate against Existing Dataset
        if c_md5 in existing_hashes or c_sha256 in existing_hashes:
            is_suspicious = True
            matched_file = existing_hashes.get(c_md5, existing_hashes.get(c_sha256))[0]
            reasons.append("Exact cryptographic duplicate of existing dataset image")
            sim_score = 1.0
            exact_duplicates_count += 1
            if "/train/" in matched_file:
                train_overlaps_count += 1
            elif "/validation/" in matched_file:
                val_overlaps_count += 1
            elif "/test/" in matched_file:
                test_overlaps_count += 1
            recommended_action = "exclude_exact_duplicate"
            
        # Check 2: Internal Duplicate within Candidates
        if c_md5 in candidate_hash_map:
            is_suspicious = True
            matched_file = candidate_hash_map[c_md5]
            reasons.append("Internal exact duplicate within candidate dataset")
            sim_score = 1.0
            internal_duplicates_count += 1
            recommended_action = "exclude_internal_duplicate"
        else:
            candidate_hash_map[c_md5] = c_rel_path
            
        # Check 3: Filename Collision
        if c_fname in existing_filenames:
            is_suspicious = True
            reasons.append("Filename collision with existing dataset file")
            if recommended_action == "keep_candidate":
                recommended_action = "rename_candidate"
                
        # Check 4: Perceptual Near-Duplicate (dHash Hamming distance <= 6)
        if width > 0 and height > 0:
            c_dh = compute_dhash(pil_img)
            
            # Check against existing clean dataset dhashes
            for e_rel_path, e_dh, e_split in existing_dhashes:
                dist = hamming_distance(c_dh, e_dh)
                if dist <= 6:  # High perceptual similarity
                    is_suspicious = True
                    matched_file = e_rel_path
                    sim_score = round(1.0 - (dist / 64.0), 4)
                    reasons.append(f"Near-duplicate of existing dataset image (dHash distance {dist}/64)")
                    near_duplicates_count += 1
                    if e_split == "train":
                        train_overlaps_count += 1
                    elif e_split == "validation":
                        val_overlaps_count += 1
                    elif e_split == "test":
                        test_overlaps_count += 1
                    recommended_action = "exclude_near_duplicate"
                    break
                    
            # Check against internal candidate dhashes
            for int_rel_path, int_dh in candidate_dhashes:
                dist = hamming_distance(c_dh, int_dh)
                if dist <= 4: # Very close candidate-to-candidate near duplicate
                    is_suspicious = True
                    matched_file = int_rel_path
                    sim_score = round(1.0 - (dist / 64.0), 4)
                    reasons.append(f"Internal near-duplicate of another candidate (dHash distance {dist}/64)")
                    internal_duplicates_count += 1
                    recommended_action = "exclude_internal_near_duplicate"
                    break
                    
            candidate_dhashes.append((c_rel_path, c_dh))
            
        category = cpath.parent.name
        record = {
            "filename": c_rel_path,
            "category": category,
            "width": width,
            "height": height,
            "md5_hash": c_md5,
            "is_suspicious": is_suspicious,
            "audit_status": "SUSPICIOUS" if is_suspicious else "SAFE",
            "reasons": "; ".join(reasons) if reasons else "None - Completely Independent",
            "matched_existing_file": matched_file if matched_file else "None",
            "similarity_score": sim_score if sim_score is not None else 0.0,
            "recommended_action": recommended_action
        }
        candidate_records.append(record)
        
        if is_suspicious:
            suspicious_files.append({
                "filename": c_rel_path,
                "reason": "; ".join(reasons),
                "matched_existing_file": matched_file if matched_file else "None",
                "similarity_score": sim_score if sim_score is not None else 0.0,
                "recommended_action": recommended_action
            })
            
    total_candidates = len(candidate_records)
    safe_candidates = total_candidates - len(suspicious_files)
    excluded_candidates = len(suspicious_files)
    
    verdict = "PASS" if excluded_candidates == 0 else "FAIL"
    verdict_message = (
        "PASS: No meaningful overlap with the existing dataset. Candidate set is completely independent and leak-free."
        if verdict == "PASS"
        else f"FAIL: {excluded_candidates} candidate(s) overlap or collide with existing dataset or internal candidates."
    )
    
    audit_summary = {
        "verdict": verdict,
        "verdict_message": verdict_message,
        "total_candidates": total_candidates,
        "exact_duplicates": exact_duplicates_count,
        "near_duplicates": near_duplicates_count,
        "train_overlaps": train_overlaps_count,
        "validation_overlaps": val_overlaps_count,
        "test_overlaps": test_overlaps_count,
        "candidate_internal_duplicates": internal_duplicates_count,
        "suspicious_files_count": len(suspicious_files),
        "safe_candidates": safe_candidates,
        "excluded_candidates": excluded_candidates,
        "suspicious_files": suspicious_files
    }
    
    output_json = {
        "audit_summary": audit_summary,
        "candidate_audits": candidate_records
    }
    
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2)
    print(f"Saved JSON leakage audit to {JSON_OUT}")
    
    # Save CSV
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
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidate_records)
    print(f"Saved CSV leakage audit to {CSV_OUT}")
    
    print("\n" + "=" * 65)
    print("         LEAF CURL CANDIDATE LEAKAGE AUDIT SUMMARY         ")
    print("=" * 65)
    print(f"VERDICT                         : {verdict}")
    print(f"Total Candidates Audited       : {total_candidates}")
    print(f"Safe Independent Candidates    : {safe_candidates}")
    print(f"Suspicious / Overlapping       : {excluded_candidates}")
    print("-" * 65)
    print(f"Exact Duplicates                : {exact_duplicates_count}")
    print(f"Near Duplicates (Perceptual)    : {near_duplicates_count}")
    print(f"Train Split Overlaps            : {train_overlaps_count}")
    print(f"Validation Split Overlaps       : {val_overlaps_count}")
    print(f"Test Split Overlaps             : {test_overlaps_count}")
    print(f"Internal Duplicate Candidates   : {internal_duplicates_count}")
    print("=" * 65)

if __name__ == "__main__":
    main()
