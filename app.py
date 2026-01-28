import re
import streamlit as st

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Bias Check", page_icon="🕵️‍♀️", layout="wide")

# -----------------------------
# Session state defaults
# -----------------------------
if "nav" not in st.session_state:
    st.session_state.nav = "Home"   # <-- single source of truth for page
if "step" not in st.session_state:
    st.session_state.step = 1
if "blind_text" not in st.session_state:
    st.session_state.blind_text = ""
if "original_text" not in st.session_state:
    st.session_state.original_text = ""
if "score_blind" not in st.session_state:
    st.session_state.score_blind = 5
if "notes_blind" not in st.session_state:
    st.session_state.notes_blind = ""

# -----------------------------
# Redaction patterns + function
# -----------------------------
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(\+?\d{1,2}\s*)?(\(?\d{3}\)?[\s.-]*)\d{3}[\s.-]*\d{4}")
URL_RE = re.compile(r"\bhttps?://\S+|\bwww\.\S+", re.IGNORECASE)

def redact_text(text: str, tokens: list[str]) -> str:
    """MVP redaction: emails/phones/URLs + exact token list (case-insensitive)."""
    redacted = text
    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", redacted)
    redacted = PHONE_RE.sub("[REDACTED_PHONE]", redacted)
    redacted = URL_RE.sub("[REDACTED_URL]", redacted)

    cleaned = [t.strip() for t in tokens if t.strip()]
    cleaned.sort(key=len, reverse=True)
    for tok in cleaned:
        redacted = re.compile(re.escape(tok), re.IGNORECASE).sub("[REDACTED]", redacted)

    return redacted

# -----------------------------
# Sidebar navigation (FIXED)
# -----------------------------
with st.sidebar:
    st.markdown("## Bias Check")
    st.caption("Blind-first evaluation MVP")

    # IMPORTANT: key="nav" makes Streamlit persist the selection across reruns
    st.radio("Navigate", ["Home", "Demo"], key="nav")

    st.markdown("---")
    if st.button("Reset demo"):
        st.session_state.step = 1
        st.session_state.blind_text = ""
        st.session_state.original_text = ""
        st.session_state.score_blind = 5
        st.session_state.notes_blind = ""
        st.rerun()

# Read current page from the radio
page = st.session_state.nav

# =============================
# HOME PAGE
# =============================
if page == "Home":
    st.title("⭐ Bias Check")
    st.subheader("Blind-first evaluation for more intentional decision-making.")

    st.write(
        "Bias Check helps teams evaluate written submissions (resumes, pitches, applications) "
        "based on **substance first**, then intentionally reintroduces identity/context to see "
        "whether it changes judgment."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### Problem")
        st.write(
            "Early signals like name, school, and prestige brands have the ability to influence decisions "
            "before evaluators fully engage with the content."
        )
    with c2:
        st.markdown
