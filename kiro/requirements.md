# 英文構文解析・強調表示 Web アプリ - 要件定義

## 1. プロジェクト概要

### 1.1. 目標
英文の構造を視覚的に理解しやすくするツールを提供する。特に、名詞句、動詞句の識別、主語・動詞の強調表示を通じて、英語学習者や言語分析に関心のあるユーザーを支援する。

### 1.2. 課題
* 自然言語処理（NLP）の複雑なロジックを、専門知識のないユーザーでも直感的に利用できる形で提供すること。
* 入力された英文に対して、正確な構文解析と品詞タグ付けを実現すること。
* 解析結果を、視覚的に分かりやすく、かつ読みやすい形式で表示する方法を確立すること。
* Webアプリケーションとして、特別な環境設定なしに手軽に利用・デプロイできること。

## 2. 機能要件

### 2.1. テキスト入力機能
* ユーザーが英文を自由に入力できるテキストエリアを提供する。
* 複数行の入力、およびある程度の長さの文章（例: 数段落）に対応する。
* **入力のバリデーションとフィードバック**: 入力が英文であることをある程度検証し、不適切な入力に対して具体的なフィードバック（例: 「英語の文章を入力してください」）を提供する。
* **関連タスク (既存ロードマップより):**
    * テキスト入力エリア (st.text_area) の設置

### 2.2. 構文解析機能
* 入力された英文を解析し、名詞句 (NP)、動詞句 (VP) などの主要な句構造を識別し、それぞれを括弧で囲んで表示する。
* 品詞タグ付け (POS tagging) の結果を内部的に利用し、必要に応じて表示オプションを提供する（初期フェーズでは表示不要）。
* **複雑な構文への対応**: 関係代名詞節、分詞構文、不定詞句、動名詞句、比較構文など、より複雑な英文構造も可能な限り正確に解析する。
* **複数文の扱い**: 入力されたテキストが複数の文で構成される場合、文ごとに分割して解析し、結果を提示する。
* **関連タスク (既存ロードマップより):**
    * SentenceAnalyzer クラス/関数のスケルトン作成
    * spaCyを用いた英文のロードと基本解析 (nlp(text))
    * 名詞句、動詞句、前置詞句の特定ロジックの実装 (spaCyの doc.noun_chunks や依存関係ツリーのトラバースを使用)
    * 解析結果を構造化されたデータ（例: 辞書やリスト）として返すように実装

### 2.3. 主語・動詞強調表示機能
* 解析された文の中から、主語と動詞を正確に特定し、それぞれ異なる色で強調表示する。
* 複数の節（句）を含む複雑な文においても、各節の主語と動詞を適切に識別し、強調表示する。
* **視覚表現の多様性**: 色付けだけでなく、太字、下線、背景色など、複数の強調スタイルを組み合わせるオプションを提供する。
* **関連タスク (既存ロードマップより):**
    * 主語と動詞の特定ロジックの実装 (spaCyの依存関係解析 token.dep_ == 'nsubj' などを使用)
    * 主語と動詞を色付けするHTML/Markdown生成ロジックの実装

### 2.4. 結果表示機能
* 解析結果（括弧で囲まれた句、色付けされた主語・動詞）を、元の文の構造を保ちつつ、整形された形で表示する。
* 元の文と解析結果を並べて表示する、または切り替えて表示するオプションを提供する。
* **インタラクティブ性**: 強調表示された要素にマウスオーバーした際に、その要素の品詞、依存関係、詳細な文法情報などをツールチップで表示する。
* **表示オプションとダウンロード**: 解析結果の表示レベル（例: 主語・動詞のみ、名詞句のみ、全て）を選択できるオプションや、HTML、プレーンテキスト、JSON形式でのダウンロード機能を提供する。
* **関連タスク (既存ロードマップより):**
    * 解析結果表示用のプレースホルダー (st.empty) の設置
    * ResultFormatter クラス/関数のスケルトン作成
    * 句を括弧で囲むHTML/Markdown生成ロジックの実装
    * 生成されたHTML/Markdownを st.markdown(..., unsafe_allow_html=True) で表示
    * 複数の句が入れ子になる場合の表示ロジックの検討と実装

### 2.5. クリア/リセット機能
* 入力テキストエリアと解析結果表示を一度にクリアし、初期状態に戻すボタンを提供する。
* **関連タスク (既存ロードマップより):**
    * クリアボタン (st.button) の設置とロジック実装

## 3. 非機能要件

### 3.1. パフォーマンス
* 解析処理が、入力されたテキストの長さにもよるが、数秒以内（例: 100文字あたり1秒以内）に完了し、結果が表示されること。
* アプリケーションの応答性が高く、操作がスムーズであること。
* **長文解析時の最適化**: 大量のテキストが入力された場合でも、処理時間が許容範囲内であること。
* **関連タスク (既存ロードマップより):**
    * パフォーマンス測定とボトルネックの特定、改善 (100文字程度の英文であれば、解析から表示まで3秒以内に完了すること)

### 3.2. UI/UX
* 解析結果が視覚的に分かりやすく、読みやすい形式で表示されること。括弧と色付けが明確に区別できること。
* 直感的で、初めてのユーザーでも迷わず利用できること。
* レスポンシブデザインが適切か、異なる画面サイズで確認できること。
* CSSによる表示スタイルの微調整（括弧の色、背景色など）が可能であること。
* **アクセシビリティ**: 色覚多様性を持つユーザーのために、色のコントラストや代替テキストを考慮すること。
* **オンボーディングとヘルプ**: 初めてのユーザーが迷わず利用できるよう、簡単なチュートリアルやヘルプ機能を提供する。
* **フィードバックの強化**: ユーザーのアクション（解析完了、エラーなど）に対して、明確で分かりやすいメッセージを表示する。
* **関連タスク (既存ロードマップより):**
    * レスポンシブデザインの確認と調整
    * CSSによる表示スタイルの微調整（括弧の色、背景色など）

### 3.3. 精度
* 一般的な単文、複文、重文において、名詞句、動詞句がspaCyのデフォルトモデルの精度に準拠して正確に括弧で囲まれること。
* 解析された文の主語と動詞が、高い精度（例: 90%以上）で正しく識別され、指定された色で表示されること。
* 複数の主語・動詞が存在する場合（例: 複合文）でも、それぞれが適切に強調表示されること。
* **複雑な構文の解析精度**: 関係代名詞節、分詞構文、不定詞句、動名詞句、比較構文など、より複雑な英文構造に対しても高い解析精度を維持すること。
* **関連タスク (既存ロードマップより):**
    * 主語、動詞、句の特定精度に関するテストと改善
    * 受け入れ基準: 一般的な英文において、主語と動詞を90%以上の精度で、名詞句、動詞句、前置詞句を80%以上の精度で正確に識別できること。
    * 受け入れ基準: 解析結果が元の英文と対応付けられ、視覚的に分かりやすく表示されること。主語と動詞の色付けが明確で、視認性が高いこと。句の括弧表示が正確で、入れ子構造も正しく表現されること。

### 3.4. デプロイ・環境
* Webアプリケーションとして、特別な環境設定なしに手軽に利用・デプロイできること。
* **関連タスク (既存ロードマップより):**
    * Streamlit Community Cloud へのデプロイ
    * requirements.txt の最終化

### 3.5. コード品質と保守性
* **モジュール化**: コードが適切にモジュール化され、各コンポーネントが独立して機能すること。
* **コーディング規約**: PEP 8などの標準的なコーディング規約に準拠し、コードの一貫性が保たれていること。
* **テスト容易性**: 各コンポーネントがテストしやすいように設計されていること。
* **関連タスク (新規):**
    * モジュール化とファイル分割
    * コーディング規約と静的解析ツールの導入
    * ユニットテストの作成

### 3.6. その他
* 任意の長さの英文（例: 最大500文字程度）がスムーズに入力でき、表示崩れがないこと。
* クリア/リセット機能が瞬時に動作し、入力と表示が完全に初期化されること。
* 解析に失敗した場合のユーザーフレンドリーなメッセージ表示。
* 無効な入力（空文字列など）に対するエラーメッセージ表示。
