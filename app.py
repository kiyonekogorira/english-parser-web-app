import streamlit as st
import spacy
from analyzer import SentenceAnalyzer

# --- Streamlitページ設定 ---
st.set_page_config(
    page_title="英文構造解析アプリ",
    layout="centered", # または "wide"
    initial_sidebar_state="auto"
)

# --- spaCyモデルのロード ---
@st.cache_resource
def load_model():
    try:
        nlp = spacy.load("en_core_web_sm")
        return nlp
    except OSError:
        st.error("spaCyモデル 'en_core_web_sm' が見つかりません。")
        st.info("コマンドラインで 'python -m spacy download en_core_web_sm' を実行してインストールしてください。")
        st.stop()

nlp = load_model()

# --- 構文要素を保持するデータ構造 ---
class SyntaxElement:
    def __init__(self, text, type, role="", children=None, tokens=None, start_token_index=None, start_char=None, end_char=None, pos_tagged_text=""):
        self.text = text
        self.type = type # 例: "Sentence", "Main Clause", "Noun Phrase", "Word"
        self.role = role # 例: "Subject", "Predicate", "Location"
        self.children = children if children is not None else []
        self.tokens = tokens if tokens is not None else [] # 葉ノード（単語）用
        self.start_token_index = start_token_index if start_token_index is not None else (tokens[0].i if tokens else -1)
        self.start_char = start_char if start_char is not None else (tokens[0].idx if tokens else -1)
        self.end_char = end_char if end_char is not None else (tokens[-1].idx + len(tokens[-1].text) if tokens else -1)
        self.pos_tagged_text = pos_tagged_text

    def to_string(self, indent_level=0, analyzer=None):
        indent = "  " * indent_level
        output = []

        # 句や節のヘッダー表示
        header = f"{indent}{self.type}"
        if self.role:
            header += f" ({self.role})"
        if self.text:
             header += f": {self.text}"
        output.append(header)

        # 子要素（単語や他の句）をインデントして表示
        if self.tokens and not self.children:
            for token in self.tokens:
                if token.pos_ != "PUNCT":
                    pos_japanese = analyzer.pos_map.get(token.pos_, token.pos_)
                    output.append(f"{indent}  {token.text}: {pos_japanese}")
        else:
            for child in self.children:
                output.append(child.to_string(indent_level + 1, analyzer))

        return "\n".join(output)

# --- 役割推定の補助関数 ---
def get_noun_phrase_role(root_token):
    if root_token.dep_ == "nsubj": return "主語"
    if root_token.dep_ == "dobj": return "直接目的語"
    if root_token.dep_ == "pobj": return "前置詞の目的語"
    if root_token.dep_ == "attr": return "補語"
    if root_token.dep_ == "oprd": return "目的語補語"
    if root_token.dep_ == "appos": return "同格"
    if root_token.dep_ == "npadvmod": return "副詞的修飾 (名詞句)"
    if root_token.dep_ == "iobj": return "間接目的語"
    return "名詞句"

def get_prepositional_phrase_role(prep_token):
    head = prep_token.head
    if head.pos_ == "VERB":
        if prep_token.text.lower() in ["in", "on", "at", "from", "to", "near"]: return "副詞的修飾 (場所)"
        if prep_token.text.lower() in ["after", "before", "during", "until", "since", "while"]: return "副詞的修飾 (時)"
        if prep_token.text.lower() in ["with", "by"]: return "副詞的修飾 (手段/方法)"
        if prep_token.text.lower() in ["for", "about"]: return "副詞的修飾 (目的/対象)"
        if prep_token.text.lower() in ["because of", "due to"]: return "副詞的修飾 (原因)"
    elif head.pos_ in ["NOUN", "PROPN"]:
        return "形容詞的修飾 (名詞)"
    return "前置詞句"

def get_verb_phrase_role(verb_token):
    if verb_token.dep_ == "ROOT":
        if verb_token.lemma_ in ["be", "seem", "become", "appear", "feel", "look", "sound", "taste", "smell", "grow", "remain", "stay", "turn"]: 
            return "述語 (連結動詞)"
        return "述語 (主動詞)"
    if verb_token.dep_ == "xcomp": return "述語 (開補文)"
    if verb_token.dep_ == "ccomp": return "述語 (補文)"
    if verb_token.dep_ == "conj": return "述語 (並列)"
    if verb_token.dep_ == "aux" or verb_token.dep_ == "auxpass": return "助動詞"
    return "述語"

def get_clause_role(clause_root_token):
    # Find the conjunction (marker) if it exists
    marker_token = None
    for child in clause_root_token.children:
        if child.dep_ == "mark":
            marker_token = child
            break
    # If not found as a child, check if the clause_root_token itself is a conjunction
    if not marker_token and clause_root_token.pos_ == "SCONJ":
        marker_token = clause_root_token

    marker_text = marker_token.text.lower() if marker_token else ""

    if clause_root_token.dep_ == "advcl":
        if marker_text in ["because", "since", "as"]: return "副詞節 (原因・理由)"
        if marker_text in ["although", "though", "even though"]: return "副詞節 (譲歩)"
        if marker_text in ["when", "while", "after", "before", "until", "as soon as"]: return "副詞節 (時)"
        if marker_text in ["if", "unless", "provided that"]: return "副詞節 (条件)"
        if marker_text in ["so that", "in order that"]: return "副詞節 (目的)"
        if marker_text in ["where", "wherever"]: return "副詞節 (場所)"
        if marker_text in ["as if", "as though"]: return "副詞節 (様態)"
        return "副詞節" # Default for advcl
    if clause_root_token.dep_ == "acl" or clause_root_token.dep_ == "relcl": return "形容詞節"
    if clause_root_token.dep_ == "ccomp": return "名詞節 (補文)"
    if clause_root_token.dep_ == "xcomp": return "名詞節 (開補文)"
    return "節"

# --- ヘルパー関数 ---
def get_span_text(tokens):
    if not tokens: return ""
    # spaCyのSpanオブジェクトのようにテキストを結合
    return tokens[0].doc.text[tokens[0].idx : tokens[-1].idx + len(tokens[-1].text)]

def get_subtree_tokens(token):
    return sorted([t for t in token.subtree], key=lambda t: t.i)

# --- 依存ツリーを再帰的に走査し、構文要素を構築する関数 ---
def build_syntax_tree(token, processed_indices, analyzer):
    if token.i in processed_indices or token.pos_ == "PUNCT":
        processed_indices.add(token.i) # Ensure punctuation is marked processed
        return None

    element = None
    element_tokens = [] # Tokens belonging to the current element

    # 1. 従属節 (Subordinate Clauses) の検出を最優先
    if token.dep_ in ["advcl", "acl", "ccomp", "xcomp", "relcl"] or \
       (token.pos_ == "SCONJ" and token.dep_ == "mark") or \
       (token.pos_ == "PRON" and token.dep_ == "nsubj" and token.head.dep_ == "relcl"): # 関係代名詞
        
        element_tokens = get_subtree_tokens(token)
        element = SyntaxElement(get_span_text(element_tokens), "従属節", get_clause_role(token), tokens=element_tokens, start_token_index=token.i, start_char=element_tokens[0].idx, end_char=element_tokens[-1].idx + len(element_tokens[-1].text))
    
    # 2. 句の検出 (名詞句、前置詞句など)
    elif token.pos_ in ["NOUN", "PROPN", "PRON"]:
        for chunk in token.sent.noun_chunks:
            if token == chunk.root and all(t.i not in processed_indices for t in chunk):
                element_tokens = list(chunk)
                element = SyntaxElement(get_span_text(element_tokens), "名詞句", get_noun_phrase_role(chunk.root), tokens=element_tokens, start_token_index=chunk.start, start_char=element_tokens[0].idx, end_char=element_tokens[-1].idx + len(element_tokens[-1].text))
                break
    elif token.pos_ == "ADP" and token.dep_ == "prep":
        element_tokens = get_subtree_tokens(token)
        element = SyntaxElement(get_span_text(element_tokens), "前置詞句", get_prepositional_phrase_role(token), tokens=element_tokens, start_token_index=token.i, start_char=element_tokens[0].idx, end_char=element_tokens[-1].idx + len(element_tokens[-1].text))

    # 3. 動詞 (句) の検出
    elif token.pos_ == "VERB" or token.pos_ == "AUX":
        element_tokens = [token]
        element = SyntaxElement(token.text, "動詞", get_verb_phrase_role(token), tokens=element_tokens, start_token_index=token.i, start_char=token.idx, end_char=token.idx + len(token.text))

    # 4. その他の単語
    if element is None:
        element_tokens = [token]
        pos_japanese = analyzer.pos_map.get(token.pos_, token.pos_)
        element = SyntaxElement(token.text, pos_japanese, "", tokens=element_tokens, start_token_index=token.i, start_char=token.idx, end_char=token.idx + len(token.text))

    # トークンを処理済みとしてマーク
    for t in element_tokens:
        processed_indices.add(t.i)

    return element

# --- メインの解析ロジック ---
def analyze_and_format_text(doc, analyzer):
    parsed_elements = []
    analyzed_sentences = analyzer.analyze_text(doc.text)

    for i, sent in enumerate(doc.sents):
        sentence_element = SyntaxElement(sent.text, "文章全体", "", start_token_index=sent.start, start_char=sent.start_char, end_char=sent.end_char, pos_tagged_text=analyzed_sentences[i]["pos_tagged_text"])
        
        processed_indices = set()
        
        # 文のトークンを順番に処理
        tokens_in_sentence = sorted([t for t in sent], key=lambda t: t.i)
        
        while len(processed_indices) < len(tokens_in_sentence):
            # 未処理のトークンを取得
            unprocessed_tokens = [t for t in tokens_in_sentence if t.i not in processed_indices]
            if not unprocessed_tokens:
                break
            
            # 次の未処理トークンから構文ツリーを構築
            token = unprocessed_tokens[0]
            element = build_syntax_tree(token, processed_indices, analyzer)
            if element:
                sentence_element.children.append(element)

        # 最終的な要素の順序を調整
        sentence_element.children.sort(key=lambda x: x.start_token_index)
        parsed_elements.append(sentence_element)

    return parsed_elements

# --- UI構築 ---
st.title("英文構造解析アプリ")

st.write("解析したい英文を下のテキストボックスに入力してください。")

# --- 入力エリア ---
user_input = st.text_area(
    "英文を入力",
    "",
    height=150,
    placeholder="例: The quick brown fox jumps over the lazy dog. Having finished his work, he went home. She wants to learn English."
)

# --- 解析実行ボタン ---
if st.button("解析実行"):
    if not user_input.strip():
        st.warning("英文を入力してください。")
    else:
        try:
            with st.spinner("解析中..."):
                analyzer = SentenceAnalyzer(nlp)
                doc = nlp(user_input)
                parsed_data = analyze_and_format_text(doc, analyzer)

                st.subheader("解析結果:")
                
                for element in parsed_data:
                    with st.expander(f"**{element.type}:** {element.text}", expanded=True):
                        st.markdown(f"**品詞分解:** {element.pos_tagged_text}")
                        st.markdown(f"```\n{element.to_string(indent_level=0, analyzer=analyzer)}\n```")

        except Exception as e:
            st.error(
                f"解析中にエラーが発生しました。入力された英文を確認してください。エラー詳細: {e}"
            )