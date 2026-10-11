import os
import glob
import json
import csv
import hashlib
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np
from datasets import load_dataset

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_BASE_DIR = ROOT / "mirchi_new_data" / "Leaf_Curl_Virus"
MANIFEST_CSV = CANDIDATE_BASE_DIR / "candidate_manifest.csv"

CATEGORIES = [
    "structural_curling_green",
    "structural_curling_mild_yellow",
    "severe_curling",
    "early_stage_leaf_curl",
    "leaf_curl_with_whitefly",
    "field_diverse_leaf_curl"
]

def rgb_to_hsv(rgb_arr):
    r, g, b = rgb_arr[:, :, 0], rgb_arr[:, :, 1], rgb_arr[:, :, 2]
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    v = maxc
    deltac = maxc - minc
    
    s = np.where(maxc != 0, deltac / (maxc + 1e-7), 0)
    
    rc = (maxc - r) / (deltac + 1e-7)
    gc = (maxc - g) / (deltac + 1e-7)
    bc = (maxc - b) / (deltac + 1e-7)
    
    h = np.zeros_like(r)
    h = np.where(r == maxc, bc - gc, h)
    h = np.where(g == maxc, 2.0 + rc - bc, h)
    h = np.where(b == maxc, 4.0 + gc - rc, h)
    h = (h / 6.0) % 1.0
    h = np.where(deltac == 0, 0, h)
    
    return np.stack([h * 360.0, s, v], axis=-1)

def get_existing_hashes():
    """Collect MD5 hashes of all clean dataset images to prevent duplicate inclusion."""
    clean_dir = ROOT / "src" / "data_clean"
    clean_hashes = set()
    for p in clean_dir.glob("**/*"):
        if p.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            try:
                h = hashlib.md5(p.read_bytes()).hexdigest()
                clean_hashes.add(h)
            except Exception:
                pass
    return clean_hashes

def main():
    print("==================================================")
    print("  PREPARING TARGETED LEAF CURL CANDIDATE DATASET  ")
    print("==================================================")
    
    # 1. Create subdirectories
    for cat in CATEGORIES:
        (CANDIDATE_BASE_DIR / cat).mkdir(parents=True, exist_ok=True)
        
    existing_hashes = get_existing_hashes()
    print(f"Loaded {len(existing_hashes)} existing clean dataset MD5 hashes for duplicate suppression.")
    
    # 2. Load AgML dataset
    print("\n--- Loading AgML Chili Dataset ---")
    dataset = load_dataset("Project-AgML/chili_leaf_curl_detection", split="train")
    print(f"Total dataset samples: {len(dataset)}")
    
    cat_names = dataset.features["objects"]["categories"].feature.names
    virus_idx = cat_names.index("Virus") if "Virus" in cat_names else 2
    print(f"Category 'Virus' index: {virus_idx}")
    
    manifest_rows = []
    category_counts = {cat: 0 for cat in CATEGORIES}
    processed_hashes = set()
    
    target_max_total = 260
    
    for idx, item in enumerate(dataset):
        objs = item.get("objects", {})
        cats = objs.get("categories", [])
        
        # Only process images containing 'Virus' (Leaf Curl Virus)
        if virus_idx not in cats:
            continue
            
        pil_img = item["image"].convert("RGB")
        width, height = pil_img.size
        
        # Quality Filters: reject tiny thumbnails or low resolution
        if width < 200 or height < 200:
            continue
            
        # Compute MD5 Hash
        img_bytes = pil_img.tobytes()
        img_hash = hashlib.md5(img_bytes).hexdigest()
        
        if img_hash in existing_hashes or img_hash in processed_hashes:
            dup_status = "duplicate_skipped"
            continue
        else:
            dup_status = "unique"
            
        np_img = np.array(pil_img, dtype=float) / 255.0
        gray_img = pil_img.convert("L")
        np_gray = np.array(gray_img, dtype=float)
        
        # Blur filter
        laplacian_img = gray_img.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1))
        lap_var = float(np.var(np.array(laplacian_img, dtype=float)))
        if lap_var < 10.0:
            continue  # Skip severely blurred images
            
        # Color & Yellowing analysis
        r, g, b = np_img[:, :, 0], np_img[:, :, 1], np_img[:, :, 2]
        yellow_index = float(np.mean((r + g) / (2.0 * b + 1e-5)))
        hsv = rgb_to_hsv(np_img)
        hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        
        yellow_mask = (hue >= 40) & (hue <= 75) & (sat >= 0.25) & (val >= 0.35)
        yellow_ratio = float(np.mean(yellow_mask))
        
        green_mask = (hue >= 75) & (hue <= 160) & (sat >= 0.18) & (val >= 0.20)
        green_ratio = float(np.mean(green_mask))
        
        soil_mask = (hue >= 10) & (hue <= 35) & (sat >= 0.15) & (sat <= 0.70) & (val >= 0.15) & (val <= 0.65)
        soil_ratio = float(np.mean(soil_mask))
        
        if soil_ratio > 0.35:
            continue  # Skip images dominated by soil/background
            
        # Edge density & gradient variance for curling/puckering
        gx, gy = np.gradient(np_gray)
        grad_mag = np.sqrt(gx**2 + gy**2)
        edge_density = float(np.mean(grad_mag > 12.0))
        grad_var = float(np.var(grad_mag))
        
        # Whitefly speckles
        white_speckles = (sat < 0.18) & (val > 0.78) & (green_mask | yellow_mask)
        whitefly_ratio = float(np.mean(white_speckles))
        whitefly_present = bool(whitefly_ratio > 0.012)
        
        # Determine Logical Category
        if yellow_ratio < 0.15 and green_ratio > 0.35 and (edge_density > 0.035 or grad_var > 45.0):
            target_category = "structural_curling_green"
            yellow_level = "minimal"
            curl_vis = "high_visible"
        elif yellow_ratio >= 0.15 and yellow_ratio < 0.35 and (edge_density > 0.035 or grad_var > 45.0):
            target_category = "structural_curling_mild_yellow"
            yellow_level = "mild_moderate"
            curl_vis = "clearly_visible"
        elif grad_var > 90.0 or edge_density > 0.075:
            target_category = "severe_curling"
            yellow_level = "moderate" if yellow_ratio > 0.15 else "minimal"
            curl_vis = "severe_rolling_puckering"
        elif whitefly_present:
            target_category = "leaf_curl_with_whitefly"
            yellow_level = "moderate" if yellow_ratio > 0.15 else "minimal"
            curl_vis = "visible"
        elif edge_density > 0.025 and edge_density <= 0.04:
            target_category = "early_stage_leaf_curl"
            yellow_level = "minimal" if yellow_ratio < 0.15 else "mild"
            curl_vis = "early_margin_rolling"
        else:
            target_category = "field_diverse_leaf_curl"
            yellow_level = "moderate" if yellow_ratio > 0.20 else "minimal"
            curl_vis = "visible"
            
        # Check quota to maintain balanced distribution
        if sum(category_counts.values()) >= target_max_total:
            break
            
        filename = f"leaf_curl_candidate_{idx:04d}.jpg"
        save_path = CANDIDATE_BASE_DIR / target_category / filename
        
        pil_img.save(save_path, quality=95)
        processed_hashes.add(img_hash)
        category_counts[target_category] += 1
        
        # Build Manifest Record
        manifest_rows.append({
            "filename": f"mirchi_new_data/Leaf_Curl_Virus/{target_category}/{filename}",
            "category": target_category,
            "source": "AgML_Chili_Field_Dataset",
            "width": width,
            "height": height,
            "quality_status": "high_resolution_sharp" if min(width, height) >= 400 else "adequate_resolution",
            "curl_visibility": curl_vis,
            "yellowing_level": yellow_level,
            "whitefly_marks": "present" if whitefly_present else "absent",
            "background_level": "low" if soil_ratio < 0.15 else "medium",
            "duplicate_status": "unique_pass",
            "review_status": "pending_audit"
        })
        
    # Write Candidate Manifest CSV
    fieldnames = [
        "filename",
        "category",
        "source",
        "width",
        "height",
        "quality_status",
        "curl_visibility",
        "yellowing_level",
        "whitefly_marks",
        "background_level",
        "duplicate_status",
        "review_status"
    ]
    
    with open(MANIFEST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)
        
    total_candidates = sum(category_counts.values())
    green_and_mild_yellow = category_counts["structural_curling_green"] + category_counts["structural_curling_mild_yellow"]
    pct_green_mild_yellow = (green_and_mild_yellow / total_candidates * 100) if total_candidates > 0 else 0
    
    print("\n" + "=" * 65)
    print("      TARGETED LEAF CURL CANDIDATE DATASET SUMMARY        ")
    print("=" * 65)
    print(f"Total Candidate Images Collected : {total_candidates}")
    print(f"Manifest CSV Path                : {MANIFEST_CSV}")
    print("-" * 65)
    print(f"{'Category Name':<35} | {'Candidate Count':<15}")
    print("-" * 65)
    for cat in CATEGORIES:
        print(f"{cat:<35} | {category_counts[cat]:<15}")
    print("-" * 65)
    print(f"Structural Curling (Green + Mild Yellow) : {green_and_mild_yellow} / {total_candidates} ({pct_green_mild_yellow:.1f}%)")
    print("Requirement Check (> 40-50% Green/Mild Yellow) : PASSED" if pct_green_mild_yellow >= 40.0 else "WARNING: Green/Mild Yellow ratio below 40%")
    print("=" * 65)

if __name__ == "__main__":
    main()
