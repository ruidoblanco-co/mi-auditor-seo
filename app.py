import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# 1. Configuración básica para evitar pantalla negra
st.set_page_config(page_title="SEO Audit Tool", layout="wide")

st.title("🛠️ Auditoría SEO Automática")

# 2. Variables fijas (Para que tus colegas no tengan que ponerlas)
# RECOMIENDO: Pega aquí tus llaves directamente entre las comillas
AHREFS_KEY = "TU_API_KEY_AQUÍ"
GEMINI_KEY = "TU_API_KEY_AQUÍ"

# 3. Interfaz
st.sidebar.header("Estado del Sistema")
if AHREFS_KEY == "TU_API_KEY_AQUÍ" or GEMINI_KEY == "TU_API_KEY_AQUÍ":
    st.sidebar.warning("⚠️ Faltan las llaves API en el código.")
else:
    st.sidebar.success("✅ Sistema listo para auditar.")

url_input = st.text_input("Introduce la URL de la empresa (ej: https://empresa.com)")

if st.button("Generar Auditoría"):
    if url_input:
        with st.spinner('Trabajando... esto puede tardar 1 minuto.'):
            try:
                # Configurar Gemini
                genai.configure(api_key=GEMINI_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Simulación de datos (hasta que conectemos la API de Ahrefs real)
                datos_seo = f"Auditoría para {url_input}. DR: 40. Errores: 25. H1 duplicados: 10."
                
                # Pedir a Gemini que redacte
                prompt = f"Actúa como consultor SEO Senior. Basado en {datos_seo}, redacta un informe profesional con Resumen, Errores Técnicos y Plan de Acción."
                respuesta = model.generate_content(prompt)
                informe_texto = respuesta.text
                
                # Mostrar en pantalla
                st.markdown("### 📋 Resultado de la Auditoría")
                st.write(informe_texto)
                
                # Crear el Word
                doc = Document()
                doc.add_heading(f"Informe SEO - {url_input}", 0)
                doc.add_paragraph(informe_texto)
                
                buffer = BytesIO()
                doc.save(buffer)
                
                st.download_button(
                    label="💾 Descargar Informe Word",
                    data=buffer.getvalue(),
                    file_name="auditoria_seo.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Hubo un error: {e}")
    else:
        st.error("Por favor, escribe una URL.")
