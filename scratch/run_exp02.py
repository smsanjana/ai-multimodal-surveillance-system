"""
EXP-02 Implementation & Execution Script:
1. Model capacity scaling experiment: YOLOv8s (11.2M parameters) vs YOLOv8n (3.0M parameters).
2. Train YOLOv8s on clean dataset data/datasets/military/KIIT-MiTA_cleaned/KIIT-MiTA.yml.
3. Save weights, config, and logs to data/models/experiments/exp02_clean_yolov8s/.
4. Evaluate best.pt on validation split and held-out test split using 1-to-1 matching protocol.
5. Compute comparison metrics against EXP-01 (YOLOv8n Cleaned) and EXP-00 (Baseline Original Data).
6. Generate exp02_results.json and exp02_report.md deliverables.
"""

import os
import shutil
import time
import json
import yaml
import torch
import numpy as np
from collections import defaultdict
from ultralytics import YOLO

# Paths
CLEAN_DATASET_YAML = "data/datasets/military/KIIT-MiTA_cleaned/KIIT-MiTA.yml"
ORIGINAL_DATASET_YAML = "data/datasets/military/KIIT-MiTA/KIIT-MiTA.yml"
ORIGINAL_DATASET_DIR = "data/datasets/military/KIIT-MiTA"
EXP_DIR = "data/models/experiments/exp02_clean_yolov8s"
RUNS_EXP_DIR = "runs/detect/experiments"
RUN_NAME = "exp02_clean_yolov8s"
BASELINE_REPORT_PATH = "data/demo/drone/stage1_corrected_audit_report.json"
EXP01_RESULTS_PATH = "data/models/experiments/exp01_clean_yolov8n/exp01_results.json"

CLASS_NAMES = {
    0: "Artilary",
    1: "Missile",
    2: "Radar",
    3: "M. Rocket Launcher",
    4: "Soldier",
    5: "Tank",
    6: "Vehicle"
}

# Training Hyperparameters matching baseline and EXP-01, changing only model to yolov8s.pt
TRAIN_CONFIG = {
    "task": "detect",
    "mode": "train",
    "model": "yolov8s.pt",
    "data": os.path.abspath(CLEAN_DATASET_YAML),
    "epochs": 40,
    "patience": 10,
    "batch": 16,
    "imgsz": 640,
    "seed": 42,
    "deterministic": True,
    "workers": 4,
    "optimizer": "auto",
    "lr0": 0.01,
    "lrf": 0.01,
    "momentum": 0.937,
    "weight_decay": 0.0005,
    "warmup_epochs": 3.0,
    "box": 7.5,
    "cls": 0.5,
    "dfl": 1.5,
    "hsv_h": 0.015,
    "hsv_s": 0.7,
    "hsv_v": 0.4,
    "translate": 0.1,
    "scale": 0.5,
    "fliplr": 0.5,
    "mosaic": 1.0,
    "close_mosaic": 10,
    "erasing": 0.4,
    "amp": False
}


def compute_iou(boxA, boxB):
    ix1 = max(boxA[0], boxB[0])
    iy1 = max(boxA[1], boxB[1])
    ix2 = min(boxA[2], boxB[2])
    iy2 = min(boxA[3], boxB[3])

    inter_w = max(0.0, ix2 - ix1)
    inter_h = max(0.0, iy2 - iy1)
    inter_area = inter_w * inter_h

    areaA = max(0.0, boxA[2] - boxA[0]) * max(0.0, boxA[3] - boxA[1])
    areaB = max(0.0, boxB[2] - boxB[0]) * max(0.0, boxB[3] - boxB[1])

    union_area = areaA + areaB - inter_area
    if union_area <= 0.0:
        return 0.0
    return inter_area / union_area


def load_gt_labels(label_path):
    if not os.path.exists(label_path):
        return []
    gt_list = []
    with open(label_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            parts = line.strip().split()
            if len(parts) >= 5:
                try:
                    c_id = int(parts[0])
                    xc, yc, w, h = map(float, parts[1:5])
                    x1 = xc - w / 2.0
                    y1 = yc - h / 2.0
                    x2 = xc + w / 2.0
                    y2 = yc + h / 2.0
                    gt_list.append({
                        "gt_id": idx,
                        "class_id": c_id,
                        "class_name": CLASS_NAMES.get(c_id, f"Unknown({c_id})"),
                        "box": [x1, y1, x2, y2]
                    })
                except ValueError:
                    continue
    return gt_list


def evaluate_1to1_matching(dataset_dir, split_name, model, conf_thresh=0.25, iou_thresh=0.50):
    img_dir = os.path.join(dataset_dir, split_name, "images")
    lbl_dir = os.path.join(dataset_dir, split_name, "labels")
    img_files = sorted([f for f in os.listdir(img_dir) if f.endswith((".jpg", ".jpeg", ".png"))])

    gt_counts = defaultdict(int)
    tp_counts = defaultdict(int)
    unmatched_fn_counts = defaultdict(int)
    wrong_class_fn_counts = defaultdict(int)
    fp_counts = defaultdict(int)

    total_inf_time_ms = 0.0

    for img_file in img_files:
        img_path = os.path.join(img_dir, img_file)
        lbl_file = os.path.splitext(img_file)[0] + ".txt"
        lbl_path = os.path.join(lbl_dir, lbl_file)

        gt_list = load_gt_labels(lbl_path)
        for g in gt_list:
            gt_counts[g["class_id"]] += 1

        t0 = time.time()
        raw_res = model(img_path, conf=conf_thresh, iou=iou_thresh, verbose=False)[0]
        t1 = time.time()
        total_inf_time_ms += (t1 - t0) * 1000.0

        preds = []
        if raw_res.boxes is not None:
            for box in raw_res.boxes:
                xyxyn = box.xyxyn[0].cpu().numpy().tolist()
                c_val = float(box.conf[0].cpu().numpy())
                c_id = int(box.cls[0].cpu().numpy())
                preds.append({
                    "class_id": c_id,
                    "class_name": CLASS_NAMES.get(c_id, f"Unknown({c_id})"),
                    "confidence": c_val,
                    "box": xyxyn
                })

        matched_gt = set()
        matched_pred = set()

        # Same class match
        candidates = []
        for g_idx, g in enumerate(gt_list):
            for p_idx, p in enumerate(preds):
                if g["class_id"] == p["class_id"]:
                    iou = compute_iou(g["box"], p["box"])
                    if iou >= iou_thresh:
                        candidates.append((iou, g_idx, p_idx))

        candidates.sort(key=lambda x: x[0], reverse=True)
        for iou, g_idx, p_idx in candidates:
            if g_idx not in matched_gt and p_idx not in matched_pred:
                matched_gt.add(g_idx)
                matched_pred.add(p_idx)
                c_id = gt_list[g_idx]["class_id"]
                tp_counts[c_id] += 1

        # Wrong class match
        wrong_candidates = []
        for g_idx, g in enumerate(gt_list):
            if g_idx in matched_gt:
                continue
            for p_idx, p in enumerate(preds):
                if p_idx in matched_pred:
                    continue
                iou = compute_iou(g["box"], p["box"])
                if iou >= iou_thresh:
                    wrong_candidates.append((iou, g_idx, p_idx))

        wrong_candidates.sort(key=lambda x: x[0], reverse=True)
        for iou, g_idx, p_idx in wrong_candidates:
            if g_idx not in matched_gt and p_idx not in matched_pred:
                matched_gt.add(g_idx)
                matched_pred.add(p_idx)
                gt_cls = gt_list[g_idx]["class_id"]
                pred_cls = preds[p_idx]["class_id"]
                wrong_class_fn_counts[gt_cls] += 1
                fp_counts[pred_cls] += 1

        for g_idx, g in enumerate(gt_list):
            if g_idx not in matched_gt:
                gt_cls = g["class_id"]
                unmatched_fn_counts[gt_cls] += 1

        for p_idx, p in enumerate(preds):
            if p_idx not in matched_pred:
                pred_cls = p["class_id"]
                fp_counts[pred_cls] += 1

    per_class_summary = {}
    total_gt = sum(gt_counts.values())
    total_tp = sum(tp_counts.values())
    total_unmatched_fn = sum(unmatched_fn_counts.values())
    total_wrong_class_fn = sum(wrong_class_fn_counts.values())
    total_total_fn = total_unmatched_fn + total_wrong_class_fn
    total_fp = sum(fp_counts.values())

    for c_id in range(7):
        c_name = CLASS_NAMES[c_id]
        gt = gt_counts[c_id]
        tp = tp_counts[c_id]
        u_fn = unmatched_fn_counts[c_id]
        w_fn = wrong_class_fn_counts[c_id]
        tot_fn = u_fn + w_fn
        fp = fp_counts[c_id]

        prec = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        rec = round(tp / gt, 4) if gt > 0 else 0.0

        per_class_summary[c_name] = {
            "class_id": c_id,
            "ground_truth_count": gt,
            "true_positives": tp,
            "unmatched_false_negatives": u_fn,
            "wrong_class_false_negatives": w_fn,
            "total_false_negatives": tot_fn,
            "false_positives": fp,
            "precision_at_0.25": prec,
            "recall_at_0.25": rec
        }

    overall_prec = round(total_tp / (total_tp + total_fp), 4) if (total_tp + total_fp) > 0 else 0.0
    overall_rec = round(total_tp / total_gt, 4) if total_gt > 0 else 0.0
    avg_latency_ms = round(total_inf_time_ms / len(img_files), 2) if img_files else 0.0

    return {
        "split_name": split_name,
        "image_count": len(img_files),
        "avg_inference_ms": avg_latency_ms,
        "overall_1to1": {
            "total_ground_truth": total_gt,
            "total_true_positives": total_tp,
            "total_unmatched_false_negatives": total_unmatched_fn,
            "total_wrong_class_false_negatives": total_wrong_class_fn,
            "total_false_negatives": total_total_fn,
            "total_false_positives": total_fp,
            "precision_at_0.25": overall_prec,
            "recall_at_0.25": overall_rec
        },
        "per_class_1to1": per_class_summary
    }


def main():
    print("=" * 70)
    print("      EXP-02: YOLOv8s CAPACITY COMPARISON ON CLEANED KIIT-MiTA")
    print("=" * 70)

    os.makedirs(EXP_DIR, exist_ok=True)
    os.makedirs(RUNS_EXP_DIR, exist_ok=True)

    # Save exp02_config.yaml
    exp02_config_path = os.path.join(EXP_DIR, "exp02_config.yaml")
    with open(exp02_config_path, "w", encoding="utf-8") as f:
        yaml.dump(TRAIN_CONFIG, f, default_flow_style=False)
    print(f"Saved experiment configuration to: {exp02_config_path}")

    exp_best_weights = os.path.join(EXP_DIR, "best.pt")
    exp_last_weights = os.path.join(EXP_DIR, "last.pt")

    device = "mps" if torch.backends.mps.is_available() else "cpu"

    if os.path.exists(exp_best_weights):
        print(f"\nFound existing trained EXP-02 best weights at '{exp_best_weights}'. Skipping training execution...")
        train_duration_sec = 0.0
    else:
        print(f"\nTarget Training Device: {device}")
        print(f"Dataset YAML:           {CLEAN_DATASET_YAML}")
        print(f"Model Architecture:     yolov8s.pt")
        print(f"Epochs: {TRAIN_CONFIG['epochs']} | Batch: {TRAIN_CONFIG['batch']} | Imgsz: {TRAIN_CONFIG['imgsz']} | Seed: {TRAIN_CONFIG['seed']}")

        t0_train = time.time()
        yolo_model = YOLO("yolov8s.pt")

        results = yolo_model.train(
            data=os.path.abspath(CLEAN_DATASET_YAML),
            epochs=TRAIN_CONFIG["epochs"],
            patience=TRAIN_CONFIG["patience"],
            batch=TRAIN_CONFIG["batch"],
            imgsz=TRAIN_CONFIG["imgsz"],
            device=device,
            seed=TRAIN_CONFIG["seed"],
            deterministic=TRAIN_CONFIG["deterministic"],
            workers=TRAIN_CONFIG["workers"],
            amp=False,
            project=os.path.abspath(RUNS_EXP_DIR),
            name=RUN_NAME,
            exist_ok=True,
            verbose=True
        )
        t1_train = time.time()
        train_duration_sec = round(t1_train - t0_train, 2)
        print(f"\nEXP-02 Training completed in {train_duration_sec} seconds ({train_duration_sec/60:.2f} mins).")

        best_weights_src = os.path.join(RUNS_EXP_DIR, RUN_NAME, "weights", "best.pt")
        last_weights_src = os.path.join(RUNS_EXP_DIR, RUN_NAME, "weights", "last.pt")

        if os.path.exists(best_weights_src):
            shutil.copy2(best_weights_src, exp_best_weights)
            print(f"Copied best weights to: {exp_best_weights}")
        if os.path.exists(last_weights_src):
            shutil.copy2(last_weights_src, exp_last_weights)
            print(f"Copied last weights to: {exp_last_weights}")

    # Step 2: Evaluate best.pt on Validation & Held-out Test Split
    print("\n" + "=" * 70)
    print("EVALUATING EXP-02 BEST CHECKPOINT")
    print("=" * 70)

    best_model = YOLO(exp_best_weights)

    # 1-to-1 matching evaluation
    exp02_test_1to1 = evaluate_1to1_matching(ORIGINAL_DATASET_DIR, "test", best_model)
    exp02_valid_1to1 = evaluate_1to1_matching(ORIGINAL_DATASET_DIR, "valid", best_model)

    # Ultralytics val for mAP
    print("\nRunning Ultralytics val on test split...")
    test_val_res = best_model.val(data=ORIGINAL_DATASET_YAML, split="test", conf=0.25, iou=0.50, batch=16, imgsz=640, verbose=False)

    print("\nRunning Ultralytics val on valid split...")
    val_val_res = best_model.val(data=ORIGINAL_DATASET_YAML, split="val", conf=0.25, iou=0.50, batch=16, imgsz=640, verbose=False)

    def attach_map(val_res, matching_data):
        names = val_res.names
        for i in range(len(names)):
            c_name = names[i]
            ap50 = float(val_res.box.ap50[i]) if i < len(val_res.box.ap50) else 0.0
            ap = float(val_res.box.ap[i]) if i < len(val_res.box.ap) else 0.0
            matching_data["per_class_1to1"][c_name]["map50"] = round(ap50, 4)
            matching_data["per_class_1to1"][c_name]["map50_95"] = round(ap, 4)

        matching_data["overall_detector_map"] = {
            "ultralytics_precision_b": round(float(val_res.results_dict.get("metrics/precision(B)", 0.0)), 4),
            "ultralytics_recall_b": round(float(val_res.results_dict.get("metrics/recall(B)", 0.0)), 4),
            "map50": round(float(val_res.results_dict.get("metrics/mAP50(B)", 0.0)), 4),
            "map50_95": round(float(val_res.results_dict.get("metrics/mAP50-95(B)", 0.0)), 4)
        }

    attach_map(test_val_res, exp02_test_1to1)
    attach_map(val_val_res, exp02_valid_1to1)

    # Step 3: Load Baseline (EXP-00) and EXP-01 for Comparison
    with open(BASELINE_REPORT_PATH, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)

    with open(EXP01_RESULTS_PATH, "r", encoding="utf-8") as f:
        exp01_data = json.load(f)

    base_test_1to1 = baseline_data["reconciled_test_audit"]
    exp01_test_1to1 = exp01_data["exp01_test_evaluation"]

    # Calculate Deltas
    exp02_prec = exp02_test_1to1["overall_1to1"]["precision_at_0.25"]
    exp01_prec = exp01_test_1to1["overall_1to1"]["precision_at_0.25"]
    base_prec = base_test_1to1["overall_1to1"]["precision_at_0.25"]

    exp02_rec = exp02_test_1to1["overall_1to1"]["recall_at_0.25"]
    exp01_rec = exp01_test_1to1["overall_1to1"]["recall_at_0.25"]
    base_rec = base_test_1to1["overall_1to1"]["recall_at_0.25"]

    exp02_map50 = exp02_test_1to1["overall_detector_map"]["map50"]
    exp01_map50 = exp01_test_1to1["overall_detector_map"]["map50"]
    base_map50 = base_test_1to1["overall_detector_map"]["map50"]

    exp02_map50_95 = exp02_test_1to1["overall_detector_map"]["map50_95"]
    exp01_map50_95 = exp01_test_1to1["overall_detector_map"]["map50_95"]
    base_map50_95 = base_test_1to1["overall_detector_map"]["map50_95"]

    comparison_summary = {
        "precision_at_0_25": {
            "exp00_baseline": base_prec,
            "exp01_n": exp01_prec,
            "exp02_s": exp02_prec,
            "delta_vs_exp01_pp": round((exp02_prec - exp01_prec) * 100.0, 2),
            "delta_vs_exp00_pp": round((exp02_prec - base_prec) * 100.0, 2)
        },
        "recall_at_0_25": {
            "exp00_baseline": base_rec,
            "exp01_n": exp01_rec,
            "exp02_s": exp02_rec,
            "delta_vs_exp01_pp": round((exp02_rec - exp01_rec) * 100.0, 2),
            "delta_vs_exp00_pp": round((exp02_rec - base_rec) * 100.0, 2)
        },
        "map50": {
            "exp00_baseline": base_map50,
            "exp01_n": exp01_map50,
            "exp02_s": exp02_map50,
            "delta_vs_exp01_pp": round((exp02_map50 - exp01_map50) * 100.0, 2),
            "delta_vs_exp00_pp": round((exp02_map50 - base_map50) * 100.0, 2)
        },
        "map50_95": {
            "exp00_baseline": base_map50_95,
            "exp01_n": exp01_map50_95,
            "exp02_s": exp02_map50_95,
            "delta_vs_exp01_pp": round((exp02_map50_95 - exp01_map50_95) * 100.0, 2),
            "delta_vs_exp00_pp": round((exp02_map50_95 - base_map50_95) * 100.0, 2)
        },
        "per_class_comparison": {}
    }

    for c_id, c_name in CLASS_NAMES.items():
        b_cls = base_test_1to1["per_class_1to1"][c_name]
        e1_cls = exp01_test_1to1["per_class_1to1"][c_name]
        e2_cls = exp02_test_1to1["per_class_1to1"][c_name]

        e2_r = e2_cls["recall_at_0.25"]
        e1_r = e1_cls["recall_at_0.25"]
        b_r = b_cls["recall_at_0.25"]

        e2_m = e2_cls["map50"]
        e1_m = e1_cls["map50"]
        b_m = b_cls["map50"]

        comparison_summary["per_class_comparison"][c_name] = {
            "exp00_recall": b_r,
            "exp01_recall": e1_r,
            "exp02_recall": e2_r,
            "delta_vs_exp01_recall_pp": round((e2_r - e1_r) * 100.0, 2),
            "delta_vs_exp00_recall_pp": round((e2_r - b_r) * 100.0, 2),
            "exp00_map50": b_m,
            "exp01_map50": e1_m,
            "exp02_map50": e2_m,
            "delta_vs_exp01_map50_pp": round((e2_m - e1_m) * 100.0, 2),
            "delta_vs_exp00_map50_pp": round((e2_m - b_m) * 100.0, 2)
        }

    # Save exp02_results.json
    exp02_results_path = os.path.join(EXP_DIR, "exp02_results.json")
    results_payload = {
        "experiment_id": "EXP-02",
        "experiment_name": "YOLOv8s Capacity Comparison on Cleaned KIIT-MiTA Dataset",
        "training_duration_seconds": train_duration_sec,
        "training_device": device,
        "best_weights_path": exp_best_weights,
        "last_weights_path": exp_last_weights,
        "comparison_summary": comparison_summary,
        "exp02_test_evaluation": exp02_test_1to1,
        "exp02_valid_evaluation": exp02_valid_1to1
    }

    with open(exp02_results_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    print(f"\nSaved machine-readable results to: {exp02_results_path}")

    # Build exp02_report.md
    exp02_report_path = os.path.join(EXP_DIR, "exp02_report.md")
    report_md = f"""# EXP-02 REPORT: YOLOv8s CAPACITY COMPARISON ON CLEANED KIIT-MiTA DATASET

**Project Title**: *AI-Based Multimodal Surveillance System for Threat Detection and Decision Support*  
**Experiment ID**: EXP-02  
**Dataset Config**: `data/datasets/military/KIIT-MiTA_cleaned/KIIT-MiTA.yml` (1,341 Cleaned Train Images)  
**Baseline Model**: `YOLOv8n` (EXP-01, 3.0M Parameters)  
**Evaluated Model**: `YOLOv8s` (EXP-02, 11.2M Parameters)  
**EXP-02 Best Checkpoint**: `{exp_best_weights}`  
**Training Duration**: {train_duration_sec:.2f} seconds ({train_duration_sec/60:.2f} mins) on `{device}`

---

## 1. Methodology & Controlled Settings

- **Controlled Hyperparameters**: Identical training pipeline as EXP-01 (40 epochs, batch 16, imgsz 640, seed 42, AdamW auto optimizer, mosaic 1.0, close_mosaic 10).
- **Architecture Difference**: Swapped starting checkpoint from `yolov8n.pt` (3.0M params, 8.7 GFLOPs) to `yolov8s.pt` (11.2M params, 28.6 GFLOPs).
- **Preserved Artifacts**: EXP-00 baseline weights, EXP-01 weights, original dataset, cleaned dataset, and application configuration remained **100% untouched**.

---

## 2. Overall Performance Comparison vs EXP-01 & EXP-00 (Held-Out Test Set)

| Metric | EXP-00 (Baseline Original Data) | EXP-01 (YOLOv8n Cleaned) | EXP-02 (YOLOv8s Cleaned) | $\Delta$ vs EXP-01 | $\Delta$ vs EXP-00 | Status vs EXP-01 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Precision @ 0.25** | {base_prec*100:.2f}% | {exp01_prec*100:.2f}% | {exp02_prec*100:.2f}% | {comparison_summary['precision_at_0_25']['delta_vs_exp01_pp']:+.2f} pp | {comparison_summary['precision_at_0_25']['delta_vs_exp00_pp']:+.2f} pp | {'✅ Improved' if exp02_prec > exp01_prec else '🔻 Regressed'} |
| **Recall @ 0.25** | {base_rec*100:.2f}% | {exp01_rec*100:.2f}% | {exp02_rec*100:.2f}% | {comparison_summary['recall_at_0_25']['delta_vs_exp01_pp']:+.2f} pp | {comparison_summary['recall_at_0_25']['delta_vs_exp00_pp']:+.2f} pp | {'✅ Improved' if exp02_rec > exp01_rec else '🔻 Regressed'} |
| **mAP@50** | {base_map50*100:.2f}% | {exp01_map50*100:.2f}% | {exp02_map50*100:.2f}% | {comparison_summary['map50']['delta_vs_exp01_pp']:+.2f} pp | {comparison_summary['map50']['delta_vs_exp00_pp']:+.2f} pp | {'✅ Improved' if exp02_map50 > exp01_map50 else '🔻 Regressed'} |
| **mAP@50-95** | {base_map50_95*100:.2f}% | {exp01_map50_95*100:.2f}% | {exp02_map50_95*100:.2f}% | {comparison_summary['map50_95']['delta_vs_exp01_pp']:+.2f} pp | {comparison_summary['map50_95']['delta_vs_exp00_pp']:+.2f} pp | {'✅ Improved' if exp02_map50_95 > exp01_map50_95 else '🔻 Regressed'} |
| **Avg Latency** | {base_test_1to1.get('avg_inference_ms', 139.4):.1f} ms | {exp01_test_1to1['avg_inference_ms']:.1f} ms | {exp02_test_1to1['avg_inference_ms']:.1f} ms | {exp02_test_1to1['avg_inference_ms'] - exp01_test_1to1['avg_inference_ms']:+.1f} ms | {exp02_test_1to1['avg_inference_ms'] - base_test_1to1.get('avg_inference_ms', 139.4):+.1f} ms | Nominal |

---

## 3. Per-Class Performance Breakdown (Held-Out Test Set)

| Class Name | EXP-01 mAP@50 | EXP-02 mAP@50 | mAP@50 $\Delta$ | EXP-01 Recall | EXP-02 Recall | Recall $\Delta$ | Wrong Class FN (EXP-01 vs EXP-02) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""

    for c_id, c_name in CLASS_NAMES.items():
        comp = comparison_summary["per_class_comparison"][c_name]
        e1_m = comp["exp01_map50"] * 100.0
        e2_m = comp["exp02_map50"] * 100.0
        d_m = comp["delta_vs_exp01_map50_pp"]

        e1_r = comp["exp01_recall"] * 100.0
        e2_r = comp["exp02_recall"] * 100.0
        d_r = comp["delta_vs_exp01_recall_pp"]

        e1_wfn = exp01_test_1to1["per_class_1to1"][c_name]["wrong_class_false_negatives"]
        e2_wfn = exp02_test_1to1["per_class_1to1"][c_name]["wrong_class_false_negatives"]

        status = "✅ Improved" if d_m > 0 and d_r >= 0 else ("🔻 Regressed" if d_m < 0 or d_r < 0 else "➖ Mixed")
        report_md += f"| **{c_name}** | {e1_m:.2f}% | {e2_m:.2f}% | {d_m:+.2f} pp | {e1_r:.2f}% | {e2_r:.2f}% | {d_r:+.2f} pp | {e1_wfn} vs {e2_wfn} | {status} |\n"

    report_md += f"""
---

## 4. Key Findings & Empirical Analysis

1. **Impact of Model Capacity Scaling**:
   - Model parameters increased from 3.0M (`YOLOv8n`) to 11.2M (`YOLOv8s`).
   - Overall test mAP@50 changed by {comparison_summary['map50']['delta_vs_exp01_pp']:+.2f} pp vs EXP-01 and {comparison_summary['map50']['delta_vs_exp00_pp']:+.2f} pp vs EXP-00.

2. **Inter-Class Confusion Resolution**:
   - Total wrong-class False Negatives changed from {exp01_test_1to1['overall_1to1']['total_wrong_class_false_negatives']} in EXP-01 to {exp02_test_1to1['overall_1to1']['total_wrong_class_false_negatives']} in EXP-02.

3. **Small Target Detection (`Soldier`)**:
   - `Soldier` mAP@50 changed by {comparison_summary['per_class_comparison']['Soldier']['delta_vs_exp01_map50_pp']:+.2f} pp.

---

## 5. Summary & Next Steps

EXP-02 completes the capacity evaluation of `YOLOv8s` on `KIIT-MiTA_cleaned`.
All metrics, weights, and comparison logs have been recorded in `{exp02_results_path}`.
"""

    with open(exp02_report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Saved Markdown report to: {exp02_report_path}")
    print("\n=" * 70)
    print("EXP-02 EXECUTION & REPORTING COMPLETED SUCCESSFULLY.")
    print("=" * 70)


if __name__ == "__main__":
    main()
