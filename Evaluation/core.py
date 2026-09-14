#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core.py — Nhóm 7 / LLM Pháp lý
Cung cấp embeddings (Vietnamese-SBERT) và vectorstore (ChromaDB collection legal_docs).
"""

from __future__ import annotations

import os
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
import torch


def _find_chroma_path() -> Path:
    cur = Path(__file__).resolve().parent
    candidates = [
        cur / "data" / "chromadb",
        cur.parent / "data" / "chromadb",
        cur.parent.parent / "data" / "chromadb",
    ]
    for c in candidates:
        if c.exists():
            return c
    return cur.parent / "data" / "chromadb"


CHROMA_PATH = _find_chroma_path()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class EmbeddingsWrapper:
    def __init__(self, model_name: str = "keepitreal/vietnamese-sbert"):
        self.model_name = model_name
        self.device = DEVICE
        self._model = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    def encode(self, sentences, **kwargs):
        model = self._get_model()
        if "device" not in kwargs:
            kwargs["device"] = self.device
        return model.encode(sentences, **kwargs)


class VectorStoreWrapper:
    def __init__(self, chroma_path: Path | str = CHROMA_PATH):
        self.chroma_path = str(chroma_path)
        self._client = None
        self._collection = None

    def get_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self.chroma_path)
        return self._client

    def get_collection(self, name: str = "legal_docs"):
        if self._collection is None:
            client = self.get_client()
            self._collection = client.get_collection(name=name)
        return self._collection


embeddings = EmbeddingsWrapper()
vectorstore = VectorStoreWrapper()
