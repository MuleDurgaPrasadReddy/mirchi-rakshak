from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "src" / "data"
EXPECTED_SPLITS = ("train", "valid", "test")
SUPPORTED = {".jpg", ".jpeg", ".png"}

with (Path(__file__).parent / "class_mapping.json").open(encoding="utf-8") as file:
    mapping = json.load(file)["classes"]

errors = []
for split in EXPECTED_SPLITS:
    split_path = DATASET / split
    if not split_path.is_dir():
        errors.append(f"Missing split: {split_path}")
        continue
    classes = sorted(path.name for path in split_path.iterdir() if path.is_dir())
    missing_mapping = sorted(set(classes) - set(mapping))
    if missing_mapping:
        errors.append(f"Unmapped classes in {split}: {missing_mapping}")
    for class_name in classes:
        count = sum(1 for path in (split_path / class_name).iterdir() if path.suffix.lower() in SUPPORTED)
        if count == 0:
            errors.append(f"Empty class: {split}/{class_name}")
        print(f"{split:5} {class_name:35} {count:5} images")

if errors:
    raise SystemExit("\n".join(errors))
print("Dataset validation passed.")
