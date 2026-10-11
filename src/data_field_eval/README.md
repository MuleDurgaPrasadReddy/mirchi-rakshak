# Mirchi Rakshak — Independent Field Evaluation Dataset

## Overview
This repository contains the independent field-evaluation dataset structure for real-world out-of-distribution pathology validation of the **Mirchi Rakshak** classification models.

- **Isolation Rule:** All images in `src/data_field_eval/` are strictly isolated from `src/data_clean` (Train, Validation, and Test splits).
- **Target Coverage:** 50–100 independent images per class (prioritizing `Chilli__Leaf_Curl_Virus` and `Chilli__Damping_Off`).

---

## 8 Official Disease Classes
1. `Chilli __Whitefly`
2. `Chilli __Yellowish`
3. `Chilli__Anthracnos`
4. `Chilli__Damping_Off`
5. `Chilli__Leaf_Curl_Virus`
6. `Chilli__Leaf_Spot`
7. `Chilli__Veinal_Mottle_Virus`
8. `Chilli___healthy`

---

## Manifest Schema (`field_eval_manifest.csv`)
- `image_id`: Unique ID (e.g. `fe_leaf_curl_001`)
- `filename`: Local image file name
- `class_label`: Official disease class name
- `image_source`: Field source / collection origin
- `capture_group`: Camera session / physical group ID (for group-level deduplication)
- `host_verified`: Host plant identity confirmation (`Yes` / `No` / `Pending`)
- `disease_verified`: Pathology symptom confirmation (`Yes` / `No` / `Pending`)
- `verification_status`: Status (`AWAITING_VERIFICATION`, `APPROVED_FIELD_EVAL`, `EXCLUDED`)
- `sha256`: Cryptographic hash
- `dhash`: Perceptual fingerprint
- `review_notes`: Expert pathology notes
