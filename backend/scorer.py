"""
Gender-specific weighted scoring engine.
Keys match exactly what the JS faceScorer.js sends:
Symmetry, Eyes, Eyebrows, Nose, Lips, Cheeks, Jawline, Ears, Forehead, Chin
"""

# ─── Weight Tables ────────────────────────────────────────────────────────────
# Weights MUST match WEIGHTS in frontend/src/utils/faceScorer.js

MALE_WEIGHTS = {
    "Symmetry": 22,
    "Eyes":     9,
    "Eyebrows": 7,
    "Nose":     12,
    "Lips":     8,
    "Cheeks":   6,
    "Jawline":  18,   # Higher for males — strong jaw is key
    "Ears":     5,
    "Forehead": 8,
    "Chin":     5,
}

FEMALE_WEIGHTS = {
    "Symmetry": 25,
    "Eyes":     13,   # Eyes weighted higher for females
    "Eyebrows": 9,
    "Nose":     8,
    "Lips":     12,   # Lips weighted higher for females
    "Cheeks":   8,
    "Jawline":  5,    # Softer jawline preferred
    "Ears":     4,
    "Forehead": 7,
    "Chin":     9,
}

NEUTRAL_WEIGHTS = {
    "Symmetry": 23,
    "Eyes":     11,
    "Eyebrows": 8,
    "Nose":     10,
    "Lips":     10,
    "Cheeks":   7,
    "Jawline":  11,
    "Ears":     4,
    "Forehead": 7,
    "Chin":     7,
}


def compute_score(metrics: dict, gender: str) -> dict:
    """
    Compute the weighted total score and per-feature scores.

    Args:
        metrics: dict of {feature: raw_score_0_to_100}
                 Keys must be: Symmetry, Eyes, Eyebrows, Nose, Lips,
                               Cheeks, Jawline, Ears, Forehead, Chin
        gender: "male" | "female" | "prefer_not_to_say"

    Returns:
        dict with total_score (0-100) and feature_scores (labeled)
    """
    if gender == "male":
        weights = MALE_WEIGHTS
    elif gender == "female":
        weights = FEMALE_WEIGHTS
    else:
        weights = NEUTRAL_WEIGHTS

    total_weight = sum(weights.values())   # should be 100 for all tables
    total        = 0.0
    feature_out  = {}

    for feature, weight in weights.items():
        # scores arrive as 0-100 from frontend
        raw = float(metrics.get(feature, 0.0))
        raw = max(0.0, min(100.0, raw))    # clamp
        contribution = raw * (weight / total_weight)
        total += contribution
        feature_out[feature] = round(raw, 1)

    return {
        "total_score":   round(min(total, 100.0), 1),
        "feature_scores": feature_out,
        "weights_used":  gender,
    }
