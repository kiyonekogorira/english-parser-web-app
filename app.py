import streamlit as st
import spacy

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
    def __init__(self, text, type, role="", children=None, tokens=None, start_token_index=None):
        self.text = text
        self.type = type # 例: "Sentence", "Main Clause", "Noun Phrase", "Word"
        self.role = role # 例: "Subject", "Predicate", "Location"
        self.children = children if children is not None else []
        self.tokens = tokens if tokens is not None else [] # 葉ノード（単語）用
        self.start_token_index = start_token_index if start_token_index is not None else (tokens[0].i if tokens else -1)

    def to_string(self, indent_level=0):
        indent = "  " * indent_level
        output = []
        header = f"{indent}- **{self.type}**"
        if self.role:
            header += f" ({self.role})"
        
        # 単語レベルの要素の場合はテキストと品詞を表示
        if self.type == "Word" and self.tokens:
            token_info = self.tokens[0]
            output.append(f"{header}: {self.text} ({token_info.pos_} / {token_info.tag_})")
        else:
            output.append(f"{header}: {self.text}")

        for child in self.children:
            output.append(child.to_string(indent_level + 1))
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
    return "名詞句"

def get_prepositional_phrase_role(prep_token):
    head = prep_token.head
    if head.pos_ == "VERB":
        if prep_token.text.lower() in ["in", "on", "at", "from", "to", "near"]: return "副詞的修飾 (場所)"
        if prep_token.text.lower() in ["after", "before", "during", "until", "since"]: return "副詞的修飾 (時)"
        if prep_token.text.lower() in ["with", "by"]: return "副詞的修飾 (手段/方法)"
        if prep_token.text.lower() in ["for", "about"]: return "副詞的修飾 (目的/対象)"
    elif head.pos_ in ["NOUN", "PROPN"]:
        return "形容詞的修飾 (名詞)"
    return "前置詞句"

def get_verb_phrase_role(verb_token):
    if verb_token.dep_ == "ROOT": return "述語 (主動詞)"
    if verb_token.dep_ == "xcomp": return "目的語補語 (不定詞/分詞)"
    if verb_token.dep_ == "ccomp": return "補文節 (名詞節)"
    if verb_token.dep_ == "advcl": return "副詞節"
    if verb_token.dep_ == "acl": return "形容詞節"
    return "述語"

def get_clause_role(clause_root_token):
    if clause_root_token.dep_ == "advcl":
        if clause_root_token.text.lower() in ["because", "since", "as"]: return "原因・理由"
        if clause_root_token.text.lower() in ["although", "though", "even though"]: return "譲歩"
        if clause_root_token.text.lower() in ["when", "while", "after", "before"]: return "時"
        if clause_root_token.text.lower() in ["if", "unless"]: return "条件"
        return "副詞節"
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
def build_syntax_tree(token, processed_indices):
    if token.i in processed_indices or token.pos_ == "PUNCT":
        processed_indices.add(token.i) # Ensure punctuation is marked processed
        return None

    element = None
    element_tokens = [] # Tokens belonging to the current element

    # 1. 従属節 (Subordinate Clauses) の検出を最優先
    # 関係代名詞節 (relcl) も含める
    if token.dep_ in ["advcl", "acl", "ccomp", "xcomp", "relcl"] or \
       (token.pos_ == "SCONJ" and token.dep_ == "mark") or \
       (token.pos_ == "PRON" and token.dep_ == "nsubj" and token.head.dep_ == "relcl"): # 関係代名詞
        
        element_tokens = get_subtree_tokens(token)
        element = SyntaxElement(get_span_text(element_tokens), "従属節", get_clause_role(token), start_token_index=token.i)
    
    # 2. 不定詞句 / 分詞構文 の検出 (動詞がルートの場合)
    elif token.pos_ == "VERB" or token.pos_ == "AUX":
        vp_type = "動詞句"
        vp_role = get_verb_phrase_role(token)
        
        is_infinitive = False
        to_token = None
        # Check for 'to' as a child with PART pos_ and specific dep_ for infinitive
        if (token.dep_ in ["xcomp", "ccomp", "advcl", "acl"]) and \
           any(child.text.lower() == "to" and child.pos_ == "PART" for child in token.children):
            is_infinitive = True
            to_token = next((child for child in token.children if child.text.lower() == "to" and child.pos_ == "PART"), None)

        if is_infinitive and to_token:
            vp_type = "不定詞句"
            # Get subtree of the verb, then add 'to' at the beginning if it's not already there
            verb_subtree_tokens = get_subtree_tokens(token)
            if to_token not in verb_subtree_tokens: # Ensure 'to' is included and at the start
                element_tokens = sorted([to_token] + verb_subtree_tokens, key=lambda t: t.i)
            else:
                element_tokens = verb_subtree_tokens # 'to' is already part of subtree
            
            element = SyntaxElement(get_span_text(element_tokens), vp_type, vp_role, start_token_index=element_tokens[0].i)

        elif (token.pos_ == "VERB" and (token.tag_ == "VBG" or token.tag_ == "VBN")) and \
             (token.dep_ in ["acl", "advcl"]):
            vp_type = "分詞構文"
            element_tokens = get_subtree_tokens(token)
            element = SyntaxElement(get_span_text(element_tokens), vp_type, vp_role, start_token_index=token.i)

        else: # General Verb Phrase
            element_tokens = get_subtree_tokens(token) # Use subtree for general VP
            element = SyntaxElement(get_span_text(element_tokens), vp_type, vp_role, start_token_index=token.i)

    # 3. 名詞句 (Noun Phrases) の検出
    # Check if the current token is the root of a noun chunk in its sentence
    elif token.pos_ in ["NOUN", "PROPN", "PRON"]:
        for chunk in token.sent.noun_chunks: # Iterate over noun chunks in the current sentence
            if token == chunk.root: # If the current token is the root of this chunk
                # Ensure all tokens in chunk are unprocessed before claiming it
                if all(t.i not in processed_indices for t in chunk):
                    element_tokens = list(chunk)
                    element = SyntaxElement(get_span_text(element_tokens), "名詞句", get_noun_phrase_role(chunk.root), start_token_index=chunk.start)
                break # Found the chunk, no need to check other chunks for this token

    # 4. 前置詞句 (Prepositional Phrases) の検出
    elif token.pos_ == "ADP" and token.dep_ == "prep":
        element_tokens = get_subtree_tokens(token)
        element = SyntaxElement(get_span_text(element_tokens), "前置詞句", get_prepositional_phrase_role(token), start_token_index=token.i)

    # 5. その他の単語 (Word) として処理
    if element is None: # If no larger element was identified
        element_tokens = [token]
        element = SyntaxElement(token.text, "Word", tokens=[token], start_token_index=token.i)

    # Now, if an element was created, mark its tokens as processed and build its children
    if element:
        for t in element_tokens:
            processed_indices.add(t.i) # Mark all tokens of this element as processed

        # Recursively build children from tokens within this element's span
        # This is the crucial part to avoid re-processing and infinite recursion
        # Iterate through the tokens that *belong* to this element's span
        for t in element_tokens:
            # Only process children that are not yet processed and are not punctuation
            # And ensure we don't try to process the current element's root token again as a child
            if t.i != token.i and t.i not in processed_indices and t.pos_ != "PUNCT":
                child_element = build_syntax_tree(t, processed_indices)
                if child_element:
                    element.children.append(child_element)
        
        # Sort children by their start index for consistent output
        element.children.sort(key=lambda x: x.start_token_index)
        
        return element
    
    return None

# --- メインの解析ロジック ---
def analyze_and_format_text(doc):
    parsed_elements = []

    for sent in doc.sents:
        sentence_element = SyntaxElement(sent.text, "文", "全体", start_token_index=sent.start)
        processed_indices = set()
        
        # Collect all top-level elements for this sentence
        top_level_elements = []
        
        # Iterate through tokens in the sentence
        for token in sent:
            if token.i not in processed_indices and token.pos_ != "PUNCT":
                # Try to build a syntax element from this token
                element = build_syntax_tree(token, processed_indices)
                if element:
                    top_level_elements.append(element)
        
        # Sort top-level elements by their start index to maintain original order
        top_level_elements.sort(key=lambda x: x.start_token_index)
        
        # Add them as children of the sentence element
        sentence_element.children.extend(top_level_elements)
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
                doc = nlp(user_input)
                parsed_data = analyze_and_format_text(doc)

                st.subheader("解析結果:")
                for element in parsed_data:
                    with st.expander(f"**{element.type}:** {element.text}", expanded=True):
                        st.markdown(element.to_string(indent_level=0))

        except Exception as e:
            st.error(
                f"解析中にエラーが発生しました。入力された英文を確認してください。エラー詳細: {e}"
            )