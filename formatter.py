class ResultFormatter:
    def __init__(self, list_of_analyzed_data):
        self.list_of_analyzed_data = list_of_analyzed_data

    def format_html_all(self):
        full_html = []
        for analyzed_data in self.list_of_analyzed_data:
            full_html.append(self._format_single_html(analyzed_data))
        # Use <p> tags for better separation between sentences
        return "".join([f"<p>{html}</p>" for html in full_html])

    def _format_single_html(self, analyzed_data):
        original_text = analyzed_data["original_text"]
        text_len = len(original_text)
        events_at_pos = [[] for _ in range(text_len + 1)]

        # 文の開始位置をオフセットとして取得
        offset = analyzed_data["sent_offset"]

        subject_style = "color:red; font-weight:bold;"
        verb_style = "color:blue; font-weight:bold;"
        np_style = "background-color:#ADD8E6; border:1px solid #00CED1; border-radius:3px; padding:0 2px;"
        vp_style = "background-color:#E0FFE0; border:1px solid #32CD32; border-radius:3px; padding:0 2px;"
        pp_style = "background-color:#FFFFE0; border:1px solid #FFD700; border-radius:3px; padding:0 2px;"

        def add_events(items, open_tag, close_tag, prefix="", suffix=""):
            for item in items:
                start_pos = max(0, item["start"] - offset)
                end_pos = min(text_len, item["end"] - offset)
                if start_pos <= end_pos:
                    events_at_pos[start_pos].append((prefix + open_tag, True))
                    events_at_pos[end_pos].append((close_tag + suffix, False))

        # Add tags for all element types
        add_events(
            analyzed_data["subjects"], f"""<span style="{subject_style}">""", "</span>",
            prefix="", suffix=""
        )
        add_events(
            analyzed_data["verbs"], f"""<span style="{verb_style}">""", "</span>",
            prefix="", suffix=""
        )
        add_events(
            analyzed_data["noun_phrases"],
            f"""<span style="{np_style}">""",
            "</span>",
            prefix="[名詞句: ", suffix="]"
        )
        add_events(
            analyzed_data["verb_phrases"],
            f"""<span style="{vp_style}">""",
            "</span>",
            prefix="(動詞句: ", suffix=")"
        )
        add_events(
            analyzed_data["prepositional_phrases"],
            f"""<span style="{pp_style}">""",
            "</span>",
            prefix="{前置詞句: ", suffix="}"
        )

        # Build the formatted HTML string
        formatted_html = []
        for i, char in enumerate(original_text):
            events_at_pos[i].sort(key=lambda x: not x[1])
            for tag_string, is_opening_tag in events_at_pos[i]:
                formatted_html.append(tag_string)
            formatted_html.append(char)

        events_at_pos[text_len].sort(key=lambda x: not x[1])
        for tag_string, is_opening_tag in events_at_pos[text_len]:
            formatted_html.append(tag_string)

        return "".join(formatted_html)