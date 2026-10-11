import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import json
import random
import shutil
from pathlib import Path
import numpy as np
import tensorflow as tf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Set seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "src" / "data_clean"
OUTPUT_DIR = ROOT / "ml" / "models"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IMG_SIZE = (224, 224)
BATCH_SIZE = 32

print("==========================================================")
print("  MIRCHI RAKSHAK — LEAF CURL EXP01 RETRAINING PIPELINE   ")
print("==========================================================")
print(f"Dataset root: {DATASET}")
print(f"Output dir  : {OUTPUT_DIR}")

# 1. Pre-training Audit Verification
print("\n--- Running Pre-training Dataset Integrity Audit ---")
train_files = list((DATASET / "train").glob("**/*"))
val_files = list((DATASET / "validation").glob("**/*"))
test_files = list((DATASET / "test").glob("**/*"))

train_img_count = len([f for f in train_files if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png"]])
val_img_count = len([f for f in val_files if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png"]])
test_img_count = len([f for f in test_files if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png"]])

leaf_curl_train = len(list((DATASET / "train" / "Chilli__Leaf_Curl_Virus").glob("*")))
leaf_curl_val = len(list((DATASET / "validation" / "Chilli__Leaf_Curl_Virus").glob("*")))
leaf_curl_test = len(list((DATASET / "test" / "Chilli__Leaf_Curl_Virus").glob("*")))

print(f"Total Train Images      : {train_img_count} (Expected: 2295)")
print(f"Total Validation Images : {val_img_count} (Expected: 246)")
print(f"Total Test Images       : {test_img_count} (Expected: 246)")
print(f"Leaf Curl Train Images  : {leaf_curl_train} (Expected: 408)")
print(f"Leaf Curl Val Images    : {leaf_curl_val} (Expected: 8)")
print(f"Leaf Curl Test Images   : {leaf_curl_test} (Expected: 8)")

if train_img_count != 2295 or val_img_count != 246 or test_img_count != 246:
    raise RuntimeError(f"Integrity Audit Error: Unexpected split file count! Train={train_img_count}, Val={val_img_count}, Test={test_img_count}")

if leaf_curl_train != 408 or leaf_curl_val != 8 or leaf_curl_test != 8:
    raise RuntimeError(f"Integrity Audit Error: Unexpected Leaf Curl split count! Train={leaf_curl_train}, Val={leaf_curl_val}, Test={leaf_curl_test}")

print("[+] Pre-training dataset audit PASSED 100%!")

# 2. Load Data Splits
print("\n--- Loading Clean Dataset Splits ---")
train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET / "train",
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=True,
    seed=SEED
)
class_names = train_ds.class_names
num_classes = len(class_names)
print(f"Classes ({num_classes}): {class_names}")

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET / "validation",
    class_names=class_names,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False,
    seed=SEED
)

test_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET / "test",
    class_names=class_names,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False,
    seed=SEED
)

# 3. Compute Class Weights (TRAIN ONLY)
print("\n--- Calculating Class Weights from Train Set ONLY ---")
train_counts = {}
for i, cname in enumerate(class_names):
    cdir = DATASET / "train" / cname
    train_counts[cname] = len(list(cdir.glob("*")))

total_train_samples = sum(train_counts.values())
print(f"Total training samples: {total_train_samples}")

class_weights = {}
for i, cname in enumerate(class_names):
    count = train_counts[cname]
    weight = total_train_samples / (num_classes * count)
    class_weights[i] = weight

print("\nComputed Training Class Weights:")
print("-" * 65)
print(f"{'Class Index':<12} | {'Class Name':<30} | {'Train Count':<12} | {'Weight':<10}")
print("-" * 65)
for i, cname in enumerate(class_names):
    w = class_weights[i]
    cnt = train_counts[cname]
    print(f"[{i:<10}] | {cname:<30} | {cnt:<12} | {w:.4f}")
print("-" * 65)

# Prefetch datasets for performance
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)
test_ds = test_ds.prefetch(buffer_size=AUTOTUNE)

# 4. Build Model Architecture
print("\n--- Building MobileNetV3Large Architecture ---")
inputs = tf.keras.Input(shape=(*IMG_SIZE, 3), name="input_image")

training_augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal"),
    tf.keras.layers.RandomRotation(0.08),
    tf.keras.layers.RandomZoom(0.10),
    tf.keras.layers.RandomTranslation(0.05, 0.05),
    tf.keras.layers.RandomContrast(0.10),
], name="training_augmentation")

x = training_augmentation(inputs)

base_model = tf.keras.applications.MobileNetV3Large(
    input_shape=(*IMG_SIZE, 3),
    include_top=False,
    weights="imagenet",
    include_preprocessing=True
)
base_model.trainable = False

x = base_model(x)
x = tf.keras.layers.GlobalAveragePooling2D(name="global_avg_pool")(x)
x = tf.keras.layers.Dropout(0.30, name="dropout_head")(x)
outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="prediction_head")(x)

model = tf.keras.Model(inputs, outputs, name="mirchi_rakshak_leafcurl_exp01")
model.summary()

# 5. Stage 1 Training (Frozen Backbone)
print("\n==================================================")
print("     STAGE 1: TRAINING CLASSIFICATION HEAD        ")
print("==================================================")
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

stage1_model_path = str(OUTPUT_DIR / "mirchi_rakshak_leafcurl_exp01_stage1.keras")
callbacks_stage1 = [
    tf.keras.callbacks.ModelCheckpoint(
        stage1_model_path,
        monitor="val_loss",
        save_best_only=True,
        verbose=1
    ),
    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=4,
        restore_best_weights=True,
        verbose=1
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.2,
        patience=2,
        min_lr=1e-6,
        verbose=1
    )
]

history_stage1 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=18,
    class_weight=class_weights,
    callbacks=callbacks_stage1,
    verbose=1
)

# 6. Stage 2 Training (Fine-Tuning Last ~40 Layers)
print("\n==================================================")
print("     STAGE 2: FINE-TUNING BACKBONE LAYERS         ")
print("==================================================")
print(f"Loading best Stage 1 checkpoint from: {stage1_model_path}")
model = tf.keras.models.load_model(stage1_model_path)

backbone_layer = None
for layer in model.layers:
    if "mobilenet" in layer.name.lower():
        backbone_layer = layer
        break

if backbone_layer is None:
    raise RuntimeError("Could not find MobileNetV3 backbone in loaded model!")

print(f"Retrieved backbone: {backbone_layer.name} with {len(backbone_layer.layers)} layers")
backbone_layer.trainable = True

num_sub_layers = len(backbone_layer.layers)
unfreeze_from = max(0, num_sub_layers - 40)

for layer in backbone_layer.layers[:unfreeze_from]:
    layer.trainable = False

for layer in backbone_layer.layers[unfreeze_from:]:
    if isinstance(layer, tf.keras.layers.BatchNormalization):
        layer.trainable = False
    else:
        layer.trainable = True

print(f"Backbone layers {unfreeze_from} to {num_sub_layers} unfrozen (BatchNorm frozen).")

total_params = model.count_params()
trainable_params = sum(tf.keras.backend.count_params(w) for w in model.trainable_weights)
non_trainable_params = sum(tf.keras.backend.count_params(w) for w in model.non_trainable_weights)

print("\nParameter counts after unfreezing final 40 layers:")
print(f"  Total parameters       : {total_params:,}")
print(f"  Trainable parameters   : {trainable_params:,}")
print(f"  Non-trainable parameters: {non_trainable_params:,}")

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

stage2_model_path = str(OUTPUT_DIR / "mirchi_rakshak_leafcurl_exp01.keras")
callbacks_stage2 = [
    tf.keras.callbacks.ModelCheckpoint(
        stage2_model_path,
        monitor="val_loss",
        save_best_only=True,
        verbose=1
    ),
    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=3,
        restore_best_weights=True,
        verbose=1
    )
]

history_stage2 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=12,
    class_weight=class_weights,
    callbacks=callbacks_stage2,
    verbose=1
)

# 7. Final Test Evaluation (Evaluated Exactly ONCE)
print("\n==================================================")
print("     FINAL TEST: EVALUATION ON CLEAN TEST SET     ")
print("==================================================")
final_model = tf.keras.models.load_model(stage2_model_path)

y_true = []
y_pred_probs = []

for images, labels in test_ds:
    preds = final_model.predict(images, verbose=0)
    y_true.extend(labels.numpy())
    y_pred_probs.extend(preds)

y_true = np.array(y_true)
y_pred_probs = np.array(y_pred_probs)
y_pred = np.argmax(y_pred_probs, axis=1)

scce = tf.keras.losses.SparseCategoricalCrossentropy()
test_loss = float(scce(y_true, y_pred_probs).numpy())
test_acc = float(np.mean(y_true == y_pred))

cm = np.zeros((num_classes, num_classes), dtype=int)
for t, p in zip(y_true, y_pred):
    cm[t, p] += 1

per_class_metrics = {}
precisions, recalls, f1s, supports = [], [], [], []

for i, cname in enumerate(class_names):
    tp = int(cm[i, i])
    fp = int(np.sum(cm[:, i]) - tp)
    fn = int(np.sum(cm[i, :]) - tp)
    support = int(np.sum(cm[i, :]))
    
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    
    per_class_metrics[cname] = {
        "precision": float(round(prec, 4)),
        "recall": float(round(rec, 4)),
        "f1-score": float(round(f1, 4)),
        "support": support,
        "correct": tp,
        "incorrect": fn
    }
    precisions.append(prec)
    recalls.append(rec)
    f1s.append(f1)
    supports.append(support)

total_support = sum(supports)
macro_prec = float(np.mean(precisions))
macro_rec = float(np.mean(recalls))
macro_f1 = float(np.mean(f1s))

weighted_prec = float(np.sum(np.array(precisions) * np.array(supports)) / total_support)
weighted_rec = float(np.sum(np.array(recalls) * np.array(supports)) / total_support)
weighted_f1 = float(np.sum(np.array(f1s) * np.array(supports)) / total_support)

metrics_data = {
    "experiment": "leafcurl_exp01",
    "checkpoint": "ml/models/mirchi_rakshak_leafcurl_exp01.keras",
    "test_loss": round(test_loss, 4),
    "test_accuracy": round(test_acc, 4),
    "test_accuracy_percentage": round(test_acc * 100, 2),
    "total_test_samples": total_support,
    "macro_precision": round(macro_prec, 4),
    "macro_recall": round(macro_rec, 4),
    "macro_f1": round(macro_f1, 4),
    "weighted_precision": round(weighted_prec, 4),
    "weighted_recall": round(weighted_rec, 4),
    "weighted_f1": round(weighted_f1, 4),
    "correct_predictions": int(np.sum(np.diag(cm))),
    "incorrect_predictions": int(total_support - np.sum(np.diag(cm))),
    "class_names": class_names
}

classification_report_data = {
    "experiment": "leafcurl_exp01",
    "per_class": per_class_metrics,
    "macro_avg": {
        "precision": round(macro_prec, 4),
        "recall": round(macro_rec, 4),
        "f1-score": round(macro_f1, 4)
    },
    "weighted_avg": {
        "precision": round(weighted_prec, 4),
        "recall": round(weighted_rec, 4),
        "f1-score": round(weighted_f1, 4)
    }
}

# Save artifact files separately without overwriting baseline
for target_dir in [OUTPUT_DIR, ROOT, DATASET]:
    (target_dir / "leafcurl_exp01_metrics.json").write_text(json.dumps(metrics_data, indent=2), encoding="utf-8")
    (target_dir / "leafcurl_exp01_classification_report.json").write_text(json.dumps(classification_report_data, indent=2), encoding="utf-8")

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
ax.figure.colorbar(im, ax=ax)
ax.set(
    xticks=np.arange(cm.shape[1]),
    yticks=np.arange(cm.shape[0]),
    xticklabels=class_names,
    yticklabels=class_names,
    ylabel="True Label",
    xlabel="Predicted Label",
    title=f"LeafCurl Exp01 Test Confusion Matrix (Accuracy: {test_acc*100:.2f}%)"
)
plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        ax.text(j, i, format(cm[i, j], "d"),
                ha="center", va="center",
                color="white" if cm[i, j] > cm.max() / 2. else "black")

fig.tight_layout()
for target_dir in [OUTPUT_DIR, ROOT, DATASET]:
    plt.savefig(str(target_dir / "leafcurl_exp01_confusion_matrix.png"), dpi=150)
plt.close()

# 8. Print Comprehensive Summary & Baseline Comparison
print("\n" + "=" * 75)
print("           LEAFCURL EXP01 BENCHMARK EVALUATION RESULTS            ")
print("=" * 75)
print(f"Test Loss            : {test_loss:.4f}")
print(f"Test Accuracy        : {test_acc*100:.2f}% ({metrics_data['correct_predictions']}/{total_support} correct)")
print(f"Macro Precision      : {macro_prec*100:.2f}%")
print(f"Macro Recall         : {macro_rec*100:.2f}%")
print(f"Macro F1 Score       : {macro_f1*100:.2f}%")
print(f"Weighted F1 Score    : {weighted_f1*100:.2f}%")
print("-" * 75)
print(f"{'Class Name':<30} | {'Correct':<8} | {'Total':<6} | {'Prec (%)':<9} | {'Rec (%)':<9} | {'F1 (%)':<8}")
print("-" * 75)
for cname in class_names:
    m = per_class_metrics[cname]
    print(f"{cname:<30} | {m['correct']:<8} | {m['support']:<6} | {m['precision']*100:<9.2f} | {m['recall']*100:<9.2f} | {m['f1-score']*100:<8.2f}")
print("-" * 75)

baseline_acc = 0.8984
baseline_wf1 = 0.8969
print("\n==================================================")
print("          EXPERIMENT VS BASELINE COMPARISON       ")
print("==================================================")
print(f"BASELINE TEST ACCURACY    : {baseline_acc*100:.2f}%")
print(f"LEAFCURL EXP01 ACCURACY   : {test_acc*100:.2f}%")
print(f"Accuracy Delta            : {(test_acc - baseline_acc)*100:+.2f}%")
print("-" * 50)
print(f"BASELINE WEIGHTED F1      : {baseline_wf1*100:.2f}%")
print(f"LEAFCURL EXP01 WEIGHTED F1: {weighted_f1*100:.2f}%")
print(f"Weighted F1 Delta         : {(weighted_f1 - baseline_wf1)*100:+.2f}%")
print("==================================================")

if __name__ == "__main__":
    pass
