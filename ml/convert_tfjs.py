import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import numpy as np
if not hasattr(np, "object"):
    np.object = object
if not hasattr(np, "bool"):
    np.bool = np.bool_

import sys
import types
import json
dummy_hub_estimator = types.ModuleType("tensorflow_hub.estimator")
dummy_hub_estimator.LatestModuleExporter = object
dummy_hub_estimator.register_module_for_export = lambda *args, **kwargs: (lambda fn: fn)
sys.modules["tensorflow_hub.estimator"] = dummy_hub_estimator

try:
    import tensorflow.python.trackable.autotrackable as autotrackable
    sys.modules["tensorflow.python.training.tracking"] = autotrackable
    sys.modules["tensorflow.python.training.tracking.data_structures"] = autotrackable
except Exception:
    pass

from pathlib import Path
import tensorflow as tf
import tensorflowjs as tfjs

ROOT = Path(__file__).resolve().parents[1]
source_keras = ROOT / "ml" / "models" / "mirchi_rakshak_leafcurl_exp01.keras"
if not source_keras.exists():
    source_keras = ROOT / "ml" / "models" / "mirchi_rakshak_clean_best_finetuned.keras"

target = ROOT / "public" / "models" / "chili-disease"
target.mkdir(parents=True, exist_ok=True)

print("Loading trained Keras model:", source_keras)
model = tf.keras.models.load_model(source_keras)

backbone = next(
    (
        layer
        for layer in model.layers
        if isinstance(layer, tf.keras.Model) and "mobilenet" in layer.name.lower()
    ),
    None,
)
if backbone is None:
    raise RuntimeError("Could not find the MobileNet backbone in the trained model.")

backbone_index = model.layers.index(backbone)
inference_input = tf.keras.Input(shape=model.input_shape[1:], name="input_image")
x = backbone(inference_input, training=False)
for layer in model.layers[backbone_index + 1 :]:
    x = layer(x, training=False) if isinstance(layer, tf.keras.layers.Dropout) else layer(x)
inference_model = tf.keras.Model(inference_input, x, name="mirchi_rakshak_inference")

print("Converting the inference-only model to TensorFlow.js format...")
tfjs.converters.save_keras_model(inference_model, str(target))

model_json = target / "model.json"
with model_json.open(encoding="utf-8") as model_file:
    artifacts = json.load(model_file)


def normalize_model_config(config):
    for layer in config.get("layers", []):
        if (
            layer.get("class_name") == "GlobalAveragePooling2D"
            and layer.get("config", {}).get("keepdims") is True
        ):
            layer["class_name"] = "GlobalAveragePooling2DKeepDims"

        if layer.get("class_name") == "TFOpLambda":
            layer["class_name"] = "MobileNetScalarOp"
            inbound_nodes = layer.get("inbound_nodes", [])
            if len(inbound_nodes) != 1:
                raise RuntimeError(
                    f"Expected one MobileNet operator call for {layer.get('name')}"
                )

            node = inbound_nodes[0]
            if (
                isinstance(node, list)
                and node
                and isinstance(node[0], list)
            ):
                if len(node) != 1:
                    raise RuntimeError(
                        f"Expected one input for MobileNet operator {layer.get('name')}"
                    )
                node = node[0]
            if (
                not isinstance(node, list)
                or len(node) < 4
                or not isinstance(node[0], str)
                or not isinstance(node[1], int)
                or not isinstance(node[2], int)
                or not isinstance(node[3], dict)
                or not isinstance(node[3].get("y"), (int, float))
            ):
                raise RuntimeError(
                    f"Unsupported MobileNet operator inputs for {layer.get('name')}"
                )

            layer["config"]["scalar"] = node[3]["y"]
            layer["inbound_nodes"] = [
                [[node[0], node[1], node[2], {}]]
            ]

        nested_config = layer.get("config")
        if isinstance(nested_config, dict) and "layers" in nested_config:
            normalize_model_config(nested_config)


normalize_model_config(artifacts["modelTopology"]["model_config"]["config"])
with model_json.open("w", encoding="utf-8") as model_file:
    json.dump(artifacts, model_file, separators=(",", ":"))

classes = """Chilli __Whitefly
Chilli __Yellowish
Chilli__Anthracnos
Chilli__Damping_Off
Chilli__Leaf_Curl_Virus
Chilli__Leaf_Spot
Chilli__Veinal_Mottle_Virus
Chilli___healthy"""

(target / "classes.txt").write_text(classes, encoding="utf-8")
print(f"SUCCESS: TensorFlow.js model exported to {target}")
