import re
import spacy

class SentenceAnalyzer:
    def __init__(self, nlp_model):
        self.nlp = nlp_model
        self.pos_map = {
            "PROPN": "名詞 (固有名詞)", "NOUN": "名詞", "VERB": "動詞", "ADP": "前置詞",
            "DET": "冠詞", "ADJ": "形容詞", "ADV": "副詞", "CONJ": "接続詞",
            "SCONJ": "接続詞 (従属)", "CCONJ": "接続詞 (等位)", "PRON": "代名詞",
            "AUX": "助動詞", "PART": "助詞", "NUM": "数詞", "PUNCT": "句読点",
            "SYM": "記号", "X": "その他", "SPACE": "空白",
        }
        self.dep_map = {
            "ROOT": "文の主動詞。文の中心となる単語です。",
            "nsubj": "動詞の主語となる名詞句。",
            "dobj": "動詞の直接目的語となる名詞句（例: apple）",
            "attr": "属性補語（主語や目的語の属性を説明する補語）（例: beautiful）",
            "acomp": "形容詞補語（動詞の補語となる形容詞）（例: happy）",
            "pobj": "前置詞の目的語となる名詞句（例: school）",
            "aux": "主動詞を助ける動詞（例: have, be, do）",
            "auxpass": "受動態助動詞（受動態を形成する助動詞）（例: was）",
            "advmod": "動詞、形容詞、他の副詞を修飾する副詞（例: very）",
            "amod": "名詞を修飾する形容詞（例: big）",
            "compound": "複数の単語が結合して一つの意味をなす複合語（例: post office）",
            "prep": "前置詞とその目的語からなる句（例: in）",
            "cc": "2つ以上の同等の要素（単語、句、節）を結びつける接続詞（例: and）",
            "conj": "等位接続詞によって結びつけられた要素（例: running）",
            "det": "名詞を限定する単語（例: the）",
            "poss": "所有格（名詞の所有を示す）（例: 's）",
            "case": "格標識（前置詞など、格を示す要素）（例: of）",
            "punct": "文の句読点（例: .）",
            "appos": "同格語（先行する名詞句を別の名詞句で説明する）（例: Bob）",
            "relcl": "関係節（先行する名詞を修飾する関係代名詞節）（例: which）",
            "acl": "形容詞句（名詞を修飾する句や節）（例: to read）",
            "xcomp": "開いた補語（主語が省略された補語節）（例: to swim）",
            "csubj": "節主語（主語が節になっている場合）（例: That he is honest）",
            "ccomp": "閉じた補語（主語が明示された補語節）（例: that he is honest）",
            "agent": "動作主（受動態文の動作主を示す）（例: by）",
            "oprd": "目的語補語（目的語の属性を説明する補語）（例: happy）",
            "mark": "従属接続詞（従属節を導入する接続詞）（例: because）",
            "expl": "形式主語/目的語（it is...構文などの形式的な主語/目的語）（例: it）",
            "prt": "句動詞の小詞（句動詞を構成する副詞や前置詞）（例: up）",
            "dative": "与格（間接目的語）（例: me）",
            "npadvmod": "名詞句副詞修飾語（副詞的に機能する名詞句）（例: yesterday）",
            "nummod": "数詞修飾語（名詞を修飾する数詞）（例: two）",
            "quantmod": "数量修飾語（数量を表す修飾語）（例: many）",
            "dep": "汎用依存関係（特定のラベルが適用できない場合の汎用的な依存関係）",
            "meta": "メタ情報（文法的な関係ではないメタ情報）",
            "intj": "間投詞（感情や驚きを表す単語）（例: Oh）",
            "parataxis": "並列（文や句が並列に配置されている関係）（例: saw）",
            "discourse": "談話標識（談話の流れを示す単語や句）（例: however）",
            "vocative": "呼びかけ（呼びかけの対象を示す）（例: John）",
            "csubjpass": "受動態節主語（受動態文の主語が節になっている場合）（例: That the book was written）",
            "neg": "否定（否定を表す要素）（例: not）",
            "predet": "前限定詞（限定詞の前に来る要素）（例: all）",
            "preconj": "前接続詞（接続詞の前に来る要素）（例: either）",
            "fixed": "固定表現（複数の単語で一つの意味をなす固定表現）（例: as well as）",
            "flat": "フラットな関係（複合固有名詞などのフラットな構造）（例: New York）",
            "goeswith": "結合（ハイフンなどで結合された単語の一部）（例: state-of-the-art）",
            "list": "リスト（リスト構造の要素）（例: bananas）",
            "dislocated": "転位（文頭などに移動した要素）（例: The book）",
            "reparandum": "言い直し（言い直された部分）",
            "orphan": "孤立語（文法的な親を持たない孤立した単語）",
            "advcl": "副詞節（動詞を修飾する副詞節）（例: when I arrived）",
            "obj": "目的語（動詞の目的語）（例: a book）",
            "iobj": "間接目的語（動詞の間接目的語）（例: him）",
            "obl": "斜格補語（動詞の補語で、直接目的語や間接目的語以外のもの）（例: on the table）",
        }
        self.morph_map = {
            # Aspect
            "Aspect=Imp": "未完了相",
            "Aspect=Perf": "完了相",
            "Aspect=Prog": "進行相",
            # Case
            "Case=Acc": "対格 (目的格)",
            "Case=Dat": "与格",
            "Case=Gen": "属格 (所有格)",
            "Case=Nom": "主格",
            # Gender
            "Gender=Fem": "女性",
            "Gender=Masc": "男性",
            "Gender=Neut": "中性",
            # Mood
            "Mood=Imp": "命令法",
            "Mood=Ind": "直説法",
            "Mood=Sub": "接続法",
            # Number
            "Number=Plur": "複数",
            "Number=Sing": "単数",
            # Person
            "Person=1": "一人称",
            "Person=2": "二人称",
            "Person=3": "三人称",
            # Tense
            "Tense=Past": "過去形",
            "Tense=Pres": "現在形",
            # VerbForm
            "VerbForm=Fin": "定形動詞",
            "VerbForm=Ger": "動名詞",
            "VerbForm=Inf": "不定詞",
            "VerbForm=Part": "分詞",
            # Degree
            "Degree=Cmp": "比較級",
            "Degree=Pos": "原級",
            "Degree=Sup": "最上級",
        }
        self.ent_type_map = {
            "PERSON": "人名",
            "NORP": "国籍、宗教、政治集団",
            "FAC": "建物、空港など",
            "ORG": "組織",
            "GPE": "国、都市、州",
            "LOC": "場所（GPE以外）",
            "PRODUCT": "製品",
            "EVENT": "イベント",
            "WORK_OF_ART": "芸術作品",
            "LAW": "法律",
            "LANGUAGE": "言語",
            "DATE": "日付",
            "TIME": "時間",
            "PERCENT": "パーセンテージ",
            "MONEY": "金額",
            "QUANTITY": "数量",
            "ORDINAL": "序数",
            "CARDINAL": "基数",
        }

    def get_morph_japanese(self, morph_str):
        if not morph_str:
            return ""
        parts = morph_str.split('|')
        translated_parts = [self.morph_map.get(part, part) for part in parts]
        return ", ".join(translated_parts)

    def get_ent_type_japanese(self, ent_type):
        return self.ent_type_map.get(ent_type, ent_type)

    def get_dep_japanese(self, dep_tag):
        return self.dep_map.get(dep_tag, dep_tag)

    def get_pos_japanese(self, token):
        if token.pos_ == "PUNCT":
            if token.text == ".": return "句読点 (ピリオド)"
            if token.text == ",": return "句読点 (カンマ)"
        return self.pos_map.get(token.pos_, token.pos_)

    def analyze_text(self, text):
        cleaned_lines = [
            re.sub(r"^(?:\d+\.\s*)+", "", line).strip()
            for line in text.split("\n")
            if re.search(r"[a-zA-Z]", line)
        ]
        clean_text = "\n".join(cleaned_lines)
        if not clean_text.strip():
            return []

        doc = self.nlp(clean_text)
        return [self._analyze_sentence(sent) for sent in doc.sents if sent.text.strip()]

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

    def _get_adverb_phrase_tokens(self, token):
        """副詞トークンから副詞句全体を構成するトークンを収集する"""
        advp_tokens = {token}
        for child in token.children:
            if child.dep_ == 'advmod':
                advp_tokens.update(self._get_adverb_phrase_tokens(child))
        return advp_tokens

    def _get_prepositional_phrase_tokens(self, token):
        """前置詞トークンから前置詞句全体を構成するトークンを収集する"""
        return set(token.subtree)

    def _remove_subsets(self, chunks):
        """包含関係にある句を削除する(大きい方を残す)"""
        # 同じタイプの句で、完全に包含されているものを削除
        final_chunks = []
        chunks.sort(key=lambda c: (c['start_id'], - (c['end_id'] - c['start_id'])))
        
        for i, current in enumerate(chunks):
            is_subset = False
            for j, other in enumerate(chunks):
                if i == j:
                    continue
                # currentがotherに完全に包含されている場合
                if current['type'] == other['type'] and \
                   current['start_id'] >= other['start_id'] and \
                   current['end_id'] <= other['end_id'] and \
                   (current['start_id'] > other['start_id'] or current['end_id'] < other['end_id']):
                    is_subset = True
                    break
            if not is_subset:
                final_chunks.append(current)
        return final_chunks

    def _analyze_sentence(self, doc):
        # 固有表現情報を事前に辞書にまとめる
        ent_info_map = {}
        for ent in doc.ents:
            for token_idx in range(ent.start, ent.end):
                ent_info_map[token_idx] = {
                    'entity_text': ent.text,
                    'entity_type': ent.label_
                }

        tokens_info = [{
            'id': token.i, 'text': token.text, 'lemma': token.lemma_,
            'pos': token.pos_, 'tag': token.tag_, 'dep': token.dep_,
            'dep_japanese': self.get_dep_japanese(token.dep_),
            'head_id': token.head.i, 'children_ids': [c.i for c in token.children],
            'is_root': token.dep_ == "ROOT", 'pos_japanese': self.get_pos_japanese(token),
            'start': token.idx,
            'end': token.idx + len(token.text),
            'morph': str(token.morph),
            'morph_japanese': self.get_morph_japanese(str(token.morph)),
            'ent_type': token.ent_type_,
            'ent_type_japanese': self.get_ent_type_japanese(token.ent_type_),
            'is_entity_part': bool(token.ent_type_),
            'entity_text': ent_info_map.get(token.i, {}).get('entity_text'),
            'entity_type': ent_info_map.get(token.i, {}).get('entity_type'),
        } for token in doc]

        chunks_info = []
        # NP (名詞句)
        for chunk in doc.noun_chunks:
            chunks_info.append({'type': 'NP', 'text': chunk.text, 'start_id': chunk.start, 'end_id': chunk.end - 1})

        # VP, PP, ADVP
        for token in doc:
            phrase_tokens = set()
            chunk_type = None
            if token.pos_ in ('VERB', 'AUX'):
                phrase_tokens = self._get_verb_phrase_tokens(token)
                chunk_type = 'VP'
            elif token.pos_ == 'ADP':
                phrase_tokens = self._get_prepositional_phrase_tokens(token)
                chunk_type = 'PP'
            elif token.pos_ == 'ADV':
                phrase_tokens = self._get_adverb_phrase_tokens(token)
                chunk_type = 'ADVP'

            if phrase_tokens:
                start_id = min(t.i for t in phrase_tokens)
                end_id = max(t.i for t in phrase_tokens)
                
                # 句のテキストを生成する際に、句読点や空白を除外する
                # ただし、start_idとend_idは元のトークンの範囲を維持
                chunk_text_tokens = [
                    doc.doc[i] for i in range(start_id, end_id + 1) 
                    if doc.doc[i] in phrase_tokens and not doc.doc[i].is_punct and not doc.doc[i].is_space
                ]
                
                # 句のテキストが空でないことを確認
                if chunk_text_tokens:
                    chunk_text = "".join([t.text_with_ws for t in chunk_text_tokens]).strip()
                    
                    # デバッグプリント
                    print(f"DEBUG: Created chunk: Type={chunk_type}, Text='{chunk_text}', Start={start_id}, End={end_id}")
                    print(f"DEBUG: Phrase tokens for this chunk: {[t.text for t in phrase_tokens]}")

                    chunks_info.append({
                        'type': chunk_type,
                        'text': chunk_text,
                        'start_id': start_id,
                        'end_id': end_id
                    })
                else:
                    print(f"DEBUG: Skipped empty chunk: Type={chunk_type}, Start={start_id}, End={end_id}, Phrase tokens={[t.text for t in phrase_tokens]}")

        # 重複を排除
        unique_chunks = { (c['type'], c['start_id'], c['end_id']): c for c in chunks_info }
        cleaned_chunks = list(unique_chunks.values())
        
        # 句の長さに応じてソート
        cleaned_chunks.sort(key=lambda x: (x['start_id'], x['end_id']), reverse=True)

        return {
            "original_text": doc.text,
            "sent_offset": doc.start_char,
            "tokens": tokens_info,
            "chunks": cleaned_chunks,
            "pos_tagged_text": " ".join(f"{t.text}({self.get_pos_japanese(t)})" for t in doc if t.pos_ != 'SPACE'),
            # 旧形式のキーは空リストで維持
            "subjects": [], "verbs": [], "noun_phrases": [], "verb_phrases": [], "prepositional_phrases": [],
        }