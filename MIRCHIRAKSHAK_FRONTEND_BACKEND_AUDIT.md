# MirchiRakshak AI — Frontend & Backend Audit Report

**Date**: September 23, 2026  
**Project**: MirchiRakshak AI (Chili Crop Protection & AI Diagnostics Platform)  
**Role**: Senior Full-Stack Engineer Audit  

---

## Executive Summary
This document provides an exhaustive, non-destructive audit of the **MirchiRakshak AI** application. It inspects all 20 architectural components of the codebase, demarcates real vs. mocked features, specifies existing data structures and routes, and maps out the backend requirements to transition from TanStack Start server functions & client mock fallbacks to a dedicated backend architecture.

---

## 🔍 Detailed Inspection of 20 Architectural Components

### 1. Frontend Framework & Version
- **Core UI Framework**: React `^19.2.0` with React DOM `^19.2.0`
- **Build Tool**: Vite `^8.0.16` with `@vitejs/plugin-react` `^5.2.0` and `@tailwindcss/vite` `^4.2.1`
- **Routing & SSR Framework**: TanStack Router `^1.170.16` with TanStack Start `^1.168.26` (file-based routing via `src/routes`)
- **State & Data Fetching**: TanStack React Query `^5.101.1`
- **Styling & Components**: Tailwind CSS `^4.2.1`, Lucide React `^0.575.0`, Radix UI primitives, Sonner `^2.0.7` for toast notifications
- **Machine Learning**: `@tensorflow/tfjs` `^4.22.0` (Client-side MobileNet classifier)

### 2. Folder Structure
```
Mirchi Ai App/
├── src/
│   ├── assets/                # Static assets (farmer avatar, logo, background graphics)
│   ├── components/            # Reusable UI components
│   │   ├── ui/                # Radix UI + Tailwind primitive components
│   │   ├── BottomNav.tsx      # Mobile bottom navigation bar
│   │   ├── HealthRing.tsx     # Animated crop health score gauge ring
│   │   └── PhoneShell.tsx     # Mobile viewport shell wrapper
│   ├── data/                  # TensorFlow.js dataset classes & training manifests
│   ├── integrations/          # External API & Database SDK integrations
│   │   ├── supabase/          # Supabase client, admin server client, auth middleware, DB types
│   │   └── lovable/           # Lovable platform integration wrapper
│   ├── lib/                   # Core business logic & server functions
│   │   ├── ai.functions.ts    # TanStack Start server functions (analyzeScan, chatAssistant, fetchWeather, saveScan, listScans)
│   │   ├── diseaseDataset.ts  # Master offline dataset (14 diseases + Telugu/Hindi/English translations + image profiling logic)
│   │   ├── tfjsModel.ts       # TensorFlow.js MobileNet 8-class inference helper
│   │   ├── firebase.ts        # Firebase Auth & Web SDK configuration
│   │   ├── i18n.tsx           # Multilingual React Context (English, Hindi, Telugu)
│   │   ├── utils.ts           # Tailwind class merger (clsx + tailwind-merge)
│   │   └── error-capture.ts   # Client error reporting helpers
│   ├── routes/                # TanStack Router file-based route definitions
│   │   ├── __root.tsx         # Root HTML shell, QueryClientProvider, LanguageProvider, Toaster
│   │   ├── index.tsx          # Root redirect handler
│   │   ├── onboarding.tsx     # Welcome carousel & language selector
│   │   ├── auth.tsx           # Authentication screen (Email, Phone OTP, Google OAuth)
│   │   └── _authenticated/    # Protected route group with authentication guard
│   │       ├── route.tsx      # Guard checking Firebase/Supabase auth sessions
│   │       ├── home.tsx       # Farmer dashboard (health score, weather widget, quick scan actions)
│   │       ├── scan.tsx       # Live camera & upload photo AI scanner with image canvas stats
│   │       ├── history.tsx    # Timeline list of past scan records
│   │       ├── chat.tsx       # AI voice & text chat assistant
│   │       ├── advisor.tsx    # Expert phone consultation & field visit booking workflow
│   │       ├── market.tsx     # Market prices, yard slots, & cold storage directory
│   │       ├── weather.tsx    # 7-day weather forecast & disease risk advisory
│   │       └── profile.tsx    # Farmer profile info, language switcher, sign out
│   ├── styles.css             # Tailwind CSS v4 setup & custom animations
│   ├── start.ts               # TanStack Start server handler
│   └── router.tsx             # TanStack Router instantiation
├── package.json
└── tsconfig.json
```

### 3. Existing Pages / Screens
1. `/onboarding`: Welcome screen showcasing app features and language selection (`en`, `hi`, `te`).
2. `/auth`: Multi-modal sign-in/up page supporting Email/Password, Phone OTP (Firebase Recaptcha), and Google OAuth.
3. `/_authenticated/home`: Dashboard displaying farm crop health score (0-100), harvest countdown, soil moisture, live weather snippet, and scan shortcuts.
4. `/_authenticated/scan`: Camera viewfinder and file picker with pixel profiling (`getLeafImageStats`), local TFJS classification, server Vision AI diagnosis, and diagnostic error result card.
5. `/_authenticated/history`: Chronological list of user scan records with disease names, confidence scores, severity badges, and image thumbnails.
6. `/_authenticated/chat`: Real-time voice and text AI farming assistant with Web Speech recognition (`SpeechRecognition`) and text-to-speech synthesis (`SpeechSynthesis`).
7. `/_authenticated/advisor`: Expert consultation portal for scheduling phone calls with crop pathologists and requesting field visits.
8. `/_authenticated/market`: Agricultural market intelligence displaying prices for Teja, 341, and Wonder chili varieties, yard slot booking status, and cold storage options.
9. `/_authenticated/weather`: 7-day forecast with humidity, wind speed, spray window advice, and disease risk alerts powered by Open-Meteo.
10. `/_authenticated/profile`: Profile card displaying farmer name, email/phone, district, language selection buttons, scan history link, and sign-out action.

### 4. Existing Authentication Implementation
- **Dual Auth Handler**:
  - **Firebase Auth**: Configured in [`firebase.ts`](file:///c:/Users/muled/OneDrive/Desktop/Mirchi%20Ai%20App/src/lib/firebase.ts). Handles Email/Password (`createUserWithEmailAndPassword`, `signInWithEmailAndPassword`), Google OAuth Popup (`signInWithPopup`), and Phone Number OTP with invisible Recaptcha (`signInWithPhoneNumber`, `RecaptchaVerifier`).
  - **Supabase Auth**: Configured in [`client.ts`](file:///c:/Users/muled/OneDrive/Desktop/Mirchi%20Ai%20App/src/integrations/supabase/client.ts). Manages database row-level security sessions (`supabase.auth.getUser()`, `onAuthStateChange`).
- **Route Protection Guard**:
  - [`_authenticated/route.tsx`](file:///c:/Users/muled/OneDrive/Desktop/Mirchi%20Ai%20App/src/routes/_authenticated/route.tsx) checks `auth.currentUser` (Firebase) first, then `supabase.auth.getUser()` (Supabase). If both are unauthenticated, it redirects the user to `/auth`.

### 5. Existing Supabase & Firebase Configuration
- **Firebase**: Project ID `mirchi-rakshak-ai`, initialized in [`firebase.ts`](file:///c:/Users/muled/OneDrive/Desktop/Mirchi%20Ai%20App/src/lib/firebase.ts). Used primarily for client-side authentication.
- **Supabase**: Configured in [`client.ts`](file:///c:/Users/muled/OneDrive/Desktop/Mirchi%20Ai%20App/src/integrations/supabase/client.ts) (browser client proxy) and [`client.server.ts`](file:///c:/Users/muled/OneDrive/Desktop/Mirchi%20Ai%20App/src/integrations/supabase/client.server.ts) (server-side admin client using `SUPABASE_SERVICE_ROLE_KEY`). Database contains tables: `profiles`, `farms`, `scans`. Storage bucket: `scans`.

### 6. Existing API Calls
- **Open-Meteo Weather API**: Direct `fetch` to `https://api.open-meteo.com/v1/forecast` inside `fetchWeather` server function.
- **Google Gemini Vision & Chat API**:
  - Direct API key endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=...`
  - Gateway fallback: `https://ai.gateway.lovable.dev/v1/chat/completions`
- **Supabase REST / Storage API**:
  - `supabase.from("scans").insert()` and `supabase.from("scans").select()`
  - `supabase.from("profiles").select()` and `supabase.from("profiles").update()`
  - `supabase.storage.from("scans").upload()` and `createSignedUrl()`

### 7. Existing Mock Data
- **Offline Disease Dataset**: 14 chili pathologies defined in [`diseaseDataset.ts`](file:///c:/Users/muled/OneDrive/Desktop/Mirchi%20Ai%20App/src/lib/diseaseDataset.ts) (`bacterial_spot`, `anthracnose`, `cercospora`, `leaf_curl`, `mosaic_virus`, `powdery_mildew`, `phytophthora_blight`, `fusarium_wilt`, `damping_off`, `thrips_damage`, `mites_damage`, `nitrogen_deficiency`, `potassium_deficiency`, `healthy`).
- **Offline Q&A Engine**: `getOfflineChatReply` matching keywords for leaf curl, anthracnose, thrips/mites, and fertilizers.
- **Marketplace Static Data**: Daily mandi prices for Teja (₹18,750/Q), 341 (₹17,900/Q), and Wonder (₹16,800/Q), yard slot requests, and cold storage directories in [`market.tsx`](file:///c:/Users/muled/OneDrive/Desktop/Mirchi%20Ai%20App/src/routes/_authenticated/market.tsx).
- **Expert Advisor Mock Data**: `Dr. Rajesh Kumar` consultation steps and field visit booking workflow in [`advisor.tsx`](file:///c:/Users/muled/OneDrive/Desktop/Mirchi%20Ai%20App/src/routes/_authenticated/advisor.tsx).

### 8. Existing AI & Gemini Integration
- **Vision Diagnosis (`analyzeScan`)**:
  - Accepts image Base64/URL, language preference (`en`, `hi`, `te`), pixel feature stats (`imageStats`), and local MobileNet predicted class (`predictedClass`).
  - Evaluates `scanSystem` pathologist prompt with strict crop identification rules.
  - Rejects human face/body photos and non-chili tree leaves (e.g., Mango, Tomato, Cotton, Rose).
  - Normalizes JSON responses to return structured `ScanResult`.
- **Conversational Advisor (`chatAssistant`)**:
  - Accepts chat message history and language.
  - Generates concise advice (<120 words) focused on low-cost ICAR-approved remedies.

### 9. Scan & Diagnosis Workflow
1. User captures a frame with camera or selects an image file on `/_authenticated/scan`.
2. Client canvas resizes image to 96x96 and extracts `imageStats`:
   - `greenRatio`, `foliageRatio`, `skinRatio`, `brownSpotRatio`, `yellowRatio`, `darkGreenRatio`, `glossyRatio`.
3. Client runs local MobileNet classifier (`classifyChiliImageWithTFJS`). If `maxScore >= 0.45`, passes `predictedClass`.
4. Client invokes `analyzeScan` server function.
5. Server verifies subject (person vs. mango vs. chili leaf).
6. If API key exists, calls Gemini Vision; otherwise falls back to `analyzeImageOffline`.
7. UI displays result card (or diagnostic error card for unmatched images).
8. Image is asynchronously uploaded to Supabase Storage `scans` bucket, and scan metadata is saved to `scans` table.

### 10. Farm Management Workflow
- Schema defined in Supabase `farms` table (`id`, `user_id`, `name`, `variety`, `size_acres`, `village`, `planting_date`, `latitude`, `longitude`).
- UI currently displays farm stat summaries on the dashboard ("Guntur Sannam • 24 days to harvest"), while full CRUD operations on farms are managed via database bindings.

### 11. User Profile Workflow
- Schema defined in Supabase `profiles` table (`id`, `full_name`, `phone`, `avatar_url`, `language`, `district`, `village`, `onboarded`).
- Profile screen (`profile.tsx`) displays user name, email/phone, avatar, and district.
- Language buttons (`English`, `हिंदी`, `తెలుగు`) immediately update global i18n context (`LanguageProvider`) and update `profiles.language` in Supabase.

### 12. Chat & Advisor Workflow
- **Chat (`chat.tsx`)**: Interactive speech and text interface. Uses Web Speech API for voice recognition and browser SpeechSynthesis for audio readout. Invokes `chatAssistant` server function.
- **Advisor (`advisor.tsx`)**: Step-by-step workflow for selecting crop issues (disease, pest, general), placing simulated expert calls, and requesting field visits.

### 13. Image Upload Workflow
- Client captures file or camera blob, converts to Base64 data URL for instant canvas profiling and API payload.
- Asynchronous storage upload:
  ```ts
  const path = `${currentUserId}/${Date.now()}.jpg`;
  await supabase.storage.from("scans").upload(path, blob, { contentType: "image/jpeg" });
  const { data: signed } = await supabase.storage.from("scans").createSignedUrl(path, 31536000);
  ```
- Uploaded signed image URL is stored in `scans.image_url`.

### 14. Environment Variables Currently Used
- `VITE_SUPABASE_URL` / `SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY` / `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_SECRET_KEY`
- `GEMINI_API_KEY` / `VITE_GEMINI_API_KEY`
- `LOVABLE_API_KEY` / `VITE_LOVABLE_API_KEY`

### 15. Existing TypeScript Interfaces & Types
- **`ScanResult`** (in [`diseaseDataset.ts`](file:///c:/Users/muled/OneDrive/Desktop/Mirchi%20Ai%20App/src/lib/diseaseDataset.ts)):
  ```ts
  export type ScanResult = {
    is_chili_leaf: boolean;
    invalid_reason?: string;
    disease: string;
    is_healthy: boolean;
    confidence: number;
    severity: "None" | "Low" | "Moderate" | "High" | "Critical";
    affected_area: string;
    risk_level: "Low" | "Medium" | "High";
    recommendation: string;
    treatment: { step: string; detail: string }[];
    recovery_days: number;
  };
  ```
- **`LeafImageStats`**:
  ```ts
  export type LeafImageStats = {
    greenRatio?: number;
    foliageRatio?: number;
    skinRatio?: number;
    brownSpotRatio?: number;
    yellowRatio?: number;
    darkGreenRatio?: number;
    glossyRatio?: number;
  };
  ```
- **`WeatherData`** (in [`ai.functions.ts`](file:///c:/Users/muled/OneDrive/Desktop/Mirchi%20Ai%20App/src/lib/ai.functions.ts)):
  ```ts
  export type WeatherData = {
    current: { temp: number; humidity: number; wind: number; code: number; time: string };
    daily: { date: string; tmax: number; tmin: number; rain: number; code: number }[];
    risk: "Low" | "Medium" | "High";
    advice: string;
    sprayWindow: string;
  };
  ```
- **Database Types** (in [`types.ts`](file:///c:/Users/muled/OneDrive/Desktop/Mirchi%20Ai%20App/src/integrations/supabase/types.ts)): `profiles`, `farms`, `scans`, and `app_language` (`en` | `hi` | `te`).

### 16. Existing Database-Related Code
- Direct Supabase PostgREST client queries in `home.tsx`, `history.tsx`, `profile.tsx`, and `__root.tsx`.
- Administrative bypass using `supabaseAdmin` service role client in `ai.functions.ts` for saving/listing scans across auth providers.

### 17. Existing Services & Hooks
- `useLang()` hook providing `t(key)`, `lang`, and `setLang(code)` for multilingual text rendering.
- `@tanstack/react-query` hooks (`useQuery`, `useSuspenseQuery`, `ensureQueryData`).
- `@tanstack/react-start` server function caller (`useServerFn`).
- `useIsMobile()` viewport query hook.

### 18. Existing Error Handling
- `ErrorComponent` in `__root.tsx` sending unhandled boundary errors to `reportLovableError`.
- Toast notifications (`toast.error()`, `toast.success()`) in auth, scan, and language update flows.
- Multi-tiered fallbacks (Gemini Vision API $\rightarrow$ Offline Dataset engine; Firebase Auth $\rightarrow$ Supabase Auth fallback).

### 19. Existing Loading States
- `analyzing` animated scanner line in `scan.tsx`.
- Bouncing dot loading animation in `chat.tsx`.
- `loading` spinners and disabled button states on `auth.tsx`.
- Suspense route loaders for dashboard and scan history.

### 20. Existing Route Structure
- `/`: Root landing / redirect
- `/onboarding`: App walkthrough & language selector
- `/auth`: Sign in & sign up screen
- `/_authenticated`: Layout guard route
  - `/_authenticated/home`
  - `/_authenticated/scan`
  - `/_authenticated/history`
  - `/_authenticated/chat`
  - `/_authenticated/advisor`
  - `/_authenticated/market`
  - `/_authenticated/weather`
  - `/_authenticated/profile`

---

## 📑 Categorized Backend Analysis (Sections A – G)

### A. What Already Exists
1. **Fully Functional UI Shell**: Responsive mobile app layout (`PhoneShell`, `BottomNav`, custom styling, badges, animations).
2. **Client-Side Image Profiler**: Canvas 96x96 pixel feature extractor (`greenRatio`, `skinRatio`, `yellowRatio`, `darkGreenRatio`, `glossyRatio`).
3. **TensorFlow.js MobileNet Classifier**: Client-side MobileNet model for instant offline chili leaf classification with threshold filtering ($< 0.45$).
4. **Comprehensive Pathology Dataset**: 14 full disease entries with English, Hindi, and Telugu translations (`diseaseDataset.ts`).
5. **Subject Verification Logic**: Non-chili leaf rejection (Mango, Tomato, Rose, Cotton) and human photo rejection in `scanSystem` & `inspectChiliLeafSignature`.
6. **Multilingual Context System**: Complete translation engine (`i18n.tsx`) supporting English, Hindi, and Telugu across all routes.
7. **Speech Processing**: Native browser Web Speech recognition and speech synthesis integration in `chat.tsx`.

### B. What Is Mocked
1. **Marketplace Data (`market.tsx`)**: Daily mandi prices for Teja, 341, and Wonder, yard slot booking statuses, and cold storage directory lists are hardcoded constants.
2. **Expert Consultation (`advisor.tsx`)**: Expert profile (`Dr. Rajesh Kumar`), simulated 3-second call timer, and field visit request submissions are UI state transitions.
3. **Weather Advisory Fallback**: Hardcoded fallback values in `fetchWeather` when Open-Meteo API is unreachable.
4. **Harvest Countdown**: Hardcoded 24-day countdown and soil moisture percentage (68%) on dashboard.

### C. What Requires a Backend
1. **Centralized REST/GraphQL API Server**: Moving TanStack Start server functions out of the frontend bundle into a dedicated Node.js (Express/FastAPI) backend.
2. **Unified Authentication & JWT Verification**: Unified authentication backend issuing and validating JWT tokens across Firebase and Supabase auth flows.
3. **AI Vision Diagnosis Service**: Secure server-side endpoint wrapping Gemini 2.5 Flash API calls with API key isolation.
4. **Marketplace & Mandi Price Engine**: Dynamic endpoints to fetch, create, and list daily mandi prices, yard booking slots, and cold storage availability.
5. **Expert Booking & Field Visit Engine**: API endpoints to store consultation bookings, assign pathologist calls, and log field visit requests.
6. **Persistent Chat History**: Server-side storage for farmer Q&A conversations per user session.

### D. What APIs the Frontend Expects
| Endpoint | Method | Expected Input Payload | Expected Output Payload |
| :--- | :--- | :--- | :--- |
| `/api/scan/analyze` | `POST` | `{ imageBase64, language, imageStats, predictedClass }` | `ScanResult` JSON object |
| `/api/chat` | `POST` | `{ messages: [{ role, content }], language }` | `{ reply: string }` |
| `/api/scans` | `GET` | Header: `Authorization: Bearer <token>` | `ScanRecord[]` array |
| `/api/scans` | `POST` | `ScanResult & { image_url, language }` | `{ id: string }` |
| `/api/weather` | `GET` | Query: `lat`, `lon` | `WeatherData` JSON object |
| `/api/farms` | `GET/POST` | `{ name, variety, size_acres, village, planting_date }` | `Farm` object |
| `/api/profile` | `GET/PUT` | `{ full_name, language, district, village }` | `Profile` object |

### 5. What Data Structures Are Already Defined
- `ScanResult` (`is_chili_leaf`, `invalid_reason`, `disease`, `is_healthy`, `confidence`, `severity`, `affected_area`, `risk_level`, `recommendation`, `treatment`, `recovery_days`).
- `LeafImageStats` (`greenRatio`, `foliageRatio`, `skinRatio`, `brownSpotRatio`, `yellowRatio`, `darkGreenRatio`, `glossyRatio`).
- `WeatherData` (`current`, `daily`, `risk`, `advice`, `sprayWindow`).
- Database Row Interfaces for `profiles`, `farms`, and `scans`.

### F. What Should NOT Be Changed
1. **Existing UI Design System**: Tailored colors (`chili-600`, `leaf-600`, `earth-50`), `PhoneShell`, `BottomNav`, typography, and Radix UI components.
2. **Multilingual Architecture**: `i18n.tsx` keys, language context provider, and code maps (`en`, `hi`, `te`).
3. **Client-Side Canvas Feature Extraction**: `getLeafImageStats` in `scan.tsx` (crucial for pre-filtering image features before server request).
4. **Client-Side MobileNet Model**: `tfjsModel.ts` (essential for offline classification).
5. **Subject Verification Rules**: Rejection signatures for person/human photos and non-chili leaves (Mango, Tomato, Cotton, Rose).

### G. Potential Frontend/Backend Integration Conflicts
1. **Dual Auth Token Mismatch**: Firebase issues Google/Phone OAuth tokens, while Supabase issues Supabase JWTs. Backend JWT middleware must support dual token verification or exchange Firebase tokens for backend JWTs.
2. **Base64 Payload Size Limits**: Capturing high-resolution camera photos can generate 5MB+ Base64 strings, potentially exceeding default body-parser limits (e.g. Express default 100kb limit). Backend parser must set `limit: '50mb'`.
3. **Cross-Origin Resource Sharing (CORS)**: When moving from SSR server functions to a separate backend URL, CORS headers must explicitly allow requests from the Vite dev server (`http://localhost:8080` / `http://localhost:3000`).
4. **Storage Signed URL Expiration**: Image uploads stored with signed URLs must ensure expiration windows (e.g. 1 year) or use public bucket access for scan history thumbnails.

---

## 📌 Summary Recommendation
The frontend codebase is well-structured, clean, and highly functional. The TypeScript interfaces, route structure, and ML profiling logic are fully established. When implementing the backend, maintain the existing data contracts (`ScanResult`, `WeatherData`, `Database` schema) to ensure seamless integration without disrupting the UI.
