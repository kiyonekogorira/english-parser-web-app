プロジェクト名: 英文構造解析Webアプリ - 開発タスクリスト
1. 環境構築と初期設定
[ ] プロジェクトリポジトリの作成と初期コミット
[ ] requirements.txt に streamlit, spacy (または nltk) を追加
[ ] app.py ファイルの作成とStreamlitアプリの初期起動確認
[ ] spaCyモデルのダウンロード (python -m spacy download en_core_web_sm)

2. コア機能の実装 - テキスト入力と基本表示
[ ] テキスト入力エリア (st.text_area) の設置
[ ] 解析実行ボタン (st.button) の設置
[ ] 解析結果表示用のプレースホルダー (st.empty) の設置
[ ] クリアボタン (st.button) の設置とロジック実装

3. 英文解析ロジックの実装
[ ] SentenceAnalyzer クラス/関数のスケルトン作成
[ ] spaCy (またはNLTK) を用いた英文のロードと基本解析 (nlp(text))
[ ] 主語と動詞の特定ロジックの実装 (spaCyの依存関係解析 token.dep_ == 'nsubj' などを使用)
[ ] 名詞句、動詞句、前置詞句の特定ロジックの実装 (spaCyの doc.noun_chunks や依存関係ツリーのトラバースを使用)
[ ] 解析結果を構造化されたデータ（例: 辞書やリスト）として返すように実装

4. 解析結果の表示ロジックの実装
[ ] ResultFormatter クラス/関数のスケルトン作成
[ ] 主語と動詞を色付けするHTML/Markdown生成ロジックの実装
例: <span style="color: #FF5733;">主語</span> <span style="color: #337AFF;">動詞</span>
[ ] 句を括弧で囲むHTML/Markdown生成ロジックの実装
例: [NP <span style="background-color:#E0FFFF;">...</span>]
[ ] 生成されたHTML/Markdownを st.markdown(..., unsafe_allow_html=True) で表示
[ ] 複数の句が入れ子になる場合の表示ロジックの検討と実装

5. UI/UXの改善とエラーハンドリング
[ ] 解析中のローディング表示 (st.spinner)
[ ] 無効な入力（空文字列など）に対するエラーメッセージ表示
[ ] 解析に失敗した場合のユーザーフレンドリーなメッセージ表示
[ ] レスポンシブデザインの確認と調整
[ ] CSSによる表示スタイルの微調整（括弧の色、背景色など）

6. 全体統合とテスト
[ ] 各コンポーネントの統合と連携確認
[ ] 様々な英文パターン（短文、長文、複雑な構文）でのテスト
[ ] 主語、動詞、句の特定精度に関するテストと改善
[ ] パフォーマンス測定とボトルネックの特定、改善

7. デプロイ
[ ] requirements.txt の最終化
[ ] Streamlit Community Cloud へのデプロイ