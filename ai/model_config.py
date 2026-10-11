
"""
ReNexa - AI Model Configuration
================================
Central configuration for model paths, detection settings,
material options, and waste profile categories.
"""

import os

# Project root
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

# --------------------------------------------------
# Trained ReNexa YOLO26s detection model
# --------------------------------------------------

# Model included for deployment on GitHub / Streamlit Cloud
DEPLOYMENT_MODEL_PATH = os.path.join(
    PROJECT_ROOT,
    "models",
    "deployment",
    "best.pt",
)

# Original model location used during local training
REPO_MODEL_PATH = os.path.join(
    PROJECT_ROOT,
    "training",
    "runs",
    "yolo26s_final",
    "weights",
    "best.pt",
)

# Optional environment variable override
ENV_MODEL_PATH = os.environ.get("RENEXA_MODEL_PATH")

if ENV_MODEL_PATH and os.path.isfile(ENV_MODEL_PATH):
    MODEL_PATH = ENV_MODEL_PATH
elif os.path.isfile(DEPLOYMENT_MODEL_PATH):
    MODEL_PATH = DEPLOYMENT_MODEL_PATH
else:
    MODEL_PATH = REPO_MODEL_PATH

# --------------------------------------------------
# Detection settings
# --------------------------------------------------

# Minimum confidence required to keep a detection
CONFIDENCE_THRESHOLD = 0.40

# Glass labels that should be normalised to "glass"
GLASS_LABELS = {
    "brown-glass",
    "green-glass",
    "white-glass",
}

# --------------------------------------------------
# Material options for user confirmation/correction
# These are not limited to the model's 7 classes.
# --------------------------------------------------

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

# --------------------------------------------------
# Standard condition categories
# --------------------------------------------------

ALLOWED_CONDITIONS = [
    "Good",
    "Used",
    "Damaged",
    "Heavily Damaged",
    "Unknown",
]

# --------------------------------------------------
# Standard contamination categories
# --------------------------------------------------

ALLOWED_CONTAMINATIONS = [
    "Clean",
    "Slightly Contaminated",
    "Heavily Contaminated",
    "Unknown",
]
