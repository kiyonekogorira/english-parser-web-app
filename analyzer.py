import re
import spacy

class SentenceAnalyzer:
    def __init__(self, nlp_model):
        self.nlp = nlp_model
        self.pos_map = {
            "PROPN": "名詞 (固有名詞)",
            "NOUN": "名詞",
            "VERB": "動詞",
            "ADP": "前置詞",
            "DET": "冠詞",
            "ADJ": "形容詞",
            "ADV": "副詞",
            "CONJ": "接続詞",
            "SCONJ": "接続詞 (従属)",
            "CCONJ": "接続詞 (等位)",
            "PRON": "代名詞",
            "AUX": "助動詞",
            "PART": "助詞",
            "NUM": "数詞",
            "PUNCT": "句読点",
            "SYM": "記号",
            "X": "その他",
            "SPACE": "空白",
        }
        # 依存関係タグの日本語訳を追加
        self.dep_map = {
            "ROOT": "ルート (文の主動詞)",
            "nsubj": "名詞主語",
            "dobj": "直接目的語",
            "attr": "属性補語",
            "acomp": "形容詞補語",
            "pobj": "前置詞の目的語",
            "aux": "助動詞",
            "auxpass": "受動態助動詞",
            "advmod": "副詞修飾語",
            "amod": "形容詞修飾語",
            "compound": "複合語",
            "prep": "前置詞句",
            "cc": "等位接続詞",
            "conj": "接続",
            "det": "限定詞",
            "poss": "所有格",
            "case": "格標識",
            "punct": "句読点",
            "appos": "同格語",
            "relcl": "関係節",
            "acl": "形容詞句",
            "xcomp": "開いた補語",
            "csubj": "節主語",
            "ccomp": "閉じた補語",
            "agent": "動作主",
            "oprd": "目的語補語",
            "mark": "従属接続詞",
            "expl": "形式主語/目的語",
            "prt": "句動詞の小詞",
            "dative": "与格",
            "npadvmod": "名詞句副詞修飾語",
            "nummod": "数詞修飾語",
            "quantmod": "数量修飾語",
            "dep": "汎用依存関係",
            "meta": "メタ情報",
            "intj": "間投詞",
            "parataxis": "並列",
            "discourse": "談話標識",
            "vocative": "呼びかけ",
            "csubjpass": "受動態節主語",
            "neg": "否定",
            "predet": "前限定詞",
            "preconj": "前接続詞",
            "fixed": "固定表現",
            "flat": "フラットな関係",
            "goeswith": "結合",
            "list": "リスト",
            "dislocated": "転位",
            "reparandum": "言い直し",
            "orphan": "孤立語",
            "advcl": "副詞節",
            "obj": "目的語", # dobjとiobjをまとめた汎用目的語
            "iobj": "間接目的語",
            "obl": "斜格補語", # prepとpobjをまとめた汎用斜格補語
            "csubj": "節主語",
            "ccomp": "補語節",
            "xcomp": "開いた補語節",
            "advcl": "副詞節",
            "amod": "形容詞修飾語",
            "appos": "同格語",
            "nummod": "数詞修飾語",
            "poss": "所有格",
            "punct": "句読点",
            "compound": "複合語",
            "prt": "句動詞の小詞",
            "det": "限定詞",
            "predet": "前限定詞",
            "neg": "否定",
            "expl": "形式主語/目的語",
            "discourse": "談話標識",
            "vocative": "呼びかけ",
            "parataxis": "並列",
            "goeswith": "結合",
            "reparandum": "言い直し",
            "orphan": "孤立語",
            "list": "リスト",
            "dislocated": "転位",
            "dep": "汎用依存関係",
            "meta": "メタ情報",
            "intj": "間投詞",
            "fixed": "固定表現",
            "flat": "フラットな関係",
            "conj": "接続",
            "cc": "等位接続詞",
            "acl": "形容詞句",
            "relcl": "関係節",
            "csubjpass": "受動態節主語",
            "agent": "動作主",
            "oprd": "目的語補語",
            "mark": "従属接続詞",
            "dative": "与格",
            "npadvmod": "名詞句副詞修飾語",
            "quantmod": "数量修飾語",
        }

    def get_pos_japanese_from_pos_tag(self, pos_tag):
        """pos_tag (例: "NOUN") から日本語品詞を取得するヘルパーメソッド"""
        return self.pos_map.get(pos_tag, pos_tag)

    def get_dep_japanese(self, dep_tag):
        """dep_tag (例: "nsubj") から日本語依存関係を取得するヘルパーメソッド"""
        return self.dep_map.get(dep_tag, dep_tag)

    def get_pos_japanese(self, token):
        if token.pos_ == "PUNCT":
            if token.text == ".":
                return "句読点 (ピリオド)"
            elif token.text == ",":
                return "句読点 (カンマ)"
        return self.pos_map.get(token.pos_, token.pos_)

    def analyze_text(self, text):
        cleaned_lines = []
        for line in text.split("\n"):
            line = re.sub(r"^(?:テストケース:|\d+\.\s*)+", "", line).strip()

            if re.search(
                r"[a-zA-Z]", line
            ):  # Check if the line still contains English letters
                cleaned_lines.append(line)

        clean_text = "\n".join(cleaned_lines)
        if not clean_text.strip():
            return []

        doc = self.nlp(clean_text)
        analyzed_sentences = []
        for sent in doc.sents:
            if not sent.text.strip():
                continue
            analyzed_sentences.append(self._analyze_sentence(sent))
        return analyzed_sentences

    def _analyze_sentence(self, doc):
        subjects = []
        verbs = []
        noun_phrases = []
        verb_phrases = []
        prepositional_phrases = []

        sent_offset = doc.start_char

        pos_tagged_tokens = []
        for token in doc:
            if token.pos_ != "SPACE":
                pos_tagged_tokens.append(f"{token.text} ({self.get_pos_japanese(token)})")

        tokens_info = []
        for token in doc:
            children_ids = [child.i for child in token.children]
            token_info = {
                'id': token.i,
                'text': token.text,
                'lemma': token.lemma_,
                'pos': token.pos_,
                'tag': token.tag_,
                'dep': token.dep_,
                'dep_japanese': self.get_dep_japanese(token.dep_), # 日本語依存関係を追加
                'head_id': token.head.i,
                'children_ids': children_ids,
                'is_root': token.dep_ == "ROOT",
                'pos_japanese': self.get_pos_japanese(token) # 日本語品詞を追加
            }
            tokens_info.append(token_info)

        chunks_info = []

        # 名詞句 (NP) - spaCyのnoun_chunksをそのまま利用
        for chunk in doc.noun_chunks:
            chunks_info.append({
                'type': 'NP',
                'text': chunk.text,
                'start_id': chunk.start,
                'end_id': chunk.end - 1
            })

        # 動詞句 (VP) の抽出を改善
        # ROOT動詞とその依存関係を探索
        # または、動詞で、かつそのheadが動詞である場合（複合動詞など）
        for token in doc:
            if token.pos_ == "VERB" or token.pos_ == "AUX":
                # ROOT動詞、または動詞句の主要な動詞
                if token.dep_ == "ROOT" or (token.head.pos_ == "VERB" and token.dep_ in ["aux", "xcomp", "ccomp", "advcl"]):
                    # 動詞句の開始と終了インデックスを見つける
                    # 動詞とその全ての依存関係を含むスパンを考慮
                    # spaCyのsubtreeは連続したスパンを保証しないため、手動で最小・最大インデックスを計算
                    
                    # 関連するトークンを収集するヘルパー関数
                    def get_verb_phrase_tokens(verb_token):
                        vp_tokens = set([verb_token])
                        # 助動詞、目的語、補語、副詞修飾語などを追加
                        for child in verb_token.children:
                            if child.dep_ in ["aux", "auxpass", "dobj", "iobj", "attr", "acomp", "xcomp", "ccomp", "advcl", "prt", "agent", "oprd", "neg"]:
                                vp_tokens.add(child)
                                vp_tokens.update(get_verb_phrase_tokens(child)) # 再帰的に子孫も追加
                            elif child.dep_ == "prep": # 前置詞句もVPの一部として含める場合
                                vp_tokens.add(child)
                                vp_tokens.update(get_verb_phrase_tokens(child))
                        return vp_tokens

                    vp_tokens_set = get_verb_phrase_tokens(token)
                    
                    if vp_tokens_set:
                        vp_tokens_list = sorted(list(vp_tokens_set), key=lambda t: t.i)
                        
                        # 連続したスパンを形成するために、最小と最大のインデックスを使用
                        start_id = vp_tokens_list[0].i
                        end_id = vp_tokens_list[-1].i
                        
                        # 句のテキストを正確に取得
                        vp_text = doc[start_id : end_id + 1].text
                        
                        # 重複するVPを追加しないようにチェック（簡易的な重複排除）
                        # より厳密な重複排除は、後でremove_subsetsで行う
                        is_duplicate = False
                        for existing_chunk in chunks_info:
                            if existing_chunk['type'] == 'VP' and \
                               existing_chunk['start_id'] == start_id and \
                               existing_chunk['end_id'] == end_id:
                               is_duplicate = True
                               break
                        
                        if not is_duplicate:
                            chunks_info.append({
                                'type': 'VP',
                                'text': vp_text,
                                'start_id': start_id,
                                'end_id': end_id
                            })

        # 前置詞句 (PP) の抽出を改善
        for token in doc:
            if token.pos_ == "ADP": # 前置詞
                # 前置詞の目的語 (pobj) を探す
                pobj_token = None
                for child in token.children:
                    if child.dep_ == "pobj":
                        pobj_token = child
                        break
                
                if pobj_token:
                    # 前置詞と目的語のサブツリー全体を含むスパンを形成
                    pp_tokens = sorted(list(token.subtree), key=lambda t: t.i)
                    
                    start_id = pp_tokens[0].i
                    end_id = pp_tokens[-1].i
                    
                    pp_text = doc[start_id : end_id + 1].text
                    
                    is_duplicate = False
                    for existing_chunk in chunks_info:
                        if existing_chunk['type'] == 'PP' and \
                           existing_chunk['start_id'] == start_id and \
                           existing_chunk['end_id'] == end_id:
                           is_duplicate = True
                           break
                    
                    if not is_duplicate:
                        chunks_info.append({
                            'type': 'PP',
                            'text': pp_text,
                            'start_id': start_id,
                            'end_id': end_id
                        })

        # 副詞句 (ADVP) の抽出を改善
        for token in doc:
            if token.pos_ == "ADV": # 副詞
                # 副詞とその修飾語（他の副詞など）を含むスパンを形成
                advp_tokens = sorted(list(token.subtree), key=lambda t: t.i)
                
                start_id = advp_tokens[0].i
                end_id = advp_tokens[-1].i
                
                advp_text = doc[start_id : end_id + 1].text
                
                is_duplicate = False
                for existing_chunk in chunks_info:
                    if existing_chunk['type'] == 'ADVP' and \
                       existing_chunk['start_id'] == start_id and \
                       existing_chunk['end_id'] == end_id:
                       is_duplicate = True
                       break
                
                if not is_duplicate:
                    chunks_info.append({
                        'type': 'ADVP',
                        'text': advp_text,
                        'start_id': start_id,
                        'end_id': end_id
                    })

        # 句の重複とネストを考慮して最終的なchunks_infoを整理
        # ここでremove_subsetsのようなロジックを適用して、より大きな句の中に含まれる小さな句を排除する
        # ただし、implementation_plan.mdでは「ネストした句の表示も考慮する」とあるため、
        # ここでは重複排除のみを行い、ネストの表示はdisplay_chunks側で処理する
        
        # start_idとend_idでソートし、重複を排除
        # 同じ開始・終了IDを持つ句は一つだけ残す
        unique_chunks = {}
        for chunk in chunks_info:
            key = (chunk['type'], chunk['start_id'], chunk['end_id'])
            unique_chunks[key] = chunk
        
        chunks_info = list(unique_chunks.values())
        
        # 句の長さに応じてソート（長い句を優先して表示するため）
        chunks_info.sort(key=lambda x: (x['end_id'] - x['start_id']), reverse=True)

        print(f"DEBUG: tokens_info count: {len(tokens_info)}")
        print(f"DEBUG: chunks_info count: {len(chunks_info)}")
        print(f"DEBUG: first 3 tokens_info: {tokens_info[:3]}")
        print(f"DEBUG: first 3 chunks_info: {chunks_info[:3]}")

        return {
            "original_text": doc.text,
            "sent_offset": sent_offset,
            "subjects": subjects,
            "verbs": verbs,
            "noun_phrases": noun_phrases,
            "verb_phrases": verb_phrases,
            "prepositional_phrases": prepositional_phrases,
            "tokens": tokens_info, # tokens_infoを返す
            "chunks": chunks_info, # chunks_infoを返す
            "pos_tagged_text": " ".join(pos_tagged_tokens),
        }