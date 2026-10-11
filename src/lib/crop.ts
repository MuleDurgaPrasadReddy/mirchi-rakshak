export type CropStage =
  | "seedling"
  | "vegetative"
  | "flowering"
  | "fruiting"
  | "harvesting";

export interface CropProfileData {
  cropName: string;
  variety: string;
  plantationDate: string; // YYYY-MM-DD
  stage: CropStage;
}

const STORAGE_KEY = "mirchi_crop_profile_v1";

export const STAGE_CONFIG: Record<
  CropStage,
  {
    label: string;
    description: string;
    typicalDaysFromPlanting: number;
    remainingDaysEstimate: number;
    badgeBg: string;
    textColor: string;
  }
> = {
  seedling: {
    label: "Seedling (Nursery)",
    description: "4-6 true leaves, root establishment",
    typicalDaysFromPlanting: 15,
    remainingDaysEstimate: 115,
    badgeBg: "bg-emerald-100",
    textColor: "text-emerald-800",
  },
  vegetative: {
    label: "Vegetative Growth",
    description: "Vigorous branching & leaf canopy expansion",
    typicalDaysFromPlanting: 45,
    remainingDaysEstimate: 75,
    badgeBg: "bg-emerald-100",
    textColor: "text-emerald-800",
  },
  flowering: {
    label: "Flowering Stage",
    description: "Active blooming, high boron & pollination need",
    typicalDaysFromPlanting: 75,
    remainingDaysEstimate: 24,
    badgeBg: "bg-amber-100",
    textColor: "text-amber-800",
  },
  fruiting: {
    label: "Fruit Setting & Pods",
    description: "Green pods elongating and maturing",
    typicalDaysFromPlanting: 105,
    remainingDaysEstimate: 12,
    badgeBg: "bg-lime-100",
    textColor: "text-lime-800",
  },
  harvesting: {
    label: "Maturity & Harvesting",
    description: "Deep red/green ripe chillies ready for picking",
    typicalDaysFromPlanting: 135,
    remainingDaysEstimate: 0,
    badgeBg: "bg-red-100",
    textColor: "text-red-800",
  },
};

export const STAGE_LOCALIZED: Record<
  "en" | "te" | "hi",
  Record<CropStage, { label: string; shortLabel: string; description: string }>
> = {
  en: {
    seedling: { label: "Seedling (Nursery)", shortLabel: "Seedling", description: "4-6 true leaves, root establishment" },
    vegetative: { label: "Vegetative Growth", shortLabel: "Vegetative", description: "Vigorous branching & canopy expansion" },
    flowering: { label: "Flowering Stage", shortLabel: "Flowering", description: "Active blooming & pollination" },
    fruiting: { label: "Fruit Setting & Pods", shortLabel: "Fruit Setting", description: "Green pods elongating & maturing" },
    harvesting: { label: "Maturity & Harvesting", shortLabel: "Harvesting", description: "Ripe chillies ready for picking" },
  },
  te: {
    seedling: { label: "మొక్క దశ (నారుమడి)", shortLabel: "మొక్క దశ", description: "4-6 ఆకులు, వేళ్ళ బలాభివృద్ధి" },
    vegetative: { label: "శాకీయ పెరుగుదల", shortLabel: "శాకీయ దశ", description: "కొమ్మలు విరివిగా రావడం & ఆకుల ఎదుగుదల" },
    flowering: { label: "పూత దశ", shortLabel: "పూత దశ", description: "పువ్వులు వికసించడం, బోరాన్ & పరాగసంపర్కం" },
    fruiting: { label: "కాయ దశ", shortLabel: "కాయ దశ", description: "పచ్చి మిర్చి కాయలు పొడవు కావడం & పక్వత" },
    harvesting: { label: "పక్వత & కోత దశ", shortLabel: "కోత దశ", description: "ఎర్రగా పండిన మిర్చి కోతకు సిద్ధం" },
  },
  hi: {
    seedling: { label: "पौध अवस्था (नर्सरी)", shortLabel: "पौध अवस्था", description: "4-6 पत्तियां, जड़ का विकास" },
    vegetative: { label: "वानस्पतिक वृद्धि", shortLabel: "वानस्पतिक", description: "शाखाओं और पत्तियों का फैलाव" },
    flowering: { label: "फूल आने की अवस्था", shortLabel: "फूल अवस्था", description: "सक्रिय फूल खिलना और परागण" },
    fruiting: { label: "फल लगने की अवस्था", shortLabel: "फल अवस्था", description: "हरी मिर्च की फलियों का विकास" },
    harvesting: { label: "परिपक्वता और कटाई", shortLabel: "कटाई अवस्था", description: "लाल पकी मिर्च तुड़ाई के लिए तैयार" },
  },
};

export const COMMON_VARIETIES = [
  "Teja (S-17)",
  "Guntur Sannam (S4)",
  "Byadgi",
  "Armoor",
  "Indam 5",
  "US-341",
  "Devanur Deluxe",
];

export function getDefaultCropData(): CropProfileData {
  const past = new Date(Date.now() - 55 * 24 * 60 * 60 * 1000);
  const formatted = past.toISOString().split("T")[0];

  return {
    cropName: "Chilli (Mirchi)",
    variety: "Teja (S-17)",
    plantationDate: formatted,
    stage: "flowering",
  };
}

export function loadCropProfile(): CropProfileData {
  if (typeof window === "undefined") return getDefaultCropData();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      const def = getDefaultCropData();
      saveCropProfile(def);
      return def;
    }
    const parsed = JSON.parse(raw) as CropProfileData;
    if (!parsed.plantationDate || !parsed.variety) {
      return getDefaultCropData();
    }
    return parsed;
  } catch {
    return getDefaultCropData();
  }
}

export function saveCropProfile(data: CropProfileData): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    window.dispatchEvent(new CustomEvent("mirchi_crop_updated"));
  } catch (err) {
    console.error("Failed to save crop profile:", err);
  }
}

/**
 * Computes exact harvest calculation based on plantation date and selected stage
 */
export function calculateHarvest(
  plantationDateStr: string,
  stage: CropStage = "flowering",
  lang: "en" | "te" | "hi" = "en"
): {
  daysSincePlantation: number;
  daysToHarvest: number;
  estimatedHarvestDate: string;
  stageInfo: (typeof STAGE_CONFIG)[CropStage];
  localizedStage: { label: string; shortLabel: string; description: string };
  harvestStatus: string;
  daysInFieldText: string;
} {
  const stageInfo = STAGE_CONFIG[stage] || STAGE_CONFIG.flowering;
  const langKey = lang === "te" || lang === "hi" ? lang : "en";
  const localizedStage = STAGE_LOCALIZED[langKey][stage] || STAGE_LOCALIZED.en[stage];

  const now = new Date();
  now.setHours(0, 0, 0, 0);

  let daysSincePlantation = 0;
  if (plantationDateStr) {
    const pDate = new Date(plantationDateStr);
    pDate.setHours(0, 0, 0, 0);
    const diff = Math.max(0, now.getTime() - pDate.getTime());
    daysSincePlantation = Math.floor(diff / (1000 * 60 * 60 * 24));
  } else {
    daysSincePlantation = stageInfo.typicalDaysFromPlanting;
  }

  const TOTAL_CYCLE_DAYS = 135;

  let daysToHarvest = 0;
  if (stage === "harvesting") {
    daysToHarvest = 0;
  } else if (daysSincePlantation > 0) {
    const theoreticalRemaining = Math.max(0, TOTAL_CYCLE_DAYS - daysSincePlantation);
    daysToHarvest = Math.max(
      1,
      Math.round((theoreticalRemaining + stageInfo.remainingDaysEstimate) / 2)
    );
  } else {
    daysToHarvest = stageInfo.remainingDaysEstimate;
  }

  const harvestDateObj = new Date(now.getTime() + daysToHarvest * 24 * 60 * 60 * 1000);
  const estimatedHarvestDate = harvestDateObj.toLocaleDateString(
    langKey === "te" ? "te-IN" : langKey === "hi" ? "hi-IN" : "en-GB",
    {
      day: "numeric",
      month: "short",
      year: "numeric",
    }
  );

  let harvestStatus = "";
  if (daysToHarvest === 0) {
    harvestStatus =
      langKey === "te"
        ? "ఇప్పుడే కోతకు సిద్ధంగా ఉంది!"
        : langKey === "hi"
          ? "अभी कटाई के लिए तैयार!"
          : "Ready for harvest now!";
  } else if (daysToHarvest === 1) {
    harvestStatus =
      langKey === "te"
        ? "కోతకు ~1 రోజు"
        : langKey === "hi"
          ? "कटाई तक ~1 दिन"
          : "~1 day to harvest";
  } else {
    harvestStatus =
      langKey === "te"
        ? `కోతకు ~${daysToHarvest} రోజులు`
        : langKey === "hi"
          ? `कटाई तक ~${daysToHarvest} दिन`
          : `~${daysToHarvest} days to harvest`;
  }

  const daysInFieldText =
    langKey === "te"
      ? `పొలంలో ${daysSincePlantation} రోజులు`
      : langKey === "hi"
        ? `खेत में ${daysSincePlantation} दिन`
        : `${daysSincePlantation}d in field`;

  return {
    daysSincePlantation,
    daysToHarvest,
    estimatedHarvestDate,
    stageInfo,
    localizedStage,
    harvestStatus,
    daysInFieldText,
  };
}
