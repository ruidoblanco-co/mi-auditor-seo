import streamlit as st
import time
from datetime import datetime

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
# 📊 FUNCIONES DE SIMULACIÓN
# ===========================
def simular_auditoria_basic(url, modelo):
    """Simula una auditoría básica"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    steps = [
        ("Conectando con el sitio web...", 20),
        ("Analizando estructura HTML...", 40),
        ("Evaluando meta tags y headings...", 60),
        (f"Generando análisis con {modelo}...", 80),
        ("Preparando reporte final...", 100)
    ]
    
    for step, progress in steps:
        status_text.text(step)
        progress_bar.progress(progress)
        time.sleep(0.8)
    
    status_text.empty()
    progress_bar.empty()
    
    return """
# 📊 Auditoría SEO Básica - Ejemplo.com

## 🎯 Executive Summary

**Puntuación General**: 68/100

El sitio presenta una base sólida pero con oportunidades significativas de mejora en optimización on-page y estructura técnica.

### Hallazgos Clave:
- ✅ **Fortalezas**: Velocidad de carga aceptable, mobile-friendly
- ⚠️ **Oportunidades**: Meta descriptions faltantes, estructura H1 inconsistente
- 🔴 **Crítico**: 15 páginas sin indexar, sitemap.xml desactualizado

---

## 🔍 Análisis Técnico

### Meta Tags
- **Title tags**: 85% optimizados
- **Meta descriptions**: 45% faltantes (URGENTE)
- **Canonical tags**: Implementados correctamente

### Estructura de Contenido
- **H1**: Presente en 70% de páginas
- **H2-H6**: Jerarquía inconsistente
- **Imágenes sin ALT**: 23 detectadas

### Performance
- **Load Time**: 2.3s (Aceptable)
- **Mobile Score**: 78/100
- **Core Web Vitals**: Needs improvement

---

## 📋 Recomendaciones Priorizadas

### Critical (Hacer YA)
1. Añadir meta descriptions a 18 páginas principales
2. Corregir estructura H1 en páginas de producto
3. Actualizar sitemap.xml

### High Priority
4. Optimizar imágenes (WebP + lazy loading)
5. Implementar schema markup
6. Mejorar linking interno

---

**Análisis generado por**: {modelo}
**Fecha**: {datetime.now().strftime("%d/%m/%Y %H:%M")}
"""

def simular_auditoria_full(url, modelo):
    """Simula una auditoría completa con Ahrefs"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    steps = [
        ("Conectando con el sitio web...", 15),
        ("Obteniendo datos de Ahrefs API...", 30),
        ("Analizando backlink profile...", 45),
        ("Evaluando keywords ranking...", 60),
        ("Analizando competencia...", 75),
        (f"Generando análisis profundo con {modelo}...", 90),
        ("Preparando reportes completos...", 100)
    ]
    
    for step, progress in steps:
        status_text.text(step)
        progress_bar.progress(progress)
        time.sleep(1)
    
    status_text.empty()
    progress_bar.empty()
    
    return """
# 🏆 Auditoría SEO Completa - Ejemplo.com

## 📈 Executive Summary

**Puntuación General**: 72/100
**Domain Rating**: 45/100
**Estimated Monthly Traffic**: ~12,500 visits

### Métricas Clave (Ahrefs):
- 🔗 **Backlinks**: 1,247 (↑ 15% vs mes anterior)
- 🌐 **Referring Domains**: 89
- 📊 **Organic Keywords**: 342 keywords ranking
- 💰 **Traffic Value**: $3,400/month

### Posicionamiento:
- Top 3: 12 keywords
- Top 10: 45 keywords  
- Top 100: 342 keywords

---

## 🔍 Análisis Técnico Completo

### SEO On-Page (68/100)
- Title tags: 85% optimizados
- Meta descriptions: 45% faltantes ⚠️
- H1 structure: Necesita mejoras
- Image optimization: 67% completado

### Backlink Profile (75/100)
**Calidad General**: Buena

**Top Referring Domains**:
1. industry-blog.com (DR 67) - 15 backlinks
2. tech-news.net (DR 58) - 8 backlinks
3. partner-site.io (DR 52) - 12 backlinks

**Anchor Text Distribution**:
- Branded: 45%
- Naked URL: 30%
- Keywords: 20%
- Other: 5%

⚠️ **Broken Backlinks**: 23 enlaces rotos detectados (oportunidad de recuperación)

### Organic Performance

**Top Performing Pages**:
1. /blog/guia-seo → 2,300 visits/mes
2. /productos/servicio-premium → 1,800 visits/mes
3. /recursos/herramientas → 1,200 visits/mes

**Keyword Opportunities** (gaps detectados):
- "seo para ecommerce" - Vol: 1,200 - Difficulty: 35 - Posición actual: #15
- "optimización web" - Vol: 890 - Difficulty: 42 - Posición actual: #12
- "marketing digital" - Vol: 5,400 - Difficulty: 68 - Posición actual: #28

### Análisis Competitivo

**Principales Competidores**:
1. competitor-a.com - DR 62 - Overlap: 78 keywords
2. competitor-b.com - DR 55 - Overlap: 45 keywords
3. competitor-c.com - DR 51 - Overlap: 34 keywords

**Keywords que ellos rankean y tú no**:
- 15 oportunidades de contenido identificadas
- Potencial traffic: ~3,500 visits/mes adicionales

---

## 🎯 Plan de Acción Estratégico

### 🔴 CRITICAL (Semana 1-2)

1. **Recuperar Broken Backlinks** (23 enlaces)
   - Esfuerzo: 4 horas
   - Impacto: Alto - Recuperar ~15 DR points
   - Acción: Contactar webmasters + redirecciones 301

2. **Optimizar Meta Descriptions** (18 páginas)
   - Esfuerzo: 3 horas
   - Impacto: Medio-Alto - Mejorar CTR 15-20%
   - Acción: Escribir descriptions con keywords objetivo

3. **Fix H1 Structure** (12 páginas productos)
   - Esfuerzo: 2 horas
   - Impacto: Medio
   - Acción: Un H1 único y optimizado por página

### 🟡 HIGH PRIORITY (Semana 3-4)

4. **Crear Contenido para Keyword Gaps**
   - Target: "seo para ecommerce", "optimización web"
   - Esfuerzo: 12 horas
   - Impacto: Alto - Potencial +2,000 visits/mes
   - Acción: 2 artículos de 2,000+ palabras

5. **Link Building Campaign**
   - Objetivo: +15 backlinks de DR 40+
   - Esfuerzo: 20 horas
   - Impacto: Alto - Mejorar DR a 50+
   - Estrategia: Guest posting + digital PR

6. **Implementar Schema Markup**
   - Tipos: Organization, Product, Article
   - Esfuerzo: 6 horas
   - Impacto: Medio - Rich snippets en SERPs

### 🟢 MEDIUM PRIORITY (Mes 2)

7. Optimización técnica de imágenes
8. Mejora de Core Web Vitals
9. Ampliar linking interno
10. Crear pillar content

---

## 📊 Proyección de Resultados (3 meses)

**Si se implementa el plan completo**:
- Domain Rating: 45 → 52 (+7 puntos)
- Organic Traffic: 12,500 → 18,000 visits/mes (+44%)
- Keywords Top 10: 45 → 75 (+67%)
- Traffic Value: $3,400 → $5,200/mes

---

**Análisis generado por**: {modelo}
**Powered by**: Ahrefs API + AI Analysis
**Fecha**: {datetime.now().strftime("%d/%m/%Y %H:%M")}
"""

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
    
    # Simulación de estado de APIs (hardcoded para preview)
    gemini_status = True  # Cambiar a True/False para probar
    claude_status = False  # Cambiar a True/False para probar
    ahrefs_status = False  # Cambiar a True/False para probar
    
    if gemini_status:
        st.markdown('<span class="status-badge status-connected">🟢 Gemini Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-disconnected">🔴 Gemini Offline</span>', unsafe_allow_html=True)
    
    if claude_status:
        st.markdown('<span class="status-badge status-connected">🟢 Claude Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-disconnected">🔴 Claude Offline</span>', unsafe_allow_html=True)
    
    if ahrefs_status:
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

# Métricas superiores (placeholders)
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
    modelo_seleccionado = st.selectbox(
        "Choose AI Model",
        [
            "⚡ Gemini 2.0 Flash (Free)",
            "🎯 Claude Sonnet 4.5 (~$0.18)",
            "👑 Claude Opus 4.5 (~$0.50)"
        ],
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
    st.warning("⚠️ **Full Audit will use Ahrefs API credits**")
    confirmar_ahrefs = st.checkbox("✓ I confirm the use of Ahrefs API", value=False)
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
        elif "Full" in tipo_auditoria and not confirmar_ahrefs:
            st.error("❌ Please confirm Ahrefs API usage")
        else:
            # Determinar modelo a usar
            if "Gemini" in modelo_seleccionado:
                modelo_nombre = "Gemini 2.0 Flash"
            elif "Sonnet" in modelo_seleccionado:
                modelo_nombre = "Claude Sonnet 4.5"
            else:
                modelo_nombre = "Claude Opus 4.5"
            
            # Ejecutar auditoría según tipo
            st.markdown("---")
            st.markdown("## 📊 Audit Results")
            
            with st.spinner(""):
                if "Basic" in tipo_auditoria:
                    resultado = simular_auditoria_basic(url_input, modelo_nombre)
                else:
                    resultado = simular_auditoria_full(url_input, modelo_nombre)
            
            # Mostrar resultado
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
