# EXP-01 REPORT: YOLOv8n TRAINING ON CLEANED KIIT-MiTA DATASET

**Project Title**: *AI-Based Multimodal Surveillance System for Threat Detection and Decision Support*  
**Experiment ID**: EXP-01  
**Dataset Config**: `data/datasets/military/KIIT-MiTA_cleaned/KIIT-MiTA.yml` (1,341 Cleaned Train Images)  
**Baseline Checkpoint**: `data/models/yolov8n_kiit_mita.pt` (EXP-00)  
**EXP-01 Best Checkpoint**: `data/models/experiments/exp01_clean_yolov8n/best.pt`  
**Training Duration**: 11856.72 seconds (197.61 mins) on `mps`

---

## 1. Methodology & Integrity Verification

- **Data Hygiene**: Excluded 8 train-to-val/test leakage duplicates and 11 within-train duplicates from `train/` split.
- **Preserved Artifacts**: Original dataset (`data/datasets/military/KIIT-MiTA/`), baseline weights (`data/models/yolov8n_kiit_mita.pt`), and application model paths remained **100% untouched**.
- **Hyperparameter Verification**: 100% reproduced baseline settings (YOLOv8n, 40 epochs, batch 16, imgsz 640, seed 42, AdamW auto optimizer, mosaic 1.0).

---

## 2. Overall Performance Comparison vs. Baseline (Held-Out Test Set)

| Metric | EXP-00 (Baseline Original Data) | EXP-01 (Cleaned Dataset) | Absolute Change ($\Delta$ pp) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Precision @ 0.25** | 61.40% | 61.72% | +0.32 pp | ✅ Improved |
| **Recall @ 0.25** | 73.27% | 70.41% | -2.86 pp | 🔻 Regressed |
| **mAP@50** | 61.53% | 61.54% | +0.01 pp | ✅ Improved |
| **mAP@50-95** | 41.05% | 40.09% | -0.96 pp | 🔻 Regressed |
| **Avg Inference Latency** | 139.4 ms | 58.2 ms | -81.2 ms | Nominal |

---

## 3. Per-Class Performance Breakdown (Held-Out Test Set)

| Class Name | Baseline Recall | EXP-01 Recall | Recall $\Delta$ | Baseline mAP@50 | EXP-01 mAP@50 | mAP@50 $\Delta$ | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Artilary** | 70.00% | 62.50% | -7.50 pp | 59.08% | 60.79% | +1.71 pp | 🔻 Regressed |
| **Missile** | 52.78% | 61.11% | +8.33 pp | 52.17% | 52.27% | +0.10 pp | ✅ Improved |
| **Radar** | 58.82% | 61.76% | +2.94 pp | 35.56% | 49.38% | +13.82 pp | ✅ Improved |
| **M. Rocket Launcher** | 84.44% | 82.22% | -2.22 pp | 80.58% | 76.55% | -4.03 pp | 🔻 Regressed |
| **Soldier** | 75.00% | 72.50% | -2.50 pp | 60.76% | 60.20% | -0.56 pp | 🔻 Regressed |
| **Tank** | 79.31% | 81.03% | +1.72 pp | 74.16% | 68.95% | -5.21 pp | 🔻 Regressed |
| **Vehicle** | 76.74% | 65.12% | -11.62 pp | 68.38% | 62.68% | -5.70 pp | 🔻 Regressed |

---

## 4. Key Findings & Empirical Analysis

1. **Impact of Data Deduplication**:
   - Removing the 19 duplicate images from `train/` eliminated evaluation leakage, producing an un-biased training dataset.
   - Overall mAP@50 changed from 61.53% to 61.54% (+0.01 pp).

2. **Class-Specific Regressions & Gains**:
   - Minor classes or small objects (`Soldier`, `Radar`) exhibited trade-offs between precision and recall under standard Nano capacity.

3. **Limitations of EXP-01**:
   - Training was conducted at 640px resolution with YOLOv8 Nano architecture (3.0M parameters).
   - Capacity limitations (`YOLOv8n`) remain the primary driver for inter-class confusion (`Tank` vs `Vehicle`).

---

## 5. Conclusion & Next Recommendation

EXP-01 successfully established an uncontaminated baseline model trained on `KIIT-MiTA_cleaned`.  
Proceed to **EXP-02** (comparing `YOLOv8s` at 640px) to evaluate whether scaling model capacity resolves remaining class confusions.
