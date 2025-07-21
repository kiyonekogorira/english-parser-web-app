# 英文構造解析アプリ - 実装計画書 (MVP)

## 1. 目標 (Goal)

**spaCyとStreamlitを使用し、入力された英文の構造を視覚的に解析するMVP（Minimum Viable Product）を構築する。**

具体的には、以下の機能を提供する。
- **品詞 (POS):** 単語を品詞ごとに色分けし、クリックで詳細情報を表示する。
- **依存関係 (Dependency):** 単語間の依存関係をツリー形式で可視化する。
- **句構造 (Chunk):** 名詞句(NP)、動詞句(VP)、前置詞句(PP)、副詞句(ADVP)を背景色でハイライトする。

---

## 2. 最終データモデル (Data Model)

`analyze_sentence`関数は、以下の構造を持つ単一の辞書を返す。

```python
{
    'tokens': [
        {
            'id': int,           # 単語のインデックス
            'text': str,         # 単語テキスト
            'lemma': str,        # 原形
            'pos': str,          # 汎用品詞 (U-POS)
            'tag': str,          # 詳細品詞 (X-POS)
            'dep': str,          # 依存関係タイプ
            'head_id': int,      # 親単語のID
            'children_ids': list[int], # 子単語IDのリスト
            'is_root': bool      # ROOT単語か
        },
        # ...
    ],
    'chunks': [
        {
            'type': str,         # 句のタイプ (NP, VP, PP, ADVP)
            'text': str,         # 句のテキスト
            'start_id': int,     # 開始単語のID
            'end_id': int        # 終了単語のID
        },
        # ...
    ]
}
```

---

## 3. 実装する主要関数リスト (Functions)

- `load_spacy_model()`: spaCyモデル (`en_core_web_sm`) をロードし、`@st.cache_resource`でキャッシュする。
- `analyze_sentence(text: str) -> dict`: テキストを解析し、上記データモデルの辞書を返す。**NP, VP, PP, ADVPの抽出ロジックを含む。**
- `get_pos_color(pos_tag: str) -> str`: 品詞に対応する色を返す。
- `display_tokens_default(tokens_info: list)`: 品詞を色分けしたHTMLを `st.markdown` で表示する。
- `display_tokens_detailed(tokens_info: list)`: `st.popover` を使い、各単語の詳細情報（品詞、依存関係など）を表示する。
- `display_dependency_tree(tokens_info: list)`: `graphviz` を使い、依存関係ツリーを構築し `st.graphviz_chart` で表示する。ROOTノードやnsubj等の重要な関係は強調表示する。
- `get_chunk_color(chunk_type: str) -> str`: 句の種類に対応する背景色を返す。
- `display_chunks(tokens_info: list, chunks_info: list)`: 句を背景色でハイライトしたHTMLを `st.markdown` で表示する。**ネストした句の表示も考慮する。**

---

## 4. UIレイアウト (UI Layout)

**メインエリア:**
1.  `st.title("英文解析ツール")`
2.  `st.text_area("解析したい英文を入力してください:", ...)`
3.  `st.button("解析実行")`
4.  `st.header("1. 品詞情報")`
5.  `st.checkbox("詳細な品詞を表示 (クリックで詳細)")`
    -   チェック状態に応じて `display_tokens_default` または `display_tokens_detailed` を呼び出す。
6.  `st.header("2. 依存関係解析")`
    -   `display_dependency_tree` の結果を表示する。
7.  `st.header("3. 句構造解析")`
    -   `display_chunks` の結果を表示する。
    -   検出された句の一覧も表示する。

**サイドバー:**
- `st.sidebar.info("このツールは...")`
- `st.sidebar.markdown("© 2025 英文解析プロジェクト")`

---

## 5. 実装ステップ (Implementation Steps)

- [ ] **1. 環境設定:**
    - [ ] `requirements.txt` に `streamlit`, `spacy`, `graphviz` を記述する。
    - [ ] `python -m spacy download en_core_web_sm` を実行する (READMEにも記載)。

- [ ] **2. `app.py` の基本構造作成:**
    - [ ] 必要なライブラリをインポートする。
    - [ ] `load_spacy_model` 関数を実装する。
    - [ ] UIレイアウトの骨格を配置する。

- [ ] **3. 解析ロジックの実装 (`analyze_sentence`):**
    - [ ] `TokenInfo` リストを作成する。
    - [ ] `ChunkInfo` リストを作成する。
        - [ ] **名詞句 (NP):** `doc.noun_chunks` を利用して抽出する。
        - [ ] **動詞句 (VP):** `ROOT`動詞とその子 (`aux`, `dobj`等) をグループ化する簡易ロジックを実装する。
        - [ ] **前置詞句 (PP):** `ADP` (前置詞) とその `pobj` (目的語) をグループ化する簡易ロジックを実装する。
        - [ ] **副詞句 (ADVP):** `ADV` (副詞) を中心に関連語をグループ化する簡易ロジックを実装する。
    - [ ] 最終的な辞書を返す。

- [ ] **4. 表示関数の実装:**
    - [ ] `get_pos_color` と `display_tokens_default` を実装する。
    - [ ] `display_tokens_detailed` を実装する。
    - [ ] `display_dependency_tree` を実装する。
        - [ ] `graphviz.Digraph` オブジェクトを初期化する。
        - [ ] 全トークンをノードとして追加する (`is_root`がTrueのノードは色を変える)。
        - [ ] 全トークンの `head_id` を参照してエッジを追加する。
        - [ ] エッジに `dep` ラベルを付ける (`nsubj` など特定のラベルは色を変える)。
    - [ ] `get_chunk_color` と `display_chunks` を実装する。
        - [ ] 各単語に適用すべき背景色を決定するロジックを実装する（ネストを考慮し、最も内側の句を優先）。
        - [ ] `<span>` タグと `background-color` を使ってHTMLを生成する。
        - [ ] 検出された句の一覧を `st.markdown` で表示する。

- [ ] **5. 全体の連携:**
    - [ ] 「解析実行」ボタンが押されたら `analyze_sentence` を呼び出す。
    - [ ] 解析結果を各 `display_` 関数に渡し、結果を画面に表示させる。
    - [ ] `st.spinner` を追加して、解析中の待機状態を示す。
