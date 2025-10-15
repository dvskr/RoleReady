from __future__ import annotations
from typing import List, Dict
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords

_stop = set(stopwords.words("english"))
_token = re.compile(r"[A-Za-z][A-Za-z0-9+._-]{1,}")

def top_keywords(text: str, top_n: int = 20) -> List[str]:
    vec = TfidfVectorizer(ngram_range=(1,2), stop_words="english", min_df=1)
    X = vec.fit_transform([text])
    vocab = vec.get_feature_names_out()
    scores = X.toarray()[0]
    pairs = sorted(zip(vocab, scores), key=lambda x: x[1], reverse=True)
    out: List[str] = []
    for term, _ in pairs:
        t = term.strip()
        if len(t) < 3: continue
        if t.lower() in _stop: continue
        out.append(t)
        if len(out) == top_n: break
    return out

def alignment_score(resume_text: str, jd_text: str) -> Dict:
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2), min_df=1)
    X = vec.fit_transform([jd_text, resume_text])
    sim = cosine_similarity(X[0:1], X[1:2])[0][0]
    jd_terms = top_keywords(jd_text, 25)
    missing = [t for t in jd_terms if t.lower() not in resume_text.lower()][:15]
    return {"score": round(float(sim) * 100, 2), "missing_keywords": missing, "jd_keywords": jd_terms}
