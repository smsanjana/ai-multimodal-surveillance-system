"""
Stage 1 Execution Script:
1. Create data/datasets/military/KIIT-MiTA_cleaned/ as a separate copy.
2. Exclude 8 train-to-val/test duplicate training images and 11 within-train duplicate images.
3. Preserve all valid and test files 100% untouched.
4. Check for any additional MD5 duplicates across splits in the cleaned dataset.
5. Verify image-label pairing and record class counts for each split.
6. Generate diagnostic list of duplicate pairs with annotation discrepancies.
7. Evaluate baseline data/models/yolov8n_kiit_mita.pt on original valid and test splits.
8. Reconcile TP, FP, FN, wrong-class counts, and mAP definitions.
9. Save Stage 1 diagnostic JSON report.
"""

import os
import shutil
import hashlib
import json
import yaml
from collections import Counter, defaultdict
from ultralytics import YOLO

ORIGINAL_DATASET_DIR = "data/datasets/military/KIIT-MiTA"
CLEANED_DATASET_DIR = "data/datasets/military/KIIT-MiTA_cleaned"
MODEL_PATH = "data/models/yolov8n_kiit_mita.pt"
STAGE1_REPORT_PATH = "data/demo/drone/stage1_clean_dataset_and_baseline_report.json"

CLASS_NAMES = {
    0: "Artilary",
    1: "Missile",
    2: "Radar",
    3: "M. Rocket Launcher",
    4: "Soldier",
    5: "Tank",
    6: "Vehicle"
}

# 8 train-to-val/test leakage duplicates to exclude from train
EXCLUDE_LEAKAGE_TRAIN = {
    "image_s3r2_kiit_1484.jpeg",
    "image_s3r2_kiit_428.jpeg",
    "image_s3r2_kiit_1164.jpeg",
    "image_s3r2_kiit_191.jpeg",
    "image_s3r2_kiit_566.jpeg",
    "image_s3r2_kiit_1239.jpeg",
    "image_s3r2_kiit_1151.jpeg",
    "image_s3r2_kiit_972.jpeg"
}

# 11 within-train duplicates to exclude from train (keeping the first occurrence)
EXCLUDE_WITHIN_TRAIN = {
    "image_s3r2_kiit_1487.jpeg",  # keeps 1158
    "image_s3r2_kiit_153.jpeg",   # keeps 142
    "image_s3r2_kiit_1570.jpeg",  # keeps 1521
    "image_s3r2_kiit_285.jpeg",   # keeps 15
    "image_s3r2_kiit_52.jpeg",    # keeps 1051
    "image_s3r2_kiit_563.jpeg",   # keeps 1011
    "image_s3r2_kiit_578.jpeg",   # keeps 425
    "image_s3r2_kiit_679.jpeg",   # keeps 417
    "image_s3r2_kiit_730.jpeg",   # keeps 227
    "image_s3r2_kiit_774.jpeg",   # keeps 280
    "image_s3r2_kiit_880.jpeg"    # keeps 244
}

EXCLUDE_ALL_TRAIN = EXCLUDE_LEAKAGE_TRAIN.union(EXCLUDE_WITHIN_TRAIN)


def create_cleaned_dataset():
    print("=" * 70)
    print("STEP 1: CREATING CLEANED DATASET COPY")
    print("=" * 70)

    if os.path.exists(CLEANED_DATASET_DIR):
        shutil.rmtree(CLEANED_DATASET_DIR)

    for split in ["train", "valid", "test"]:
        os.makedirs(os.path.join(CLEANED_DATASET_DIR, split, "images"), exist_ok=True)
        os.makedirs(os.path.join(CLEANED_DATASET_DIR, split, "labels"), exist_ok=True)

    # Copy YAML
    cleaned_yaml_path = os.path.join(CLEANED_DATASET_DIR, "KIIT-MiTA.yml")
    yaml_data = {
        "path": os.path.abspath(CLEANED_DATASET_DIR),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "names": CLASS_NAMES
    }
    with open(cleaned_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, default_flow_style=False)

    # Copy valid and test completely
    for split in ["valid", "test"]:
        src_img_dir = os.path.join(ORIGINAL_DATASET_DIR, split, "images")
        src_lbl_dir = os.path.join(ORIGINAL_DATASET_DIR, split, "labels")
        dst_img_dir = os.path.join(CLEANED_DATASET_DIR, split, "images")
        dst_lbl_dir = os.path.join(CLEANED_DATASET_DIR, split, "labels")

        for fname in os.listdir(src_img_dir):
            if fname.endswith((".jpg", ".jpeg", ".png")):
                shutil.copy2(os.path.join(src_img_dir, fname), os.path.join(dst_img_dir, fname))
                lbl_fname = os.path.splitext(fname)[0] + ".txt"
                lbl_src = os.path.join(src_lbl_dir, lbl_fname)
                if os.path.exists(lbl_src):
                    shutil.copy2(lbl_src, os.path.join(dst_lbl_dir, lbl_fname))

    # Copy train excluding specified 19 images
    src_train_img = os.path.join(ORIGINAL_DATASET_DIR, "train", "images")
    src_train_lbl = os.path.join(ORIGINAL_DATASET_DIR, "train", "labels")
    dst_train_img = os.path.join(CLEANED_DATASET_DIR, "train", "images")
    dst_train_lbl = os.path.join(CLEANED_DATASET_DIR, "train", "labels")

    copied_train_count = 0
    excluded_train_count = 0

    for fname in sorted(os.listdir(src_train_img)):
        if fname.endswith((".jpg", ".jpeg", ".png")):
            if fname in EXCLUDE_ALL_TRAIN:
                excluded_train_count += 1
                continue
            shutil.copy2(os.path.join(src_train_img, fname), os.path.join(dst_train_img, fname))
            lbl_fname = os.path.splitext(fname)[0] + ".txt"
            lbl_src = os.path.join(src_train_lbl, lbl_fname)
            if os.path.exists(lbl_src):
                shutil.copy2(lbl_src, os.path.join(dst_train_lbl, lbl_fname))
            copied_train_count += 1

    print(f"Created cleaned dataset at: {CLEANED_DATASET_DIR}")
    print(f"Copied Train Images: {copied_train_count} (Excluded {excluded_train_count} duplicates)")
    print(f"Copied Valid Images: {len(os.listdir(os.path.join(CLEANED_DATASET_DIR, 'valid', 'images')))}")
    print(f"Copied Test Images:  {len(os.listdir(os.path.join(CLEANED_DATASET_DIR, 'test', 'images')))}")


def verify_cleaned_dataset_integrity():
    print("\n" + "=" * 70)
    print("STEP 2: VERIFYING CLEANED DATASET INTEGRITY")
    print("=" * 70)

    hashes = {}
    remaining_cross_leakage = []
    remaining_within_split = []

    split_stats = {}

    for split in ["train", "valid", "test"]:
        img_dir = os.path.join(CLEANED_DATASET_DIR, split, "images")
        lbl_dir = os.path.join(CLEANED_DATASET_DIR, split, "labels")

        img_files = sorted([f for f in os.listdir(img_dir) if f.endswith((".jpg", ".jpeg", ".png"))])
        lbl_files = sorted([f for f in os.listdir(lbl_dir) if f.endswith(".txt")])

        class_counts = Counter()
        total_objects = 0
        missing_pairings = 0

        for img in img_files:
            img_path = os.path.join(img_dir, img)
            with open(img_path, "rb") as f:
                h = hashlib.md5(f.read()).hexdigest()

            if h in hashes:
                prev_split, prev_img = hashes[h]
                if prev_split != split:
                    remaining_cross_leakage.append((h, prev_split, prev_img, split, img))
                else:
                    remaining_within_split.append((h, split, prev_img, img))
            else:
                hashes[h] = (split, img)

            base = os.path.splitext(img)[0]
            lbl_path = os.path.join(lbl_dir, base + ".txt")
            if not os.path.exists(lbl_path):
                missing_pairings += 1
            else:
                with open(lbl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            c_id = int(parts[0])
                            class_counts[c_id] += 1
                            total_objects += 1

        split_stats[split] = {
            "image_count": len(img_files),
            "label_count": len(lbl_files),
            "missing_pairings": missing_pairings,
            "total_objects": total_objects,
            "class_counts_by_id": dict(sorted(class_counts.items())),
            "class_counts_by_name": {CLASS_NAMES[k]: v for k, v in sorted(class_counts.items())}
        }

        print(f"Split: {split:<5} | Images: {len(img_files):<4} | Labels: {len(lbl_files):<4} | Objects: {total_objects:<4} | Missing Pairs: {missing_pairings}")
        for c_id, c_name in CLASS_NAMES.items():
            print(f"  Class {c_id} ({c_name:<18}): {class_counts[c_id]:<4} instances")

    print(f"\nRemaining Cross-Split Duplicates: {len(remaining_cross_leakage)}")
    print(f"Remaining Within-Split Duplicates: {len(remaining_within_split)}")

    return split_stats, remaining_cross_leakage, remaining_within_split


def build_annotation_discrepancy_report():
    print("\n" + "=" * 70)
    print("STEP 3: ANNOTATION DISCREPANCY DIAGNOSTIC REPORT")
    print("=" * 70)

    discrepancies = []
    orig_hashes = defaultdict(list)

    for s in ["train", "valid", "test"]:
        img_d = os.path.join(ORIGINAL_DATASET_DIR, s, "images")
        lbl_d = os.path.join(ORIGINAL_DATASET_DIR, s, "labels")
        for img in os.listdir(img_d):
            if img.endswith((".jpg", ".jpeg", ".png")):
                p = os.path.join(img_d, img)
                with open(p, "rb") as f:
                    h = hashlib.md5(f.read()).hexdigest()
                base = os.path.splitext(img)[0]
                lbl_p = os.path.join(lbl_d, base + ".txt")
                classes = []
                if os.path.exists(lbl_p):
                    with open(lbl_p, "r", encoding="utf-8") as lf:
                        classes = [int(line.split()[0]) for line in lf if line.strip()]
                orig_hashes[h].append({"split": s, "image_name": img, "classes": classes, "box_count": len(classes)})

    for h, file_list in orig_hashes.items():
        if len(file_list) > 1:
            box_counts = [f["box_count"] for f in file_list]
            class_lists = [sorted(f["classes"]) for f in file_list]
            has_discrepancy = len(set(box_counts)) > 1 or any(cl != class_lists[0] for cl in class_lists)

            discrepancies.append({
                "hash": h,
                "file_count": len(file_list),
                "has_discrepancy": has_discrepancy,
                "files": file_list
            })

    print(f"Total Duplicate Image Groups Audited: {len(discrepancies)}")
    discrepancy_count = sum(1 for d in discrepancies if d["has_discrepancy"])
    print(f"Duplicate Groups with Label Discrepancies: {discrepancy_count}")

    for idx, d in enumerate(discrepancies, 1):
        status = "⚠️ DISCREPANCY" if d["has_discrepancy"] else "✅ MATCHED"
        print(f"\nGroup #{idx} [{status}] Hash: {d['hash'][:8]}...")
        for f in d["files"]:
            cls_named = [CLASS_NAMES.get(c, str(c)) for c in f["classes"]]
            print(f"  - {f['split']}/{f['image_name']} ({f['box_count']} boxes): {cls_named}")

    return discrepancies


def evaluate_baseline_model():
    print("\n" + "=" * 70)
    print("STEP 4: EVALUATING BASELINE MODEL ON ORIGINAL VALID & TEST SPLITS")
    print("=" * 70)

    model = YOLO(MODEL_PATH)
    orig_yaml_path = os.path.join(ORIGINAL_DATASET_DIR, "KIIT-MiTA.yml")

    # 1. Validation Split Evaluation
    print("\nExecuting evaluation on ORIGINAL VALID split...")
    val_res = model.val(
        data=orig_yaml_path,
        split="val",
        conf=0.25,
        iou=0.50,
        batch=16,
        imgsz=640,
        verbose=False
    )

    # 2. Test Split Evaluation
    print("\nExecuting evaluation on ORIGINAL TEST split...")
    test_res = model.val(
        data=orig_yaml_path,
        split="test",
        conf=0.25,
        iou=0.50,
        batch=16,
        imgsz=640,
        verbose=False
    )

    def extract_metrics(res):
        cm = res.confusion_matrix.matrix
        names = res.names
        
        per_class = {}
        total_gt_all = 0
        total_tp_all = 0
        total_fn_all = 0
        total_fp_all = 0
        total_wrong_all = 0

        for i in range(len(names)):
            gt_i = int(cm[i, :].sum())
            tp_i = int(cm[i, i])
            fn_i = int(cm[i, len(names)]) if cm.shape[1] > len(names) else 0
            wrong_i = max(0, gt_i - tp_i - fn_i)
            fp_i = int(cm[len(names), i]) if cm.shape[0] > len(names) else 0

            p_i = float(res.box.p[i]) if i < len(res.box.p) else 0.0
            r_i = float(res.box.r[i]) if i < len(res.box.r) else 0.0
            ap50_i = float(res.box.ap50[i]) if i < len(res.box.ap50) else 0.0
            ap_i = float(res.box.ap[i]) if i < len(res.box.ap) else 0.0

            total_gt_all += gt_i
            total_tp_all += tp_i
            total_fn_all += fn_i
            total_fp_all += fp_i
            total_wrong_all += wrong_i

            per_class[names[i]] = {
                "class_id": i,
                "ground_truth_objects": gt_i,
                "true_positives": tp_i,
                "false_negatives": fn_i,
                "wrong_class": wrong_i,
                "false_positives": fp_i,
                "precision": round(p_i, 4),
                "recall": round(r_i, 4),
                "map50": round(ap50_i, 4),
                "map50_95": round(ap_i, 4)
            }

        return {
            "overall": {
                "precision": round(float(res.results_dict.get("metrics/precision(B)", 0.0)), 4),
                "recall": round(float(res.results_dict.get("metrics/recall(B)", 0.0)), 4),
                "map50": round(float(res.results_dict.get("metrics/mAP50(B)", 0.0)), 4),
                "map50_95": round(float(res.results_dict.get("metrics/mAP50-95(B)", 0.0)), 4),
                "total_ground_truth": total_gt_all,
                "total_true_positives": total_tp_all,
                "total_false_negatives": total_fn_all,
                "total_false_positives": total_fp_all,
                "total_wrong_class": total_wrong_all
            },
            "per_class": per_class
        }

    val_metrics = extract_metrics(val_res)
    test_metrics = extract_metrics(test_res)

    print("\n--- ORIGINAL VALIDATION METRICS ---")
    print(f"Precision: {val_metrics['overall']['precision']} | Recall: {val_metrics['overall']['recall']} | mAP50: {val_metrics['overall']['map50']} | mAP50-95: {val_metrics['overall']['map50_95']}")
    print("\n--- ORIGINAL TEST METRICS ---")
    print(f"Precision: {test_metrics['overall']['precision']} | Recall: {test_metrics['overall']['recall']} | mAP50: {test_metrics['overall']['map50']} | mAP50-95: {test_metrics['overall']['map50_95']}")

    return val_metrics, test_metrics


def main():
    create_cleaned_dataset()
    split_stats, remaining_cross, remaining_within = verify_cleaned_dataset_integrity()
    discrepancies = build_annotation_discrepancy_report()
    val_metrics, test_metrics = evaluate_baseline_model()

    # Save comprehensive Stage 1 JSON Report
    stage1_report = {
        "stage": "STAGE_1_BASELINE_AND_CLEAN_DATASET_VERIFICATION",
        "original_dataset_path": ORIGINAL_DATASET_DIR,
        "cleaned_dataset_path": CLEANED_DATASET_DIR,
        "model_path": MODEL_PATH,
        "evaluation_configuration": {
            "confidence_threshold": 0.25,
            "iou_threshold": 0.50,
            "imgsz": 640,
            "batch": 16,
            "device": "cpu"
        },
        "cleaned_dataset_stats": split_stats,
        "integrity_check": {
            "remaining_cross_split_duplicates": len(remaining_cross),
            "remaining_within_split_duplicates": len(remaining_within)
        },
        "annotation_discrepancy_report": discrepancies,
        "original_val_evaluation": val_metrics,
        "original_test_evaluation": test_metrics
    }

    os.makedirs(os.path.dirname(STAGE1_REPORT_PATH), exist_ok=True)
    with open(STAGE1_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(stage1_report, f, indent=2)

    print("\n" + "=" * 70)
    print("STAGE 1 COMPLETED SUCCESSFULLY.")
    print(f"Diagnostic JSON report saved to: {STAGE1_REPORT_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
