"""
AI Guidance Engine -- Rule-based tips + 4-Week Glowup Strategies.
Feature keys match scorer.py and faceScorer.js:
Symmetry, Eyes, Eyebrows, Nose, Lips, Cheeks, Jawline, Ears, Forehead, Chin
"""
import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "Cosmetic guidance only - not medical advice. "
    "Consult a qualified dermatologist, plastic surgeon, or healthcare "
    "professional before making any medical decisions."
)

# --- 4-Week Glowup Strategies per feature ------------------------------------
# Each entry: { week1, week2, week3, week4, highlight_technique }

FOUR_WEEK_PLANS: Dict[str, Dict] = {
    "Symmetry": {
        "highlight": "Mewing posture + sleep position correction",
        "week1": "Day 1-7: Sleep on your back (no pillow tilt), practice mewing (tongue on palate), take daily front-facing photos for baseline.",
        "week2": "Day 8-14: Add facial massage (5 min gua sha morning + evening). Chew food equally on both sides. Fix posture with chin-tuck exercises.",
        "week3": "Day 15-21: Add jaw-stretch asymmetry drills -- hold the weaker side 2x longer. Start scalp massage to reduce tension headaches that pull face.",
        "week4": "Day 22-28: Full routine locked in. Compare to Week 1 baseline photos. Symmetry improvements of 5-12% are typical from posture alone.",
    },
    "Eyes": {
        "highlight": "Under-eye depuffing + lash serum protocol",
        "week1": "Day 1-7: Add caffeine eye cream (morning). Sleep 8h flat. Cut sodium to reduce puffiness. Cold spoon rolling under eyes each morning.",
        "week2": "Day 8-14: Add Vitamin C serum under eyes (PM). Start eyelid exercises (look up-down without head movement, 3 sets x 20). Hydrate 2.5L/day.",
        "week3": "Day 15-21: Apply retinol eye cream every 3rd night. Consider lash serum (castor oil is free -- apply with clean spoon weekly). Reduce screen time 1h before bed.",
        "week4": "Day 22-28: Full eye care stack in place. Evaluate dark circles vs puffiness separately -- photograph in same lighting as Week 1.",
    },
    "Eyebrows": {
        "highlight": "Brow mapping + microblading-free shaping",
        "week1": "Day 1-7: Map your ideal brow with the 3-point rule (nose-to-eye-corner-to-brow tail). Use a brow pencil to test the shape without committing.",
        "week2": "Day 8-14: Trim brows with scissors before tweezing. Apply castor oil to sparse areas nightly. Only tweeze hairs OUTSIDE your mapped shape.",
        "week3": "Day 15-21: Add brow serum (peptides or minoxidil -- consult dermatologist first). Practice filling with feathery strokes vs block fill.",
        "week4": "Day 22-28: Evaluate symmetry improvement. If gaps remain, consult a certified brow artist for lamination or tinting (non-permanent).",
    },
    "Nose": {
        "highlight": "Contouring + posture alignment for profile",
        "week1": "Day 1-7: Photograph your nose from 3 angles (front, 45 deg, profile). Practice chin-forward posture which elongates nose appearance.",
        "week2": "Day 8-14: Learn nose contour technique for your shape (highlighter on bridge + shadow on sides). Reduces width perception 10-15% optically.",
        "week3": "Day 15-21: Practice nasal breathing and breathing exercises to reduce nostril flare. Rhinoplasty consultations are worth 1 free consult to understand options.",
        "week4": "Day 22-28: Consolidate grooming and contour skills. If structural concerns remain, book a consult with a board-certified rhinoplasty surgeon.",
    },
    "Lips": {
        "highlight": "Lip plumping hydration stack + cupid's bow definition",
        "week1": "Day 1-7: Exfoliate lips with sugar scrub (2x/week). Apply hyaluronic acid lip mask nightly. Drink 3L water daily. Stop licking lips (dries them).",
        "week2": "Day 8-14: Add a peptide lip serum (daytime). Practice over-lining cupid's bow 0.5mm with matching liner. Peppermint oil in lip balm gives temporary plump.",
        "week3": "Day 15-21: Cold-roller on lips each morning (5 min). SPF lip balm during day. If interested in fillers, book a consultation (results are reversible).",
        "week4": "Day 22-28: Lips should be visibly healthier and fuller from hydration alone. Reassess with a professional if enhancement is desired.",
    },
    "Cheeks": {
        "highlight": "Face yoga + cheeked bone definition",
        "week1": "Day 1-7: Reduce sodium + alcohol (main causes of facial bloat). Add 2L water daily. Learn 'cheekbone lift' facial yoga (hold the lift 30 sec x 10).",
        "week2": "Day 8-14: Gua sha upward strokes on cheeks (2 min each side, daily). Apply retinol to mid-face at night for collagen stimulation.",
        "week3": "Day 15-21: Reduce body fat % through cardio -- cheeks are one of the first places fat loss shows. Add collagen powder to morning coffee.",
        "week4": "Day 22-28: Cheek definition improvements from this protocol alone are typically 8-15%. Blush placement high on cheekbones optically lifts.",
    },
    "Jawline": {
        "highlight": "Mastic gum chewing + neck/chin posture protocol",
        "week1": "Day 1-7: Start mewing (tongue on palate 24/7). Cut sodium and processed foods. Begin chin-tuck exercises (10 reps x 3 sets daily).",
        "week2": "Day 8-14: Add mastic gum (20-30 min daily -- genuine jaw workout). Add neck exercises (side tilts, chin presses). Apply caffeine cream to jawline.",
        "week3": "Day 15-21: Lose 0.5-1kg body fat if applicable (jaw is highly fat-responsive). Add neck-to-jaw massage with ice roller each morning.",
        "week4": "Day 22-28: Jawline is typically the fastest-responding feature to lifestyle changes. Results of 1-2 months compound. Consider kybella or filler consult if desired.",
    },
    "Ears": {
        "highlight": "Positioning check + hair framing techniques",
        "week1": "Day 1-7: Ear position is largely structural. Focus on hairstyle choices that frame or draw attention away from ears if needed.",
        "week2": "Day 8-14: If ears protrude, consult an otoplasty specialist (simple day-procedure). Hairstyle volume at temples reduces ear prominence.",
        "week3": "Day 15-21: Ear care: clean, moisturize lobes. If you have stretched piercings you want closed, consult a dermatologist.",
        "week4": "Day 22-28: Evaluate symmetry from front-on photos. Hair styling and positioning are the primary levers here.",
    },
    "Forehead": {
        "highlight": "Hairline framing + brow positioning optimization",
        "week1": "Day 1-7: Measure your facial thirds. Determine if forehead is long, short, or balanced. Style hair to optically balance (fringe for long, volume for short).",
        "week2": "Day 8-14: Apply retinol to forehead (anti-wrinkle). SPF 50 to prevent sun damage. If hairline receding, consult a trichologist for options.",
        "week3": "Day 15-21: Brow position heavily affects forehead perception -- well-shaped, slightly arched brows shorten apparent forehead length.",
        "week4": "Day 22-28: Hair transplant FUE/FUT consults are worth exploring if hairline is the concern -- modern results are undetectable.",
    },
    "Chin": {
        "highlight": "Chin projection + neck posture alignment",
        "week1": "Day 1-7: Practice chin-forward posture (not chin-up). This projects the chin and elongates the neck simultaneously. Photograph profile daily.",
        "week2": "Day 8-14: Mewing and tongue posture strengthen the mentalis muscle which defines chin over time. Add chin-tap exercises (tap chin upward 20x).",
        "week3": "Day 15-21: Reduce submental fat (double chin) with cardio + intermittent fasting if applicable. Kybella injections are FDA-approved for this.",
        "week4": "Day 22-28: Chin filler is a highly effective non-surgical option for projection -- reversible, quick, and natural-looking. Book a consult to explore.",
    },
}

# --- Tip Database (keys match scorer.py / faceScorer.js) ---------------------
TIPS: Dict[str, Dict[str, List]] = {
    "Symmetry": {
        "any": [
            (75, "low",    "Excellent facial symmetry. Maintain consistent sleep posture (back sleeping) to preserve it. Regular mewing helps long-term."),
            (50, "medium", "Mild asymmetry detected. Targeted facial exercises (cheek lifts, jaw stretches) can improve muscle balance. Sleeping on your back and correcting jaw posture are free and effective."),
            (0,  "high",   "Noticeable asymmetry observed. This can result from habitual sleep positions, dental misalignment, or muscle imbalance. Consult a maxillofacial surgeon or orthodontist for structural options."),
        ],
    },
    "Eyes": {
        "male": [
            (75, "low",    "Well-proportioned eyes. Caffeine eye cream in the morning reduces puffiness. Keep under-eye area hydrated."),
            (50, "medium", "Consider an under-eye cream with retinol or vitamin C to address puffiness or dark circles. Cold compress in the morning helps significantly."),
            (0,  "high",   "Eye area may benefit from professional treatment. Consult a dermatologist about options for under-eye filler, laser resurfacing, or blepharoplasty assessment."),
        ],
        "female": [
            (75, "low",    "Beautiful eye shape with great aspect ratio. Lash serum and brow lifting enhance it further."),
            (50, "medium", "Lash growth serums (castor oil free at home, or Latisse via prescription) can enhance eye openness. Under-eye hydration patches help with puffiness."),
            (0,  "high",   "An oculoplastic surgeon consultation may be worthwhile to discuss options for upper lid ptosis correction or brow lifting."),
        ],
        "prefer_not_to_say": [
            (75, "low",    "Good eye aesthetics. Keep hydrated and use SPF eye cream daily."),
            (50, "medium", "Eye care products with peptides and caffeine can reduce puffiness. Consult a dermatologist for personalized options."),
            (0,  "high",   "Consider consulting an oculoplastic surgeon for a professional assessment."),
        ],
    },
    "Eyebrows": {
        "male": [
            (75, "low",    "Well-shaped brows. Keep them clean and defined -- a light trim and brush-up is all you need."),
            (50, "medium", "Brow grooming makes a huge difference for males. Castor oil stimulates growth in sparse areas. Consider a professional brow shaping session."),
            (0,  "high",   "Consider a consultation with a certified brow artist. Microblading is an option for very sparse brows. A dermatologist can evaluate minoxidil for growth."),
        ],
        "female": [
            (75, "low",    "Great brow shape. Brow lamination or tinting can enhance definition without permanent commitment."),
            (50, "medium", "Apply castor oil nightly to sparse areas. Map your ideal shape using the 3-point nose-eye-tail technique before tweezing."),
            (0,  "high",   "Consult a certified brow artist for microblading or lamination. A dermatologist can prescribe bimatoprost for brow growth if needed."),
        ],
        "prefer_not_to_say": [
            (75, "low",    "Good brow aesthetics. Maintain with regular grooming."),
            (50, "medium", "Castor oil and professional shaping can significantly improve brow symmetry and density."),
            (0,  "high",   "Consult a brow artist or dermatologist for growth-stimulating treatments."),
        ],
    },
    "Nose": {
        "any": [
            (75, "low",    "Well-proportioned nose relative to your facial features. Nose contouring can optically enhance further if desired."),
            (50, "medium", "Contouring techniques (highlight on bridge, shadow on sides) can visually adjust the nose. Rhinoplasty consultation is worth considering if structural changes interest you."),
            (0,  "high",   "A consultation with a board-certified rhinoplasty specialist can assess structural and aesthetic options. Non-surgical nose fillers exist as a temporary alternative."),
        ],
    },
    "Lips": {
        "male": [
            (75, "low",    "Balanced lip shape. Staying hydrated and using SPF lip balm maintains volume naturally."),
            (50, "medium", "Hyaluronic acid lip balm helps with volume and texture. A dermatologist can discuss minimally invasive filler options."),
            (0,  "high",   "Consult a board-certified dermatologist about lip augmentation options. Results from HA fillers are temporary and fully reversible."),
        ],
        "female": [
            (75, "low",    "Great lip proportions. Lip liner to define the cupid's bow can further enhance your natural shape."),
            (50, "medium", "A dermatologist can discuss hyaluronic acid fillers for volume balance. Topical lip plumpers (peptides, peppermint) give instant non-invasive results."),
            (0,  "high",   "Consult a licensed aesthetic practitioner about lip augmentation. Ensure they are board-certified and use only FDA-approved HA products."),
        ],
        "prefer_not_to_say": [
            (75, "low",    "Good lip proportions. Hydration and SPF lip balm are your best tools."),
            (50, "medium", "Hyaluronic acid lip treatments (topical or professional) can help. Consult a dermatologist."),
            (0,  "high",   "Consider a consultation with a board-certified aesthetic practitioner for filler options."),
        ],
    },
    "Cheeks": {
        "any": [
            (75, "low",    "Good cheek volume and symmetry. Gua sha upward strokes maintain definition and lymphatic drainage."),
            (50, "medium", "Reduce sodium intake and increase water to eliminate facial bloating. Gua sha and face yoga (cheekbone lifts) improve definition over 4 weeks."),
            (0,  "high",   "Cheek definition can be significantly improved through body fat reduction and facial exercises. Cheek filler or fat transfer are surgical options -- consult a specialist."),
        ],
    },
    "Jawline": {
        "male": [
            (75, "low",    "Strong, defined jaw -- a key masculine trait. Maintain low body fat and continue mewing posture."),
            (50, "medium", "Mastic gum chewing (30 min daily), sodium reduction, and chin-tuck posture exercises can significantly define the jaw within 4 weeks."),
            (0,  "high",   "Jaw definition needs improvement. Mewing, mastic gum, and reducing submental fat are first steps. Consider a maxillofacial specialist consult for structural assessment. Chin/jaw filler is a minimally invasive option."),
        ],
        "female": [
            (75, "low",    "Soft, balanced jawline -- aesthetically ideal for feminine features. Gua sha maintains definition."),
            (50, "medium", "Gua sha massage along the jaw reduces puffiness. Facial contouring with blush and highlight can sculpt the jaw visually."),
            (0,  "high",   "Consult a certified aesthetician about facial sculpting techniques. Non-invasive options like Kybella or jawline slimming injections may be worth exploring."),
        ],
        "prefer_not_to_say": [
            (75, "low",    "Good jaw definition. Continue mewing and low-sodium diet to maintain."),
            (50, "medium", "Jawline exercises and low-sodium diet are effective. Consult a professional for personalized advice."),
            (0,  "high",   "Consult a maxillofacial specialist for a structural assessment. Lifestyle changes (diet, mewing) are effective first steps."),
        ],
    },
    "Ears": {
        "any": [
            (75, "low",    "Ear position looks symmetrical. Hairstyle choices can frame or complement your ear position."),
            (50, "medium", "If ear prominence is a concern, hairstyle volume at the temples reduces perceived projection. Otoplasty is a simple day-procedure if needed."),
            (0,  "high",   "Consult an otoplasty specialist if ear position or shape is a concern. It is one of the simplest and most effective cosmetic procedures available."),
        ],
    },
    "Forehead": {
        "any": [
            (75, "low",    "Good forehead proportions. SPF 50 daily prevents sun damage and maintains skin quality."),
            (50, "medium", "Hairstyle choices can optically balance forehead height (fringe for long, volume at crown for short). Brow position is key -- well-arched brows reduce apparent forehead size."),
            (0,  "high",   "Hairline lowering surgery or FUE hair transplant are options for receding or high hairlines. Consult a trichologist or hair transplant specialist."),
        ],
    },
    "Chin": {
        "male": [
            (75, "low",    "Good chin projection. Chin-forward posture (not chin-up) maintains natural projection and defines the neck-jaw angle."),
            (50, "medium", "Mewing and chin-tuck exercises project the chin over time. Reducing submental fat (body fat loss + Kybella) can significantly improve chin definition."),
            (0,  "high",   "Chin filler is a highly effective non-surgical option for projection enhancement. Chin implants are a permanent alternative -- both require a board-certified surgeon."),
        ],
        "female": [
            (75, "low",    "Balanced chin shape. Ensure posture is upright to maintain the chin-neck definition naturally."),
            (50, "medium", "Chin projection can be improved with posture and targeted exercises. A non-surgical chin filler consultation is worth considering for quick enhancement."),
            (0,  "high",   "Chin augmentation (filler or implant) can significantly improve facial balance. Consult a board-certified cosmetic surgeon for options."),
        ],
        "prefer_not_to_say": [
            (75, "low",    "Good chin aesthetics. Posture maintenance is key."),
            (50, "medium", "Chin exercises and posture improvements can help. Consult a professional for structural options."),
            (0,  "high",   "Consider a consultation with a board-certified cosmetic surgeon for chin augmentation options."),
        ],
    },
}


def _get_tip_for_feature(feature: str, score: float, gender: str) -> Dict[str, Any] | None:
    """Fetch the most appropriate tip for a feature score and gender."""
    gender_tips = TIPS.get(feature, {})
    candidates  = gender_tips.get(gender, gender_tips.get("any", []))
    if not candidates:
        return None
    for threshold, severity, tip_text in candidates:
        if score >= threshold:
            plan = FOUR_WEEK_PLANS.get(feature, {})
            return {
                "feature":           feature,
                "score":             score,
                "severity":          severity,
                "tip":               tip_text,
                "disclaimer":        DISCLAIMER,
                "highlight":         plan.get("highlight", ""),
                "week1":             plan.get("week1",     ""),
                "week2":             plan.get("week2",     ""),
                "week3":             plan.get("week3",     ""),
                "week4":             plan.get("week4",     ""),
            }
    return None


def generate_tips(feature_scores: Dict[str, float], gender: str) -> List[Dict[str, Any]]:
    """
    Generate guidance tips for all features that score below 85.
    Tips are sorted by severity (high - medium - low), then by score ascending.
    """
    tips = []
    for feature, score in feature_scores.items():
        if score < 85:
            tip = _get_tip_for_feature(feature, score, gender)
            if tip:
                tips.append(tip)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    tips.sort(key=lambda t: (severity_order.get(t["severity"], 3), t["score"]))
    return tips


async def generate_tips_ollama(
    feature_scores: Dict[str, float],
    gender: str,
    ollama_url: str = "http://localhost:11434",
) -> List[Dict[str, Any]]:
    """
    Phase 2: Generate tips using Ollama llama3:8b.
    Falls back to rule-based tips if Ollama is unavailable.
    """
    try:
        low_features = {k: v for k, v in feature_scores.items() if v < 70}
        if not low_features:
            return generate_tips(feature_scores, gender)

        prompt = (
            f"You are a professional facial aesthetics advisor. Gender context: {gender}.\n"
            f"Facial features scored below 70/100:\n"
            + "\n".join(f"- {k}: {v}/100" for k, v in low_features.items())
            + "\n\nFor each feature provide ONE concise practical improvement tip. "
            "Always end each tip with: Consult a qualified professional before any medical action.\n"
            "Format: Feature: tip text"
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{ollama_url}/api/generate",
                json={"model": "llama3:8b", "prompt": prompt, "stream": False},
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "")
                ollama_tips = []
                for line in text.strip().split("\n"):
                    if ":" in line:
                        parts = line.split(":", 1)
                        feature = parts[0].strip()
                        plan    = FOUR_WEEK_PLANS.get(feature, {})
                        ollama_tips.append({
                            "feature":    feature,
                            "tip":        parts[1].strip(),
                            "severity":   "medium",
                            "disclaimer": DISCLAIMER,
                            "highlight":  plan.get("highlight", ""),
                            "week1":      plan.get("week1",     ""),
                            "week2":      plan.get("week2",     ""),
                            "week3":      plan.get("week3",     ""),
                            "week4":      plan.get("week4",     ""),
                        })
                return ollama_tips if ollama_tips else generate_tips(feature_scores, gender)
    except Exception as e:
        logger.info(f"Ollama unavailable ({e}), falling back to rule-based tips")

    return generate_tips(feature_scores, gender)
