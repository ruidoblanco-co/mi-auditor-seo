import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO
import requests

# --- 1. CONFIG & DARK THEME ---
st.set_page_config(page_title="Claudio - SEO Consultant", page_icon="🕴️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    .claudio-avatar { border-radius: 50%; border: 3px solid #4FB3FF; width: 150px; display: block; margin: auto; }
    /* Forzar visibilidad de textos */
    .stMarkdown, p, span, label, .stSelectbox, .stRadio { color: #FFFFFF !important; }
    .stTextInput>div>div>input { color: white !important; background-color: #262730 !important; }
    .stButton>button { background-color: #1E3A8A; color: white !important; border-radius: 8px; font-weight: bold; width: 100%; border: none; }
    .metric-card { background-color: #1A1C23; padding: 20px; border-radius: 12px; border: 1px solid #34495E; text-align: center; }
    h1, h2, h3 { color: #4FB3FF !important; }
    /* Fix para los labels de los Radio Buttons */
    div[data-baseweb="radio"] div { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API KEYS REAL CHECK ---
def get_secret(key):
    try:
        val = st.secrets[key]
        return val if val and str(val).strip() != "" else None
    except:
        return None

GEMINI_KEY = get_secret("GEMINI_API_KEY")
AHREFS_KEY = get_secret("AHREFS_API_KEY")

# --- 3. SIDEBAR STATUS ---
with st.sidebar:
    st.header("🏛️ Office Status")
    
    if GEMINI_KEY:
        st.success("Gemini API: 🟢 Connected")
    else:
        st.error("Gemini API: 🔴 Missing")
        st.stop()

    if AHREFS_KEY:
        st.success("Ahrefs API: 🟢 Connected")
        has_ahrefs = True
    else:
        st.error("Ahrefs API: 🔴 Disconnected")
        st.info("Using Basic Mode")
        has_ahrefs = False

# --- 4. CLAUDIO HEADER (BROWN SKIN AVATAR) ---
col_img, col_txt = st.columns([1, 4])
with col_img:
    # Avatar: Persona con piel marrón y traje
    st.markdown('<img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" class="claudio-avatar">', unsafe_allow_html=True)
with col_txt:
    st.title("Claudio: SEO Executive")
    st.write("International SEO Strategy Consultant.")

st.markdown("---")

# --- 5. AUDIT INTERFACE ---
url_input = st.text_input("🌐 Target URL:", placeholder="https://example.com")

if has_ahrefs:
    audit_selection = st.radio("Audit Type:", ["Basic (Visual)", "Full (Ahrefs)"], horizontal=True)
else:
    st.info("🛡️ **Basic Visual Audit** is the only mode available without Ahrefs API.")
    audit_selection = "Basic (Visual)"

# Confirmación para Ahrefs
confirm_full = True
if audit_selection == "Full (Ahrefs)":
    confirm_full = st.checkbox("I confirm I want to use Ahrefs credits", value=False)

if st.button("🕴️ START AUDIT"):
    if not url_input:
        st.error("Please enter a URL.")
    elif audit_selection == "Full (Ahrefs)" and not confirm_full:
        st.warning("Please check the confirmation box.")
    else:
        with st.spinner('Claudio is thinking...'):
            try:
                genai.configure(api_key=GEMINI_KEY)
                
                # DINAMIC MODEL SELECTION (To avoid 404)
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                # Priorizar Flash, si no, el primero disponible
                model_name = next((m for m in available_models if "flash" in m), available_models[0])
                model = genai.GenerativeModel(model_name)
                
                metrics = {"DR": "N/A", "Links": "N/A"}
                
                if audit_selection == "Full (Ahrefs)":
                    target = url_input.replace("https://", "").replace("http://", "").strip("/")
                    headers = {"Authorization": f"Bearer {AHREFS_KEY}"}
                    api_res = requests.get(f"https://api.ahrefs.com/v3/site-explorer/overview?target={target}&output=json", headers=headers)
                    data = api_res.json()
                    metrics["DR"] = data.get('metrics', {}).get('domain_rating', 'N/A')
                    metrics["Links"] = data.get('metrics', {}).get('backlinks', 'N/A')
                    prompt = f"Act as Claudio. Analyze {url_input} (DR: {metrics['DR']}, Links: {metrics['Links']}). Professional SEO audit in English."
                else:
                    prompt = f"Act as Claudio. Provide a strategic visual SEO overview for {url_input} in English."

                response = model.generate_content(prompt)
                
                # RESULTS
                st.balloons()
                c1, c2, c3 = st.columns(3)
                c1.markdown(f'<div class="metric-card"><h4>DR</h4><h2>{metrics["DR"]}</h2></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-card"><h4>Links</h4><h2>{metrics["Links"]}</h2></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-card"><h4>Level</h4><p>{audit_selection}</p></div>', unsafe_allow_html=True)

                st.markdown("### 📝 Report Preview")
                st.markdown(response.text)

                doc = Document()
                doc.add_heading(f'SEO Audit: {url_input}', 0)
                doc.add_paragraph(response.text)
                buf = BytesIO()
                doc.save(buf)
                st.download_button("📥 DOWNLOAD REPORT", buf.getvalue(), f"Claudio_Audit.docx")

            except Exception as e:
                st.error(f"Error: {e}")
