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

# --- ヘルパー関数 ---
def find_chunk(chunks, chunk_type, text):
    """特定のタイプのチャンクとテキストを持つチャンクを見つける"""
    for chunk in chunks:
        if chunk['type'] == chunk_type and chunk['text'] == text:
            return True
    print(f"Chunk not found: type={chunk_type}, text='{text}'")
    print(f"Available chunks of type {chunk_type}: {[c['text'] for c in chunks if c['type'] == chunk_type]}")
    return False

# --- 基本的な解析テスト ---

def test_analyze_text_returns_tokens_and_chunks(analyzer):
    text = "The cat sat on the mat."
    result = analyzer.analyze_text(text)
    assert len(result) == 1
    sentence_result = result[0]
    
    assert "tokens" in sentence_result and len(sentence_result["tokens"]) > 0
    first_token = sentence_result["tokens"][0]
    assert "id" in first_token and "text" in first_token and "pos" in first_token
    
    assert "chunks" in sentence_result and len(sentence_result["chunks"]) > 0
    # NP, PP, VPなどが含まれていることを確認
    chunk_types = {c['type'] for c in sentence_result["chunks"]}
    assert 'NP' in chunk_types
    assert 'PP' in chunk_types
    assert 'VP' in chunk_types

def test_analyze_empty_and_non_english_text(analyzer):
    assert analyzer.analyze_text("") == []
    assert analyzer.analyze_text("      ") == []
    assert analyzer.analyze_text("これはテストです。") == []
    assert analyzer.analyze_text("12345 !@#$%^&*()") == []

def test_analyze_multiple_sentences(analyzer):
    text = "Hello world. How are you?"
    result = analyzer.analyze_text(text)
    assert len(result) == 2
    assert result[0]["original_text"] == "Hello world."
    assert result[1]["original_text"] == "How are you?"

# --- 句抽出ロジックのテスト ---

def test_vp_extraction_with_auxiliaries_and_adverb(analyzer):
    text = "I will have been running quickly."
    chunks = analyzer.analyze_text(text)[0]['chunks']
    assert find_chunk(chunks, 'VP', 'will have been running quickly'), "VP with auxiliaries and adverb failed."

def test_vp_extraction_with_prep_phrase(analyzer):
    text = "He jumps over the lazy dog."
    chunks = analyzer.analyze_text(text)[0]['chunks']
    assert find_chunk(chunks, 'VP', 'jumps over the lazy dog'), "VP with prepositional phrase failed."

def test_advp_extraction_with_modifier(analyzer):
    text = "She works very hard."
    chunks = analyzer.analyze_text(text)[0]['chunks']
    assert find_chunk(chunks, 'ADVP', 'very hard'), "ADVP with modifier failed."

def test_pp_extraction_complex_nesting(analyzer):
    text = "The book on the table in the corner is mine."
    chunks = analyzer.analyze_text(text)[0]['chunks']
    # analyzer._remove_subsets により、'in the corner' は 'on the table in the corner' に包含されるため削除される
    assert find_chunk(chunks, 'PP', 'on the table in the corner'), "Largest PP not found."
    assert find_chunk(chunks, 'PP', 'in the corner'), "Subset PP was not removed."

def test_vp_with_direct_object(analyzer):
    text = "She is singing a song."
    chunks = analyzer.analyze_text(text)[0]['chunks']
    assert find_chunk(chunks, 'VP', 'is singing a song'), "VP with direct object failed."

def test_no_duplicate_chunks(analyzer):
    text = "I see a man who is tall and who is running."
    chunks = analyzer.analyze_text(text)[0]['chunks']
    
    unique_keys = set()
    for chunk in chunks:
        key = (chunk['type'], chunk['start_id'], chunk['end_id'])
        assert key not in unique_keys, f"Duplicate chunk found: {key}"
        unique_keys.add(key)

# --- ヘルパー関数のテスト ---

def test_get_pos_japanese(analyzer):
    assert analyzer.get_pos_japanese_from_pos_tag("NOUN") == "名詞"
    assert analyzer.get_pos_japanese_from_pos_tag("VERB") == "動詞"
    assert analyzer.get_pos_japanese_from_pos_tag("UNKNOWN") == "UNKNOWN"

def test_get_dep_japanese(analyzer):
    assert analyzer.get_dep_japanese("nsubj") == "名詞主語"
    assert analyzer.get_dep_japanese("dobj") == "直接目的語"
    assert analyzer.get_dep_japanese("UNKNOWN") == "UNKNOWN"
