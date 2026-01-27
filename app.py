import re
import streamlit as st

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Bias Check", page_icon="🕵️‍♀️", layout="wide")

# -----------------------------
# Session state defaults
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "nav" not in st.session_state:
    st.session_state.nav = "Home"
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

    st.radio("Navigate", ["Home", "Demo"], key="nav")
    st.session_state.page = st.session_state.nav

    st.markdown("---")
    if st.button("Reset demo"):
        st.session_state.step = 1
        st.session_state.blind_text = ""
        st.session_state.original_text = ""
        st.session_state.score_blind = 5
        st.session_state.notes_blind = ""
        st.rerun()

# =============================
# HOME PAGE
# =============================
if st.session_state.page == "Home":
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
            "Early signals like name, school, and prestige brands can influence decisions "
            "before reviewers fully engage with the content."
        )
    with c2:
        st.markdown("### What we do")
        st.write(
            "We generate a blind (redacted) version of a submission, collect a score, then "
            "reveal identity/context and collect a second score."
        )
    with c3:
        st.markdown("### Why it matters")
        st.write("Bias becomes observable. Teams can discuss decisions using evidence.")

    st.markdown("---")
    if st.button("▶ Start demo", type="primary"):
        st.session_state.nav = "Demo"
        st.session_state.page = "Demo"
        st.session_state.step = 1
        st.rerun()

    st.stop()

# =============================
# DEMO PAGE
# =============================
st.title("Demo: Blind-first evaluation")
st.caption("Paste → Redact → Score blind → Reveal → Re-score → Compare")

# -----------------------------
# STEP 1 — INPUT
# -----------------------------
if st.session_state.step == 1:
    st.subheader("1) Input submission")

    submission_text = st.text_area(
        "Paste the submission text",
        height=280
    )

    tokens_text = st.text_area(
        "Redact list (one per line)",
        height=160
    )

    if st.button("Generate blind version →", type="primary"):
        if submission_text.strip():
            tokens = [t.strip() for t in tokens_text.splitlines() if t.strip()]
            st.session_state.original_text = submission_text
            st.session_state.blind_text = redact_text(submission_text, tokens)
            st.session_state.step = 2
            st.rerun()
        else:
            st.error("Please paste submission text first.")

# -----------------------------
# STEP 2 — BLIND REVIEW
# -----------------------------
elif st.session_state.step == 2:
    st.subheader("2) Blind review (identity hidden)")

    st.text_area(
        "Redacted submission (blind view)",
        value=st.session_state.blind_text,
        height=320,
        disabled=True
    )

    score_blind = st.slider("Score (blind)", 1, 10, st.session_state.score_blind)
    notes_blind = st.text_area("Notes (blind)", height=100)

    if st.button("Reveal identity/context →"):
        st.session_state.score_blind = score_blind
        st.session_state.notes_blind = notes_blind
        st.session_state.step = 3
        st.rerun()

# -----------------------------
# STEP 3 — REVEAL + COMPARE
# -----------------------------
elif st.session_state.step == 3:
    st.subheader("3) Identity revealed + compare")

    st.text_area(
        "Original (unredacted) text",
        value=st.session_state.original_text,
        height=240,
        disabled=True
    )

    score_revealed = st.slider("Score (revealed)", 1, 10, 5)
    delta = score_revealed - st.session_state.score_blind
    st.metric("Score change", f"{delta:+d}")

    if st.button("Back to Home"):
        st.session_state.nav = "Home"
        st.session_state.page = "Home"
        st.session_state.step = 1
        st.rerun()
