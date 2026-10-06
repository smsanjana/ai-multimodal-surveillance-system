"""
Test script to verify if amp=False fixes NaN loss on Apple Silicon MPS device.
"""
import torch
from ultralytics import YOLO

print(f"MPS Available: {torch.backends.mps.is_available()}")

model = YOLO("yolov8s.pt")
results = model.train(
    data="data/datasets/military/KIIT-MiTA_cleaned/KIIT-MiTA.yml",
    epochs=1,
    imgsz=640,
    batch=16,
    device="mps",
    amp=False,  # Disable AMP (automatic mixed precision) on MPS
    project="runs/detect/tests",
    name="test_amp_false",
    exist_ok=True,
    verbose=True
)
print("1-epoch AMP=False test completed successfully!")
