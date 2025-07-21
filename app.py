import streamlit as st
import spacy
import graphviz

# --- 1. spaCyモデルのロード ---
@st.cache_resource # アプリケーション起動時に一度だけロード
def load_spacy_model():
    return spacy.load("en_core_web_sm")

nlp = load_spacy_model()

# --- 2. 解析関数の定義 (今後のステップで実装) ---
def analyze_sentence(text):
    doc = nlp(text)
    
    # トークン情報のリストを初期化
    tokens_info = []
    for token in doc:
        children_ids = [child.i for child in token.children]
        token_info = {
            'id': token.i,
            'text': token.text,
            'lemma': token.lemma_,
            'pos': token.pos_,
            'tag': token.tag_,
            'dep': token.dep_,
            'head_id': token.head.i,
            'children_ids': children_ids,
            'is_root': token.dep_ == "ROOT"
        }
        tokens_info.append(token_info)

    # 句構造のリストを初期化
    chunks_info = []

    # 名詞句 (NP)
    for chunk in doc.noun_chunks:
        chunks_info.append({
            'type': 'NP',
            'text': chunk.text,
            'start_id': chunk.start,
            'end_id': chunk.end - 1
        })

    # 動詞句 (VP), 前置詞句 (PP), 副詞句 (ADVP) はカスタムロジックで抽出
    # (MVPでは簡易的な抽出)
    for token in doc:
        # 動詞句 (VP)
        if token.dep_ == "ROOT":
            vp_start = token.i
            vp_end = token.i
            for child in token.children:
                if child.dep_ in ["aux", "auxpass", "dobj", "attr", "acomp"]:
                    vp_end = max(vp_end, child.i)
            chunks_info.append({
                'type': 'VP',
                'text': doc[vp_start:vp_end+1].text,
                'start_id': vp_start,
                'end_id': vp_end
            })

        # 前置詞句 (PP)
        if token.pos_ == "ADP":
            pp_start = token.i
            pp_end = token.i
            for child in token.children:
                if child.dep_ == "pobj":
                    pp_end = child.i
            chunks_info.append({
                'type': 'PP',
                'text': doc[pp_start:pp_end+1].text,
                'start_id': pp_start,
                'end_id': pp_end
            })

        # 副詞句 (ADVP)
        if token.pos_ == "ADV":
            advp_start = token.i
            advp_end = token.i
            chunks_info.append({
                'type': 'ADVP',
                'text': doc[advp_start:advp_end+1].text,
                'start_id': advp_start,
                'end_id': advp_end
            })

    return {
        'tokens': tokens_info,
        'chunks': chunks_info
    }

# --- 3. UI表示関数の定義 (今後のステップで実装) ---
def get_pos_color(pos_tag):
    colors = {
        'NOUN': 'blue', 'VERB': 'red', 'ADJ': 'green', 'ADP': 'purple', 'DET': 'orange',
        'ADV': 'brown', 'PRON': 'pink', 'AUX': 'cyan', 'PART': 'grey', 'CCONJ': 'lime',
        'SCONJ': 'teal', 'INTJ': 'maroon', 'NUM': 'navy', 'PROPN': 'darkblue',
        'SYM': 'olive', 'X': 'black', 'SPACE': 'lightgrey', 'PUNCT': 'darkgrey'
    }
    return colors.get(pos_tag, 'black')

def display_tokens_default(tokens_info):
    html_string = ""
    for token in tokens_info:
        color = get_pos_color(token['pos'])
        html_string += f"<span style='color: {color};'>{token['text']} </span>"
    st.markdown(f"<div style='font-size: 20px;'>{html_string}</div>", unsafe_allow_html=True)

def display_tokens_detailed(tokens_info):
    st.subheader("詳細な品詞情報")
    for token in tokens_info:
        with st.popover(f"**{token['text']}**"):
            st.write(f"**単語:** {token['text']}")
            st.write(f"**原形:** {token['lemma']}")
            st.write(f"**U-POS (汎用品詞):** {token['pos']}")
            st.write(f"**X-POS (詳細品詞):** {token['tag']}")
            st.write(f"**依存関係:** {token['dep']}")
            st.write(f"**親単語ID:** {token['head_id']}")
            st.write(f"**子単語ID:** {token['children_ids']}")

def display_dependency_tree(tokens_info):
    st.subheader("依存関係ツリー")
    graph = graphviz.Digraph(comment='Dependency Tree', format='svg')
    graph.attr(rankdir='LR', overlap='false', compound='true')

    # ノードの追加
    for token in tokens_info:
        node_label = f"{token['text']} ({token['pos']})"
        node_fillcolor = 'salmon' if token['is_root'] else 'lightblue'
        graph.node(str(token['id']), node_label, style='filled', fillcolor=node_fillcolor, shape='box')

    # エッジの追加
    for token in tokens_info:
        if not token['is_root']:
            head_token = next((t for t in tokens_info if t['id'] == token['head_id']), None)
            if head_token:
                edge_color = 'red' if token['dep'] in ['nsubj', 'dobj'] else 'black'
                edge_penwidth = '2' if token['dep'] in ['nsubj', 'dobj'] else '1'
                graph.edge(str(token['head_id']), str(token['id']), label=token['dep'], color=edge_color, penwidth=edge_penwidth)
    
    try:
        st.graphviz_chart(graph)
    except Exception as e:
        st.error(f"依存関係ツリーの表示中にエラーが発生しました: {e}")
        st.info("Graphvizが正しくインストールされているか確認してください。")

def get_chunk_color(chunk_type):
    colors = {
        'NP': '#DDA0DD', # Plum
        'VP': '#ADD8E6', # LightBlue
        'PP': '#90EE90', # LightGreen
        'ADVP': '#FFB6C1' # LightPink
    }
    return colors.get(chunk_type, 'lightgrey')

def display_chunks(tokens_info, chunks_info):
    st.subheader("句構造")
    
    sentence_html = ""
    token_background_colors = {}

    for i, token in enumerate(tokens_info):
        token_background_colors[token['id']] = 'transparent'
        
        for chunk in sorted(chunks_info, key=lambda x: (x['end_id'] - x['start_id'])):
            if chunk['start_id'] <= token['id'] <= chunk['end_id']:
                token_background_colors[token['id']] = get_chunk_color(chunk['type'])
                break

    for token in tokens_info:
        bg_color = token_background_colors.get(token['id'], 'transparent')
        sentence_html += f"<span style='background-color: {bg_color}; padding: 2px 4px; border-radius: 3px; margin: 0 1px; display: inline-block;'>{token['text']}</span> "
    
    st.markdown(f"<div style='font-size: 18px; line-height: 2.0; padding: 10px; border: 1px solid #ddd; border-radius: 5px;'>{sentence_html}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 検出された句の一覧:")
    for chunk in chunks_info:
        st.markdown(f"- **{chunk['type']}**: `{chunk['text']}` (単語ID: {chunk['start_id']} - {chunk['end_id']})")

# --- 4. Streamlitアプリのメイン部分 ---
st.set_page_config(layout="wide", page_title="英文解析ツール")

st.title("英文解析ツール")

input_text = st.text_area("解析したい英文を入力してください:", "The quick brown fox jumps over the lazy dog.", height=100)

if st.button("解析実行"):
    if input_text:
        with st.spinner('解析中...'):
            analysis_result = analyze_sentence(input_text)
            tokens = analysis_result['tokens']
            chunks = analysis_result['chunks']

            st.markdown("---")
            st.header("1. 品詞情報")

            show_detailed_pos = st.checkbox("詳細な品詞を表示 (クリックで詳細)", value=False)
            if show_detailed_pos:
                display_tokens_detailed(tokens)
            else:
                display_tokens_default(tokens)
            
            st.markdown("---")
            st.header("2. 依存関係解析")
            display_dependency_tree(tokens)

            st.markdown("---")
            st.header("3. 句構造解析")
            display_chunks(tokens, chunks)

    else:
        st.warning("解析する英文を入力してください。")

st.sidebar.markdown("### アプリケーション情報")
st.sidebar.info("このツールはSpaCyライブラリを使用して英文の品詞、依存関係、句構造を解析し、視覚的に表示します。")
st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 英文解析プロジェクト")