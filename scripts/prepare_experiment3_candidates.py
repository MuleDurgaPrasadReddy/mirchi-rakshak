import os
import json
import csv
import hashlib
import numpy as np
from PIL import Image

NEW_DATA_DIR = os.path.join("mirchi_new_data", "Leaf_Curl_Virus")
EXP3_DIR = os.path.join(NEW_DATA_DIR, "experiment3_severe_yellow_curl")
CLEAN_DATA_DIR = os.path.join("src", "data_clean")

APPROVED_MANIFEST = os.path.join(NEW_DATA_DIR, "approved_training_set", "manifest.csv")
QUALITY_AUDIT_JSON = os.path.join(NEW_DATA_DIR, "quality_audit.json")

os.makedirs(EXP3_DIR, exist_ok=True)

def compute_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def compute_dhash(image, hash_size=8):
    image = image.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(image)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

def dhash_hamming_distance(h1, h2):
    return bin(h1 ^ h2).count('1')

def color_stats(img):
    img_rgb = img.convert('RGB')
    arr = np.array(img_rgb)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    # Yellow mask
    yellow_mask = (r > 120) & (g > 120) & (b < 130) & (abs(r.astype(int) - g.astype(int)) < 45)
    green_mask = (g > r) & (g > b)
    
    yellow_pct = float(np.mean(yellow_mask) * 100)
    green_pct = float(np.mean(green_mask) * 100)
    return yellow_pct, green_pct

def main():
    print("=== Scanning All Existing Leaf Curl Candidate Pools for Exp 3 Severe Yellow Curl ===")
    
    # 1. Gather all existing clean dataset files for audit
    clean_files = []
    for root, _, files in os.walk(CLEAN_DATA_DIR):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                clean_files.append(os.path.join(root, f))
                
    print(f"Total clean dataset images (train/val/test): {len(clean_files)}")
    clean_md5s = {}
    clean_dhashes = {}
    for fpath in clean_files:
        try:
            m = compute_md5(fpath)
            clean_md5s[m] = fpath
            with Image.open(fpath) as img:
                dh = compute_dhash(img)
                clean_dhashes[dh] = fpath
        except Exception:
            pass
            
    print(f"Computed MD5s ({len(clean_md5s)}) and dHashes ({len(clean_dhashes)}) for clean dataset.")

    # 2. Gather candidates from mirchi_new_data/Leaf_Curl_Virus/
    all_candidate_files = []
    for root, dirs, files in os.walk(NEW_DATA_DIR):
        if "approved_training_set" in root or "experiment3_severe_yellow_curl" in root:
            continue
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                all_candidate_files.append(os.path.join(root, f))
                
    print(f"Total available raw candidate image files: {len(all_candidate_files)}")

    # 3. Read existing quality audit metadata if available
    audit_lookup = {}
    if os.path.exists(QUALITY_AUDIT_JSON):
        with open(QUALITY_AUDIT_JSON, "r", encoding="utf-8") as f:
            q_list = json.load(f)
            for item in q_list:
                fname = item.get("filename")
                if fname:
                    audit_lookup[fname] = item

    # 4. Filter candidate pool for severe yellowing + clear curling
    selected_pool = []
    for fpath in all_candidate_files:
        fname = os.path.basename(fpath)
        try:
            with Image.open(fpath) as img:
                w, h = img.size
                dh = compute_dhash(img)
                md5_val = compute_md5(fpath)
                y_pct, g_pct = color_stats(img)
                
            # Check for exact duplicate with clean dataset
            if md5_val in clean_md5s:
                print(f"Skipping exact duplicate of clean dataset: {fname}")
                continue
                
            # Check near duplicate with clean dataset (hamming <= 3)
            is_near_dup = False
            for c_dh in clean_dhashes:
                if dhash_hamming_distance(dh, c_dh) <= 3:
                    is_near_dup = True
                    break
            if is_near_dup:
                print(f"Skipping near-duplicate of clean dataset: {fname}")
                continue

            audit_item = audit_lookup.get(fname, {})
            chlorosis = audit_item.get("yellowing_chlorosis", "")
            curl_sev = audit_item.get("curl_severity", "")
            puckering = audit_item.get("leaf_puckering", "")
            
            # Select images with severe/moderate yellowing AND clear curling
            if chlorosis in ["severe", "moderate"] or y_pct > 8.0:
                if curl_sev in ["severe", "moderate"] or puckering in ["severe", "moderate"] or "yellow" in fpath.lower():
                    if w >= 200 and h >= 200:
                        selected_pool.append({
                            "original_path": fpath,
                            "filename": fname,
                            "width": w,
                            "height": h,
                            "md5": md5_val,
                            "dhash": dh,
                            "yellow_pct": round(y_pct, 2),
                            "green_pct": round(g_pct, 2),
                            "chlorosis": chlorosis if chlorosis else ("severe" if y_pct > 15 else "moderate"),
                            "curl_severity": curl_sev if curl_sev else "severe",
                            "puckering": puckering if puckering else "moderate",
                            "audit_info": audit_item
                        })
        except Exception as e:
            pass
            
    print(f"Filtered pool size for Exp 3 severe yellow curl: {len(selected_pool)}")
    
    with open("scripts/exp3_candidate_pool.json", "w") as f:
        json.dump(selected_pool, f, indent=2)

if __name__ == "__main__":
    main()
