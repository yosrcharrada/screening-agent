import os
import re
import json
import math
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

# Try LangChain wrapper (optional)
try:
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
except Exception:
    ChatGoogleGenerativeAI = None  # type: ignore
    GoogleGenerativeAIEmbeddings = None  # type: ignore

# Google direct SDK
try:
    import google.generativeai as genai
except Exception:
    genai = None  # type: ignore

# OpenAI SDK
try:
    from openai import OpenAI  # pip install openai
except Exception:
    OpenAI = None  # type: ignore

# Optional local embeddings
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None  # type: ignore

logger = logging.getLogger(__name__)

def _split_sentences(text: str) -> List[str]:
    if not text:
        return []
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in parts if 8 <= len(s.strip()) <= 600]

def _cos_sim(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

@dataclass
class Evidence:
    quote: str
    start: int
    end: int
    score: float

def _unique(seq):
    seen = set()
    out = []
    for s in seq:
        if s and s not in seen:
            seen.add(s); out.append(s)
    return out

class QuestionXAIJudge:
    """
    Robust XAI judge:
    - Provider order: Google via LangChain → Google direct → OpenAI
    - Embeddings: disabled by default (XAI_DISABLE_EMBEDDINGS=1). Optional local embeddings supported via XAI_EMBED_MODEL="local/<hf_model>"
    """
    def __init__(self, model_name: Optional[str] = None):
        self.google_key = os.getenv("GOOGLE_API_KEY_XAI") or os.getenv("GOOGLE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        preferred = (model_name or os.getenv("XAI_MODEL") or "").strip()
        self.candidates = _unique([
            preferred,
            "gemini-1.5-pro",
            "gemini-1.5-pro-latest",
            "models/gemini-1.5-pro",
            "models/gemini-1.5-pro-latest",
            "gemini-pro",
            "models/gemini-pro",
            "gemini-1.0-pro",
            "models/gemini-1.0-pro",
        ])
        self.disable_emb = os.getenv("XAI_DISABLE_EMBEDDINGS", "").lower() in ("1","true","yes")
        self.embed_model = os.getenv("XAI_EMBED_MODEL", "text-embedding-004")  # supports local/<model> too

        self.llm_langchain = None
        self.llm_google_direct = None
        self.llm_openai: Optional[OpenAI] = None
        self.embedder = None
        self.local_embedder = None
        self.model_used: Optional[str] = None
        self.provider_used: Optional[str] = None
        self._direct_ready = False

        # 1) Google via LangChain
        if self.google_key and ChatGoogleGenerativeAI is not None:
            for m in self.candidates:
                try:
                    if not m:
                        continue
                    self.llm_langchain = ChatGoogleGenerativeAI(
                        model=m,
                        temperature=0.2,
                        google_api_key=self.google_key
                    )
                    self.model_used = m
                    self.provider_used = "google_langchain"
                    logger.info(f"✅ XAI judge: LangChain Google model={m}")
                    break
                except Exception as e:
                    logger.warning(f"XAI LC model '{m}' init failed; next. Error: {e}")
                    self.llm_langchain = None

        # 2) OpenAI fallback (initialize now so we always have a provider)
        if OpenAI is not None and self.openai_key:
            try:
                self.llm_openai = OpenAI(api_key=self.openai_key)
                self.provider_used = self.provider_used or "openai"
                logger.info(f"✅ XAI judge: OpenAI ready")
            except Exception as e:
                logger.warning(f"XAI judge OpenAI init failed: {e}")
                self.llm_openai = None

        # Google direct deferred
        if not self.llm_langchain and (not self.google_key or genai is None):
            logger.warning("XAI judge: Google direct not available (missing key or SDK).")

        # Embeddings setup
        if self.disable_emb:
            logger.info("XAI embeddings disabled (heuristic evidence).")
        else:
            if self.embed_model.startswith("local/") and SentenceTransformer is not None:
                try:
                    local_name = self.embed_model.split("/", 1)[1]
                    self.local_embedder = SentenceTransformer(local_name)
                    logger.info(f"✅ Local embeddings initialized: {local_name}")
                except Exception as e:
                    logger.error(f"Local embeddings init failed: {e}")
            elif GoogleGenerativeAIEmbeddings is not None and self.google_key:
                try:
                    self.embedder = GoogleGenerativeAIEmbeddings(model=self.embed_model, google_api_key=self.google_key)
                    logger.info(f"✅ XAI embeddings initialized (LangChain, model={self.embed_model}).")
                except Exception as e:
                    logger.error(f"Embedding init failed (LangChain). Error: {e}")

    def _ensure_google_direct(self) -> None:
        if self._direct_ready or not self.google_key or genai is None:
            return
        for m in self.candidates:
            try:
                if not m:
                    continue
                genai.configure(api_key=self.google_key)
                model = genai.GenerativeModel(m)
                _ = model.generate_content("ping").text
                self.llm_google_direct = model
                self._direct_ready = True
                self.provider_used = "google_direct"
                self.model_used = m
                logger.info(f"✅ XAI judge: Google direct model={m}")
                return
            except Exception as e:
                logger.warning(f"XAI direct model '{m}' init failed; next. Error: {e}")
        logger.error("❌ XAI judge: no Google direct model worked.")

    def _invoke(self, prompt: str) -> str:
        # Prefer LangChain
        if self.llm_langchain is not None:
            try:
                resp = self.llm_langchain.invoke(prompt)
                return resp.content if hasattr(resp, "content") else str(resp)
            except Exception as e:
                logger.warning(f"XAI LC invoke failed; trying Google direct. Error: {e}")

        # Google direct
        self._ensure_google_direct()
        if self.llm_google_direct is not None:
            try:
                resp = self.llm_google_direct.generate_content(prompt)
                if hasattr(resp, "text") and resp.text:
                    return resp.text
                parts = []
                for cand in getattr(resp, "candidates", []) or []:
                    for p in getattr(cand, "content", {}).get("parts", []):
                        parts.append(getattr(p, "text", "") or "")
                return "\n".join([p for p in parts if p])
            except Exception as e:
                logger.warning(f"XAI Google direct failed; trying OpenAI. Error: {e}")

        # OpenAI
        if self.llm_openai is not None:
            resp = self.llm_openai.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert interviewer and XAI judge."},
                    {"role": "user", "content": prompt}
                ],
                model=os.getenv("XAI_OPENAI_MODEL", "gpt-4o")
            )
            return resp.choices[0].message.content or ""

        raise RuntimeError("No judge LLM available")

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self.disable_emb:
            raise RuntimeError("Embeddings disabled")
        if self.local_embedder is not None:
            vecs = self.local_embedder.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            return [v.tolist() for v in vecs]
        if self.embedder is not None:
            return self.embedder.embed_documents(texts)
        if genai is not None and self.google_key:
            res = genai.embed_content(model=self.embed_model, content=texts)
            if hasattr(res, "embeddings"):
                return [e.values for e in res.embeddings]  # type: ignore
            if isinstance(res, dict) and "embeddings" in res:
                return [e.get("values", []) for e in res["embeddings"]]
            if isinstance(res, dict) and "embedding" in res:
                return [res["embedding"]["values"]]
        raise RuntimeError("Embeddings unavailable")

    def _top_evidence(self, full_text: str, query: str, k: int = 2) -> List[Evidence]:
        if not full_text:
            return []
        sents = _split_sentences(full_text)
        if not sents:
            return []

        # Heuristic if embeddings off/unavailable
        def heuristic():
            scored = []
            q_tokens = set(re.findall(r"\b\w+\b", query.lower()))
            for s in sents:
                s_tokens = set(re.findall(r"\b\w+\b", s.lower()))
                overlap = len(q_tokens & s_tokens) / (len(q_tokens) + 1e-6)
                idx = full_text.find(s)
                scored.append(Evidence(s, idx, idx + len(s), float(overlap)))
            return sorted(scored, key=lambda e: e.score, reverse=True)[:k]

        if self.disable_emb:
            return heuristic()

        try:
            q_vecs = self._embed_texts([query])
            s_vecs = self._embed_texts(sents)
        except Exception as e:
            logger.error(f"Embedding error; fallback heuristic. Error: {e}")
            return heuristic()

        q_vec = q_vecs[0] if q_vecs else []
        scored: List[Evidence] = []
        for s, v in zip(sents, s_vecs):
            score = _cos_sim(q_vec, v)
            idx = full_text.find(s)
            scored.append(Evidence(s, idx, idx + len(s), float(score)))
        return sorted(scored, key=lambda e: e.score, reverse=True)[:k]

    def explain_question(self, question_obj: Dict, cv_text: str, jd_text: str) -> Dict:
        q_text = question_obj.get("question", "")
        target_skill = question_obj.get("target_skill") or question_obj.get("focus") or ""
        retrieval_query = f"{target_skill} {q_text}".strip()

        cv_ev = self._top_evidence(cv_text, retrieval_query, k=2)
        jd_ev = self._top_evidence(jd_text, retrieval_query, k=2)

        # If no LLM, heuristic XAI
        if self.llm_langchain is None and self.llm_google_direct is None and self.llm_openai is None:
            avg = (sum(e.score for e in cv_ev) + sum(e.score for e in jd_ev)) / max(len(cv_ev) + len(jd_ev), 1)
            return {
                "rationale": f"This question targets '{target_skill or 'relevant skills'}' supported by CV/JD evidence.",
                "alignment_score": round(avg, 3),
                "target_skill_detected": target_skill,
                "cv_evidence": [e.__dict__ for e in cv_ev],
                "jd_evidence": [e.__dict__ for e in jd_ev],
                "hallucination_flags": [],
                "proposed_revision": ""
            }

        sys = (
            "Given a question and top CV/JD evidence, return JSON with: "
            "rationale, alignment_score (0..1), target_skill_detected, "
            "cv_evidence[{quote,score}], jd_evidence[{quote,score}], "
            "hallucination_flags[], proposed_revision. JSON only."
        )
        payload = {
            "question": q_text,
            "target_skill_hint": target_skill,
            "cv_top_evidence": [{"quote": e.quote, "score": e.score} for e in cv_ev],
            "jd_top_evidence": [{"quote": e.quote, "score": e.score} for e in jd_ev]
        }
        prompt = f"{sys}\nINPUT:\n{json.dumps(payload, ensure_ascii=False)}\nJSON:"

        try:
            raw = self._invoke(prompt)
            cleaned = re.sub(r"```json\s*|\s*```", "", raw).strip()
            data = json.loads(cleaned)
        except Exception as e:
            logger.error(f"Judge LLM failed; fallback heuristic XAI. Error: {e}")
            avg = (sum(ev.score for ev in cv_ev) + sum(ev.score for ev in jd_ev)) / max(len(cv_ev) + len(jd_ev), 1)
            return {
                "rationale": f"This question targets '{target_skill or 'relevant skills'}' based on overlap with JD and CV.",
                "alignment_score": round(avg, 3),
                "target_skill_detected": target_skill,
                "cv_evidence": [e.__dict__ for e in cv_ev],
                "jd_evidence": [e.__dict__ for e in jd_ev],
                "hallucination_flags": ["judge_llm_unavailable"],
                "proposed_revision": ""
            }

        def attach_spans(evs: List[Dict], full_text: str) -> List[Dict]:
            out = []
            for ev in evs or []:
                q = ev.get("quote", "")
                idx = full_text.find(q) if q else -1
                out.append({
                    "quote": q,
                    "start": idx,
                    "end": idx + len(q) if idx != -1 else -1,
                    "score": float(ev.get("score", 0.0))
                })
            return out

        return {
            "rationale": data.get("rationale", ""),
            "alignment_score": float(data.get("alignment_score", 0.0)),
            "target_skill_detected": data.get("target_skill_detected", target_skill),
            "cv_evidence": attach_spans(data.get("cv_evidence", []), cv_text),
            "jd_evidence": attach_spans(data.get("jd_evidence", []), jd_text),
            "hallucination_flags": data.get("hallucination_flags", []),
            "proposed_revision": data.get("proposed_revision", "")
        }

try:
    question_xai_judge = QuestionXAIJudge()
except Exception as e:
    logger.error(f"Failed to init QuestionXAIJudge: {e}")
    question_xai_judge = QuestionXAIJudge(model_name=os.getenv("XAI_MODEL", "gemini-1.5-pro"))