import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO
import requests

# --- 1. PAGE CONFIG & IDENTITY ---
st.set_page_config(page_title="Claudio - Your SEO Consultant", page_icon="🕴️", layout="wide")

# CUSTOM CSS FOR CLAUDIO (BROWN SKIN AVATAR & NAVY THEME)
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .claudio-avatar { border-radius: 50%; border: 3px solid #0E2A47; width: 150px; display: block; margin: auto; }
    .stButton>button { background-color: #0E2A47; color: white; border-radius: 8px; font-weight: bold; height: 3em; }
    .metric-card { background-color: white; padding: 15px; border-radius: 12px; border-left: 5px solid #0E2A47; text-align: center; }
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
    # Avatar de consultor con piel marrón
    st.markdown('<img src="https://cdn-icons-png.flaticon.com/512/4042/4042424.png" class="claudio-avatar">', unsafe_allow_html=True)
with col_txt:
    st.title("Hello, I'm Claudio.")
    st.markdown("### Your Senior SEO Consultant.")
    st.write("I'll prepare a professional audit for you. Just provide the URL.")

st.markdown("---")

# --- 4. AUDIT SELECTION LOGIC ---
url_input = st.text_input("🌐 Target URL:", placeholder="https://example.com")

# Opciones de auditoría
if AHREFS_KEY:
    audit_selection = st.radio("Select Audit Type:", ["Basic (Visual Overview)", "Full (Ahrefs Integration)"], index=0, horizontal=True)
else:
    st.warning("🕵️ Ahrefs API Key not found. Only 'Basic Visual Audit' is available.")
    audit_selection = "Basic (Visual Overview)"

# Mensaje de confirmación para auditoría Full
confirm_full = True
if audit_selection == "Full (Ahrefs Integration)":
    st.info("💡 Note: This will use Ahrefs API credits.")
    confirm_full = st.checkbox("I confirm I want to run a Full Ahrefs Audit", value=False)

if st.button("🕴️ START AUDIT"):
    if not url_input:
        st.error("Please enter a URL.")
    elif audit_selection == "Full (Ahrefs Integration)" and not confirm_full:
        st.warning("Please check the confirmation box to proceed with the Full Audit.")
    else:
        with st.spinner('Claudio is working on the report...'):
            try:
                # Configuración de Gemini (Usando el modelo más estable para evitar el error NotFound)
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

                    prompt = f"Act as Claudio. Analyze {url_input} with DR {metrics['DR']} and {metrics['Links']} backlinks. Provide a deep professional SEO audit in English. Include a Priority Matrix table."
                else:
                    prompt = f"Act as Claudio. Provide a professional visual/strategic SEO overview for {url_input} in English. Focus on UX, Search Intent, and Quick Wins."
                
                response = model.generate_content(prompt)
                report_content = response.text

                # RESULTADOS VISUALES
                st.balloons()
                st.success(f"Audit completed: {audit_selection}")
                
                c1, c2, c3 = st.columns(3)
                c1.markdown(f'<div class="metric-card"><h4>Domain Rating</h4><h2>{metrics["DR"]}</h2></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-card"><h4>Backlinks</h4><h2>{metrics["Links"]}</h2></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-card"><h4>Status</h4><p>Completed</p></div>', unsafe_allow_html=True)

                with st.expander("📜 Preview Report"):
                    st.markdown(report_content)

                # DOCUMENTO WORD
                doc = Document()
                doc.add_heading(f'SEO Audit: {url_input}', 0)
                doc.add_paragraph(report_content)
                buf = BytesIO()
                doc.save(buf)
                st.download_button("📥 DOWNLOAD DOCX", buf.getvalue(), f"Claudio_Audit_{target if 'target' in locals() else 'basic'}.docx")
                
            except Exception as e:
                st.error(f"Claudio encountered an error: {e}")

# SIDEBAR
with st.sidebar:
    st.header("🏛️ Office Status")
    if AHREFS_KEY:
        st.success("Ahrefs API: Connected")
    else:
        st.error("Ahrefs API: Disconnected")
