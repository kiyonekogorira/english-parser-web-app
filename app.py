import streamlit as st
import spacy

# spaCyモデルのロード
# アプリケーション起動時に一度だけロードするためにst.cache_resourceを使用
@st.cache_resource
def load_model():
    return spacy.load("en_core_web_sm")

nlp = load_model()

class SentenceAnalyzer:
    def __init__(self, text):
        self.text = text
        self.doc = nlp(text)

    def analyze(self):
        subjects = []
        verbs = []
        noun_phrases = []
        verb_phrases = []
        prepositional_phrases = []

        for token in self.doc:
            # 主語の特定
            if "nsubj" in token.dep_:
                subjects.append({"text": token.text, "start": token.idx, "end": token.idx + len(token.text)})
            # 動詞の特定 (助動詞も含む)
            if token.pos_ == "VERB" or token.pos_ == "AUX":
                verbs.append({"text": token.text, "start": token.idx, "end": token.idx + len(token.text)})

        # 名詞句の特定
        for chunk in self.doc.noun_chunks:
            noun_phrases.append({"text": chunk.text, "start": chunk.start_char, "end": chunk.end_char})

        # 動詞句と前置詞句の特定 (簡易版)
        # より正確な句の特定には、より複雑なロジックや句構造解析が必要
        for token in self.doc:
            # 動詞句 (簡易版: 動詞とその直接の子孫の一部)
            if token.pos_ == "VERB":
                # 動詞とその直接の子孫をまとめる
                # これは完全な動詞句ではないが、視覚化の出発点として
                vp_tokens = [token] + list(token.children)
                # トークンのインデックスに基づいてソートし、連続するスパンを形成
                vp_tokens.sort(key=lambda t: t.idx)
                if vp_tokens:
                    start_char = vp_tokens[0].idx
                    end_char = vp_tokens[-1].idx + len(vp_tokens[-1].text)
                    verb_phrases.append({"text": self.doc.text[start_char:end_char], "start": start_char, "end": end_char})

            # 前置詞句 (簡易版: 前置詞とその目的語)
            if token.pos_ == "ADP": # Adposition (前置詞または後置詞)
                for child in token.children:
                    if child.dep_ == "pobj": # object of preposition
                        pp_tokens = [token, child]
                        pp_tokens.sort(key=lambda t: t.idx)
                        if pp_tokens:
                            start_char = pp_tokens[0].idx
                            end_char = pp_tokens[-1].idx + len(pp_tokens[-1].text)
                            prepositional_phrases.append({"text": self.doc.text[start_char:end_char], "start": start_char, "end": end_char})


        return {
            "original_text": self.text,
            "subjects": subjects,
            "verbs": verbs,
            "noun_phrases": noun_phrases,
            "verb_phrases": verb_phrases,
            "prepositional_phrases": prepositional_phrases,
            # デバッグ用にトークン情報も残しておく
            "tokens_info": [{"text": token.text, "pos": token.pos_, "dep": token.dep_, "head": token.head.text} for token in self.doc]
        }

class ResultFormatter:
    def __init__(self, analyzed_data):
        self.analyzed_data = analyzed_data
        self.original_text = analyzed_data["original_text"]

    def format_html(self):
        text_len = len(self.original_text)
        # Store (tag_string, is_opening_tag) at each position
        # is_opening_tag = True for opening tags, False for closing tags
        events_at_pos = [[] for _ in range(text_len + 1)]

        # Define styles
        subject_style = "color:red; font-weight:bold;"
        verb_style = "color:blue; font-weight:bold;"
        np_style = "background-color:#E0FFFF; border:1px solid #00CED1; border-radius:3px; padding:0 2px;"
        vp_style = "background-color:#E0FFE0; border:1px solid #32CD32; border-radius:3px; padding:0 2px;"
        pp_style = "background-color:#FFFFE0; border:1px solid #FFD700; border-radius:3px; padding:0 2px;"

        # Add tags for subjects
        for s in self.analyzed_data["subjects"]:
            events_at_pos[s["start"]].append((f"<span style=\"{subject_style}\">", True))
            events_at_pos[s["end"]].append(("</span>", False))

        # Add tags for verbs
        for v in self.analyzed_data["verbs"]:
            events_at_pos[v["start"]].append((f"<span style=\"{verb_style}\">", True))
            events_at_pos[v["end"]].append(("</span>", False))

        # Add tags for noun phrases
        for np in self.analyzed_data["noun_phrases"]:
            events_at_pos[np["start"]].append((f"<span style=\"{np_style}\">[NP ", True))
            events_at_pos[np["end"]].append(("]</span>", False))

        # Add tags for verb phrases
        for vp in self.analyzed_data["verb_phrases"]:
            events_at_pos[vp["start"]].append((f"<span style=\"{vp_style}\">(VP ", True))
            events_at_pos[vp["end"]].append((")</span>", False))

        # Add tags for prepositional phrases
        for pp in self.analyzed_data["prepositional_phrases"]:
            events_at_pos[pp["start"]].append((f"<span style=\"{pp_style}\">{{PP ", True))
            events_at_pos[pp["end"]].append(("}}</span>", False))

        # Build the formatted HTML string
        formatted_html = []
        for i, char in enumerate(self.original_text):
            # Sort events at current position: closing tags first, then opening tags
            events_at_pos[i].sort(key=lambda x: not x[1]) # False (closing) comes before True (opening)

            for tag_string, is_opening_tag in events_at_pos[i]:
                formatted_html.append(tag_string)
            formatted_html.append(char)

        # Handle tags at the very end of the text
        events_at_pos[text_len].sort(key=lambda x: not x[1])
        for tag_string, is_opening_tag in events_at_pos[text_len]:
            formatted_html.append(tag_string)

        return "".join(formatted_html)

st.title('英文構造解析Webアプリ')

st.write('ここに英文を入力してください。')

# セッションステートでテキスト入力を管理
if 'text_input' not in st.session_state:
    st.session_state.text_input = ""

text_area_key = "english_text_input"
text_input_widget = st.text_area('英文を入力', value=st.session_state.text_input, height=150, key=text_area_key)

# 結果表示用のプレースホルダー
result_placeholder = st.empty()

if st.button('解析実行'):
    st.session_state.text_input = text_input_widget # 最新のテキスト入力をセッションステートに保存
    if st.session_state.text_input:
        try:
            with st.spinner('解析中...'):
                analyzer = SentenceAnalyzer(st.session_state.text_input)
                analyzed_data = analyzer.analyze()
                formatter = ResultFormatter(analyzed_data)
                formatted_html = formatter.format_html()

            result_placeholder.markdown(formatted_html, unsafe_allow_html=True)
        except Exception as e:
            result_placeholder.error(f"解析中にエラーが発生しました。入力された英文を確認してください。エラー詳細: {e}")
    else:
        result_placeholder.warning('英文を入力してください。')

if st.button('クリア'):
    st.session_state.text_input = ""
    st.experimental_rerun() # セッションステートをリセットして再描画
