"""
Satu-satunya tempat SentenceTransformer di-load di seluruh sistem.

Kenapa file ini perlu ada:
Sebelumnya, retriever.py DAN strict_grounding.py masing-masing
load model "paraphrase-multilingual-mpnet-base-v2" secara terpisah.
Akibatnya model besar yang SAMA ada 2 copy di memori RAM sekaligus,
yang di laptop dengan RAM terbatas bisa bikin Windows kehabisan
paging file dan proses server crash (OSError: paging file too small).

Solusinya: satu model, satu instance, dipakai bareng-bareng oleh
retriever.py dan strict_grounding.py lewat fungsi get_embedding_model().
"""
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
_model = None  # lazy-load, cuma di-load sekali untuk SELURUH aplikasi


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model