プロジェクト名: 英文構造解析Webアプリ
1. 技術的なアーキテクチャ
Streamlitアプリケーション: すべてのUIと基本的なロジックをPythonとStreamlitで実装する。
自然言語処理 (NLP) ライブラリ: 英文解析の中核として、spaCyまたはNLTKなどのPython NLPライブラリを利用する。特に構文解析（Dependency Parsing / Constituency Parsing）機能が重要となる。
表示ロジック: 解析結果（句の範囲、主語/動詞の位置）に基づいて、元のテキストをHTML/Markdown形式で整形し、Streamlitのst.markdownで表示する。カスタムCSSで色付けや括弧のスタイルを適用する。

2. 使用する技術スタック候補
フレームワーク: Streamlit
言語: Python
NLPライブラリ: spaCy (高性能な構文解析モデルが利用可能) または NLTK (より低レベルな制御が可能)
UI/UX: Streamlitの標準ウィジェット、カスタムCSS (st.markdownで埋め込み)
デプロイ: Streamlit Community Cloud / Render / Heroku など

3. 主要なコンポーネントとその役割 (Streamlitのセクション/関数/ウィジェットとして)
メインアプリ (app.py):
役割: アプリケーション全体のレイアウト、テキスト入力エリア、解析結果表示エリアの制御。
Streamlitウィジェット: st.text_area, st.button, st.empty (結果表示用)

SentenceAnalyzer クラス/関数:
役割: 入力された英文を受け取り、NLPライブラリを用いて構文解析を実行する。名詞句、動詞句、主語、動詞などの情報を抽出する。
依存関係解析 (Dependency Parsing) または句構造解析 (Constituency Parsing) を利用する。

ResultFormatter クラス/関数:
役割: SentenceAnalyzerから得られた解析結果（句の開始/終了位置、主語/動詞の位置）を基に、元の英文をHTML/Markdown形式の文字列に変換する。
例: <span style="color:red;">Subject</span> <span style="color:blue;">Verb</span> [NP ... ] (VP ... )

SessionStateManagement:
役割: ユーザーの入力テキストや解析結果をセッション間で保持する必要がある場合、st.session_stateを利用する。

4. データモデルの概要 (Streamlitのセッションステート内)
st.session_state['input_text']: string (ユーザーが入力した英文)
st.session_state['parsed_result']: dict (解析結果を格納。例: {'subject_span': (start, end), 'verb_span': (start, end), 'phrases': [{'type': 'NP', 'span': (start, end)}, ...]})
st.session_state['display_html']: string (整形されたHTML/Markdown文字列)

5. NLPライブラリの選定とモデル
spaCyを使用する場合: en_core_web_sm (または md/lg モデル) を利用し、doc.noun_chunks, doc.ents, doc.dep_ (依存関係) などを活用して句や主語/動詞を特定する。
NLTKを使用する場合: nltk.pos_tag, nltk.chunk.regexp.RegexpParser や nltk.tree.Tree を用いて句構造を解析する。