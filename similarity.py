import spacy
from typing import List, Tuple

# Load the spaCy model
nlp = spacy.load("en_core_web_md")

def extract_important_text(text: str) -> str:
    doc = nlp(text.lower())
    return " ".join(token.text for token in doc if token.pos_ in ["NOUN", "PROPN", "NUM"])

def extract_numbers(text: str) -> List[str]:
    doc = nlp(text.lower())
    return [token.text for token in doc if token.like_num]

def semantic_similarity(a: str, b: str) -> float:
    doc1 = nlp(extract_important_text(a))
    doc2 = nlp(extract_important_text(b))

    # Ensure both docs have valid vectors
    if not doc1.has_vector or not doc2.has_vector:
        return 0.0

    return doc1.similarity(doc2)

def penalize_mismatched_numbers(a: str, b: str, similarity: float) -> float:
    numbers_a = set(extract_numbers(a))
    numbers_b = set(extract_numbers(b))
    if numbers_a != numbers_b:
        similarity -= 0.3
    return max(0, similarity)

def score_similarity(a: str, b: str) -> float:
    similarity = semantic_similarity(a, b)
    return penalize_mismatched_numbers(a, b, similarity)

def detailed_similarity_report(a: str, b: str) -> Tuple[float, List[str], List[str]]:
    similarity = semantic_similarity(a, b)
    numbers_a = extract_numbers(a)
    numbers_b = extract_numbers(b)
    adjusted_similarity = penalize_mismatched_numbers(a, b, similarity)
    return adjusted_similarity, numbers_a, numbers_b
