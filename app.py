import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO
import requests

# --- 1. CONFIG & DARK THEME STYLE ---
st.set_page_config(page_title="Claudio - SEO Consultant", page_icon="🕴️", layout="wide")

st.markdown("""
    <style>
    /* Fondo oscuro para toda la app */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    /* Avatar circular */
    .claudio-avatar {
        border-radius: 50%;
        border: 2px solid #34495E;
        width: 150px;
        display: block;
        margin: auto;
    }
    /* Estilo de los inputs y radio buttons en modo oscuro */
    .stTextInput>div>div>input {
        color: white;
        background-color: #262730;
    }
    /* Botón principal estilo corporativo */
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2563EB;
        border: none;
    }
    /* Tarjetas de métricas para modo oscuro */
    .metric-card {
        background-color: #1A1C23;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #34495E;
        text-align: center;
        color: white;
    }
    /* Color de los títulos */
    h1, h2, h3, h4 {
        color: #F8FAFC !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API KEYS ---
AHREFS_KEY = st.secrets.get("AHREFS_API_KEY", None)
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", None)

if not GEMINI_KEY:
    st.error("⚠️ Gemini API Key is missing in Secrets!")
    st.stop()

# --- 3. CLAUDIO'S HEADER ---
col_img, col_txt = st.columns([1, 4])
with col_img:
    # Restaurada la imagen previa del avatar profesional
    st.markdown('<img src="https://cdn-icons-png.flaticon.com/512/4042/4042356.png" class="claudio-avatar">', unsafe_allow_html=True)
with col_txt:
    st.title("Claudio: AI SEO Consultant")
    st.markdown("### Delivering international executive audits.")
    st.write("Ready to analyze your next target.")

st.markdown("---")

# --- 4. AUDIT LOGIC ---
url_input = st.text_input("🌐 Target URL:", placeholder="https://example.com")

if AHREFS_KEY:
    audit_selection = st.radio("Select Audit Type:", ["Basic (Visual Overview)", "Full (Ahrefs Integration)"], index=0, horizontal=True)
else:
    st.warning("🕵️ Ahrefs API Key not found. Only 'Basic Visual Audit' is available.")
    audit_selection = "Basic (Visual Overview)"

confirm_full = True
if audit_selection == "Full (Ahrefs Integration)":
    st.info("💡 Note: This will consume Ahrefs API credits.")
    confirm_full = st.checkbox("Confirm Full Ahrefs Audit", value=False)

if st.button("🕴️ START AUDIT"):
    if not url_input:
        st.error("Please enter a URL.")
    elif audit_selection == "Full (Ahrefs Integration)" and not confirm_full:
        st.warning("Please confirm the Ahrefs audit to proceed.")
    else:
        with st.spinner('Claudio is processing...'):
            try:
                genai.configure(api_key=GEMINI_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                
                report_content = ""
                metrics = {"DR": "N/A", "Links": "N/A", "Type": audit_selection}

                if audit_selection == "Full (Ahrefs Integration)":
                    target = url_input.replace("https://", "").replace("http://", "").strip("/")
                    headers = {"Authorization": f"Bearer {AHREFS_KEY}"}
                    api_res = requests.get(f"https://api.ahrefs.com/v3/site-explorer/overview?target={target}&output=json", headers=headers)
                    data = api_res.json()
                    metrics["DR"] = data.get('metrics', {}).get('domain_rating', 'N/A')
                    metrics["Links"] = data.get('metrics', {}).get('backlinks', 'N/A')
                    
                    prompt = f"Act as Claudio. Analyze {url_input} with DR {metrics['DR']} and {metrics['Links']} backlinks. Detailed SEO audit in English."
                else:
                    prompt = f"Act as Claudio. Provide a professional visual/strategic SEO overview for {url_input} in English. Focus on UX and Quick Wins."
                
                response = model.generate_content(prompt)
                report_content = response.text

                # UI RESULTS
                st.balloons()
                st.success("Audit Completed Successfully.")
                
                c1, c2, c3 = st.columns(3)
                c1.markdown(f'<div class="metric-card"><h4>Domain Rating</h4><h2>{metrics["DR"]}</h2></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-card"><h4>Backlinks</h4><h2>{metrics["Links"]}</h2></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-card"><h4>Audit Type</h4><p>{metrics["Type"]}</p></div>', unsafe_allow_html=True)

                with st.expander("📜 Preview Report"):
                    st.markdown(report_content)

                doc = Document()
                doc.add_heading(f'SEO Audit: {url_input}', 0)
                doc.add_paragraph(report_content)
                buf = BytesIO()
                doc.save(buf)
                st.download_button("📥 DOWNLOAD REPORT (DOCX)", buf.getvalue(), f"Claudio_Audit.docx")
                
            except Exception as e:
                st.error(f"Error: {e}")

# SIDEBAR
with st.sidebar:
    st.header("Office Status")
    st.write("Ahrefs API:", "🟢 Connected" if AHREFS_KEY else "🔴 Disconnected")
