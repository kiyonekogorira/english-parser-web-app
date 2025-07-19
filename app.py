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

# --- 構文要素を保持するデータ構造 --- (フェーズ1, ステップ3)
class SyntaxElement:
    def __init__(self, text, type, role="", children=None, tokens=None):
        self.text = text
        self.type = type # 例: "Sentence", "Main Clause", "Noun Phrase", "Word"
        self.role = role # 例: "Subject", "Predicate", "Location"
        self.children = children if children is not None else []
        self.tokens = tokens if tokens is not None else [] # 葉ノード（単語）用

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

# --- 解析ロジック --- (フェーズ1, ステップ3)
def analyze_and_format_text(doc):
    parsed_elements = []

    for sent in doc.sents:
        # 節の特定 (簡易版: 各文を節として扱う)
        clause_type = "主節"
        clause_role = ""

        # 簡易的な従属節の識別
        if sent[0].pos_ == "SCONJ" or sent[0].dep_ == "mark":
            clause_type = "従属節"
            if sent[0].text.lower() in ["because", "since", "as"]:
                clause_role = "原因・理由"
            elif sent[0].text.lower() in ["although", "though", "even though"]:
                clause_role = "譲歩"
            elif sent[0].text.lower() in ["when", "while", "after", "before"]:
                clause_role = "時"
            elif sent[0].text.lower() in ["if", "unless"]:
                clause_role = "条件"
            elif sent[0].text.lower() in ["who", "which", "that"]:
                clause_role = "修飾 (形容詞節)"
            elif sent[0].text.lower() in ["what", "where", "how"]:
                clause_role = "名詞節"
        
        clause_element = SyntaxElement(sent.text, clause_type, clause_role)

        # 句の特定と役割の付与
        processed_tokens = set()

        # 1. 名詞句の処理
        for chunk in sent.noun_chunks:
            role = ""
            if chunk.root.dep_ == "nsubj": role = "主語"
            elif chunk.root.dep_ == "dobj": role = "直接目的語"
            elif chunk.root.dep_ == "pobj": role = "前置詞の目的語"
            elif chunk.root.dep_ == "attr": role = "補語"
            elif chunk.root.dep_ == "oprd": role = "目的語補語"
            
            np_element = SyntaxElement(chunk.text, "名詞句", role)
            for token in chunk:
                np_element.children.append(SyntaxElement(token.text, "Word", tokens=[token]))
                processed_tokens.add(token.i)
            clause_element.children.append(np_element)

        # 2. 動詞句の処理 (簡易版)
        # 文のルート動詞を探し、その動詞と直接の子孫の一部を動詞句とする
        verbs = [token for token in sent if token.pos_ == "VERB" or token.pos_ == "AUX"]
        for verb in verbs:
            if verb.i not in processed_tokens: # 既に名詞句の一部として処理されていないか確認
                vp_tokens = [verb] + [child for child in verb.children if child.pos_ != "PUNCT" and child.i not in processed_tokens]
                vp_text = " ".join([t.text for t in sorted(vp_tokens, key=lambda t: t.i)])
                
                vp_element = SyntaxElement(vp_text, "動詞句", "述語")
                for token in sorted(vp_tokens, key=lambda t: t.i):
                    if token.i not in processed_tokens: # 重複を避ける
                        vp_element.children.append(SyntaxElement(token.text, "Word", tokens=[token]))
                        processed_tokens.add(token.i)
                clause_element.children.append(vp_element)

        # 3. 前置詞句の処理
        preps = [token for token in sent if token.pos_ == "ADP" and token.dep_ == "prep"]
        for prep in preps:
            if prep.i not in processed_tokens: # 既に処理されていないか確認
                pp_tokens = [prep] + [child for child in prep.children if child.dep_ == "pobj" and child.i not in processed_tokens]
                pp_text = " ".join([t.text for t in sorted(pp_tokens, key=lambda t: t.i)])
                
                pp_role = "修飾語"
                if prep.head.pos_ == "VERB":
                    if prep.text.lower() in ["in", "on", "at", "from", "to"]: pp_role = "副詞的修飾 (場所)"
                    elif prep.text.lower() in ["after", "before", "during"]: pp_role = "副詞的修飾 (時)"
                elif prep.head.pos_ in ["NOUN", "PROPN"]: pp_role = "形容詞的修飾"

                pp_element = SyntaxElement(pp_text, "前置詞句", pp_role)
                for token in sorted(pp_tokens, key=lambda t: t.i):
                    if token.i not in processed_tokens: # 重複を避ける
                        pp_element.children.append(SyntaxElement(token.text, "Word", tokens=[token]))
                        processed_tokens.add(token.i)
                clause_element.children.append(pp_element)

        # 4. その他の未処理の単語 (接続詞、副詞など) を追加
        for token in sent:
            if token.i not in processed_tokens and token.pos_ != "PUNCT": # 句読点は除外
                clause_element.children.append(SyntaxElement(token.text, "Word", tokens=[token]))

        parsed_elements.append(clause_element)

    return parsed_elements

# --- UI構築 ---
st.title("英文構造解析アプリ")

st.write("解析したい英文を下のテキストボックスに入力してください。")

# --- 入力エリア ---
user_input = st.text_area(
    "英文を入力",
    "",
    height=150,
    placeholder="例: The quick brown fox jumps over the lazy dog."
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
                # UI/UXの改善 (MVPレベル) - st.expanderと階層表示
                for element in parsed_data:
                    with st.expander(f"**{element.type} ({element.role}):** {element.text}", expanded=True): # 初期は展開
                        st.markdown(element.to_string(indent_level=0)) # to_string内でインデントを処理

        except Exception as e:
            st.error(
                f"解析中にエラーが発生しました。入力された英文を確認してください。エラー詳細: {e}"
            )