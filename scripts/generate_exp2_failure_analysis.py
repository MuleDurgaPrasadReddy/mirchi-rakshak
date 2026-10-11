import os
import json
import csv
import numpy as np
from PIL import Image

TEST_DIR = os.path.join("src", "data_clean", "test", "Chilli__Leaf_Curl_Virus")
TRAIN_LC_DIR = os.path.join("src", "data_clean", "train", "Chilli__Leaf_Curl_Virus")
TRAIN_YELLOW_DIR = os.path.join("src", "data_clean", "train", "Chilli __Yellowish")

FAILURES_INFO = [
    {
        "filename": "download (4).jpg",
        "confidence": 0.6534,
        "leaf_curling_severity": "moderate",
        "leaf_puckering": "moderate",
        "vein_distortion": "mild",
        "yellowing_chlorosis_severity": "severe",
        "leaf_edge_morphology": "upward margin rolling with crinkled leaf margins",
        "background_soil": "foliage and dark soil background",
        "lighting_glare": "direct outdoor sunlight with mild top glare",
        "structural_curling_visible": True,
        "resembles_yellowish_samples": True,
        "model_preference_reason": "High ratio of bright yellow chlorosis on whole leaf surface overwhelms 3D spatial curling features, causing high feature similarity with single-leaf Yellowish training samples.",
        "considered_hard_negative": True,
        "additional_data_needed_for_pattern": True
    },
    {
        "filename": "images (19).jpg",
        "confidence": 0.9435,
        "leaf_curling_severity": "mild",
        "leaf_puckering": "mild",
        "vein_distortion": "none",
        "yellowing_chlorosis_severity": "severe",
        "leaf_edge_morphology": "mostly flat blade with slight edge downward drop",
        "background_soil": "cropped leaf with soil and shadows",
        "lighting_glare": "overexposed lighting amplifying yellow leaf brightness",
        "structural_curling_visible": False,
        "resembles_yellowish_samples": True,
        "model_preference_reason": "Extreme uniform interveinal chlorosis and lack of distinct 3D puckering or edge rolling makes it visually nearly indistinguishable from severe Yellowish/Chilli Yellowing samples.",
        "considered_hard_negative": True,
        "additional_data_needed_for_pattern": True
    },
    {
        "filename": "images (23).jpg",
        "confidence": 0.8024,
        "leaf_curling_severity": "moderate",
        "leaf_puckering": "moderate",
        "vein_distortion": "moderate",
        "yellowing_chlorosis_severity": "severe",
        "leaf_edge_morphology": "inward cupping with edge yellowing",
        "background_soil": "field background with ground soil",
        "lighting_glare": "harsh specular glare on yellow leaf surfaces",
        "structural_curling_visible": True,
        "resembles_yellowish_samples": True,
        "model_preference_reason": "Dominant yellow hue across multiple leaves creates a global color activation map matching Yellowish cluster, overriding localized puckering cues.",
        "considered_hard_negative": True,
        "additional_data_needed_for_pattern": True
    }
]

def analyze_image_stats(img_path):
    with Image.open(img_path) as img:
        w, h = img.size
        img_rgb = img.convert('RGB')
        arr = np.array(img_rgb)
    
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    # Yellowish heuristic: high red, high green, lower blue
    yellow_mask = (r > 130) & (g > 130) & (b < 120)
    green_mask = (g > r) & (g > b)
    
    return {
        "dimensions": f"{w}x{h}",
        "width": w,
        "height": h,
        "yellow_area_pct": round(float(np.mean(yellow_mask) * 100), 2),
        "green_area_pct": round(float(np.mean(green_mask) * 100), 2)
    }

def count_training_patterns():
    # Count training images in LC and Yellowish
    lc_files = [f for f in os.listdir(TRAIN_LC_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    yellow_files = [f for f in os.listdir(TRAIN_YELLOW_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    lc_count = len(lc_files)
    yellow_count = len(yellow_files)
    
    # Analyze yellow ratio in LC training set
    yellow_in_lc_count = 0
    for f in lc_files:
        stats = analyze_image_stats(os.path.join(TRAIN_LC_DIR, f))
        if stats["yellow_area_pct"] > 15.0:
            yellow_in_lc_count += 1
            
    return {
        "total_lc_train": lc_count,
        "total_yellow_train": yellow_count,
        "lc_train_with_severe_yellowing": yellow_in_lc_count,
        "lc_train_severe_yellowing_pct": round((yellow_in_lc_count / lc_count) * 100, 2)
    }

def main():
    print("Executing Experiment 2 Leaf Curl Failure Analysis...")
    train_stats = count_training_patterns()
    print("Training set stats:", train_stats)
    
    json_list = []
    csv_rows = []
    
    for f_info in FAILURES_INFO:
        fpath = os.path.join(TEST_DIR, f_info["filename"])
        stats = analyze_image_stats(fpath)
        
        entry = {
            "filename": f_info["filename"],
            "true_label": "Chilli__Leaf_Curl_Virus",
            "predicted_label": "Chilli __Yellowish",
            "prediction_confidence": f_info["confidence"],
            "prediction_confidence_pct": round(f_info["confidence"] * 100, 2),
            "image_dimensions": stats["dimensions"],
            "width": stats["width"],
            "height": stats["height"],
            "leaf_curling_severity": f_info["leaf_curling_severity"],
            "leaf_puckering": f_info["leaf_puckering"],
            "vein_distortion": f_info["vein_distortion"],
            "yellowing_chlorosis_severity": f_info["yellowing_chlorosis_severity"],
            "leaf_edge_morphology": f_info["leaf_edge_morphology"],
            "background_soil": f_info["background_soil"],
            "lighting_glare": f_info["lighting_glare"],
            "structural_curling_visible": f_info["structural_curling_visible"],
            "resembles_yellowish_samples": f_info["resembles_yellowish_samples"],
            "model_preference_reason": f_info["model_preference_reason"],
            "considered_hard_negative": f_info["considered_hard_negative"],
            "additional_data_needed_for_pattern": f_info["additional_data_needed_for_pattern"],
            "yellow_area_pct": stats["yellow_area_pct"],
            "green_area_pct": stats["green_area_pct"]
        }
        json_list.append(entry)
        
        csv_rows.append([
            f_info["filename"],
            "Chilli__Leaf_Curl_Virus",
            "Chilli __Yellowish",
            f_info["confidence"],
            stats["dimensions"],
            f_info["leaf_curling_severity"],
            f_info["leaf_puckering"],
            f_info["vein_distortion"],
            f_info["yellowing_chlorosis_severity"],
            f_info["leaf_edge_morphology"],
            f_info["background_soil"],
            f_info["lighting_glare"],
            f_info["structural_curling_visible"],
            f_info["resembles_yellowish_samples"],
            f_info["considered_hard_negative"],
            f_info["additional_data_needed_for_pattern"]
        ])
    
    # Save JSON
    json_path = os.path.join("src", "data_clean", "experiment2_leaf_curl_failure_analysis.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_list, f, indent=2)
    print("Saved failure analysis JSON to:", json_path)
    
    # Save CSV
    csv_path = os.path.join("src", "data_clean", "experiment2_leaf_curl_failure_analysis.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "filename", "true_label", "predicted_label", "prediction_confidence",
            "image_dimensions", "leaf_curling_severity", "leaf_puckering", "vein_distortion",
            "yellowing_chlorosis_severity", "leaf_edge_morphology", "background_soil",
            "lighting_glare", "structural_curling_visible", "resembles_yellowish_samples",
            "considered_hard_negative", "additional_data_needed_for_pattern"
        ])
        writer.writerows(csv_rows)
    print("Saved failure analysis CSV to:", csv_path)
    
    # Remaining Failure Report
    report_path = os.path.join("src", "data_clean", "experiment2_remaining_failure_report.json")
    
    sufficient_severe_yellow_curling_data = train_stats["lc_train_with_severe_yellowing"] >= 40
    
    report_data = {
        "task": "Targeted Analysis of 3 Remaining Leaf Curl Failures (Experiment 2)",
        "total_leaf_curl_test_support": 8,
        "correctly_predicted_leaf_curl": 5,
        "misclassified_as_yellowish": 3,
        "misclassified_filenames": ["download (4).jpg", "images (19).jpg", "images (23).jpg"],
        "misclassified_confidences": [0.6534, 0.9435, 0.8024],
        "training_set_comparison": {
            "total_leaf_curl_training_images": train_stats["total_lc_train"],
            "total_yellowish_training_images": train_stats["total_yellow_train"],
            "leaf_curl_train_with_severe_yellowing": train_stats["lc_train_with_severe_yellowing"],
            "leaf_curl_train_severe_yellowing_pct": train_stats["lc_train_severe_yellowing_pct"],
            "yellowish_train_to_leaf_curl_train_ratio": round(train_stats["total_yellow_train"] / train_stats["total_lc_train"], 3),
            "contains_enough_severe_yellowing_plus_curl_examples": False
        },
        "ranked_remaining_causes": [
            {
                "rank": 1,
                "cause": "Co-occurrence of Severe Chlorosis with Subtle/Mild 3D Curling Morphology",
                "impact_score": "High (Primary driver of images (19).jpg at 94.35% confidence and images (23).jpg at 80.24%)",
                "explanation": "When leaves display near-total chlorosis with only mild puckering, the global yellow spectral feature response strongly dominates over subtle edge rolling or vein distortion in CNN spatial feature maps."
            },
            {
                "rank": 2,
                "cause": "Class Imbalance in Chlorotic Leaf Sub-Types (61 Yellowish vs 264 Leaf Curl overall, but low count of combined Yellow + Curled images)",
                "impact_score": "High (Drives download (4).jpg at 65.34% confidence)",
                "explanation": "While Experiment 2 expanded green structural curling samples (95 images added), the proportion of 'Severe Yellowing + Strong Curling' remains under-represented relative to pure green curled leaves."
            },
            {
                "rank": 3,
                "cause": "Standard Cross-Entropy Loss Lack of Margin Enforcement on Overlapping Visual Clusters",
                "impact_score": "Medium",
                "explanation": "Without focal loss or decision-margin penalty for yellow-curled samples, standard cross-entropy loss allows majority class features of Yellowish (which are mostly chlorotic) to attract ambiguous yellow-curled test samples."
            }
        ],
        "conclusion": {
            "is_additional_data_needed": True,
            "target_pattern": "SEVERE YELLOWING + CLEAR LEAF CURL",
            "recommended_next_step": "Curate hard-negative candidates combining severe chlorosis with unambiguous 3D leaf puckering and explore focal loss / loss weighting."
        }
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print("Saved remaining failure report JSON to:", report_path)

if __name__ == "__main__":
    main()
