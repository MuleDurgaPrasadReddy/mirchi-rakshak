import * as tf from "@tensorflow/tfjs";
import type { LayerArgs } from "@tensorflow/tfjs-layers/dist/engine/topology";
import { DATASET_CLASS_MAP, getDiseaseByClass, DiseaseInfo } from "./diseaseDataset";

const MODEL_URL = "/models/chili-disease/model.json";

function registerIdentityLayer(className: string) {
  const IdentityLayer = class extends tf.layers.Layer {
    static get className() {
      return className;
    }

    call(inputs: tf.Tensor | tf.Tensor[]) {
      return inputs;
    }

    computeOutputShape(inputShape: tf.Shape): tf.Shape {
      return inputShape;
    }
  };

  tf.serialization.registerClass(IdentityLayer);
}

class MobileNetScalarOp extends tf.layers.Layer {
  static get className() {
    return "MobileNetScalarOp";
  }

  private readonly operation: string;
  private readonly scalar: number;

  constructor(config: LayerArgs & { function?: string; scalar?: number }) {
    super(config);
    this.operation = config.function ?? "";
    if (typeof config.scalar !== "number") {
      throw new Error("MobileNet operator is missing its scalar configuration");
    }
    this.scalar = config.scalar;
  }

  call(inputs: tf.Tensor | tf.Tensor[]) {
    const input = Array.isArray(inputs) ? inputs[0] : inputs;
    if (!input) throw new Error("MobileNet operator received no input tensor");

    if (
      this.operation === "__operators__.add" ||
      this.operation === "Operators_.add"
    ) {
      return tf.add(input, this.scalar);
    }
    if (this.operation === "math.multiply") return tf.mul(input, this.scalar);
    throw new Error(`Unsupported MobileNet operator: ${this.operation}`);
  }

  computeOutputShape(inputShape: tf.Shape): tf.Shape {
    return inputShape;
  }
}

class GlobalAveragePooling2DKeepDims extends tf.layers.Layer {
  static get className() {
    return "GlobalAveragePooling2DKeepDims";
  }

  call(inputs: tf.Tensor | tf.Tensor[]) {
    const input = Array.isArray(inputs) ? inputs[0] : inputs;
    if (!input) throw new Error("MobileNet pooling layer received no input tensor");
    return tf.mean(input, [1, 2], true);
  }

  computeOutputShape(inputShape: tf.Shape): tf.Shape {
    return [inputShape[0], 1, 1, inputShape[3]];
  }
}

function registerModelCompatibilityLayers() {
  for (const className of [
    "RandomFlip",
    "RandomRotation",
    "RandomZoom",
    "RandomTranslation",
    "RandomContrast",
  ]) {
    if (!tf.serialization.SerializationMap.getMap().classNameMap[className]) {
      registerIdentityLayer(className);
    }
  }

  if (!tf.serialization.SerializationMap.getMap().classNameMap.MobileNetScalarOp) {
    tf.serialization.registerClass(MobileNetScalarOp);
  }

  if (!tf.serialization.SerializationMap.getMap().classNameMap.GlobalAveragePooling2DKeepDims) {
    tf.serialization.registerClass(GlobalAveragePooling2DKeepDims);
  }
}

registerModelCompatibilityLayers();

export const CHILI_DATASET_CLASSES = [
  "Chilli __Whitefly",
  "Chilli __Yellowish",
  "Chilli__Anthracnos",
  "Chilli__Damping_Off",
  "Chilli__Leaf_Curl_Virus",
  "Chilli__Leaf_Spot",
  "Chilli__Veinal_Mottle_Virus",
  "Chilli___healthy",
] as const;

export type ChiliDatasetClass = (typeof CHILI_DATASET_CLASSES)[number];

let modelPromise: Promise<tf.LayersModel | tf.GraphModel | null> | null = null;

/**
 * Loads the pre-trained MobileNetV3 model trained on src/data (public/models/chili-disease/model.json)
 */
export async function loadChiliTFJSModel(): Promise<tf.LayersModel | tf.GraphModel | null> {
  if (typeof window === "undefined") return null;
  if (!modelPromise) {
    modelPromise = tf.loadLayersModel(MODEL_URL)
      .catch(() => tf.loadGraphModel(MODEL_URL))
      .catch((err) => {
        console.warn("[MirchiRakshak] Local TFJS model load deferred/failed:", err);
        modelPromise = null;
        return null;
      });
  }
  return modelPromise;
}

export type ChiliScanImage = HTMLImageElement | HTMLCanvasElement;

export type TFJSClassificationResult = {
  className: ChiliDatasetClass;
  diseaseId: string;
  confidence: number;
  diseaseInfo: DiseaseInfo | undefined;
};

/**
 * Classifies an image (HTMLImageElement or data URL string) against the 8 dataset classes in src/data
 */
export async function classifyChiliImageWithTFJS(
  imageSource: ChiliScanImage | string,
): Promise<TFJSClassificationResult | null> {
  try {
    const model = await loadChiliTFJSModel();
    if (!model) return null;

    let imgElement: ChiliScanImage;
    if (typeof imageSource === "string") {
      imgElement = new Image();
      imgElement.crossOrigin = "anonymous";
      imgElement.src = imageSource;
      await imgElement.decode();
    } else {
      imgElement = imageSource;
    }

    const prediction = tf.tidy(() =>
      model.predict(
        tf.browser
          .fromPixels(imgElement)
          .resizeNearestNeighbor([224, 224])
          .toFloat()
          .expandDims(0),
      ) as tf.Tensor,
    );
    let scores: Float32Array;
    try {
      scores = await prediction.data();
    } finally {
      prediction.dispose();
    }

    let maxIndex = 0;
    let maxScore = -1;
    for (let i = 0; i < scores.length; i++) {
      if (scores[i] > maxScore) {
        maxScore = scores[i];
        maxIndex = i;
      }
    }

    // If highest confidence score is low (< 0.45), image is likely non-chili or a person photo
    if (maxScore < 0.45) {
      return null;
    }

    const className = CHILI_DATASET_CLASSES[maxIndex] || CHILI_DATASET_CLASSES[0];
    const diseaseId = DATASET_CLASS_MAP[className] || "healthy";
    const diseaseInfo = getDiseaseByClass(className);
    const confidence = Math.min(99, Math.round(maxScore * 100));

    return {
      className,
      diseaseId,
      confidence,
      diseaseInfo,
    };
  } catch (err) {
    console.warn("[MirchiRakshak] TFJS classification error:", err);
    return null;
  }
}
