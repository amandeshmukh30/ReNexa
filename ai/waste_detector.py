"""
ReNexa — Waste Detector
========================
Loads the pretrained YOLOv8 waste-classification model and runs
inference on a single image.  Returns plain Python dicts — no
Streamlit dependency so this module can also be used in tests.

"""

import os
from PIL import Image
from ultralytics import YOLO

from ai.model_config import (
    MODEL_PATH,
    CONFIDENCE_THRESHOLD,
    GLASS_LABELS,
)


class WasteDetector:
    """
    Simple wrapper around the pretrained YOLOv8 model.

    Responsibilities:
        1. Load the model once.
        2. Run inference on a PIL image or file path.
        3. Return a structured Python dict with results.
        4. Normalise glass sub-labels → "glass".
    """

    def __init__(self, model_path=None, confidence=None):
        """
        Load the YOLO model.

        Args:
            model_path:  Override path to .pt file (default: from config).
            confidence:  Override confidence threshold (default: from config).
        """
        self.model_path = model_path or MODEL_PATH
        self.confidence = confidence or CONFIDENCE_THRESHOLD

        # Verify the model file exists before trying to load it
        if not os.path.isfile(self.model_path):
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}"
            )

        # Load the YOLO model (this can take a few seconds the first time)
        self.model = YOLO(self.model_path)

        # Store class names the model knows about
        self.class_names = list(self.model.names.values())

    # ── Public API ────────────────────────────────────────────────────

    def detect(self, image):
        """
        Run detection on a single image.

        Args:
            image: Either a PIL.Image.Image or a file-path string.

        Returns:
            dict with keys:
                detected        (bool)  — True if at least one box found
                label           (str|None)  — top-prediction material
                model_label     (str|None)  — raw model label (e.g. "green-glass")
                confidence      (float)     — confidence of top prediction
                count           (int)       — total number of detected objects
                material_counts (dict)      — e.g. {"plastic": 3, "glass": 2}
                all_detections  (list[dict]) — every detection box
        """
        try:
            # Accept both PIL images and file paths
            if isinstance(image, str):
                if not os.path.isfile(image):
                    return self._empty_result()
                pil_image = Image.open(image)
            elif isinstance(image, Image.Image):
                pil_image = image
            else:
                # Try treating raw bytes (e.g. from Streamlit upload)
                import io
                pil_image = Image.open(io.BytesIO(image))

            # Run YOLO inference (verbose=False to avoid console spam)
            results = self.model(pil_image, conf=self.confidence, verbose=False)
            result = results[0]  # single image → single result object

            # Build the list of all detections
            all_detections = []
            if len(result.boxes) > 0:
                for cls_id, conf, box in zip(
                    result.boxes.cls,
                    result.boxes.conf,
                    result.boxes.xyxy,      # [x1, y1, x2, y2]
                ):
                    raw_label = self.model.names[int(cls_id)]
                    all_detections.append({
                        "label": self._normalize_label(raw_label),
                        "model_label": raw_label,
                        "confidence": round(float(conf), 4),
                        "box": [round(float(v), 1) for v in box],
                    })

            # No detections at all
            if not all_detections:
                return self._empty_result()

            # Sort by confidence (highest first)
            all_detections.sort(key=lambda d: d["confidence"], reverse=True)
            top = all_detections[0]

            # Count detections per material (after normalisation)
            material_counts = {}
            for det in all_detections:
                mat = det["label"]
                material_counts[mat] = material_counts.get(mat, 0) + 1

            return {
                "detected": True,
                "label": top["label"],
                "model_label": top["model_label"],
                "confidence": top["confidence"],
                "count": len(all_detections),
                "material_counts": material_counts,
                "all_detections": all_detections,
            }

        except Exception as exc:
            # Never crash — return an empty result with error info
            return self._empty_result(error=str(exc))

    # ── Internal helpers ──────────────────────────────────────────────

    @staticmethod
    def _normalize_label(raw_label):
        """
        Map glass sub-labels to a single 'glass' material.
        All other labels pass through unchanged.
        """
        if raw_label in GLASS_LABELS:
            return "glass"
        return raw_label

    @staticmethod
    def _empty_result(error=None):
        """Return the standard no-detection dict."""
        result = {
            "detected": False,
            "label": None,
            "model_label": None,
            "confidence": 0.0,
            "count": 0,
            "material_counts": {},
            "all_detections": [],
        }
        if error:
            result["error"] = error
        return result
