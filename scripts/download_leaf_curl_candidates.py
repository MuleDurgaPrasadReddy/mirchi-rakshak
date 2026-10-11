import os
import random
import csv
from datasets import load_dataset
from PIL import Image

DATASET_NAME = "Project-AgML/chili_leaf_curl_detection"
OUTPUT_DIR = os.path.join("mirchi_new_data", "Leaf_Curl_Virus")
METADATA_PATH = os.path.join(OUTPUT_DIR, "metadata.csv")
SEED = 42
TARGET_COUNT = 200

def run():
    print(f"=== Loading dataset '{DATASET_NAME}' (split='train') ===")
    dataset = load_dataset(DATASET_NAME, split="train")

    num_rows = len(dataset)
    col_names = dataset.column_names
    features = dataset.features

    print("\n--- DATASET STRUCTURE REPORT ---")
    print(f"Total dataset images (rows): {num_rows}")
    print(f"Available columns: {col_names}")
    print(f"Features breakdown: {features}")

    # Inspect nested objects categories
    available_classes = []
    if "objects" in features and "categories" in features["objects"]:
        cat_feature = features["objects"]["categories"]
        if hasattr(cat_feature, "feature") and hasattr(cat_feature.feature, "names"):
            available_classes = list(cat_feature.feature.names)

    print(f"Available category classes in 'objects': {available_classes}")

    # Inspect category distribution across the dataset
    category_counts = {cat_name: 0 for cat_name in available_classes}
    virus_candidate_indices = []

    # Class 2 in ['Healthy', 'Mites', 'Virus'] corresponds to 'Virus' (Leaf Curl Virus)
    virus_class_idx = None
    virus_class_name = None

    for idx, name in enumerate(available_classes):
        if "virus" in name.lower() or "curl" in name.lower():
            virus_class_idx = idx
            virus_class_name = name
            break

    print(f"\nIdentifying Leaf Curl Virus class... Found: '{virus_class_name}' (index: {virus_class_idx})")

    for i, item in enumerate(dataset):
        objs = item.get("objects", {})
        cats = objs.get("categories", [])
        
        # Count category occurrences
        present_cats = set(cats)
        for cat_id in present_cats:
            if 0 <= cat_id < len(available_classes):
                category_counts[available_classes[cat_id]] += 1

        # Filter rows containing 'Virus'
        if virus_class_idx is not None and virus_class_idx in cats:
            virus_candidate_indices.append(i)

    print("\n--- CATEGORY DISTRIBUTION IN DATASET ---")
    for cat_name, count in category_counts.items():
        print(f" - {cat_name}: present in {count} images")

    if virus_class_idx is None or not virus_candidate_indices:
        print("\nSTOPPING: Could not find a reliable 'Leaf Curl Virus' class in dataset categories.")
        print_final_report(
            total_images=num_rows,
            available_classes=available_classes,
            selected_class=None,
            num_selected=0,
            output_dir=OUTPUT_DIR,
            saved_count=0,
            status="STOPPED - No reliable Leaf Curl Virus class identified."
        )
        return

    print(f"\nTotal candidate images containing '{virus_class_name}': {len(virus_candidate_indices)}")

    if len(virus_candidate_indices) < TARGET_COUNT:
        print(f"WARNING: Candidate pool ({len(virus_candidate_indices)}) is smaller than target count ({TARGET_COUNT}).")
        selected_indices = virus_candidate_indices
    else:
        random.seed(SEED)
        selected_indices = random.sample(virus_candidate_indices, TARGET_COUNT)
        selected_indices.sort()

    print(f"Selected {len(selected_indices)} images containing '{virus_class_name}' using seed {SEED}.")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    metadata_rows = []
    saved_files = []

    print(f"Processing and saving images to {OUTPUT_DIR}...")
    for idx_num, orig_idx in enumerate(selected_indices, start=1):
        item = dataset[orig_idx]
        filename = f"leaf_curl_{idx_num:03d}.jpg"
        filepath = os.path.join(OUTPUT_DIR, filename)

        img = item.get("image")
        if img is None:
            print(f"Error: Row {orig_idx} does not contain image data. Skipping.")
            continue

        if not isinstance(img, Image.Image):
            try:
                img = Image.open(img)
            except Exception as e:
                print(f"Error converting image at index {orig_idx}: {e}")
                continue

        if img.mode != "RGB":
            img = img.convert("RGB")

        # Save image as JPG
        img.save(filepath, format="JPEG", quality=95)

        # Verify saved file
        try:
            with Image.open(filepath) as test_img:
                test_img.verify()
            with Image.open(filepath) as test_img:
                assert test_img.mode == "RGB", f"Mode is {test_img.mode}, expected RGB"
        except Exception as ve:
            print(f"Corrupted or invalid image saved at {filepath}: {ve}")
            if os.path.exists(filepath):
                os.remove(filepath)
            continue

        saved_files.append(filepath)

        # Collect metadata
        cats_in_row = [available_classes[c] for c in item.get("objects", {}).get("categories", []) if 0 <= c < len(available_classes)]
        orig_label = f"Virus (Categories in image: {', '.join(cats_in_row)})"
        source_url = f"https://huggingface.co/datasets/{DATASET_NAME}"

        metadata_rows.append({
            "new_filename": filename,
            "source_dataset": DATASET_NAME,
            "original_index": orig_idx,
            "original_label": orig_label,
            "source_url": source_url,
            "collection_seed": SEED
        })

    # Save metadata.csv
    fieldnames = ["new_filename", "source_dataset", "original_index", "original_label", "source_url", "collection_seed"]
    with open(METADATA_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metadata_rows)

    # Verification step
    verified_count = 0
    for file_path in saved_files:
        try:
            with Image.open(file_path) as verify_img:
                if verify_img.mode == "RGB":
                    verified_count += 1
        except Exception:
            pass

    status = "SUCCESS" if verified_count == TARGET_COUNT else f"COMPLETED WITH {verified_count}/{TARGET_COUNT} IMAGES VERIFIED"

    print_final_report(
        total_images=num_rows,
        available_classes=available_classes,
        selected_class=f"{virus_class_name} (index {virus_class_idx})",
        num_selected=len(selected_indices),
        output_dir=OUTPUT_DIR,
        saved_count=verified_count,
        status=status
    )

def print_final_report(total_images, available_classes, selected_class, num_selected, output_dir, saved_count, status):
    print("\n" + "="*50)
    print("           FINAL CANDIDATE COLLECTION REPORT          ")
    print("="*50)
    print(f"Status                           : {status}")
    print(f"Total Dataset Images             : {total_images}")
    print(f"Available Classes / Categories   : {available_classes}")
    print(f"Selected Class                   : {selected_class}")
    print(f"Number Selected                  : {num_selected}")
    print(f"Output Directory                 : {output_dir}")
    print(f"Number of Successfully Saved     : {saved_count}")
    print("="*50 + "\n")

if __name__ == "__main__":
    run()
