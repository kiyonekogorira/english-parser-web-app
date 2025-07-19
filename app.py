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
def get_span_text(span):
    return span.text

def get_subtree_tokens(token):
    return sorted([t for t in token.subtree], key=lambda t: t.i)

# --- 依存ツリーを再帰的に走査し、構文要素を構築する関数 ---
def build_syntax_tree(token, processed_indices):
    if token.i in processed_indices or token.pos_ == "PUNCT":
        processed_indices.add(token.i)
        return None

    # 1. 従属節 (Subordinate Clauses) の検出を最優先
    if token.dep_ in ["advcl", "acl", "ccomp", "xcomp", "relcl"] or \
       (token.pos_ == "SCONJ" and token.dep_ == "mark") or \
       (token.pos_ == "PRON" and token.dep_ == "nsubj" and token.head.dep_ == "relcl"): # 関係代名詞
        
        clause_tokens = get_subtree_tokens(token)
        clause_text = " ".join([t.text for t in clause_tokens])
        
        clause_type = "従属節"
        clause_role = get_clause_role(token)

        clause_element = SyntaxElement(clause_text, clause_type, clause_role, start_token_index=token.i)
        
        for child in token.children:
            child_element = build_syntax_tree(child, processed_indices)
            if child_element:
                clause_element.children.append(child_element)
        
        for t in clause_tokens:
            processed_indices.add(t.i)
        return clause_element

    # 2. 不定詞句 / 分詞構文 の検出 (動詞がルートの場合)
    if token.pos_ == "VERB" or token.pos_ == "AUX":
        vp_type = "動詞句"
        vp_role = get_verb_phrase_role(token)
        
        is_infinitive = False
        to_token = None
        if (token.dep_ in ["xcomp", "ccomp"]) and \
           any(child.text.lower() == "to" and child.pos_ == "PART" for child in token.children):
            is_infinitive = True
            to_token = next((child for child in token.children if child.text.lower() == "to" and child.pos_ == "PART"), None)

        if is_infinitive and to_token:
            vp_type = "不定詞句"
            infinitive_tokens = get_subtree_tokens(token) # 動詞のsubtree
            infinitive_tokens.insert(0, to_token) # 'to' を先頭に追加
            infinitive_tokens = sorted(list(set(infinitive_tokens)), key=lambda t: t.i) # 重複削除とソート
            
            infinitive_text = " ".join([t.text for t in infinitive_tokens])
            vp_element = SyntaxElement(infinitive_text, vp_type, vp_role, start_token_index=to_token.i)
            
            for t in infinitive_tokens:
                if t.i not in processed_indices:
                    child_element = build_syntax_tree(t, processed_indices)
                    if child_element:
                        vp_element.children.append(child_element)
            
            for t in infinitive_tokens: processed_indices.add(t.i)
            return vp_element

        if (token.pos_ == "VERB" and (token.tag_ == "VBG" or token.tag_ == "VBN")) and \
           (token.dep_ in ["acl", "advcl"]):
            vp_type = "分詞構文"
            participle_tokens = get_subtree_tokens(token)
            participle_text = " ".join([t.text for t in participle_tokens])
            vp_element = SyntaxElement(participle_text, vp_type, vp_role, start_token_index=token.i)
            
            for t in participle_tokens:
                if t.i not in processed_indices:
                    child_element = build_syntax_tree(t, processed_indices)
                    if child_element:
                        vp_element.children.append(child_element)
            
            for t in participle_tokens: processed_indices.add(t.i)
            return vp_element

        # 一般的な動詞句
        vp_tokens = [token]
        for child in token.children:
            if child.i not in processed_indices and child.pos_ != "PUNCT":
                vp_tokens.append(child)
        
        vp_tokens = sorted(vp_tokens, key=lambda t: t.i)
        vp_text = " ".join([t.text for t in vp_tokens])
        
        vp_element = SyntaxElement(vp_text, vp_type, vp_role, start_token_index=token.i)
        for t in vp_tokens:
            if t.i not in processed_indices:
                child_element = build_syntax_tree(t, processed_indices)
                if child_element:
                    vp_element.children.append(child_element)
        
        for t in vp_tokens: processed_indices.add(t.i)
        return vp_element

    # 3. 名詞句 (Noun Phrases) の検出
    # Check if the current token is the root of a noun chunk in its sentence
    current_token_is_np_root = False
    for chunk in token.sent.noun_chunks: # Iterate over noun chunks in the current sentence
        if token == chunk.root: # If the current token is the root of this chunk
            current_token_is_np_root = True
            if all(t.i not in processed_indices for t in chunk): # Ensure all tokens in chunk are unprocessed
                np_element = SyntaxElement(chunk.text, "名詞句", get_noun_phrase_role(chunk.root), tokens=list(chunk), start_token_index=chunk.start)
                for t in chunk:
                    processed_indices.add(t.i)
                return np_element
            break # Found the chunk, no need to check other chunks for this token

    if current_token_is_np_root: # If it was an NP root but already processed or not fully unprocessed
        return None # Or handle appropriately, maybe it's part of a larger processed element

    # 4. 前置詞句 (Prepositional Phrases) の検出
    if token.pos_ == "ADP" and token.dep_ == "prep":
        pp_tokens = get_subtree_tokens(token)
        pp_text = " ".join([t.text for t in pp_tokens])
        
        pp_element = SyntaxElement(pp_text, "前置詞句", get_prepositional_phrase_role(token), start_token_index=token.i)
        for t in pp_tokens:
            if t.i not in processed_indices:
                child_element = build_syntax_tree(t, processed_indices)
                if child_element:
                    pp_element.children.append(child_element)
        
        for t in pp_tokens: processed_indices.add(t.i)
        return pp_element

    # 5. その他の単語 (Word) として処理
    if token.i not in processed_indices:
        processed_indices.add(token.i)
        return SyntaxElement(token.text, "Word", tokens=[token], start_token_index=token.i)
    
    return None

# --- メインの解析ロジック ---
def analyze_and_format_text(doc):
    parsed_elements = []

    for sent in doc.sents:
        sentence_element = SyntaxElement(sent.text, "文", "全体", start_token_index=sent.start)
        processed_indices = set()
        
        # 文のルートから構文ツリーを構築
        main_clause_root_element = build_syntax_tree(sent.root, processed_indices)
        
        if main_clause_root_element:
            # 主節のテキストは文全体とするか、より正確に特定するかは要検討
            main_clause_element = SyntaxElement(sent.text, "主節", "文の核", start_token_index=sent.start)
            main_clause_element.children.append(main_clause_root_element)
            sentence_element.children.append(main_clause_element)

        # 文中の残りのトークンを処理し、未処理の要素（主に独立した従属節など）を追加
        for token in sent:
            if token.i not in processed_indices:
                element = build_syntax_tree(token, processed_indices)
                if element:
                    # 従属節は直接 sentence_element の子として追加
                    if element.type == "従属節":
                        sentence_element.children.append(element)
                    else:
                        # それ以外の要素は主節の子として追加 (主節が構築されている場合)
                        if main_clause_element:
                            main_clause_element.children.append(element)
                        else:
                            # 主節が構築されていない場合は文の直接の子として追加
                            sentence_element.children.append(element)
        
        # 最終的な要素の順序を調整 (元の文の順序に近づける)
        # sentence_elementの直接の子要素をソート
        sentence_element.children.sort(key=lambda x: x.start_token_index)
        
        # main_clause_elementの直接の子要素もソート (存在する場合)
        if main_clause_element and main_clause_element.children:
            main_clause_element.children.sort(key=lambda x: x.start_token_index)

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
