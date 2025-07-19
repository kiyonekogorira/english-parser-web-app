import pytest
from formatter import ResultFormatter

def test_format_simple_sentence():
    analyzed_data = {
        "original_text": "I love programming.",
        "sent_offset": 0,
        "subjects": [{"text": "I", "start": 0, "end": 1}],
        "verbs": [{"text": "love", "start": 2, "end": 6}],
        "noun_phrases": [{"text": "programming", "start": 7, "end": 18}],
        "verb_phrases": [],
        "prepositional_phrases": [],
        "tokens_info": []
    }
    formatter = ResultFormatter([analyzed_data])
    html = formatter.format_html_all()
    assert "<p>" in html
    assert "<span style=\"color:red; font-weight:bold;\">I</span>" in html
    assert "<span style=\"color:blue; font-weight:bold;\">love</span>" in html
    assert "[名詞句: <span style=\"background-color:#ADD8E6; border:1px solid #00CED1; border-radius:3px; padding:0 2px;\">programming</span>]" in html

def test_format_multiple_sentences():
    analyzed_data_1 = {
        "original_text": "Hello.",
        "sent_offset": 0,
        "subjects": [], "verbs": [], "noun_phrases": [], "verb_phrases": [], "prepositional_phrases": [], "tokens_info": []
    }
    analyzed_data_2 = {
        "original_text": "How are you?",
        "sent_offset": 7,
        "subjects": [], "verbs": [], "noun_phrases": [], "verb_phrases": [], "prepositional_phrases": [], "tokens_info": []
    }
    formatter = ResultFormatter([analyzed_data_1, analyzed_data_2])
    html = formatter.format_html_all()
    assert html.count("<p>") == 2
    assert "Hello." in html
    assert "How are you?" in html

def test_format_empty_data():
    formatter = ResultFormatter([])
    html = formatter.format_html_all()
    assert html == ""

def test_format_with_all_phrases():
    analyzed_data = {
        "original_text": "The quick brown fox jumps over the lazy dog.",
        "sent_offset": 0,
        "subjects": [{"text": "fox", "start": 16, "end": 19}],
        "verbs": [{"text": "jumps", "start": 20, "end": 25}],
        "noun_phrases": [
            {"text": "The quick brown fox", "start": 0, "end": 19},
            {"text": "the lazy dog", "start": 30, "end": 42}
        ],
        "verb_phrases": [
            {"text": "jumps over the lazy dog", "start": 20, "end": 42}
        ],
        "prepositional_phrases": [
            {"text": "over the lazy dog", "start": 26, "end": 42}
        ],
        "tokens_info": []
    }
    formatter = ResultFormatter([analyzed_data])
    html = formatter.format_html_all()
    assert "<span style=\"color:red; font-weight:bold;\">fox</span>" in html
    assert "<span style=\"color:blue; font-weight:bold;\">jumps</span>" in html
    assert "[名詞句: <span style=\"background-color:#ADD8E6; border:1px solid #00CED1; border-radius:3px; padding:0 2px;\">The quick brown fox</span>]" in html
    assert "(動詞句: <span style=\"background-color:#E0FFE0; border:1px solid #32CD32; border-radius:3px; padding:0 2px;\">jumps over the lazy dog</span>)" in html
    assert "{前置詞句: <span style=\"background-color:#FFFFE0; border:1px solid #FFD700; border-radius:3px; padding:0 2px;\">over the lazy dog</span>}" in html
