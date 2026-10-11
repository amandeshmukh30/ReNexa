import csv
import json
import os
import sys
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.recovery_service import (
    get_recovery_pathways,
    get_available_materials,
    get_tutorials,
    get_tutorials_for_pathway,
    load_recovery_pathways,
)
from services.eligibility_service import get_eligible_pathways_for_profile
from services.ranking_service import get_ranked_recommendations_for_profile
from services.execution_service import get_execution_guide
from services.outcome_service import (
    load_outcome_feedback,
    save_outcome_feedback,
    calculate_outcome_metrics,
    summarize_failure_reasons,
    analyze_pathway_outcomes,
)
from utils.validation import (
    get_default_constraints,
    is_valid_extension,
    is_valid_size,
    format_file_size,
)
from ai.model_config import (
    MATERIAL_OPTIONS,
    ALLOWED_CONDITIONS,
    ALLOWED_CONTAMINATIONS,
)
from ai.waste_profile import (
    create_waste_profile,
    update_profile_user_fields,
)
from database.database import (
    save_scan,
    save_waste_profile,
    get_user_scans,
    save_recommendation,
)

KNOWLEDGE = ROOT / "data" / "knowledge"
RUNTIME = ROOT / "data" / "runtime"
RUNTIME.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# CACHED MODEL LOADER
# --------------------------------------------------

@st.cache_resource(show_spinner="Loading waste detection model…")
def load_detector():
    """Load the WasteDetector once and cache across Streamlit reruns."""
    from ai.waste_detector import WasteDetector
    return WasteDetector()


# --------------------------------------------------
# STATE HELPERS
# --------------------------------------------------

def current_profile():
    return st.session_state.get("waste_profile") or {}


def current_constraints():
    defaults = get_default_constraints()
    return {
        "budget": st.session_state.get("budget", defaults["budget"]),
        "tools": st.session_state.get("tools", defaults["tools"]),
        "skill": st.session_state.get("skill", defaults["skill"]),
        "time": st.session_state.get("time", defaults["time"]),
        "workspace": st.session_state.get("workspace", "Any"),
        "extra_materials": st.session_state.get("extra_materials", []),
        "safety_preference": st.session_state.get(
            "safety_preference", defaults["safety_preference"]
        ),
    }


def require_profile():
    profile = current_profile()
    if not profile.get("material") or profile.get("material") == "Unknown":
        st.warning("Scan a waste item and confirm its material first.")
        st.page_link("pages/1_Scan_Waste.py", label="Go to Scan Waste →")
        return None
    return profile


def get_evaluations(profile=None):
    profile = profile or current_profile()
    if not profile.get("material") or profile.get("material") == "Unknown":
        return []
    return get_eligible_pathways_for_profile(
        profile, current_constraints()
    )


def get_ranked(profile=None, top_k=None):
    profile = profile or current_profile()
    if not profile.get("material") or profile.get("material") == "Unknown":
        return []

    return get_ranked_recommendations_for_profile(
        waste_profile=profile,
        user_constraints=current_constraints(),
        top_k=top_k,
    )


def pathway_list(profile=None):
    profile = profile or current_profile()
    material = profile.get("material")
    if material and material != "Unknown":
        return get_recovery_pathways(material=material)
    return get_recovery_pathways()


# --------------------------------------------------
# 1. SCAN WASTE
# --------------------------------------------------

def render_scan_waste():
    st.title("📷 Scan Waste Item")
    st.caption("Capture or upload a household waste item for AI identification & physical assessment.")

    st.markdown(
        """
        <div style="padding:0.75rem 1rem; border-radius:12px; background:var(--rx-surface2); border:1px solid var(--rx-border); margin-bottom:1rem;">
            <b>💡 Best Results Tips:</b> Use bright lighting • Keep the waste item centered • Avoid heavy background clutter • Separate distinct materials.
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        detector = load_detector()
        model_ready = True
    except Exception as exc:
        st.error(f"⚠️ Could not load the waste detection model: {exc}")
        model_ready = False

    # --------------------------------------------------
    # INPUT WORKFLOW (GALLERY UPLOAD OR CAMERA CAPTURE)
    # --------------------------------------------------
    tab_upload, tab_camera = st.tabs(["📤 Gallery / File Upload", "📸 Camera Capture"])

    new_bytes = None
    new_filename = None
    new_size = 0

    with tab_upload:
        st.caption("Supported Formats: JPG, JPEG, PNG, WEBP • Maximum Size: 5 MB")
        uploaded_file = st.file_uploader(
            "Choose an image from your device",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=False,
            key="waste_upload",
            help="Select a clear photo of the household waste item.",
        )
        if uploaded_file is not None:
            if not is_valid_extension(uploaded_file.name):
                st.error(f"❌ Invalid file type: **{uploaded_file.name}**. Please upload a JPG, JPEG, PNG, or WEBP image.")
            elif not is_valid_size(uploaded_file.size):
                st.error(f"❌ File too large: **{format_file_size(uploaded_file.size)}**. Maximum size is 5 MB.")
            else:
                new_bytes = uploaded_file.getvalue()
                new_filename = uploaded_file.name
                new_size = uploaded_file.size

    with tab_camera:
        st.caption("Point your webcam or device camera directly at the waste item.")
        camera_image = st.camera_input("Take a photo of the waste item", key="waste_camera")
        st.markdown(
            """
            <div style="font-size:0.83rem; opacity:0.8; margin-top:0.35rem; margin-bottom:0.5rem;">
                ℹ️ <b>Camera guidance:</b> If camera capture does not appear, ensure camera permissions are allowed in your browser address bar.
            </div>
            """,
            unsafe_allow_html=True,
        )
        if camera_image is not None:
            new_bytes = camera_image.getvalue()
            new_filename = "camera_capture.jpg"
            new_size = len(new_bytes)

    # Update session state with new image if submitted
    if new_bytes is not None:
        if (
            st.session_state.get("uploaded_filename") != new_filename
            or st.session_state.get("uploaded_size") != new_size
            or st.session_state.get("uploaded_image") != new_bytes
        ):
            st.session_state["uploaded_image"] = new_bytes
            st.session_state["uploaded_filename"] = new_filename
            st.session_state["uploaded_size"] = new_size
            st.session_state["detection_result"] = None
            st.session_state["annotated_image"] = None
            st.session_state["user_confirmed_material"] = None
            st.session_state["user_correction_mode"] = False

    current_image_bytes = st.session_state.get("uploaded_image")
    current_filename = st.session_state.get("uploaded_filename", "waste_item.jpg")
    current_size = st.session_state.get("uploaded_size", 0)

    if not current_image_bytes:
        return

    # Image reset / scan new toolbar
    col_hdr, col_reset = st.columns([3, 1])
    with col_hdr:
        st.caption(f"📁 **Active Item:** {current_filename} ({format_file_size(current_size)})")
    with col_reset:
        if st.button("🔄 Scan Another Item", key="btn_clear_scan", use_container_width=True):
            st.session_state.pop("uploaded_image", None)
            st.session_state.pop("uploaded_filename", None)
            st.session_state.pop("uploaded_size", None)
            st.session_state.pop("detection_result", None)
            st.session_state.pop("annotated_image", None)
            st.session_state.pop("user_confirmed_material", None)
            st.session_state.pop("user_correction_mode", None)
            st.session_state.pop("waste_profile", None)
            st.rerun()

    if not model_ready:
        st.warning("🔌 Detection model is not available.")
        return

    # Run detection once per image
    if st.session_state.get("detection_result") is None:
        with st.spinner("🔍 Analysing image with trained YOLO26s model…"):
            result = detector.detect(current_image_bytes)
        st.session_state["detection_result"] = result
    else:
        result = st.session_state["detection_result"]

    if result.get("error"):
        st.error(f"⚠️ Detection error: {result['error']}")
        return

    if not result.get("detected"):
        col_no_img, col_no_msg = st.columns([1, 1], gap="medium")
        with col_no_img:
            with st.container(border=True):
                st.markdown("#### 📷 Original Image")
                st.image(current_image_bytes, caption="Original Image", use_container_width=True)
                st.caption(f"📁 {current_filename} ({format_file_size(current_size)})")
        with col_no_msg:
            st.warning("🔍 **No waste item detected.** Try a clearer photo with the item well lit and centered.")
            st.caption("Common causes: Object is too distant, extreme low lighting, or background blend.")
        st.session_state.pop("waste_profile", None)
        return

    all_detections = result.get("all_detections", [])
    det_count = len(all_detections)
    primary_mat = result.get("label", "Unknown").capitalize()
    conf_pct = f"{result.get('confidence', 0) * 100:.1f}%"

    # Generate high-contrast annotated detection image
    if st.session_state.get("annotated_image") is None:
        annotated_image = Image.open(BytesIO(current_image_bytes)).convert("RGB")
        draw = ImageDraw.Draw(annotated_image)

        img_min_dim = min(annotated_image.width, annotated_image.height)
        line_width = max(3, int(img_min_dim * 0.005))
        font_size = max(14, int(img_min_dim * 0.024))
        try:
            font = ImageFont.load_default(size=font_size)
        except TypeError:
            font = ImageFont.load_default()

        for index, detection in enumerate(all_detections, start=1):
            x1, y1, x2, y2 = [int(v) for v in detection["box"]]
            draw.rectangle((x1, y1, x2, y2), outline="#087F50", width=line_width)
            box_label = f"{index}. {detection['label'].title()} {detection['confidence']:.0%}"

            text_y = max(0, y1 - font_size - 8)
            if hasattr(draw, "textbbox"):
                tb = draw.textbbox((x1, text_y), box_label, font=font)
                draw.rectangle((tb[0] - 4, tb[1] - 2, tb[2] + 4, tb[3] + 2), fill="#087F50")
                draw.text((x1, text_y), box_label, fill="#FFFFFF", font=font)
            else:
                draw.text((x1, text_y), box_label, fill="#087F50", stroke_width=2, stroke_fill="white")

        st.session_state["annotated_image"] = annotated_image
    else:
        annotated_image = st.session_state["annotated_image"]

    # --------------------------------------------------
    # 1. SIDE-BY-SIDE IMAGE COMPARISON
    # --------------------------------------------------
    st.markdown("---")
    col_orig, col_annot = st.columns([1, 1], gap="medium")

    with col_orig:
        with st.container(border=True):
            st.markdown("#### 📷 Original Image")
            st.image(current_image_bytes, caption="Original Image", use_container_width=True)
            st.caption(f"📁 {current_filename} • {format_file_size(current_size)}")

    with col_annot:
        with st.container(border=True):
            st.markdown("#### 🎯 YOLO26s Detection")
            st.image(annotated_image, caption="YOLO26s Detection", use_container_width=True)
            st.caption(f"⚡ Model: YOLO26s • {det_count} object{'s' if det_count != 1 else ''} detected • Primary: {primary_mat} ({conf_pct})")

    # --------------------------------------------------
    # 2. AI RECOGNITION RESULT & MATERIAL CONFIRMATION
    # --------------------------------------------------
    confirmed_material = st.session_state.get("user_confirmed_material") or result.get("label", "Unknown")

    with st.container(border=True):
        st.markdown("### 🔍 AI Recognition Result")
        st.caption("Real-time inference generated by trained YOLO26s waste detection model.")

        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("Primary Material", primary_mat)
        with m_col2:
            st.metric("Model Confidence", conf_pct)
        with m_col3:
            st.metric("Objects Detected", f"{det_count}")

        material_counts = result.get("material_counts", {})
        if len(material_counts) > 1:
            st.markdown("##### 📦 All Detected Materials Breakdown")
            chip_cols = st.columns(min(len(material_counts), 4))
            for i, (mat, count) in enumerate(material_counts.items()):
                with chip_cols[i % len(chip_cols)]:
                    st.info(f"**{mat.title()}**: {count} item{'s' if count != 1 else ''}")

        st.divider()

        # Material Confirmation
        st.markdown("#### ✅ Material Confirmation")
        is_confirmed = st.session_state.get("user_confirmed_material") is not None
        status_text = f"Confirmed as **{confirmed_material.title()}**" if is_confirmed else f"Model predicted: **{primary_mat}** (Awaiting confirmation)"
        st.write(f"**Status:** {status_text}")
        st.write(f"Did AI correctly identify the primary material as **{primary_mat}**?")

        col_y, col_n, _ = st.columns([1, 1, 2])
        with col_y:
            if st.button("👍 Yes, Correct", key="confirm_yes", use_container_width=True):
                st.session_state["user_confirmed_material"] = result["label"]
                st.session_state["user_correction_mode"] = False
                st.rerun()
        with col_n:
            if st.button("✏️ No, Change", key="confirm_no", use_container_width=True):
                st.session_state["user_correction_mode"] = True
                st.rerun()

        if st.session_state.get("user_correction_mode"):
            with st.container(border=True):
                st.markdown("##### ✏️ Select True Material")
                curr_idx = (
                    MATERIAL_OPTIONS.index(result["label"])
                    if result["label"] in MATERIAL_OPTIONS
                    else 0
                )
                corrected = st.selectbox(
                    "Choose true material type:",
                    options=MATERIAL_OPTIONS,
                    index=curr_idx,
                    key="material_correction",
                    help="Select the true physical material from standardized ReNexa categories.",
                )
                col_apply, col_cancel, _ = st.columns([1, 1, 2])
                with col_apply:
                    if st.button("✅ Apply Selection", key="apply_correction", use_container_width=True):
                        st.session_state["user_confirmed_material"] = corrected
                        st.session_state["user_correction_mode"] = False
                        st.rerun()
                with col_cancel:
                    if st.button("Cancel", key="cancel_correction", use_container_width=True):
                        st.session_state["user_correction_mode"] = False
                        st.rerun()

    # --------------------------------------------------
    # 3. HOUSEHOLD PHYSICAL ASSESSMENT
    # --------------------------------------------------
    with st.container(border=True):
        st.markdown("### 📝 Household Physical Assessment")
        st.caption("Assess physical condition and contamination level to evaluate safe recovery pathway eligibility.")

        q_col, c_col, cont_col = st.columns(3)
        with q_col:
            quantity = st.number_input(
                "Quantity of Items:",
                min_value=1,
                max_value=100,
                value=min(max(1, det_count), 100),
                step=1,
                key="input_quantity",
                help="Estimated number of discrete waste items present.",
            )
        with c_col:
            condition = st.selectbox(
                "Physical Condition:",
                options=ALLOWED_CONDITIONS,
                index=0,
                key="input_condition",
                help="Physical integrity of the waste material.",
            )
        with cont_col:
            contamination = st.selectbox(
                "Contamination Level:",
                options=ALLOWED_CONTAMINATIONS,
                index=0,
                key="input_contamination",
                help="Presence of grease, food residue, chemicals, or other contaminants.",
            )

        # Profile creation and persistence
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

        # Update session scan history
        history = st.session_state.get("scan_history", [])
        scan_entry = {
            "filename": current_filename,
            "material": confirmed_material,
            "confidence": result.get("confidence", 0),
            "quantity": int(quantity),
            "condition": condition,
            "contamination": contamination,
        }
        if not history or history[-1] != scan_entry:
            history.append(scan_entry)
            st.session_state["scan_history"] = history
            st.session_state["scan_count"] = len(history)

        # Persist to data store
        try:
            save_scan({
                "detected_material": confirmed_material,
                "model_label": result.get("model_label") or result.get("label"),
                "confidence": result.get("confidence"),
                "detected_object_count": det_count,
                "confirmed_quantity": int(quantity),
                "image_filename": current_filename,
            })
            save_waste_profile({
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

        st.success("✅ **Structured Waste Profile ready.** Material, condition, and contamination parameters are recorded.")
        st.page_link("pages/2_Results.py", label="View Profile & Feasible Pathways →", use_container_width=True)


# --------------------------------------------------
# 2. RESULTS
# --------------------------------------------------

def render_results():
    st.title("📊 Waste Profile Results")
    profile = require_profile()
    if not profile:
        return

    detection = st.session_state.get("detection_result", {})
    image = st.session_state.get("uploaded_image")
    annotated = st.session_state.get("annotated_image")

    left, right = st.columns([1, 1], gap="medium")
    with left:
        display_img = annotated or image
        if display_img:
            st.image(
                display_img,
                caption=st.session_state.get("uploaded_filename", "Scanned item"),
                use_container_width=True,
            )
    with right:
        st.metric("AI confidence", f"{float(profile.get('confidence', 0)) * 100:.1f}%")
        st.write("**Material:**", profile.get("material", "Unknown"))
        st.write("**Model label:**", profile.get("model_label") or detection.get("model_label") or "Not recorded")
        st.write("**Quantity confirmed:**", profile.get("confirmed_quantity", 1))
        st.write("**Condition:**", profile.get("condition", "Unknown"))
        st.write("**Contamination:**", profile.get("contamination", "Unknown"))
        st.write("**Objects detected:**", profile.get("detected_object_count", detection.get("count", 0)))

    # --------------------------------------------------
    # DETECTED MATERIAL BREAKDOWN
    # --------------------------------------------------
    counts = profile.get("material_counts") or detection.get("material_counts", {})
    valid_counts = {
        str(k).strip(): int(v)
        for k, v in counts.items()
        if isinstance(v, (int, float)) and int(v) > 0
    } if isinstance(counts, dict) and counts else {}

    total_detected = sum(valid_counts.values()) if valid_counts else 0

    st.markdown("---")
    with st.container(border=True):
        st.subheader("📦 Detected Material Breakdown")

        if total_detected > 0:
            header_col1, header_col2 = st.columns([3, 1])
            with header_col1:
                st.caption(
                    f"Visual composition distribution across **{len(valid_counts)}** detected "
                    f"material categor{'ies' if len(valid_counts) != 1 else 'y'}."
                )
            with header_col2:
                st.metric("Total Objects", f"{total_detected}")

            sorted_materials = sorted(valid_counts.items(), key=lambda item: item[1], reverse=True)

            for material_name, count in sorted_materials:
                pct = (count / total_detected) * 100.0
                ratio = min(max(count / total_detected, 0.0), 1.0)

                col_name, col_meta = st.columns([3, 2])
                with col_name:
                    st.markdown(f"**{material_name.title()}**")
                with col_meta:
                    st.markdown(
                        f"<div style='text-align:right; font-weight:600;'>"
                        f"{count} object{'s' if count != 1 else ''} &nbsp;•&nbsp; "
                        f"<span style='color:var(--rx-primary); font-weight:750;'>{pct:.1f}%</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                st.progress(ratio)
        else:
            primary_label = profile.get("material") or detection.get("label") or "Unknown"
            if primary_label and primary_label != "Unknown":
                st.info(f"ℹ️ Primary detected material is **{primary_label.title()}** (Single uniform composition).")
            else:
                st.info("ℹ️ No multi-material breakdown available for this scan.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.page_link("pages/3_Recovery.py", label="Explore recovery pathways →", use_container_width=True)
    with c2:
        st.page_link("pages/4_Constraints.py", label="Set household constraints →", use_container_width=True)
    with c3:
        st.page_link("pages/5_Recommendations.py", label="Get ranked recommendations →", use_container_width=True)


# --------------------------------------------------
# 3. RECOVERY PATHWAYS
# --------------------------------------------------

def render_pathways():
    st.title("♻️ Recovery Pathways")
    profile = current_profile()
    materials = get_available_materials()

    if not materials:
        st.error("No recovery pathways were loaded. Check data/knowledge/recovery_pathways.csv.")
        return

    default_material = profile.get("material")
    index = materials.index(default_material) if default_material in materials else 0
    material = st.selectbox("Material category", materials, index=index)
    kind = st.selectbox(
        "Recovery method",
        ["All", "repair", "reuse", "upcycle", "recycle", "dispose"],
    )
    rows = get_recovery_pathways(
        material=material,
        pathway_type=None if kind == "All" else kind,
    )
    st.caption(f"{len(rows)} matching pathway(s)")

    for p in rows:
        with st.expander(f"{p.get('title', 'Untitled')} — {p.get('pathway_type', '').title()}"):
            st.write(p.get("description", ""))
            a, b, c = st.columns(3)
            a.write(f"**Cost:** ₹{p.get('budget', '0')}")
            b.write(f"**Time:** {p.get('time_required', 'Unknown')}")
            c.write(f"**Skill:** {p.get('skill_level', 'Beginner')}")
            st.write("**Tools:**", p.get("tools", "None"))
            st.write("**Extra materials:**", p.get("extra_materials", "None"))
            st.write("**Condition requirement:**", p.get("condition_requirement", "Any"))
            st.write("**Expected output:**", p.get("expected_output", "Not specified"))
            st.write("**Procedure:**")
            st.write(p.get("steps", "No steps recorded."))
            st.write("**Fallback:**", p.get("fallback", "Not specified"))
            st.caption(
                f"Source: {p.get('source', 'Not recorded')} | "
                f"Verification: {p.get('verification_status', 'Unknown')}"
            )
            col_btn, col_exec = st.columns([1, 1])
            with col_btn:
                if st.button("Use this pathway", key=f"use_{p.get('pathway_id')}"):
                    st.session_state["selected_pathway_id"] = p.get("pathway_id")
                    st.success("Pathway selected. Open Execution to check safety and feasibility.")
            with col_exec:
                st.page_link("pages/6_Execution.py", label="Open Execution Guidance →")


# --------------------------------------------------
# 4. CONSTRAINTS
# --------------------------------------------------

def render_constraints():
    st.title("⚙️ Household Constraints")
    defaults = get_default_constraints()
    with st.form("renexa_constraints_form"):
        budget_options = ["₹0", "₹50", "₹100", "₹250", "₹500+"]
        time_options = ["5 minutes", "15 minutes", "30 minutes", "1 hour", "2+ hours"]
        budget_now = st.session_state.get("budget", defaults["budget"])
        time_now = st.session_state.get("time", defaults["time"])
        budget = st.select_slider(
            "Maximum budget",
            options=budget_options,
            value=budget_now if budget_now in budget_options else "₹0",
        )
        time_available = st.select_slider(
            "Available time",
            options=time_options,
            value=time_now if time_now in time_options else "15 minutes",
        )
        tool_options = [
            "Scissors", "Utility knife", "Glue", "Tape", "Screwdriver",
            "Hammer", "Needle", "Drill", "Trowel", "Measuring tape",
            "Binder clip",
        ]
        tools = st.multiselect(
            "Tools available at home",
            tool_options,
            default=[x for x in st.session_state.get("tools", []) if x in tool_options],
        )
        skill = st.selectbox(
            "DIY skill level", ["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(
                st.session_state.get("skill", "Beginner")
            ),
        )
        workspace = st.selectbox(
            "Workspace", ["Indoor", "Outdoor", "Any"],
            index=["Indoor", "Outdoor", "Any"].index(
                st.session_state.get("workspace", "Any")
                if st.session_state.get("workspace", "Any") in ["Indoor", "Outdoor", "Any"]
                else "Any"
            ),
        )
        extras = st.text_input(
            "Extra materials (comma-separated)",
            value=", ".join(st.session_state.get("extra_materials", [])),
        )
        safety = st.radio(
            "Safety preference",
            ["Only low-risk options", "Allow medium-risk options with warning"],
            index=0 if st.session_state.get(
                "safety_preference", "Only low-risk options"
            ) == "Only low-risk options" else 1,
        )
        save = st.form_submit_button("Save constraints and evaluate")

    if save:
        st.session_state["budget"] = budget
        st.session_state["time"] = time_available
        st.session_state["tools"] = tools
        st.session_state["skill"] = skill
        st.session_state["workspace"] = workspace
        st.session_state["extra_materials"] = [
            x.strip() for x in extras.split(",") if x.strip()
        ]
        st.session_state["safety_preference"] = safety
        st.success("Constraints saved.")

    profile = current_profile()
    if profile.get("material") and profile.get("material") != "Unknown":
        evaluations = get_evaluations(profile)
        if not evaluations:
            st.info("No matching pathways for this material.")
            return

        eligible = sum(bool(x.get("eligible")) for x in evaluations)
        blocked = sum(x.get("safety_status") == "BLOCK" for x in evaluations)
        a, b, c = st.columns(3)
        a.metric("Candidate pathways", len(evaluations))
        b.metric("Eligible", eligible)
        c.metric("Safety blocked", blocked)

        for item in evaluations:
            p = item.get("pathway", {})
            with st.expander(f"{p.get('title', 'Pathway')} — {'ELIGIBLE' if item.get('eligible') else 'NOT ELIGIBLE'}"):
                st.write("**Safety status:**", item.get("safety_status"))
                st.write("**Constraint status:**", item.get("constraint_status"))
                for reason in item.get("reasons", []):
                    st.warning(reason)
                for warning in item.get("warnings", []):
                    st.info(warning)
                if item.get("missing_tools"):
                    st.write("**Missing tools:**", ", ".join(item["missing_tools"]))
                if item.get("missing_materials"):
                    st.write("**Missing materials:**", ", ".join(item["missing_materials"]))

        st.page_link("pages/5_Recommendations.py", label="View Ranked Recommendations →")
    else:
        st.info("Scan and confirm a waste item to evaluate its pathways against these constraints.")


# --------------------------------------------------
# 5. RECOMMENDATIONS
# --------------------------------------------------

def render_recommendations():
    st.title("🎯 Feasible Recommendations")
    profile = require_profile()
    if not profile:
        return

    evaluations = get_evaluations(profile)
    ranked = get_ranked(profile, top_k=None)

    a, b, c = st.columns(3)
    a.metric("Candidate pathways", len(evaluations))
    b.metric("Eligible pathways", sum(bool(x.get("eligible")) for x in evaluations))
    c.metric("Ranked recommendations", len(ranked))

    if not ranked:
        st.warning("No pathways passed the safety and feasibility checks. Review your constraints.")
        st.page_link("pages/4_Constraints.py", label="Review constraints →")
        return

    for rec in ranked:
        p = rec.get("pathway", {})
        with st.container(border=True):
            st.subheader(f"#{rec.get('rank', '?')} — {rec.get('title', p.get('title', 'Pathway'))}")
            st.metric("MCDA score", f"{rec.get('score', 0):.2f}/100")
            st.caption(
                f"{rec.get('pathway_type', p.get('pathway_type', '')).title()} | "
                f"₹{rec.get('budget', p.get('budget', '0'))} | "
                f"{rec.get('time_required', p.get('time_required', 'Unknown'))}"
            )
            for reason in rec.get("why_this", []):
                st.write(f"• {reason}")
            if rec.get("warnings"):
                for warning in rec["warnings"]:
                    st.warning(warning)
            col_act1, col_act2 = st.columns([1, 1])
            with col_act1:
                if st.button("Select for execution", key=f"select_{rec.get('pathway_id')}"):
                    st.session_state["selected_pathway_id"] = rec.get("pathway_id")
                    try:
                        save_recommendation({
                            "pathway_id": rec.get("pathway_id"),
                            "rank": rec.get("rank"),
                            "mcda_score": rec.get("score"),
                            "title": p.get("title"),
                            "material": profile.get("material"),
                        })
                    except Exception:
                        pass
                    st.success("Selected. Open Execution Guidance to review preparation and instructions.")
            with col_act2:
                st.page_link("pages/6_Execution.py", label="Open Execution Guidance →")


# --------------------------------------------------
# 6. EXECUTION & TUTORIALS
# --------------------------------------------------

def render_execution(tutorials=False):
    st.title("📘 Tutorials & Physical Guides" if tutorials else "🧰 Execution Guidance")
    profile = require_profile()
    if not profile:
        return

    pathways = pathway_list(profile)
    if not pathways:
        st.info("No pathways are available for this material.")
        return

    ids = [p.get("pathway_id") for p in pathways]
    saved = st.session_state.get("selected_pathway_id")
    selected_index = ids.index(saved) if saved in ids else 0
    selected_id = st.selectbox(
        "Choose a recovery pathway",
        ids,
        index=selected_index,
        format_func=lambda pid: next(
            (p.get("title", pid) for p in pathways if p.get("pathway_id") == pid), pid
        ),
    )
    pathway = next(p for p in pathways if p.get("pathway_id") == selected_id)
    guide = get_execution_guide(
        pathway,
        user_constraints=current_constraints(),
        waste_profile=profile,
    )

    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.write("**Execution readiness:**", guide.get("execution_status"))
        st.write("**Safety rating:**", guide.get("safety_status"))
    with col_stat2:
        st.write("**Required tools:**", ", ".join(guide.get("tools", [])) or "None listed")
        st.write("**Extra materials:**", ", ".join(guide.get("extra_materials", [])) or "None listed")

    for warning in guide.get("warnings", []):
        st.warning(warning)
    for reason in guide.get("reasons", []):
        st.info(reason)

    if guide.get("can_execute"):
        st.subheader("Step-by-step procedure")
        for i, step in enumerate(guide.get("steps", []), 1):
            st.write(f"{i}. {step}")
        st.success(f"Expected output: {guide.get('expected_output', 'Not specified')}")
        st.write("**Fallback:**", guide.get("fallback", "Not specified"))
    else:
        st.warning("Physical execution is disabled until feasibility or safety conditions are met.")

    st.divider()
    st.subheader("Verified Video References")
    verified_tutorials = guide.get("verified_tutorials", [])
    if verified_tutorials:
        for tut in verified_tutorials:
            with st.container(border=True):
                st.write(f"**{tut.get('title') or tut.get('product_name')}**")
                st.caption(f"Channel: {tut.get('youtube_channel', 'Unknown')} | Verified: ✅ Yes")
                url = tut.get("youtube_url")
                if url:
                    st.video(url)
    else:
        st.info(f"No verified video tutorials currently indexed for {pathway.get('title', 'this pathway')}.")
        st.caption("ReNexa strictly displays verified catalogued video references and does not generate unverified links.")


# --------------------------------------------------
# 7. SCAN HISTORY
# --------------------------------------------------

def render_history():
    st.title("🕘 Scan History")
    session_records = list(st.session_state.get("scan_history", []))

    st.subheader("Current Session Scans")
    if session_records:
        st.dataframe(session_records, use_container_width=True)
        st.download_button(
            "Download this session's history",
            data=json.dumps(session_records, indent=2),
            file_name="renexa_scan_history.json",
            mime="application/json",
        )
    else:
        st.info("No scans recorded in this active session yet.")

    try:
        persisted = get_user_scans(limit=25)
        if persisted:
            st.subheader("Persisted Scan History")
            st.dataframe(persisted, use_container_width=True)
    except Exception:
        pass


# --------------------------------------------------
# 8. OUTCOME FEEDBACK
# --------------------------------------------------

def render_outcome():
    st.title("📝 Recovery Outcome Feedback")
    profile = current_profile()
    pathways = pathway_list(profile)
    if not pathways:
        st.info("Scan a waste item first to select its recovery pathway.")
        return

    saved_id = st.session_state.get("selected_pathway_id")
    ids = [p.get("pathway_id") for p in pathways]
    idx = ids.index(saved_id) if saved_id in ids else 0
    selected = st.selectbox(
        "Pathway attempted",
        ids,
        index=idx,
        format_func=lambda pid: next(
            (p.get("title", pid) for p in pathways if p.get("pathway_id") == pid), pid
        ),
    )
    pathway = next(p for p in pathways if p.get("pathway_id") == selected)

    with st.form("outcome_form"):
        status = st.selectbox(
            "Outcome",
            ["not_attempted", "successful", "partial", "failed"],
            index=0,
        )
        actual_time = st.number_input("Actual time taken (minutes)", min_value=0, value=0)
        tools_missing = st.checkbox("Were tools missing?")
        materials_missing = st.checkbox("Were extra materials missing?")
        safety_issue = st.checkbox("Did you encounter a safety issue?")
        failure_reason = st.selectbox(
            "Main challenge",
            ["other", "missing_tool", "missing_material", "time_underestimated",
             "condition_problem", "instruction_problem", "safety_issue"],
        )
        notes = st.text_area("Notes (optional)")
        submit = st.form_submit_button("Save outcome")

    if submit:
        record = {
            "pathway_id": selected,
            "pathway_title": pathway.get("title", selected),
            "material": profile.get("material", "Unknown"),
            "attempt_status": status,
            "estimated_time_minutes": pathway.get("time_required", ""),
            "actual_time_minutes": actual_time if actual_time > 0 else None,
            "missing_tools": tools_missing,
            "missing_materials": materials_missing,
            "safety_issue": safety_issue,
            "failure_reason": failure_reason,
            "notes": notes.strip(),
        }
        if save_outcome_feedback(record):
            if status == "successful":
                st.session_state["successful_recoveries"] = st.session_state.get("successful_recoveries", 0) + 1
            st.success("Outcome feedback saved.")
        else:
            st.error("Feedback could not be saved. Check storage permissions.")

    st.subheader("Recorded Feedback History")
    feedback = load_outcome_feedback()
    if feedback:
        st.dataframe(feedback, use_container_width=True)
    else:
        st.info("No feedback records are available yet.")


# --------------------------------------------------
# 9. IMPACT ANALYSIS
# --------------------------------------------------

def render_impact():
    st.title("🌍 Recovery Impact & Validation")
    feedback = load_outcome_feedback()
    metrics = calculate_outcome_metrics(feedback)

    a, b, c = st.columns(3)
    a.metric("Recorded Outcomes", metrics["total_recorded"])
    b.metric("Recovery Attempts", metrics["total_attempted"])
    c.metric("Successful Attempts", metrics["successful_count"])

    d, e, f = st.columns(3)
    d.metric("Success Rate (RESR)", f"{metrics['resr']:.1f}%")
    e.metric("Recipe Reliability (OVRR)", f"{metrics['ovrr']:.1f}%")
    mae_str = f"{metrics['time_mae']:.1f} mins" if metrics["time_mae"] is not None else "N/A"
    f.metric("Time Estimation MAE", mae_str)

    st.caption(
        "All metrics are calculated strictly from user-confirmed outcome feedback records. "
        "ReNexa does not fabricate speculative carbon credits or estimated CO₂ savings."
    )

    if feedback:
        st.subheader("Detailed Outcome Feedback Records")
        st.dataframe(feedback, use_container_width=True)


# --------------------------------------------------
# 10. RESEARCH BENCHMARK
# --------------------------------------------------

def render_benchmark():
    st.title("📈 Research Benchmark Evaluation")
    path = ROOT / "data" / "phase8_benchmark.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            st.caption("Phase 8 empirical benchmark results (100 independent multi-criteria decision scenarios).")
            st.json(data)
        except Exception as exc:
            st.error(f"Could not read benchmark data: {exc}")
    else:
        st.info("No benchmark summary file found at data/phase8_benchmark.json.")

    if st.button("Run Live Decision Benchmark Evaluation"):
        with st.spinner("Evaluating 100 decision scenarios across all material classes…"):
            try:
                from services.benchmark_evaluation import evaluate_benchmarks
                results = evaluate_benchmarks()
                st.success(f"Benchmark completed! Overall Accuracy: {results.get('overall_accuracy', 0):.1%}")
                st.write("**Classification Report:**")
                st.code(results.get("classification_report_str", ""))
            except Exception as exc:
                st.error(f"Evaluation error: {exc}")


# --------------------------------------------------
# FEATURE PAGE DISPATCHER
# --------------------------------------------------

def render_feature_page(name):
    renderers = {
        "Scan Waste": render_scan_waste,
        "Results": render_results,
        "Pathways": render_pathways,
        "Constraints": render_constraints,
        "Recommendations": render_recommendations,
        "Execution": lambda: render_execution(False),
        "Tutorials": lambda: render_execution(True),
        "History": render_history,
        "Outcome": render_outcome,
        "Impact": render_impact,
        "Benchmark": render_benchmark,
    }
    renderer = renderers.get(name)
    if renderer:
        renderer()
    else:
        st.error(f"Unknown ReNexa feature page: {name}")
