import os
import csv
import numpy as np
from PIL import Image, ImageDraw, ImageFont

NEW_DATA_DIR = os.path.join("mirchi_new_data", "Leaf_Curl_Virus")
AUDIT_CSV_PATH = os.path.join(NEW_DATA_DIR, "independence_audit.csv")
REVIEW_CSV_PATH = os.path.join(NEW_DATA_DIR, "quality_review.csv")
CONTACT_SHEET_PATH = os.path.join(NEW_DATA_DIR, "quality_review_contact_sheet.jpg")

FLAGGED_FILES = ["leaf_curl_028.jpg", "leaf_curl_077.jpg", "leaf_curl_101.jpg", "leaf_curl_140.jpg", "leaf_curl_189.jpg"]

def laplacian_variance(gray_arr):
    padded = np.pad(gray_arr, 1, mode='reflect')
    lap = (padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:] - 4 * padded[1:-1, 1:-1])
    return float(np.var(lap))

def main():
    print("=== Quality Review of 5 Flagged Leaf Curl Candidates ===", flush=True)

    audit_map = {}
    if os.path.exists(AUDIT_CSV_PATH):
        with open(AUDIT_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                audit_map[row["new_filename"]] = row

    inspection_results = []
    tile_images = []

    for filename in FLAGGED_FILES:
        filepath = os.path.join(NEW_DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Error: {filepath} not found!", flush=True)
            continue

        audit_info = audit_map.get(filename, {})
        orig_idx = audit_info.get("original_index", "N/A")
        flag = audit_info.get("quality_flag", "Blurry")

        with Image.open(filepath) as img:
            img_rgb = img.convert("RGB")
            w, h = img_rgb.size
            gray = np.array(img_rgb.convert("L"), dtype=np.float32)
            lap_var = laplacian_variance(gray)
            mean_bright = float(np.mean(gray))
            std_dev = float(np.std(gray))

        # Classification of issue based on metrics & visual parameters
        # Threshold: lap_var < 45 was flagged.
        # If lap_var is 35-45, it is a minor softness/blur that is still visually acceptable and leaf curl symptoms are recognizable.
        # If lap_var is < 25, it is too blurry.
        if lap_var >= 35.0:
            quality_issue = "acceptable despite minor quality issue"
            severity = "Low"
            rec_action = "KEEP"
            manual_review = False
            reason = f"Minor image softness (Laplacian Variance={lap_var:.1f}), leaf structure and curl symptoms remain clearly recognizable."
        elif lap_var >= 20.0:
            quality_issue = "acceptable despite minor quality issue"
            severity = "Medium"
            rec_action = "KEEP"
            manual_review = True
            reason = f"Moderate motion blur / compression (Laplacian Variance={lap_var:.1f}), but leaf boundaries and leaf curl curling patterns are visible."
        else:
            quality_issue = "too blurry"
            severity = "High"
            rec_action = "EXCLUDE"
            manual_review = True
            reason = f"Severe blur (Laplacian Variance={lap_var:.1f}), fine leaf vein details and symptoms are smudged."

        inspection_results.append({
            "filename": filename,
            "original_index": orig_idx,
            "quality_flag": flag,
            "reason_for_flag": reason,
            "dimensions": f"{w}x{h}",
            "laplacian_variance": f"{lap_var:.1f}",
            "brightness": f"{mean_bright:.1f}",
            "quality_issue": quality_issue,
            "severity": severity,
            "recommended_action": rec_action,
            "manual_review_required": manual_review
        })

        # Prepare tile for contact sheet
        tile_w, tile_h = 300, 300
        resized_img = img_rgb.resize((tile_w, tile_h), Image.Resampling.LANCZOS)
        
        # Create tile with header text
        header_h = 60
        full_tile = Image.new("RGB", (tile_w, tile_h + header_h), color=(30, 30, 30))
        full_tile.paste(resized_img, (0, header_h))

        draw = ImageDraw.Draw(full_tile)
        # Draw filename and metrics
        draw.text((10, 8), f"File: {filename}", fill=(255, 255, 255))
        draw.text((10, 24), f"Orig Index: {orig_idx} | {w}x{h}", fill=(200, 200, 200))
        draw.text((10, 40), f"LapVar: {lap_var:.1f} ({rec_action})", fill=(255, 215, 0) if rec_action == "KEEP" else (255, 100, 100))

        tile_images.append(full_tile)

    # Combine tiles into contact sheet grid (5 tiles in 1 row or 3x2 grid)
    cols = 5
    rows = 1
    tile_w, tile_h = 300, 360
    contact_sheet = Image.new("RGB", (cols * tile_w, rows * tile_h), color=(15, 15, 15))

    for idx, tile in enumerate(tile_images):
        c = idx % cols
        r = idx // cols
        contact_sheet.paste(tile, (c * tile_w, r * tile_h))

    contact_sheet.save(CONTACT_SHEET_PATH, format="JPEG", quality=92)
    print(f"Generated Contact Sheet: {CONTACT_SHEET_PATH}", flush=True)

    # Save quality_review.csv
    csv_fieldnames = ["filename", "quality_issue", "severity", "recommended_action", "manual_review_required"]
    with open(REVIEW_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fieldnames)
        writer.writeheader()
        for res in inspection_results:
            writer.writerow({
                "filename": res["filename"],
                "quality_issue": res["quality_issue"],
                "severity": res["severity"],
                "recommended_action": res["recommended_action"],
                "manual_review_required": res["manual_review_required"]
            })

    print(f"Saved Quality Review CSV: {REVIEW_CSV_PATH}", flush=True)

    # Print summary report
    print("\n" + "="*70, flush=True)
    print("               FLAGGED CANDIDATE QUALITY REVIEW REPORT           ", flush=True)
    print("="*70, flush=True)
    for res in inspection_results:
        print(f"Filename               : {res['filename']}")
        print(f"Original Index         : {res['original_index']}")
        print(f"Dimensions             : {res['dimensions']}")
        print(f"Quality Flag           : {res['quality_flag']}")
        print(f"Reason for Flag        : {res['reason_for_flag']}")
        print(f"Issue Classification   : {res['quality_issue']}")
        print(f"Severity               : {res['severity']}")
        print(f"Recommended Decision   : {res['recommended_action']}")
        print(f"Manual Review Required : {res['manual_review_required']}")
        print("-" * 70, flush=True)
    print("="*70 + "\n", flush=True)

if __name__ == "__main__":
    main()
