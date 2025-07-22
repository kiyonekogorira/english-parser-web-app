# 英文構文解析・強調表示 Web アプリ - 開発タスクリスト

## 1. 環境構築と初期設定

*   [ ] プロジェクトリポジトリの作成と初期コミット
*   [ ] `requirements.txt` に `streamlit` と `spacy` を追加
*   [ ] `app.py` ファイルの作成とStreamlitアプリの初期起動確認
*   [ ] spaCy英語モデルのダウンロードコマンドの実行 (例: `python -m spacy download en_core_web_sm`)
*   [ ] `.streamlit/config.toml` でテーマ設定（任意）
*   [ ] **Black, isort, Flake8/Ruff などの静的解析ツールの導入と設定**

## 2. コア機能の実装

### 2.1. UIのスケルトン作成
*   [ ] `st.text_area` で英文入力ボックスを配置
*   [ ] `st.button` で「解析実行」ボタンと「クリア」ボタンを配置
*   [ ] `st.empty` または `st.markdown` で解析結果表示用のプレースホルダーを配置

### 2.2. spaCyモデルのロードロジックの実装
*   [ ] アプリ起動時に一度だけspaCyモデルをロードする (`st.cache_resource` を利用)

### 2.3. テキスト解析ロジックの実装
*   [ ] 入力テキストをspaCyで処理し、`Doc`オブジェクトを生成する関数を作成
*   [ ] `Doc`オブジェクトから名詞句 (`doc.noun_chunks`) と動詞句を識別するロジックを実装
*   [ ] `Doc`オブジェクトから主語 (`token.dep_ == 'nsubj'`) と動詞 (`token.pos_ == 'VERB'`) を特定するロジックを実装
*   [ ] **複数文の分割と各文の解析ロジックを実装**
*   [ ] **複雑な構文パターン（関係代名詞節、分詞構文など）への対応ロジックを実装**

## 3. 結果表示ロジックの実装

### 3.1. 括弧表示のロジック
*   [ ] 名詞句、動詞句の`Span`オブジェクトから、元のテキストに括弧を挿入した文字列を生成する関数を作成
*   [ ] **句のネスト（入れ子構造）を考慮した括弧表示ロジックを実装**

### 3.2. 主語・動詞の色付けロジック
*   [ ] 特定された主語と動詞のトークンをHTMLの `<span>` タグで囲み、カスタムCSSクラスを適用する関数を作成
*   [ ] **色付け以外の強調スタイル（太字、下線、背景色など）を適用するロジックを実装**

### 3.3. 結果の統合表示
*   [ ] 括弧表示と色付けを組み合わせた最終的なHTML文字列を生成する関数を作成
*   [ ] 生成されたHTMLを `st.markdown(unsafe_allow_html=True)` で表示
*   [ ] **インタラクティブな表示（マウスオーバー時のツールチップなど）の検討と実装**
*   [ ] **表示オプション（表示レベル、元の文との切り替え）の実装**
*   [ ] **解析結果のダウンロード機能（HTML, TXT, JSON形式）の実装**

## 4. 全体統合と品質向上

*   [ ] 「解析実行」ボタンクリック時の処理フローを実装 (入力取得 -> 解析 -> 結果整形 -> 表示)
*   [ ] 「クリア」ボタンクリック時の処理フローを実装 (入力エリアと結果表示をクリア)
*   [ ] `st.session_state` を利用して、入力テキストや解析結果の状態を管理
*   [ ] エラーハンドリングの実装 (例: 空の入力、非英語の入力に対するメッセージ表示)
*   [ ] **入力のバリデーションとフィードバック（英文判定など）の実装**
*   [ ] UI/UXの調整 (Streamlitの標準機能範囲内で、視覚的な改善)
*   [ ] レスポンシブデザインの確認 (PCとスマートフォンでの表示崩れがないか)
*   [ ] **アクセシビリティ（色覚多様性対応など）の考慮と実装**
*   [ ] パフォーマンスのテストと最適化 (特に長いテキストの処理速度)
*   [ ] **オンボーディングとヘルプ機能の実装（初回アクセス時の説明、ツールチップなど）**
*   [ ] **フィードバックメッセージの強化（解析完了メッセージ、より分かりやすいエラーメッセージ）**
*   [ ] **SentenceAnalyzer, ResultFormatter などのモジュール化とファイル分割**
*   [ ] **ユニットテストの作成（pytest を使用）**

## 5. デプロイ

*   [ ] `requirements.txt` の最終化 (必要なライブラリとそのバージョンを正確に記載)
*   [ ] Streamlit Community Cloud もしくは他のホスティングサービスへのデプロイ手順

 2025_07_20  句の構造解析の改善
 現在の句構造の表示は、色が重なって見えるだけで、句の入れ        
  子（ネスト）構造が直感的に分かりづらいですよね。学習ツールとして、これでは不十分です。

  ご提案いただいたように、より明確に階層がわかる表示方法に変更するのが良いでしょう。

  添付いただいた画像のようなツリー形式の表示は、構文構造を学ぶ上で最も標準的で分かりやすい方法です。そこで、現        
  在の依存関係ツリーと同様に、句構造（NP, VPなど）の階層もツリーで表示する機能を実装します。

  改善計画

   1. 句構造ツリーの追加:
       * 現在の分かりにくい「ネストボックス表示」を、Graphvizを使った「句構造ツリー」に置き換えます。
       * このツリーでは、どの句（例: VP）が、どの小さな句（例:
         PP）や単語を含んでいるのかが、親子関係として一目で分かります。
   2. テキストベースの階層リストの維持:
       * 現在、階層表示の下に表示されているインデント付きの「検出された句の一覧」は、テキストとして構造を確認
         するのに便利なので、これはこのまま残します。

  この改善により、視覚的なツリーとテキストのリストの両方で、文の構造を深く理解できるようになります。

  句構造をツリー形式で表示する改善計画に基づき、実装を開始します。

  実装方針:

   1. `app.py` に `display_chunk_tree` 関数を新設:
       * graphviz を利用して、句構造の階層をツリーとして描画する新しい関数を作成します。
       * この関数は、句（NP, VPなど）を親ノード、そこに含まれる小さな句や個々の単語を子ノードとして配置し、文
         の構造を視覚的に表現します。
   2. 既存の表示を置き換え:
       * 現在の分かりにくい「ネストボックス表示」を、新しく作成する display_chunk_tree
         関数の呼び出しに置き換えます。
       * テキストベースのインデント付きリストは、ツリーとの比較参照に便利なため、そのまま残します。

  まずは、app.py に新しい display_chunk_tree 関数を追加し、関連する部分を修正します。

  app.py に句構造をツリー表示する display_chunk_tree 関数を新たに追加し、既存の display_chunks
  を置き換える形で実装を進めます。

  主な変更点:

   * `display_chunk_tree` 関数の新設:
       * Graphvizを使い、句の親子関係を視覚的なツリーとして描画します。
       * 句（NP, VPなど）を色のついたノード、個々の単語を白いノードとして表現し、構造を明確に区別します。
   * `display_chunks` 関数の役割変更:
       * これまでのHTMLによるボックス表示の代わりに、新設した display_chunk_tree を呼び出すように変更します。
       * ツリーの下に表示していたテキストベースの階層リストは、ツリーとの対応が分かりやすいように、ツリー表示
         の一部として統合します。

  この変更により、ユーザーは句構造を、より直感的で分かりやすいツリー形式で確認できるようになります。

  エラーの原因:

  エラーメッセージ IndexError: list index out of range
  は、前回と同様に、リストの範囲外のインデックスにアクセスしようとしたことが原因です。

  具体的には、display_chunk_tree 関数内で、文ごとのトークンリスト（tokens_info）に対して、文章全体で通し番号に        
  なっているID（token_id）をそのままインデックスとして使おうとして、範囲外アクセスが発生していました。

  修正方針:

  この問題を根本的に解決するため、display_chunk_tree 関数を修正します。

   1. まず、トークンのIDをキーとし、トークン情報そのものを値とする辞書（token_map）を作成します。
   2. その後、トークン情報を参照する際は、リストのインデックスではなく、この辞書（token_map）を使ってIDを指定
      して安全にアクセスするように変更します。

  この修正により、トークンIDの採番方法に依存しない、より堅牢なツリー描画ロジックになります。

  エラーメッセージ IndexError: list index out of range とトレースバックから、app.py の display_chunk_tree
  関数内で、tokens_info
  リストに対して、リストの範囲外のインデックスでアクセスしようとしていることが分かります。

  これは、tokens_info が文ごとのトークン情報のリストであり、そのインデックスは0から始まるのに対し、token_id
  は文章全体でのトークンの通し番号であるため、両者が一致しない場合に発生します。

  前回の修正で token_map を導入しましたが、どうやら一部の箇所でまだ tokens_info[token_id]
  のような直接的なリストアクセスが残っていたか、replace 操作が完全に適用されていなかった可能性があります。

  この問題を確実に解決するため、app.py ファイル全体を、修正済みの display_chunk_tree
  関数を含む内容で上書きします。これにより、確実に token_map を使用した安全なアクセスに統一されます。

  エラーメッセージ IndexError: list index out of range とトレースバックから、app.py の display_chunk_tree
  関数内で、tokens_info
  リストに対して、リストの範囲外のインデックスでアクセスしようとしていることが分かります。

  これは、tokens_info が文ごとのトークン情報のリストであり、そのインデックスは0から始まるのに対し、token_id
  は文章全体でのトークンの通し番号であるため、両者が一致しない場合に発生します。

  前回の修正で token_map を導入しましたが、どうやら一部の箇所でまだ tokens_info[token_id]
  のような直接的なリストアクセスが残っていたか、replace 操作が完全に適用されていなかった可能性があります。

  この問題を確実に解決するため、app.py ファイル全体を、修正済みの display_chunk_tree
  関数を含む内容で上書きします。これにより、確実に token_map を使用した安全なアクセスに統一されます。

  IndexError の根本原因は、tokens_info が現在の文のトークンリストであるにもかかわらず、token_id
  が文章全体のトークンの通し番号であるため、tokens_info[token_id]
  のように直接インデックスとして使用すると範囲外エラーが発生することです。

  前回の修正で token_map を導入しましたが、まだ一部の箇所で tokens_info[token_id]
  のような直接的なリストアクセスが残っているようです。

  この問題を確実に解決するため、display_chunk_tree 関数内の tokens_info[token_id]
  となっている箇所を、token_map[token_id] に置き換えます。
2025年7月22日火曜日

### 実装計画：VP/ADVP抽出ロジックの強化とテスト

#### 1. 現状の抽出ロジックの理解 (`analyzer.py`の確認)

まず、現在の`analyzer.py`におけるVPおよびADVPの抽出ロジックを詳細に確認します。特に`SentenceAnalyzer`クラス内の関連メソッド（例: `_extract_chunks`、`_get_verb_phrase_tokens`、`_get_adverb_phrase_tokens`など）に注目します。

現在の`_get_verb_phrase_tokens`関数は、助動詞の収集や、動詞句を構成する要素（目的語、補語、修飾語など）の範囲特定において、改善の余地があります。特に、助動詞が主動詞と正しく結合されないケースや、前置詞句や副詞句が動詞句の範囲に適切に含まれないケースが考えられます。

`_get_adverb_phrase_tokens`関数は、副詞が他の副詞を修飾するケース（例: "very quickly"）を再帰的に処理する基本的なロジックはありますが、より複雑な副詞句の構成要素を網羅しているか確認が必要です。

#### 2. テストケースの作成 (`tests/test_analyzer.py`の更新)

既存の`tests/test_analyzer.py`に、VPおよびADVPの抽出精度を検証するための具体的なテストケースを追加します。これにより、現在のロジックの限界を明確にし、改善後のロジックが正しく機能するかを検証します。

**テストファイルの場所:** `tests/test_analyzer.py`

**テストケースの例:**

```python
import pytest
import spacy
from analyzer import SentenceAnalyzer

@pytest.fixture(scope="module")
def nlp_model():
    # spaCyモデルを一度だけロード
    return spacy.load("en_core_web_sm")

@pytest.fixture(scope="module")
def analyzer(nlp_model):
    # SentenceAnalyzerのインスタンスを一度だけ作成
    return SentenceAnalyzer(nlp_model)

# ヘルパー関数：指定された文から特定のタイプの句を抽出
def get_chunks_for_sentence(analyzer_instance, text, chunk_type):
    analyzed_data = analyzer_instance.analyze_text(text)
    if not analyzed_data:
        return []
    # 単一の文を想定
    sentence_chunks = analyzed_data[0]['chunks']
    return [c['text'] for c in sentence_chunks if c['type'] == chunk_type]

# --- VP (動詞句) 抽出のテストケース ---

def test_vp_simple(analyzer):
    text = "He runs."
    expected_vps = ["runs"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_with_auxiliary(analyzer):
    text = "He will run."
    expected_vps = ["will run"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_with_multiple_auxiliaries(analyzer):
    text = "He has been running."
    expected_vps = ["has been running"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_with_dobj(analyzer):
    text = "She eats apples."
    expected_vps = ["eats apples"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_with_iobj_dobj(analyzer):
    text = "He gave her a book."
    expected_vps = ["gave her a book"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_with_prep_phrase(analyzer):
    text = "He runs in the park."
    expected_vps = ["runs in the park"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_with_complex_prep_phrase(analyzer):
    text = "He jumps over the lazy dog."
    expected_vps = ["jumps over the lazy dog"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_with_advmod(analyzer):
    text = "She sings beautifully."
    expected_vps = ["sings beautifully"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_with_xcomp(analyzer):
    text = "He tried to run."
    expected_vps = ["tried to run"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_with_ccomp(analyzer):
    text = "She said that he was happy."
    expected_vps = ["said that he was happy"] # ccompは節全体を含むと仮定
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_passive_voice(analyzer):
    text = "The ball was hit by him."
    expected_vps = ["was hit by him"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_with_negation(analyzer):
    text = "He did not run."
    expected_vps = ["did not run"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_with_phrasal_verb(analyzer):
    text = "She looked up the word."
    expected_vps = ["looked up the word"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

def test_vp_with_advcl(analyzer):
    text = "He ran quickly because he was late."
    expected_vps = ["ran quickly because he was late"]
    assert get_chunks_for_sentence(analyzer, text, 'VP') == expected_vps

# --- ADVP (副詞句) 抽出のテストケース ---

def test_advp_simple(analyzer):
    text = "He runs quickly."
    expected_advps = ["quickly"]
    assert get_chunks_for_sentence(analyzer, text, 'ADVP') == expected_advps

def test_advp_with_modifier(analyzer):
    text = "He runs very quickly."
    expected_advps = ["very quickly"]
    assert get_chunks_for_sentence(analyzer, text, 'ADVP') == expected_advps

def test_advp_with_multiple_modifiers(analyzer):
    text = "He runs extremely very quickly."
    expected_advps = ["extremely very quickly"]
    assert get_chunks_for_sentence(analyzer, text, 'ADVP') == expected_advps

def test_advp_at_start_of_sentence(analyzer):
    text = "Quickly, he ran."
    expected_advps = ["Quickly"]
    assert get_chunks_for_sentence(analyzer, text, 'ADVP') == expected_advps
```

#### 3. `analyzer.py`の`_get_verb_phrase_tokens`関数の修正

`_get_verb_phrase_tokens`関数を、より堅牢な再帰的アプローチで書き換えます。主要な動詞から開始し、その助動詞、目的語、補語、および関連する修飾語（前置詞句、副詞句、節など）を依存関係ツリーを辿って網羅的に収集します。

**修正方針:**

*   **BFS (幅優先探索) の利用:** キューを使用して、動詞から関連するトークンを段階的に探索します。
*   **助動詞の統合:** `aux`や`auxpass`の依存関係を持つトークンを確実に動詞句に含めます。
*   **包括的な依存関係の考慮:** `dobj`, `iobj`, `attr`, `acomp`, `xcomp`, `ccomp`, `advmod`, `prep`, `prt`, `agent`, `oprd`, `neg`, `pobj`, `csubj`, `csubjpass`, `obj`, `obl`, `advcl`など、動詞句を構成する可能性のあるすべての依存関係の子孫（`subtree`）を収集します。

**修正後の`_get_verb_phrase_tokens`の例:**

```python
    def _get_verb_phrase_tokens(self, token):
        """動詞トークンから動詞句全体を構成するトークンを収集する"""
        vp_tokens = set()
        queue = [token] # 主動詞/助動詞から探索を開始

        while queue:
            current_token = queue.pop(0) # キューからトークンを取り出す
            if current_token in vp_tokens:
                continue
            vp_tokens.add(current_token)

            # 助動詞 (子と、もし現在のトークンが助動詞ならその親も) を追加
            # 助動詞はそれ自体がVPの一部であり、さらに他のトークンを支配する可能性があるため、キューに追加
            for child in current_token.children:
                if child.dep_.startswith('aux'):
                    queue.append(child)
            
            # 現在のトークンが助動詞で、その親が主動詞の場合、親もキューに追加
            if current_token.dep_.startswith('aux') and current_token.head != current_token and current_token.head.pos_ in ('VERB', 'AUX'):
                queue.append(current_token.head)

            # 動詞句の構成要素となる主要な依存関係の子孫をすべて追加
            # これらの依存関係は、句全体を形成するため、subtree を使用
            relevant_deps_for_subtree = [
                'dobj', 'iobj', 'attr', 'acomp', 'xcomp', 'ccomp', # 補語/引数
                'advmod', 'prep', 'prt', 'neg', 'agent', 'oprd', 'advcl', # 修飾語
                'csubj', 'csubjpass', 'obj', 'obl', # その他の引数/補語
                'relcl', 'acl' # 関係節や形容詞句が動詞の補語/修飾語となる場合
            ]
            for child in current_token.children:
                if child.dep_ in relevant_deps_for_subtree:
                    vp_tokens.update(child.subtree)
                # 助動詞は既にキューで処理済みなのでスキップ
                elif child.dep_.startswith('aux'):
                    pass
                # その他の依存関係の子は、必要に応じて個別に処理を検討
                # 現状では、subtreeでカバーされないがVPに含めるべきケースがあればここに追加
                # 例: 'conj' (等位接続された動詞) など
                elif child.dep_ == 'conj':
                    queue.append(child) # 接続された動詞もVPの一部として探索
        
        return vp_tokens
```

#### 4. `analyzer.py`の`_get_adverb_phrase_tokens`関数の修正

現在の`_get_adverb_phrase_tokens`関数は、副詞が他の副詞を修飾するケース（`advmod`）を再帰的に処理しています。このロジックは基本的なADVP抽出には有効ですが、より複雑なケースに対応するため、必要に応じて拡張を検討します。

**修正方針:**

*   現在のロジックでテストケースがパスするか確認し、必要であれば、`quantmod`（数量修飾語）など、ADVPを構成する可能性のある他の依存関係も考慮に入れます。

#### 5. 実装とテストの繰り返し

1.  **テストの実行:** まず、上記で作成したテストケースを実行します。多くのテストが失敗するはずです。
2.  **`analyzer.py`の修正:** `_get_verb_phrase_tokens`関数と`_get_adverb_phrase_tokens`関数を、提案された修正方針に基づいて実装します。
3.  **デバッグと反復:** 修正後、再度テストを実行し、失敗したテストケースをデバッグします。必要に応じて、`analyzer.py`のロジックをさらに調整し、すべてのテストがパスするまでこのプロセスを繰り返します。
4.  **追加テストケースの作成:** デバッグ中に新たなエッジケースや問題が発見された場合は、それらをカバーする新しいテストケースを追加し、テストスイートを強化します。

この計画に従うことで、VPおよびADVPの抽出ロジックを体系的に改善し、その精度をテストによって確実に検証することができます。
