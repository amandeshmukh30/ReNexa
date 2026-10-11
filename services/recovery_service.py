"""
ReNexa — Recovery Knowledge Base Service
==========================================
Loads, validates, and queries structured recovery pathways from CSV.

Supports recovery pathways across 5 canonical types:
    - repair
    - reuse
    - upcycle
    - recycle
    - dispose

Design Principles:
- Material-level matching: Normalizes glass sub-labels ("brown-glass" -> "glass").
- No Ranking in Phase 4: Returns all candidate pathways for downstream feasibility evaluation.
- Pure Python/CSV: No database, vector embeddings, or LLM dependencies.
"""

import csv
import os

# Paths to the recovery pathways dataset (check knowledge dir first, then fallback to data dir)
_KNOWLEDGE_CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "knowledge", "recovery_pathways.csv")
)
_FALLBACK_CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "recovery_pathways.csv")
)
DEFAULT_CSV_PATH = (
    _KNOWLEDGE_CSV_PATH if os.path.isfile(_KNOWLEDGE_CSV_PATH) else _FALLBACK_CSV_PATH
)

# Required columns in the CSV schema
REQUIRED_COLUMNS = [
    "pathway_id",
    "input_material",
    "input_item",
    "pathway_type",
    "title",
    "description",
    "condition_requirement",
    "min_quantity",
    "tools",
    "extra_materials",
    "budget",
    "time_required",
    "skill_level",
    "workspace",
    "safety_level",
    "steps",
    "expected_output",
    "fallback",
    "source",
    "verification_status",
    "last_reviewed",
]

# Canonical allowed pathway types
ALLOWED_PATHWAY_TYPES = {
    "repair",
    "reuse",
    "upcycle",
    "recycle",
    "dispose",
}

# Glass label normalisation set
GLASS_VARIANTS = {"brown-glass", "green-glass", "white-glass", "glass"}

# Material alias mappings (e.g. detector class 'organic' -> KB class 'biological')
MATERIAL_ALIASES = {
    "organic": "biological",
    "bio": "biological",
    "food": "biological",
}


def normalize_material_name(material):
    """
    Normalize raw or sub-class material name to canonical category.
    Example: 'brown-glass' -> 'glass', 'Plastic' -> 'plastic', 'organic' -> 'biological'.
    """
    if not material:
        return "unknown"
    mat = str(material).strip().lower()
    if mat in GLASS_VARIANTS:
        return "glass"
    if mat in MATERIAL_ALIASES:
        return MATERIAL_ALIASES[mat]
    return mat


def load_recovery_pathways(csv_path=None):
    """
    Read and validate recovery_pathways.csv.

    Args:
        csv_path: Optional custom path to CSV file.

    Returns:
        list[dict]: List of validated and normalized recovery pathway dicts.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If required columns are missing or values are invalid.
    """
    path = csv_path or DEFAULT_CSV_PATH

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Recovery pathways CSV not found at: {path}")

    pathways = []
    with open(path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Validate required headers
        headers = reader.fieldnames or []
        missing = [col for col in REQUIRED_COLUMNS if col not in headers]
        if missing:
            raise ValueError(f"Recovery CSV missing required columns: {missing}")

        for row_idx, row in enumerate(reader, start=2):
            # Verify non-empty required fields
            pathway_id = (row.get("pathway_id") or "").strip()
            title = (row.get("title") or "").strip()
            raw_mat = (row.get("input_material") or "").strip()
            raw_type = (row.get("pathway_type") or "").strip().lower()

            if not title:
                raise ValueError(f"Row {row_idx}: 'title' must not be empty.")

            if raw_type not in ALLOWED_PATHWAY_TYPES:
                raise ValueError(
                    f"Row {row_idx}: invalid pathway_type '{raw_type}'. "
                    f"Must be one of {ALLOWED_PATHWAY_TYPES}"
                )

            # Parse numeric min_quantity safely
            try:
                min_qty = int(row.get("min_quantity", 1))
            except (ValueError, TypeError):
                min_qty = 1

            # Build standardized pathway dictionary
            entry = {
                "pathway_id": pathway_id,
                "input_material": normalize_material_name(raw_mat),
                "input_item": (row.get("input_item") or "Unknown").strip(),
                "pathway_type": raw_type,
                "title": title,
                "description": (row.get("description") or "").strip(),
                "condition_requirement": (row.get("condition_requirement") or "Any").strip(),
                "min_quantity": min_qty,
                "tools": (row.get("tools") or "None").strip(),
                "extra_materials": (row.get("extra_materials") or "None").strip(),
                "budget": (row.get("budget") or "0").strip(),
                "time_required": (row.get("time_required") or "Unknown").strip(),
                "skill_level": (row.get("skill_level") or "Beginner").strip(),
                "workspace": (row.get("workspace") or "Any").strip(),
                "safety_level": (row.get("safety_level") or "Low").strip(),
                "steps": (row.get("steps") or "").strip(),
                "expected_output": (row.get("expected_output") or "").strip(),
                "fallback": (row.get("fallback") or "").strip(),
                "source": (row.get("source") or "Internal prototype rule").strip(),
                "verification_status": (row.get("verification_status") or "prototype").strip(),
                "last_reviewed": (row.get("last_reviewed") or "").strip(),
            }
            pathways.append(entry)

    return pathways


def get_recovery_pathways(material=None, pathway_type=None, csv_path=None):
    """
    Query recovery pathways matching material and/or pathway type.

    Args:
        material: Normalized or raw material name (e.g. 'plastic', 'glass', 'brown-glass').
        pathway_type: Optional filter by type ('repair', 'reuse', 'upcycle', 'recycle', 'dispose').
        csv_path: Optional custom path to CSV.

    Returns:
        list[dict]: List of matching pathways. Returns empty list if no matches or unknown.
    """
    if material is not None and str(material).strip().lower() in ("unknown", "none", ""):
        return []

    all_pathways = load_recovery_pathways(csv_path=csv_path)
    target_mat = normalize_material_name(material) if material else None
    target_type = str(pathway_type).strip().lower() if pathway_type else None

    results = []
    for p in all_pathways:
        if target_mat and p["input_material"] != target_mat:
            continue
        if target_type and p["pathway_type"] != target_type:
            continue
        results.append(p)

    return results


def get_pathways_for_profile(waste_profile, csv_path=None):
    """
    Helper to fetch all matching pathways directly from a structured waste profile.

    Args:
        waste_profile: Waste profile dict containing at least 'material'.

    Returns:
        list[dict]: List of matching recovery pathways.
    """
    if not waste_profile or not isinstance(waste_profile, dict):
        return []
    material = waste_profile.get("material")
    return get_recovery_pathways(material=material, csv_path=csv_path)


def get_available_materials(csv_path=None):
    """Return a sorted list of unique materials present in the knowledge base."""
    all_pathways = load_recovery_pathways(csv_path=csv_path)
    return sorted(list({p["input_material"] for p in all_pathways}))


def get_all_pathways(csv_path=None):
    """
    Return all validated recovery pathways in the knowledge base.
    Compatible helper for discovery, tutorials, and catalog exploration.
    """
    return load_recovery_pathways(csv_path=csv_path)


# ── Video Index & Recovery Projects Knowledge Base ─────────────────────────

_KNOWLEDGE_VIDEO_CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "knowledge", "video_index.csv")
)
_FALLBACK_VIDEO_CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "video_index.csv")
)
DEFAULT_VIDEO_CSV_PATH = (
    _KNOWLEDGE_VIDEO_CSV_PATH if os.path.isfile(_KNOWLEDGE_VIDEO_CSV_PATH) else _FALLBACK_VIDEO_CSV_PATH
)

_KNOWLEDGE_PROJECTS_CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "knowledge", "recovery_projects.csv")
)
_FALLBACK_PROJECTS_CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "recovery_projects.csv")
)
DEFAULT_PROJECTS_CSV_PATH = (
    _KNOWLEDGE_PROJECTS_CSV_PATH if os.path.isfile(_KNOWLEDGE_PROJECTS_CSV_PATH) else _FALLBACK_PROJECTS_CSV_PATH
)


def load_video_index(csv_path=None):
    """
    Read and parse video_index.csv.

    Args:
        csv_path: Optional custom path to video_index.csv.

    Returns:
        list[dict]: List of video index dictionaries.
    """
    path = csv_path or DEFAULT_VIDEO_CSV_PATH
    if not os.path.isfile(path):
        return []

    videos = []
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = (row.get("project_id") or "").strip()
            url = (row.get("youtube_url") or "").strip()
            title = (row.get("youtube_title") or "").strip()
            channel = (row.get("youtube_channel") or "").strip()
            verified = (row.get("youtube_verified") or "No").strip()
            relevance = (row.get("video_relevance") or "").strip()
            notes = (row.get("notes") or "").strip()

            videos.append({
                "project_id": pid,
                "youtube_url": url,
                "youtube_title": title,
                "youtube_channel": channel,
                "youtube_verified": verified,
                "video_relevance": relevance,
                "notes": notes,
            })
    return videos


def load_recovery_projects(csv_path=None):
    """
    Read and parse recovery_projects.csv.

    Args:
        csv_path: Optional custom path to recovery_projects.csv.

    Returns:
        list[dict]: List of recovery project dictionaries.
    """
    path = csv_path or DEFAULT_PROJECTS_CSV_PATH
    if not os.path.isfile(path):
        return []

    projects = []
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = (row.get("project_id") or "").strip()
            steps = []
            for i in range(1, 7):
                st = (row.get(f"step_{i}") or "").strip()
                if st:
                    steps.append(st)

            projects.append({
                "project_id": pid,
                "waste_item": (row.get("waste_item") or "").strip(),
                "material": (row.get("material") or "").strip(),
                "object_type": (row.get("object_type") or "").strip(),
                "condition": (row.get("condition") or "").strip(),
                "product_name": (row.get("product_name") or "").strip(),
                "product_category": (row.get("product_category") or "").strip(),
                "recovery_type": (row.get("recovery_type") or "").strip(),
                "required_tools": (row.get("required_tools") or "").strip(),
                "additional_materials": (row.get("additional_materials") or "").strip(),
                "required_waste_quantity": (row.get("required_waste_quantity") or "1").strip(),
                "preparation": (row.get("preparation") or "").strip(),
                "steps": steps,
                "difficulty": (row.get("difficulty") or "Easy").strip(),
                "time_minutes": (row.get("time_minutes") or "15").strip(),
                "safety_level": (row.get("safety_level") or "Low").strip(),
                "adult_supervision": (row.get("adult_supervision") or "No").strip(),
                "feasibility": (row.get("feasibility") or "High").strip(),
                "skill_level": (row.get("skill_level") or "Beginner").strip(),
                "youtube_url": (row.get("youtube_url") or "").strip(),
                "youtube_title": (row.get("youtube_title") or "").strip(),
                "youtube_channel": (row.get("youtube_channel") or "").strip(),
                "youtube_verified": (row.get("youtube_verified") or "No").strip(),
                "source_name": (row.get("source_name") or "").strip(),
                "source_url": (row.get("source_url") or "").strip(),
                "source_type": (row.get("source_type") or "").strip(),
                "notes": (row.get("notes") or "").strip(),
            })
    return projects


def map_project_material(raw_material, waste_item=""):
    """
    Map recovery project material and waste_item to canonical ReNexa material category.
    """
    mat = str(raw_material or "").strip().lower()
    item = str(waste_item or "").strip().lower()

    if mat in ("pet", "hdpe", "plastic", "pvc", "pp"):
        return "plastic"
    if mat in ("steel", "metal", "aluminum", "tin", "iron"):
        return "metal"
    if mat in ("cotton", "fabric", "textile", "denim", "clothes", "wool"):
        return "clothes"
    if mat in ("glass", "brown-glass", "green-glass", "white-glass"):
        return "glass"
    if mat == "cardboard" or "cardboard" in item or "carton" in item or "cereal" in item:
        return "cardboard"
    if mat in ("paper", "newspaper", "tp roll", "tp_roll") or "paper" in item or "roll" in item:
        return "paper"
    if mat in ("cork", "other", "wood", "rubber"):
        return "other"
    return normalize_material_name(mat)


def get_tutorials(
    material=None,
    category=None,
    verified_only=True,
    video_csv_path=None,
    projects_csv_path=None,
):
    """
    Query tutorial records combined from video_index.csv and recovery_projects.csv.

    Args:
        material: Optional canonical or raw material filter (e.g. 'plastic', 'glass').
        category: Optional category filter (e.g. 'Gardening', 'Office', 'Decor').
        verified_only: If True, only returns entries with youtube_verified == 'Yes' and valid URL.
        video_csv_path: Optional custom path for video_index.csv.
        projects_csv_path: Optional custom path for recovery_projects.csv.

    Returns:
        list[dict]: List of enriched tutorial objects.
    """
    videos = load_video_index(csv_path=video_csv_path)
    projects = load_recovery_projects(csv_path=projects_csv_path)

    v_map = {v["project_id"]: v for v in videos if v.get("project_id")}

    target_mat = normalize_material_name(material) if material else None
    target_cat = str(category).strip().lower() if category and str(category).strip().lower() != "all" else None

    tutorials = []
    # Iterate over projects (and any videos not in projects)
    seen_pids = set()

    for p in projects:
        pid = p["project_id"]
        seen_pids.add(pid)
        v = v_map.get(pid, {})

        is_verified_raw = (v.get("youtube_verified") or p.get("youtube_verified") or "No").strip()
        is_verified = is_verified_raw.lower() in ("yes", "true", "1")

        url = (v.get("youtube_url") or p.get("youtube_url") or "").strip()
        title = (v.get("youtube_title") or p.get("youtube_title") or p.get("product_name") or "").strip()
        channel = (v.get("youtube_channel") or p.get("youtube_channel") or p.get("source_name") or "").strip()

        if verified_only and (not is_verified or not url or not url.startswith("http")):
            continue

        c_mat = map_project_material(p.get("material"), p.get("waste_item"))
        if target_mat and target_mat != "all" and c_mat != target_mat and normalize_material_name(p.get("material")) != target_mat:
            continue

        p_cat = (p.get("product_category") or "").strip()
        if target_cat and p_cat.lower() != target_cat:
            continue

        tutorials.append({
            "project_id": pid,
            "product_name": p.get("product_name", ""),
            "title": title or p.get("product_name", ""),
            "material": c_mat,
            "raw_material": p.get("material", ""),
            "waste_item": p.get("waste_item", ""),
            "category": p_cat,
            "recovery_type": (p.get("recovery_type") or "Upcycle").strip(),
            "tools": p.get("required_tools", ""),
            "additional_materials": p.get("additional_materials", ""),
            "required_waste_quantity": p.get("required_waste_quantity", "1"),
            "preparation": p.get("preparation", ""),
            "steps": p.get("steps", []),
            "difficulty": p.get("difficulty", "Easy"),
            "time_minutes": p.get("time_minutes", "15"),
            "skill_level": p.get("skill_level", "Beginner"),
            "safety_level": p.get("safety_level", "Low"),
            "youtube_url": url,
            "youtube_title": title,
            "youtube_channel": channel,
            "youtube_verified": "Yes" if is_verified else "No",
            "video_relevance": v.get("video_relevance", "High"),
            "notes": v.get("notes") or p.get("notes", ""),
        })

    # Also include any standalone video index entries not present in recovery_projects
    for v in videos:
        pid = v.get("project_id")
        if not pid or pid in seen_pids:
            continue

        is_verified_raw = (v.get("youtube_verified") or "No").strip()
        is_verified = is_verified_raw.lower() in ("yes", "true", "1")
        url = (v.get("youtube_url") or "").strip()
        title = (v.get("youtube_title") or "").strip()
        channel = (v.get("youtube_channel") or "").strip()

        if verified_only and (not is_verified or not url or not url.startswith("http")):
            continue

        tutorials.append({
            "project_id": pid,
            "product_name": title,
            "title": title,
            "material": "unknown",
            "raw_material": "",
            "waste_item": "",
            "category": "General",
            "recovery_type": "Upcycle",
            "tools": "",
            "additional_materials": "",
            "required_waste_quantity": "1",
            "preparation": "",
            "steps": [],
            "difficulty": "Easy",
            "time_minutes": "15",
            "skill_level": "Beginner",
            "safety_level": "Low",
            "youtube_url": url,
            "youtube_title": title,
            "youtube_channel": channel,
            "youtube_verified": "Yes" if is_verified else "No",
            "video_relevance": v.get("video_relevance", "High"),
            "notes": v.get("notes", ""),
        })

    return tutorials


def get_tutorials_for_pathway(
    pathway_or_id,
    verified_only=True,
    video_csv_path=None,
    projects_csv_path=None,
):
    """
    Match and retrieve relevant verified tutorial videos for a given recovery pathway.

    Args:
        pathway_or_id: Pathway dict or string pathway_id.
        verified_only: If True, only returns verified video records.
        video_csv_path: Optional custom path for video_index.csv.
        projects_csv_path: Optional custom path for recovery_projects.csv.

    Returns:
        list[dict]: Ranked list of matched tutorial dicts for the pathway.
    """
    if not pathway_or_id:
        return []

    # Resolve pathway dict
    if isinstance(pathway_or_id, dict):
        pw = pathway_or_id
    else:
        all_pws = load_recovery_pathways()
        pw = next((p for p in all_pws if str(p.get("pathway_id", "")).upper() == str(pathway_or_id).strip().upper()), None)

    if not pw:
        return []

    p_mat = normalize_material_name(pw.get("input_material", ""))
    p_title = (pw.get("title") or "").lower()
    p_desc = (pw.get("description") or "").lower()
    p_type = (pw.get("pathway_type") or "").lower()

    all_tutorials = get_tutorials(
        verified_only=verified_only,
        video_csv_path=video_csv_path,
        projects_csv_path=projects_csv_path,
    )

    scored_tutorials = []
    # Stopwords to avoid irrelevant keyword matches
    stopwords = {"with", "from", "that", "this", "your", "into", "clean", "used", "household", "small", "sturdy", "unsoiled", "item", "items"}

    pw_keywords = [
        w for w in (p_title + " " + p_desc).replace(",", " ").replace(".", " ").replace("-", " ").split()
        if len(w) > 3 and w.lower() not in stopwords
    ]

    for tut in all_tutorials:
        t_mat = tut.get("material", "").lower()

        # Material must match or be closely related
        if p_mat != "unknown" and t_mat != p_mat and t_mat != "unknown":
            continue

        score = 1.0  # Base material match
        t_prod = (tut.get("product_name") or "").lower()
        t_title = (tut.get("youtube_title") or "").lower()
        t_cat = (tut.get("category") or "").lower()
        t_item = (tut.get("waste_item") or "").lower()

        # Safety filter: do not recommend metal tutorials involving hole creation.
        if p_mat == "metal":
            raw_steps = tut.get("steps", "")
            if isinstance(raw_steps, (list, tuple)):
                steps_text = " ".join(str(step) for step in raw_steps)
            else:
                steps_text = str(raw_steps or "")

            tutorial_text = " ".join([
                t_prod,
                t_title,
                t_cat,
                t_item,
                str(tut.get("tools") or ""),
                str(tut.get("notes") or ""),
                steps_text,
            ]).lower()

            uses_hole_creation = (
                any(term in tutorial_text for term in ("punch", "drill", "pierce"))
                and any(term in tutorial_text for term in ("hole", "holes", "perforat"))
            )

            if uses_hole_creation:
                continue

        for kw in pw_keywords:
            if kw in t_prod:
                score += 3.0
            if kw in t_title:
                score += 2.0
            if kw in t_cat:
                score += 1.5
            if kw in t_item:
                score += 1.5

        scored_tutorials.append((score, tut))

    # Sort descending by relevance score
    scored_tutorials.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored_tutorials]
