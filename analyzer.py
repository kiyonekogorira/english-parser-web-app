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
        }

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
            "tokens_info": [
                {
                    "text": token.text,
                    "pos": token.pos_,
                    "dep": token.dep_,
                    "head": token.head.text,
                }
                for token in doc
            ],
            "pos_tagged_text": " ".join(pos_tagged_tokens),
        }