import os
import shutil
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DATASET = ROOT / 'src' / 'data'
TARGET_DATASET = ROOT / 'src' / 'data_stratified'

# Clean target dataset if exists
if TARGET_DATASET.exists():
    shutil.rmtree(TARGET_DATASET)

SUPPORTED = {'.jpg', '.jpeg', '.png'}

# 1. Collect all images grouped by class
class_files = {}
for split in ['train', 'valid', 'test']:
    split_dir = SOURCE_DATASET / split
    if not split_dir.exists():
        continue
    for class_dir in split_dir.iterdir():
        if class_dir.is_dir():
            cname = class_dir.name
            if cname not in class_files:
                class_files[cname] = []
            for file_path in class_dir.iterdir():
                if file_path.suffix.lower() in SUPPORTED:
                    class_files[cname].append(file_path)

distribution = []

# Prepare target dirs
for split in ['train', 'valid', 'test']:
    for cname in class_files:
        (TARGET_DATASET / split / cname).mkdir(parents=True, exist_ok=True)

print(f'Total classes found: {len(class_files)}')

# Use fixed seed for deterministic reproducibility
rng = random.Random(42)

for cname in sorted(class_files.keys()):
    files = list(class_files[cname])
    rng.shuffle(files)
    total_count = len(files)
    
    # 80% train, 10% val, 10% test
    n_train = int(total_count * 0.80)
    n_val = int(total_count * 0.10)
    
    train_files = files[:n_train]
    val_files = files[n_train:n_train + n_val]
    test_files = files[n_train + n_val:]
    
    # Copy files
    for f in train_files:
        shutil.copy2(f, TARGET_DATASET / 'train' / cname / f.name)
    for f in val_files:
        shutil.copy2(f, TARGET_DATASET / 'valid' / cname / f.name)
    for f in test_files:
        shutil.copy2(f, TARGET_DATASET / 'test' / cname / f.name)
        
    train_c = len(train_files)
    val_c = len(val_files)
    test_c = len(test_files)
    
    distribution.append({
        'class_name': cname,
        'train_count': train_c,
        'validation_count': val_c,
        'test_count': test_c,
        'train_percentage': round((train_c / total_count) * 100, 2),
        'validation_percentage': round((val_c / total_count) * 100, 2),
        'test_percentage': round((test_c / total_count) * 100, 2),
        'total_count': total_count
    })

# Save distribution JSON in both dataset dir and ml/models dir
dist_path = TARGET_DATASET / 'dataset_distribution.json'
dist_path.write_text(json.dumps(distribution, indent=2), encoding='utf-8')
(ROOT / 'ml' / 'models' / 'dataset_distribution.json').write_text(json.dumps(distribution, indent=2), encoding='utf-8')

print('\n=== STRATIFIED DATASET DISTRIBUTION ===')
header = f"{'Class Name':<30} | {'Train (80%)':<12} | {'Val (10%)':<10} | {'Test (10%)':<10} | {'Total':<8}"
print(header)
print('-' * len(header))
for row in distribution:
    print(f"{row['class_name']:<30} | {row['train_count']:<12} | {row['validation_count']:<10} | {row['test_count']:<10} | {row['total_count']:<8}")
print('-' * len(header))
