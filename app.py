import streamlit as st
import spacy
import graphviz
from analyzer import SentenceAnalyzer # analyzer.pyからSentenceAnalyzerをインポート

# --- 1. spaCyモデルのロード ---
@st.cache_resource # アプリケーション起動時に一度だけロード
def load_spacy_model():
    return spacy.load("en_core_web_sm")

nlp = load_spacy_model()
analyzer = SentenceAnalyzer(nlp) # SentenceAnalyzerのインスタンスを作成

# --- 2. 解析関数の定義 (analyzer.pyのSentenceAnalyzerを使用) ---
def analyze_sentence(text):
    analyzed_data = analyzer.analyze_text(text)
    if analyzed_data:
        return analyzed_data[0] # analyzer.pyのanalyze_textが返す最初の文の解析結果をそのまま返す
    else:
        return {'tokens': [], 'chunks': []} # 解析結果がない場合

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
            st.write(f"**U-POS (汎用品詞):** {token['pos']} ({token['pos_japanese']})")
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
        node_label = f"{token['text']} ({token['pos_japanese']})"
        node_fillcolor = 'salmon' if token['is_root'] else 'lightblue'
        graph.node(str(token['id']), node_label, style='filled', fillcolor=node_fillcolor, shape='box')

    # エッジの追加
    for token in tokens_info:
        if not token['is_root']:
            head_token = next((t for t in tokens_info if t['id'] == token['head_id']), None)
            if head_token:
                edge_color = 'red' if token['dep'] in ['nsubj', 'dobj'] else 'black'
                edge_penwidth = '2' if token['dep'] in ['nsubj', 'dobj'] else '1'
                # 日本語の依存関係ラベルを使用
                edge_label = token['dep_japanese']
                graph.edge(str(token['head_id']), str(token['id']), label=edge_label, color=edge_color, penwidth=edge_penwidth)
    
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

chunk_type_japanese_map = {
    'NP': '名詞句 (Noun Phrase)',
    'VP': '動詞句 (Verb Phrase)',
    'PP': '前置詞句 (Prepositional Phrase)',
    'ADVP': '副詞句 (Adverb Phrase)'
}

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
        japanese_type = chunk_type_japanese_map.get(chunk['type'], chunk['type'])
        st.markdown(f"- **{japanese_type}**: `{chunk['text']}` (単語ID: {chunk['start_id']} - {chunk['end_id']})")

# --- 4. Streamlitアプリのメイン部分 ---
st.set_page_config(layout="wide", page_title="英文解析ツール")

# セッション状態の初期化
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

st.title("英文解析ツール")

input_text = st.text_area("解析したい英文を入力してください:", "The quick brown fox jumps over the lazy dog.", height=100)

if st.button("解析実行"):
    if input_text:
        with st.spinner('解析中...'):
            st.session_state.analysis_result = analyze_sentence(input_text)
    else:
        st.warning("解析する英文を入力してください。")

# 解析結果がある場合のみ表示
if st.session_state.analysis_result:
    tokens = st.session_state.analysis_result['tokens']
    chunks = st.session_state.analysis_result['chunks']

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

st.sidebar.markdown("### アプリケーション情報")
st.sidebar.info("このツールはSpaCyライブラリを使用して英文の品詞、依存関係、句構造を解析し、視覚的に表示します。")
st.sidebar.markdown("---")
st.sidebar.markdown("### 品詞の解説")
st.sidebar.markdown("- **名詞 (NOUN)**: 人、場所、物、概念などを表す単語。")
st.sidebar.markdown("- **動詞 (VERB)**: 動作や状態を表す単語。")
st.sidebar.markdown("- **形容詞 (ADJ)**: 名詞や代名詞を修飾する単語。")
st.sidebar.markdown("- **副詞 (ADV)**: 動詞、形容詞、他の副詞、文全体を修飾する単語。")
st.sidebar.markdown("- **前置詞 (ADP)**: 名詞や代名詞の前に置かれ、他の語との関係を示す単語。")
st.sidebar.markdown("- **限定詞 (DET)**: 名詞の前に置かれ、その名詞が特定のものであるか、一般的なものであるかを示す単語（例: a, the, this）。")
st.sidebar.markdown("- **代名詞 (PRON)**: 名詞の代わりに使われる単語。")
st.sidebar.markdown("- **助動詞 (AUX)**: 主動詞を助ける動詞（例: be, have, do, will）。")
st.sidebar.markdown("- **接続詞 (CONJ/CCONJ/SCONJ)**: 単語、句、節などを結びつける単語。")
st.sidebar.markdown("- **固有名詞 (PROPN)**: 特定の人、場所、組織などの名前。")
st.sidebar.markdown("- **数詞 (NUM)**: 数量を表す単語。")
st.sidebar.markdown("- **句読点 (PUNCT)**: 文の区切りを示す記号。")
st.sidebar.markdown("---")
st.sidebar.markdown("### 句構造の解説")
st.sidebar.markdown("- **名詞句 (NP)**: 名詞を中心に構成される句。文の主語や目的語になることが多いです。例: `The quick brown fox`")
st.sidebar.markdown("- **動詞句 (VP)**: 動詞を中心に構成される句。動詞とその目的語、補語、副詞などが含まれます。例: `jumps over the lazy dog`")
st.sidebar.markdown("- **前置詞句 (PP)**: 前置詞とそれに続く名詞句で構成される句。場所、時間、方法などを表します。例: `over the lazy dog`")
st.sidebar.markdown("- **副詞句 (ADVP)**: 副詞を中心に構成される句。動詞、形容詞、他の副詞を修飾します。例: `very quickly`")
st.sidebar.markdown("---")
st.sidebar.markdown("### 依存関係の解説")
st.sidebar.markdown("- **ROOT**: 文の主動詞。文の中心となる単語です。")
st.sidebar.markdown("- **nsubj (名詞主語)**: 動詞の主語となる名詞句。")
st.sidebar.markdown("- **dobj (直接目的語)**: 動詞の直接目的語となる名詞句。")
st.sidebar.markdown("- **amod (形容詞修飾語)**: 名詞を修飾する形容詞。")
st.sidebar.markdown("- **advmod (副詞修飾語)**: 動詞、形容詞、他の副詞を修飾する副詞。")
st.sidebar.markdown("- **prep (前置詞句)**: 前置詞とその目的語からなる句。")
st.sidebar.markdown("- **pobj (前置詞の目的語)**: 前置詞の目的語となる名詞句。")
st.sidebar.markdown("- **det (限定詞)**: 名詞を限定する単語（例: a, the, this）。")
st.sidebar.markdown("- **aux (助動詞)**: 主動詞を助ける動詞（例: have, be, do）。")
st.sidebar.markdown("- **cc (等位接続詞)**: 2つ以上の同等の要素（単語、句、節）を結びつける接続詞（例: and, but, or）。")
st.sidebar.markdown("- **conj (接続)**: 等位接続詞によって結びつけられた要素。")
st.sidebar.markdown("- **compound (複合語)**: 複数の単語が結合して一つの意味をなす複合語。")
st.sidebar.markdown("- **punct (句読点)**: 文の句読点。")
st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 英文解析プロジェクト")