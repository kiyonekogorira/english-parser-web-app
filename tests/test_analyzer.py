import pytest
import spacy
from analyzer import SentenceAnalyzer

# spaCyモデルをテスト用にロード
@pytest.fixture(scope="module")
def nlp_model():
    return spacy.load("en_core_web_sm")

@pytest.fixture(scope="module")
def analyzer(nlp_model):
    return SentenceAnalyzer(nlp_model)

def test_analyze_simple_sentence(analyzer):
    text = "I love programming."
    result = analyzer.analyze_text(text)
    assert len(result) == 1
    assert result[0]["original_text"] == "I love programming."
    assert {"text": "I", "start": 0, "end": 1} in result[0]["subjects"]
    assert {"text": "love", "start": 2, "end": 6} in result[0]["verbs"]
    assert {"text": "programming", "start": 7, "end": 18} in result[0]["noun_phrases"]

def test_analyze_multiple_sentences(analyzer):
    text = "Hello. How are you? I am fine."
    result = analyzer.analyze_text(text)
    assert len(result) == 3
    assert result[0]["original_text"] == "Hello."
    assert result[1]["original_text"] == "How are you?"
    assert result[2]["original_text"] == "I am fine."

def test_analyze_empty_text(analyzer):
    text = ""
    result = analyzer.analyze_text(text)
    assert len(result) == 0

def test_analyze_text_with_japanese_labels(analyzer):
    text = "テストケース: This is a test. 1. Another test."
    result = analyzer.analyze_text(text)
    assert len(result) == 2
    assert result[0]["original_text"] == "This is a test."
    assert result[1]["original_text"] == "Another test."

def test_analyze_verb_phrase(analyzer):
    text = "She is singing a song."
    result = analyzer.analyze_text(text)
    assert len(result) == 1
    vp_found = False
    for vp in result[0]["verb_phrases"]:
        if "singing a song" in vp["text"]:
            vp_found = True
            break
    assert vp_found

def test_analyze_prepositional_phrase(analyzer):
    text = "He is in the room."
    result = analyzer.analyze_text(text)
    assert len(result) == 1
    pp_found = False
    for pp in result[0]["prepositional_phrases"]:
        if "in the room" in pp["text"]:
            pp_found = True
            break
    assert pp_found
