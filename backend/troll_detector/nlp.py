"""NLP utilities for claim breadth analysis and linguistic fingerprinting.

Uses TF-IDF (scikit-learn) for similarity and basic text statistics for
fingerprinting. No PyTorch required — runs comfortably on constrained hardware.
"""

import math
import re
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Shared vectorizer — fitted on patent claim corpus
_vectorizer: TfidfVectorizer | None = None
_corpus_matrix = None
_corpus_ids: list[str] = []


def fit_vectorizer(texts: list[str], ids: list[str]) -> None:
    """Fit the TF-IDF vectorizer on a corpus of patent claim texts."""
    global _vectorizer, _corpus_matrix, _corpus_ids
    if not texts:
        return
    _vectorizer = TfidfVectorizer(
        max_features=10000,
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )
    _corpus_matrix = _vectorizer.fit_transform(texts)
    _corpus_ids = ids


def semantic_similarity(query: str, top_n: int = 10) -> list[tuple[str, float]]:
    """Compare a query against the fitted corpus. Returns (id, score) pairs."""
    if _vectorizer is None or _corpus_matrix is None:
        return []
    query_vec = _vectorizer.transform([query])
    scores = cosine_similarity(query_vec, _corpus_matrix).flatten()
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_n]
    return [(_corpus_ids[i], float(s)) for i, s in ranked if s > 0.01]


def claim_breadth_score(claims_text: str) -> float:
    """Score how broad/vague patent claims are (0-100, higher = broader).

    Broad claims tend to have:
    - Fewer specific technical terms
    - More abstract/functional language
    - Shorter independent claims with less detail
    - Heavy use of words like "comprising", "method", "system", "apparatus"
    """
    if not claims_text or len(claims_text.strip()) < 20:
        return 50.0

    words = claims_text.lower().split()
    word_count = len(words)
    if word_count == 0:
        return 50.0

    # Broad/vague indicator words
    broad_words = {
        "comprising", "including", "method", "system", "apparatus", "device",
        "means", "configured", "adapted", "operable", "wherein", "thereof",
        "substantially", "generally", "approximately", "plurality",
        "at least one", "one or more",
    }
    broad_count = sum(1 for w in words if w in broad_words)
    broad_ratio = broad_count / word_count

    # Specific/technical indicator: numbers, units, chemical formulas, specific nouns
    specific_pattern = re.compile(r'\d+\.?\d*\s*(mm|cm|nm|hz|ghz|mhz|v|a|ohm|mol|mg|kg|°)')
    specific_count = len(specific_pattern.findall(claims_text.lower()))
    specific_ratio = specific_count / max(word_count / 100, 1)

    # Average sentence length (shorter independent claims = broader)
    sentences = [s.strip() for s in claims_text.split('.') if s.strip()]
    avg_sentence_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

    # Vocabulary richness (lower = more repetitive/template-like = broader)
    unique_ratio = len(set(words)) / word_count

    # Combine signals
    score = 50.0
    score += (broad_ratio - 0.05) * 300  # broad words push score up
    score -= specific_ratio * 20          # specifics push score down
    score -= (avg_sentence_len - 30) * 0.5  # longer sentences = more specific
    score -= (unique_ratio - 0.4) * 50    # richer vocab = more specific

    return max(0.0, min(100.0, score))


def linguistic_fingerprint_score(texts: list[str]) -> float:
    """Score likelihood that texts were AI-generated (0-100, higher = more likely AI).

    Looks for:
    - Low vocabulary diversity across documents
    - Uniform sentence length distribution
    - Repetitive structural patterns
    - Unusually consistent formality
    """
    if not texts or len(texts) < 2:
        return 50.0  # can't assess with single document

    all_text = " ".join(texts)
    words = all_text.lower().split()
    if len(words) < 50:
        return 50.0

    # 1. Vocabulary diversity across documents
    per_doc_vocab = [set(t.lower().split()) for t in texts if t.strip()]
    if len(per_doc_vocab) < 2:
        return 50.0

    # Jaccard similarity between consecutive docs — high = suspicious
    jaccard_scores = []
    for i in range(len(per_doc_vocab) - 1):
        a, b = per_doc_vocab[i], per_doc_vocab[i + 1]
        if a | b:
            jaccard_scores.append(len(a & b) / len(a | b))
    avg_jaccard = sum(jaccard_scores) / len(jaccard_scores) if jaccard_scores else 0.5

    # 2. Sentence length variance (AI tends toward uniform length)
    sentences = [s.strip() for s in all_text.split('.') if len(s.strip()) > 5]
    if len(sentences) > 2:
        lengths = [len(s.split()) for s in sentences]
        mean_len = sum(lengths) / len(lengths)
        variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
        cv = math.sqrt(variance) / mean_len if mean_len > 0 else 0
    else:
        cv = 0.3  # neutral

    # 3. Repeated n-gram patterns
    trigrams = [tuple(words[i:i+3]) for i in range(len(words) - 2)]
    trigram_counts = Counter(trigrams)
    repeated_trigrams = sum(1 for c in trigram_counts.values() if c > 2)
    repeat_ratio = repeated_trigrams / max(len(trigram_counts), 1)

    # Combine
    score = 50.0
    score += (avg_jaccard - 0.3) * 100   # high cross-doc similarity = AI
    score -= (cv - 0.3) * 80             # low sentence variance = AI (so subtract less)
    score += repeat_ratio * 150           # repetitive patterns = AI

    return max(0.0, min(100.0, score))
