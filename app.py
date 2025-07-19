import streamlit as st
import spacy

# --- Streamlitページ設定 ---
st.set_page_config(
    page_title="英文構造解析アプリ",
    layout="centered", # または "wide"
    initial_sidebar_state="auto"
)

# --- spaCyモデルのロード ---
@st.cache_resource
def load_model():
    try:
        nlp = spacy.load("en_core_web_sm")
        return nlp
    except OSError:
        st.error("spaCyモデル 'en_core_web_sm' が見つかりません。")
        st.info("コマンドラインで 'python -m spacy download en_core_web_sm' を実行してインストールしてください。")
        st.stop()

nlp = load_model()

# --- 構文要素を保持するデータ構造 ---
class SyntaxElement:
    def __init__(self, text, type, role="", children=None, tokens=None, start_token_index=None, start_char=None, end_char=None):
        self.text = text
        self.type = type # 例: "Sentence", "Main Clause", "Noun Phrase", "Word"
        self.role = role # 例: "Subject", "Predicate", "Location"
        self.children = children if children is not None else []
        self.tokens = tokens if tokens is not None else [] # 葉ノード（単語）用
        self.start_token_index = start_token_index if start_token_index is not None else (tokens[0].i if tokens else -1)
        self.start_char = start_char if start_char is not None else (tokens[0].idx if tokens else -1)
        self.end_char = end_char if end_char is not None else (tokens[-1].idx + len(tokens[-1].text) if tokens else -1)

    def get_display_text(self, indent_level=0):
        indent = "  " * indent_level
        
        # 単語レベルの要素の場合は品詞も表示
        if self.tokens and len(self.tokens) == 1: # 単一トークンの要素
            token_info = self.tokens[0]
            # Wordタイプの場合、roleに品詞名が入るようにbuild_syntax_treeで設定
            return f"{indent}{self.text}: {self.role} ({token_info.tag_})"
        else: # 句や節の場合
            display_text = f"{indent}{self.type}"
            if self.role:
                display_text += f" ({self.role})"
            display_text += f": {self.text}"
            return display_text

# --- 役割推定の補助関数 ---
def get_noun_phrase_role(root_token):
    if root_token.dep_ == "nsubj": return "主語"
    if root_token.dep_ == "dobj": return "直接目的語"
    if root_token.dep_ == "pobj": return "前置詞の目的語"
    if root_token.dep_ == "attr": return "補語"
    if root_token.dep_ == "oprd": return "目的語補語"
    if root_token.dep_ == "appos": return "同格"
    if root_token.dep_ == "npadvmod": return "副詞的修飾 (名詞句)"
    if root_token.dep_ == "iobj": return "間接目的語"
    return "名詞句"

def get_prepositional_phrase_role(prep_token):
    head = prep_token.head
    if head.pos_ == "VERB":
        if prep_token.text.lower() in ["in", "on", "at", "from", "to", "near"]: return "副詞的修飾 (場所)"
        if prep_token.text.lower() in ["after", "before", "during", "until", "since", "while"]: return "副詞的修飾 (時)"
        if prep_token.text.lower() in ["with", "by"]: return "副詞的修飾 (手段/方法)"
        if prep_token.text.lower() in ["for", "about"]: return "副詞的修飾 (目的/対象)"
        if prep_token.text.lower() in ["because of", "due to"]: return "副詞的修飾 (原因)"
    elif head.pos_ in ["NOUN", "PROPN"]:
        return "形容詞的修飾 (名詞)"
    return "前置詞句"

def get_verb_phrase_role(verb_token):
    if verb_token.dep_ == "ROOT":
        if verb_token.lemma_ in ["be", "seem", "become", "appear", "feel", "look", "sound", "taste", "smell", "grow", "remain", "stay", "turn"]:
            return "述語 (連結動詞)"
        return "述語 (主動詞)"
    if verb_token.dep_ == "xcomp": return "述語 (開補文)"
    if verb_token.dep_ == "ccomp": return "述語 (補文)"
    if verb_token.dep_ == "conj": return "述語 (並列)"
    if verb_token.dep_ == "aux" or verb_token.dep_ == "auxpass": return "助動詞"
    return "述語"

def get_clause_role(clause_root_token):
    # Find the conjunction (marker) if it exists
    marker_token = None
    for child in clause_root_token.children:
        if child.dep_ == "mark":
            marker_token = child
            break
    # If not found as a child, check if the clause_root_token itself is a conjunction
    if not marker_token and clause_root_token.pos_ == "SCONJ":
        marker_token = clause_root_token

    marker_text = marker_token.text.lower() if marker_token else ""

    if clause_root_token.dep_ == "advcl":
        if marker_text in ["because", "since", "as"]: return "副詞節 (原因・理由)"
        if marker_text in ["although", "though", "even though"]: return "副詞節 (譲歩)"
        if marker_text in ["when", "while", "after", "before", "until", "as soon as"]: return "副詞節 (時)"
        if marker_text in ["if", "unless", "provided that"]: return "副詞節 (条件)"
        if marker_text in ["so that", "in order that"]: return "副詞節 (目的)"
        if marker_text in ["where", "wherever"]: return "副詞節 (場所)"
        if marker_text in ["as if", "as though"]: return "副詞節 (様態)"
        return "副詞節" # Default for advcl
    if clause_root_token.dep_ == "acl" or clause_root_token.dep_ == "relcl": return "形容詞節"
    if clause_root_token.dep_ == "ccomp": return "名詞節 (補文)"
    if clause_root_token.dep_ == "xcomp": return "名詞節 (開補文)"
    return "節"

# --- ヘルパー関数 ---
def get_span_text(tokens):
    if not tokens: return ""
    # spaCyのSpanオブジェクトのようにテキストを結合
    return tokens[0].doc.text[tokens[0].idx : tokens[-1].idx + len(tokens[-1].text)]

def get_subtree_tokens(token):
    return sorted([t for t in token.subtree], key=lambda t: t.i)

# --- 依存ツリーを再帰的に走査し、構文要素を構築する関数 ---
def build_syntax_tree(token, processed_indices):
    if token.i in processed_indices or token.pos_ == "PUNCT":
        processed_indices.add(token.i) # Ensure punctuation is marked processed
        return None

    element = None
    element_tokens = [] # Tokens belonging to the current element

    # 1. 従属節 (Subordinate Clauses) の検出を最優先
    # 関係代名詞節 (relcl) も含める
    if token.dep_ in ["advcl", "acl", "ccomp", "xcomp", "relcl"] or \
       (token.pos_ == "SCONJ" and token.dep_ == "mark") or \
       (token.pos_ == "PRON" and token.dep_ == "nsubj" and token.head.dep_ == "relcl"): # 関係代名詞
        
        element_tokens = get_subtree_tokens(token)
        element = SyntaxElement(get_span_text(element_tokens), "従属節", get_clause_role(token), start_token_index=token.i, start_char=element_tokens[0].idx, end_char=element_tokens[-1].idx + len(element_tokens[-1].text))
    
    # 2. 不定詞句 / 分詞構文 の検出 (動詞がルートの場合)
    elif token.pos_ == "VERB" or token.pos_ == "AUX":
        vp_type = "動詞句"
        vp_role = get_verb_phrase_role(token)
        
        is_infinitive = False
        to_token = None
        # Check for 'to' as a child with PART pos_ and specific dep_ for infinitive
        if (token.dep_ in ["xcomp", "ccomp", "advcl", "acl"]) and \
           any(child.text.lower() == "to" and child.pos_ == "PART" for child in token.children):
            is_infinitive = True
            to_token = next((child for child in token.children if child.text.lower() == "to" and child.pos_ == "PART"), None)

        if is_infinitive and to_token:
            vp_type = "不定詞句"
            # Get subtree of the verb, then add 'to' at the beginning if it's not already there
            verb_subtree_tokens = get_subtree_tokens(token)
            if to_token not in verb_subtree_tokens: # Ensure 'to' is included and at the start
                element_tokens = sorted([to_token] + verb_subtree_tokens, key=lambda t: t.i)
            else:
                element_tokens = verb_subtree_tokens # 'to' is already part of subtree
            
            element = SyntaxElement(get_span_text(element_tokens), vp_type, vp_role, start_token_index=element_tokens[0].i, start_char=element_tokens[0].idx, end_char=element_tokens[-1].idx + len(element_tokens[-1].text))

        elif (token.pos_ == "VERB" and (token.tag_ == "VBG" or token.tag_ == "VBN")) and \
             (token.dep_ in ["acl", "advcl"]):
            vp_type = "分詞構文"
            element_tokens = get_subtree_tokens(token)
            element = SyntaxElement(get_span_text(element_tokens), vp_type, vp_role, start_token_index=token.i, start_char=element_tokens[0].idx, end_char=element_tokens[-1].idx + len(element_tokens[-1].text))

        else: # General Verb Phrase
            element_tokens = get_subtree_tokens(token) # Use subtree for general VP
            element = SyntaxElement(get_span_text(element_tokens), vp_type, vp_role, start_token_index=token.i, start_char=element_tokens[0].idx, end_char=element_tokens[-1].idx + len(element_tokens[-1].text))

    # 3. 名詞句 (Noun Phrases) の検出
    # Check if the current token is the root of a noun chunk in its sentence
    elif token.pos_ in ["NOUN", "PROPN", "PRON"]:
        for chunk in token.sent.noun_chunks: # Iterate over noun chunks in the current sentence
            if token == chunk.root: # If the current token is the root of this chunk
                # Ensure all tokens in chunk are unprocessed before claiming it
                if all(t.i not in processed_indices for t in chunk):
                    element_tokens = list(chunk)
                    element = SyntaxElement(get_span_text(element_tokens), "名詞句", get_noun_phrase_role(chunk.root), start_token_index=chunk.start, start_char=element_tokens[0].idx, end_char=element_tokens[-1].idx + len(element_tokens[-1].text))
                break # Found the chunk, no need to check other chunks for this token

    # 4. 前置詞句 (Prepositional Phrases) の検出
    elif token.pos_ == "ADP" and token.dep_ == "prep":
        element_tokens = get_subtree_tokens(token)
        element = SyntaxElement(get_span_text(element_tokens), "前置詞句", get_prepositional_phrase_role(token), start_token_index=token.i, start_char=element_tokens[0].idx, end_char=element_tokens[-1].idx + len(element_tokens[-1].text))

    # 5. その他の単語 (Word) として処理
    if element is None: # If no larger element was identified
        element_tokens = [token]
        word_type = "Word" # Default
        word_role = token.pos_ # Default role is POS
        
        # More specific types/roles for single words
        if token.pos_ == "PRON":
            word_type = "代名詞"
            word_role = get_noun_phrase_role(token) # e.g., 主語
        elif token.pos_ == "ADP": # Preposition
            word_type = "前置詞"
            word_role = "前置詞"
        elif token.pos_ == "SCONJ": # Subordinating Conjunction
            word_type = "接続詞"
            word_role = "従属接続詞"
        elif token.pos_ == "CCONJ": # Coordinating Conjunction
            word_type = "接続詞"
            word_role = "等位接続詞"
        elif token.pos_ == "ADV": # Adverb
            word_type = "副詞"
            word_role = "副詞"
        elif token.pos_ == "ADJ": # Adjective
            word_type = "形容詞"
            word_role = "形容詞"
        elif token.pos_ == "DET": # Determiner
            word_type = "冠詞"
            word_role = "限定詞"
        elif token.pos_ == "VERB" or token.pos_ == "AUX": # 単一の動詞が句として認識されない場合
            word_type = "動詞"
            word_role = get_verb_phrase_role(token)
        
        element = SyntaxElement(token.text, word_type, role=word_role, tokens=[token], start_token_index=token.i, start_char=token.idx, end_char=token.idx + len(token.text))

    # Now, if an element was created, mark its tokens as processed and build its children
    if element:
        for t in element_tokens:
            processed_indices.add(t.i) # Mark all tokens of this element as processed

        # Recursively build children from tokens within this element's span
        # This is the crucial part to avoid re-processing and infinite recursion
        # Iterate through the tokens that *belong* to this element's span
        for t in element_tokens:
            # Only process children that are not yet processed and are not punctuation
            # And ensure we don't try to process the current element's root token again as a child
            if t.i != token.i and t.i not in processed_indices and t.pos_ != "PUNCT":
                child_element = build_syntax_tree(t, processed_indices)
                if child_element:
                    element.children.append(child_element)
        
        # Sort children by their start index for consistent output
        element.children.sort(key=lambda x: x.start_token_index)
        
        return element
    
    return None

# --- メインの解析ロジック ---
def analyze_and_format_text(doc):
    parsed_elements = []

    for sent in doc.sents:
        sentence_element = SyntaxElement(sent.text, "文章全体", "", start_token_index=sent.start, start_char=sent.start_char, end_char=sent.end_char)
        
        # 従属節のトークンを事前に特定
        all_sub_clause_tokens_indices = set()
        sub_clause_elements_temp = []

        for token in sent:
            # Check if this token is the root of a subordinate clause
            if token.dep_ in ["advcl", "acl", "ccomp", "xcomp", "relcl"] or \
               (token.pos_ == "SCONJ" and token.dep_ == "mark") or \
               (token.pos_ == "PRON" and token.dep_ == "nsubj" and token.head.dep_ == "relcl"): # 関係代名詞
                
                sub_clause_subtree_tokens = get_subtree_tokens(token)
                # Create a temporary element to get its span and mark its tokens
                temp_sub_element = SyntaxElement(get_span_text(sub_clause_subtree_tokens), "従属節", get_clause_role(token), tokens=sub_clause_subtree_tokens, start_token_index=token.i, start_char=sub_clause_subtree_tokens[0].idx, end_char=sub_clause_subtree_tokens[-1].idx + len(sub_clause_subtree_tokens[-1].text))
                sub_clause_elements_temp.append(temp_sub_element)
                for t in sub_clause_subtree_tokens:
                    all_sub_clause_tokens_indices.add(t.i)

        # 主節のトークンを構築 (従属節のトークンを除外)
        main_clause_tokens = []
        for token in sent:
            if token.i not in all_sub_clause_tokens_indices:
                main_clause_tokens.append(token)
        
        main_clause_text = get_span_text(sorted(main_clause_tokens, key=lambda t: t.i)) if main_clause_tokens else ""
        main_clause_element = SyntaxElement(main_clause_text, "主節", "", 
                                            start_token_index=main_clause_tokens[0].i if main_clause_tokens else -1,
                                            start_char=main_clause_tokens[0].idx if main_clause_tokens else -1,
                                            end_char=main_clause_tokens[-1].idx + len(main_clause_tokens[-1].text) if main_clause_tokens else -1)
        
        # 主節内部の要素を構築
        main_clause_processed_indices = set()
        for token in sorted(main_clause_tokens, key=lambda t: t.i):
            if token.pos_ != "PUNCT":
                element = build_syntax_tree(token, main_clause_processed_indices)
                if element:
                    main_clause_element.children.append(element)
        main_clause_element.children.sort(key=lambda x: x.start_token_index)

        sentence_element.children.append(main_clause_element)

        # 従属節の内部要素を構築し、sentence_elementに追加
        for sub_el_temp in sorted(sub_clause_elements_temp, key=lambda x: x.start_token_index):
            sub_clause_processed_indices = set()
            sub_clause_actual_element = SyntaxElement(sub_el_temp.text, sub_el_temp.type, sub_el_temp.role, 
                                                      tokens=sub_el_temp.tokens, # 元のトークンを渡す
                                                      start_token_index=sub_el_temp.start_token_index,
                                                      start_char=sub_el_temp.start_char, end_char=sub_el_temp.end_char)
            for token in sorted(sub_el_temp.tokens, key=lambda t: t.i):
                if token.pos_ != "PUNCT":
                    element = build_syntax_tree(token, sub_clause_processed_indices)
                    if element:
                        sub_clause_actual_element.children.append(element)
            sub_clause_actual_element.children.sort(key=lambda x: x.start_token_index)
            sentence_element.children.append(sub_clause_actual_element)

        # 最終的な要素の順序を調整 (元の文の順序に近づける)
        sentence_element.children.sort(key=lambda x: x.start_token_index)
        parsed_elements.append(sentence_element)

    return parsed_elements

# --- 文法用語の説明辞書 ---
GRAMMAR_EXPLANATIONS = {
    "文章全体": "解析対象の英文全体を表します。",
    "主節": "文の主要な部分で、それだけで完全な意味を持つことができます。",
    "従属節": "主節に意味的に依存し、それだけでは完全な意味を持たない節です。名詞節、形容詞節、副詞節などがあります。",
    "名詞句": "名詞を中心に構成される句で、文中で主語、目的語、補語などの名詞の働きをします。",
    "動詞句": "動詞を中心に構成される句で、述語動詞とその目的語、補語、修飾語などを含みます。",
    "前置詞句": "前置詞とそれに続く名詞句（前置詞の目的語）で構成される句です。文中で形容詞的または副詞的に機能します。",
    "不定詞句": "to + 動詞の原形から始まり、名詞、形容詞、または副詞の働きをする句です。",
    "分詞構文": "動詞の現在分詞（-ing形）または過去分詞（-ed/-en形）から始まり、主節に付帯的な状況（時、理由、条件など）を加える句です。",
    "Word": "文を構成する最小単位である単語です。", # この説明は汎用的なWord用
    "主語": "動詞の動作を行う主体、または状態を表す対象です。",
    "述語": "主語の動作や状態を表す動詞の部分です。",
    "直接目的語": "動詞の動作を直接受ける対象です。",
    "間接目的語": "動詞の動作が間接的に向けられる対象です（例: give someone somethingのsomeone）。",
    "補語": "主語や目的語の状態や性質を補足説明する要素です。",
    "同格": "直前の名詞（句）と同じものを指し、補足説明する要素です。",
    "副詞的修飾 (名詞句)": "名詞句が副詞のように動詞や文全体を修飾する働きをします（例: every day, last night）。",
    "副詞的修飾 (場所)": "動作が行われる場所を示します。",
    "副詞的修飾 (時)": "動作が行われる時を示します。",
    "副詞的修飾 (手段/方法)": "動作が行われる手段や方法を示します。",
    "副詞的修飾 (目的/対象)": "動作の目的や対象を示します。",
    "副詞的修飾 (原因)": "動作や状態の原因を示します。",
    "形容詞的修飾 (名詞)": "名詞を修飾し、その性質や状態を説明します。",
    "述語 (連結動詞)": "主語と補語をつなぐ動詞（例: be, seem, becomeなど）です。",
    "述語 (開補文)": "主語が省略された補語節を持つ述語です。",
    "述語 (補文)": "動詞の補語となる節を持つ述語です。",
    "述語 (並列)": "and, orなどの接続詞で並列に繋がれた述語です。",
    "助動詞": "動詞の意味を補う動詞です（例: can, will, haveなど）。",
    "副詞節 (原因・理由)": "主節の動作や状態の原因・理由を示します。",
    "副詞節 (譲歩)": "主節の内容と対照的な状況を示します（〜にもかかわらず）。",
    "副詞節 (時)": "主節の動作や状態が行われる時を示します。",
    "副詞節 (条件)": "主節の動作や状態が成立するための条件を示します。",
    "副詞節 (目的)": "主節の動作や状態の目的を示します。",
    "副詞節 (場所)": "主節の動作や状態が行われる場所を示します。",
    "副詞節 (様態)": "主節の動作や状態の様態（〜のように）を示します。",
    "形容詞節": "名詞を修飾する節です（関係代名詞節など）。",
    "名詞節 (補文)": "動詞や形容詞の補語となる名詞の働きをする節です。",
    "名詞節 (開補文)": "主語が省略された名詞の働きをする節です。",
    "代名詞": "名詞の代わりに人や物を指し示す語です。",
    "接続詞": "語と語、句と句、節と節をつなぐ語です。",
    "従属接続詞": "従属節を導き、主節に従属させる接続詞です。",
    "等位接続詞": "対等な関係の語、句、節をつなぐ接続詞です。",
    "副詞": "動詞、形容詞、他の副詞、または文全体を修飾し、時、場所、様態などを表します。",
    "形容詞": "名詞を修飾し、その性質や状態を表します。",
    "冠詞": "名詞の前に置かれ、その名詞が特定のものか不特定のものかを示す語です（a, an, the）。",
    "限定詞": "名詞の意味を限定する語です（冠詞、指示代名詞、所有格など）。",
    "動詞": "主語の動作や状態を表す語です。",
    "前置詞": "名詞や代名詞の前に置かれ、時、場所、方向、手段などの関係を示す語です。"
}

# --- 再帰的な表示ヘルパー関数 ---
def display_syntax_element(element, indent_level=0):
    display_text = element.get_display_text(indent_level) # get_display_textは内部でインデントを処理

    # 説明があるかチェック
    explanation = None
    if element.type in GRAMMAR_EXPLANATIONS: 
        explanation = GRAMMAR_EXPLANATIONS[element.type]
    elif element.role and element.role in GRAMMAR_EXPLANATIONS:
        explanation = GRAMMAR_EXPLANATIONS[element.role]
    
    # ポップオーバーまたは通常のテキスト表示
    if explanation:
        with st.popover(display_text):
            st.markdown(explanation)
    else:
        st.markdown(display_text)

    # 子要素を再帰的に表示
    for child in element.children:
        display_syntax_element(child, indent_level + 1)

# --- UI構築 ---
st.title("英文構造解析アプリ")

st.write("解析したい英文を下のテキストボックスに入力してください。")

# --- 入力エリア ---
user_input = st.text_area(
    "英文を入力",
    "",
    height=150,
    placeholder="例: The quick brown fox jumps over the lazy dog. Having finished his work, he went home. She wants to learn English."
)

# --- 解析実行ボタン ---
if st.button("解析実行"):
    if not user_input.strip():
        st.warning("英文を入力してください。")
    else:
        try:
            with st.spinner("解析中..."):
                doc = nlp(user_input)
                parsed_data = analyze_and_format_text(doc)

                st.subheader("解析結果:")
                
                # フィルタリングオプションは削除済み
                filtered_parsed_data = parsed_data

                for element in filtered_parsed_data:
                    # 最上位の要素を表示
                    display_syntax_element(element, indent_level=0)

        except Exception as e:
            st.error(
                f"解析中にエラーが発生しました。入力された英文を確認してください。エラー詳細: {e}"
            )
