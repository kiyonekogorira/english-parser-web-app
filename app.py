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
    return analyzed_data # リスト全体を返す

# --- 3. UI表示関数の定義 (今後のステップで実装) ---
pos_colors = {
    'NOUN': 'blue', 'VERB': 'red', 'ADJ': 'green', 'ADP': 'purple', 'DET': 'orange',
    'ADV': 'brown', 'PRON': 'pink', 'AUX': 'magenta', 'PART': 'orange', 'CCONJ': 'lime',
    'SCONJ': 'teal', 'INTJ': 'maroon', 'NUM': 'navy', 'PROPN': 'darkblue',
    'SYM': 'olive', 'X': 'black', 'SPACE': 'lightgrey', 'PUNCT': 'darkgrey'
}

def get_pos_color(pos_tag):
    return pos_colors.get(pos_tag, 'black')

chunk_colors = {
    'NP': '#ADD8E6', # LightBlue
    'VP': '#DDA0DD', # Plum
    'PP': '#90EE90', # LightGreen
    'ADVP': '#FFB6C1' # LightPink
}

def get_chunk_color(chunk_type):
    return chunk_colors.get(chunk_type, 'lightgrey')

chunk_type_japanese_map = {
    'NP': '名詞句 (Noun Phrase)',
    'VP': '動詞句 (Verb Phrase)',
    'PP': '前置詞句 (Prepositional Phrase)',
    'ADVP': '副詞句 (Adverb Phrase)'
}

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
    root_token = None
    nsubj_token = None
    other_tokens = []

    for token in tokens_info:
        if token['is_root']:
            root_token = token
        elif token['dep'] == 'nsubj':
            nsubj_token = token
        else:
            other_tokens.append(token)

    with graph.subgraph(name='cluster_main_nodes') as c:
        c.attr(rank='same') # ROOTとnsubjを同じランクに配置

        # nsubjノードを先に配置 (左側)
        if nsubj_token:
            node_label = f"{nsubj_token['text']} ({nsubj_token['pos_japanese']})"
            c.node(str(nsubj_token['id']), node_label, style='filled', fillcolor='salmon', shape='box')

        # ROOTノードを次に配置 (右側)
        if root_token:
            node_label = f"{root_token['text']} ({root_token['pos_japanese']})"
            c.node(str(root_token['id']), node_label, style='filled', fillcolor='salmon', shape='box')

        # nsubjとROOTの間に不可視の順序付けエッジを追加
        if nsubj_token and root_token:
            # このエッジが左右の順序を強制する
            graph.edge(str(nsubj_token['id']), str(root_token['id']), style='invis', constraint='true')

    # その他のノードを追加
    for token in other_tokens:
        node_label = f"{token['text']} ({token['pos_japanese']})"
        node_fillcolor = 'lightblue' # その他のノードはlightblue
        graph.node(str(token['id']), node_label, style='filled', fillcolor=node_fillcolor, shape='box')

    # エッジの追加
    for token in tokens_info:
        if not token['is_root']:
            head_token = next((t for t in tokens_info if t['id'] == token['head_id']), None)
            if head_token:
                edge_color = 'salmon' if token['dep'] == 'nsubj' else ('red' if token['dep'] == 'dobj' else 'black')
                edge_penwidth = '2' if token['dep'] in ['nsubj', 'dobj'] else '1'
                # 日本語の依存関係ラベルを使用
                edge_label = token['dep_japanese']
                edge_dir = 'forward' # Default direction
                if token['dep'] == 'nsubj':
                    edge_dir = 'both'
                elif token['dep'] in ['det', 'amod'] and head_token and head_token['dep'] == 'nsubj': # head_tokenがnsubjの場合
                    edge_dir = 'back'
                graph.edge(str(token['head_id']), str(token['id']), label=edge_label, color=edge_color, penwidth=edge_penwidth, dir=edge_dir)
    
    try:
        st.graphviz_chart(graph)
    except Exception as e:
        st.error(f"依存関係ツリーの表示中にエラーが発生しました: {e}")
        st.info("Graphvizが正しくインストールされているか確認してください。")

def display_chunk_tree(tokens_info, chunks_info):
    st.subheader("句構造ツリー")
    graph = graphviz.Digraph(comment='Chunk Tree', format='svg')
    graph.attr(rankdir='TB', overlap='false', compound='true')

    # トークンIDから情報を引けるように辞書を作成
    token_map = {token['id']: token for token in tokens_info}

    # チャンクをIDでアクセスできるように辞書化
    chunk_dict = {f"{c['type']}_{c['start_id']}_{c['end_id']}": c for c in chunks_info}

    # 親子関係を構築
    parent_map = {}
    sorted_chunks = sorted(chunks_info, key=lambda x: (x['start_id'], - (x['end_id'] - x['start_id'])))

    for i, chunk in enumerate(sorted_chunks):
        chunk_id = f"{chunk['type']}_{chunk['start_id']}_{chunk['end_id']}"
        parent_id = None
        for j, potential_parent in enumerate(sorted_chunks):
            if i == j: continue
            if potential_parent['start_id'] <= chunk['start_id'] and potential_parent['end_id'] >= chunk['end_id']:
                if parent_id is None or (chunk_dict[parent_id]['end_id'] - chunk_dict[parent_id]['start_id'] > potential_parent['end_id'] - potential_parent['start_id']):
                    parent_id = f"{potential_parent['type']}_{potential_parent['start_id']}_{potential_parent['end_id']}"
        parent_map[chunk_id] = parent_id

    # ノードを追加
    for chunk_id, chunk in chunk_dict.items():
        color = get_chunk_color(chunk['type'])
        graph.node(chunk_id, f"{chunk['type']}\n({chunk['text']})", style='filled', fillcolor=color, shape='box')

    # 単語ノードを追加 (どのチャンクにも属さないもの)
    token_in_chunk = {t['id']: False for t in tokens_info}
    for chunk in chunks_info:
        for i in range(chunk['start_id'], chunk['end_id'] + 1):
            if i in token_in_chunk:
                token_in_chunk[i] = True
    
    for token_id, is_in_chunk in token_in_chunk.items():
        if not is_in_chunk:
             graph.node(str(token_id), token_map[token_id]['text'], shape='plaintext')


    # エッジを追加
    for chunk_id, parent_id in parent_map.items():
        if parent_id:
            graph.edge(parent_id, chunk_id)
        else: # 親がいない場合は文のルートに接続 (見えないノード)
            graph.edge("S", chunk_id)
    
    # チャンクと単語のエッジを追加
    for chunk_id, chunk in chunk_dict.items():
        current_tokens_ids = list(range(chunk['start_id'], chunk['end_id'] + 1))
        children_chunks = [cid for cid, pid in parent_map.items() if pid == chunk_id]
        
        for child_chunk_id in children_chunks:
            child_chunk = chunk_dict[child_chunk_id]
            for i in range(child_chunk['start_id'], child_chunk['end_id'] + 1):
                if i in current_tokens_ids:
                    current_tokens_ids.remove(i)
        
        for token_id in current_tokens_ids:
            # token_map を使って安全にアクセス
            token_data = token_map.get(token_id) # ここを修正
            if token_data: # token_data が存在する場合のみ処理
                graph.node(str(token_id), token_data['text'], shape='plaintext')
                graph.edge(chunk_id, str(token_id))

    try:
        st.graphviz_chart(graph)
    except Exception as e:
        st.error(f"句構造ツリーの表示中にエラーが発生しました: {e}")

def display_chunks(tokens_info, chunks_info):
    st.subheader("句構造の階層表示")
    display_chunk_tree(tokens_info, chunks_info)

    st.markdown("---")
    st.markdown("#### 検出された句の一覧 (ネスト構造):")
    
    # 句のネストレベルを計算して表示
    nested_chunks = []
    for i, chunk in enumerate(chunks_info):
        nesting_level = 0
        for other_chunk in chunks_info:
            if chunk != other_chunk and \
               other_chunk['start_id'] <= chunk['start_id'] and \
               chunk['end_id'] <= other_chunk['end_id']:
                nesting_level += 1
        nested_chunks.append((chunk, nesting_level))
    
    nested_chunks.sort(key=lambda x: (x[0]['start_id'], x[1]))

    for chunk, nesting_level in nested_chunks:
        indent = "&nbsp;" * 4 * nesting_level
        japanese_type = chunk_type_japanese_map.get(chunk['type'], chunk['type'])
        st.markdown(f"{indent}- **{japanese_type}**: `{chunk['text']}`")

# 期待される句構造データ (デバッグ用)
expected_chunks_data = [
    {"sentence": "The quick brown fox jumps over the lazy dog.", "chunks": [
        {"type": "NP", "text": "The quick brown fox"},
        {"type": "VP", "text": "jumps over the lazy dog"},
        {"type": "PP", "text": "over the lazy dog"}
    ]},
    {"sentence": "He is running quickly in the park.", "chunks": [
        {"type": "NP", "text": "He"},
        {"type": "VP", "text": "is running quickly in the park"},
        {"type": "ADVP", "text": "quickly"},
        {"type": "PP", "text": "in the park"}
    ]},
    {"sentence": "She has been studying English very hard.", "chunks": [
        {"type": "NP", "text": "She"},
        {"type": "NP", "text": "English"},
        {"type": "VP", "text": "has been studying English very hard"},
        {"type": "ADVP", "text": "very hard"}
    ]},
    {"sentence": "They will go to the store to buy some groceries.", "chunks": [
        {"type": "NP", "text": "They"},
        {"type": "NP", "text": "the store"},
        {"type": "NP", "text": "some groceries"},
        {"type": "VP", "text": "will go to the store to buy some groceries"},
        {"type": "VP", "text": "to buy some groceries"},
        {"type": "PP", "text": "to the store"}
    ]}
]

def display_expected_chunks(expected_data):
    st.subheader("期待される句構造 (デバッグ用):")
    for sent_data in expected_data:
        st.markdown(f"**文:** `{sent_data['sentence']}`")
        for chunk in sent_data['chunks']:
            japanese_type = chunk_type_japanese_map.get(chunk['type'], chunk['type'])
            st.markdown(f"- **{japanese_type}**: `{chunk['text']}`")
    st.markdown("---")

def display_color_legend():
    st.sidebar.markdown("### 色分け凡例")
    st.sidebar.markdown("#### 品詞 (POS)")
    for pos, color in pos_colors.items():
        st.sidebar.markdown(f"<span style='color: {color};'>■</span> {pos} ({analyzer.pos_map.get(pos, pos)})", unsafe_allow_html=True)
    
    st.sidebar.markdown("#### 句構造 (Chunk)")
    for chunk_type, color in chunk_colors.items():
        st.sidebar.markdown(f"<span style='background-color: {color}; padding: 2px 5px; border-radius: 3px;'>&nbsp;&nbsp;&nbsp;</span> {chunk_type_japanese_map.get(chunk_type, chunk_type)}", unsafe_allow_html=True)

# --- 4. Streamlitアプリのメイン部分 ---
st.set_page_config(layout="wide", page_title="英文解析ツール")

# セッション状態の初期化
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

st.title("英文解析ツール")

input_text = st.text_area("解析したい英文を入力してください:", "The quick brown fox jumps over the lazy dog. A young boy is running quickly in the park. My diligent sister has been studying English very hard. All the students will go to the store to buy some groceries.", height=100)

if st.button("解析実行"):
    if input_text:
        with st.spinner('解析中...'):
            st.session_state.analysis_result = analyze_sentence(input_text)
    else:
        st.warning("解析する英文を入力してください。")

# 解析結果がある場合のみ表示
if st.session_state.analysis_result:
    # 各文の解析結果をループして表示
    for i, sentence_analysis in enumerate(st.session_state.analysis_result):
        st.markdown(f"## 文 {i+1}: {sentence_analysis['original_text']}")

        tokens = sentence_analysis['tokens']
        chunks = sentence_analysis['chunks']

        st.markdown("---")
        st.header("1. 品詞情報")

        show_detailed_pos = st.checkbox(f"文 {i+1} の詳細な品詞を表示 (クリックで詳細)", value=False, key=f"detailed_pos_{i}")
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

        # 期待される句構造のデバッグ表示 (該当する文のみ表示)
        if i < len(expected_chunks_data):
            display_expected_chunks([expected_chunks_data[i]])
        st.markdown("---<br>---") # 各文の区切りを明確にする

st.sidebar.markdown("### アプリケーション情報")
st.sidebar.info("このツールはSpaCyライブラリを使用して英文の品詞、依存関係、句構造を解析し、視覚的に表示します。")
st.sidebar.markdown("---")
display_color_legend() # 色分け凡例の呼び出し
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
st.sidebar.markdown("- **間投詞 (INTJ)**: 感情や驚きなどを表す単語（例: Oh!, Wow!）。")
st.sidebar.markdown("- **句読点 (PUNCT)**: 文の句読点。")
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