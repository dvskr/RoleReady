from __future__ import annotations
from io import BytesIO
from typing import Dict, List, Tuple, Optional
import re, difflib

from docx import Document
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image

# ---------- Fuzzy heading mapping ----------
CANONICAL = {
    "summary": ["summary","professional summary","profile","about me","overview","executive summary","career summary","objective"],
    "skills": ["skills","technical skills","core competencies","skills & tools","competencies","key skills","technology stack","stack"],
    "experience": ["experience","work experience","professional experience","employment","work history","career history","relevant experience"],
    "projects": ["projects","selected projects","personal projects","key projects"],
    "education": ["education","academics","academic background"],
    "certifications": ["certifications","licenses","certs"]
}
MISSPELLINGS = {
    "summery":"professional summary","sumary":"summary","proffesional summary":"professional summary",
    "experiance":"experience","work experiance":"work experience","educatoin":"education","cerifications":"certifications"
}
ALL_ALIASES: Dict[str,str] = {}
for canon,names in CANONICAL.items():
    for n in names: ALL_ALIASES[n]=canon
for wrong,right in MISSPELLINGS.items():
    # map misspelling to same bucket as corrected phrase
    target = None
    for k,v in CANONICAL.items():
        if right in v or right==k:
            target = k; break
    if target: ALL_ALIASES[wrong] = target
ALL_KEYS = list(ALL_ALIASES.keys())

def _norm_heading(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[:\-\u2013\u2014]+$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.lower()

def _maybe_heading(line: str) -> Optional[str]:
    s = _norm_heading(line)
    if not s or len(s) > 60 or s.endswith("."):
        return None
    if s in ALL_ALIASES:
        return ALL_ALIASES[s]
    match = difflib.get_close_matches(s, ALL_KEYS, n=1, cutoff=0.78)
    if match: return ALL_ALIASES[match[0]]
    if line.isupper():
        match = difflib.get_close_matches(s.title(), ALL_KEYS, n=1, cutoff=0.72)
        if match: return ALL_ALIASES[match[0]]
    return None

# ---------- Cleaners & splitters ----------
_bullet_re = re.compile(r"^(?:[-•·*]|\u2022|\d+\.)\s+")
_space = re.compile(r"\s+")
_newline = re.compile(r"\r\n?")

def _clean_lines(text: str) -> List[str]:
    text = _newline.sub("\n", text)
    lines = [_space.sub(" ", ln).strip() for ln in text.split("\n")]
    return [ln for ln in lines if ln]

def _split_sections(lines: List[str]) -> Dict[str,List[str]]:
    sections: Dict[str,List[str]] = {}
    cur = "other"
    sections[cur] = []
    for ln in lines:
        bucket = _maybe_heading(ln)
        if bucket:
            cur = bucket
            sections.setdefault(cur, [])
        else:
            sections.setdefault(cur, []).append(ln)
    return sections

def _extract_skills(lines: List[str]) -> List[str]:
    text = " ".join(lines)
    parts = re.split(r"[,/|;]|\u2022|\n", text)
    skills, seen, out = [], set(), []
    for p in parts:
        t = p.strip()
        if not t or len(t) > 40 or re.search(r"\d{4}|@|https?://", t): continue
        skills.append(t)
    for s in skills:
        k = s.lower()
        if k not in seen:
            seen.add(k); out.append(s)
    return out[:80]

def _extract_bullets_from_lines(lines: List[str]) -> List[str]:
    bullets: List[str] = []
    cur: List[str] = []
    def flush():
        nonlocal bullets, cur
        if cur:
            txt = " ".join(cur).strip()
            if len(txt.split()) >= 5:
                bullets.append(txt)
            cur = []
    for ln in lines:
        if _bullet_re.match(ln):
            flush()
            bullets.append(_bullet_re.sub("", ln).strip()); continue
        if not ln.strip():
            flush(); continue
        # single-sentence heuristic
        if ln.strip().endswith(".") and len(ln.split()) >= 5 and not cur:
            bullets.append(ln.strip())
        else:
            cur.append(ln.strip())
    flush()
    # de-dupe
    out, seen = [], set()
    for b in bullets:
        k = b.lower()
        if k not in seen:
            seen.add(k); out.append(b)
    return out[:200]

# ---------- PDF text-layer detection & OCR ----------
def _pdf_text_density(pdf_bytes: bytes, pages_to_check: int = 3) -> float:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    n = min(pages_to_check, len(doc))
    if n == 0: return 0.0
    total_chars = 0
    for i in range(n):
        page = doc.load_page(i)
        txt = page.get_text("text")
        total_chars += len(txt or "")
    doc.close()
    return total_chars / max(n,1)

def _ocr_pdf_to_text(pdf_bytes: bytes, dpi: int = 200) -> str:
    try:
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
        ocr_texts = []
        for img in images:
            if not isinstance(img, Image.Image):
                img = img.convert("RGB")
            ocr_texts.append(pytesseract.image_to_string(img))
        return "\n".join(ocr_texts)
    except Exception as e:
        # Fallback if OCR fails (e.g., Tesseract not installed)
        print(f"OCR failed: {e}")
        return ""

# ---------- DOCX & PDF parsing paths ----------
def _docx_text_with_tables(doc: Document) -> List[str]:
    lines = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                t = cell.text.strip()
                if t: lines.append(t)
    return lines

def _parse_from_lines(lines: List[str]) -> Dict:
    lines = _clean_lines("\n".join(lines)) if isinstance(lines, list) else _clean_lines(lines)
    sections = _split_sections(lines)
    summary = " ".join(
        sections.get("summary", []) or sections.get("professional summary", []) or sections.get("profile", [])
    )[:1000]  # keep it shortish
    skill_lines = (
        sections.get("skills", []) + sections.get("technical skills", []) +
        sections.get("core competencies", []) + sections.get("skills & tools", [])
    )
    skills = _extract_skills(skill_lines)
    exp_lines = (
        sections.get("experience", []) + sections.get("work experience", []) +
        sections.get("professional experience", []) + sections.get("employment", []) +
        sections.get("work history", [])
    )
    experience = _extract_bullets_from_lines(exp_lines) or _extract_bullets_from_lines(lines)
    return {"summary": summary, "skills": skills, "experience": experience}

def parse_docx(file_bytes: bytes) -> Tuple[Dict,str]:
    doc = Document(BytesIO(file_bytes))
    structure = _parse_from_lines(_docx_text_with_tables(doc))
    return structure, "docx"

def parse_pdf(file_bytes: bytes) -> Tuple[Dict,str]:
    density = _pdf_text_density(file_bytes)
    if density >= 200:  # ~200+ chars per page → likely has text layer
        text = pdfminer_extract(BytesIO(file_bytes)) or ""
        structure = _parse_from_lines(text)
        path = "pdf_text"
    else:
        # OCR fallback
        text = _ocr_pdf_to_text(file_bytes)
        structure = _parse_from_lines(text)
        path = "pdf_ocr"
    return structure, path

def parse_any(filename: str, file_bytes: bytes) -> Dict:
    if filename.lower().endswith(".docx"):
        structure, path = parse_docx(file_bytes)
    elif filename.lower().endswith(".pdf"):
        structure, path = parse_pdf(file_bytes)
    else:
        # plain text or unknown; try as text
        text = file_bytes.decode(errors="ignore")
        structure = _parse_from_lines(text)
        path = "plain_text"

    # Confidence score: headings found + items count
    conf = 0.0
    if structure.get("summary"): conf += 0.35
    if structure.get("skills"): conf += 0.25
    if len(structure.get("experience", [])) >= 5: conf += 0.25
    if len(structure.get("experience", [])) >= 10: conf += 0.15
    structure["confidence"] = round(conf, 2)
    structure["extraction_path"] = path
    structure["raw_text_present"] = bool(structure.get("summary") or structure.get("experience"))

    return structure