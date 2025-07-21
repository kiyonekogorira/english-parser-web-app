# 英文構文解析・強調表示 Web アプリ - 設計書

## 1. 技術的なアーキテクチャ

### 1.1. 全体構成
* **Streamlitアプリケーション:** すべてのUIとロジックをPythonとStreamlitで実装する。
* **NLPライブラリ:** 自然言語処理（NLP）の中核としてspaCyを使用し、英文の構文解析、品詞タグ付け、固有表現認識（必要に応じて）を行う。
* **バックエンド処理:** StreamlitのサーバーサイドでspaCyモデルをロードし、入力された英文の解析を実行する。解析結果はHTML形式に整形され、Streamlitの`st.markdown`機能で表示される。

## 2. 使用する技術スタック

*   **フレームワーク:** Streamlit
*   **言語:** Python
*   **NLPライブラリ:** spaCy (英語モデル 'en_core_web_sm' または 'en_core_web_md')
*   **UI/UX:** Streamlitの標準ウィジェット、および`st.markdown`でカスタムCSSを適用し、名詞句・動詞句の括弧表示や主語・動詞の色付けを実現する。
*   **デプロイ:** Streamlit Community Cloud / Render / Heroku など

## 3. 主要なコンポーネントとその役割

### 3.1. メインアプリ (`app.py`)
*   **役割:** アプリケーション全体のレイアウト、テキスト入力エリア、解析実行ボタン、結果表示エリアを制御する。**オンボーディング、ヘルプ、フィードバックメッセージの表示も担当する。**
*   **Streamlitウィジェット:** `st.text_area`, `st.button`, `st.markdown`, `st.empty` (結果表示用)

### 3.2. `SentenceAnalyzer` クラス/ロジック
*   **役割:** spaCyモデルのロード、入力テキストの解析、品詞タグ、依存関係、句構造を抽出する。
*   **詳細:** spaCyの`Doc`オブジェクトを利用して、以下の構文情報を抽出する。
    *   **品詞タグ (POS Tag):** 各単語の `token.pos_` (Universal POS tags) と `token.tag_` (Treebank-style POS tags) を取得する。
    *   **依存関係 (Dependency Parsing):** 各単語の `token.dep_` (依存関係タイプ)、`token.head` (親単語)、`token.children` (子単語) を利用する。
    *   **句構造 (Phrase Structure):**
        *   **名詞句 (NP):** `doc.noun_chunks` を使用して抽出する。
        *   **動詞句 (VP):** 文のROOT動詞 (`token.dep_ == "ROOT"`) を核とし、助動詞 (`aux`, `auxpass`)、目的語 (`dobj`, `iobj`)、補語 (`attr`, `acomp`, `pcomp`)、副詞 (`advmod`) などを再帰的に辿り、グループ化するカスタムロジックを実装する。
        *   **前置詞句 (PP):** `token.pos_ == "ADP"` (前置詞) を特定し、その `pobj` (前置詞の目的語) とその子孫を再帰的に含めてグループ化するカスタムロジックを実装する。
        *   **副詞句 (ADVP):** `token.pos_ == "ADV"` (副詞) を核とし、関連する単語をグループ化するカスタムロジックを実装する。

### 3.3. `ResultFormatter` クラス/ロジック
*   **役割:** `SentenceAnalyzer`で得られた構造化データを、ユーザーに視覚的に分かりやすいHTML/Markdown形式に整形する。
*   **詳細:**
    *   句 (NP, VP, PP, ADVP) に括弧や背景色を適用する処理。
    *   特定の品詞（例: 動詞）や依存関係（例: 主語）に特定のCSSスタイル（色）を適用するためのHTMLタグを挿入する処理。
    *   **句のネスト表示の改善**: ネストの深さに応じた括弧の種類や色、インデントなどを考慮した表示ロジック。
    *   **視覚表現の多様性**: 色付けだけでなく、太字、下線、背景色など、複数の強調スタイルを組み合わせるオプションに対応するためのロジック。

### 3.4. UIウィジェット
*   `st.text_area`: ユーザーが英文を入力するための複数行テキストエリア。**入力バリデーション（英文判定など）のフィードバック表示も考慮する。**
*   `st.button`: 「解析実行」ボタンと「クリア」ボタン。
*   `st.markdown`: 解析された結果（HTML形式）を表示するためのエリア。`unsafe_allow_html=True` を使用する。**インタラクティブな表示（マウスオーバー時のツールチップなど）や表示オプション（表示レベル、元の文との切り替え）に対応するための拡張を検討する。**

## 4. 解析結果の内部データモデル

解析結果は、UI表示や解説生成に利用しやすいように、以下の構造を持つ辞書として `st.session_state` に保持する。

*   `st.session_state['analysis_result']`: `dict`
    *   `'tokens'`: `list[TokenInfo]` - 単語情報のリスト
    *   `'chunks'`: `list[ChunkInfo]` - 句構造情報のリスト

### 4.1. TokenInfo (単語情報)

| キー           | 型          | 説明                                         |
|----------------|-------------|----------------------------------------------|
| `id`           | `int`       | ドキュメント内での単語のインデックス (token.i) |
| `text`         | `str`       | 単語のテキスト (token.text)                  |
| `lemma`        | `str`       | 単語の原形 (token.lemma_)                    |
| `pos`          | `str`       | Universal POS タグ (token.pos_)              |
| `tag`          | `str`       | Treebank-style POS タグ (token.tag_)         |
| `dep`          | `str`       | 依存関係タイプ (token.dep_)                  |
| `head_id`      | `int`       | 親単語のID (token.head.i)                    |
| `children_ids` | `list[int]` | 子単語のIDのリスト                           |
| `is_root`      | `bool`      | この単語が文のROOTであるか                   |

### 4.2. ChunkInfo (句構造情報)

| キー         | 型     | 説明                               |
|--------------|--------|------------------------------------|
| `type`       | `str`  | 句のタイプ (NP, VP, PP, ADVP)      |
| `text`       | `str`  | 句全体のテキスト                   |
| `start_id`   | `int`  | 句の開始単語のID (chunk.start)     |
| `end_id`     | `int`  | 句の終了単語のID (chunk.end - 1)   |

## 5. JavaScript連携の可能性

*   **現時点:** StreamlitとPython/spaCyの機能で要件を満たすことが可能であり、JavaScript連携は必須ではない。
*   **将来的な検討:** より高度なインタラクティブな表示（例: マウスオーバーで品詞や依存関係の詳細を表示）が必要になった場合に、Streamlit Custom Components を用いたJavaScript連携を検討する。

## 6. コード構造と品質

*   **モジュール化**: `SentenceAnalyzer`や`ResultFormatter`などのクラスを独立したPythonファイルに分割し、`app.py`はUIとメインロジックに徹する。
*   **コーディング規約**: PEP 8に準拠し、`Black`、`isort`、`Flake8`などのツールを導入してコード品質を維持する。
*   **テスト**: `pytest`を用いたユニットテストを導入し、主要なロジックの動作を保証する。
