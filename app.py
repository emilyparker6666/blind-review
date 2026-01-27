import re
import streamlit as st

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

left, right = st.columns([1.1, 0.9], gap="large")


# LEFT COLUMN: INPUTS

with left:
    st.subheader("1) Input submission")

    submission_type = st.selectbox(
        "Submission type",
        ["Resume", "Startup pitch paragraph", "Application response", "Other"]
    )

    submission_text = st.text_area(
        "Paste the submission text",
        height=260,
        placeholder="Paste a resume, pitch paragraph, or application response here."
    )

    st.subheader("2) Admin-provided redaction list")
    st.write(
        "Paste identity or signaling information you want removed "
        "(one item per line)."
    )

    tokens_text = st.text_area(
        "Redact list (one per line)",
        height=160,
        placeholder=(
            "Example:\n"
            "Jane Doe\n"
            "Georgetown University\n"
            "McDonough School of Business\n"
            "jane.doe@email.com\n"
            "(202) 555-0198\n"
            "linkedin.com/in/janedoe"
        )
    )

    generate = st.button(
        "Generate blind (redacted) version",
        type="primary",
        use_container_width=True
    )


# RIGHT COLUMN: BLIND VIEW + SCORING

with right:
    st.subheader("Blind version (what evaluator sees first)")

    if "blind_text" not in st.session_state:
        st.session_state.blind_text = ""

    if generate:
        if not submission_text.strip():
            st.error("Please paste submission text first.")
        else:
            tokens = [ln.strip() for ln in tokens_text.splitlines() if ln.strip()]
            st.session_state.blind_text = redact_text(submission_text, tokens)

    st.text_area(
        "Redacted (blind) text",
        value=st.session_state.blind_text,
        height=260,
        disabled=True
    )

    st.divider()
    st.subheader("3) Blind scoring")

    st.write(
        "**Rubric (1–10):** Score overall quality based on clarity, substance, and fit."
    )

    score_blind = st.slider("Score (blind)", 1, 10, 5)
    notes_blind = st.text_area(
        "Notes (blind)",
        height=90,
        placeholder="Optional: why this score?"
    )

    st.divider()
    st.subheader("4) Reveal identity / context")

    st.info(
        "Admin or submitter: paste identity/context information here BEFORE revealing. "
        "The evaluator should not read this until after blind scoring."
    )

    reveal_text = st.text_area(
        "Identity / context to reveal later",
        height=110,
        placeholder="Name, school, location, prestige signals, leadership titles, etc."
    )

    if "revealed" not in st.session_state:
        st.session_state.revealed = False

    reveal = st.button("Reveal identity / context", use_container_width=True)

    if reveal:
        st.session_state.revealed = True

    if st.session_state.revealed:
        st.success("Identity / context revealed:")
        st.write(reveal_text if reveal_text.strip() else "_(none provided)_")

        st.subheader("5) Revealed scoring")

        score_revealed = st.slider(
            "Score (revealed)",
            1,
            10,
            5,
            key="score_revealed"
        )

        notes_revealed = st.text_area(
            "Notes (revealed)",
            height=90,
            placeholder="Optional: what changed after seeing identity/context?"
        )

        delta = score_revealed - score_blind
        st.metric("Score change", f"{delta:+d}")

        with st.expander("Copy / paste session export (for assignment submission)"):
            export = f"""
Bias Check — Session Export

Submission type: {submission_type}

Blind score (1–10): {score_blind}
Blind notes:
{notes_blind}

Revealed identity / context:
{reveal_text}

Revealed score (1–10): {score_revealed}
Revealed notes:
{notes_revealed}

Score change: {delta:+d}
"""
            st.code(export, language="text")

st.caption(
    "MVP note: Redaction uses pattern-based removal (email/phone/URL) "
    "plus a user-provided redaction list. Focus is on evaluation sequencing."
)
