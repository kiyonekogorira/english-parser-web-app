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
            "ROOT": "ルート", "nsubj": "名詞主語", "dobj": "直接目的語", "attr": "属性補語",
            "acomp": "形容詞補語", "pobj": "前置詞の目的語", "aux": "助動詞",
            "auxpass": "受動態助動詞", "advmod": "副詞修飾語", "amod": "形容詞修飾語",
            "compound": "複合語", "prep": "前置詞句", "cc": "等位接続詞", "conj": "接続",
            "det": "限定詞", "poss": "所有格", "case": "格標識", "punct": "句読点",
            "appos": "同格語", "relcl": "関係節", "acl": "形容詞句", "xcomp": "開いた補語",
            "csubj": "節主語", "ccomp": "閉じた補語", "agent": "動作主", "oprd": "目的語補語",
            "mark": "従属接続詞", "expl": "形式主語/目的語", "prt": "句動詞の小詞",
            "dative": "与格", "npadvmod": "名詞句副詞修飾語", "nummod": "数詞修飾語",
            "quantmod": "数量修飾語", "dep": "汎用依存関係", "meta": "メタ情報",
            "intj": "間投詞", "parataxis": "並列", "discourse": "談話標識",
            "vocative": "呼びかけ", "csubjpass": "受動態節主語", "neg": "否定",
            "predet": "前限定詞", "preconj": "前接続詞", "fixed": "固定表現",
            "flat": "フラットな関係", "goeswith": "結合", "list": "リスト",
            "dislocated": "転位", "reparandum": "言い直し", "orphan": "孤立語",
            "advcl": "副詞節", "obj": "目的語", "iobj": "間接目的語", "obl": "斜格補語",
        }

    def get_pos_japanese_from_pos_tag(self, pos_tag):
        return self.pos_map.get(pos_tag, pos_tag)

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
        
        def collect_vp_tokens(current_token):
            # 助動詞と本体の動詞を追加
            if current_token not in vp_tokens:
                vp_tokens.add(current_token)
                # 助動詞を遡って追加
                if current_token.dep_ in ('conj', 'xcomp', 'ccomp', 'advcl'):
                    for child in current_token.children:
                        if child.dep_.startswith('aux'):
                            vp_tokens.add(child)
            
            # 目的語、補語、副詞、小詞などを再帰的に収集
            for child in current_token.children:
                if child.dep_ in ('dobj', 'iobj', 'attr', 'acomp', 'xcomp', 'ccomp', 'advmod', 'prt', 'agent', 'oprd', 'neg', 'pobj'):
                    vp_tokens.update(child.subtree)
                # 前置詞句全体を追加
                elif child.dep_ == 'prep':
                    vp_tokens.update(child.subtree)
                # 助動詞を追加
                elif child.dep_.startswith('aux'):
                    vp_tokens.add(child)
            
            # 主動詞に接続する助動詞を追加
            for head_child in token.head.children:
                if head_child.dep_.startswith('aux') and head_child not in vp_tokens:
                    vp_tokens.add(head_child)

        collect_vp_tokens(token)
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
        """包含関係にある句を削除する（大きい方を残す）"""
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
        tokens_info = [{
            'id': token.i, 'text': token.text, 'lemma': token.lemma_,
            'pos': token.pos_, 'tag': token.tag_, 'dep': token.dep_,
            'dep_japanese': self.get_dep_japanese(token.dep_),
            'head_id': token.head.i, 'children_ids': [c.i for c in token.children],
            'is_root': token.dep_ == "ROOT", 'pos_japanese': self.get_pos_japanese(token)
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
                # トークンが連続していることを確認
                if all(doc.doc[i] in phrase_tokens for i in range(start_id, end_id + 1)):
                    chunks_info.append({
                        'type': chunk_type,
                        'text': doc[start_id:end_id + 1].text,
                        'start_id': start_id,
                        'end_id': end_id
                    })

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