import os
import sys
import json
import csv
import shutil
import hashlib
import numpy as np

# Use Legacy Keras for compatibility in .venv-ml
os.environ["TF_USE_LEGACY_KERAS"] = "1"
import tensorflow as tf
import tf_keras as keras
from tf_keras.applications import MobileNetV3Large
from tf_keras.layers import Dense, GlobalAveragePooling2D, Dropout, RandomFlip, RandomRotation, RandomZoom, RandomContrast
from tf_keras.models import Sequential, Model
from tf_keras.optimizers import Adam
from tf_keras.callbacks import EarlyStopping, ModelCheckpoint

# Paths
DATA_CLEAN_DIR = os.path.join("src", "data_clean")
TRAIN_DIR = os.path.join(DATA_CLEAN_DIR, "train")
VAL_DIR = os.path.join(DATA_CLEAN_DIR, "validation")
TEST_DIR = os.path.join(DATA_CLEAN_DIR, "test")

EXP3_CANDIDATE_DIR = os.path.join("mirchi_new_data", "Leaf_Curl_Virus", "experiment3_severe_yellow_curl")
EXP3_MANIFEST = os.path.join("mirchi_new_data", "Leaf_Curl_Virus", "experiment3_candidate_manifest.csv")
BACKUP_DIR = os.path.join("src", "data_clean", "train_backup_before_exp3a")
MODEL_OUTPUT_DIR = os.path.join("ml", "models")

# Output files required by prompt
EXP3A_METRICS_JSON = os.path.join(DATA_CLEAN_DIR, "experiment3a_metrics.json")
EXP3A_PER_CLASS_CSV = os.path.join(DATA_CLEAN_DIR, "experiment3a_per_class_metrics.csv")
EXP3A_CM_CSV = os.path.join(DATA_CLEAN_DIR, "experiment3a_confusion_matrix.csv")
EXP3A_COMPARISON_JSON = os.path.join(DATA_CLEAN_DIR, "experiment3a_comparison.json")

# Hyperparameters (identical to Exp 2)
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
STAGE1_EPOCHS = 18
STAGE2_EPOCHS = 18
STAGE1_LR = 1e-3
STAGE2_LR = 1e-5
UNFREEZE_TOP_N_LAYERS = 40

def compute_md5(fpath):
    h = hashlib.md5()
    with open(fpath, "rb") as f:
        for chunk in iter(lambda: f.read(16384), b""):
            h.update(chunk)
    return h.hexdigest()

def verify_and_integrate_exp3_candidates():
    print("==================================================")
    print("  PRE-TRAINING INTEGRATION & DATASET INTEGRITY   ")
    print("==================================================")
    
    # 1. Verify candidate files exist
    if not os.path.exists(EXP3_CANDIDATE_DIR):
        raise FileNotFoundError(f"Candidate directory missing: {EXP3_CANDIDATE_DIR}")
        
    cand_files = [f for f in os.listdir(EXP3_CANDIDATE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"Verified candidate files in folder: {len(cand_files)}")
    if len(cand_files) != 65:
        print(f"WARNING: Expected 65 candidates, found {len(cand_files)}")

    # 2. Check overlap with validation and test sets
    val_test_md5s = set()
    for split_dir in [VAL_DIR, TEST_DIR]:
        for root, _, files in os.walk(split_dir):
            for f in files:
                if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    val_test_md5s.add(compute_md5(os.path.join(root, f)))
                    
    print(f"Indexed {len(val_test_md5s)} validation/test MD5 hashes.")

    train_lc_dir = os.path.join(TRAIN_DIR, "Chilli__Leaf_Curl_Virus")
    existing_train_md5s = set()
    for root, _, files in os.walk(TRAIN_DIR):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                existing_train_md5s.add(compute_md5(os.path.join(root, f)))
                
    print(f"Indexed {len(existing_train_md5s)} existing train dataset MD5 hashes.")

    cand_md5s = set()
    overlap_val_test = 0
    overlap_train = 0

    for cfile in cand_files:
        fp = os.path.join(EXP3_CANDIDATE_DIR, cfile)
        m = compute_md5(fp)
        if m in val_test_md5s:
            overlap_val_test += 1
        if m in existing_train_md5s:
            overlap_train += 1
        cand_md5s.add(m)

    print(f"Candidate vs Val/Test Overlap: {overlap_val_test}")
    print(f"Candidate vs Existing Train Overlap: {overlap_train}")
    if overlap_val_test > 0 or overlap_train > 0:
        raise ValueError("DATASET LEAKAGE DETECTED! Aborting training.")

    # 3. Create dataset backup before merging
    if not os.path.exists(BACKUP_DIR):
        print(f"Creating backup of training Leaf Curl directory: {BACKUP_DIR}")
        shutil.copytree(train_lc_dir, os.path.join(BACKUP_DIR, "Chilli__Leaf_Curl_Virus"))
    else:
        print(f"Backup directory already exists: {BACKUP_DIR}")

    # 4. Copy 65 candidates into training Leaf Curl directory
    integrated_count = 0
    for cfile in cand_files:
        src_path = os.path.join(EXP3_CANDIDATE_DIR, cfile)
        dest_path = os.path.join(train_lc_dir, cfile)
        if not os.path.exists(dest_path):
            shutil.copy2(src_path, dest_path)
            integrated_count += 1

    print(f"Successfully integrated {integrated_count} new candidates into {train_lc_dir}")

    # 5. Verify final training set counts
    total_train_images = 0
    train_counts = {}
    for cname in sorted(os.listdir(TRAIN_DIR)):
        cdir = os.path.join(TRAIN_DIR, cname)
        if os.path.isdir(cdir):
            cnt = len([f for f in os.listdir(cdir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            train_counts[cname] = cnt
            total_train_images += cnt

    print(f"\nFinal Exp 3A Training Counts (Total: {total_train_images}):")
    for cname, cnt in train_counts.items():
        print(f"  - {cname:<30}: {cnt}")

    if train_counts["Chilli__Leaf_Curl_Virus"] != 329:
        print(f"WARNING: Leaf Curl train count is {train_counts['Chilli__Leaf_Curl_Virus']}, expected 329.")
    if total_train_images != 2216:
        print(f"WARNING: Total train count is {total_train_images}, expected 2216.")

    return train_counts, total_train_images

def compute_class_weights(train_counts):
    total_samples = sum(train_counts.values())
    num_classes = len(train_counts)
    class_names = sorted(list(train_counts.keys()))
    
    class_weights = {}
    print("\n--- Calculated Exp 3A Class Weights ---")
    for i, cname in enumerate(class_names):
        count = train_counts[cname]
        weight = total_samples / (num_classes * count)
        class_weights[i] = float(weight)
        print(f"[{i:<2}] {cname:<30}: Count = {count:<4} | Weight = {weight:.4f}")
        
    return class_weights, class_names

def build_model(num_classes):
    data_augmentation = Sequential([
        RandomFlip("horizontal_and_vertical"),
        RandomRotation(0.2),
        RandomZoom(0.2),
        RandomContrast(0.2),
    ], name="training_augmentation")

    inputs = tf.keras.Input(shape=(224, 224, 3), name="input_image")
    x = data_augmentation(inputs)

    backbone = MobileNetV3Large(
        input_shape=(224, 224, 3),
        include_top=False,
        weights="imagenet",
        pooling=None
    )
    backbone.trainable = False

    x = backbone(x, training=False)
    x = GlobalAveragePooling2D(name="global_avg_pool")(x)
    x = Dropout(0.3, name="dropout_head")(x)
    outputs = Dense(num_classes, activation="softmax", name="prediction_head")(x)

    model = Model(inputs=inputs, outputs=outputs, name="mirchi_rakshak_exp3a_model")
    return model, backbone

def main():
    print("==================================================")
    print("     MIRCHI RAKSHAK EXPERIMENT-3A PIPELINE       ")
    print("==================================================")
    
    # 1. Integrate dataset and verify counts
    train_counts, total_train = verify_and_integrate_exp3_candidates()
    class_weights, class_names = compute_class_weights(train_counts)
    num_classes = len(class_names)

    # 2. Load splits using image_dataset_from_directory
    print("\n--- Loading Dataset Splits ---")
    train_ds = tf.keras.utils.image_dataset_from_directory(
        TRAIN_DIR,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=True,
        seed=42
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        VAL_DIR,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    test_ds = tf.keras.utils.image_dataset_from_directory(
        TEST_DIR,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)
    test_ds = test_ds.prefetch(buffer_size=AUTOTUNE)

    # 3. Build Model
    model, backbone = build_model(num_classes)
    model.summary()

    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
    stage1_model_path = os.path.join(MODEL_OUTPUT_DIR, "mirchi_rakshak_exp3a_stage1_best.keras")
    stage2_model_path = os.path.join(MODEL_OUTPUT_DIR, "mirchi_rakshak_exp3a_best_finetuned.keras")

    # 4. Stage 1 Training (Frozen Backbone)
    print("\n==================================================")
    print("     STAGE 1: TRAINING CLASSIFICATION HEAD        ")
    print("==================================================")
    model.compile(
        optimizer=Adam(learning_rate=STAGE1_LR),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    callbacks_stage1 = [
        ModelCheckpoint(stage1_model_path, monitor="val_loss", save_best_only=True, verbose=1),
        EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True, verbose=1)
    ]

    history_stage1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=STAGE1_EPOCHS,
        class_weight=class_weights,
        callbacks=callbacks_stage1,
        verbose=1
    )

    # 5. Stage 2 Fine-Tuning (Unfreeze Top 40 Layers)
    print("\n==================================================")
    print("     STAGE 2: FINE-TUNING TOP 40 LAYERS          ")
    print("==================================================")
    backbone.trainable = True
    total_backbone_layers = len(backbone.layers)
    freeze_until = total_backbone_layers - UNFREEZE_TOP_N_LAYERS

    print(f"Total backbone layers: {total_backbone_layers}")
    print(f"Freezing backbone layers up to index {freeze_until}, unfreezing top {UNFREEZE_TOP_N_LAYERS} layers.")

    for i, layer in enumerate(backbone.layers):
        if i < freeze_until:
            layer.trainable = False
        else:
            layer.trainable = True

    model.compile(
        optimizer=Adam(learning_rate=STAGE2_LR),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    callbacks_stage2 = [
        ModelCheckpoint(stage2_model_path, monitor="val_loss", save_best_only=True, verbose=1),
        EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True, verbose=1)
    ]

    history_stage2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=STAGE2_EPOCHS,
        class_weight=class_weights,
        callbacks=callbacks_stage2,
        verbose=1
    )

    # 6. Evaluation on UNTOUCHED Clean Test Set
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

    exp3a_metrics_data = {
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

    with open(EXP3A_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(exp3a_metrics_data, f, indent=2)
    print(f"Saved Experiment 3A metrics JSON to {EXP3A_METRICS_JSON}")

    # 7. Save Per-Class CSV and Confusion Matrix CSV
    with open(EXP3A_PER_CLASS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["class_name", "support", "correct", "precision", "recall", "f1_score"])
        for cname in class_names:
            m = per_class_metrics[cname]
            writer.writerow([cname, m["support"], m["correct"], m["precision"], m["recall"], m["f1-score"]])
    print(f"Saved per-class CSV to {EXP3A_PER_CLASS_CSV}")

    with open(EXP3A_CM_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["true_class"] + class_names)
        for i, cname in enumerate(class_names):
            writer.writerow([cname] + list(cm[i]))
    print(f"Saved confusion matrix CSV to {EXP3A_CM_CSV}")

    # 8. Comparison against Experiment 2 Benchmark
    exp2_bench = {
        "accuracy": 0.9146,
        "macro_f1": 0.8138,
        "leaf_curl_recall": 0.6250,
        "leaf_curl_precision": 0.6250,
        "leaf_curl_f1": 0.6250,
        "leaf_curl_to_yellowish": 3,
        "leaf_curl_to_whitefly": 0,
        "leaf_curl_to_damping_off": 0,
        "test_loss": 0.2986
    }

    lc_rec_diff = round((lc_metrics["recall"] - exp2_bench["leaf_curl_recall"]) * 100, 2)
    lc_f1_diff = round((lc_metrics["f1-score"] - exp2_bench["leaf_curl_f1"]) * 100, 2)
    acc_diff = round((test_acc - exp2_bench["accuracy"]) * 100, 2)
    macro_f1_diff = round((macro_f1 - exp2_bench["macro_f1"]) * 100, 2)

    # Classification logic as requested:
    # SUCCESS: Leaf Curl recall and/or Yellowish confusion substantially improved without degrading overall performance.
    # PARTIAL: Small Leaf Curl improvement but remaining confusion persists.
    # NO IMPROVEMENT: No meaningful improvement.
    if lc_metrics["recall"] > exp2_bench["leaf_curl_recall"] and lc_predicted_yellowish < exp2_bench["leaf_curl_to_yellowish"] and acc_diff >= -1.5:
        verdict = "SUCCESS — Leaf Curl recall and Yellowish confusion substantially improved without degrading overall performance."
    elif lc_metrics["recall"] >= exp2_bench["leaf_curl_recall"] or lc_predicted_yellowish <= exp2_bench["leaf_curl_to_yellowish"]:
        verdict = "PARTIAL — Small Leaf Curl improvement but remaining confusion persists."
    else:
        verdict = "NO IMPROVEMENT — No meaningful improvement."

    comparison_data = {
        "experiment3a_verdict": verdict,
        "primary_success_criteria_check": {
            "1_leaf_curl_recall_improvement": f"{exp2_bench['leaf_curl_recall']*100:.2f}% -> {lc_metrics['recall']*100:.2f}% ({lc_rec_diff:+.2f}%)",
            "2_leaf_curl_f1_improvement": f"{exp2_bench['leaf_curl_f1']*100:.2f}% -> {lc_metrics['f1-score']*100:.2f}% ({lc_f1_diff:+.2f}%)",
            "3_leaf_curl_to_yellowish_reduction": f"{exp2_bench['leaf_curl_to_yellowish']}/8 -> {lc_predicted_yellowish}/8",
            "4_overall_macro_f1": f"{exp2_bench['macro_f1']*100:.2f}% -> {macro_f1*100:.2f}% ({macro_f1_diff:+.2f}%)",
            "5_overall_accuracy": f"{exp2_bench['accuracy']*100:.2f}% -> {test_acc*100:.2f}% ({acc_diff:+.2f}%)"
        },
        "experiment2_benchmark": exp2_bench,
        "experiment3a_benchmark": {
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

    with open(EXP3A_COMPARISON_JSON, "w", encoding="utf-8") as f:
        json.dump(comparison_data, f, indent=2)
    print(f"Saved comparison JSON to {EXP3A_COMPARISON_JSON}")

    # 9. Print Comprehensive Results Rationale
    print("\n" + "=" * 75)
    print("       EXPERIMENT 3A BENCHMARK EVALUATION RESULTS                   ")
    print("=" * 75)
    print(f"VERDICT              : {verdict}")
    print(f"Test Loss            : {test_loss:.4f} (Exp 2: {exp2_bench['test_loss']:.4f})")
    print(f"Test Accuracy        : {test_acc*100:.2f}% (Exp 2: {exp2_bench['accuracy']*100:.2f}%)")
    print(f"Macro F1 Score       : {macro_f1*100:.2f}% (Exp 2: {exp2_bench['macro_f1']*100:.2f}%)")
    print(f"Weighted F1 Score    : {weighted_f1*100:.2f}%")
    print("-" * 75)
    print(f"Leaf Curl Recall     : {lc_metrics['recall']*100:.2f}% (Exp 2: {exp2_bench['leaf_curl_recall']*100:.2f}%)")
    print(f"Leaf Curl Precision  : {lc_metrics['precision']*100:.2f}% (Exp 2: {exp2_bench['leaf_curl_precision']*100:.2f}%)")
    print(f"Leaf Curl F1-Score   : {lc_metrics['f1-score']*100:.2f}% (Exp 2: {exp2_bench['leaf_curl_f1']*100:.2f}%)")
    print(f"Leaf Curl -> Yellowish: {lc_predicted_yellowish}/8 (Exp 2: {exp2_bench['leaf_curl_to_yellowish']}/8)")
    print(f"Leaf Curl -> Whitefly : {lc_predicted_whitefly}/8 (Exp 2: {exp2_bench['leaf_curl_to_whitefly']}/8)")
    print("-" * 75)
    print(f"{'Class Name':<30} | {'Correct':<8} | {'Total':<6} | {'Prec (%)':<9} | {'Rec (%)':<9} | {'F1 (%)':<8}")
    print("-" * 75)
    for cname in class_names:
        m = per_class_metrics[cname]
        print(f"{cname:<30} | {m['correct']:<8} | {m['support']:<6} | {m['precision']*100:<9.2f} | {m['recall']*100:<9.2f} | {m['f1-score']*100:<8.2f}")
    print("=" * 75)

if __name__ == "__main__":
    main()
