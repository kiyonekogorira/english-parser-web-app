import streamlit as st
import spacy
import re

# spaCyモデルのロード
# アプリケーション起動時に一度だけロードするためにst.cache_resourceを使用
@st.cache_resource
def load_model():
    return spacy.load("en_core_web_sm")

nlp = load_model()

class SentenceAnalyzer:
    @classmethod
    def analyze_text(cls, text):
        # Filter lines to keep only those that likely contain English sentences
        cleaned_lines = []
        for line in text.split('\n'):
            line = line.strip()
            # Remove leading numbers and periods (e.g., "1. ", "2. ")
            line = re.sub(r'^\d+\.\s*', '', line)
            # Remove common Japanese labels like "テストケース:"
            line = re.sub(r'^テストケース:\s*', '', line)
            line = re.sub(r'^\d+\.\s*', '', line) # 再度数字とピリオドを削除（日本語ラベルの後に続く場合）

            if re.search(r'[a-zA-Z]', line): # Check if the line still contains English letters
                cleaned_lines.append(line)
        
        clean_text = "\n".join(cleaned_lines)
        if not clean_text.strip():
            return []

        doc = nlp(clean_text)
        analyzed_sentences = []
        for sent in doc.sents:
            if not sent.text.strip():
                continue
            # 文のオフセットを考慮して解析
            analyzed_sentences.append(cls._analyze_sentence(sent))
        return analyzed_sentences

    @staticmethod
    def _analyze_sentence(doc):
        # doc is a spaCy Span object (a sentence)
        subjects = []
        verbs = []
        noun_phrases = []
        verb_phrases = []
        prepositional_phrases = []

        # 文の開始位置をオフセットとして保持
        sent_offset = doc.start_char

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
            if token.pos_ == "VERB" or token.pos_ == "AUX": # AUX (助動詞) も動詞句の起点と見なす
                vp_tokens = [token]

                # 動詞の直接の子孫で、主語ではないものを追加
                for child in token.children:
                    if child.dep_ not in ["nsubj", "csubj", "expl"]: # 主語を除外
                        vp_tokens.extend(list(child.subtree))

                # 動詞がAUXの場合、そのheadがVERBであれば、そのVERBのsubtreeも追加
                if token.pos_ == "AUX" and token.head.pos_ == "VERB":
                    vp_tokens.extend(list(token.head.subtree))

                # Sort tokens by index to get a continuous span
                if vp_tokens:
                    vp_tokens.sort(key=lambda t: t.i)
                    start_node = vp_tokens[0]
                    end_node = vp_tokens[-1]
                    start_char = start_node.idx
                    end_char = end_node.idx + len(end_node.text)
                    temp_verb_phrases.append({
                        "text": doc.text[start_char-sent_offset:end_char-sent_offset],
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
                    "text": doc.text[start_char-sent_offset:end_char-sent_offset],
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
            "sent_offset": sent_offset,
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
        # Use <p> tags for better separation between sentences
        return "".join([f"<p>{html}</p>" for html in full_html])

    def _format_single_html(self, analyzed_data):
        original_text = analyzed_data["original_text"]
        text_len = len(original_text)
        events_at_pos = [[] for _ in range(text_len + 1)]
        
        # 文の開始位置をオフセットとして取得
        offset = analyzed_data["sent_offset"]

        subject_style = "color:red; font-weight:bold;"
        verb_style = "color:blue; font-weight:bold;"
        np_style = "background-color:#E0FFFF; border:1px solid #00CED1; border-radius:3px; padding:0 2px;"
        vp_style = "background-color:#E0FFE0; border:1px solid #32CD32; border-radius:3px; padding:0 2px;"
        pp_style = "background-color:#FFFFE0; border:1px solid #FFD700; border-radius:3px; padding:0 2px;"

        def add_events(items, open_tag, close_tag):
            for item in items:
                start_pos = max(0, item["start"] - offset)
                end_pos = min(text_len, item["end"] - offset)
                if start_pos <= end_pos:
                    events_at_pos[start_pos].append((open_tag, True))
                    events_at_pos[end_pos].append((close_tag, False))

        # Add tags for all element types
        add_events(analyzed_data["subjects"], f'''<span style="{subject_style}">''', "</span>")
        add_events(analyzed_data["verbs"], f'''<span style="{verb_style}">''', "</span>")
        add_events(analyzed_data["noun_phrases"], f'''<span style="{np_style}">[名詞句: ''', "]</span>")
        add_events(analyzed_data["verb_phrases"], f'''<span style="{vp_style}">(動詞句: ''', ")</span>")
        add_events(analyzed_data["prepositional_phrases"], f'''<span style="{pp_style}">{{前置詞句: ''', "}}</span>")

        # Build the formatted HTML string
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

# 凡例
st.markdown("""
<div style="font-size: 0.8em; margin-top: 1em; padding: 0.5em; border: 1px solid #eee; border-radius: 5px;">
    <b>凡例:</b><br>
    <span style="color:red; font-weight:bold;">主語</span>
    <span style="color:blue; font-weight:bold;">動詞</span><br>
    <span style="background-color:#E0FFFF; border:1px solid #00CED1; border-radius:3px; padding:0 2px;">[NP ... ]</span>
    <span style="background-color:#E0FFE0; border:1px solid #32CD32; border-radius:3px; padding:0 2px;">(VP ... )</span>
    <span style="background-color:#FFFFE0; border:1px solid #FFD700; border-radius:3px; padding:0 2px;">{PP ... }}</span>
</div>
""", unsafe_allow_html=True)

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
                if analyzed_data_list:
                    formatter = ResultFormatter(analyzed_data_list)
                    formatted_html = formatter.format_html_all()
                    result_placeholder.markdown(formatted_html, unsafe_allow_html=True)
                else:
                    result_placeholder.warning('有効な英文が見つかりませんでした。')

        except Exception as e:
            result_placeholder.error(f"解析中にエラーが発生しました。入力された英文を確認してください。エラー詳細: {e}")
    else:
        result_placeholder.warning('英文を入力してください。')

if st.button('クリア'):
    st.session_state.text_input = ""
    st.rerun()
