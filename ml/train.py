import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import json
from pathlib import Path
import numpy as np
import tensorflow as tf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "src" / "data_stratified"
OUTPUT = ROOT / "ml" / "models"
OUTPUT.mkdir(exist_ok=True, parents=True)

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 123

# 1. Load dataset splits from newly stratified dataset
train_ds_raw = tf.keras.utils.image_dataset_from_directory(
    DATASET / "train",
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=True,
    seed=SEED,
)
class_names = train_ds_raw.class_names
print(f"Detected {len(class_names)} classes: {class_names}")

valid_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET / "valid",
    class_names=class_names,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False,
    seed=SEED,
)

test_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET / "test",
    class_names=class_names,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False,
    seed=SEED,
)

# 2. Compute class weights from TRAINING SET ONLY
train_counts = {}
for class_dir in (DATASET / "train").iterdir():
    if class_dir.is_dir():
        train_counts[class_dir.name] = len(list(class_dir.glob("*")))

total_train_samples = sum(train_counts.values())
num_classes = len(class_names)

class_weights = {}
for i, cname in enumerate(class_names):
    count = train_counts.get(cname, 1)
    class_weights[i] = total_train_samples / (num_classes * count)

print("\nComputed Training Class Weights:")
for i, cname in enumerate(class_names):
    print(f"  [{i}] {cname:<30}: {class_weights[i]:.4f}")

# 3. Data Augmentation (Applied ONLY to training images)
augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal"),
    tf.keras.layers.RandomRotation(0.08),
    tf.keras.layers.RandomZoom(0.10),
    tf.keras.layers.RandomTranslation(0.05, 0.05),
    tf.keras.layers.RandomContrast(0.10),
], name="augmentation")

AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds_raw.map(lambda x, y: (augmentation(x, training=True), y), num_parallel_calls=AUTOTUNE)

train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
valid_ds = valid_ds.prefetch(buffer_size=AUTOTUNE)
test_ds = test_ds.prefetch(buffer_size=AUTOTUNE)

# 4. MobileNetV3Large with built-in preprocessing (no manual /255 scaling)
base_model = tf.keras.applications.MobileNetV3Large(
    input_shape=(*IMG_SIZE, 3),
    include_top=False,
    weights="imagenet",
    include_preprocessing=True
)
base_model.trainable = False

inputs = tf.keras.Input(shape=(*IMG_SIZE, 3))
x = base_model(inputs)
x = tf.keras.layers.GlobalAveragePooling2D()(x)
x = tf.keras.layers.Dropout(0.30)(x)
outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)

model = tf.keras.Model(inputs, outputs)

# 5. Stage 1 Training
print("\n--- STAGE 1: Training Classification Head ---")
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

stage1_model_path = str(OUTPUT / "mirchi_rakshak_stage1_best.keras")
callbacks_stage1 = [
    tf.keras.callbacks.ModelCheckpoint(stage1_model_path, save_best_only=True, monitor="val_loss"),
    tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=4, restore_best_weights=True),
    tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.2, patience=2, min_lr=1e-6)
]

history_stage1 = model.fit(
    train_ds,
    validation_data=valid_ds,
    epochs=15,
    class_weight=class_weights,
    callbacks=callbacks_stage1
)

# 6. Stage 2: Fine-Tuning
print("\n--- STAGE 2: Fine-Tuning Backbone Layers ---")
# Reload best checkpoint from Stage 1
model = tf.keras.models.load_model(stage1_model_path)

# Locate actual MobileNetV3 backbone inside the loaded model object
backbone_layer = None
for layer in model.layers:
    if "mobilenet" in layer.name.lower():
        backbone_layer = layer
        break

if backbone_layer is None:
    backbone_layer = base_model

backbone_layer.trainable = True

# Freeze majority of layers, unfreeze approximately the final 40 layers
num_sub_layers = len(backbone_layer.layers)
unfreeze_from = max(0, num_sub_layers - 40)

for layer in backbone_layer.layers[:unfreeze_from]:
    layer.trainable = False
for layer in backbone_layer.layers[unfreeze_from:]:
    if isinstance(layer, tf.keras.layers.BatchNormalization):
        layer.trainable = False  # keep BN frozen
    else:
        layer.trainable = True

print(f"Backbone total layers: {num_sub_layers} | Unfrozen last {num_sub_layers - unfreeze_from} layers")

total_params = model.count_params()
trainable_params = sum(tf.keras.backend.count_params(w) for w in model.trainable_weights)
non_trainable_params = sum(tf.keras.backend.count_params(w) for w in model.non_trainable_weights)

print(f"Total parameters       : {total_params:,}")
print(f"Trainable parameters   : {trainable_params:,}")
print(f"Non-trainable parameters: {non_trainable_params:,}")

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

finetuned_model_path = str(OUTPUT / "mirchi_rakshak_best_finetuned.keras")
callbacks_stage2 = [
    tf.keras.callbacks.ModelCheckpoint(finetuned_model_path, save_best_only=True, monitor="val_loss"),
    tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True)
]

history_stage2 = model.fit(
    train_ds,
    validation_data=valid_ds,
    epochs=12,
    class_weight=class_weights,
    callbacks=callbacks_stage2
)

# Save final model as main model path for compatibility
final_model = tf.keras.models.load_model(finetuned_model_path)
final_model.save(str(OUTPUT / "mirchi_rakshak_model.keras"))

# 7. Final Test Evaluation & Complete Metrics Computation
print("\n--- STAGE 7: Final Test Set Evaluation ---")
y_true = []
y_pred_probs = []

for images, labels in test_ds:
    preds = final_model.predict(images, verbose=0)
    y_true.extend(labels.numpy())
    y_pred_probs.extend(preds)

y_true = np.array(y_true)
y_pred_probs = np.array(y_pred_probs)
y_pred = np.argmax(y_pred_probs, axis=1)

# Loss & Accuracy
scce = tf.keras.losses.SparseCategoricalCrossentropy()
test_loss = float(scce(y_true, y_pred_probs).numpy())
test_acc = float(np.mean(y_true == y_pred))

# Confusion Matrix
cm = np.zeros((num_classes, num_classes), dtype=int)
for t, p in zip(y_true, y_pred):
    cm[t, p] += 1

# Per-class & Macro / Weighted metrics
per_class_metrics = {}
precisions, recalls, f1s, supports = [], [], [], []

for i, cname in enumerate(class_names):
    tp = cm[i, i]
    fp = np.sum(cm[:, i]) - tp
    fn = np.sum(cm[i, :]) - tp
    support = np.sum(cm[i, :])
    
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    
    per_class_metrics[cname] = {
        "precision": float(round(prec, 4)),
        "recall": float(round(rec, 4)),
        "f1-score": float(round(f1, 4)),
        "support": int(support)
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
    "test_loss": round(test_loss, 4),
    "test_accuracy": round(test_acc, 4),
    "macro_precision": round(macro_prec, 4),
    "macro_recall": round(macro_rec, 4),
    "macro_f1": round(macro_f1, 4),
    "weighted_precision": round(weighted_prec, 4),
    "weighted_recall": round(weighted_rec, 4),
    "weighted_f1": round(weighted_f1, 4),
    "class_names": class_names
}

classification_report_data = {
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

# Save outputs
(OUTPUT / "classes.txt").write_text("\n".join(class_names) + "\n", encoding="utf-8")
(OUTPUT / "metrics.json").write_text(json.dumps(metrics_data, indent=2), encoding="utf-8")
(OUTPUT / "classification_report.json").write_text(json.dumps(classification_report_data, indent=2), encoding="utf-8")

# Plot & save Confusion Matrix PNG
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
    title="Confusion Matrix - Mirchi Rakshak"
)
plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        ax.text(j, i, format(cm[i, j], "d"),
                ha="center", va="center",
                color="white" if cm[i, j] > cm.max() / 2. else "black")

fig.tight_layout()
plt.savefig(str(OUTPUT / "confusion_matrix.png"), dpi=150)
plt.close()

# 8. Model Comparison Output
old_acc = 0.3982
old_loss = 1.5139

print("\n==================================================")
print("             MODEL COMPARISON SUMMARY              ")
print("==================================================")
print(f"OLD Model Test Accuracy: {old_acc*100:.2f}% | Test Loss: {old_loss:.4f}")
print(f"NEW Model Test Accuracy: {test_acc*100:.2f}% | Test Loss: {test_loss:.4f}")
print(f"Accuracy Diff          : {(test_acc - old_acc)*100:+.2f}%")
print(f"Loss Diff              : {test_loss - old_loss:+.4f}")
print(f"Macro Precision        : {macro_prec*100:.2f}%")
print(f"Macro Recall           : {macro_rec*100:.2f}%")
print(f"Macro F1 Score         : {macro_f1*100:.2f}%")
print("==================================================")
