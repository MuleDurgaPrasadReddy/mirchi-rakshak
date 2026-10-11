import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import json
import csv
import random
import shutil
from pathlib import Path
import numpy as np
import tensorflow as tf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Set seeds for exact reproducibility
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

EXP2_METRICS_JSON = DATASET / "experiment2_metrics.json"
EXP2_PER_CLASS_CSV = DATASET / "experiment2_per_class_metrics.csv"
EXP2_CM_CSV = DATASET / "experiment2_confusion_matrix.csv"
EXP2_COMPARISON_JSON = DATASET / "experiment2_comparison.json"

def main():
    print("==================================================")
    print("     MIRCHI RAKSHAK EXPERIMENT-2 PIPELINE        ")
    print("==================================================")
    print(f"Dataset root: {DATASET}")
    print(f"Output dir  : {OUTPUT_DIR}")

    # 1. Load Data Splits
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

    # 2. Compute Class Weights (TRAIN ONLY)
    print("\n--- Calculating Class Weights from Expanded Train Set ONLY ---")
    train_counts = {}
    for i, cname in enumerate(class_names):
        cdir = DATASET / "train" / cname
        train_counts[cname] = len(list(cdir.glob("*")))

    total_train_samples = sum(train_counts.values())
    print(f"Total training samples: {total_train_samples}")

    class_weights = {}
    print("\nComputed Training Class Weights:")
    print("-" * 65)
    print(f"{'Class Index':<12} | {'Class Name':<30} | {'Train Count':<12} | {'Weight':<10}")
    print("-" * 65)
    for i, cname in enumerate(class_names):
        count = train_counts[cname]
        weight = total_train_samples / (num_classes * count)
        class_weights[i] = weight
        print(f"[{i:<10}] | {cname:<30} | {count:<12} | {weight:.4f}")
    print("-" * 65)

    # Prefetch datasets
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)
    test_ds = test_ds.prefetch(buffer_size=AUTOTUNE)

    # 3. Build Model Architecture (MobileNetV3Large)
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

    model = tf.keras.Model(inputs, outputs, name="mirchi_rakshak_exp2_model")
    model.summary()

    # 4. Stage 1 Training (Frozen Backbone)
    print("\n==================================================")
    print("     STAGE 1: TRAINING CLASSIFICATION HEAD        ")
    print("==================================================")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    stage1_model_path = str(OUTPUT_DIR / "mirchi_rakshak_exp2_stage1_best.keras")
    callbacks_stage1 = [
        tf.keras.callbacks.ModelCheckpoint(stage1_model_path, monitor="val_loss", save_best_only=True, verbose=1),
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=4, restore_best_weights=True, verbose=1),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.2, patience=2, min_lr=1e-6, verbose=1)
    ]

    history_stage1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=18,
        class_weight=class_weights,
        callbacks=callbacks_stage1,
        verbose=1
    )

    # 5. Stage 2 Training (Fine-Tuning Last 40 Layers)
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

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    stage2_model_path = str(OUTPUT_DIR / "mirchi_rakshak_exp2_best_finetuned.keras")
    callbacks_stage2 = [
        tf.keras.callbacks.ModelCheckpoint(stage2_model_path, monitor="val_loss", save_best_only=True, verbose=1),
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True, verbose=1)
    ]

    history_stage2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=12,
        class_weight=class_weights,
        callbacks=callbacks_stage2,
        verbose=1
    )

    # 6. Evaluation on UNTOUCHED Test Set
    print("\n==================================================")
    print("     EVALUATION ON UNTOUCHED CLEAN TEST SET       ")
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

    lc_idx = class_names.index("Chilli__Leaf_Curl_Virus")
    yellow_idx = class_names.index("Chilli __Yellowish")
    wf_idx = class_names.index("Chilli __Whitefly")
    damp_idx = class_names.index("Chilli__Damping_Off")

    lc_metrics = per_class_metrics["Chilli__Leaf_Curl_Virus"]
    lc_predicted_yellowish = int(cm[lc_idx, yellow_idx])
    lc_predicted_whitefly = int(cm[lc_idx, wf_idx])
    lc_predicted_damping_off = int(cm[lc_idx, damp_idx])

    # Leaf Curl confidence distribution on test set
    lc_test_indices = np.where(y_true == lc_idx)[0]
    lc_confidences = [float(round(y_pred_probs[idx][y_pred[idx]], 4)) for idx in lc_test_indices]
    lc_correct_confidences = [float(round(y_pred_probs[idx][lc_idx], 4)) for idx in lc_test_indices if y_pred[idx] == lc_idx]

    exp2_metrics_data = {
        "test_loss": round(test_loss, 4),
        "test_accuracy": round(test_acc, 4),
        "test_accuracy_percentage": round(test_acc * 100, 2),
        "macro_precision": round(macro_prec, 4),
        "macro_recall": round(macro_rec, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_precision": round(weighted_prec, 4),
        "weighted_recall": round(weighted_rec, 4),
        "weighted_f1": round(weighted_f1, 4),
        "leaf_curl_metrics": {
            "precision": lc_metrics["precision"],
            "recall": lc_metrics["recall"],
            "f1_score": lc_metrics["f1-score"],
            "support": lc_metrics["support"],
            "correct_count": lc_metrics["correct"],
            "predicted_as_yellowish": lc_predicted_yellowish,
            "predicted_as_whitefly": lc_predicted_whitefly,
            "predicted_as_damping_off": lc_predicted_damping_off,
            "confidence_distribution_all": lc_confidences,
            "confidence_distribution_correct": lc_correct_confidences
        },
        "per_class_metrics": per_class_metrics
    }

    with open(EXP2_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(exp2_metrics_data, f, indent=2)
    print(f"Saved Experiment 2 metrics JSON to {EXP2_METRICS_JSON}")

    # 7. Save Per-Class CSV and Confusion Matrix CSV
    with open(EXP2_PER_CLASS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["class_name", "support", "correct", "precision", "recall", "f1_score"])
        for cname in class_names:
            m = per_class_metrics[cname]
            writer.writerow([cname, m["support"], m["correct"], m["precision"], m["recall"], m["f1-score"]])
    print(f"Saved per-class CSV to {EXP2_PER_CLASS_CSV}")

    with open(EXP2_CM_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["true_class"] + class_names)
        for i, cname in enumerate(class_names):
            writer.writerow([cname] + list(cm[i]))
    print(f"Saved confusion matrix CSV to {EXP2_CM_CSV}")

    # 8. Comparison against Previous Clean Model
    prev_bench = {
        "accuracy": 0.8902,
        "macro_f1": 0.7257,
        "leaf_curl_recall": 0.1250,
        "leaf_curl_precision": 0.2500,
        "leaf_curl_f1": 0.1667,
        "leaf_curl_to_yellowish": 5,
        "leaf_curl_to_whitefly": 1,
        "leaf_curl_to_damping_off": 1,
        "test_loss": 0.3547
    }

    lc_rec_diff = round((lc_metrics["recall"] - prev_bench["leaf_curl_recall"]) * 100, 2)
    lc_f1_diff = round((lc_metrics["f1-score"] - prev_bench["leaf_curl_f1"]) * 100, 2)
    acc_diff = round((test_acc - prev_bench["accuracy"]) * 100, 2)
    macro_f1_diff = round((macro_f1 - prev_bench["macro_f1"]) * 100, 2)

    if lc_metrics["recall"] >= 0.75 and lc_predicted_yellowish <= 1:
        verdict = "A. SUCCESS — Leaf Curl recognition significantly improved."
    elif lc_metrics["recall"] > prev_bench["leaf_curl_recall"]:
        verdict = "B. PARTIAL SUCCESS — Leaf Curl improved but additional work is needed."
    else:
        verdict = "C. FAILURE — Leaf Curl remains severely under-recognized."

    comparison_data = {
        "experiment2_verdict": verdict,
        "primary_success_criteria_check": {
            "1_leaf_curl_recall_improvement": f"{prev_bench['leaf_curl_recall']*100:.2f}% -> {lc_metrics['recall']*100:.2f}% ({lc_rec_diff:+.2f}%)",
            "2_leaf_curl_f1_improvement": f"{prev_bench['leaf_curl_f1']*100:.2f}% -> {lc_metrics['f1-score']*100:.2f}% ({lc_f1_diff:+.2f}%)",
            "3_leaf_curl_to_yellowish_reduction": f"{prev_bench['leaf_curl_to_yellowish']}/8 -> {lc_predicted_yellowish}/8",
            "4_leaf_curl_to_whitefly_reduction": f"{prev_bench['leaf_curl_to_whitefly']}/8 -> {lc_predicted_whitefly}/8",
            "5_overall_macro_f1": f"{prev_bench['macro_f1']*100:.2f}% -> {macro_f1*100:.2f}% ({macro_f1_diff:+.2f}%)",
            "6_overall_accuracy": f"{prev_bench['accuracy']*100:.2f}% -> {test_acc*100:.2f}% ({acc_diff:+.2f}%)"
        },
        "previous_model_benchmark": prev_bench,
        "experiment2_model_benchmark": {
            "accuracy": round(test_acc, 4),
            "macro_f1": round(macro_f1, 4),
            "leaf_curl_recall": lc_metrics["recall"],
            "leaf_curl_precision": lc_metrics["precision"],
            "leaf_curl_f1": lc_metrics["f1-score"],
            "leaf_curl_to_yellowish": lc_predicted_yellowish,
            "leaf_curl_to_whitefly": lc_predicted_whitefly,
            "leaf_curl_to_damping_off": lc_predicted_damping_off,
            "test_loss": round(test_loss, 4)
        }
    }

    with open(EXP2_COMPARISON_JSON, "w", encoding="utf-8") as f:
        json.dump(comparison_data, f, indent=2)
    print(f"Saved comparison JSON to {EXP2_COMPARISON_JSON}")

    # 9. Print Final Comprehensive Summary
    print("\n" + "=" * 75)
    print("       EXPERIMENT 2 BENCHMARK EVALUATION RESULTS                   ")
    print("=" * 75)
    print(f"VERDICT              : {verdict}")
    print(f"Test Loss            : {test_loss:.4f} (Previous: {prev_bench['test_loss']:.4f})")
    print(f"Test Accuracy        : {test_acc*100:.2f}% (Previous: {prev_bench['accuracy']*100:.2f}%)")
    print(f"Macro F1 Score       : {macro_f1*100:.2f}% (Previous: {prev_bench['macro_f1']*100:.2f}%)")
    print(f"Weighted F1 Score    : {weighted_f1*100:.2f}%")
    print("-" * 75)
    print(f"Leaf Curl Recall     : {lc_metrics['recall']*100:.2f}% (Previous: {prev_bench['leaf_curl_recall']*100:.2f}%)")
    print(f"Leaf Curl Precision  : {lc_metrics['precision']*100:.2f}% (Previous: {prev_bench['leaf_curl_precision']*100:.2f}%)")
    print(f"Leaf Curl F1-Score   : {lc_metrics['f1-score']*100:.2f}% (Previous: {prev_bench['leaf_curl_f1']*100:.2f}%)")
    print(f"Leaf Curl -> Yellowish: {lc_predicted_yellowish}/8 (Previous: {prev_bench['leaf_curl_to_yellowish']}/8)")
    print(f"Leaf Curl -> Whitefly : {lc_predicted_whitefly}/8 (Previous: {prev_bench['leaf_curl_to_whitefly']}/8)")
    print("-" * 75)
    print(f"{'Class Name':<30} | {'Correct':<8} | {'Total':<6} | {'Prec (%)':<9} | {'Rec (%)':<9} | {'F1 (%)':<8}")
    print("-" * 75)
    for cname in class_names:
        m = per_class_metrics[cname]
        print(f"{cname:<30} | {m['correct']:<8} | {m['support']:<6} | {m['precision']*100:<9.2f} | {m['recall']*100:<9.2f} | {m['f1-score']*100:<8.2f}")
    print("=" * 75)

if __name__ == "__main__":
    main()
