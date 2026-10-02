"""
ReNexa — Scan Waste Page
========================
Upload or capture a waste item image for AI recognition & condition assessment.
"""

import streamlit as st
import sys
import os
from io import BytesIO
from PIL import Image

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.ui import (
    configure_page,
    page_header,
    render_sidebar,
    pill_badge,
    PRIMARY,
    SURFACE,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from utils.validation import is_valid_extension, is_valid_size, format_file_size
from ai.model_config import MATERIAL_OPTIONS, ALLOWED_CONDITIONS, ALLOWED_CONTAMINATIONS
from ai.waste_profile import create_waste_profile, update_profile_user_fields, validate_waste_profile

# ── Page config ───────────────────────────────────────────────────────────
configure_page(title="Scan Waste — ReNexa", icon="📷")

# ── Sidebar ───────────────────────────────────────────────────────────────
render_sidebar("pages/1_Scan_Waste.py")

# ── Header ────────────────────────────────────────────────────────────────
page_header("📷 Scan Waste Item", "Capture or upload a household waste item for AI identification & physical assessment.")

# ── Scanning Tips Card ───────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(
        f"""
        <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
            <div style="font-size: 1.5rem;">💡</div>
            <div style="flex: 1; font-size: 0.9rem; color: {TEXT_SECONDARY};">
                <strong style="color: {PRIMARY};">Best Results Tips:</strong> 
                Use bright lighting • Keep the waste item centered • Avoid heavy background clutter • Separate distinct materials.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── Load the YOLO model (cached) ──────────────────────────────────────────
@st.cache_resource(show_spinner="Loading waste detection model…")
def load_detector():
    """Load the WasteDetector once and cache it across reruns."""
    from ai.waste_detector import WasteDetector
    return WasteDetector()


try:
    detector = load_detector()
    model_ready = True
except Exception as exc:
    st.error(f"⚠️ Could not load the waste detection model: {exc}")
    model_ready = False


# ── Helper: process an uploaded/captured image ────────────────────────────
def process_image(image_bytes, filename, file_size):
    """
    Run the detector on raw image bytes and store everything
    in session_state for the Results page to pick up.
    """
    st.session_state["uploaded_image"] = image_bytes
    st.session_state["uploaded_filename"] = filename
    st.session_state["uploaded_size"] = file_size

    col_img, col_proc = st.columns([1, 1])

    with col_img:
        with st.container(border=True):
            st.image(image_bytes, caption="Uploaded waste item", use_container_width=True)
            st.caption(f"📁 {filename} ({format_file_size(file_size)})")

    with col_proc:
        if not model_ready:
            st.warning("🔌 Detection model is not available.")
            return

        with st.spinner("🔍 Analysing image with trained vision model…"):
            result = detector.detect(image_bytes)

        st.session_state["detection_result"] = result

        if result.get("error"):
            st.error(f"⚠️ Detection error: {result['error']}")
            return

        if result["detected"]:
            det_count = result.get("count", len(result["all_detections"]))
            primary_mat = result["label"].capitalize()
            conf_pct = f"{result['confidence'] * 100:.1f}%"

            with st.container(border=True):
                st.markdown(f"### 🔍 AI Recognition {pill_badge('Detected', 'primary')}", unsafe_allow_html=True)
                st.markdown(f"**Primary Material:** `{primary_mat}`")
                st.markdown(f"**Confidence:** `{conf_pct}` &nbsp;|&nbsp; **Objects Found:** `{det_count}`")

                material_counts = result.get("material_counts", {})
                if len(material_counts) > 1:
                    st.caption("Multiple Materials Found:")
                    for m, c in material_counts.items():
                        st.markdown(f"- `{m.capitalize()}`: {c} object(s)")

            # Confirmation buttons
            st.markdown("#### ✅ Confirm Material")
            st.markdown(f"Did AI correctly identify this material as **{primary_mat}**?")

            col_y, col_n = st.columns(2)
            with col_y:
                if st.button("👍 Yes, Correct", key="confirm_yes", use_container_width=True):
                    st.session_state["user_confirmed_material"] = result["label"]
                    st.session_state["user_correction_mode"] = False
            with col_n:
                if st.button("✏️ No, Change", key="confirm_no", use_container_width=True):
                    st.session_state["user_correction_mode"] = True

            if st.session_state.get("user_correction_mode"):
                corrected = st.selectbox(
                    "Select true material:",
                    options=MATERIAL_OPTIONS,
                    index=MATERIAL_OPTIONS.index(result["label"]) if result["label"] in MATERIAL_OPTIONS else 0,
                    key="material_correction",
                )
                if st.button("✅ Apply Selection", key="apply_correction", use_container_width=True):
                    st.session_state["user_confirmed_material"] = corrected
                    st.session_state["user_correction_mode"] = False
                    st.rerun()

            # Condition & Contamination Assessment
            confirmed_material = st.session_state.get("user_confirmed_material")
            if confirmed_material:
                st.divider()
                st.markdown("### 📝 Household Condition Assessment")
                st.caption("Assess physical condition & contamination to determine safe recovery eligibility.")

                q_col, c_col, cont_col = st.columns(3)
                with q_col:
                    quantity = st.number_input(
                        "Quantity:",
                        min_value=1,
                        max_value=100,
                        value=det_count,
                        step=1,
                        key="input_quantity",
                    )
                with c_col:
                    condition = st.selectbox(
                        "Condition:",
                        options=ALLOWED_CONDITIONS,
                        index=0,
                        key="input_condition",
                    )
                with cont_col:
                    contamination = st.selectbox(
                        "Contamination:",
                        options=ALLOWED_CONTAMINATIONS,
                        index=0,
                        key="input_contamination",
                    )

                profile = create_waste_profile(result)
                profile = update_profile_user_fields(
                    profile,
                    material=confirmed_material,
                    condition=condition,
                    confirmed_quantity=int(quantity),
                    quantity=int(quantity),
                    contamination=contamination,
                    confirmed=True,
                )
                st.session_state["waste_profile"] = profile

                # Persist scan & profile to database/local fallback
                try:
                    from database.database import save_scan, save_waste_profile
                    scan_rec = save_scan({
                        "detected_material": confirmed_material,
                        "model_label": result.get("label"),
                        "confidence": result.get("confidence"),
                        "detected_object_count": det_count,
                        "confirmed_quantity": int(quantity),
                        "image_filename": filename,
                    })
                    st.session_state["active_scan_id"] = scan_rec.get("id")
                    save_waste_profile({
                        "scan_id": scan_rec.get("id"),
                        "material": confirmed_material,
                        "condition": condition,
                        "contamination": contamination,
                        "confirmed_quantity": int(quantity),
                        "item": profile.get("item", "Unknown"),
                        "user_confirmed": True,
                        "material_counts": profile.get("material_counts", {}),
                    })
                except Exception:
                    pass

                st.success("✅ Structured Waste Profile ready for recovery matching.")
                st.page_link("pages/2_Results.py", label="📊  View Profile & Feasible Pathways →", use_container_width=True)

        else:
            st.warning("🔍 **No waste item detected.** Try a clearer photo with the item well lit and centered.")
            st.session_state.pop("waste_profile", None)
            st.session_state.pop("detection_result", None)


# ── Input Selection Tabs ──────────────────────────────────────────────────
tab_upload, tab_camera = st.tabs(["📤 Gallery / File Upload", "📸 Camera Capture"])

with tab_upload:
    st.markdown(
        "**Supported Formats:** JPG, JPEG, PNG, WEBP &nbsp;|&nbsp; **Max Size:** 5 MB"
    )
    uploaded_file = st.file_uploader(
        "Choose an image from your device",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=False,
        key="waste_upload",
    )

    if uploaded_file is not None:
        if not is_valid_extension(uploaded_file.name):
            st.error(f"❌ Invalid file type: **{uploaded_file.name}**.")
        elif not is_valid_size(uploaded_file.size):
            st.error(f"❌ File too large: **{format_file_size(uploaded_file.size)}**. Max is 5 MB.")
        else:
            process_image(
                uploaded_file.getvalue(),
                uploaded_file.name,
                uploaded_file.size,
            )

with tab_camera:
    camera_image = st.camera_input("Take a photo of the waste item")
    if camera_image is not None:
        process_image(
            camera_image.getvalue(),
            "camera_capture.jpg",
            len(camera_image.getvalue()),
        )
