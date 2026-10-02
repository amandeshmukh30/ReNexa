"""
ReNexa — AI Model Configuration
================================
Central place for model paths, detection settings, and profile categories.
All AI modules import from here so values are not repeated.
"""

import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# ── Pretrained YOLO waste-classification model ────────────────────────────
# 12 classes: battery, biological, brown-glass, cardboard, clothes,
#             green-glass, metal, paper, plastic, shoes, trash, white-glass

REPO_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "yolov8n-waste-12cls-best.pt")
CACHE_MODEL_PATH = os.path.expanduser(
    os.path.join(
        "~",
        ".cache",
        "huggingface",
        "hub",
        "models--kendrickfff--waste-classification-yolov8-ken",
        "snapshots",
        "0bf64a69712abcc9f80e4697a4fd90028a4ba74e",
        "yolov8n-waste-12cls-best.pt",
    )
)

# Resolve model path dynamically in order of preference:
# 1. Environment variable override
# 2. Repository-relative path (`models/yolov8n-waste-12cls-best.pt`)
# 3. Local HuggingFace cache snapshot
# 4. Fallback to repo model path
if os.environ.get("RENEXA_MODEL_PATH") and os.path.isfile(os.environ["RENEXA_MODEL_PATH"]):
    MODEL_PATH = os.environ["RENEXA_MODEL_PATH"]
elif os.path.isfile(REPO_MODEL_PATH):
    MODEL_PATH = REPO_MODEL_PATH
elif os.path.isfile(CACHE_MODEL_PATH):
    MODEL_PATH = CACHE_MODEL_PATH
else:
    MODEL_PATH = REPO_MODEL_PATH

# ── Detection settings ────────────────────────────────────────────────────
# Minimum confidence for a detection to be kept.
CONFIDENCE_THRESHOLD = 0.25

# ── Glass label normalisation ─────────────────────────────────────────────
GLASS_LABELS = {"brown-glass", "green-glass", "white-glass"}

# ── All material choices the user can pick from ──────────────────────────
MATERIAL_OPTIONS = [
    "battery",
    "biological",
    "glass",
    "cardboard",
    "clothes",
    "metal",
    "paper",
    "plastic",
    "shoes",
    "trash",
]

# ── Standard Condition & Contamination Categories ─────────────────────────
ALLOWED_CONDITIONS = [
    "Good",
    "Used",
    "Damaged",
    "Heavily Damaged",
    "Unknown",
]

ALLOWED_CONTAMINATIONS = [
    "Clean",
    "Slightly Contaminated",
    "Heavily Contaminated",
    "Unknown",
]
