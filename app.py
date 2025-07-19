import streamlit as st
import spacy

# --- Streamlitページ設定 ---
st.set_page_config(
    page_title="英文構造解析アプリ",
    layout="centered", # または "wide"
    initial_sidebar_state="auto"
)

# --- spaCyモデルのロード (フェーズ1で実装) ---
# アプリケーション起動時に一度だけロードするためにst.cache_resourceを使用
@st.cache_resource
def load_model():
    try:
        # en_core_web_smモデルをロード
        nlp = spacy.load("en_core_web_sm")
        return nlp
    except OSError:
        st.error("spaCyモデル 'en_core_web_sm' が見つかりません。")
        st.info("コマンドラインで 'python -m spacy download en_core_web_sm' を実行してインストールしてください。")
        st.stop() # モデルがない場合はこれ以上実行しない

nlp = load_model()

# --- UI構築 ---
st.title("英文構造解析アプリ")

st.write("解析したい英文を下のテキストボックスに入力してください。")

# --- 入力エリア ---
user_input = st.text_area(
    "英文を入力",
    "",
    height=150,
    placeholder="例: The quick brown fox jumps over the lazy dog."
)

# --- 解析実行ボタン ---
if st.button("解析実行"):
    if not user_input.strip():
        st.warning("英文を入力してください。")
    else:
        try:
            with st.spinner("解析中..."):
                # --- spaCyによる基本解析 (フェーズ1で実装) ---
                doc = nlp(user_input)

                st.subheader("解析結果 (基本情報):")
                st.write(f"入力された英文: **{user_input}**")
                st.write("---")

                for token in doc:
                    st.write(
                        f"**単語**: {token.text}, "
                        f"**品詞**: {token.pos_} ({token.tag_}), "
                        f"**依存関係**: {token.dep_}, "
                        f"**親**: {token.head.text}"
                    )

        except Exception as e:
            st.error(
                f"解析中にエラーが発生しました。入力された英文を確認してください。エラー詳細: {e}"
            )
