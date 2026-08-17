"""Помощники колоды: ни базы, ни запросов — чистые преобразования."""

from apps.vocabulary.utils.cardref import PHRASE, WORD, to_id
from apps.vocabulary.utils.images import to_webp

__all__ = ["PHRASE", "WORD", "to_id", "to_webp"]
