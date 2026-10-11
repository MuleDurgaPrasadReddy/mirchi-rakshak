import os
import json
import csv
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_DIR = ROOT / "mirchi_new_data" / "Leaf_Curl_Virus"

JSON_OUT = CANDIDATE_DIR / "quality_audit.json"
CSV_OUT = CANDIDATE_DIR / "quality_audit.csv"
SUMMARY_JSON_OUT = CANDIDATE_DIR / "quality_summary.json"

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

def main():
    print("==================================================")
    print("  LEAF CURL CANDIDATE QUALITY & SEMANTIC AUDIT    ")
    print("==================================================")
    
    candidate_files = sorted(list(CANDIDATE_DIR.glob("**/*")))
    candidate_files = [f for f in candidate_files if f.suffix.lower() in [".jpg", ".jpeg", ".png"]]
    
    print(f"Auditing {len(candidate_files)} candidate images...")
    
    audits = []
    
    # Counter metrics for summary
    cnt_excellent = 0
    cnt_good = 0
    cnt_questionable = 0
    cnt_reject = 0
    
    cnt_clear_structural_curling = 0
    cnt_green_strong_curling = 0
    cnt_mild_yellow_strong_curling = 0
    cnt_mod_yellow_strong_curling = 0
    cnt_severe_yellow_curling = 0
    
    cnt_severe_curling = 0
    cnt_early_stage = 0
    cnt_vector_confounded = 0
    cnt_excessive_bg = 0
    cnt_low_quality = 0
    cnt_ambiguous = 0
    cnt_recommended_for_training = 0
    
    category_utility = {
        "structural_curling_green": 0,
        "structural_curling_mild_yellow": 0,
        "severe_curling": 0,
        "early_stage_leaf_curl": 0,
        "leaf_curl_with_whitefly": 0,
        "field_diverse_leaf_curl": 0
    }
    
    for cpath in candidate_files:
        filename = str(cpath.relative_to(ROOT)).replace("\\", "/")
        category = cpath.parent.name if cpath.parent.name != "Leaf_Curl_Virus" else "uncategorized"
        
        try:
            pil_img = Image.open(cpath).convert("RGB")
            width, height = pil_img.size
            is_corrupted = False
        except Exception:
            width, height = 0, 0
            is_corrupted = True
            
        if is_corrupted or width < 150 or height < 150:
            usefulness = "reject"
            cnt_reject += 1
            cnt_low_quality += 1
            audits.append({
                "filename": filename,
                "category": category,
                "width": width,
                "height": height,
                "image_quality": "low",
                "blur_sharpness": "blurry",
                "leaf_visibility": "low",
                "curl_visibility": "absent",
                "curl_severity": "none",
                "leaf_puckering": "minimal",
                "vein_distortion": "minimal",
                "yellowing_chlorosis": "none",
                "whitefly_vector_marks": "absent",
                "soil_background_percentage": "100.0%",
                "lighting_quality": "poor",
                "ambiguity_yellowish": False,
                "ambiguity_whitefly": False,
                "confidence_leaf_curl": "low",
                "training_usefulness": "reject"
            })
            continue
            
        np_img = np.array(pil_img, dtype=float) / 255.0
        gray_img = pil_img.convert("L")
        np_gray = np.array(gray_img, dtype=float)
        
        laplacian_img = gray_img.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1))
        lap_var = float(np.var(np.array(laplacian_img, dtype=float)))
        
        min_dim = min(width, height)
        if lap_var < 8.0:
            sharpness = "blurry"
            quality = "low"
        elif lap_var < 20.0:
            sharpness = "moderate"
            quality = "medium"
        else:
            sharpness = "sharp"
            quality = "high"
            
        mean_brightness = float(np.mean(np_gray))
        std_brightness = float(np.std(np_gray))
        if mean_brightness < 40 or mean_brightness > 225 or std_brightness < 18:
            lighting = "poor"
        elif mean_brightness < 70 or mean_brightness > 195 or std_brightness < 32:
            lighting = "adequate"
        else:
            lighting = "good"
            
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
        non_foliage_ratio = float(1.0 - np.mean(green_mask | yellow_mask))
        bg_pct = round((soil_ratio + non_foliage_ratio * 0.4) * 100, 1)
        
        # Leaf visibility
        foliage_pct = (green_ratio + yellow_ratio) * 100
        leaf_vis = "high" if foliage_pct > 55 else ("medium" if foliage_pct > 30 else "low")
        
        # Yellowing level classification
        if yellow_ratio > 0.35 or yellow_index > 1.85:
            yellow_level = "severe"
        elif yellow_ratio > 0.22 or yellow_index > 1.70:
            yellow_level = "moderate"
        elif yellow_ratio > 0.10 or yellow_index > 1.55:
            yellow_level = "mild"
        else:
            yellow_level = "none"
            
        # Edge gradient and curling severity
        gx, gy = np.gradient(np_gray)
        grad_mag = np.sqrt(gx**2 + gy**2)
        edge_density = float(np.mean(grad_mag > 12.0))
        grad_var = float(np.var(grad_mag))
        
        if edge_density > 0.08 or grad_var > 95.0:
            curl_severity = "severe"
            curl_vis = "high_visible"
            puckering = "present"
            vein_distortion = "present"
        elif edge_density > 0.045 or grad_var > 55.0:
            curl_severity = "moderate"
            curl_vis = "clearly_visible"
            puckering = "present"
            vein_distortion = "present"
        elif edge_density > 0.025 or grad_var > 35.0:
            curl_severity = "mild"
            curl_vis = "subtle"
            puckering = "minimal"
            vein_distortion = "minimal"
        else:
            curl_severity = "none"
            curl_vis = "absent"
            puckering = "minimal"
            vein_distortion = "minimal"
            
        white_speckles = (sat < 0.18) & (val > 0.78) & (green_mask | yellow_mask)
        whitefly_marks = bool(float(np.mean(white_speckles)) > 0.012)
        
        ambiguity_yellowish = bool(yellow_level in ["moderate", "severe"] and curl_severity in ["none", "mild"])
        ambiguity_whitefly = bool(whitefly_marks)
        
        # Training usefulness evaluation & Quality Rejection Criteria
        if sharpness == "blurry" or bg_pct > 65.0 or (leaf_vis == "low" and curl_severity == "none"):
            usefulness = "reject"
            cnt_reject += 1
            if sharpness == "blurry":
                cnt_low_quality += 1
            if bg_pct > 65.0:
                cnt_excessive_bg += 1
        elif ambiguity_yellowish and curl_severity == "none":
            usefulness = "questionable"
            cnt_questionable += 1
            cnt_ambiguous += 1
        elif curl_severity in ["moderate", "severe"] and yellow_level in ["none", "mild"]:
            usefulness = "excellent"  # HIGH-VALUE for breaking color shortcut
            cnt_excellent += 1
            cnt_recommended_for_training += 1
            if category in category_utility:
                category_utility[category] += 2
        elif curl_severity in ["moderate", "severe"]:
            usefulness = "good"
            cnt_good += 1
            cnt_recommended_for_training += 1
            if category in category_utility:
                category_utility[category] += 1
        else:
            usefulness = "good"
            cnt_good += 1
            cnt_recommended_for_training += 1
            
        # Summary tally metrics
        if curl_severity in ["moderate", "severe"]:
            cnt_clear_structural_curling += 1
        if yellow_level == "none" and curl_severity in ["moderate", "severe"]:
            cnt_green_strong_curling += 1
        if yellow_level == "mild" and curl_severity in ["moderate", "severe"]:
            cnt_mild_yellow_strong_curling += 1
        if yellow_level == "moderate" and curl_severity in ["moderate", "severe"]:
            cnt_mod_yellow_strong_curling += 1
        if yellow_level == "severe" and curl_severity != "none":
            cnt_severe_yellow_curling += 1
            
        if curl_severity == "severe":
            cnt_severe_curling += 1
        if category == "early_stage_leaf_curl" or curl_severity == "mild":
            cnt_early_stage += 1
        if whitefly_marks:
            cnt_vector_confounded += 1
            
        confidence_level = "high" if usefulness in ["excellent", "good"] else ("medium" if usefulness == "questionable" else "low")
        
        audits.append({
            "filename": filename,
            "category": category,
            "width": width,
            "height": height,
            "image_quality": quality,
            "blur_sharpness": sharpness,
            "leaf_visibility": leaf_vis,
            "curl_visibility": curl_vis,
            "curl_severity": curl_severity,
            "leaf_puckering": puckering,
            "vein_distortion": vein_distortion,
            "yellowing_chlorosis": yellow_level,
            "whitefly_vector_marks": "present" if whitefly_marks else "absent",
            "soil_background_percentage": f"{bg_pct}%",
            "lighting_quality": lighting,
            "ambiguity_yellowish": ambiguity_yellowish,
            "ambiguity_whitefly": ambiguity_whitefly,
            "confidence_leaf_curl": confidence_level,
            "training_usefulness": usefulness
        })
        
    total_candidates = len(audits)
    
    # Rank categories by usefulness for correcting color-over-morphology shortcut
    ranked_categories = [
        {
            "rank": 1,
            "category": "structural_curling_green",
            "utility_score": category_utility["structural_curling_green"],
            "reason": "Highest value for directly breaking the color shortcut. Provides pure structural 3D curling features on green foliage."
        },
        {
            "rank": 2,
            "category": "structural_curling_mild_yellow",
            "utility_score": category_utility["structural_curling_mild_yellow"],
            "reason": "Teaches the model to recognize structural puckering even in the presence of mild chlorosis."
        },
        {
            "rank": 3,
            "category": "severe_curling",
            "utility_score": category_utility["severe_curling"],
            "reason": "Provides extreme edge distortion and upward leaf rolling features."
        },
        {
            "rank": 4,
            "category": "field_diverse_leaf_curl",
            "utility_score": category_utility["field_diverse_leaf_curl"],
            "reason": "Ensures model generalization across varied field lighting, farm conditions, and chilli varieties."
        },
        {
            "rank": 5,
            "category": "early_stage_leaf_curl",
            "utility_score": category_utility["early_stage_leaf_curl"],
            "reason": "Useful for early disease detection, though margin rolling is subtle."
        },
        {
            "rank": 6,
            "category": "leaf_curl_with_whitefly",
            "utility_score": category_utility["leaf_curl_with_whitefly"],
            "reason": "Secondary vector-confounded examples for multi-symptom robustness."
        }
    ]
    
    output_audit_json = {
        "total_candidates": total_candidates,
        "audited_candidates": audits
    }
    
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(output_audit_json, f, indent=2)
    print(f"Saved quality audit JSON to {JSON_OUT}")
    
    # CSV Export
    fieldnames = [
        "filename",
        "category",
        "width",
        "height",
        "image_quality",
        "blur_sharpness",
        "leaf_visibility",
        "curl_visibility",
        "curl_severity",
        "leaf_puckering",
        "vein_distortion",
        "yellowing_chlorosis",
        "whitefly_vector_marks",
        "soil_background_percentage",
        "lighting_quality",
        "ambiguity_yellowish",
        "ambiguity_whitefly",
        "confidence_leaf_curl",
        "training_usefulness"
    ]
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(audits)
    print(f"Saved quality audit CSV to {CSV_OUT}")
    
    # Summary JSON Export
    summary_data = {
        "total_candidates": total_candidates,
        "excellent": cnt_excellent,
        "good": cnt_good,
        "questionable": cnt_questionable,
        "reject": cnt_reject,
        "clear_structural_curling": cnt_clear_structural_curling,
        "green_and_strong_curling": cnt_green_strong_curling,
        "mild_yellow_and_strong_curling": cnt_mild_yellow_strong_curling,
        "moderate_yellow_and_strong_curling": cnt_mod_yellow_strong_curling,
        "severe_yellow_and_curling": cnt_severe_yellow_curling,
        "severe_curling": cnt_severe_curling,
        "early_stage": cnt_early_stage,
        "whitefly_vector_confounded": cnt_vector_confounded,
        "excessive_background": cnt_excessive_bg,
        "low_quality": cnt_low_quality,
        "ambiguous_leaf_curl": cnt_ambiguous,
        "recommended_candidates_for_training": cnt_recommended_for_training,
        "ranked_candidate_categories": ranked_categories
    }
    
    with open(SUMMARY_JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Saved quality summary JSON to {SUMMARY_JSON_OUT}")
    
    print("\n" + "=" * 65)
    print("      LEAF CURL CANDIDATE QUALITY AUDIT SUMMARY            ")
    print("=" * 65)
    print(f"Total Candidates Audited                : {total_candidates}")
    print(f"  - Excellent Usefulness (High Value)   : {cnt_excellent}")
    print(f"  - Good Usefulness                     : {cnt_good}")
    print(f"  - Questionable                        : {cnt_questionable}")
    print(f"  - Reject                              : {cnt_reject}")
    print("-" * 65)
    print(f"Clear Structural Curling                : {cnt_clear_structural_curling}")
    print(f"Green + Strong Curling                  : {cnt_green_strong_curling}")
    print(f"Mild Yellow + Strong Curling            : {cnt_mild_yellow_strong_curling}")
    print(f"Moderate Yellow + Strong Curling        : {cnt_mod_yellow_strong_curling}")
    print(f"Recommended Candidates for Training     : {cnt_recommended_for_training}")
    print("=" * 65)

if __name__ == "__main__":
    main()
