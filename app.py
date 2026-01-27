import re
import streamlit as st
# App step state
if "step" not in st.session_state:
    st.session_state.step = 1


# page setup

st.set_page_config(
    page_title="Bias Check",
    page_icon="🕵️‍♀️",
    layout="wide"
)

st.title("🕵️‍♀️ Bias Check")
st.caption(
    "Blind-first evaluation tool. Generate a redacted version, score it, "
    "reveal identity/context, re-score, and compare how judgments change."
)

# Redaction patterns

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(\+?\d{1,2}\s*)?(\(?\d{3}\)?[\s.-]*)\d{3}[\s.-]*\d{4}")
URL_RE = re.compile(r"\bhttps?://\S+|\bwww\.\S+", re.IGNORECASE)

def redact_text(text: str, tokens: list[str]) -> str:
    """Redact common contact info + user-provided identity tokens."""
    redacted = text
    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", redacted)
    redacted = PHONE_RE.sub("[REDACTED_PHONE]", redacted)
    redacted = URL_RE.sub("[REDACTED_URL]", redacted)

    cleaned = [t.strip() for t in tokens if t.strip()]
    cleaned.sort(key=len, reverse=True)

    for tok in cleaned:
        redacted = re.compile(re.escape(tok), re.IGNORECASE).sub("[REDACTED]", redacted)

    return redacted


# Layout

# -----------------------------
# STEP 1 — INPUT
# -----------------------------
if st.session_state.step == 1:
    st.subheader("1) Input submission")

    submission_text = st.text_area(
        "Paste the submission text",
        height=300,
        placeholder="Paste a resume, pitch paragraph, or application response here."
    )

    tokens_text = st.text_area(
        "Redact list (one per line)",
        height=180,
        placeholder="Jane Doe\nGeorgetown University\njane.doe@email.com"
    )

    if st.button("Generate blind version →", type="primary"):
        if submission_text.strip():
            tokens = [t.strip() for t in tokens_text.splitlines() if t.strip()]
            st.session_state.original_text = submission_text
            st.session_state.blind_text = redact_text(submission_text, tokens)
            st.session_state.step = 2
        else:
            st.error("Please paste submission text first.")

# -----------------------------
# STEP 2 — BLIND REVIEW
# -----------------------------
elif st.session_state.step == 2:
    st.subheader("2) Blind review (identity hidden)")

    st.text_area(
        "Redacted submission",
        value=st.session_state.blind_text,
        height=350,
        disabled=True
    )

    score_blind = st.slider("Score (blind)", 1, 10, 5)
    notes_blind = st.text_area("Notes (blind)", height=100)

    if st.button("Reveal identity/context →"):
        st.session_state.score_blind = score_blind
        st.session_state.notes_blind = notes_blind
        st.session_state.step = 3

# -----------------------------
# STEP 3 — REVEAL + COMPARE
# -----------------------------
elif st.session_state.step == 3:
    st.subheader("3) Identity revealed")
    
    st.markdown("### Original submission (identity revealed)")
    st.text_area(
        "Original (unredacted) text",
        value=st.session_state.original_text,
        height=300,
        disabled=True
    )

    reveal_text = st.text_area(
        "Identity / context",
        height=120,
        placeholder="Name, school, location, prestige signals"
    )

    st.success("Identity/context revealed")
    st.write(reveal_text if reveal_text.strip() else "_(none provided)_")

    score_revealed = st.slider("Score (revealed)", 1, 10, 5)
    notes_revealed = st.text_area("Notes (revealed)", height=100)

    delta = score_revealed - st.session_state.score_blind
    st.metric("Score change", f"{delta:+d}")

