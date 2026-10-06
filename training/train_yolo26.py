from pathlib import Path
from ultralytics import YOLO
import torch


# ==========================================
# ReNexa YOLO26s Final Training
# ==========================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_YAML = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "renexa_detection_final"
    / "data.yaml"
)

RUN_DIR = PROJECT_DIR / "training" / "runs"


print("=" * 60)
print("ReNexa YOLO26s Final Training")
print("=" * 60)

print("\nProject directory:")
print(PROJECT_DIR)

print("\nDataset configuration:")
print(DATA_YAML)

print("\nOutput directory:")
print(RUN_DIR)


# ------------------------------------------
# Check dataset
# ------------------------------------------

if not DATA_YAML.exists():
    print("\nERROR: data.yaml was not found.")
    print("Expected location:")
    print(DATA_YAML)
    raise SystemExit(1)

print("\nDataset configuration found.")


# ------------------------------------------
# Check GPU
# ------------------------------------------

if torch.cuda.is_available():
    device = 0
    print("\nGPU detected.")
    print("GPU:", torch.cuda.get_device_name(0))
else:
    device = "cpu"
    print("\nWARNING: No CUDA GPU detected.")
    print("Training will use CPU and may be very slow.")


# ------------------------------------------
# Load YOLO26s
# ------------------------------------------

print("\nLoading YOLO26s...")

model = YOLO("yolo26s.pt")

print("YOLO26s loaded successfully.")


# ------------------------------------------
# Start training
# ------------------------------------------

print("\nStarting training...")
print("=" * 60)

results = model.train(
    data=str(DATA_YAML),

    epochs=100,
    imgsz=640,
    batch=8,

    device=device,
    workers=4,

    project=str(RUN_DIR),
    name="yolo26s_final",

    pretrained=True,
    cache=False,
    save=True,
    plots=True,

    exist_ok=True
)


# ------------------------------------------
# Training completed
# ------------------------------------------

BEST_MODEL = RUN_DIR / "yolo26s_final" / "weights" / "best.pt"
LAST_MODEL = RUN_DIR / "yolo26s_final" / "weights" / "last.pt"


print("\n")
print("=" * 60)
print("TRAINING COMPLETED")
print("=" * 60)

print("\nBest model:")
print(BEST_MODEL)

print("\nLast model:")
print(LAST_MODEL)

print("\nReNexa YOLO26s training finished successfully.")