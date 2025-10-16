from openai import OpenAI
import os, re, json

# Initialize OpenAI client only if API key is available
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

SYSTEM_PROMPT = (
  "You are an expert technical resume writer. Rewrite or improve the given text strictly in context, keeping factual accuracy."
)

SYSTEM_AGGRESSIVE = (
  "You are an expert technical resume editor. "
  "Rewrite bullets to improve relevance to the job description without inventing experience. "
  "Follow all constraints precisely and respond ONLY with JSON."
)

def _extract_tech(text: str) -> set[str]:
    """Extract technology names from text"""
    cand = re.split(r"[,;/|()\n]+", text)
    keep = []
    for t in cand:
        s = t.strip()
        if 2 <= len(s) <= 40 and not re.search(r"\d{3,}", s):
            keep.append(s)
    return set(k.lower() for k in keep)

def rewrite_experience_aggressive(bullets: list[str], jd_keywords: list[str], resume_skills: list[str]) -> list[str]:
    """Aggressive-but-safe rewrite that distributes keywords intelligently"""
    if not client:
        # Demo mode with better simulation
        result = []
        used_keywords = set()
        for i, bullet in enumerate(bullets):
            # Find one relevant keyword for this bullet
            relevant_kw = next((kw for kw in jd_keywords[:8] if kw.lower() in bullet.lower() and kw not in used_keywords), None)
            if not relevant_kw:
                relevant_kw = next((kw for kw in jd_keywords[:8] if kw not in used_keywords), None)
            if relevant_kw:
                used_keywords.add(relevant_kw)
                result.append(f"[Enhanced with {relevant_kw}] {bullet}")
            else:
                result.append(bullet)
        return result

    # 1) Allowed keywords = present skills/tools OR already inside the bullets text
    flat_text = "\n".join(bullets)
    present = _extract_tech(", ".join(resume_skills) + "\n" + flat_text)
    allowed = [kw for kw in jd_keywords if kw.lower() in present]

    # Fallback: if too few allowed, still keep top 8 jd keywords but mark them "soft" (no new tools)
    if len(allowed) < 8:
        allowed = list(dict.fromkeys(jd_keywords))[:8]

    # 2) Distribute: at most 1 allowed kw per bullet, don't repeat
    used = set()
    targets = []
    for i, b in enumerate(bullets):
        pick = next((kw for kw in allowed if kw not in used and kw.lower() in b.lower()), None)
        # if bullet already contains one, fine; else pick a new one not used yet
        if not pick:
            pick = next((kw for kw in allowed if kw not in used), None)
        if pick:
            used.add(pick)
        targets.append(pick or "")

    # 3) Build strict JSON instruction
    schema = {
        "type": "object",
        "properties": {
            "bullets": { "type": "array", "items": { "type": "string" } }
        },
        "required": ["bullets"]
    }

    instruction = {
        "constraints": {
            "max_words_per_bullet": 45,
            "max_new_keywords_per_bullet": 1,
            "forbidden": ["fabrication", "exaggeration"],
            "ensure": ["metrics where possible", "action + impact + tech order"],
            "allowed_keywords": allowed
        },
        "mapping": [
            {"bullet_index": i, "place_keyword": targets[i] or None}
            for i in range(len(bullets))
        ],
        "source_bullets": bullets
    }

    msg_user = (
        "Rewrite each bullet to be more aligned with the job description. "
        "Use at most one keyword from 'allowed_keywords' for each bullet as indicated in 'mapping.place_keyword'. "
        "If the keyword is not contextually justified by the source bullet, omit it. "
        "Never add tools, products, or certifications that are not already present in the source bullets or in the candidate skills. "
        "Keep each bullet <= {max_words_per_bullet} words. Preserve truthfulness; do not invent numbers."
    ).format(max_words_per_bullet=instruction["constraints"]["max_words_per_bullet"])

    resp = client.chat.completions.create(
        model="gpt-4o",  # Using gpt-4o instead of gpt-5-large
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM_AGGRESSIVE},
            {"role": "user", "content": msg_user + "\n\nSCHEMA:\n" + json.dumps(schema) + "\n\nDATA:\n" + json.dumps(instruction)}
        ]
    )
    try:
        js = json.loads(resp.choices[0].message.content)
        out = [b.strip() for b in js.get("bullets", []) if b.strip()]
        return out or bullets
    except Exception:
        return bullets

def rewrite_text(section: str, text: str, jd_keywords: list[str], resume_skills: list[str] = None) -> str:
    """Main rewrite function with smart keyword distribution"""
    if not client:
        # Better demo mode
        if section == "experience":
            bullets = [line.strip() for line in text.split('\n') if line.strip()]
            if bullets:
                return '\n'.join(rewrite_experience_aggressive(bullets, jd_keywords, resume_skills or []))
        return f"[Demo Mode] Enhanced {section} with relevant keywords from: {', '.join(jd_keywords[:5])}\n\n{text}"
    
    # For experience sections, use the aggressive-but-safe approach
    if section == "experience":
        bullets = [line.strip() for line in text.split('\n') if line.strip()]
        if bullets:
            rewritten_bullets = rewrite_experience_aggressive(bullets, jd_keywords, resume_skills or [])
            return '\n'.join(rewritten_bullets)
    
    # For other sections, use the original approach
    joined = ", ".join(jd_keywords[:10])
    user_prompt = f"Section: {section}\nJD keywords: {joined}\nText to rewrite:\n{text}"
    completion = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.4,
        messages=[
            {"role":"system", "content":SYSTEM_PROMPT},
            {"role":"user", "content":user_prompt}
        ]
    )
    return completion.choices[0].message.content.strip()
