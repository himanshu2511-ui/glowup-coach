"""
Facial Analysis Engine — MediaPipe FaceMesh (468 + refined landmarks)
Extracts geometric metrics for aesthetic scoring.
"""
import math
import numpy as np
import mediapipe as mp
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

mp_face_mesh = mp.solutions.face_mesh

# ─── Landmark Index Constants ─────────────────────────────────────────────────

# Symmetry pairs: (left_index, right_index)
SYMMETRY_PAIRS = [
    (33, 263),   # eye corners
    (133, 362),  # inner eye corners
    (234, 454),  # cheekbones
    (172, 397),  # jaw corners
    (50, 280),   # cheek mid
    (70, 300),   # brow outer
    (105, 334),  # brow inner
    (61, 291),   # lip corners
]

# Jawline points for smoothness
JAWLINE_INDICES = [172, 136, 150, 149, 148, 152, 377, 400, 378, 379, 397]

# Key landmark indices
FACE_LEFT    = 234
FACE_RIGHT   = 454
FACE_TOP     = 10
FACE_BOTTOM  = 152
EYE_L_INNER  = 133
EYE_R_INNER  = 362
EYE_L_OUTER  = 33
EYE_R_OUTER  = 263
EYE_L_TOP    = 159
EYE_L_BOT    = 145
EYE_R_TOP    = 386
EYE_R_BOT    = 374
NOSE_TIP     = 1
NOSE_BASE    = 2
FOREHEAD     = 10
MID_NOSE     = 168
CHIN         = 152
UPPER_LIP    = 0
LOWER_LIP_T  = 13
LOWER_LIP_B  = 14
CHIN_LOW     = 17
JAW_L        = 172
JAW_R        = 397
JAW_C        = 152
CUPID_L1     = 61
CUPID_L2     = 62
CUPID_R1     = 291
CUPID_R2     = 292


# ─── Utilities ────────────────────────────────────────────────────────────────

def _dist(p1, p2) -> float:
    return math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2 + (p2.z - p1.z)**2)


def _angle(a, b, c) -> float:
    """Angle at vertex b formed by points a-b-c (degrees)."""
    ba = np.array([a.x - b.x, a.y - b.y])
    bc = np.array([c.x - b.x, c.y - b.y])
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    return math.degrees(math.acos(np.clip(cos_angle, -1.0, 1.0)))


def _normalize_score(value: float, ideal: float, tolerance: float = 0.15) -> float:
    """Map a ratio to 0–100 based on closeness to ideal."""
    deviation = abs(value - ideal) / ideal
    score = max(0.0, 1.0 - (deviation / tolerance))
    return round(min(score, 1.0) * 100, 2)


def _clamp_score(s: float) -> float:
    return round(max(0.0, min(100.0, s)), 2)


# ─── Metric Calculators ───────────────────────────────────────────────────────

def _bilateral_symmetry(lm) -> float:
    """Compare distances of left-right symmetric landmark pairs."""
    ratios = []
    face_w = _dist(lm[FACE_LEFT], lm[FACE_RIGHT]) + 1e-9
    for l_idx, r_idx in SYMMETRY_PAIRS:
        l_dist = abs(lm[l_idx].x - lm[FACE_LEFT].x) / face_w
        r_dist = abs(lm[FACE_RIGHT].x - lm[r_idx].x) / face_w
        diff = abs(l_dist - r_dist)
        ratios.append(max(0.0, 1.0 - diff * 10))
    score = np.mean(ratios) * 100
    return _clamp_score(score)


def _horizontal_symmetry(lm) -> float:
    """Top-bottom balance."""
    face_h = _dist(lm[FACE_TOP], lm[FACE_BOTTOM]) + 1e-9
    top_h = _dist(lm[FACE_TOP], lm[MID_NOSE]) / face_h
    bot_h = _dist(lm[MID_NOSE], lm[FACE_BOTTOM]) / face_h
    score = max(0.0, 1.0 - abs(top_h - bot_h) * 5) * 100
    return _clamp_score(score)


def _golden_ratio_face(lm) -> float:
    face_w = _dist(lm[FACE_LEFT], lm[FACE_RIGHT])
    face_h = _dist(lm[FACE_TOP], lm[FACE_BOTTOM]) + 1e-9
    ratio = face_w / face_h
    return _normalize_score(ratio, ideal=0.618, tolerance=0.20)


def _eye_spacing(lm) -> float:
    face_w = _dist(lm[FACE_LEFT], lm[FACE_RIGHT]) + 1e-9
    eye_gap = _dist(lm[EYE_L_INNER], lm[EYE_R_INNER])
    ratio = eye_gap / face_w
    return _normalize_score(ratio, ideal=0.46, tolerance=0.15)


def _facial_thirds(lm) -> float:
    """Forehead : nose : chin ideally 1:1:1."""
    forehead = _dist(lm[FACE_TOP], lm[MID_NOSE])
    mid_face = _dist(lm[MID_NOSE], lm[NOSE_BASE])
    lower    = _dist(lm[NOSE_BASE], lm[FACE_BOTTOM])
    total = forehead + mid_face + lower + 1e-9
    thirds = [forehead / total, mid_face / total, lower / total]
    variance = np.var(thirds)
    score = max(0.0, 1.0 - variance * 100) * 100
    return _clamp_score(score)


def _eye_aesthetics(lm) -> float:
    l_w = _dist(lm[EYE_L_OUTER], lm[EYE_L_INNER])
    l_h = _dist(lm[EYE_L_TOP], lm[EYE_L_BOT]) + 1e-9
    r_w = _dist(lm[EYE_R_INNER], lm[EYE_R_OUTER])
    r_h = _dist(lm[EYE_R_TOP], lm[EYE_R_BOT]) + 1e-9
    l_ratio = l_h / l_w
    r_ratio = r_h / r_w
    avg_ratio = (l_ratio + r_ratio) / 2
    return _normalize_score(avg_ratio, ideal=0.35, tolerance=0.20)


def _nose_aesthetics(lm) -> float:
    """Nasolabial angle: nose tip (1) → nose base (2) → upper lip (0). Ideal: 90-110°."""
    angle = _angle(lm[NOSE_TIP], lm[NOSE_BASE], lm[UPPER_LIP])
    ideal_mid = 100.0
    deviation = abs(angle - ideal_mid)
    score = max(0.0, 1.0 - deviation / 25.0) * 100
    return _clamp_score(score)


def _lip_aesthetics(lm) -> float:
    upper_h = _dist(lm[UPPER_LIP], lm[LOWER_LIP_T]) + 1e-9
    lower_h = _dist(lm[LOWER_LIP_T], lm[CHIN_LOW])
    ratio = lower_h / upper_h
    ratio_score = _normalize_score(ratio, ideal=2.0, tolerance=0.40)
    cupid_l = _dist(lm[CUPID_L1], lm[CUPID_L2])
    cupid_r = _dist(lm[CUPID_R1], lm[CUPID_R2])
    sym = max(0.0, 1.0 - abs(cupid_l - cupid_r) / (max(cupid_l, cupid_r) + 1e-9)) * 100
    return _clamp_score((ratio_score + sym) / 2)


def _jawline_aesthetics(lm) -> float:
    """Jaw angle + smoothness of jawline curve."""
    jaw_angle = _angle(lm[JAW_L], lm[JAW_C], lm[JAW_R])
    angle_score = max(0.0, 1.0 - abs(jaw_angle - 120.0) / 30.0) * 100

    # Smoothness: variance in segment lengths along jawline
    pts = [lm[i] for i in JAWLINE_INDICES]
    segments = [_dist(pts[i], pts[i+1]) for i in range(len(pts)-1)]
    norm_segs = np.array(segments) / (max(segments) + 1e-9)
    variance = float(np.var(norm_segs))
    smooth_score = max(0.0, 1.0 - variance * 20) * 100

    return _clamp_score((angle_score + smooth_score) / 2)


def _facial_harmony(lm) -> float:
    """Composite of multiple soft proportions."""
    face_w = _dist(lm[FACE_LEFT], lm[FACE_RIGHT]) + 1e-9
    # Nose width relative to face
    nose_w = _dist(lm[49], lm[279]) / face_w
    nose_score = _normalize_score(nose_w, ideal=0.25, tolerance=0.15)
    # Mouth width relative to face
    mouth_w = _dist(lm[CUPID_L1], lm[CUPID_R1]) / face_w
    mouth_score = _normalize_score(mouth_w, ideal=0.45, tolerance=0.15)
    return _clamp_score((nose_score + mouth_score) / 2)


# ─── Main Analysis Function ───────────────────────────────────────────────────

def analyze_frame(image_bytes: bytes) -> dict | None:
    """
    Analyze a single frame image.
    Returns dict of metric scores or None if no face detected.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(img)

        with mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        ) as face_mesh:
            results = face_mesh.process(img_np)

        if not results.multi_face_landmarks:
            return None

        lm = results.multi_face_landmarks[0].landmark

        return {
            "bilateral_symmetry": _bilateral_symmetry(lm),
            "horizontal_symmetry": _horizontal_symmetry(lm),
            "golden_ratio_face": _golden_ratio_face(lm),
            "eye_spacing": _eye_spacing(lm),
            "facial_thirds": _facial_thirds(lm),
            "eye_aesthetics": _eye_aesthetics(lm),
            "nose_aesthetics": _nose_aesthetics(lm),
            "lip_aesthetics": _lip_aesthetics(lm),
            "jawline_aesthetics": _jawline_aesthetics(lm),
            "facial_harmony": _facial_harmony(lm),
        }

    except Exception as e:
        logger.error(f"Frame analysis error: {e}")
        return None


def aggregate_frames(frame_results: list[dict]) -> dict:
    """Average metrics across multiple frames for a stable final score."""
    if not frame_results:
        return {}
    keys = frame_results[0].keys()
    return {
        k: round(float(np.mean([f[k] for f in frame_results])), 2)
        for k in keys
    }
