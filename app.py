import streamlit as st
import spacy
import graphviz
import streamlit.components.v1 as components
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
            st.write(f"**依存関係:** {token['dep']} ({token['dep_japanese']})")
            st.write(f"**親単語ID:** {token['head_id']}")
            st.write(f"**子単語ID:** {token['children_ids']}")
            if token.get('morph_japanese'):
                st.write(f"**形態素情報:** {token['morph_japanese']}")
            if token.get('is_entity_part'):
                st.write(f"**固有表現タイプ:** {token['ent_type']} ({token['ent_type_japanese']})")
                if token.get('entity_text'):
                    st.write(f"**固有表現全体:** {token['entity_text']}")

def display_mermaid_dependency_tree(tokens_info, sentence_id):
    st.subheader("依存関係ツリー (Mermaid版)")
    mermaid_code = "graph LR\n" # Left-Right direction for dependency tree

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

    # ROOTとnsubjを強調
    if nsubj_token:
        mermaid_code += f"    {nsubj_token['id']}[\"{nsubj_token['text']}<br>({nsubj_token['pos_japanese']})\"]:::main_node\n"
    if root_token:
        mermaid_code += f"    {root_token['id']}[\"{root_token['text']}<br>({root_token['pos_japanese']})\"]:::main_node\n"

    # その他のノード
    for token in other_tokens:
        mermaid_code += f"    {token['id']}[\"{token['text']}<br>({token['pos_japanese']})\"]:::other_node\n"

    # nsubjとROOTの順序を強制
    if nsubj_token and root_token:
        mermaid_code += f"    {nsubj_token['id']} --- {root_token['id']}\n"

    # エッジの追加
    for token in tokens_info:
        if not token['is_root']:
            head_token = next((t for t in tokens_info if t['id'] == token['head_id']), None)
            if head_token:
                edge_label = token['dep_japanese']
                mermaid_code += f"    {head_token['id']} -- {edge_label} --> {token['id']}\n"

    # スタイル定義
    mermaid_code += "    classDef main_node fill:#salmon,stroke:#333,stroke-width:2px;\n"
    mermaid_code += "    classDef other_node fill:#lightblue,stroke:#333,stroke-width:1px;\n"

    html_content = f"""
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
    <div id="mermaid-dep-container-{sentence_id}" style="width: 100%; height: 600px; border:1px solid #ddd; overflow: hidden;">
        <div class="mermaid">
{mermaid_code}
        </div>
    </div>
    <script>
    (function(){{
        const container = document.getElementById('mermaid-dep-container-{sentence_id}');
        const mermaidDiv = container.querySelector('.mermaid');
        const mermaidId = `mermaid-svg-dep-{sentence_id}`;
        
        mermaid.initialize({{{{ startOnLoad: false }}}});
        try {{
            mermaid.render(mermaidId, mermaidDiv.textContent, (svgCode) => {{
                mermaidDiv.innerHTML = svgCode;
                const svg = mermaidDiv.querySelector('svg');
                if (svg) {{
                    svg.style.width = '100%';
                    svg.style.height = '100%';
                    svgPanZoom(svg, {{{{ 
                        zoomEnabled: true,
                        controlIconsEnabled: true,
                        fit: true,
                        center: true,
                        minZoom: 0.5,
                        maxZoom: 10
                    }}}});
                }}
            }});
        }} catch (e) {{
            mermaidDiv.innerHTML = "図の描画に失敗しました: " + e.message;
        }}
    }})();
    </script>
    """
    components.html(html_content, height=610)

def display_dependency_tree(tokens_info, sentence_id):
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

def get_chunk_color(chunk_type):
    return chunk_colors.get(chunk_type, '#808080') # Default to grey if not found

def display_chunk_tree(tokens_info, chunks_info, sentence_id):
    st.subheader("句構造ツリー")
    graph = graphviz.Digraph(comment='Chunk Tree', format='svg')
    graph.attr(rankdir='TB', overlap='false', compound='true') # 上から下へのレイアウト

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

    # --- デバッグ情報: 中間データ構造 ---
    with st.expander("句構造ツリー生成用中間データ (Graphviz版)"):
        st.markdown("#### `token_map` (トークンIDからトークン情報へのマッピング)")
        st.markdown("**使用目的**: 単語のIDをキーとして、その単語の全情報（テキスト、品詞、依存関係など）に素早くアクセスするために使用されます。")
        st.json(token_map)

        st.markdown("#### `chunk_dict` (チャンクIDからチャンク情報へのマッピング)")
        st.markdown("**使用目的**: チャンクを一意に識別するID（例: `NP_0_2`）をキーとして、そのチャンクの全情報（種類、テキスト、開始/終了IDなど）に素早くアクセスするために使用されます。")
        st.json(chunk_dict)

        st.markdown("#### `parent_map` (チャンクの親子関係)")
        st.markdown("**使用目的**: 各チャンクがどのチャンクに包含されているか（ネスト構造）を定義します。`{子チャンクID: 親チャンクID}`の形式で、ツリーの階層構造を構築するために使用されます。`parent_id`が`None`のチャンクはトップレベルのチャンクです。")
        st.json(parent_map)

    # --- レイアウトのための主要な句の特定 ---
    subject_np_id = None
    root_vp_id = None
    root_token_id = None

    # ROOTトークンとnsubjトークンを見つける
    for token in tokens_info:
        if token['is_root']:
            root_token_id = token['id']
        if token['dep'] == 'nsubj':
            # nsubjトークンを含むNPを探す
            for chunk_id, chunk in chunk_dict.items():
                if chunk['type'] == 'NP' and chunk['start_id'] <= token['id'] <= chunk['end_id']:
                    subject_np_id = chunk_id
                    break
        if root_token_id and subject_np_id: # 両方見つかったらループを抜ける
            break

    # ROOTトークンを含むVPを探す
    if root_token_id:
        for chunk_id, chunk in chunk_dict.items():
            if chunk['type'] == 'VP' and chunk['start_id'] <= root_token_id <= chunk['end_id']:
                root_vp_id = chunk_id
                break

    print(f"DEBUG: subject_np_id: {subject_np_id}")
    print(f"DEBUG: root_vp_id: {root_vp_id}")

    # ノードを追加
    for chunk_id, chunk in chunk_dict.items():
        color = get_chunk_color(chunk['type'])
        # heightとfixedsize='true'を追加
        graph.node(chunk_id, f"{chunk['type']}\n({chunk['text']})", style='filled', fillcolor=color, shape='box', height='0.8', width='1.5', fixedsize='true')

    # 単語ノードを追加 (どのチャンクにも属さないもの)
    token_in_chunk = {t['id']: False for t in tokens_info}
    for chunk in chunks_info:
        for i in range(chunk['start_id'], chunk['end_id'] + 1):
            if i in token_in_chunk:
                token_in_chunk[i] = True
    
    for token_id, is_in_chunk in token_in_chunk.items():
        if not is_in_chunk:
             graph.node(str(token_id), token_map[token_id]['text'], shape='plaintext')

    # --- トップレベルのチャンクのグループ化と順序付け ---
    # Sノードを追加
    graph.node("S", "S (Sentence)", shape='ellipse', style='filled', fillcolor='lightgoldenrod', rank='min')

    # 主要なNPとVPを同じグループに配置
    if subject_np_id and root_vp_id:
        # NPとVPを同じランクに配置するためのサブグラフ
        with graph.subgraph(name='cluster_np_vp') as c:
            c.attr(rank='same')
            c.node(subject_np_id, group='main_np_vp')
            c.node(root_vp_id, group='main_np_vp')
            # NPとVPの間に不可視のエッジを追加して順序を強制
            c.edge(subject_np_id, root_vp_id, style='invis', constraint='true')

        # SからNPへのエッジ (VPはNPに続くため、NPにのみ接続)
        graph.edge("S", subject_np_id)
    elif subject_np_id:
        graph.edge("S", subject_np_id)
    elif root_vp_id:
        graph.edge("S", root_vp_id)

    # その他のトップレベルチャンク
    for chunk_id, parent_id in parent_map.items():
        if parent_id is None and chunk_id != subject_np_id and chunk_id != root_vp_id:
            graph.edge("S", chunk_id)

    # エッジを追加 (既存のロジック)
    for chunk_id, parent_id in parent_map.items():
        if parent_id:
            graph.edge(parent_id, chunk_id)
        # Sノードへの接続は上記で処理済みなので、ここではスキップ
    
    # チャンクと単語のエッジを追加 (既存のロジック)
    for chunk_id, chunk in chunk_dict.items():
        current_tokens_ids = list(range(chunk['start_id'], chunk['end_id'] + 1))
        children_chunks = [cid for cid, pid in parent_map.items() if pid == chunk_id]
        
        for child_chunk_id in children_chunks:
            child_chunk = chunk_dict[child_chunk_id]
            for i in range(child_chunk['start_id'], child_chunk['end_id'] + 1):
                if i in current_tokens_ids:
                    current_tokens_ids.remove(i)
        
        for token_id in current_tokens_ids:
            token_data = token_map.get(token_id)
            if token_data:
                graph.node(str(token_id), token_data['text'], shape='plaintext')
                graph.edge(chunk_id, str(token_id))

    try:
        st.graphviz_chart(graph)
    except Exception as e:
        st.error(f"句構造ツリーの表示中にエラーが発生しました: {e}")

def display_mermaid_chunk_tree(tokens_info, chunks_info, sentence_id):
    st.subheader("句構造ツリー (Mermaid版)")
    mermaid_code = "graph TD\n" # Top-Down direction for overall tree

    token_map = {token['id']: token for token in tokens_info}
    chunk_dict = {f"{c['type']}_{c['start_id']}_{c['end_id']}": c for c in chunks_info}

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

    # --- デバッグ情報: 中間データ構造 (Mermaid版) ---
    with st.expander("句構造ツリー生成用中間データ (Mermaid版)"):
        st.markdown("#### `token_map` (トークンIDからトークン情報へのマッピング)")
        st.markdown("**使用目的**: 単語のIDをキーとして、その単語の全情報（テキスト、品詞、依存関係など）に素早くアクセスするために使用されます。")
        st.json(token_map)

        st.markdown("#### `chunk_dict` (チャンクIDからチャンク情報へのマッピング)")
        st.markdown("**使用目的**: チャンクを一意に識別するID（例: `NP_0_2`）をキーとして、そのチャンクの全情報（種類、テキスト、開始/終了IDなど）に素早くアクセスするために使用されます。")
        st.json(chunk_dict)

        st.markdown("#### `parent_map` (チャンクの親子関係)")
        st.markdown("**使用目的**: 各チャンクがどのチャンクに包含されているか（ネスト構造）を定義します。`{子チャンクID: 親チャンクID}`の形式で、ツリーの階層構造を構築するために使用されます。`parent_id`が`None`のチャンクはトップレベルのチャンクです。")
        st.json(parent_map)

    # --- レイアウトのための主要な句の特定 (Graphviz版から流用) ---
    subject_np_id = None
    root_vp_id = None
    root_token_id = None

    for token in tokens_info:
        if token['is_root']:
            root_token_id = token['id']
        if token['dep'] == 'nsubj':
            for chunk_id, chunk in chunk_dict.items():
                if chunk['type'] == 'NP' and chunk['start_id'] <= token['id'] <= chunk['end_id']:
                    subject_np_id = chunk_id
                    break
        if root_token_id and subject_np_id:
            break

    if root_token_id:
        for chunk_id, chunk in chunk_dict.items():
            if chunk['type'] == 'VP' and chunk['start_id'] <= root_token_id <= chunk['end_id']:
                root_vp_id = chunk_id
                break

    # Sノードの定義
    mermaid_code += "    S((Sentence))\n"

    # NPとVPの水平配置を試みるサブグラフ
    if subject_np_id and root_vp_id:
        mermaid_code += "    subgraph MainPhrases\n"
        mermaid_code += "        direction LR\n" # Left-Right direction for this subgraph
        mermaid_code += f"        {subject_np_id}[\"{chunk_dict[subject_np_id]['type']}<br>{chunk_dict[subject_np_id]['text']}\"]\n"
        mermaid_code += f"        {root_vp_id}[\"{chunk_dict[root_vp_id]['type']}<br>{chunk_dict[root_vp_id]['text']}\"]\n"
        mermaid_code += f"        {subject_np_id} --- {root_vp_id}\n" # NPからVPへの不可視エッジで順序を強制
        mermaid_code += "    end\n"
        mermaid_code += f"    S --> MainPhrases\n"
    elif subject_np_id:
        mermaid_code += f"    {subject_np_id}[\"{chunk_dict[subject_np_id]['type']}<br>{chunk_dict[subject_np_id]['text']}\"]\n"
        mermaid_code += f"    S --> {subject_np_id}\n"
    elif root_vp_id:
        mermaid_code += f"    {root_vp_id}[\"{chunk_dict[root_vp_id]['type']}<br>{chunk_dict[root_vp_id]['text']}\"]\n"
        mermaid_code += f"    S --> {root_vp_id}\n"

    # その他のチャンクノードとエッジ
    for chunk_id, chunk in chunk_dict.items():
        if chunk_id != subject_np_id and chunk_id != root_vp_id:
            mermaid_code += f"    {chunk_id}[\"{chunk['type']}<br>{chunk['text']}\"]\n"
            if parent_map[chunk_id] is None: # Top-level chunk not NP/VP
                mermaid_code += f"    S --> {chunk_id}\n"

    # 親子関係のエッジ
    for chunk_id, parent_id in parent_map.items():
        if parent_id and (chunk_id != subject_np_id and chunk_id != root_vp_id): # Avoid re-adding S->NP/VP edges
            mermaid_code += f"    {parent_id} --> {chunk_id}\n"

    # チャンクと単語のエッジ
    for chunk_id, chunk in chunk_dict.items():
        current_tokens_ids = list(range(chunk['start_id'], chunk['end_id'] + 1))
        children_chunks = [cid for cid, pid in parent_map.items() if pid == chunk_id]

        for child_chunk_id in children_chunks:
            child_chunk = chunk_dict[child_chunk_id]
            for i in range(child_chunk['start_id'], child_chunk['end_id'] + 1):
                if i in current_tokens_ids:
                    current_tokens_ids.remove(i)

        for token_id in current_tokens_ids:
            token_data = token_map.get(token_id)
            if token_data:
                # MermaidノードIDは数字から始まることができないため、プレフィックスを追加
                token_node_id = f"token_{token_id}"
                mermaid_code += f"    {token_node_id}[{token_data['text']}]\n"
                mermaid_code += f"    {chunk_id} --> {token_node_id}\n"

    html_content = f'''
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <div class="mermaid">
        {mermaid_code}
    </div>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
    '''
    components.html(html_content, height=800) # Adjust height as needed

def display_chunks(tokens, chunks, i):
    st.subheader("句構造の階層表示")
    display_chunk_tree(tokens, chunks, i)

    st.markdown("---")
    st.markdown("#### 検出された句の一覧 (ネスト構造):")
    
    # 句のネストレベルを計算して表示
    nested_chunks = []
    for i, chunk in enumerate(chunks):
        nesting_level = 0
        for other_chunk in chunks:
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
        st.sidebar.markdown(f"<span style='color: {color};'>■</span> {analyzer.pos_map.get(pos, pos)} ({pos})", unsafe_allow_html=True)
    
    st.sidebar.markdown("#### 句構造 (Chunk)")
    for chunk_type, color in chunk_colors.items():
        japanese_name = chunk_type_japanese_map.get(chunk_type, chunk_type).split('(')[0].strip()
        st.sidebar.markdown(f"<span style='background-color: {color}; padding: 2px 5px; border-radius: 3px;'>&nbsp;&nbsp;&nbsp;</span> {japanese_name} ({chunk_type})", unsafe_allow_html=True)


# --- 4. Streamlitアプリのメイン部分 ---
st.set_page_config(layout="wide", page_title="英文解析ツール")

# セッション状態の初期化
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

st.title("英文解析ツール")

input_text = st.text_area("解析したい英文を入力してください:", "The quick brown fox jumps over the lazy dog. A young boy is running quickly in the park. My diligent sister has been studying English very hard. All the students will go to the store to buy some groceries. Dr. Smith visited Tokyo on July 23rd, 2025 to attend a conference organized by Google.", height=100)

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

        with st.expander(f"文 {i+1} のデバッグ情報 (tokens_info & chunks_info)"):
            st.markdown("#### トークン情報 (tokens_info)")
            st.markdown('''
**利用目的**: このデータは、文を構成する個々の単語（トークン）に関する詳細な言語的特徴を保持します。構文解析のすべてのステップで基礎情報として利用されます。
- **text**: トークンの元々のテキスト。
- **lemma**: トークンの見出し語（基本形）。
- **pos**: Universal POSタグ（言語に依存しない品詞）。
- **pos_japanese**: 日本語に翻訳されたPOSタグ。
- **tag**: 詳細なPOSタグ（言語固有）。
- **dep**: 依存関係ラベル。
- **dep_japanese**: 日本語に翻訳された依存関係ラベル。
- **head_id**: 依存関係の親となるトークンのID。
- **children_ids**: 依存関係の子となるトークンのIDのリスト。
- **id**: 文中でのトークンの一意なID。
- **start**: 文全体におけるトークンの開始位置。
- **end**: 文全体におけるトークンの終了位置。
- **is_root**: トークンが依存関係の根（ROOT）であるかどうかの真偽値。
''')
            st.markdown("品詞（POS）、依存関係（どの単語がどの単語を修飾しているか）、見出し語（単語の基本形）などが含まれており、構文解析のすべてのステップで基礎情報として利用されます。")
            processed_tokens_info = []
            for token in tokens:
                processed_tokens_info.append({
                    "単語 (text)": token['text'],
                    "見出し語 (lemma)": token['lemma'],
                    "ID (id)": token['id'],
                    "品詞 (pos)": f"{token['pos_japanese']} ({token['pos']})",
                    "詳細品詞 (tag)": token['tag'],
                    "依存関係 (dep)": f"{token['dep_japanese']} ({token['dep']})",
                    "親単語ID (head_id)": token['head_id'],
                    "子単語ID (children_ids)": token['children_ids'],
                    "文のROOT (is_root)": token['is_root'],
                    "開始位置 (start)": token['start'],
                    "終了位置 (end)": token['end'],
                    "形態素 (morph)": token['morph'],
                    "形態素_日本語訳 (morph_japanese)": token['morph_japanese'],
                    "固有表現タイプ (ent_type)": f"{token['ent_type_japanese']} ({token['ent_type']})",
                    "固有表現タイプ_日本語訳 (ent_type_japanese)": token['ent_type_japanese'],
                    "固有表現の一部 (is_entity_part)": token['is_entity_part'],
                    "固有表現テキスト (entity_text)": token['entity_text'],
                    "固有表現タイプ (entity_type)": token['entity_type']
                })
            st.json(processed_tokens_info)

            st.markdown("#### チャンク情報 (chunks_info)")
            st.markdown('''
**利用目的**: このデータは、文法的な単位である「句（チャンク）」を定義します。この情報は、句構造ツリーを構築するための直接的なインプットとなります。
- **type**: チャンクの種類（例: NP, VP, PP）。
- **text**: チャンクに含まれるテキスト全体。
- **start_id**: チャンクを構成する最初のトークンのID。
- **end_id**: チャンクを構成する最後のトークンのID。
- **start**: 文全体におけるチャンクの開始文字位置。
- **end**: 文全体におけるチャンクの終了文字位置。
''')
            st.markdown("例えば、「The quick brown fox」のような名詞句（NP）や「jumps over the lazy dog」のような動詞句（VP）を特定します。この情報は、句構造ツリーを構築するための直接的なインプットとなります。")
            processed_chunks_info = []
            for chunk in chunks:
                processed_chunks_info.append({
                    "句の種類": f"{chunk_type_japanese_map.get(chunk['type'], '不明')} ({chunk['type']})",
                    "テキスト": chunk['text'],
                    "開始ID": chunk['start_id'],
                    "終了ID": chunk['end_id']
                })
            st.json(processed_chunks_info)

        st.markdown("---")
        st.header("1. 品詞情報")

        show_detailed_pos = st.checkbox(f"文 {i+1} の詳細な品詞を表示 (クリックで詳細)", value=False, key=f"detailed_pos_{i}")
        if show_detailed_pos:
            display_tokens_detailed(tokens)
        else:
            display_tokens_default(tokens)
        
        st.markdown("---")
        st.header("2. 依存関係解析")
        display_dependency_tree(tokens, i)
        display_mermaid_dependency_tree(tokens, i)

        st.markdown("---")
        st.header("3. 句構造解析")
        display_chunks(tokens, chunks, i)
        display_mermaid_chunk_tree(tokens, chunks, i)

        # 期待される句構造のデバッグ表示 (該当する文のみ表示)
        if i < len(expected_chunks_data):
            display_expected_chunks([expected_chunks_data[i]])
        st.markdown("---<br>---") # 各文の区切りを明確にする


st.sidebar.markdown("### アプリケーション情報")
st.sidebar.info("このツールはSpaCyライブラリを使用して英文の品詞、依存関係、句構造を解析し、視覚的に表示します。")
st.sidebar.markdown("---")

# 色分け凡例の呼び出し
display_color_legend()


st.sidebar.markdown("### 品詞の解説")
for pos_tag, description in analyzer.pos_map.items():
    st.sidebar.markdown(f"- **{description} ({pos_tag})**")
st.sidebar.markdown("---")
st.sidebar.markdown("### 形態素情報 (Morphological Features) の解説")
for morph_tag, description in analyzer.morph_map.items():
    st.sidebar.markdown(f"- **{description} ({morph_tag})**")
st.sidebar.markdown("---")
st.sidebar.markdown("### 句構造の解説")
st.sidebar.markdown("- **名詞句 (NP)**: 名詞を中心に構成される句。文の主語や目的語になることが多いです。例: `The quick brown fox`")
st.sidebar.markdown("- **動詞句 (VP)**: 動詞を中心に構成される句。動詞とその目的語、補語、副詞などが含まれます。例: `jumps over the lazy dog`")
st.sidebar.markdown("- **前置詞句 (PP)**: 前置詞とそれに続く名詞句で構成される句。場所、時間、方法などを表します。例: `over the lazy dog`")
st.sidebar.markdown("- **副詞句 (ADVP)**: 副詞を中心に構成される句。動詞、形容詞、他の副詞を修飾します。例: `very quickly`")
st.sidebar.markdown("---")
st.sidebar.markdown("### 依存関係の解説")
for dep_tag, description in analyzer.dep_map.items():
    st.sidebar.markdown(f"- **{description} ({dep_tag})**")
st.sidebar.markdown("---")
st.sidebar.markdown("### 固有表現 (Named Entity) の解説")
for ent_type, description in analyzer.ent_type_map.items():
    st.sidebar.markdown(f"- **{description} ({ent_type})**")
st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 英文解析プロジェクト")