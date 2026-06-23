from __future__ import annotations

import sys
from pathlib import Path

_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_CACHE_DIR = Path.home() / ".cache" / "specify" / "embeddings"
_DIMS = 384


class EmbeddingProvider:
    def embed(self, text: str) -> list[float] | None:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError


class FastEmbedProvider(EmbeddingProvider):
    _model = None

    def available(self) -> bool:
        try:
            import fastembed  # noqa: F401
            return True
        except ImportError:
            return False

    def embed(self, text: str) -> list[float] | None:
        if not self.available():
            return None
        if FastEmbedProvider._model is None:
            from fastembed import TextEmbedding
            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            FastEmbedProvider._model = TextEmbedding(
                model_name=_MODEL_NAME,
                cache_dir=str(_CACHE_DIR),
            )
        results = list(FastEmbedProvider._model.embed([text]))
        return results[0].tolist()


class NullProvider(EmbeddingProvider):
    def available(self) -> bool:
        return False

    def embed(self, text: str) -> list[float] | None:
        return None


def get_provider(warn: bool = True) -> EmbeddingProvider:
    p = FastEmbedProvider()
    if p.available():
        return p
    if warn:
        print(
            "specify: fastembed não disponível — busca vetorial desativada, usando substring.",
            file=sys.stderr,
        )
    return NullProvider()
