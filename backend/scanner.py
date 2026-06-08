"""
Glowup Coach — Real-Time Face Scanner
Based on OpenCV + MediaPipe (cv2 direct — no browser needed)
Run: python scanner.py

Controls:
  SPACE  — Start/restart 30-second scan
  Q      — Quit
"""

import cv2
import mediapipe as mp
import numpy as np
import math
import time
import os
import sys
import json
import getpass
import requests
from datetime import datetime
from pdf_report import generate_pdf

# ─── Config ───────────────────────────────────────────────────────────────────
API_BASE     = "http://localhost:8000"
SCAN_SECONDS = 30
FRAME_RATE   = 10  # analyze every N frames
REPORTS_DIR  = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# ─── Gender-specific weights ───────────────────────────────────────────────────
WEIGHTS_MALE = {
    "Symmetry":   22,
    "Eyes":        9,
    "Eyebrows":    7,
    "Nose":       12,
    "Lips":        8,
    "Cheeks":      6,
    "Jawline":    18,   # strong jaw key for males
    "Ears":        5,
    "Forehead":    8,
    "Chin":        5,
}
WEIGHTS_FEMALE = {
    "Symmetry":   25,
    "Eyes":       13,   # eyes more important for females
    "Eyebrows":    9,
    "Nose":        8,
    "Lips":       12,   # lips more important for females
    "Cheeks":      8,
    "Jawline":     5,   # softer jaw preferred
    "Ears":        4,
    "Forehead":    7,
    "Chin":        9,
}
WEIGHTS_NEUTRAL = {k: (WEIGHTS_MALE[k] + WEIGHTS_FEMALE[k]) // 2 for k in WEIGHTS_MALE}

# ─── Colors (BGR for cv2) ─────────────────────────────────────────────────────
C_GREEN  = (80,  200, 100)
C_CYAN   = (220, 210,  80)
C_ORANGE = (60,  150, 240)
C_RED    = (60,   60, 220)
C_WHITE  = (240, 240, 240)
C_DARK   = (18,  18,  30)
C_MALE   = (210, 150,  50)   # blue-ish
C_FEMALE = (150,  90, 220)   # pink-ish
C_GOLD   = (30,  210, 215)
C_BG     = (15,  15,  25)

# ─── MediaPipe setup ──────────────────────────────────────────────────────────
mp_face_mesh = mp.solutions.face_mesh
mp_draw      = mp.solutions.drawing_utils
mp_styles    = mp.solutions.drawing_styles

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
)


# ─── Utility ──────────────────────────────────────────────────────────────────
def dist(p1, p2):
    return math.dist([p1.x, p1.y], [p2.x, p2.y])

def symmetry_score(left, right, center):
    l = abs(left.x - center.x)
    r = abs(right.x - center.x)
    return max(0.0, 1.0 - abs(l - r) / (max(l, r, 1e-6)))

def clamp(val):
    return max(0.0, min(1.0, val))

def score_color_bgr(score_0_to_100):
    if score_0_to_100 >= 80: return C_GREEN
    if score_0_to_100 >= 60: return C_CYAN
    if score_0_to_100 >= 40: return C_ORANGE
    return C_RED

def score_label(score):
    if score >= 92: return "ELITE"
    if score >= 82: return "VERY ATTRACTIVE"
    if score >= 70: return "ATTRACTIVE"
    if score >= 55: return "ABOVE AVERAGE"
    if score >= 40: return "AVERAGE"
    return "NEEDS WORK"


# ─── Analysis ─────────────────────────────────────────────────────────────────
def analyze_face(landmarks):
    lm = landmarks
    center = lm[1]  # nose bridge

    scores = {}

    # 1. Overall symmetry (average of left-right pairs)
    scores["Symmetry"] = clamp(np.mean([
        symmetry_score(lm[33],  lm[263], center),   # eye corners
        symmetry_score(lm[61],  lm[291], center),   # lip corners
        symmetry_score(lm[172], lm[397], center),   # jaw corners
        symmetry_score(lm[234], lm[454], center),   # cheekbones
    ]))

    # 2. Eyes — aspect ratio + symmetry
    l_eye_w = dist(lm[33],  lm[133])
    r_eye_w = dist(lm[362], lm[263])
    l_eye_h = dist(lm[159], lm[145])
    r_eye_h = dist(lm[386], lm[374])
    avg_ratio = ((l_eye_h / (l_eye_w + 1e-6)) + (r_eye_h / (r_eye_w + 1e-6))) / 2
    eye_ratio_score = clamp(1 - abs(avg_ratio - 0.35) / 0.25)
    eye_sym_score   = symmetry_score(lm[33], lm[263], center)
    scores["Eyes"] = clamp((eye_ratio_score + eye_sym_score) / 2)

    # 3. Eyebrows — symmetry + height
    scores["Eyebrows"] = clamp(np.mean([
        symmetry_score(lm[70],  lm[300], center),
        symmetry_score(lm[105], lm[334], center),
    ]))

    # 4. Nose — straightness + width proportion
    nose_straight = clamp(1 - abs(lm[1].x - center.x) * 20)
    face_w = dist(lm[234], lm[454])
    nose_w = dist(lm[49],  lm[279])
    nose_prop = clamp(1 - abs((nose_w / (face_w + 1e-6)) - 0.25) / 0.15)
    scores["Nose"] = clamp((nose_straight + nose_prop) / 2)

    # 5. Lips — width ratio + symmetry + cupid's bow
    mouth_w = dist(lm[61], lm[291])
    mouth_h = dist(lm[13], lm[14])
    lip_ratio = mouth_w / (mouth_h + 1e-6)
    ratio_score  = clamp(1 - abs(lip_ratio - 3.0) / 3.0)
    cupid_sym    = clamp(1 - abs(dist(lm[61], lm[62]) - dist(lm[291], lm[292])) * 10)
    scores["Lips"] = clamp((ratio_score + cupid_sym) / 2)

    # 6. Cheeks — width symmetry
    scores["Cheeks"] = clamp(np.mean([
        symmetry_score(lm[50], lm[280], center),
        symmetry_score(lm[116], lm[345], center),
    ]))

    # 7. Jawline — angle + smoothness
    jaw_pts = [lm[i] for i in [172, 136, 150, 149, 148, 152, 377, 400, 378, 379, 397]]
    segs = [dist(jaw_pts[i], jaw_pts[i+1]) for i in range(len(jaw_pts)-1)]
    smoothness = clamp(1 - np.std(segs) / (np.mean(segs) + 1e-6))
    jaw_sym = symmetry_score(lm[172], lm[397], center)
    scores["Jawline"] = clamp((smoothness * 0.4 + jaw_sym * 0.6))

    # 8. Ears — position symmetry (approximate)
    scores["Ears"] = clamp(symmetry_score(lm[234], lm[454], center))

    # 9. Forehead — width + balance
    face_h = dist(lm[10], lm[152])
    forehead_h = dist(lm[10], lm[168])
    forehead_ratio = forehead_h / (face_h + 1e-6)
    forehead_score = clamp(1 - abs(forehead_ratio - 0.33) / 0.15)
    scores["Forehead"] = clamp((forehead_score + symmetry_score(lm[109], lm[338], center)) / 2)

    # 10. Chin — definition + projection
    chin_h = dist(lm[152], lm[199])
    lower_h = dist(lm[2], lm[152])
    chin_ratio = chin_h / (lower_h + 1e-6)
    scores["Chin"] = clamp(1 - abs(chin_ratio - 0.35) / 0.2)

    return scores


# ─── Draw overlay ─────────────────────────────────────────────────────────────
def draw_ui(frame, scores, total_score, time_left, scanning, gender, frame_count, face_detected):
    h, w = frame.shape[:2]

    # Semi-transparent left panel
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (230, h), C_BG, -1)
    cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

    # ── Header ──
    cv2.rectangle(frame, (0, 0), (230, 36), (25, 20, 50), -1)
    cv2.putText(frame, "GLOWUP COACH", (10, 23),
                cv2.FONT_HERSHEY_DUPLEX, 0.55, C_GOLD, 1, cv2.LINE_AA)

    gender_color = C_MALE if gender == "male" else C_FEMALE if gender == "female" else C_CYAN
    gender_label = f"[ {gender.replace('_',' ').upper()} ]"
    cv2.putText(frame, gender_label, (10, 35),
                cv2.FONT_HERSHEY_PLAIN, 0.85, gender_color, 1, cv2.LINE_AA)

    # ── Feature scores ──
    y = 58
    if scores:
        for feature, val in scores.items():
            score_int = int(val * 100)
            color = score_color_bgr(score_int)

            # Label
            cv2.putText(frame, feature, (10, y),
                        cv2.FONT_HERSHEY_PLAIN, 1.0, C_WHITE, 1, cv2.LINE_AA)

            # Bar track
            bar_x, bar_y = 10, y + 3
            bar_w_max = 160
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w_max, bar_y + 5),
                          (40, 40, 60), -1)
            # Bar fill
            fill_w = int(bar_w_max * val)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + 5),
                          color, -1)

            # Score text
            cv2.putText(frame, str(score_int), (175, y),
                        cv2.FONT_HERSHEY_PLAIN, 0.95, color, 1, cv2.LINE_AA)
            y += 22
    else:
        cv2.putText(frame, "Waiting for face...", (10, 100),
                    cv2.FONT_HERSHEY_PLAIN, 1.0, (120, 120, 140), 1, cv2.LINE_AA)

    # ── Total score box ──
    if total_score > 0:
        box_y = h - 80
        cv2.rectangle(frame, (5, box_y), (225, box_y + 70), (30, 25, 55), -1)
        cv2.rectangle(frame, (5, box_y), (225, box_y + 70), gender_color, 1)

        total_int = int(total_score)
        total_color = score_color_bgr(total_int)
        cv2.putText(frame, f"{total_int}/100", (20, box_y + 35),
                    cv2.FONT_HERSHEY_DUPLEX, 1.2, total_color, 2, cv2.LINE_AA)
        cv2.putText(frame, score_label(total_int), (12, box_y + 56),
                    cv2.FONT_HERSHEY_PLAIN, 1.0, total_color, 1, cv2.LINE_AA)
        cv2.putText(frame, "GLOW SCORE", (12, box_y + 14),
                    cv2.FONT_HERSHEY_PLAIN, 0.85, (130, 130, 160), 1, cv2.LINE_AA)

    # ── Face detection guide (right overlay) ──
    center_x, center_y = w // 2 + 115, h // 2
    ellipse_rx, ellipse_ry = 90, 115
    guide_color = C_GREEN if face_detected else C_RED
    cv2.ellipse(frame, (center_x, center_y), (ellipse_rx, ellipse_ry),
                0, 0, 360, guide_color, 2, cv2.LINE_AA)

    # Corner ticks on ellipse
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle)
        px = int(center_x + ellipse_rx * math.cos(rad))
        py = int(center_y + ellipse_ry * math.sin(rad))
        cv2.line(frame, (px - 8, py), (px + 8, py), guide_color, 2)
        cv2.line(frame, (px, py - 8), (px, py + 8), guide_color, 2)

    # ── Countdown ring ──
    if scanning:
        ring_cx, ring_cy = w - 60, 60
        ring_r = 45
        # Background ring
        cv2.circle(frame, (ring_cx, ring_cy), ring_r, (40, 40, 60), 4)
        # Progress arc
        progress = 1.0 - (time_left / SCAN_SECONDS)
        end_angle = int(-90 + 360 * progress)
        if progress > 0:
            cv2.ellipse(frame, (ring_cx, ring_cy), (ring_r, ring_r),
                        0, -90, end_angle, C_GOLD, 4, cv2.LINE_AA)
        # Time text
        cv2.putText(frame, str(int(time_left)), (ring_cx - 14, ring_cy + 7),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, C_WHITE, 2, cv2.LINE_AA)
        cv2.putText(frame, "SEC", (ring_cx - 12, ring_cy + 22),
                    cv2.FONT_HERSHEY_PLAIN, 0.7, C_GOLD, 1, cv2.LINE_AA)
        # Frame counter
        cv2.putText(frame, f"{frame_count} frames", (w - 100, 120),
                    cv2.FONT_HERSHEY_PLAIN, 0.85, (130, 160, 130), 1, cv2.LINE_AA)

    # ── Status bar ──
    status_y = h - 18
    cv2.rectangle(frame, (230, status_y - 14), (w, h), (20, 18, 40), -1)
    if not scanning:
        hint = "SPACE = Start Scan   Q = Quit"
        cv2.putText(frame, hint, (240, status_y),
                    cv2.FONT_HERSHEY_PLAIN, 0.9, (160, 160, 180), 1, cv2.LINE_AA)
    else:
        cv2.putText(frame, "SCANNING — keep face centered and still",
                    (240, status_y), cv2.FONT_HERSHEY_PLAIN, 0.9, C_GOLD, 1, cv2.LINE_AA)

    if not face_detected and scanning:
        cv2.putText(frame, "NO FACE DETECTED", (w//2 - 20, h//2 - 140),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75, C_RED, 2, cv2.LINE_AA)

    return frame


# ─── Auth ─────────────────────────────────────────────────────────────────────
def login_to_api(username: str, password: str):
    try:
        resp = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "password": password},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["access_token"], data["user"]
        else:
            return None, None
    except requests.exceptions.ConnectionError:
        return None, None


def post_results(token: str, feature_scores: dict, frames_analyzed: int, gender: str):
    try:
        resp = requests.post(
            f"{API_BASE}/analyze/finalize",
            json={
                "feature_scores": feature_scores,
                "frames_analyzed": frames_analyzed,
                "gender_applied": gender,
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


# ─── Compute weighted total ────────────────────────────────────────────────────
def compute_total(scores_0_1: dict, weights: dict) -> float:
    total_weight = sum(weights.values())
    total = 0.0
    for feat, val in scores_0_1.items():
        w = weights.get(feat, 0)
        total += val * (w / total_weight) * 100
    return min(total, 100.0)


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "═" * 55)
    print("  ✦  GLOWUP COACH — Face Analysis Scanner  ✦")
    print("═" * 55)

    # ── Login ──
    print("\n  Login to save results to the leaderboard.")
    print("  (Press ENTER to skip login and scan offline)\n")

    username = input("  Username: ").strip()
    token, user_info = None, None

    if username:
        password = getpass.getpass("  Password: ")
        token, user_info = login_to_api(username, password)
        if token:
            gender = user_info.get("gender", "prefer_not_to_say")
            print(f"\n  ✅ Logged in as {username}  |  Gender: {gender}")
        else:
            print("  ⚠  Could not connect to API — scanning offline.")
            print("     (Make sure the backend is running: bash start.sh)")
            gender_input = input("  Select gender [male/female/n]: ").strip().lower()
            gender = "male" if gender_input == "male" else "female" if gender_input == "female" else "prefer_not_to_say"
    else:
        username = "anonymous"
        gender_input = input("  Select gender [male/female/n]: ").strip().lower()
        gender = "male" if gender_input == "male" else "female" if gender_input == "female" else "prefer_not_to_say"

    weights = WEIGHTS_MALE if gender == "male" else WEIGHTS_FEMALE if gender == "female" else WEIGHTS_NEUTRAL

    print("\n  Camera opening... Press SPACE to start scan, Q to quit.\n")

    # ── Camera ──
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("  ❌ Could not open camera. Check camera permissions.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # State
    scanning       = False
    scan_start     = 0.0
    time_left      = float(SCAN_SECONDS)
    frame_num      = 0
    analyzed_count = 0
    acc_scores: dict[str, list] = {k: [] for k in weights}
    latest_scores  = {}
    latest_total   = 0.0
    face_detected  = False

    cv2.namedWindow("Glowup Coach — Face Scanner", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Glowup Coach — Face Scanner", 1100, 680)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame_num += 1

        # ── MediaPipe ──
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        face_detected = bool(results.multi_face_landmarks)

        if face_detected:
            face = results.multi_face_landmarks[0]

            # Draw mesh
            mp_draw.draw_landmarks(
                frame, face,
                mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_styles.get_default_face_mesh_tesselation_style()
            )

            # Analyze every FRAME_RATE frames
            if scanning and frame_num % FRAME_RATE == 0:
                raw = analyze_face(face.landmark)
                latest_scores = raw
                latest_total  = compute_total(raw, weights)

                for k, v in raw.items():
                    acc_scores[k].append(v)
                analyzed_count += 1

        # ── Countdown ──
        if scanning:
            time_left = SCAN_SECONDS - (time.time() - scan_start)
            if time_left <= 0:
                time_left = 0
                scanning  = False

                # ── Finalize results ──
                final_scores = {
                    k: float(np.mean(v)) if v else 0.0
                    for k, v in acc_scores.items()
                }
                final_total = compute_total(final_scores, weights)
                tips        = []
                rank        = None

                if token:
                    api_data = post_results(
                        token,
                        {k: v * 100 for k, v in final_scores.items()},
                        analyzed_count,
                        gender,
                    )
                    if api_data:
                        tips = api_data.get("tips", [])
                        rank = api_data.get("rank")
                        print(f"\n  ✅ Results saved! Global rank: #{rank}")

                # ── Generate PDF ──
                print("  📄 Generating PDF report...")
                pdf_path = generate_pdf(
                    username=username,
                    gender=gender,
                    total_score=final_total,
                    feature_scores={k: round(v * 100, 1) for k, v in final_scores.items()},
                    tips=tips,
                    frames_analyzed=analyzed_count,
                    rank=rank,
                    output_dir=REPORTS_DIR,
                )
                print(f"  ✅ PDF saved: {pdf_path}")

                # Show result screen
                _show_result_screen(frame, final_scores, final_total, gender, rank, pdf_path)

                # Reset for next scan
                acc_scores   = {k: [] for k in weights}
                analyzed_count = 0
                latest_scores  = {}
                latest_total   = 0.0

        # ── Draw UI ──
        frame = draw_ui(
            frame,
            latest_scores,
            latest_total,
            time_left,
            scanning,
            gender,
            analyzed_count,
            face_detected,
        )

        cv2.imshow("Glowup Coach — Face Scanner", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == 27:
            break
        elif key == ord(' '):
            if not scanning:
                scanning       = True
                scan_start     = time.time()
                time_left      = float(SCAN_SECONDS)
                acc_scores     = {k: [] for k in weights}
                analyzed_count = 0
                latest_scores  = {}
                latest_total   = 0.0
                print("  🔬 Scan started! Keep your face centered...")

    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()
    print("\n  Goodbye! ✦\n")


# ─── Result screen overlay ────────────────────────────────────────────────────
def _show_result_screen(base_frame, scores, total, gender, rank, pdf_path):
    """Show a dramatic result screen until user presses any key."""
    h, w = base_frame.shape[:2]
    result_frame = np.zeros((h, w, 3), dtype=np.uint8)
    result_frame[:] = C_BG

    # Gradient top bar
    gender_color = C_MALE if gender == "male" else C_FEMALE if gender == "female" else C_CYAN
    cv2.rectangle(result_frame, (0, 0), (w, 70), (25, 20, 50), -1)
    cv2.line(result_frame, (0, 70), (w, 70), gender_color, 3)
    cv2.putText(result_frame, "GLOWUP COACH — SCAN COMPLETE",
                (w//2 - 210, 45), cv2.FONT_HERSHEY_DUPLEX, 1.0, C_GOLD, 2, cv2.LINE_AA)

    # Total score
    total_int   = int(total)
    total_color = score_color_bgr(total_int)
    cv2.putText(result_frame, f"{total_int}", (w//2 - 60, 200),
                cv2.FONT_HERSHEY_DUPLEX, 5.0, total_color, 6, cv2.LINE_AA)
    cv2.putText(result_frame, "/100", (w//2 + 90, 190),
                cv2.FONT_HERSHEY_DUPLEX, 1.5, (160, 160, 180), 2, cv2.LINE_AA)
    cv2.putText(result_frame, score_label(total_int), (w//2 - 120, 240),
                cv2.FONT_HERSHEY_DUPLEX, 1.1, total_color, 2, cv2.LINE_AA)

    if rank:
        cv2.putText(result_frame, f"GLOBAL RANK  #{rank}",
                    (w//2 - 100, 285), cv2.FONT_HERSHEY_PLAIN, 1.3, gender_color, 1, cv2.LINE_AA)

    # Feature bars
    col1_x, col2_x = 80, w//2 + 40
    bar_w_max = 200
    items = list(scores.items())
    half = len(items) // 2

    for col_idx, col_items in enumerate([items[:half], items[half:]]):
        cx = col1_x if col_idx == 0 else col2_x
        fy = 320
        for feat, val in col_items:
            sc = int(val * 100)
            col = score_color_bgr(sc)
            cv2.putText(result_frame, feat, (cx, fy),
                        cv2.FONT_HERSHEY_PLAIN, 1.05, C_WHITE, 1, cv2.LINE_AA)
            # Track
            cv2.rectangle(result_frame, (cx, fy + 5), (cx + bar_w_max, fy + 11), (40, 40, 60), -1)
            # Fill
            fill = int(bar_w_max * val)
            cv2.rectangle(result_frame, (cx, fy + 5), (cx + fill, fy + 11), col, -1)
            cv2.putText(result_frame, str(sc), (cx + bar_w_max + 6, fy + 11),
                        cv2.FONT_HERSHEY_PLAIN, 0.9, col, 1, cv2.LINE_AA)
            fy += 26

    # PDF notice
    pdf_name = os.path.basename(pdf_path)
    cv2.putText(result_frame, f"PDF REPORT: {pdf_name}",
                (80, h - 70), cv2.FONT_HERSHEY_PLAIN, 0.9, (100, 220, 100), 1, cv2.LINE_AA)
    cv2.putText(result_frame, "Press SPACE to scan again   |   Q to quit",
                (w//2 - 190, h - 40), cv2.FONT_HERSHEY_PLAIN, 1.0, (160, 160, 180), 1, cv2.LINE_AA)

    # Disclaimer
    cv2.putText(result_frame, "* Cosmetic guidance only — not medical advice",
                (80, h - 20), cv2.FONT_HERSHEY_PLAIN, 0.75, (100, 100, 120), 1, cv2.LINE_AA)

    cv2.imshow("Glowup Coach — Face Scanner", result_frame)
    cv2.waitKey(0)


if __name__ == "__main__":
    main()
