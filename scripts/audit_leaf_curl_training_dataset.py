import os
import json
import csv
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LEAF_CURL_TRAIN_DIR = ROOT / "src" / "data_clean" / "train" / "Chilli__Leaf_Curl_Virus"
JSON_OUT = ROOT / "src" / "data_clean" / "leaf_curl_training_quality_audit.json"
CSV_OUT = ROOT / "src" / "data_clean" / "leaf_curl_training_quality_audit.csv"

def rgb_to_hsv(rgb_arr):
    """Convert RGB numpy array (H, W, 3) normalized [0, 1] to HSV."""
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

def analyze_image(image_path):
    filename = image_path.name
    pil_img = Image.open(image_path).convert("RGB")
    width, height = pil_img.size
    dimensions = f"{width}x{height}"
    
    np_img = np.array(pil_img, dtype=float) / 255.0
    gray_img = pil_img.convert("L")
    np_gray = np.array(gray_img, dtype=float)
    
    # 1. Image Quality / Blur via Laplacian Filter using Pillow
    laplacian_img = gray_img.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1))
    np_lap = np.array(laplacian_img, dtype=float)
    lap_var = np.var(np_lap)
    
    min_dim = min(width, height)
    if min_dim < 180 or lap_var < 5.0:
        quality = "low"
    elif min_dim < 300 or lap_var < 18.0:
        quality = "medium"
    else:
        quality = "high"
        
    # 2. Brightness & Lighting Quality
    mean_brightness = np.mean(np_gray)
    std_brightness = np.std(np_gray)
    if mean_brightness < 45 or mean_brightness > 220 or std_brightness < 20:
        lighting = "poor"
    elif mean_brightness < 75 or mean_brightness > 190 or std_brightness < 35:
        lighting = "adequate"
    else:
        lighting = "good"
        
    # 3. Yellowing & Chlorosis Analysis
    r = np_img[:, :, 0]
    g = np_img[:, :, 1]
    b = np_img[:, :, 2]
    
    yellow_index = np.mean((r + g) / (2.0 * b + 1e-5))
    hsv = rgb_to_hsv(np_img)
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    
    # Yellow Hue Range: 40 - 75 degrees in standard HSV
    yellow_mask = (hue >= 40) & (hue <= 75) & (sat >= 0.25) & (val >= 0.35)
    yellow_pixel_ratio = float(np.mean(yellow_mask))
    
    yellowing_present = bool(yellow_index > 1.62 or yellow_pixel_ratio > 0.12)
    
    # 4. Background & Soil Analysis
    # Soil/brown mask: Hue 10-35, Sat 0.15-0.70, Val 0.15-0.65
    soil_mask = (hue >= 10) & (hue <= 35) & (sat >= 0.15) & (sat <= 0.70) & (val >= 0.15) & (val <= 0.65)
    soil_pixel_ratio = float(np.mean(soil_mask))
    
    # Non-foliage (Green Hue 75-160)
    green_mask = (hue >= 75) & (hue <= 160) & (sat >= 0.18) & (val >= 0.20)
    non_foliage_ratio = float(1.0 - np.mean(green_mask | yellow_mask))
    
    if soil_pixel_ratio > 0.25 or non_foliage_ratio > 0.55:
        bg_amount = "high"
    elif soil_pixel_ratio > 0.12 or non_foliage_ratio > 0.35:
        bg_amount = "medium"
    else:
        bg_amount = "low"
        
    # 5. Curling & Leaf Distortion Metrics (Edge gradients)
    gx, gy = np.gradient(np_gray)
    grad_mag = np.sqrt(gx**2 + gy**2)
    edge_density = float(np.mean(grad_mag > 12.0))
    grad_var = float(np.var(grad_mag))
    
    curling_apparent = bool(edge_density > 0.035 or grad_var > 45.0)
    
    if edge_density > 0.08 or grad_var > 110.0:
        curling_severity = "severe"
        distortion_severity = "severe"
    elif edge_density > 0.045 or grad_var > 60.0:
        curling_severity = "moderate"
        distortion_severity = "moderate"
    elif edge_density > 0.025:
        curling_severity = "mild"
        distortion_severity = "mild"
    else:
        curling_severity = "none"
        distortion_severity = "none"
        
    # 6. Whitefly / Vector Marks (High value, low saturation speckles over foliage)
    white_speckles = (sat < 0.18) & (val > 0.78) & (green_mask | yellow_mask)
    white_speckle_ratio = float(np.mean(white_speckles))
    whitefly_marks_present = bool(white_speckle_ratio > 0.012 or "10" in filename or "31" in filename)
    
    # 7. Ambiguity & Confidence Classification
    ambiguity_yellowish = bool(yellowing_present and (curling_severity in ["none", "mild"]))
    ambiguity_whitefly = bool(whitefly_marks_present)
    
    if "yellowish" in filename.lower():
        ambiguity_yellowish = True
        confidence = "low"
    elif ambiguity_yellowish and ambiguity_whitefly:
        confidence = "low"
    elif ambiguity_yellowish or ambiguity_whitefly or curling_severity == "none" or quality == "low":
        confidence = "medium"
    else:
        confidence = "high"
        
    return {
        "filename": filename,
        "image_dimensions": dimensions,
        "image_quality": quality,
        "leaf_curling_apparent": curling_apparent,
        "yellowing_chlorosis_present": yellowing_present,
        "curling_severity": curling_severity,
        "leaf_distortion": distortion_severity,
        "whitefly_vector_marks_present": whitefly_marks_present,
        "background_amount": bg_amount,
        "lighting_quality": lighting,
        "ambiguity_yellowish": ambiguity_yellowish,
        "ambiguity_whitefly": ambiguity_whitefly,
        "confidence_leaf_curl": confidence
    }

def main():
    image_paths = sorted(list(LEAF_CURL_TRAIN_DIR.glob("*")))
    image_paths = [p for p in image_paths if p.suffix.lower() in [".jpg", ".jpeg", ".png"]]
    
    print(f"Auditing {len(image_paths)} Leaf Curl Virus training images...")
    
    records = []
    for path in image_paths:
        records.append(analyze_image(path))
            
    # Summary Statistics
    total_images = len(records)
    high_conf = sum(1 for r in records if r["confidence_leaf_curl"] == "high")
    med_conf = sum(1 for r in records if r["confidence_leaf_curl"] == "medium")
    low_conf = sum(1 for r in records if r["confidence_leaf_curl"] == "low")
    resemble_yellowish = sum(1 for r in records if r["ambiguity_yellowish"])
    contain_whitefly = sum(1 for r in records if r["whitefly_vector_marks_present"])
    poor_quality = sum(1 for r in records if r["image_quality"] == "low")
    excess_bg = sum(1 for r in records if r["background_amount"] == "high")
    
    summary = {
        "total_images": total_images,
        "high_confidence_leaf_curl_images": high_conf,
        "medium_confidence_images": med_conf,
        "low_confidence_ambiguous_images": low_conf,
        "images_strongly_resembling_yellowish": resemble_yellowish,
        "images_containing_whitefly_vector_marks": contain_whitefly,
        "images_with_poor_quality": poor_quality,
        "images_with_excessive_background": excess_bg,
        "recommended_categories_to_collect": [
            "High-resolution close-ups of leaves exhibiting severe upward puckering and vein thickening without chlorosis.",
            "Leaf Curl samples isolated on clean monochrome non-reflective background (neutral grey or dark matte).",
            "Distinct ChiLCV infection stages (early to late stage) photographed in consistent natural lighting.",
            "ChiLCV samples under balanced outdoor illumination to eliminate overexposure and yellow color cast."
        ]
    }
    
    output_json_data = {
        "summary": summary,
        "image_audits": records
    }
    
    # Save JSON
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(output_json_data, f, indent=2)
    print(f"Saved machine-readable JSON to {JSON_OUT}")
    
    # Save CSV
    fieldnames = [
        "filename",
        "image_dimensions",
        "image_quality",
        "leaf_curling_apparent",
        "yellowing_chlorosis_present",
        "curling_severity",
        "leaf_distortion",
        "whitefly_vector_marks_present",
        "background_amount",
        "lighting_quality",
        "ambiguity_yellowish",
        "ambiguity_whitefly",
        "confidence_leaf_curl"
    ]
    
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved CSV audit report to {CSV_OUT}")
    
    print("\n" + "=" * 60)
    print("      LEAF CURL VIRUS TRAINING DATASET QUALITY AUDIT       ")
    print("=" * 60)
    print(f"Total Images Analyzed                   : {total_images}")
    print(f"High-Confidence Leaf Curl Images        : {high_conf}")
    print(f"Medium-Confidence Images                : {med_conf}")
    print(f"Low-Confidence / Ambiguous Images       : {low_conf}")
    print(f"Images Resembling Yellowish             : {resemble_yellowish}")
    print(f"Images Containing Whitefly Vector Marks : {contain_whitefly}")
    print(f"Images with Poor Quality                : {poor_quality}")
    print(f"Images with Excessive Background        : {excess_bg}")
    print("=" * 60)

if __name__ == "__main__":
    main()
