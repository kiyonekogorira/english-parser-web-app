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

        # 動詞句と前置詞句の特定 (改善版)
        temp_verb_phrases = []
        temp_prepositional_phrases = []

        # 動詞句の候補を抽出
        for token in self.doc:
            if token.pos_ == "VERB":
                # 動詞から始まる部分木を基本の句とする
                subtree_tokens = list(token.subtree)
                start_node = min(subtree_tokens, key=lambda t: t.i)
                end_node = max(subtree_tokens, key=lambda t: t.i)
                start_char = start_node.idx
                end_char = end_node.idx + len(end_node.text)
                temp_verb_phrases.append({
                    "text": self.doc.text[start_char:end_char],
                    "start": start_char,
                    "end": end_char
                })

        # 前置詞句の候補を抽出
        for token in self.doc:
            if token.pos_ == "ADP" and any(c.dep_ == "pobj" for c in token.children):
                pp_tokens = [token]
                for child in token.children:
                    if child.dep_ == "pobj":
                        pp_tokens.extend(list(child.subtree))
                
                start_node = min(pp_tokens, key=lambda t: t.i)
                end_node = max(pp_tokens, key=lambda t: t.i)
                start_char = start_node.idx
                end_char = end_node.idx + len(end_node.text)
                temp_prepositional_phrases.append({
                    "text": self.doc.text[start_char:end_char],
                    "start": start_char,
                    "end": end_char
                })

        # 句の重複や包含関係を整理する (長い句を優先)
        def remove_subsets(phrases):
            # 重複をなくす
            unique_phrases_by_span = { (p['start'], p['end']): p for p in phrases }
            phrases = list(unique_phrases_by_span.values())
            
            # 長い句が短い句を包含する場合、短い句を削除
            result = []
            for p1 in phrases:
                is_subset = False
                for p2 in phrases:
                    # 自分自身との比較はスキップ
                    if (p1['start'], p1['end']) == (p2['start'], p2['end']):
                        continue
                    # p1がp2に包含されているか
                    if p2['start'] <= p1['start'] and p1['end'] <= p2['end']:
                        is_subset = True
                        break
                if not is_subset:
                    result.append(p1)
            return result

        verb_phrases = remove_subsets(temp_verb_phrases)
        prepositional_phrases = remove_subsets(temp_prepositional_phrases)


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
