from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np
from roleready_api.services.embeddings import embed_texts
from roleready_api.services.jd_analysis import top_keywords  # reuse TF-IDF keyword picker

# Utility: cosine similarity via dot product (embeddings normalized)
def _cos(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a @ b.T  # [A x D] @ [D x B] -> [A x B]

def best_alignments(resume_bullets: List[str], jd_lines: List[str]) -> Dict:
    if not jd_lines or not resume_bullets:
        return {"score": 0.0, "per_jd": [], "missing_keywords": [], "jd_keywords": []}

    A = embed_texts(jd_lines)         # [J x 384]
    B = embed_texts(resume_bullets)   # [R x 384]
    sims = _cos(A, B)                 # [J x R]

    # For each JD line, grab best matching bullet index and score
    j_best_idx = sims.argmax(axis=1)
    j_best = sims.max(axis=1)         # [J]

    # Aggregate score: mean of top sims scaled to 0..100
    score = float(j_best.mean() * 100)

    per_jd = []
    for j, line in enumerate(jd_lines):
        r_idx = int(j_best_idx[j])
        per_jd.append({
            "jd_line": line,
            "best_bullet_index": r_idx,
            "best_bullet": resume_bullets[r_idx],
            "similarity": float(j_best[j])
        })

    # Keyword list (TF-IDF surface terms) + missing terms by substring check
    jd_keywords = top_keywords("\n".join(jd_lines), 25)
    flat_resume = "\n".join(resume_bullets)
    missing = [t for t in jd_keywords if t.lower() not in flat_resume.lower()][:15]

    return {
        "score": round(score, 2),
        "per_jd": per_jd,
        "missing_keywords": missing,
        "jd_keywords": jd_keywords,
    }
