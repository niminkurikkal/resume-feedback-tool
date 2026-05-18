import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import fitz
from groq import Groq
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Clients
client = Groq(api_key="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")
supabase = create_client(
    "https://qtvdplgsoijdmotqsien.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF0dmRwbGdzb2lqZG1vdHFzaWVuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwODk5NDQsImV4cCI6MjA5NDY2NTk0NH0.bGdK25f0TbkfWUTuzHfyF_rnPaEmq13v2_bN310FGm0"
)

# Database functions
def save_score(email, score, job_title=""):
    supabase.table("score_history").insert({
        "user_email": email,
        "score": score,
        "job_title": job_title[:100]
    }).execute()

def load_history(email):
    result = supabase.table("score_history").select("*").eq("user_email", email).order("created_at").execute()
    if result.data:
        return pd.DataFrame(result.data)
    return pd.DataFrame(columns=["user_email", "score", "job_title", "created_at"])

st.set_page_config(page_title="Resume Feedback Tool", page_icon="📄", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Montserrat', sans-serif !important; }
.stApp { background: #0e1117; }
.main-title { font-size: 36px; font-weight: 700; color: white; margin: 0 0 8px; line-height: 1.2; }
.sub-title { font-size: 14px; color: #666; margin-bottom: 2rem; }
.card { background: #1e2130; border: 1px solid #2d3148; border-radius: 14px; padding: 1.25rem; margin-bottom: 1rem; }
.card-label { font-size: 11px; font-weight: 600; color: #666; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 10px; }
.metric-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin: 1rem 0; }
.metric-box { background: #151820; border-radius: 12px; padding: 16px; text-align: center; }
.metric-num { font-size: 32px; font-weight: 700; font-family: 'Montserrat', sans-serif; }
.metric-label { font-size: 11px; color: #666; margin-top: 4px; font-family: 'Montserrat', sans-serif; }
.keyword-chip { display: inline-block; padding: 4px 12px; border-radius: 99px; font-size: 12px; margin: 3px 4px 3px 0; font-family: 'Montserrat', sans-serif; }
.chip-green { background: #0d2b1a; color: #4ade80; border: 1px solid #1a5c35; }
.chip-red { background: #2b0d0d; color: #f87171; border: 1px solid #5c1a1a; }
.advice-box { background: #12162a; border-left: 3px solid #5B6BF8; border-radius: 0 10px 10px 0; padding: 14px 16px; font-size: 13px; color: #aaa; line-height: 1.8; font-family: 'Montserrat', sans-serif; }
.strength-item { display: flex; align-items: flex-start; gap: 8px; padding: 8px 0; border-bottom: 1px solid #2d3148; font-size: 13px; color: #ccc; font-family: 'Montserrat', sans-serif; }
.strength-item:last-child { border-bottom: none; }
.dot-green { width: 8px; height: 8px; border-radius: 50%; background: #4ade80; flex-shrink: 0; margin-top: 4px; }
.dot-red { width: 8px; height: 8px; border-radius: 50%; background: #f87171; flex-shrink: 0; margin-top: 4px; }
.stButton > button { background: linear-gradient(135deg, #5B6BF8, #8b5cf6) !important; color: white !important; font-family: 'Montserrat', sans-serif !important; font-weight: 600 !important; font-size: 15px !important; border-radius: 12px !important; border: none !important; padding: 16px !important; width: 100% !important; }
.stTextArea textarea { background: #151820 !important; border: 1px solid #2d3148 !important; border-radius: 10px !important; color: #ccc !important; font-family: 'Montserrat', sans-serif !important; font-size: 13px !important; }
.stTextInput input { background: #151820 !important; border: 1px solid #2d3148 !important; border-radius: 10px !important; color: #ccc !important; font-family: 'Montserrat', sans-serif !important; font-size: 13px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📄 Resume Feedback Tool</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Upload your resume and paste a job description — get instant AI feedback</div>', unsafe_allow_html=True)

# Email login
st.markdown('<div class="card-label">👤 Enter your email to save your progress</div>', unsafe_allow_html=True)
user_email = st.text_input("", placeholder="yourname@email.com", label_visibility="collapsed")

st.markdown('<div class="card-label" style="margin-top:1rem">📎 Upload your resume (PDF)</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("", type="pdf", label_visibility="collapsed")

resume_text = ""
if uploaded_file is not None:
    page_count = 0
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        page_count = len(doc)
        for page in doc:
            resume_text += page.get_text()
    st.success(f"✅ {uploaded_file.name} uploaded · {page_count} page(s) detected")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="card-label">💼 Paste the job description</div>', unsafe_allow_html=True)
jd = st.text_area("", height=200, placeholder="Paste the full job description here...", label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)
analyse = st.button("🔍 Analyse My Resume")

if analyse:
    if not user_email.strip():
        st.warning("Please enter your email first to save your progress.")
    elif not resume_text:
        st.warning("Please upload your resume PDF first.")
    elif not jd.strip():
        st.warning("Please paste a job description.")
    else:
        with st.spinner("Analysing your resume..."):
            prompt = f"""
You are a professional resume coach and ATS expert.
Analyse the resume against the job description. Return in EXACTLY this format:

ATS SCORE: [number 0-100]
MATCHED KEYWORDS: [comma separated list]
MISSING KEYWORDS: [comma separated list]
STRENGTHS:
- [point 1]
- [point 2]
- [point 3]
WEAKNESSES:
- [point 1]
- [point 2]
- [point 3]
TOP ADVICE:
[2-3 clear sentences]

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd}
"""
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content

        st.markdown("---")
        st.markdown('<div class="card-label" style="font-size:14px; color:white; margin-bottom:1rem;">📊 Your Results</div>', unsafe_allow_html=True)

        lines = result.split('\n')
        score = matched = missing = strengths_raw = weaknesses_raw = advice = ""
        section = ""

        for line in lines:
            line = line.strip()
            if line.startswith("ATS SCORE:"):
                score = line.replace("ATS SCORE:", "").strip().replace("/100", "")
            elif line.startswith("MATCHED KEYWORDS:"):
                matched = line.replace("MATCHED KEYWORDS:", "").strip()
            elif line.startswith("MISSING KEYWORDS:"):
                missing = line.replace("MISSING KEYWORDS:", "").strip()
            elif line.startswith("STRENGTHS:"):
                section = "strengths"
            elif line.startswith("WEAKNESSES:"):
                section = "weaknesses"
            elif line.startswith("TOP ADVICE:"):
                section = "advice"
            elif line.startswith("- ") and section == "strengths":
                strengths_raw += line[2:] + "|"
            elif line.startswith("- ") and section == "weaknesses":
                weaknesses_raw += line[2:] + "|"
            elif section == "advice" and line:
                advice += line + " "

        try:
            digits = ''.join(filter(str.isdigit, score))
            score_num = int(digits[:3]) if digits else 0
            save_score(user_email, score_num, jd[:100])
            score_color = "#4ade80" if score_num >= 75 else "#facc15" if score_num >= 50 else "#f87171"
    
            
        except:
            score_num = "—"
            score_color = "#888"

        matched_list = [k.strip() for k in matched.split(",") if k.strip()]
        missing_list = [k.strip() for k in missing.split(",") if k.strip()]

        st.markdown(f"""
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-num" style="color:{score_color}">{score_num}</div>
                <div class="metric-label">ATS Score / 100</div>
            </div>
            <div class="metric-box">
                <div class="metric-num" style="color:#4ade80">{len(matched_list)}</div>
                <div class="metric-label">Matched keywords</div>
            </div>
            <div class="metric-box">
                <div class="metric-num" style="color:#f87171">{len(missing_list)}</div>
                <div class="metric-label">Missing keywords</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-label">✅ Matched keywords</div>', unsafe_allow_html=True)
        chips = " ".join([f'<span class="keyword-chip chip-green">{k}</span>' for k in matched_list])
        st.markdown(chips or "<span style='color:#666; font-size:13px;'>None found</span>", unsafe_allow_html=True)
        st.markdown('<div class="card-label" style="margin-top:14px">❌ Missing keywords</div>', unsafe_allow_html=True)
        chips2 = " ".join([f'<span class="keyword-chip chip-red">{k}</span>' for k in missing_list])
        st.markdown(chips2 or "<span style='color:#666; font-size:13px;'>None missing!</span>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-label">💪 Strengths</div>', unsafe_allow_html=True)
            for s in strengths_raw.split("|"):
                if s.strip():
                    st.markdown(f'<div class="strength-item"><div class="dot-green"></div>{s.strip()}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-label">⚠️ Weaknesses</div>', unsafe_allow_html=True)
            for w in weaknesses_raw.split("|"):
                if w.strip():
                    st.markdown(f'<div class="strength-item"><div class="dot-red"></div>{w.strip()}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card-label">🎯 Top advice</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="advice-box">{advice.strip()}</div>', unsafe_allow_html=True)

        # Score History Chart
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card-label">📈 Your ATS score history</div>', unsafe_allow_html=True)

        history = load_history(user_email)
        if len(history) >= 2:
            fig, ax = plt.subplots(figsize=(8, 3))
            fig.patch.set_facecolor('#1e2130')
            ax.set_facecolor('#151820')
            history['created_at'] = pd.to_datetime(history['created_at'])
            ax.plot(history['created_at'], history['score'], color='#5B6BF8', linewidth=2.5, marker='o', markersize=7, markerfacecolor='#5B6BF8', markeredgecolor='white', markeredgewidth=1.5)
            ax.fill_between(history['created_at'], history['score'], alpha=0.15, color='#5B6BF8')
            ax.set_ylim(0, 100)
            ax.set_ylabel('ATS Score', color='#888', fontsize=11)
            ax.tick_params(colors='#888', labelsize=9)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
            plt.xticks(rotation=30)
            for spine in ax.spines.values():
                spine.set_edgecolor('#2d3148')
            ax.grid(axis='y', color='#2d3148', linestyle='--', alpha=0.5)
            ax.axhline(y=75, color='#4ade80', linestyle='--', alpha=0.4, linewidth=1)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            st.markdown(f"""
            <div style="display:flex; gap:10px; margin-top:10px;">
                <div class="metric-box" style="background:#151820; border-radius:10px; padding:12px; text-align:center; flex:1;">
                    <div class="metric-num" style="font-size:22px; color:#4ade80;">{int(history['score'].max())}</div>
                    <div class="metric-label">Best score</div>
                </div>
                <div class="metric-box" style="background:#151820; border-radius:10px; padding:12px; text-align:center; flex:1;">
                    <div class="metric-num" style="font-size:22px; color:#5B6BF8;">{int(history['score'].mean())}</div>
                    <div class="metric-label">Average score</div>
                </div>
                <div class="metric-box" style="background:#151820; border-radius:10px; padding:12px; text-align:center; flex:1;">
                    <div class="metric-num" style="font-size:22px; color:#facc15;">{len(history)}</div>
                    <div class="metric-label">Total analyses</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:13px; color:#666; padding:10px 0;">Analyse your resume at least twice to see your score history chart.</div>', unsafe_allow_html=True)