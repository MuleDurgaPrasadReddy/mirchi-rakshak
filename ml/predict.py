from pathlib import Path
import sys
import numpy as np
import tensorflow as tf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "ml" / "models" / "mirchi_rakshak_model.keras"
CLASSES = ROOT / "ml" / "models" / "classes.txt"

if len(sys.argv) != 2:
    raise SystemExit("Usage: python ml/predict.py path/to/leaf.jpg")
model = tf.keras.models.load_model(MODEL)
classes = CLASSES.read_text(encoding="utf-8").splitlines()
image = Image.open(sys.argv[1]).convert("RGB").resize((224, 224))
array = np.expand_dims(np.asarray(image, dtype=np.float32), axis=0)
probabilities = model.predict(array, verbose=0)[0]
indices = np.argsort(probabilities)[::-1][:3]
for index in indices:
    print(f"{classes[index]}: {probabilities[index] * 100:.2f}%")
