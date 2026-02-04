import re
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Evalia.io", page_icon="🕵️‍♀️", layout="wide")

st.write("DEBUG SUPABASE_URL:", st.secrets.get("SUPABASE_URL"))
st.write("DEBUG HOST:", st.secrets.get("SUPABASE_URL", "").split("//")[-1])

# ---------- SUPABASE AUTH (FIXED) ----------
@st.cache_resource(ttl=300)
def sb_base():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

def sb():
    client = sb_base()
    if st.session_state.get("sb_session"):
        s = st.session_state["sb_session"]
        client.auth.set_session(s["access_token"], s["refresh_token"])
    return client

def login_box():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pw")

    if st.button("Log in"):
        try:
            res = sb_base().auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            st.session_state["sb_session"] = {
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token,
            }
            st.session_state["user"] = res.user
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

def require_login():
    if not st.session_state.get("sb_session"):
        login_box()
        st.stop()

def get_profile():
    uid = st.session_state["user"].id
    return (
        sb()
        .table("profiles")
        .select("*")
        .eq("id", uid)
        .single()
        .execute()
        .data
    )


# ---------- REQUIRE LOGIN ----------
require_login()
profile = get_profile()
role = profile["role"]
st.caption(f"Logged in as {profile['email']} · Role: {role}")

# ---------- NEW ABOVE  ----------



# Session state defaults
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"   # <-- use this for navigation (NOT the radio key)
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
if "score_revealed" not in st.session_state: #newly added
    st.session_state.score_revealed = 5
if "notes_revealed" not in st.session_state:
    st.session_state.notes_revealed = "" #stop


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


# Sidebar navigation (radio controls st.session_state.page via callback)
# -----------------------------
def go_page():
    st.session_state.page = st.session_state.nav_choice

with st.sidebar:
    st.markdown("## Evalia.io")
    st.caption("Blind-first evaluation MVP")

    st.radio(
        "Navigate",
        ["Home", "Demo"],
        key="nav_choice",
        index=0 if st.session_state.page == "Home" else 1,
        on_change=go_page
    )

    st.markdown("---")
    if st.button("Reset demo", key="btn_reset_demo"):
        st.session_state.step = 1
        st.session_state.blind_text = ""
        st.session_state.original_text = ""
        st.session_state.score_blind = 5
        st.session_state.notes_blind = ""
        st.rerun()

    st.markdown("---")
    if st.button("Clear cache (debug)", key="btn_clear_cache"):
        st.cache_resource.clear()
        st.session_state.pop("sb_session", None)
        st.session_state.pop("user", None)
        st.session_state.pop("profile", None)
        st.rerun()

    st.markdown("---")
    if st.button("Log out", key="btn_logout"):
        try:
            sb().auth.sign_out()
        except Exception:
            pass
        st.session_state.pop("sb_session", None)
        st.session_state.pop("user", None)
        st.session_state.pop("profile", None)
        st.cache_resource.clear()
        st.rerun()


# Keep page in sync if user clicks sidebar
page = st.session_state.page


# HOME PAGE
# =============================
if page == "Home":
    st.title("⭐ Evalia.io")
    st.subheader("Blind-first evaluation for more intentional decision-making.")

    st.write(
        "Evalia.io helps teams evaluate written submissions (resumes, pitches, applications) "
        "based on **substance first**, then intentionally reintroduces identity/context to see "
        "whether it changes judgment."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### Problem")
        st.write(
            "Early indicators like name, school, and prestige brands can unconsciously influence decisions "
            "before evaluators fully engage with the content."
        )
    with c2:
        st.markdown("### What we do")
        st.write(
            "We generate a **blind (redacted) version** of any given submission, collect a score, then reveal "
            "identity/context and then collect a second score."
        )
    with c3:
        st.markdown("### Why it matters")
        st.write("Bias becomes observable. Teams can discuss decisions using proper evidence instead of assumptions.")

    st.markdown("---")
    st.markdown("## How it works")
    st.markdown(
        "- The admin will paste a submission (this can be a resume, pitch, or application response)\n"
        "- Admin will add a redaction list (identity/signaling info to hide)\n"
        "- Evaluator scores the blind version\n"
        "- Reveal identity/context and score again\n"
        "- Compare the score change\n"
    )

    st.markdown("## Who it’s for")
    st.markdown(
        "- Student orgs reviewing applicants\n"
        "- Startup teams reviewing pitches\n"
        "- Small teams hiring interns\n"
    )

    st.markdown("## FAQ")
    with st.expander("Is this replacing hiring or selection?"):
        st.write("No. Evalia.io is a lightweight layer that makes sequencing effects visible!")
    with st.expander("Why manual redaction?"):
        st.write("This MVP prioritizes speed and reliability. Automation can come later.")
    with st.expander("What should we redact?"):
        st.write("Names, schools, brand names, locations, links, phone/email—anything that triggers early assumptions.")

    st.write("")
    if st.button("▶ Start demo", type="primary"):
        st.session_state.page = "Demo"      # <-- safe (NOT a widget key)
        st.session_state.step = 1
        st.rerun()

    st.stop()

# DEMO PAGE (3-step flow)
# =============================
st.title("Demo: Blind-first evaluation")
st.caption("Paste → Redact → Score blind → Reveal → Re-score → Compare")

# STEP 1 — INPUT
# -----------------------------
if st.session_state.step == 1:
    st.subheader("1) Input submission")

    submission_text = st.text_area(
        "Paste the submission text",
        height=280,
        placeholder="Paste a resume, pitch paragraph, or application response here.",
        key="submission_text"
    )

    tokens_text = st.text_area(
        "Redact list (one per line)",
        height=160,
        placeholder="Jane Doe\nGeorgetown University\njane.doe@email.com\n(202) 555-0198\nlinkedin.com/in/...",
        key="tokens_text"
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

    score_blind = st.slider("Score (blind)", 1, 10, int(st.session_state.score_blind))
    notes_blind = st.text_area("Notes (blind)", height=100, placeholder="Optional: why this score?")

    if st.button("Reveal identity/context →"):
        st.session_state.score_blind = score_blind
        st.session_state.notes_blind = notes_blind
        st.session_state.step = 3
        st.rerun()

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

    st.info("Optional: paste a clean summary of identity/context signals (name, school, prestige cues).")
    reveal_text = st.text_area(
        "Identity / context (optional)",
        height=110,
        placeholder="Name, school, location, prestige signals, leadership titles, etc."
    )

    score_revealed = st.slider("Score (revealed)", 1, 10, int(st.session_state.score_revealed)) #CHANGED FROM score_revealed = st.slider("Score (revealed)", 1, 10, 5, key="score_revealed")

    notes_revealed = st.text_area("Notes (revealed)", height=100, placeholder="Optional: what changed after reveal?")
    if st.button("See summary →", type="primary"): #added
        st.session_state.score_revealed = score_revealed
        st.session_state.notes_revealed = notes_revealed
        st.session_state.step = 4
        st.rerun() #stop

 



    delta = score_revealed - int(st.session_state.score_blind)
    st.metric("Score change", f"{delta:+d}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Run another demo (reset)"):
            st.session_state.step = 1
            st.session_state.blind_text = ""
            st.session_state.original_text = ""
            st.session_state.score_blind = 5
            st.session_state.notes_blind = ""
            st.rerun()
    with c2:
        if st.button("Back to Home"):
            st.session_state.page = "Home"  # safe
            st.session_state.step = 1
            st.rerun()

# STEP 4 — SUMMARY + COMPARE #added
# -----------------------------
elif st.session_state.step == 4:
    st.subheader("4) Summary + compare")

    blind = int(st.session_state.score_blind)
    revealed = int(st.session_state.score_revealed)
    delta = revealed - blind

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Blind score", blind)
    with c2:
        st.metric("Revealed score", revealed)
    with c3:
        st.metric("Score change", f"{delta:+d}")

    st.markdown("---")
    st.markdown("### Blind notes")
    st.write(st.session_state.notes_blind or "—")

    st.markdown("### Revealed notes")
    st.write(st.session_state.notes_revealed or "—")

    with st.expander("Copy/paste summary"):
        export = f"""
Evalia.io — Summary

Blind score: {blind}
Blind notes:
{st.session_state.notes_blind}

Revealed score: {revealed}
Revealed notes:
{st.session_state.notes_revealed}

Score change: {delta:+d}
"""
        st.code(export, language="text")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back to revealed scoring"):
            st.session_state.step = 3
            st.rerun()
    with c2:
        if st.button("Start over"):
            st.session_state.step = 1
            st.session_state.blind_text = ""
            st.session_state.original_text = ""
            st.session_state.score_blind = 5
            st.session_state.notes_blind = ""
            st.session_state.score_revealed = 5
            st.session_state.notes_revealed = ""
            st.rerun()

