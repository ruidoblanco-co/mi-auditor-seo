import streamlit as st
import time
from datetime import datetime
import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# ===========================
# 🎨 CONFIGURACIÓN DE PÁGINA
# ===========================
st.set_page_config(
    page_title="Claudio - AI SEO Auditor",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===========================
# 🔑 CONFIGURACIÓN DE APIs
# ===========================
try:
    GEMINI_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_DISPONIBLE = True
except Exception as e:
    GEMINI_DISPONIBLE = False
    st.error(f"⚠️ Gemini API no configurada: {e}")

try:
    CLAUDE_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")
    CLAUDE_DISPONIBLE = bool(CLAUDE_API_KEY)
except:
    CLAUDE_DISPONIBLE = False

try:
    AHREFS_API_KEY = st.secrets.get("AHREFS_API_KEY", "")
    AHREFS_DISPONIBLE = bool(AHREFS_API_KEY)
except:
    AHREFS_DISPONIBLE = False

# ===========================
# 🎨 CSS PERSONALIZADO
# ===========================
st.markdown("""
<style>
    /* Fondo oscuro corporativo */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Sidebar oscuro */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f3460 0%, #16213e 100%);
    }
    
    /* Cards de métricas */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        color: #00d4ff;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: #a0aec0;
        font-size: 14px;
        font-weight: 500;
    }
    
    /* Botones personalizados */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #00d4ff 0%, #0091ff 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 212, 255, 0.3);
    }
    
    /* Inputs */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 8px;
        padding: 10px;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #00d4ff;
        box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
    }
    
    /* Selectbox */
    .stSelectbox>div>div>div {
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
        border-radius: 8px;
    }
    
    /* Radio buttons */
    .stRadio>div {
        background-color: rgba(255, 255, 255, 0.03);
        padding: 15px;
        border-radius: 8px;
        border: 1px solid rgba(0, 212, 255, 0.2);
    }
    
    /* Info boxes */
    .stAlert {
        background-color: rgba(0, 212, 255, 0.1);
        border-left: 4px solid #00d4ff;
        border-radius: 4px;
    }
    
    /* Títulos */
    h1 {
        color: #00d4ff;
        font-weight: 700;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
    }
    
    h2, h3 {
        color: #ffffff;
    }
    
    /* Avatar personalizado de Claudio */
    .claudio-avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #8B4513 0%, #654321 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        margin: 0 auto 20px;
        border: 3px solid #00d4ff;
        box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin: 4px;
    }
    
    .status-connected {
        background-color: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        border: 1px solid #22c55e;
    }
    
    .status-disconnected {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid #ef4444;
    }
    
    .status-optional {
        background-color: rgba(251, 191, 36, 0.2);
        color: #fbbf24;
        border: 1px solid #fbbf24;
    }
</style>
""", unsafe_allow_html=True)

# ===========================
# 🎭 AVATAR DE CLAUDIO
# ===========================
def mostrar_avatar():
    st.markdown("""
    <div class="claudio-avatar">
        👔
    </div>
    """, unsafe_allow_html=True)

# ===========================
# 🔍 FUNCIONES DE ANÁLISIS WEB
# ===========================
def analizar_sitio_basico(url):
    """Analiza el sitio web extrayendo información básica del HTML"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraer información
        analisis = {
            'url': url,
            'status_code': response.status_code,
            'title': soup.title.string if soup.title else 'No title found',
            'meta_description': '',
            'h1_tags': [],
            'h2_tags': [],
            'images_without_alt': 0,
            'total_images': 0,
            'internal_links': 0,
            'external_links': 0,
            'word_count': 0
        }
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            analisis['meta_description'] = meta_desc.get('content', '')
        
        # H1 y H2
        analisis['h1_tags'] = [h1.get_text().strip() for h1 in soup.find_all('h1')]
        analisis['h2_tags'] = [h2.get_text().strip() for h2 in soup.find_all('h2')][:5]  # Primeros 5
        
        # Imágenes
        images = soup.find_all('img')
        analisis['total_images'] = len(images)
        analisis['images_without_alt'] = len([img for img in images if not img.get('alt')])
        
        # Links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if href.startswith('http') and url not in href:
                analisis['external_links'] += 1
            elif href.startswith('/') or url in href:
                analisis['internal_links'] += 1
        
        # Contar palabras
        text = soup.get_text()
        analisis['word_count'] = len(text.split())
        
        return analisis
        
    except Exception as e:
        return {'error': str(e)}

# ===========================
# 🤖 FUNCIONES DE IA
# ===========================
def generar_auditoria_con_gemini(url, datos_sitio, tipo_auditoria):
    """Genera auditoría usando Gemini"""
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        # Preparar el prompt según el tipo
        if tipo_auditoria == "Basic":
            prompt = f"""
Eres Claudio, un experto auditor SEO profesional. Analiza el siguiente sitio web y genera una auditoría SEO BÁSICA completa y profesional.

**DATOS DEL SITIO:**
URL: {datos_sitio.get('url', url)}
Title: {datos_sitio.get('title', 'N/A')}
Meta Description: {datos_sitio.get('meta_description', 'No meta description found')}
H1 Tags: {', '.join(datos_sitio.get('h1_tags', [])) if datos_sitio.get('h1_tags') else 'None found'}
H2 Tags (primeros 5): {', '.join(datos_sitio.get('h2_tags', []))}
Total Imágenes: {datos_sitio.get('total_images', 0)}
Imágenes sin ALT: {datos_sitio.get('images_without_alt', 0)}
Links Internos: {datos_sitio.get('internal_links', 0)}
Links Externos: {datos_sitio.get('external_links', 0)}
Total Palabras: {datos_sitio.get('word_count', 0)}

**INSTRUCCIONES:**
Genera un informe de auditoría SEO profesional siguiendo EXACTAMENTE esta estructura:

# 📊 Auditoría SEO Básica - [Nombre del sitio]

## 🎯 Executive Summary

**Puntuación General**: [X]/100

[Resumen de 2-3 párrafos sobre el estado general del sitio]

### Hallazgos Clave:
- ✅ **Fortalezas**: [Lista 2-3 puntos fuertes]
- ⚠️ **Oportunidades**: [Lista 2-3 áreas de mejora]
- 🔴 **Crítico**: [Lista 1-2 problemas urgentes]

---

## 🔍 Análisis Técnico SEO

### Meta Tags
- **Title Tag**: [Análisis del title - longitud, keywords, optimización]
- **Meta Description**: [Análisis - existe, longitud, llamada a la acción]
- **Open Graph**: [Si se detecta o recomendar implementar]

### Estructura de Contenido
- **H1**: [Análisis de H1s encontrados]
- **H2-H6**: [Análisis de jerarquía]
- **Densidad de contenido**: [Análisis basado en word count]

### Optimización de Imágenes
- Total de imágenes: {datos_sitio.get('total_images', 0)}
- Sin atributo ALT: {datos_sitio.get('images_without_alt', 0)}
- [Recomendaciones específicas]

### Arquitectura de Enlaces
- Links internos: {datos_sitio.get('internal_links', 0)}
- Links externos: {datos_sitio.get('external_links', 0)}
- [Análisis de linking strategy]

---

## 📋 Plan de Acción Priorizado

### 🔴 CRITICAL (Hacer inmediatamente)
1. **[Título de la acción]**
   - Descripción: [Qué hacer]
   - Esfuerzo: [X] horas
   - Impacto: Alto/Medio/Bajo
   - Acción: [Pasos específicos]

[Continuar con 2-3 acciones críticas más]

### 🟡 HIGH PRIORITY (Próximas 1-2 semanas)
[Listar 3-4 acciones de alta prioridad con el mismo formato]

### 🟢 MEDIUM PRIORITY (Mes 1-2)
[Listar 2-3 acciones de prioridad media]

---

## 🎯 Recomendaciones Estratégicas

[2-3 párrafos con recomendaciones estratégicas generales basadas en el análisis]

---

**Tipo de Análisis**: Basic (Visual)
**Generado por**: Gemini 2.0 Flash
**Fecha**: {datetime.now().strftime("%d/%m/%Y %H:%M")}

IMPORTANTE: 
- Sé específico y profesional
- Basa TODO en los datos proporcionados
- Si algo falta, indícalo como oportunidad de mejora
- Numera todas las acciones
- Usa emojis solo donde indicado en la estructura
"""
        else:  # Full
            prompt = f"""
Eres Claudio, un experto auditor SEO profesional. Genera una auditoría SEO COMPLETA ultra-profesional.

**DATOS BÁSICOS DEL SITIO:**
{datos_sitio}

**NOTA**: Esta es una auditoría FULL pero aún no tenemos datos de Ahrefs API. 
Por ahora genera la auditoría con los datos disponibles y añade secciones que DEBERÍAN incluir datos de Ahrefs
indicando claramente que esos datos se añadirán cuando esté conectada la API.

Sigue la misma estructura que Basic pero añade estas secciones:

## 📊 Métricas de Autoridad (Pendiente Ahrefs API)
[Explicar qué métricas se mostrarán aquí: DR, backlinks, referring domains, etc.]

## 🔗 Perfil de Backlinks (Pendiente Ahrefs API)
[Explicar qué análisis se hará aquí]

## 📈 Rendimiento Orgánico (Pendiente Ahrefs API)
[Explicar qué datos de keywords y traffic se mostrarán]

Genera el resto del análisis basado en datos disponibles.

**Fecha**: {datetime.now().strftime("%d/%m/%Y %H:%M")}
"""
        
        # Generar contenido
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"❌ Error generando auditoría con Gemini: {str(e)}"

# ===========================
# 🎨 SIDEBAR - OFFICE STATUS
# ===========================
with st.sidebar:
    mostrar_avatar()
    
    st.markdown("### 👔 Claudio AI")
    st.markdown("*Professional SEO Auditor*")
    st.markdown("---")
    
    # Office Status
    st.markdown("### 🏢 Office Status")
    
    if GEMINI_DISPONIBLE:
        st.markdown('<span class="status-badge status-connected">🟢 Gemini Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-disconnected">🔴 Gemini Offline</span>', unsafe_allow_html=True)
    
    if CLAUDE_DISPONIBLE:
        st.markdown('<span class="status-badge status-connected">🟢 Claude Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-disconnected">🔴 Claude Offline</span>', unsafe_allow_html=True)
    
    if AHREFS_DISPONIBLE:
        st.markdown('<span class="status-badge status-connected">🟢 Ahrefs Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-optional">⚠️ Ahrefs Optional</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Info
    st.markdown("### ℹ️ About")
    st.markdown("""
    **Claudio** is your AI-powered SEO auditor.
    
    Generate professional SEO audits in seconds.
    
    **Features**:
    - 🔍 Basic visual analysis
    - 💎 Full analysis with Ahrefs
    - 🤖 Multiple AI models
    - 📄 Professional reports
    """)
    
    st.markdown("---")
    st.markdown("*v2.0 - Premium Edition*")

# ===========================
# 🎯 MAIN INTERFACE
# ===========================

# Header
st.markdown("# 🔍 SEO Audit Generator")
st.markdown("*Professional SEO audits powered by AI*")
st.markdown("---")

# Métricas superiores (placeholders por ahora)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Audits Today", "0", "+0")
with col2:
    st.metric("Total Audits", "0", "")
with col3:
    st.metric("Avg. Score", "-", "")
with col4:
    st.metric("Time Saved", "0h", "")

st.markdown("---")

# ===========================
# 🎛️ CONFIGURACIÓN
# ===========================

# Tipo de auditoría
st.markdown("### 📋 Audit Configuration")

col1, col2 = st.columns([2, 1])

with col1:
    tipo_auditoria = st.radio(
        "Select Audit Type",
        ["🔍 Basic (Visual Analysis)", "💎 Full (With Ahrefs Data)"],
        help="Basic: Quick visual analysis without API costs\nFull: Complete analysis with Ahrefs metrics"
    )

with col2:
    if "Full" in tipo_auditoria:
        st.info("**Full Audit**\n\nIncludes:\n- Domain Rating\n- Backlinks\n- Keywords\n- Traffic data\n- Competitors")
    else:
        st.info("**Basic Audit**\n\nIncludes:\n- Technical SEO\n- On-page analysis\n- Content review\n- Quick insights")

st.markdown("---")

# Selector de modelo IA
st.markdown("### 🤖 AI Model Selection")

col1, col2 = st.columns([2, 1])

with col1:
    # Filtrar modelos según disponibilidad
    modelos_disponibles = []
    
    if GEMINI_DISPONIBLE:
        modelos_disponibles.append("⚡ Gemini 2.0 Flash (Free)")
    
    if CLAUDE_DISPONIBLE:
        modelos_disponibles.extend([
            "🎯 Claude Sonnet 4.5 (~$0.18)",
            "👑 Claude Opus 4.5 (~$0.50)"
        ])
    
    if not modelos_disponibles:
        st.error("❌ No AI models configured. Please add API keys in Streamlit Secrets.")
        st.stop()
    
    modelo_seleccionado = st.selectbox(
        "Choose AI Model",
        modelos_disponibles,
        help="Gemini: Fast and free\nSonnet: Best quality/price\nOpus: Maximum quality"
    )

with col2:
    # Cálculo de costo estimado
    if "Gemini" in modelo_seleccionado:
        costo = 0.00
        velocidad = "⚡⚡⚡ Ultra Fast"
        calidad = "⭐⭐⭐ Good"
    elif "Sonnet" in modelo_seleccionado:
        costo = 0.18
        velocidad = "⚡⚡ Fast"
        calidad = "⭐⭐⭐⭐ Excellent"
    else:  # Opus
        costo = 0.50
        velocidad = "⚡ Moderate"
        calidad = "⭐⭐⭐⭐⭐ Premium"
    
    st.metric("💰 Estimated Cost", f"${costo:.2f}")
    st.caption(f"**Speed**: {velocidad}")
    st.caption(f"**Quality**: {calidad}")

st.markdown("---")

# ===========================
# 🌐 URL INPUT
# ===========================

st.markdown("### 🌐 Website to Audit")

url_input = st.text_input(
    "Enter URL",
    placeholder="https://example.com",
    help="Enter the full URL including https://"
)

# Confirmación para Full Audit
if "Full" in tipo_auditoria:
    if AHREFS_DISPONIBLE:
        st.warning("⚠️ **Full Audit will use Ahrefs API credits**")
        confirmar_ahrefs = st.checkbox("✓ I confirm the use of Ahrefs API", value=False)
    else:
        st.warning("⚠️ **Ahrefs API not configured**. Full audit will generate report structure but without Ahrefs data.")
        confirmar_ahrefs = True
else:
    confirmar_ahrefs = True  # No necesita confirmación en Basic

st.markdown("---")

# ===========================
# 🚀 BOTÓN DE AUDITORÍA
# ===========================

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    boton_disabled = not url_input or not confirmar_ahrefs
    
    if st.button("🚀 Generate Audit", disabled=boton_disabled, use_container_width=True):
        
        if not url_input:
            st.error("❌ Please enter a URL")
        elif "Full" in tipo_auditoria and AHREFS_DISPONIBLE and not confirmar_ahrefs:
            st.error("❌ Please confirm Ahrefs API usage")
        else:
            st.markdown("---")
            st.markdown("## 📊 Audit in Progress")
            
            # Barra de progreso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Paso 1: Analizar sitio
            status_text.text("🔍 Analyzing website...")
            progress_bar.progress(30)
            datos_sitio = analizar_sitio_basico(url_input)
            time.sleep(1)
            
            if 'error' in datos_sitio:
                st.error(f"❌ Error analyzing website: {datos_sitio['error']}")
                st.stop()
            
            # Paso 2: Generar con IA
            status_text.text("🤖 Generating audit with AI...")
            progress_bar.progress(60)
            
            tipo = "Basic" if "Basic" in tipo_auditoria else "Full"
            
            # Por ahora solo Gemini está implementado
            if "Gemini" in modelo_seleccionado:
                resultado = generar_auditoria_con_gemini(url_input, datos_sitio, tipo)
            else:
                st.warning("⚠️ Claude implementation coming soon. Using Gemini for now.")
                resultado = generar_auditoria_con_gemini(url_input, datos_sitio, tipo)
            
            progress_bar.progress(100)
            status_text.text("✅ Audit completed!")
            time.sleep(0.5)
            
            progress_bar.empty()
            status_text.empty()
            
            # Mostrar resultado
            st.markdown("---")
            st.markdown("## 📊 Audit Results")
            st.success("✅ Audit completed successfully!")
            
            # Tabs para organizar resultados
            tab1, tab2 = st.tabs(["📄 Full Report", "📥 Download"])
            
            with tab1:
                st.markdown(resultado)
            
            with tab2:
                st.markdown("### Download Options")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📄 Word Document")
                    st.info("""
                    **Includes**:
                    - Executive Summary
                    - Complete Analysis
                    - Strategic Recommendations
                    - Professional Formatting
                    """)
                    st.button("📥 Download .docx", disabled=True, help="Coming soon!")
                
                with col2:
                    st.markdown("#### 📊 Excel Spreadsheet")
                    st.info("""
                    **Includes**:
                    - Task List (prioritized)
                    - Technical Issues
                    - SEO Opportunities
                    - Tracking Checkboxes
                    """)
                    st.button("📥 Download .xlsx", disabled=True, help="Coming soon!")
                
                st.markdown("---")
                st.caption("*Document generation will be enabled in the next version*")

# ===========================
# 📊 FOOTER
# ===========================

st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Claudio AI SEO Auditor**")
    st.caption("Professional audits in seconds")

with col2:
    st.markdown("**Powered by**")
    st.caption("Anthropic Claude • Google Gemini • Ahrefs")

with col3:
    st.markdown("**Need help?**")
    st.caption("[Documentation](#) • [Support](#)")
