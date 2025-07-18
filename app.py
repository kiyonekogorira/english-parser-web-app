import streamlit as st
import spacy

# spaCyモデルのロード
# アプリケーション起動時に一度だけロードするためにst.cache_resourceを使用
@st.cache_resource
def load_model():
    return spacy.load("en_core_web_sm")

nlp = load_model()

class SentenceAnalyzer:
    @classmethod
    def analyze_text(cls, text):
        doc = nlp(text)
        analyzed_sentences = []
        for sent in doc.sents:
            # 文のオフセットを考慮して解析
            analyzed_sentences.append(cls._analyze_sentence(sent))
        return analyzed_sentences

    @staticmethod
    def _analyze_sentence(doc):
        subjects = []
        verbs = []
        noun_phrases = []
        verb_phrases = []
        prepositional_phrases = []

        # 文の開始位置をオフセットとして保持
        offset = doc.start_char

        for token in doc:
            # 主語の特定
            if "nsubj" in token.dep_:
                subjects.append({"text": token.text, "start": token.idx, "end": token.idx + len(token.text)})
            # 動詞の特定 (助動詞も含む)
            if token.pos_ == "VERB" or token.pos_ == "AUX":
                verbs.append({"text": token.text, "start": token.idx, "end": token.idx + len(token.text)})

        # 名詞句の特定
        for chunk in doc.noun_chunks:
            noun_phrases.append({"text": chunk.text, "start": chunk.start_char, "end": chunk.end_char})

        # 動詞句と前置詞句の特定 (改善版)
        temp_verb_phrases = []
        temp_prepositional_phrases = []

        # 動詞句の候補を抽出
        for token in doc:
            if token.pos_ == "VERB":
                subtree_tokens = list(token.subtree)
                start_node = min(subtree_tokens, key=lambda t: t.i)
                end_node = max(subtree_tokens, key=lambda t: t.i)
                start_char = start_node.idx
                end_char = end_node.idx + len(end_node.text)
                temp_verb_phrases.append({
                    "text": doc.text[start_char-offset:end_char-offset],
                    "start": start_char,
                    "end": end_char
                })

        # 前置詞句の候補を抽出
        for token in doc:
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
                    "text": doc.text[start_char-offset:end_char-offset],
                    "start": start_char,
                    "end": end_char
                })

        # 句の重複や包含関係を整理する (長い句を優先)
        def remove_subsets(phrases):
            unique_phrases_by_span = { (p['start'], p['end']): p for p in phrases }
            phrases = list(unique_phrases_by_span.values())
            
            result = []
            for p1 in phrases:
                is_subset = False
                for p2 in phrases:
                    if (p1['start'], p1['end']) == (p2['start'], p2['end']):
                        continue
                    if p2['start'] <= p1['start'] and p1['end'] <= p2['end']:
                        is_subset = True
                        break
                if not is_subset:
                    result.append(p1)
            return result

        verb_phrases = remove_subsets(temp_verb_phrases)
        prepositional_phrases = remove_subsets(temp_prepositional_phrases)

        return {
            "original_text": doc.text,
            "subjects": subjects,
            "verbs": verbs,
            "noun_phrases": noun_phrases,
            "verb_phrases": verb_phrases,
            "prepositional_phrases": prepositional_phrases,
            "tokens_info": [{"text": token.text, "pos": token.pos_, "dep": token.dep_, "head": token.head.text} for token in doc]
        }

class ResultFormatter:
    def __init__(self, list_of_analyzed_data):
        self.list_of_analyzed_data = list_of_analyzed_data

    def format_html_all(self):
        full_html = []
        for analyzed_data in self.list_of_analyzed_data:
            full_html.append(self._format_single_html(analyzed_data))
        return "<br>".join(full_html)

    def _format_single_html(self, analyzed_data):
        original_text = analyzed_data["original_text"]
        text_len = len(original_text)
        events_at_pos = [[] for _ in range(text_len + 1)]
        
        # 文の開始位置をオフセットとして取得
        offset = analyzed_data["subjects"][0]["start"] if analyzed_data["subjects"] else (analyzed_data["verbs"][0]["start"] if analyzed_data["verbs"] else 0)
        if analyzed_data["noun_phrases"]:
            offset = min(offset, analyzed_data["noun_phrases"][0]["start"])


        subject_style = "color:red; font-weight:bold;"
        verb_style = "color:blue; font-weight:bold;"
        np_style = "background-color:#E0FFFF; border:1px solid #00CED1; border-radius:3px; padding:0 2px;"
        vp_style = "background-color:#E0FFE0; border:1px solid #32CD32; border-radius:3px; padding:0 2px;"
        pp_style = "background-color:#FFFFE0; border:1px solid #FFD700; border-radius:3px; padding:0 2px;"

        # 各要素の開始・終了位置を文の先頭からの相対位置に変換
        for s in analyzed_data["subjects"]:
            events_at_pos[s["start"] - offset].append((f'''<span style="{subject_style}">''', True))
            events_at_pos[s["end"] - offset].append(("</span>", False))

        for v in analyzed_data["verbs"]:
            events_at_pos[v["start"] - offset].append((f'''<span style="{verb_style}">''', True))
            events_at_pos[v["end"] - offset].append(("</span>", False))

        for np in analyzed_data["noun_phrases"]:
            events_at_pos[np["start"] - offset].append((f'''<span style="{np_style}">[NP ''', True))
            events_at_pos[np["end"] - offset].append(("]</span>", False))

        for vp in analyzed_data["verb_phrases"]:
            events_at_pos[vp["start"] - offset].append((f'''<span style="{vp_style}">(VP ''', True))
            events_at_pos[vp["end"] - offset].append((")</span>", False))

        for pp in analyzed_data["prepositional_phrases"]:
            events_at_pos[pp["start"] - offset].append((f'''<span style="{pp_style}">{{PP ''', True))
            events_at_pos[pp["end"] - offset].append(("}}</span>", False))

        formatted_html = []
        for i, char in enumerate(original_text):
            events_at_pos[i].sort(key=lambda x: not x[1])
            for tag_string, is_opening_tag in events_at_pos[i]:
                formatted_html.append(tag_string)
            formatted_html.append(char)

        events_at_pos[text_len].sort(key=lambda x: not x[1])
        for tag_string, is_opening_tag in events_at_pos[text_len]:
            formatted_html.append(tag_string)

        return "".join(formatted_html)

st.title('英文構造解析Webアプリ')
st.write('ここに英文を入力してください。')

if 'text_input' not in st.session_state:
    st.session_state.text_input = ""

text_area_key = "english_text_input"
text_input_widget = st.text_area('英文を入力', value=st.session_state.text_input, height=150, key=text_area_key)

result_placeholder = st.empty()

if st.button('解析実行'):
    st.session_state.text_input = text_input_widget
    if st.session_state.text_input:
        try:
            with st.spinner('解析中...'):
                analyzed_data_list = SentenceAnalyzer.analyze_text(st.session_state.text_input)
                formatter = ResultFormatter(analyzed_data_list)
                formatted_html = formatter.format_html_all()

            result_placeholder.markdown(formatted_html, unsafe_allow_html=True)
        except Exception as e:
            result_placeholder.error(f"解析中にエラーが発生しました。入力された英文を確認してください。エラー詳細: {e}")
    else:
        result_placeholder.warning('英文を入力してください。')

if st.button('クリア'):
    st.session_state.text_input = ""
    st.rerun()