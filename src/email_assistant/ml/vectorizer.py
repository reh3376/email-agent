from __future__ import annotations
import re, json, math, hashlib
from typing import Dict, List, Iterable
from collections import defaultdict

TOKEN_RE = re.compile(r"[A-Za-z0-9_@.\-/]+")

def tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]

class HashingVectorizer:
    """
    Deterministic hashing vectorizer (MD5), with bucket-level DF/IDF.
    """
    def __init__(self, n_features: int = 2**18, use_idf: bool = True):
        self.n_features = n_features
        self.use_idf = use_idf
        self.df = [0] * n_features
        self.n_docs = 0
        self.fitted = False

    def _index(self, token: str) -> int:
        return int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.n_features

    def fit(self, docs: Iterable[str]) -> "HashingVectorizer":
        for doc in docs:
            self.n_docs += 1
            seen = set()
            for tok in set(tokenize(doc)):
                idx = self._index(tok)
                if idx not in seen:
                    self.df[idx] += 1
                    seen.add(idx)
        self.fitted = True
        return self

    def transform(self, docs: Iterable[str]) -> List[List[float]]:
        X: List[List[float]] = []
        idf = None
        if self.use_idf and self.fitted and self.n_docs > 0:
            idf = [math.log((1 + self.n_docs) / (1 + d)) + 1.0 for d in self.df]
        for doc in docs:
            vec = [0.0] * self.n_features
            tokens = tokenize(doc)
            if not tokens:
                X.append(vec); continue
            tf = defaultdict(int)
            for t in tokens:
                tf[self._index(t)] += 1
            max_tf = max(tf.values()) if tf else 1
            for idx, count in tf.items():
                val = count / max_tf
                if idf is not None:
                    val *= idf[idx]
                vec[idx] = val
            X.append(vec)
        return X

    def save(self) -> Dict:
        return {"n_features": self.n_features, "use_idf": self.use_idf, "df": self.df, "n_docs": self.n_docs}

    @classmethod
    def load(cls, obj: Dict) -> "HashingVectorizer":
        hv = cls(n_features=obj.get("n_features", 2**18), use_idf=obj.get("use_idf", True))
        hv.df = obj.get("df", [0]*hv.n_features)
        hv.n_docs = obj.get("n_docs", 0)
        hv.fitted = True
        return hv
