import os
import sys
import time
import json
import torch
from PIL import Image
from ultralytics import YOLO

# Configuration
DATASET_YAML = '/Users/sanjana/Documents/ai_p2/data/datasets/military/KIIT-MiTA/KIIT-MiTA.yml'
MODEL_OUTPUT_DIR = '/Users/sanjana/Documents/ai_p2/data/models'
FINAL_MODEL_PATH = os.path.join(MODEL_OUTPUT_DIR, 'yolov8n_kiit_mita.pt')
RUNS_DIR = '/Users/sanjana/Documents/ai_p2/runs/detect'
DEMO_IMAGE_DIR = '/Users/sanjana/Documents/ai_p2/data/demo/drone/images'
DEMO_LABEL_DIR = '/Users/sanjana/Documents/ai_p2/data/demo/drone/labels'
VIS_OUTPUT_DIR = '/Users/sanjana/Documents/ai_p2/data/demo/drone/visualizations'

os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
os.makedirs(VIS_OUTPUT_DIR, exist_ok=True)

CLASS_NAMES = ['Artilary', 'Missile', 'Radar', 'M. Rocket Launcher', 'Soldier', 'Tank', 'Vehicle']

def train_model():
    print("=" * 60)
    print("STEP 1: REPRODUCIBLE YOLOv8n MODEL TRAINING")
    print("=" * 60)
    
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    print(f"Training Device: {device}")
    
    # Initialize YOLOv8n pretrained model
    model = YOLO('yolov8n.pt')
    
    start_time = time.time()
    
    # Train with fixed seed, patience for early stopping
    results = model.train(
        data=DATASET_YAML,
        epochs=40,
        patience=10,
        batch=16,
        imgsz=640,
        device=device,
        seed=42,
        deterministic=True,
        project=RUNS_DIR,
        name='kiit_mita_run',
        exist_ok=True,
        verbose=True,
        workers=4
    )
    
    elapsed_time = time.time() - start_time
    print(f"\nTraining finished in {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes).")
    
    best_weights = os.path.join(RUNS_DIR, 'kiit_mita_run', 'weights', 'best.pt')
    if os.path.exists(best_weights):
        # Save trained model to data/models/yolov8n_kiit_mita.pt
        import shutil
        shutil.copy2(best_weights, FINAL_MODEL_PATH)
        print(f"Successfully saved trained model to: {FINAL_MODEL_PATH}")
    else:
        print(f"ERROR: Best weights not found at {best_weights}")
        sys.exit(1)
        
    return elapsed_time, best_weights

def evaluate_test_split(model_path):
    print("\n" + "=" * 60)
    print("STEP 2: EVALUATING TRAINED MODEL ON TEST SPLIT")
    print("=" * 60)
    
    model = YOLO(model_path)
    
    # Run evaluation on test split
    metrics = model.val(
        data=DATASET_YAML,
        split='test',
        device='mps' if torch.backends.mps.is_available() else 'cpu',
        batch=16,
        imgsz=640,
        verbose=True
    )
    
    return metrics

def compare_and_visualize(fine_tuned_path):
    print("\n" + "=" * 60)
    print("STEP 3: COMPARISON ON DEMO SAMPLE IMAGES")
    print("=" * 60)
    
    coco_model = YOLO('/Users/sanjana/Documents/ai_p2/data/models/yolov8n.pt')
    ft_model = YOLO(fine_tuned_path)
    
    demo_images = [f for f in os.listdir(DEMO_IMAGE_DIR) if f.endswith(('.jpg', '.jpeg', '.png'))]
    demo_images.sort()
    
    comparison_results = []
    
    total_ft_time = 0.0
    
    for img_name in demo_images:
        img_path = os.path.join(DEMO_IMAGE_DIR, img_name)
        lbl_path = os.path.join(DEMO_LABEL_DIR, os.path.splitext(img_name)[0] + '.txt')
        
        # Load ground truth
        gt_classes = []
        if os.path.exists(lbl_path):
            with open(lbl_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        c_id = int(parts[0])
                        if c_id < len(CLASS_NAMES):
                            gt_classes.append(CLASS_NAMES[c_id])
        
        # COCO inference
        coco_res = coco_model(img_path, verbose=False)[0]
        coco_preds = []
        for box in coco_res.boxes:
            c_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            coco_preds.append(f"{coco_model.names[c_id]} ({conf*100:.1f}%)")
            
        # Fine-tuned inference & timing
        t0 = time.time()
        ft_res = ft_model(img_path, verbose=False)[0]
        t1 = time.time()
        inference_ms = (t1 - t0) * 1000
        total_ft_time += inference_ms
        
        ft_preds = []
        for box in ft_res.boxes:
            c_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            c_name = CLASS_NAMES[c_id] if c_id < len(CLASS_NAMES) else f"Unknown({c_id})"
            ft_preds.append(f"{c_name} ({conf*100:.1f}%)")
            
        # Save visualization of fine-tuned model prediction
        vis_save_path = os.path.join(VIS_OUTPUT_DIR, f"ft_pred_{img_name}")
        ft_res.save(filename=vis_save_path)
        
        comparison_results.append({
            'image': img_name,
            'ground_truth': gt_classes,
            'coco_preds': coco_preds,
            'ft_preds': ft_preds,
            'inference_ms': inference_ms,
            'vis_path': vis_save_path
        })
        
    avg_inference_ms = total_ft_time / len(demo_images) if demo_images else 0.0
    return comparison_results, avg_inference_ms

if __name__ == '__main__':
    train_time, best_weights = train_model()
    test_metrics = evaluate_test_split(FINAL_MODEL_PATH)
    comp_results, avg_inf_ms = compare_and_visualize(FINAL_MODEL_PATH)
    
    # Save benchmark summary to json
    summary = {
        'train_time_sec': train_time,
        'model_path': FINAL_MODEL_PATH,
        'model_size_mb': os.path.getsize(FINAL_MODEL_PATH) / (1024 * 1024),
        'avg_inference_ms': avg_inf_ms,
        'precision_all': test_metrics.results_dict.get('metrics/precision(B)', 0),
        'recall_all': test_metrics.results_dict.get('metrics/recall(B)', 0),
        'map50_all': test_metrics.results_dict.get('metrics/mAP50(B)', 0),
        'map50_95_all': test_metrics.results_dict.get('metrics/mAP50-95(B)', 0)
    }
    
    with open('/Users/sanjana/Documents/ai_p2/data/demo/drone/training_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
        
    print("\n" + "=" * 60)
    print("SUCCESS: TRAINING, EVALUATION AND COMPARISON COMPLETE!")
    print("=" * 60)
