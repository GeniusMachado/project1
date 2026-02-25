import os
import json
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

import time
import os

try:
    import google.genai as genai
except Exception:
    genai = None

from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-proto")


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """Try to extract human-readable text from uploaded bytes.
    - PDFs: use PyPDF2 if available
    - Otherwise try UTF-8 decode with fallback
    """
    lower = filename.lower()
    if lower.endswith(".pdf") and PdfReader is not None:
        try:
            reader = PdfReader()
            from io import BytesIO
            reader.stream = BytesIO(file_bytes)
            text_parts = []
            for p in reader.pages:
                try:
                    text_parts.append(p.extract_text() or "")
                except Exception:
                    continue
            return "\n".join(text_parts).strip()
        except Exception:
            pass

    # Try plain text decode
    try:
        return file_bytes.decode("utf-8")
    except Exception:
        try:
            return file_bytes.decode("latin-1")
        except Exception:
            return ""


def analyze_text_with_pandas(text: str) -> Dict[str, Any]:
    """Return simple statistics and a small word-frequency dataframe."""
    words = []
    if not text:
        return {
            "total_words": 0,
            "unique_words": 0,
            "top_words": [],
            "avg_word_length": 0.0,
            "std_word_length": 0.0,
            "word_counts": []
        }

    # Simple tokenization by whitespace and remove short tokens
    tokens = [w.strip("\n\r .,;:()[]{}\"'`)\n") for w in text.split() if len(w.strip()) > 0]
    tokens = [t.lower() for t in tokens if len(t) > 0]

    s = pd.Series(tokens)
    counts = s.value_counts()

    word_lengths = np.array([len(w) for w in tokens], dtype=float) if tokens else np.array([])

    top = counts.head(20).items()
    top_list = [{"word": k, "count": int(v)} for k, v in top]

    return {
        "total_words": int(len(tokens)),
        "unique_words": int(s.nunique()) if not s.empty else 0,
        "top_words": top_list,
        "avg_word_length": float(np.mean(word_lengths)) if word_lengths.size else 0.0,
        "std_word_length": float(np.std(word_lengths)) if word_lengths.size else 0.0,
        "word_counts": counts.head(200).to_dict()
    }


def ai_summarize_text(text: str, max_chars: int = 1000) -> str:
    """Summarize text using Google Gemini if available, otherwise fallback.
    Keeps prompt minimal.
    """
    if not text:
        return "(no text extracted)"

    if genai is not None and GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            client = genai.GenerativeModel(LLM_MODEL)
            prompt = (
                "Summarize the following text in 3 concise bullet points.\n\n" + text[:4000]
            )
            resp = client.generate_content(prompt)
            # the SDK returns .text
            return (resp.text or "").strip()[:max_chars]
        except Exception:
            pass

    # Fallback: return first 3 sentences
    sentences = text.replace('\n', ' ').split('.')
    sentences = [s.strip() for s in sentences if s.strip()]
    return '. '.join(sentences[:3]) + ('.' if len(sentences) >= 3 else '')


def process_uploaded_file(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Full processing pipeline: extract text -> analyze -> AI summary.
    Returns a JSON-serializable dict with analysis results.
    """
    start = time.time()
    text = extract_text_from_bytes(file_bytes, filename)
    analysis = analyze_text_with_pandas(text)
    summary = ai_summarize_text(text)

    result = {
        "filename": filename,
        "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "processing_seconds": round(time.time() - start, 3),
        "analysis": analysis,
        "ai_summary": summary,
    }
    return result


def save_analysis_for_id(file_id: int, analysis: Dict[str, Any], out_dir: str = "output") -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"analysis_{file_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    return path


def load_analysis_for_id(file_id: int, out_dir: str = "output") -> Dict[str, Any]:
    path = os.path.join(out_dir, f"analysis_{file_id}.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
