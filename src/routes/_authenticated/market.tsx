import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Minus,
  MapPin,
  Calculator,
  Bell,
  BarChart3,
  Info,
  CheckCircle2,
  Sparkles,
  RefreshCw,
  IndianRupee,
  Layers,
} from "lucide-react";
import { useState } from "react";
import { PhoneShell } from "@/components/PhoneShell";
import { BottomNav } from "@/components/BottomNav";
import { useLang } from "@/lib/i18n";

type VarietyPrice = {
  name: string;
  price: string;
  unit: string;
  trend: "up" | "down" | "flat";
  change: string;
  minPrice: string;
  maxPrice: string;
  modalPrice: string;
  grade: string;
  arrivals: string;
  exportDemand: string;
};

type YardData = {
  status: string;
  sentiment: string;
  totalArrivals: string;
  updateTime: string;
  prices: VarietyPrice[];
};

const mandiYards = [
  { id: "guntur", name: "Guntur Mandi Yard", location: "Andhra Pradesh", status: "Open • Active Trading" },
  { id: "khammam", name: "Khammam Mandi Yard", location: "Telangana", status: "Open • High Arrival" },
  { id: "warangal", name: "Warangal Enamul Yard", location: "Telangana", status: "Open • Steady Price" },
  { id: "byadgi", name: "Byadgi APMC Yard", location: "Karnataka", status: "Open • Premium Demand" },
];

const yardDataMap: Record<string, YardData> = {
  guntur: {
    status: "Open • Active Trading",
    sentiment: "Overall Market: +2.1% Bullish",
    totalArrivals: "45,000 Bags Arrival",
    updateTime: "Today 09:30 AM",
    prices: [
      {
        name: "Teja (S17)",
        price: "₹18,750",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹350 (+1.9%)",
        minPrice: "₹17,500",
        maxPrice: "₹19,800",
        modalPrice: "₹18,750",
        grade: "A Grade",
        arrivals: "42,000 Bags",
        exportDemand: "Very High (China & Vietnam)",
      },
      {
        name: "341 (Medium Hot)",
        price: "₹17,900",
        unit: "/ Quintal",
        trend: "flat",
        change: "₹0 (0.0%)",
        minPrice: "₹16,800",
        maxPrice: "₹18,500",
        modalPrice: "₹17,900",
        grade: "B Grade",
        arrivals: "28,500 Bags",
        exportDemand: "Moderate",
      },
      {
        name: "LCA 334 / Sannam",
        price: "₹18,200",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹400 (+2.2%)",
        minPrice: "₹17,100",
        maxPrice: "₹19,100",
        modalPrice: "₹18,200",
        grade: "A Grade",
        arrivals: "35,100 Bags",
        exportDemand: "High (Domestic & Export)",
      },
      {
        name: "Byadgi (KDL)",
        price: "₹24,500",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹600 (+2.5%)",
        minPrice: "₹23,000",
        maxPrice: "₹26,200",
        modalPrice: "₹24,500",
        grade: "Super Deluxe",
        arrivals: "18,400 Bags",
        exportDemand: "High (Oleoresin Extraction)",
      },
      {
        name: "Wonder Hot",
        price: "₹16,800",
        unit: "/ Quintal",
        trend: "down",
        change: "-₹240 (-1.4%)",
        minPrice: "₹15,500",
        maxPrice: "₹17,200",
        modalPrice: "₹16,800",
        grade: "C Grade",
        arrivals: "19,800 Bags",
        exportDemand: "Normal",
      },
      {
        name: "Single Extra Red",
        price: "₹19,500",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹250 (+1.3%)",
        minPrice: "₹18,200",
        maxPrice: "₹20,400",
        modalPrice: "₹19,500",
        grade: "A+ Grade",
        arrivals: "12,200 Bags",
        exportDemand: "High (Spice Oils)",
      },
    ],
  },
  khammam: {
    status: "Open • High Arrival",
    sentiment: "Overall Market: +1.5% Steady Up",
    totalArrivals: "38,500 Bags Arrival",
    updateTime: "Today 10:00 AM",
    prices: [
      {
        name: "Teja (S17)",
        price: "₹18,600",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹200 (+1.1%)",
        minPrice: "₹17,300",
        maxPrice: "₹19,500",
        modalPrice: "₹18,600",
        grade: "A Grade",
        arrivals: "32,000 Bags",
        exportDemand: "High",
      },
      {
        name: "341 (Medium Hot)",
        price: "₹17,850",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹150 (+0.8%)",
        minPrice: "₹16,700",
        maxPrice: "₹18,400",
        modalPrice: "₹17,850",
        grade: "B Grade",
        arrivals: "21,000 Bags",
        exportDemand: "Moderate",
      },
      {
        name: "LCA 334 / Sannam",
        price: "₹18,100",
        unit: "/ Quintal",
        trend: "flat",
        change: "₹0 (0.0%)",
        minPrice: "₹17,000",
        maxPrice: "₹18,900",
        modalPrice: "₹18,100",
        grade: "A Grade",
        arrivals: "25,000 Bags",
        exportDemand: "High",
      },
      {
        name: "Byadgi (KDL)",
        price: "₹23,800",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹300 (+1.3%)",
        minPrice: "₹22,500",
        maxPrice: "₹25,000",
        modalPrice: "₹23,800",
        grade: "Deluxe",
        arrivals: "11,000 Bags",
        exportDemand: "Moderate",
      },
      {
        name: "Wonder Hot",
        price: "₹16,750",
        unit: "/ Quintal",
        trend: "down",
        change: "-₹150 (-0.9%)",
        minPrice: "₹15,600",
        maxPrice: "₹17,100",
        modalPrice: "₹16,750",
        grade: "C Grade",
        arrivals: "14,000 Bags",
        exportDemand: "Normal",
      },
      {
        name: "Single Extra Red",
        price: "₹19,200",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹200 (+1.0%)",
        minPrice: "₹18,000",
        maxPrice: "₹20,000",
        modalPrice: "₹19,200",
        grade: "A+ Grade",
        arrivals: "8,500 Bags",
        exportDemand: "High",
      },
    ],
  },
  warangal: {
    status: "Open • Steady Price",
    sentiment: "Overall Market: +0.8% Neutral",
    totalArrivals: "29,000 Bags Arrival",
    updateTime: "Today 09:45 AM",
    prices: [
      {
        name: "Teja (S17)",
        price: "₹18,450",
        unit: "/ Quintal",
        trend: "flat",
        change: "₹0 (0.0%)",
        minPrice: "₹17,200",
        maxPrice: "₹19,300",
        modalPrice: "₹18,450",
        grade: "A Grade",
        arrivals: "24,000 Bags",
        exportDemand: "High",
      },
      {
        name: "341 (Medium Hot)",
        price: "₹17,700",
        unit: "/ Quintal",
        trend: "down",
        change: "-₹100 (-0.6%)",
        minPrice: "₹16,500",
        maxPrice: "₹18,200",
        modalPrice: "₹17,700",
        grade: "B Grade",
        arrivals: "18,000 Bags",
        exportDemand: "Normal",
      },
      {
        name: "LCA 334 / Sannam",
        price: "₹18,050",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹150 (+0.8%)",
        minPrice: "₹16,900",
        maxPrice: "₹18,800",
        modalPrice: "₹18,050",
        grade: "A Grade",
        arrivals: "19,500 Bags",
        exportDemand: "High",
      },
      {
        name: "Byadgi (KDL)",
        price: "₹23,500",
        unit: "/ Quintal",
        trend: "flat",
        change: "₹0 (0.0%)",
        minPrice: "₹22,000",
        maxPrice: "₹24,800",
        modalPrice: "₹23,500",
        grade: "Standard",
        arrivals: "9,000 Bags",
        exportDemand: "Moderate",
      },
      {
        name: "Wonder Hot",
        price: "₹16,600",
        unit: "/ Quintal",
        trend: "down",
        change: "-₹200 (-1.2%)",
        minPrice: "₹15,400",
        maxPrice: "₹17,000",
        modalPrice: "₹16,600",
        grade: "C Grade",
        arrivals: "12,000 Bags",
        exportDemand: "Normal",
      },
      {
        name: "Single Extra Red",
        price: "₹19,000",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹100 (+0.5%)",
        minPrice: "₹17,800",
        maxPrice: "₹19,800",
        modalPrice: "₹19,000",
        grade: "A Grade",
        arrivals: "7,000 Bags",
        exportDemand: "Moderate",
      },
    ],
  },
  byadgi: {
    status: "Open • Premium Demand",
    sentiment: "Overall Market: +3.2% Very High",
    totalArrivals: "52,000 Bags Arrival",
    updateTime: "Today 10:15 AM",
    prices: [
      {
        name: "Byadgi (KDL)",
        price: "₹26,800",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹900 (+3.5%)",
        minPrice: "₹24,500",
        maxPrice: "₹29,000",
        modalPrice: "₹26,800",
        grade: "Super Deluxe (High ASTA)",
        arrivals: "34,000 Bags",
        exportDemand: "Top Premium (Global Spice Extracts)",
      },
      {
        name: "Teja (S17)",
        price: "₹19,100",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹450 (+2.4%)",
        minPrice: "₹17,800",
        maxPrice: "₹20,200",
        modalPrice: "₹19,100",
        grade: "A+ Grade",
        arrivals: "18,000 Bags",
        exportDemand: "Very High",
      },
      {
        name: "Single Extra Red",
        price: "₹20,500",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹700 (+3.5%)",
        minPrice: "₹19,000",
        maxPrice: "₹21,800",
        modalPrice: "₹20,500",
        grade: "Super Red Grade",
        arrivals: "15,000 Bags",
        exportDemand: "High (Oleoresin)",
      },
      {
        name: "341 (Medium Hot)",
        price: "₹18,200",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹300 (+1.7%)",
        minPrice: "₹17,000",
        maxPrice: "₹18,800",
        modalPrice: "₹18,200",
        grade: "A Grade",
        arrivals: "12,000 Bags",
        exportDemand: "Moderate",
      },
      {
        name: "LCA 334 / Sannam",
        price: "₹18,500",
        unit: "/ Quintal",
        trend: "up",
        change: "+₹300 (+1.6%)",
        minPrice: "₹17,300",
        maxPrice: "₹19,400",
        modalPrice: "₹18,500",
        grade: "A Grade",
        arrivals: "14,500 Bags",
        exportDemand: "High",
      },
      {
        name: "Wonder Hot",
        price: "₹17,000",
        unit: "/ Quintal",
        trend: "flat",
        change: "₹0 (0.0%)",
        minPrice: "₹15,800",
        maxPrice: "₹17,500",
        modalPrice: "₹17,000",
        grade: "B Grade",
        arrivals: "9,000 Bags",
        exportDemand: "Normal",
      },
    ],
  },
};

const yardComparisons = [
  { variety: "Teja (S17)", guntur: "₹18,750", khammam: "₹18,600", warangal: "₹18,450", byadgi: "₹19,100" },
  { variety: "341 Variety", guntur: "₹17,900", khammam: "₹17,850", warangal: "₹17,700", byadgi: "₹18,200" },
  { variety: "LCA 334", guntur: "₹18,200", khammam: "₹18,100", warangal: "₹18,050", byadgi: "₹18,500" },
  { variety: "Wonder Hot", guntur: "₹16,800", khammam: "₹16,750", warangal: "₹16,600", byadgi: "₹17,000" },
];

const marketInsights = [
  {
    title: "Strong Export Demand for Teja",
    desc: "Overseas buyers from China, Malaysia and Bangladesh are aggressively sourcing Teja variety in Guntur & Khammam. Prices expected to stay firm.",
    time: "2 hours ago",
    tag: "Bullish",
  },
  {
    title: "Daily Arrival Volume High",
    desc: "Total chilli arrivals across Guntur, Khammam and Byadgi yards touched 135,500 bags today. Premium grades fetching quick sales.",
    time: "4 hours ago",
    tag: "Volume Update",
  },
  {
    title: "High Color Value Premium",
    desc: "Byadgi & Extra Red varieties with high ASTA color values (>120 ASTA) are trading at ₹1,500+ premium above modal price.",
    time: "Today 08:30 AM",
    tag: "Quality Premium",
  },
];

export const Route = createFileRoute("/_authenticated/market")({
  head: () => ({ meta: [{ title: "Market Price — MirchiRakshak AI" }] }),
  component: MarketPricePage,
});

function MarketPricePage() {
  const { t, lang } = useLang();
  const [selectedYard, setSelectedYard] = useState("guntur");
  const [activeTab, setActiveTab] = useState<"rates" | "comparison" | "calculator" | "trends">("rates");

  // Get active yard data dynamically based on selection
  const currentYardData = yardDataMap[selectedYard] || yardDataMap.guntur;
  const currentYardInfo = mandiYards.find((y) => y.id === selectedYard) || mandiYards[0];

  // Calculator State
  const [calcVariety, setCalcVariety] = useState("Teja (S17)");
  const [calcGrade, setCalcGrade] = useState("A");
  const [calcMoisture, setCalcMoisture] = useState("low");
  const [calcQuantity, setCalcQuantity] = useState(20);

  // Price Calculation Logic based on selected yard's dynamic rate
  const matchedPriceObj = currentYardData.prices.find((p) => p.name === calcVariety);
  const basePriceNumber = matchedPriceObj
    ? parseInt(matchedPriceObj.modalPrice.replace(/[^0-9]/g, ""), 10)
    : 18000;

  const gradeMultiplier = calcGrade === "A+" ? 1.08 : calcGrade === "A" ? 1.0 : calcGrade === "B" ? 0.94 : 0.88;
  const moistureMultiplier = calcMoisture === "low" ? 1.03 : calcMoisture === "optimum" ? 1.0 : 0.93;
  const estimatedPricePerQ = Math.round(basePriceNumber * gradeMultiplier * moistureMultiplier);
  const totalValue = estimatedPricePerQ * calcQuantity;

  return (
    <PhoneShell>
      {/* Page Header */}
      <header className="px-5 pt-10 pb-4 flex items-center justify-between bg-earth-50">
        <Link
          to="/home"
          className="size-10 rounded-full bg-white ring-1 ring-black/5 grid place-items-center shadow-sm"
          aria-label="Back"
        >
          <ArrowLeft className="size-4" />
        </Link>
        <div className="flex items-center gap-1.5">
          <TrendingUp className="size-4 text-leaf-600" />
          <h1 className="text-base font-bold text-stone-900">{t("marketplace")}</h1>
        </div>
        <div className="size-10 rounded-full bg-leaf-100 grid place-items-center ring-1 ring-leaf-200">
          <IndianRupee className="size-4 text-leaf-700" />
        </div>
      </header>

      <main className="px-5 pb-28 space-y-4">
        {/* Live Mandi Hero Header - DYNAMICALLY UPDATES WITH SELECTED YARD */}
        <section className="rounded-3xl bg-gradient-to-br from-stone-900 via-stone-800 to-leaf-950 text-white p-5 shadow-[0_20px_40px_-18px_rgba(30,41,59,0.7)] relative overflow-hidden transition-all duration-300">
          <div className="absolute top-0 right-0 -mt-6 -mr-6 size-32 bg-leaf-500/10 rounded-full blur-2xl" />

          <div className="flex items-center justify-between">
            <div>
              <div className="inline-flex items-center gap-1.5 rounded-full bg-leaf-500/20 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-leaf-300 ring-1 ring-leaf-500/30">
                <span className="size-1.5 rounded-full bg-leaf-400 animate-pulse" />
                {currentYardInfo.name}
              </div>
              <h2 className="mt-2 text-2xl font-bold">{currentYardInfo.location} Rates</h2>
              <p className="mt-1 text-xs text-stone-300">{currentYardData.status} • {currentYardData.totalArrivals}</p>
            </div>
            <div className="size-12 rounded-2xl bg-white/10 ring-1 ring-white/20 grid place-items-center shrink-0">
              <TrendingUp className="size-6 text-leaf-400" />
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-xs text-stone-300">
            <span className="flex items-center gap-1">
              <RefreshCw className="size-3 text-leaf-400 animate-spin" style={{ animationDuration: "12s" }} />
              {currentYardData.updateTime}
            </span>
            <span className="font-semibold text-leaf-300">{currentYardData.sentiment}</span>
          </div>
        </section>

        {/* Mandi Yard Selection */}
        <section className="rounded-2xl bg-white p-3 ring-1 ring-black/5 shadow-sm space-y-2">
          <div className="flex items-center justify-between px-1">
            <label className="text-[10px] uppercase tracking-wider text-stone-500 font-bold block">
              {t("selectMandiYard")}
            </label>
            <span className="text-[10px] text-leaf-700 font-semibold">
              {t("tapToSwitchPrice")}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {mandiYards.map((yard) => {
              const isActive = selectedYard === yard.id;
              const yardInfo = yardDataMap[yard.id];
              return (
                <button
                  key={yard.id}
                  onClick={() => setSelectedYard(yard.id)}
                  className={`p-2.5 rounded-xl text-left transition flex flex-col justify-between border ${
                    isActive
                      ? "bg-leaf-50/90 border-leaf-500 ring-2 ring-leaf-500/30 text-stone-900 shadow-sm"
                      : "bg-earth-50/50 border-black/5 text-stone-600 hover:bg-earth-50"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-bold leading-snug">{yard.name}</p>
                    </div>
                    <p className="text-[10px] text-stone-500 flex items-center gap-1 mt-0.5">
                      <MapPin className="size-2.5 text-stone-400" /> {yard.location}
                    </p>
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-[9px] font-semibold text-stone-500">{yardInfo.totalArrivals.split(" ")[0]} bags</span>
                    {isActive ? (
                      <span className="text-[9px] font-bold text-leaf-700 bg-leaf-100 rounded-md px-1.5 py-0.5">
                        {t("activePrice")}
                      </span>
                    ) : (
                      <span className="text-[9px] text-stone-400 font-medium">{t("select")}</span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* Market Price Navigation Tabs */}
        <div className="flex gap-1.5 overflow-x-auto pb-1 no-scrollbar">
          <button
            onClick={() => setActiveTab("rates")}
            className={`whitespace-nowrap rounded-full px-4 py-2 text-xs font-bold transition flex items-center gap-1.5 ${
              activeTab === "rates" ? "bg-stone-900 text-white shadow-sm" : "bg-white text-stone-600 ring-1 ring-black/5"
            }`}
          >
            <BarChart3 className="size-3.5" />
            <span>{t("liveRates")}</span>
          </button>
          <button
            onClick={() => setActiveTab("comparison")}
            className={`whitespace-nowrap rounded-full px-4 py-2 text-xs font-bold transition flex items-center gap-1.5 ${
              activeTab === "comparison" ? "bg-stone-900 text-white shadow-sm" : "bg-white text-stone-600 ring-1 ring-black/5"
            }`}
          >
            <Layers className="size-3.5" />
            <span>{t("yardComparison")}</span>
          </button>
          <button
            onClick={() => setActiveTab("calculator")}
            className={`whitespace-nowrap rounded-full px-4 py-2 text-xs font-bold transition flex items-center gap-1.5 ${
              activeTab === "calculator" ? "bg-stone-900 text-white shadow-sm" : "bg-white text-stone-600 ring-1 ring-black/5"
            }`}
          >
            <Calculator className="size-3.5" />
            <span>{t("priceCalculator")}</span>
          </button>
          <button
            onClick={() => setActiveTab("trends")}
            className={`whitespace-nowrap rounded-full px-4 py-2 text-xs font-bold transition flex items-center gap-1.5 ${
              activeTab === "trends" ? "bg-stone-900 text-white shadow-sm" : "bg-white text-stone-600 ring-1 ring-black/5"
            }`}
          >
            <Sparkles className="size-3.5" />
            <span>{t("insightsTrends")}</span>
          </button>
        </div>

        {/* TAB 1: LIVE VARIETY RATES - DYNAMICALLY RENDERED FOR SELECTED YARD */}
        {activeTab === "rates" && (
          <section className="space-y-3">
            <div className="flex items-center justify-between px-1">
              <h3 className="text-xs font-bold uppercase tracking-wider text-stone-500">
                {t("variety")} {t("marketPrices")} — {currentYardInfo.name}
              </h3>
              <span className="text-[10px] rounded-full bg-leaf-100 px-2 py-0.5 font-bold text-leaf-700">
                {t("apmcLiveFeed")}
              </span>
            </div>

            {currentYardData.prices.map((item) => (
              <div key={item.name} className="rounded-2xl bg-white p-4 ring-1 ring-black/5 shadow-sm space-y-3 transition-all">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-base font-bold text-stone-900">{item.name}</h4>
                      <span className="text-[10px] font-bold rounded-md bg-stone-100 px-2 py-0.5 text-stone-700">
                        {item.grade}
                      </span>
                    </div>
                    <p className="text-[11px] text-stone-500 mt-0.5">{t("exportDemand")}: {item.exportDemand}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-black text-stone-900">{item.price}</p>
                    <div
                      className={`flex items-center justify-end gap-0.5 text-xs font-bold mt-0.5 ${
                        item.trend === "up" ? "text-leaf-600" : item.trend === "down" ? "text-chili-600" : "text-stone-500"
                      }`}
                    >
                      {item.trend === "up" && <TrendingUp className="size-3.5" />}
                      {item.trend === "down" && <TrendingDown className="size-3.5" />}
                      {item.trend === "flat" && <Minus className="size-3.5" />}
                      <span>{item.change}</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 bg-earth-50 rounded-xl p-2.5 text-center text-xs">
                  <div>
                    <span className="text-[10px] text-stone-500 uppercase block">{t("minRate")}</span>
                    <span className="font-semibold text-stone-800">{item.minPrice}</span>
                  </div>
                  <div className="border-x border-black/5">
                    <span className="text-[10px] text-stone-500 uppercase block">{t("modalRate")}</span>
                    <span className="font-bold text-leaf-700">{item.modalPrice}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-stone-500 uppercase block">{t("maxRate")}</span>
                    <span className="font-semibold text-stone-800">{item.maxPrice}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] text-stone-500 pt-1">
                  <span>{t("arrivalsAt")} {currentYardInfo.location}: {item.arrivals}</span>
                  <span className="text-stone-400">{t("perQuintalUnit")}</span>
                </div>
              </div>
            ))}
          </section>
        )}

        {/* TAB 2: YARD PRICE COMPARISON */}
        {activeTab === "comparison" && (
          <section className="rounded-3xl bg-white p-4 ring-1 ring-black/5 shadow-sm space-y-4">
            <div>
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-stone-900">{t("yardComparison")}</h3>
                <span className="text-[10px] bg-sky-100 text-sky-800 font-bold px-2 py-0.5 rounded-full">{t("liveRates")}</span>
              </div>
              <p className="text-xs text-stone-500 mt-1">
                {t("compareMandiHeader")}
              </p>
            </div>

            <div className="space-y-3">
              {yardComparisons.map((item) => (
                <div key={item.variety} className="rounded-2xl border border-black/5 p-3.5 bg-earth-50/40 space-y-2.5">
                  <p className="text-sm font-bold text-stone-900">{item.variety}</p>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div
                      className={`p-2 rounded-xl flex justify-between items-center transition ${
                        selectedYard === "guntur"
                          ? "bg-leaf-100/80 ring-1 ring-leaf-500"
                          : "bg-white ring-1 ring-black/5"
                      }`}
                    >
                      <span className="text-stone-500 text-[11px]">Guntur</span>
                      <span className="font-bold text-stone-900">{item.guntur}</span>
                    </div>
                    <div
                      className={`p-2 rounded-xl flex justify-between items-center transition ${
                        selectedYard === "khammam"
                          ? "bg-leaf-100/80 ring-1 ring-leaf-500"
                          : "bg-white ring-1 ring-black/5"
                      }`}
                    >
                      <span className="text-stone-500 text-[11px]">Khammam</span>
                      <span className="font-bold text-stone-900">{item.khammam}</span>
                    </div>
                    <div
                      className={`p-2 rounded-xl flex justify-between items-center transition ${
                        selectedYard === "warangal"
                          ? "bg-leaf-100/80 ring-1 ring-leaf-500"
                          : "bg-white ring-1 ring-black/5"
                      }`}
                    >
                      <span className="text-stone-500 text-[11px]">Warangal</span>
                      <span className="font-bold text-stone-900">{item.warangal}</span>
                    </div>
                    <div
                      className={`p-2 rounded-xl flex justify-between items-center transition ${
                        selectedYard === "byadgi"
                          ? "bg-leaf-100/80 ring-1 ring-leaf-500"
                          : "bg-white ring-1 ring-black/5"
                      }`}
                    >
                      <span className="text-stone-500 text-[11px]">Byadgi</span>
                      <span className="font-bold text-leaf-700">{item.byadgi}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="p-3 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-start gap-2">
              <Info className="size-4 text-amber-600 shrink-0 mt-0.5" />
              <span>
                {t("byadgiTip")}
              </span>
            </div>
          </section>
        )}

        {/* TAB 3: QUALITY PRICE CALCULATOR (DYNAMIC BASE RATE FOR SELECTED YARD) */}
        {activeTab === "calculator" && (
          <section className="rounded-3xl bg-white p-4 ring-1 ring-black/5 shadow-sm space-y-4">
            <div>
              <div className="flex items-center justify-between">
                <p className="text-[10px] uppercase tracking-wider text-stone-500 font-bold">{t("qualityEstimation")}</p>
                <span className="text-[10px] font-bold text-leaf-700 bg-leaf-100 px-2 py-0.5 rounded-full">
                  {currentYardInfo.name}
                </span>
              </div>
              <h3 className="text-lg font-bold text-stone-900 mt-0.5">{t("qualityCalculatorTitle")}</h3>
              <p className="text-xs text-stone-500">
                {t("activeMandiBaseRate")} <strong>{currentYardInfo.name}</strong>.
              </p>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-stone-700 block mb-1">{t("selectVariety")}</label>
                <select
                  value={calcVariety}
                  onChange={(e) => setCalcVariety(e.target.value)}
                  className="w-full rounded-xl border border-black/10 bg-earth-50 px-3 py-2.5 text-sm font-semibold text-stone-800"
                >
                  {currentYardData.prices.map((p) => (
                    <option key={p.name} value={p.name}>
                      {p.name} ({p.modalPrice}/Q)
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-stone-700 block mb-1">{t("qualityGrade")}</label>
                  <select
                    value={calcGrade}
                    onChange={(e) => setCalcGrade(e.target.value)}
                    className="w-full rounded-xl border border-black/10 bg-earth-50 px-3 py-2.5 text-sm font-semibold text-stone-800"
                  >
                    <option value="A+">Grade A+ (Export Quality)</option>
                    <option value="A">Grade A (Standard)</option>
                    <option value="B">Grade B (Medium)</option>
                    <option value="C">Grade C (Fair)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-stone-700 block mb-1">{t("moistureLevel")}</label>
                  <select
                    value={calcMoisture}
                    onChange={(e) => setCalcMoisture(e.target.value)}
                    className="w-full rounded-xl border border-black/10 bg-earth-50 px-3 py-2.5 text-sm font-semibold text-stone-800"
                  >
                    <option value="low">Low (&lt;10% Dry)</option>
                    <option value="optimum">Optimum (10-12%)</option>
                    <option value="high">High (&gt;12% Damp)</option>
                  </select>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-xs font-semibold text-stone-700">{t("lotQuantity")}</label>
                  <span className="text-xs font-bold text-leaf-700">{calcQuantity} Quintals</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={100}
                  value={calcQuantity}
                  onChange={(e) => setCalcQuantity(Number(e.target.value))}
                  className="w-full accent-leaf-600"
                />
              </div>
            </div>

            {/* Calculated Results */}
            <div className="rounded-2xl bg-gradient-to-br from-earth-900 to-stone-900 text-white p-4 space-y-3 shadow-md">
              <div className="flex justify-between items-center text-xs text-stone-300 pb-1">
                <span>{t("activeMandiBaseRate")} ({calcVariety})</span>
                <span className="font-bold text-white">₹{basePriceNumber.toLocaleString()}/Q</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-white/10">
                <span className="text-xs text-stone-300">{t("estimatedPricePerQ")}</span>
                <span className="text-xl font-black text-leaf-400">₹{estimatedPricePerQ.toLocaleString()}/Q</span>
              </div>
              <div className="flex justify-between items-center">
                <div>
                  <span className="text-xs text-stone-300 block">{t("totalRealizationValue")}</span>
                  <span className="text-[10px] text-stone-400">For {calcQuantity} Quintals at {currentYardInfo.name}</span>
                </div>
                <span className="text-2xl font-black text-white">₹{totalValue.toLocaleString()}</span>
              </div>
            </div>
          </section>
        )}

        {/* TAB 4: MARKET INSIGHTS & TRENDS */}
        {activeTab === "trends" && (
          <section className="space-y-3">
            <div className="rounded-3xl bg-white p-4 ring-1 ring-black/5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-stone-900">{t("dailyMarketInsights")}</h3>
                <Bell className="size-4 text-leaf-600" />
              </div>
              <div className="space-y-3">
                {marketInsights.map((insight) => (
                  <div key={insight.title} className="p-3 rounded-2xl bg-earth-50 border border-black/5 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider bg-leaf-100 text-leaf-800 px-2 py-0.5 rounded-full">
                        {insight.tag}
                      </span>
                      <span className="text-[10px] text-stone-400">{insight.time}</span>
                    </div>
                    <h4 className="text-xs font-bold text-stone-900">{insight.title}</h4>
                    <p className="text-[11px] text-stone-600">{insight.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-3xl bg-stone-900 p-4 text-white shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold text-leaf-400 uppercase tracking-widest">{t("marketAdvisory")}</span>
                  <h4 className="text-base font-bold">{t("chilliPriceForecast")}</h4>
                </div>
                <CheckCircle2 className="size-6 text-leaf-400" />
              </div>
              <p className="text-xs text-stone-300 leading-relaxed">
                {t("chilliForecastDesc")}
              </p>
            </div>
          </section>
        )}
      </main>

      <BottomNav />
    </PhoneShell>
  );
}
