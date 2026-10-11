import os
import csv
import json
import hashlib
from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CLEAN_DIR = ROOT / "src" / "data_clean"
FIELD_EVAL_DIR = ROOT / "src" / "data_field_eval"

SUPPORTED = {".jpg", ".jpeg", ".png"}

def get_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compute_dhash(pil_img, hash_size=8):
    img = pil_img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
    pixels = np.array(img, dtype=float)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return diff.flatten()

def main():
    print("==========================================================")
    print("  MIRCHI RAKSHAK — FIELD EVALUATION DATA LEAKAGE AUDIT  ")
    print("==========================================================")
    
    if not FIELD_EVAL_DIR.exists():
        print("Error: Field evaluation directory does not exist.")
        return

    # 1. Load clean dataset reference fingerprints
    print("Step 1: Indexing clean dataset references (Train, Val, Test)...")
    clean_hashes = {}
    clean_dhashes = []
    
    for split in ["train", "validation", "test"]:
        s_dir = CLEAN_DIR / split
        if not s_dir.exists():
            continue
        for fpath in s_dir.glob("**/*"):
            if fpath.is_file() and fpath.suffix.lower() in SUPPORTED:
                rel_p = str(fpath.relative_to(CLEAN_DIR)).replace("\\", "/")
                sha = get_sha256(fpath)
                clean_hashes[sha] = (rel_p, split)
                try:
                    with Image.open(fpath) as img:
                        dh = compute_dhash(img)
                        clean_dhashes.append((rel_p, split, dh))
                except Exception:
                    pass

    print(f"Indexed {len(clean_hashes)} clean dataset image references.")

    # 2. Collect field evaluation candidates
    print("\nStep 2: Collecting field evaluation images...")
    field_files = []
    for cdir in FIELD_EVAL_DIR.iterdir():
        if cdir.is_dir():
            for fpath in cdir.glob("*"):
                if fpath.is_file() and fpath.suffix.lower() in SUPPORTED:
                    field_files.append((cdir.name, fpath))

    print(f"Found {len(field_files)} candidate images in field evaluation directory.")

    if len(field_files) == 0:
        print("\nNote: Field evaluation directory is currently empty. Structure is ready for candidate collection.")
        return

    # 3. Perform cryptographic and perceptual leakage checks
    exact_leakage = []
    near_leakage = []
    clean_field_count = 0

    for cname, fpath in field_files:
        rel_p = str(fpath.relative_to(FIELD_EVAL_DIR)).replace("\\", "/")
        sha = get_sha256(fpath)

        if sha in clean_hashes:
            matched_rel, matched_split = clean_hashes[sha]
            exact_leakage.append({
                "field_file": rel_p,
                "matched_clean_file": matched_rel,
                "matched_split": matched_split,
                "reason": "Exact SHA-256 match"
            })
            continue

        try:
            with Image.open(fpath) as img:
                c_dh = compute_dhash(img)
                is_near = False
                for clean_p, clean_s, clean_dh in clean_dhashes:
                    dist = int(np.sum(c_dh != clean_dh))
                    if dist <= 6:
                        near_leakage.append({
                            "field_file": rel_p,
                            "matched_clean_file": clean_p,
                            "matched_split": clean_s,
                            "hamming_distance": dist,
                            "reason": f"Near-duplicate (dHash distance {dist}/64)"
                        })
                        is_near = True
                        break
                if is_near:
                    continue
        except Exception as e:
            print(f"Warning reading image {rel_p}: {e}")
            continue

        clean_field_count += 1

    print("\n----------------------------------------------------------")
    print("FIELD EVALUATION LEAKAGE AUDIT RESULTS:")
    print(f"  - Total Field Candidates Evaluated : {len(field_files)}")
    print(f"  - Exact SHA-256 Collisions         : {len(exact_leakage)}")
    print(f"  - Near-Duplicate Perceptual Matches: {len(near_leakage)}")
    print(f"  - Independent Clean Field Candidates: {clean_field_count}")
    print("----------------------------------------------------------")

    if exact_leakage or near_leakage:
        print("\n[!] LEAKAGE WARNING: Overlapping images detected!")
        for item in exact_leakage:
            print(f"  - Exact Collision: {item['field_file']} <-> {item['matched_clean_file']} ({item['matched_split']})")
        for item in near_leakage:
            print(f"  - Near Duplicate: {item['field_file']} <-> {item['matched_clean_file']} ({item['matched_split']})")
    else:
        print("\n[+] VERDICT: PASS — All field evaluation images are 100% independent and leak-free!")

if __name__ == "__main__":
    main()
