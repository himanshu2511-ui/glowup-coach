/**
 * faceScorer.js
 * JavaScript port of backend analyzer.py + scorer.py
 * Runs entirely in the browser on MediaPipe landmark data.
 */

// ─── Distance & symmetry helpers ──────────────────────────────────────────────
function dist(p1, p2) {
  const dx = p1.x - p2.x
  const dy = p1.y - p2.y
  return Math.sqrt(dx * dx + dy * dy)
}

function symmetryScore(left, right, center) {
  const l = Math.abs(left.x - center.x)
  const r = Math.abs(right.x - center.x)
  return Math.max(0, 1 - Math.abs(l - r) / (Math.max(l, r, 1e-6)))
}

function clamp(v) { return Math.max(0, Math.min(1, v)) }

function stdDev(arr) {
  const mean = arr.reduce((a, b) => a + b, 0) / arr.length
  return Math.sqrt(arr.reduce((s, v) => s + (v - mean) ** 2, 0) / arr.length)
}

// ─── Gender-specific weights (must match backend scorer.py) ───────────────────
export const WEIGHTS = {
  male: {
    Symmetry: 22, Eyes: 9,  Eyebrows: 7,  Nose: 12, Lips: 8,
    Cheeks: 6,   Jawline: 18, Ears: 5,   Forehead: 8, Chin: 5,
  },
  female: {
    Symmetry: 25, Eyes: 13, Eyebrows: 9,  Nose: 8,  Lips: 12,
    Cheeks: 8,   Jawline: 5, Ears: 4,   Forehead: 7, Chin: 9,
  },
  prefer_not_to_say: {
    Symmetry: 23, Eyes: 11, Eyebrows: 8,  Nose: 10, Lips: 10,
    Cheeks: 7,   Jawline: 11, Ears: 4,   Forehead: 7, Chin: 7,
  },
}

// ─── Core analysis ─────────────────────────────────────────────────────────────
/**
 * Analyze a single MediaPipe FaceMesh landmark array.
 * Returns scores as 0–1 floats per feature.
 */
export function analyzeFrame(landmarks) {
  const lm = landmarks
  const center = lm[1] // nose bridge
  const scores = {}

  // 1. Symmetry (average of 4 landmark pairs)
  scores.Symmetry = clamp(
    (symmetryScore(lm[33],  lm[263], center) +
     symmetryScore(lm[61],  lm[291], center) +
     symmetryScore(lm[172], lm[397], center) +
     symmetryScore(lm[234], lm[454], center)) / 4
  )

  // 2. Eyes — aspect ratio + symmetry
  const lEyeW = dist(lm[33],  lm[133])
  const rEyeW = dist(lm[362], lm[263])
  const lEyeH = dist(lm[159], lm[145])
  const rEyeH = dist(lm[386], lm[374])
  const avgRatio = ((lEyeH / (lEyeW + 1e-6)) + (rEyeH / (rEyeW + 1e-6))) / 2
  const eyeRatioScore = clamp(1 - Math.abs(avgRatio - 0.35) / 0.25)
  const eyeSymScore   = symmetryScore(lm[33], lm[263], center)
  scores.Eyes = clamp((eyeRatioScore + eyeSymScore) / 2)

  // 3. Eyebrows — symmetry
  scores.Eyebrows = clamp(
    (symmetryScore(lm[70],  lm[300], center) +
     symmetryScore(lm[105], lm[334], center)) / 2
  )

  // 4. Nose — straightness + width proportion
  const noseStraight = clamp(1 - Math.abs(lm[1].x - center.x) * 20)
  const faceW    = dist(lm[234], lm[454])
  const noseW    = dist(lm[49],  lm[279])
  const noseProp = clamp(1 - Math.abs((noseW / (faceW + 1e-6)) - 0.25) / 0.15)
  scores.Nose = clamp((noseStraight + noseProp) / 2)

  // 5. Lips — width ratio + cupid's bow symmetry
  const mouthW = dist(lm[61], lm[291])
  const mouthH = dist(lm[13], lm[14])
  const lipRatio    = mouthW / (mouthH + 1e-6)
  const ratioScore  = clamp(1 - Math.abs(lipRatio - 3.0) / 3.0)
  const cupidSym    = clamp(1 - Math.abs(dist(lm[61], lm[62]) - dist(lm[291], lm[292])) * 10)
  scores.Lips = clamp((ratioScore + cupidSym) / 2)

  // 6. Cheeks — width symmetry
  scores.Cheeks = clamp(
    (symmetryScore(lm[50],  lm[280], center) +
     symmetryScore(lm[116], lm[345], center)) / 2
  )

  // 7. Jawline — smoothness + symmetry
  const jawIndices = [172, 136, 150, 149, 148, 152, 377, 400, 378, 379, 397]
  const jawPts = jawIndices.map(i => lm[i])
  const segs   = []
  for (let i = 0; i < jawPts.length - 1; i++) segs.push(dist(jawPts[i], jawPts[i + 1]))
  const avgSeg    = segs.reduce((a, b) => a + b, 0) / segs.length
  const smoothness = clamp(1 - stdDev(segs) / (avgSeg + 1e-6))
  const jawSym     = symmetryScore(lm[172], lm[397], center)
  scores.Jawline = clamp(smoothness * 0.4 + jawSym * 0.6)

  // 8. Ears — position symmetry
  scores.Ears = clamp(symmetryScore(lm[234], lm[454], center))

  // 9. Forehead — balance + symmetry
  const faceH      = dist(lm[10], lm[152])
  const foreH      = dist(lm[10], lm[168])
  const foreRatio  = foreH / (faceH + 1e-6)
  const foreScore  = clamp(1 - Math.abs(foreRatio - 0.33) / 0.15)
  scores.Forehead = clamp((foreScore + symmetryScore(lm[109], lm[338], center)) / 2)

  // 10. Chin — depth projection
  const chinH   = dist(lm[152], lm[199])
  const lowerH  = dist(lm[2],   lm[152])
  const chinRatio = chinH / (lowerH + 1e-6)
  scores.Chin = clamp(1 - Math.abs(chinRatio - 0.35) / 0.2)

  return scores // all values 0–1
}

// ─── Weighted total ────────────────────────────────────────────────────────────
/**
 * Compute weighted total score (0–100) from 0–1 feature scores.
 * @param {Object} scores0to1 - feature scores 0-1
 * @param {string} gender     - 'male' | 'female' | 'prefer_not_to_say'
 */
export function computeTotal(scores0to1, gender) {
  const w = WEIGHTS[gender] || WEIGHTS.prefer_not_to_say
  const totalW = Object.values(w).reduce((a, b) => a + b, 0)
  let total = 0
  for (const [feat, val] of Object.entries(scores0to1)) {
    total += val * ((w[feat] || 0) / totalW) * 100
  }
  return Math.min(Math.max(total, 0), 100)
}

// ─── Label helpers ─────────────────────────────────────────────────────────────
export function scoreLabel(s) {
  if (s >= 92) return 'Elite'
  if (s >= 82) return 'Very Attractive'
  if (s >= 70) return 'Attractive'
  if (s >= 55) return 'Above Average'
  if (s >= 40) return 'Average'
  return 'Needs Work'
}

export function scoreColor(s) {
  if (s >= 80) return '#a78bfa'
  if (s >= 60) return '#34d399'
  if (s >= 40) return '#fbbf24'
  return '#f87171'
}

// ─── Accumulator ──────────────────────────────────────────────────────────────
/**
 * Merge a new frame score into a running average accumulator.
 * acc: { FeatureName: number[] }
 */
export function accumulate(acc, frameScores) {
  for (const [k, v] of Object.entries(frameScores)) {
    if (!acc[k]) acc[k] = []
    acc[k].push(v)
  }
  return acc
}

/**
 * Average the accumulated scores.
 * Returns { FeatureName: 0–1 }
 */
export function finalizeAcc(acc) {
  const out = {}
  for (const [k, arr] of Object.entries(acc)) {
    out[k] = arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0
  }
  return out
}

export const FEATURE_ICONS = {
  Symmetry: '⚖', Eyes: '👁', Eyebrows: '〰', Nose: '👃',
  Lips: '💋', Cheeks: '🫧', Jawline: '🔲', Ears: '👂',
  Forehead: '📐', Chin: '🫦',
}

// ── Unique color per feature (used across UI + scanner bars) ──────────────────
export const FEATURE_COLORS = {
  Symmetry: '#00d4ff',   // cyan
  Eyes:     '#a855f7',   // violet
  Eyebrows: '#f59e0b',   // amber
  Nose:     '#f97316',   // orange
  Lips:     '#ec4899',   // pink
  Cheeks:   '#10b981',   // emerald
  Jawline:  '#3b82f6',   // blue
  Ears:     '#8b5cf6',   // purple
  Forehead: '#14b8a6',   // teal
  Chin:     '#f43f5e',   // rose
}

// ── Realistic glowup potential gain per feature (added to current score) ──────
// Based on scientific literature on non-surgical improvement potential
export const POTENTIAL_GAINS = {
  Symmetry: 12,   // posture, mewing, bilateral chewing
  Eyes:     20,   // depuffing, lash serum, skincare
  Eyebrows: 25,   // shaping, serum, microblading
  Nose:     8,    // contouring, rhinoplasty option
  Lips:     20,   // hydration, filler option, plumping
  Cheeks:   18,   // gua sha, fat loss, contouring
  Jawline:  25,   // mewing, mastic gum, fat loss
  Ears:     6,    // minimal (structural)
  Forehead: 12,   // hairstyle, brow shaping
  Chin:     20,   // posture, chin projection
}

/**
 * Compute potential score after following the 4-week glowup plan.
 * @param {number} currentScore - 0-100
 * @param {string} feature
 * @returns {number} potential score capped at 95
 */
export function potentialScore(currentScore, feature) {
  const gain = POTENTIAL_GAINS[feature] || 10
  return Math.min(currentScore + gain, 95)
}
