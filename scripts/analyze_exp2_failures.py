import os
import json
import csv
import numpy as np
import tensorflow as tf
from PIL import Image

os.environ["TF_USE_LEGACY_KERAS"] = "1"
import tf_keras as keras

MODEL_PATH = os.path.join("ml", "models", "mirchi_rakshak_exp2_best_finetuned.keras")
TEST_DIR = os.path.join("src", "data_clean", "test")
TRAIN_DIR = os.path.join("src", "data_clean", "train")

def main():
    print("Loading test dataset from directory...")
    test_ds = tf.keras.utils.image_dataset_from_directory(
        TEST_DIR,
        image_size=(224, 224),
        batch_size=32,
        shuffle=False
    )
    class_names = test_ds.class_names
    file_paths = test_ds.file_paths
    
    print("Classes:", class_names)
    print("Loading Experiment 2 model from:", MODEL_PATH)
    model = keras.models.load_model(MODEL_PATH)
    
    y_true = []
    y_pred_probs = []
    
    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        y_true.extend(labels.numpy())
        y_pred_probs.extend(preds)
        
    y_true = np.array(y_true)
    y_pred_probs = np.array(y_pred_probs)
    y_pred = np.argmax(y_pred_probs, axis=1)
    
    lc_idx = class_names.index("Chilli__Leaf_Curl_Virus")
    yellow_idx = class_names.index("Chilli __Yellowish")
    
    lc_indices = [i for i, label in enumerate(y_true) if label == lc_idx]
    
    print(f"\nFound {len(lc_indices)} Leaf Curl images in test set:")
    
    leaf_curl_analysis = []
    for idx in lc_indices:
        fpath = file_paths[idx]
        fname = os.path.basename(fpath)
        pred_i = y_pred[idx]
        pred_label = class_names[pred_i]
        conf = float(y_pred_probs[idx][pred_i])
        probs = {class_names[c]: float(round(y_pred_probs[idx][c], 4)) for c in range(len(class_names))}
        
        # Image details
        with Image.open(fpath) as img:
            w, h = img.size
            
        status = "CORRECT" if pred_i == lc_idx else f"MISCLASSIFIED -> {pred_label}"
        print(f"[{status}] {fname}: Pred = {pred_label} (Conf = {conf*100:.2f}%)")
        print(f"   Probabilities: Yellowish={probs['Chilli __Yellowish']*100:.2f}%, Leaf Curl={probs['Chilli__Leaf_Curl_Virus']*100:.2f}%")
        
        leaf_curl_analysis.append({
            "filename": fname,
            "filepath": fpath,
            "index_in_test": idx,
            "true_label": "Chilli__Leaf_Curl_Virus",
            "predicted_label": pred_label,
            "confidence": round(conf, 4),
            "confidence_pct": round(conf * 100, 2),
            "width": w,
            "height": h,
            "probabilities": probs
        })
        
    with open("scripts/exp2_leaf_curl_test_exact_matches.json", "w") as f:
        json.dump(leaf_curl_analysis, f, indent=2)

if __name__ == "__main__":
    main()
