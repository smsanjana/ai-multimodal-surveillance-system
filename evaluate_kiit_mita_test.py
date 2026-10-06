"""
Temporary Diagnostic Script: Evaluate KIIT-MiTA YOLO model on test split sample.
Model: data/models/yolov8n_kiit_mita.pt
Dataset: KIIT-MiTA test split (first 20 images sorted alphabetically)
Output: data/demo/drone/kiit_mita_test_diagnostic.json + clean terminal summary.
"""

import os
import sys
import time
import json
from collections import defaultdict
from typing import List, Dict, Any, Tuple
import numpy as np

# Ground Truth Class Mapping
CLASS_NAMES = {
    0: "Artilary",
    1: "Missile",
    2: "Radar",
    3: "M. Rocket Launcher",
    4: "Soldier",
    5: "Tank",
    6: "Vehicle"
}

MODEL_PATH = "data/models/yolov8n_kiit_mita.pt"
TEST_IMG_DIR = "data/datasets/military/KIIT-MiTA/test/images"
TEST_LBL_DIR = "data/datasets/military/KIIT-MiTA/test/labels"
JSON_OUTPUT_PATH = "data/demo/drone/kiit_mita_test_diagnostic.json"
CONF_THRESHOLDS = [0.25, 0.10, 0.05]
SAMPLE_SIZE = 20


def compute_iou(boxA: List[float], boxB: List[float]) -> float:
    """Computes IoU between two normalized bounding boxes [x1, y1, x2, y2]."""
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


def load_ground_truth(label_path: str) -> List[Dict[str, Any]]:
    """Reads YOLO ground truth .txt label file: class_id xc yc w h."""
    if not os.path.exists(label_path):
        return []
    
    gt_boxes = []
    with open(label_path, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f):
            parts = line.strip().split()
            if len(parts) >= 5:
                try:
                    c_id = int(parts[0])
                    xc, yc, w, h = map(float, parts[1:5])
                    x1 = xc - w / 2.0
                    y1 = yc - h / 2.0
                    x2 = xc + w / 2.0
                    y2 = yc + h / 2.0
                    gt_boxes.append({
                        "gt_id": line_idx,
                        "class_id": c_id,
                        "class_name": CLASS_NAMES.get(c_id, f"Unknown({c_id})"),
                        "box": [x1, y1, x2, y2]
                    })
                except ValueError:
                    continue
    return gt_boxes


def evaluate_image_predictions(
    gt_list: List[Dict[str, Any]],
    raw_preds: List[Dict[str, Any]],
    conf_thresh: float
) -> Dict[str, Any]:
    """
    Evaluates predictions against GT for a single image at a specific confidence threshold.
    Matching logic:
    1. Filter predictions by conf >= conf_thresh
    2. Same-class IoU >= 0.5 matching -> True Positives
    3. Cross-class IoU >= 0.5 matching -> Wrong-Class Predictions
    4. Remaining unmatched GT -> Missed
    5. Remaining unmatched Pred -> Extra / False Positive
    """
    preds = [p for p in raw_preds if p["confidence"] >= conf_thresh]
    
    matched_gt = set()
    matched_pred = set()
    
    # 1. Match same class with IoU >= 0.5
    candidates = []
    for g_idx, g in enumerate(gt_list):
        for p_idx, p in enumerate(preds):
            if g["class_id"] == p["class_id"]:
                iou = compute_iou(g["box"], p["box"])
                if iou >= 0.5:
                    candidates.append((iou, g_idx, p_idx))
    
    # Sort candidates by highest IoU first
    candidates.sort(key=lambda x: x[0], reverse=True)
    
    tp_matches = []
    for iou, g_idx, p_idx in candidates:
        if g_idx not in matched_gt and p_idx not in matched_pred:
            matched_gt.add(g_idx)
            matched_pred.add(p_idx)
            tp_matches.append({
                "gt_class": gt_list[g_idx]["class_name"],
                "pred_class": preds[p_idx]["class_name"],
                "conf": preds[p_idx]["confidence"],
                "iou": round(iou, 4)
            })

    # 2. Match wrong-class with IoU >= 0.5
    wrong_candidates = []
    for g_idx, g in enumerate(gt_list):
        if g_idx in matched_gt:
            continue
        for p_idx, p in enumerate(preds):
            if p_idx in matched_pred:
                continue
            iou = compute_iou(g["box"], p["box"])
            if iou >= 0.5:
                wrong_candidates.append((iou, g_idx, p_idx))

    wrong_candidates.sort(key=lambda x: x[0], reverse=True)
    
    wrong_class_matches = []
    for iou, g_idx, p_idx in wrong_candidates:
        if g_idx not in matched_gt and p_idx not in matched_pred:
            matched_gt.add(g_idx)
            matched_pred.add(p_idx)
            wrong_class_matches.append({
                "gt_class": gt_list[g_idx]["class_name"],
                "pred_class": preds[p_idx]["class_name"],
                "conf": preds[p_idx]["confidence"],
                "iou": round(iou, 4)
            })

    # 3. Missed ground truths
    missed_gt = [gt_list[g_idx] for g_idx in range(len(gt_list)) if g_idx not in matched_gt]

    # 4. Extra predictions
    extra_preds = [preds[p_idx] for p_idx in range(len(preds)) if p_idx not in matched_pred]

    avg_conf = float(np.mean([p["confidence"] for p in preds])) if preds else 0.0

    pred_class_counts = defaultdict(int)
    for p in preds:
        pred_class_counts[p["class_name"]] += 1

    return {
        "conf_threshold": conf_thresh,
        "pred_count": len(preds),
        "pred_class_counts": dict(pred_class_counts),
        "tp_count": len(tp_matches),
        "wrong_class_count": len(wrong_class_matches),
        "missed_count": len(missed_gt),
        "extra_count": len(extra_preds),
        "avg_confidence": round(avg_conf, 4),
        "tp_matches": tp_matches,
        "wrong_class_matches": wrong_class_matches,
        "missed_gt": [{"class_name": g["class_name"], "box": [round(b, 4) for b in g["box"]]} for g in missed_gt],
        "extra_preds": [{"class_name": p["class_name"], "conf": p["confidence"], "box": [round(b, 4) for b in p["box"]]} for p in extra_preds]
    }


def main():
    print("=" * 70)
    print("      KIIT-MiTA YOLO MODEL DIAGNOSTIC EVALUATION")
    print("=" * 70)

    # Sanity checks
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Trained model file not found at '{MODEL_PATH}'. Aborting.")
        sys.exit(1)

    if not os.path.exists(TEST_IMG_DIR):
        print(f"ERROR: Test image directory not found at '{TEST_IMG_DIR}'. Aborting.")
        sys.exit(1)

    if not os.path.exists(TEST_LBL_DIR):
        print(f"ERROR: Test label directory not found at '{TEST_LBL_DIR}'. Aborting.")
        sys.exit(1)

    # Find and sort test images
    all_images = [f for f in os.listdir(TEST_IMG_DIR) if f.endswith(('.jpg', '.jpeg', '.png', '.JPG', '.PNG'))]
    all_images.sort()

    if not all_images:
        print(f"ERROR: No test images found in '{TEST_IMG_DIR}'. Aborting.")
        sys.exit(1)

    test_samples = all_images[:SAMPLE_SIZE]
    print(f"Loaded {len(test_samples)} deterministic test images for evaluation.")

    # Load YOLO Model
    try:
        from ultralytics import YOLO
        print(f"Loading model: {MODEL_PATH}...")
        model = YOLO(MODEL_PATH)
    except Exception as e:
        print(f"ERROR: Failed to load YOLO model: {e}")
        sys.exit(1)

    # Initialize summary containers
    results_by_threshold = {thresh: {"images": [], "overall": {}} for thresh in CONF_THRESHOLDS}

    # Evaluate each sample image
    total_inf_time = 0.0
    image_evaluations = []

    for idx, img_file in enumerate(test_samples, 1):
        img_path = os.path.join(TEST_IMG_DIR, img_file)
        lbl_file = os.path.splitext(img_file)[0] + ".txt"
        lbl_path = os.path.join(TEST_LBL_DIR, lbl_file)

        gt_list = load_ground_truth(lbl_path)
        gt_class_counts = defaultdict(int)
        for g in gt_list:
            gt_class_counts[g["class_name"]] += 1

        # Run inference (conf=0.01 to capture raw bounding boxes for post-thresholding)
        t0 = time.time()
        raw_res = model(img_path, conf=0.01, verbose=False)[0]
        t1 = time.time()
        inf_time_ms = round((t1 - t0) * 1000.0, 2)
        total_inf_time += inf_time_ms

        raw_preds = []
        if raw_res.boxes is not None:
            names = raw_res.names if hasattr(raw_res, "names") and raw_res.names else CLASS_NAMES
            for box in raw_res.boxes:
                xyxyn = box.xyxyn[0].cpu().numpy().tolist()
                conf_val = round(float(box.conf[0].cpu().numpy()), 4)
                cls_id = int(box.cls[0].cpu().numpy())
                cls_name = names.get(cls_id, CLASS_NAMES.get(cls_id, f"Unknown({cls_id})"))
                raw_preds.append({
                    "class_id": cls_id,
                    "class_name": cls_name,
                    "confidence": conf_val,
                    "box": xyxyn
                })

        img_eval = {
            "image_index": idx,
            "filename": img_file,
            "inference_time_ms": inf_time_ms,
            "gt_count": len(gt_list),
            "gt_class_counts": dict(gt_class_counts),
            "thresholds": {}
        }

        for thresh in CONF_THRESHOLDS:
            thresh_eval = evaluate_image_predictions(gt_list, raw_preds, thresh)
            img_eval["thresholds"][str(thresh)] = thresh_eval

        image_evaluations.append(img_eval)

    avg_inf_time = round(total_inf_time / len(test_samples), 2)

    # Compute overall statistics per threshold
    overall_summaries = {}
    for thresh in CONF_THRESHOLDS:
        t_key = str(thresh)
        tot_gt = 0
        tot_pred = 0
        tot_tp = 0
        tot_wrong = 0
        tot_missed = 0
        tot_extra = 0

        cls_gt = defaultdict(int)
        cls_pred = defaultdict(int)
        cls_tp = defaultdict(int)
        cls_wrong = defaultdict(int)
        cls_missed = defaultdict(int)
        cls_extra = defaultdict(int)
        all_confs = []

        for img_e in image_evaluations:
            tot_gt += img_e["gt_count"]
            for c_name, count in img_e["gt_class_counts"].items():
                cls_gt[c_name] += count

            t_res = img_e["thresholds"][t_key]
            tot_pred += t_res["pred_count"]
            tot_tp += t_res["tp_count"]
            tot_wrong += t_res["wrong_class_count"]
            tot_missed += t_res["missed_count"]
            tot_extra += t_res["extra_count"]

            for c_name, count in t_res["pred_class_counts"].items():
                cls_pred[c_name] += count

            for m in t_res["tp_matches"]:
                cls_tp[m["gt_class"]] += 1
                all_confs.append(m["conf"])

            for m in t_res["wrong_class_matches"]:
                cls_wrong[m["gt_class"]] += 1

            for m in t_res["missed_gt"]:
                cls_missed[m["class_name"]] += 1

            for ex in t_res["extra_preds"]:
                cls_extra[ex["class_name"]] += 1
                all_confs.append(ex["conf"])

        avg_conf_overall = round(float(np.mean(all_confs)), 4) if all_confs else 0.0

        overall_summaries[t_key] = {
            "total_gt_objects": tot_gt,
            "total_predicted_objects": tot_pred,
            "matched_true_positives": tot_tp,
            "wrong_class_predictions": tot_wrong,
            "missed_objects": tot_missed,
            "extra_predictions": tot_extra,
            "overall_avg_confidence": avg_conf_overall,
            "class_wise": {
                c_name: {
                    "gt_count": cls_gt[c_name],
                    "predicted_count": cls_pred[c_name],
                    "true_positives": cls_tp[c_name],
                    "missed_count": cls_missed[c_name],
                    "wrong_class_count": cls_wrong[c_name],
                    "extra_count": cls_extra[c_name]
                }
                for c_name in CLASS_NAMES.values()
            }
        }

    # Prepare JSON Output Payload
    json_output = {
        "model_path": MODEL_PATH,
        "sample_size": len(test_samples),
        "total_inference_time_ms": round(total_inf_time, 2),
        "average_inference_time_ms": avg_inf_time,
        "overall_by_threshold": overall_summaries,
        "per_image_evaluations": image_evaluations
    }

    os.makedirs(os.path.dirname(JSON_OUTPUT_PATH), exist_ok=True)
    with open(JSON_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2)

    print(f"\nSaved diagnostic JSON report to: {JSON_OUTPUT_PATH}")

    # Print Clean Terminal Summary (Easy to paste into ChatGPT)
    print("\n" + "=" * 70)
    print("                   TERMINAL SUMMARY REPORT")
    print("=" * 70)
    print(f"Model File:           {MODEL_PATH}")
    print(f"Evaluated Test Images: {len(test_samples)}")
    print(f"Average Inference:    {avg_inf_time} ms / image")

    for thresh in CONF_THRESHOLDS:
        t_key = str(thresh)
        ov = overall_summaries[t_key]
        print("\n" + "-" * 70)
        print(f"CONFIDENCE THRESHOLD: {thresh}")
        print("-" * 70)
        print(f"Total Ground Truth Objects: {ov['total_gt_objects']}")
        print(f"Total Predictions:          {ov['total_predicted_objects']}")
        print(f"True Positive Matches:      {ov['matched_true_positives']}")
        print(f"Missed Objects (FN):        {ov['missed_objects']}")
        print(f"Extra Predictions (FP):     {ov['extra_predictions']}")
        print(f"Wrong Class Predictions:   {ov['wrong_class_predictions']}")
        print(f"Average Pred Confidence:    {ov['overall_avg_confidence']*100:.1f}%")

        print("\nClass-Wise Breakdown:")
        print(f"{'Class Name':<20} | {'GT':<4} | {'Pred':<4} | {'TP':<4} | {'Miss':<4} | {'Extra':<5} | {'Wrong':<5}")
        print("-" * 65)
        for c_name, cw in ov["class_wise"].items():
            print(f"{c_name:<20} | {cw['gt_count']:<4} | {cw['predicted_count']:<4} | {cw['true_positives']:<4} | {cw['missed_count']:<4} | {cw['extra_count']:<5} | {cw['wrong_class_count']:<5}")

    print("\n" + "-" * 70)
    print("PER-IMAGE SAMPLE BREAKDOWN (conf=0.25):")
    print("-" * 70)
    print(f"{'#':<3} | {'Filename':<30} | {'GT':<3} | {'Pred':<4} | {'TP':<3} | {'Miss':<4} | {'Extra':<5}")
    print("-" * 70)
    for img_e in image_evaluations[:10]:  # Show first 10 for compact display
        t25 = img_e["thresholds"]["0.25"]
        print(f"{img_e['image_index']:<3} | {img_e['filename']:<30} | {img_e['gt_count']:<3} | {t25['pred_count']:<4} | {t25['tp_count']:<3} | {t25['missed_count']:<4} | {t25['extra_count']:<5}")
    if len(image_evaluations) > 10:
        print(f"... and {len(image_evaluations) - 10} more images (see full JSON).")

    print("\n=" * 70)
    print("DIAGNOSTIC EVALUATION COMPLETE.")
    print("=" * 70)


if __name__ == "__main__":
    main()
