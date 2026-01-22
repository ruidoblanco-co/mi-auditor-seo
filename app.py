import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# --- 1. PAGE CONFIG & IDENTITY ---
st.set_page_config(
    page_title="Claudio - Your SEO Consultant",
    page_icon="🕴️", 
    layout="wide"
)

# --- 2. CSS STYLES (CLAUDIO'S CORPORATE THEME) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #f0f2f6;
    }
    .claudio-avatar {
        border-radius: 50%;
        border: 3px solid #0E2A47;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        width: 150px;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    .stButton>button {
        background-color: #0E2A47;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1c4e82;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #0E2A47;
        text-align: center;
    }
    h1, h2, h3 {
        color: #0E2A47 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. KEY MANAGEMENT ---
try:
    AHREFS_KEY = st.secrets["AHREFS_API_KEY"]
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ Credentials missing! Please check Streamlit Secrets.")
    st.stop()

# --- 4. CLAUDIO'S HEADER ---
col_img, col_txt = st.columns([1, 4])

with col_img:
    # Professional avatar
    st.markdown('<img src="https://cdn-icons-png.flaticon.com/512/4042/4042356.png" class="claudio-avatar">', unsafe_allow_html=True)

with col_txt:
    st.title("Hello, I'm Claudio.")
    st.markdown("### Your Personal SEO Consultant, 24/7.")
    st.write("Provide a URL, and I will prepare an executive audit report in English immediately.")

st.markdown("---")

# --- 5. MAIN INTERFACE ---
with st.container():
    url_input = st.text_input("🌐 Client URL to audit:", placeholder="https://example.com")
    boton = st.button("🕴️ CLAUDIO, ANALYZE THIS!")

if boton and url_input:
    target = url_input.replace("https://", "").replace("http://", "").strip("/")
    
    with st.spinner(f'Claudio is reviewing {target}. Please stand by...'):
        # --- DATA FETCHING (Ahrefs simulation) ---
        dr = 52
        backlinks = 3420
        
        # --- GEMINI BRAIN ---
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # PROMPT IN ENGLISH
        prompt = f"""
        Act as Claudio, a sophisticated Senior SEO Consultant.
        Data for {target}: DR {dr}, Backlinks {backlinks}.
        
        Write a professional SEO Audit in English. The tone should be expert and corporate.
        Structure:
        1. EXECUTIVE SUMMARY: High-level overview.
        2. AUTHORITY ANALYSIS: Insights on DR and Link Profile.
        3. PRIORITY ACTION TABLE: (Action | Estimated Impact | Difficulty).
        4. TECHNICAL RECOMMENDATIONS: Top 3 things to fix.
        
        End the report with an elegant closing statement from a high-level consultant.
        """
        report_content = model.generate_content(prompt).text
        
        # --- VISUAL RESULTS ---
        st.success("✅ Audit completed. Here is your summary:")
        
        # Claudio Style Cards
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><h4>Domain Rating</h4><h2>{dr}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h4>Total Backlinks</h4><h2>{backlinks}</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><h4>Claudio\'s Verdict</h4><h2>Promising</h2></div>', unsafe_allow_html=True)
        
        st.write(" ")
        with st.expander("📜 Preview the report on screen"):
            st.markdown(report_content)

        # --- WORD DOWNLOAD ---
        doc = Document()
        doc.add_heading(f'SEO Audit Report: {target}', 0)
        doc.add_paragraph("Audited by: Claudio (AI Consultant)")
        doc.add_paragraph(report_content)
        buffer = BytesIO()
        doc.save(buffer)
        
        st.download_button(
            label="📥 DOWNLOAD OFFICIAL REPORT (DOCX)",
            data=buffer.getvalue(),
            file_name=f"Claudio_Audit_{target}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# --- SIDEBAR ---
with st.sidebar:
    st.header("🏛️ Claudio's Office")
    st.info("System operational and ready for new audits.")
    st.write("Remember: SEO is not a cost, it's an investment.")
