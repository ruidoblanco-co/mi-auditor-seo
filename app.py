import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO
import requests

# --- 1. CONFIG & DARK THEME ---
st.set_page_config(page_title="Claudio - Gemini 3 SEO", page_icon="🕴️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    .claudio-avatar { border-radius: 50%; border: 3px solid #4FB3FF; width: 150px; display: block; margin: auto; }
    .stMarkdown, p, span, label { color: #FFFFFF !important; }
    .stTextInput>div>div>input { color: white !important; background-color: #262730 !important; }
    div[data-baseweb="radio"] label { color: white !important; }
    .stButton>button { background-color: #1E3A8A; color: white !important; border-radius: 8px; font-weight: bold; width: 100%; border: none; }
    .metric-card { background-color: #1A1C23; padding: 20px; border-radius: 12px; border: 1px solid #34495E; text-align: center; }
    h1, h2, h3 { color: #4FB3FF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API KEYS RETRIEVAL ---
# Usamos .get y comprobamos que no sea una cadena vacía
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "").strip()
AHREFS_KEY = st.secrets.get("AHREFS_API_KEY", "").strip()

# --- 3. SIDEBAR STATUS ---
with st.sidebar:
    st.header("🏛️ Office Status")
    
    # Estado de Gemini (Crítico)
    if GEMINI_KEY and len(GEMINI_KEY) > 10:
        st.success("Gemini 3 API: 🟢 Connected")
    else:
        st.error("Gemini 3 API: 🔴 Missing")
        st.stop() # Si no hay Gemini, la app no puede funcionar

    # Estado de Ahrefs (Opcional)
    has_ahrefs = False
    if AHREFS_KEY and len(AHREFS_KEY) > 10:
        has_ahrefs = True
        st.success("Ahrefs API: 🟢 Connected")
    else:
        has_ahrefs = False
        st.warning("Ahrefs API: 🔴 Disconnected")
        st.info("Using 'Basic Visual Audit' mode only.")

# --- 4. HEADER ---
col_img, col_txt = st.columns([1, 4])
with col_img:
    st.markdown('<img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" class="claudio-avatar">', unsafe_allow_html=True)
with col_txt:
    st.title("Claudio: Powered by Gemini 3")
    st.write("Specialized in Executive SEO Audits.")

st.markdown("---")

# --- 5. AUDIT INTERFACE ---
url_input = st.text_input("🌐 Target URL:", placeholder="https://example.com")

# Selección dinámica según disponibilidad de API
if has_ahrefs:
    audit_selection = st.radio("Choose Depth:", ["Basic (Visual Overview)", "Full (Ahrefs Integration)"], index=0, horizontal=True)
else:
    st.info("Mode: **Basic Visual Audit** (Ahrefs integration is disabled).")
    audit_selection = "Basic (Visual Overview)"

# Confirmación para auditoría Full
confirm_full = True
if audit_selection == "Full (Ahrefs Integration)":
    st.warning("🚨 This will consume Ahrefs API credits.")
    confirm_full = st.checkbox("I confirm I want to perform a Full Ahrefs Audit", value=False)

if st.button("🕴️ START AUDIT"):
    if not url_input:
        st.error("Please enter a URL first.")
    elif audit_selection == "Full (Ahrefs Integration)" and not confirm_full:
        st.warning("Please check the confirmation box to proceed.")
    else:
        with st.spinner('Claudio is analyzing the data...'):
            try:
                genai.configure(api_key=GEMINI_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash') # He vuelto a 1.5 por estabilidad, pero podemos probar gemini-3 si tu API lo admite
                
                metrics = {"DR": "N/A", "Links": "N/A"}
                
                if audit_selection == "Full (Ahrefs Integration)":
                    target = url_input.replace("https://", "").replace("http://", "").strip("/")
                    headers = {"Authorization": f"Bearer {AHREFS_KEY}"}
                    api_res = requests.get(f"https://api.ahrefs.com/v3/site-explorer/overview?target={target}&output=json", headers=headers)
                    data = api_res.json()
                    metrics["DR"] = data.get('metrics', {}).get('domain_rating', 'N/A')
                    metrics["Links"] = data.get('metrics', {}).get('backlinks', 'N/A')
                    
                    prompt = f"Act as Claudio. Analyze {url_input} with DR {metrics['DR']} and {metrics['Links']} backlinks. Write a professional SEO audit in English."
                else:
                    prompt = f"Act as Claudio. Provide a professional visual/strategic SEO overview for {url_input} in English. Focus on UX and Strategic Wins."

                response = model.generate_content(prompt)
                
                # MOSTRAR RESULTADOS
                st.balloons()
                c1, c2, c3 = st.columns(3)
                c1.markdown(f'<div class="metric-card"><h4>DR</h4><h2>{metrics["DR"]}</h2></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-card"><h4>Links</h4><h2>{metrics["Links"]}</h2></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-card"><h4>Level</h4><p>{audit_selection}</p></div>', unsafe_allow_html=True)

                st.markdown("### 📝 Report Preview")
                st.markdown(response.text)

                # Generar Word
                doc = Document()
                doc.add_heading(f'SEO Audit: {url_input}', 0)
                doc.add_paragraph(response.text)
                buf = BytesIO()
                doc.save(buf)
                st.download_button("📥 DOWNLOAD REPORT", buf.getvalue(), f"Claudio_Audit.docx")

            except Exception as e:
                st.error(f"Error: {e}")
