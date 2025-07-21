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
        # 名詞句 (NP)
        for chunk in doc.noun_chunks:
            chunks_info.append({
                'type': 'NP',
                'text': chunk.text,
                'start_id': chunk.start,
                'end_id': chunk.end - 1
            })

        # 動詞句 (VP), 前置詞句 (PP), 副詞句 (ADVP) はカスタムロジックで抽出
        # (MVPでは簡易的な抽出)
        for token in doc:
            # 動詞句 (VP)
            if token.dep_ == "ROOT":
                vp_start = token.i
                vp_end = token.i
                for child in token.children:
                    if child.dep_ in ["aux", "auxpass", "dobj", "attr", "acomp"]:
                        vp_end = max(vp_end, child.i)
                chunks_info.append({
                    'type': 'VP',
                    'text': doc[vp_start:vp_end+1].text,
                    'start_id': vp_start,
                    'end_id': vp_end
                })

            # 前置詞句 (PP)
            if token.pos_ == "ADP":
                pp_start = token.i
                pp_end = token.i
                for child in token.children:
                    if child.dep_ == "pobj":
                        pp_end = child.i
                chunks_info.append({
                    'type': 'PP',
                    'text': doc[pp_start:pp_end+1].text,
                    'start_id': pp_start,
                    'end_id': pp_end
                })

            # 副詞句 (ADVP)
            if token.pos_ == "ADV":
                advp_start = token.i
                advp_end = token.i
                chunks_info.append({
                    'type': 'ADVP',
                    'text': doc[advp_start:advp_end+1].text,
                    'start_id': advp_start,
                    'end_id': advp_end
                })

        for token in doc:
            if "nsubj" in token.dep_:
                subjects.append(
                    {
                        "text": token.text,
                        "start": token.idx,
                        "end": token.idx + len(token.text),
                    }
                )
            if token.pos_ == "VERB" or token.pos_ == "AUX":
                verbs.append(
                    {
                        "text": token.text,
                        "start": token.idx,
                        "end": token.idx + len(token.text),
                    }
                )

        for chunk in doc.noun_chunks:
            noun_phrases.append(
                {"text": chunk.text, "start": chunk.start_char, "end": chunk.end_char}
            )

        temp_verb_phrases = []
        temp_prepositional_phrases = []

        for token in doc:
            if token.pos_ == "VERB" or token.pos_ == "AUX":
                current_vp_tokens = []
                current_vp_tokens.append(token)

                def get_non_subject_dependents(t):
                    dependents = []
                    for child in t.children:
                        if child.dep_ not in ["nsubj", "csubj", "expl"]:
                            dependents.append(child)
                            dependents.extend(get_non_subject_dependents(child))
                    return dependents

                current_vp_tokens.extend(get_non_subject_dependents(token))

                if token.pos_ == "AUX" and token.head.pos_ == "VERB":
                    current_vp_tokens.extend(get_non_subject_dependents(token.head))

                if current_vp_tokens:
                    current_vp_tokens.sort(key=lambda t: t.i)
                    start_node = current_vp_tokens[0]
                    end_node = current_vp_tokens[-1]
                    start_char = start_node.idx
                    end_char = end_node.idx + len(end_node.text)
                    temp_verb_phrases.append(
                        {
                            "text": doc.text[
                                start_char - sent_offset : end_char - sent_offset
                            ],
                            "start": start_char,
                            "end": end_char,
                        }
                    )

        for token in doc:
            if token.pos_ == "ADP" and any(c.dep_ == "pobj" for c in token.children):
                pp_tokens = [token]
                for child in token.children:
                    if child.dep_ == "pobj":
                        pp_tokens.extend(list(child.subtree))

                start_node = min(pp_tokens, key=lambda t: t.i)
                end_node = max(pp_tokens, key=lambda t: t.i)
                start_char = start_node.idx
                end_char = end_node.idx + len(end_node.text)
                temp_prepositional_phrases.append(
                    {
                        "text": doc.text[
                            start_char - sent_offset : end_char - sent_offset
                        ],
                        "start": start_char,
                        "end": end_char,
                    }
                )

        def remove_subsets(phrases):
            unique_phrases_by_span = {(p["start"], p["end"]): p for p in phrases}
            phrases = list(unique_phrases_by_span.values())

            result = []
            for p1 in phrases:
                is_subset = False
                for p2 in phrases:
                    if (p1["start"], p1["end"]) == (p2["start"], p2["end"]):
                        continue
                    if p2["start"] <= p1["start"] and p1["end"] <= p2["end"]:
                        is_subset = True
                        break
                if not is_subset:
                    result.append(p1)
            return result

        verb_phrases = remove_subsets(temp_verb_phrases)
        prepositional_phrases = remove_subsets(temp_prepositional_phrases)

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