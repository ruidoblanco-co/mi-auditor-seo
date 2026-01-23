import streamlit as st
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

from docx import Document
from docx.shared import Pt, RGBColor

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from io import BytesIO
import json
import re
from pathlib import Path
from urllib.parse import urlparse

# Optional Claude
try:
    import anthropic
    ANTHROPIC_OK = True
except Exception:
    ANTHROPIC_OK = False


# ===========================
# PAGE CONFIG
# ===========================
st.set_page_config(
    page_title="Claudio - Professional SEO Auditor",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
PROMPTS_DIR = BASE_DIR / "prompts"

DOCX_TEMPLATE_FULL = TEMPLATES_DIR / "SEO_Audit_Template_Full.docx"
XLSX_TEMPLATE_FULL = TEMPLATES_DIR / "SEO_Tasks_Template_Full.xlsx"

PROMPT_FULL = PROMPTS_DIR / "full.md"
PROMPT_BASIC = PROMPTS_DIR / "basic.md"

# ===========================
# API CONFIG
# ===========================
GEMINI_AVAILABLE = False
CLAUDE_AVAILABLE = False
AHREFS_AVAILABLE = False

GEMINI_API_KEY = ""
CLAUDE_API_KEY = ""
AHREFS_API_KEY = ""

try:
    GEMINI_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

try:
    AHREFS_API_KEY = st.secrets.get("AHREFS_API_KEY", "")
    AHREFS_AVAILABLE = bool(AHREFS_API_KEY)
except Exception:
    AHREFS_AVAILABLE = False

try:
    CLAUDE_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")
    CLAUDE_AVAILABLE = bool(CLAUDE_API_KEY) and ANTHROPIC_OK
except Exception:
    CLAUDE_AVAILABLE = False


# ===========================
# CSS (minimal - puedes pegar tu CSS largo si quieres)
# ===========================
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #2b2d42 0%, #1a1b26 100%); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #1a1b26 0%, #121318 100%); }
h1,h2,h3 { color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)


# ===========================
# HELPERS
# ===========================
def normalize_domain(url_or_domain: str) -> str:
    s = (url_or_domain or "").strip()
    if not s:
        return ""
    if not s.startswith(("http://", "https://")):
        # Could be domain
        s2 = s
    else:
        s2 = urlparse(s).netloc
    s2 = s2.lower()
    if s2.startswith("www."):
        s2 = s2[4:]
    # remove port if any
    s2 = s2.split(":")[0]
    return s2

def safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

def strip_json_fences(text: str) -> str:
    t = (text or "").strip()
    # remove ```json fences if model returns them
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```$", "", t)
    return t.strip()

def load_prompt(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file missing: {path}")
    return path.read_text(encoding="utf-8")

def ahrefs_headers():
    return {
        "Authorization": f"Bearer {AHREFS_API_KEY}",
        "Accept": "application/json",
    }

def ahrefs_get(url: str, params: dict | None = None, timeout: int = 30):
    r = requests.get(url, headers=ahrefs_headers(), params=params or {}, timeout=timeout)
    return r.status_code, r.json() if "application/json" in r.headers.get("Content-Type", "") else r.text

def priority_from_count(n: int) -> str:
    if n <= 0:
        return "LOW"
    if n >= 100:
        return "HIGH"
    if n >= 20:
        return "MEDIUM"
    return "LOW"


# ===========================
# BASIC ON-PAGE ANALYSIS (for Basic mode)
# ===========================
def analyze_basic_site(url: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = ""
    md = soup.find("meta", attrs={"name": "description"})
    if md:
        meta_desc = md.get("content", "").strip()

    h1s = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    h2s = [h.get_text(" ", strip=True) for h in soup.find_all("h2")][:5]

    imgs = soup.find_all("img")
    total_images = len(imgs)
    images_without_alt = sum(1 for img in imgs if not img.get("alt"))

    internal_links = 0
    external_links = 0
    base_domain = normalize_domain(url)
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        if href.startswith(("http://", "https://")):
            d = normalize_domain(href)
            if d and d != base_domain:
                external_links += 1
            else:
                internal_links += 1
        else:
            # relative -> internal
            internal_links += 1

    text = soup.get_text(" ", strip=True)
    word_count = len(text.split())

    return {
        "url": url,
        "title": title or "Missing",
        "meta_description": meta_desc or "Missing",
        "h1_count": len(h1s),
        "h1_tags": h1s,
        "h2_sample": h2s,
        "total_images": total_images,
        "images_without_alt": images_without_alt,
        "internal_links": internal_links,
        "external_links": external_links,
        "word_count": word_count,
        "http_status": r.status_code,
    }


# ===========================
# AHREFS: SITE EXPLORER (metrics/keywords/backlinks/anchors/competitors)
# ===========================
@st.cache_data(ttl=900)
def get_site_explorer_metrics(domain: str) -> dict:
    # Uses v3 Site Explorer metrics endpoint (as in your old code)
    url = "https://api.ahrefs.com/v3/site-explorer/metrics"
    params = {"target": domain, "date": datetime.utcnow().strftime("%Y-%m-%d")}
    code, data = ahrefs_get(url, params)
    if code != 200:
        return {"_error": f"metrics HTTP {code}", "_raw": data}
    return data

@st.cache_data(ttl=900)
def get_organic_keywords(domain: str, country: str = "us", limit: int = 20) -> dict:
    url = "https://api.ahrefs.com/v3/site-explorer/organic-keywords"
    params = {"target": domain, "limit": limit, "country": country}
    code, data = ahrefs_get(url, params)
    if code != 200:
        return {"_error": f"organic-keywords HTTP {code}", "_raw": data}
    return data

@st.cache_data(ttl=900)
def get_backlinks_sample(domain: str, limit: int = 20) -> dict:
    url = "https://api.ahrefs.com/v3/site-explorer/all-backlinks"
    params = {"target": domain, "limit": limit, "order_by": "domain_rating:desc"}
    code, data = ahrefs_get(url, params)
    if code != 200:
        return {"_error": f"all-backlinks HTTP {code}", "_raw": data}
    return data

@st.cache_data(ttl=900)
def get_anchors(domain: str, limit: int = 20) -> dict:
    url = "https://api.ahrefs.com/v3/site-explorer/anchors"
    params = {"target": domain, "limit": limit}
    code, data = ahrefs_get(url, params)
    if code != 200:
        return {"_error": f"anchors HTTP {code}", "_raw": data}
    return data

@st.cache_data(ttl=900)
def get_refdomains(domain: str, limit: int = 10) -> dict:
    url = "https://api.ahrefs.com/v3/site-explorer/refdomains"
    params = {"target": domain, "limit": limit, "order_by": "domain_rating:desc"}
    code, data = ahrefs_get(url, params)
    if code != 200:
        return {"_error": f"refdomains HTTP {code}", "_raw": data}
    return data

@st.cache_data(ttl=900)
def get_organic_competitors(domain: str, country: str = "us", limit: int = 5) -> dict:
    # Organic competitors exists in API v3 Site Explorer docs. :contentReference[oaicite:1]{index=1}
    url = "https://api.ahrefs.com/v3/site-explorer/organic-competitors"
    params = {"target": domain, "limit": limit, "country": country}
    code, data = ahrefs_get(url, params)
    if code != 200:
        return {"_error": f"organic-competitors HTTP {code}", "_raw": data}
    return data


# ===========================
# AHREFS: SITE AUDIT (projects/issues/page-explorer)
# ===========================
@st.cache_data(ttl=900)
def site_audit_projects() -> dict:
    # Health score/projects endpoint exists in API v3 Site Audit. :contentReference[oaicite:2]{index=2}
    url = "https://api.ahrefs.com/v3/site-audit/projects"
    code, data = ahrefs_get(url, params={})
    if code != 200:
        return {"_error": f"site-audit/projects HTTP {code}", "_raw": data}
    return data

def pick_project_for_domain(projects_payload: dict, domain: str):
    """
    Tries to find a Site Audit project matching the domain.
    Because schemas can vary, this searches common keys.
    Returns (project_obj, project_id_str) or (None, None).
    """
    candidates = []
    items = safe_get(projects_payload, "projects", default=None)
    if items is None and isinstance(projects_payload, dict):
        # Sometimes APIs return list under "data" or "result"
        for k in ("data", "result", "items"):
            if isinstance(projects_payload.get(k), list):
                items = projects_payload.get(k)
                break
    if not isinstance(items, list):
        return None, None

    for p in items:
        target = (
            p.get("target")
            or p.get("domain")
            or p.get("project_target")
            or safe_get(p, "project", "target", default=None)
            or ""
        )
        tdom = normalize_domain(target)
        if tdom == domain:
            # last crawl timestamp if exists
            last_ts = p.get("crawl_timestamp") or p.get("last_crawl") or p.get("updated_at") or ""
            candidates.append((p, last_ts))

    if not candidates:
        return None, None

    # pick most recent by timestamp string (best-effort)
    candidates.sort(key=lambda x: str(x[1]), reverse=True)
    project = candidates[0][0]
    pid = project.get("project_id") or project.get("id") or project.get("uuid")
    return project, pid

@st.cache_data(ttl=900)
def site_audit_issues(project_id: str) -> dict:
    # Project issues endpoint exists. :contentReference[oaicite:3]{index=3}
    url = "https://api.ahrefs.com/v3/site-audit/issues"
    params = {"project_id": project_id}
    code, data = ahrefs_get(url, params=params)
    if code != 200:
        return {"_error": f"site-audit/issues HTTP {code}", "_raw": data}
    return data

def extract_issue_list(issues_payload: dict) -> list[dict]:
    for k in ("issues", "data", "result", "items"):
        v = issues_payload.get(k)
        if isinstance(v, list):
            return v
    return []

def find_issue_id(issues: list[dict], patterns: list[str]) -> tuple[str | None, int]:
    """
    Returns (issue_id, affected_count).
    patterns: list of lowercase substrings to match in issue name/title.
    """
    best = None
    best_count = 0
    for it in issues:
        name = (it.get("name") or it.get("title") or it.get("issue_name") or "").lower()
        if not name:
            continue
        if any(p in name for p in patterns):
            issue_id = it.get("issue_id") or it.get("id") or it.get("uuid")
            count = (
                it.get("urls_affected")
                or it.get("affected_urls")
                or it.get("affected_pages")
                or it.get("count")
                or 0
            )
            try:
                count = int(count)
            except Exception:
                count = 0
            if count >= best_count:
                best = issue_id
                best_count = count
    return best, best_count

@st.cache_data(ttl=900)
def page_explorer(project_id: str, issue_id: str, limit: int = 200, offset: int = 0) -> dict:
    # Page explorer exists; supports issue_id filtering. :contentReference[oaicite:4]{index=4}
    url = "https://api.ahrefs.com/v3/site-audit/page-explorer"
    params = {"project_id": project_id, "issue_id": issue_id, "limit": limit, "offset": offset}
    code, data = ahrefs_get(url, params=params)
    if code != 200:
        return {"_error": f"site-audit/page-explorer HTTP {code}", "_raw": data}
    return data

def extract_page_rows(payload: dict) -> tuple[list[dict], int | None]:
    """
    Returns (rows, next_offset_or_none).
    We support common response shapes: {"pages":[...], "next_offset": ...}
    """
    rows = None
    for k in ("pages", "urls", "data", "items", "result"):
        v = payload.get(k)
        if isinstance(v, list):
            rows = v
            break
    if rows is None:
        rows = []
    next_offset = payload.get("next_offset") or payload.get("offset_next")
    return rows, next_offset

def fetch_pages_for_issue(project_id: str, issue_id: str, max_rows: int = 300) -> list[dict]:
    all_rows = []
    offset = 0
    limit = min(200, max_rows)
    while True:
        payload = page_explorer(project_id, issue_id, limit=limit, offset=offset)
        if isinstance(payload, dict) and payload.get("_error"):
            break
        rows, next_offset = extract_page_rows(payload if isinstance(payload, dict) else {})
        all_rows.extend(rows)
        if len(all_rows) >= max_rows:
            all_rows = all_rows[:max_rows]
            break
        # if API provides next offset use it
        if next_offset is not None:
            try:
                offset = int(next_offset)
            except Exception:
                break
            if offset <= 0:
                break
        else:
            # fallback: assume offset pagination
            if len(rows) < limit:
                break
            offset += limit
        time.sleep(0.3)
    return all_rows


# ===========================
# AI: GENERATE JSON SECTIONS
# ===========================
def run_llm(prompt_text: str, provider: str, gemini_model: str, claude_model: str) -> dict:
    if provider == "Gemini":
        model = genai.GenerativeModel(gemini_model)
        resp = model.generate_content(prompt_text)
        raw = strip_json_fences(getattr(resp, "text", "") or "")
    else:
        if not CLAUDE_AVAILABLE:
            raise RuntimeError("Claude not available (missing key or SDK).")
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        msg = client.messages.create(
            model=claude_model,
            max_tokens=1200,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt_text}],
        )
        raw = strip_json_fences("".join([b.text for b in msg.content if hasattr(b, "text")]))

    try:
        return json.loads(raw)
    except Exception:
        # return raw for debugging
        return {"_parse_error": True, "_raw": raw}


# ===========================
# DOCX TEMPLATE RENDER
# ===========================
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_:\-]+\}\}")

def replace_in_paragraph(paragraph, mapping: dict):
    # naive replace on paragraph.text (good enough for your templates)
    text = paragraph.text
    for k, v in mapping.items():
        if k in text:
            text = text.replace(k, str(v))
    if text != paragraph.text:
        paragraph.text = text

def replace_in_cell(cell, mapping: dict):
    for p in cell.paragraphs:
        replace_in_paragraph(p, mapping)

def remove_instruction_paragraphs(doc: Document):
    kill_phrases = [
        "— e.g.",
        "— 2-3 paragraph",
        "— Brief overview",
        "{{*_COUNT}}",
        "{{KW_*}}",
        "{{REF_*}}",
        "{{COMP_*}}",
        "Populate with",
        "Use 0 or '-'",
        "Up to 20",
    ]
    # remove paragraphs containing these instructions
    for p in list(doc.paragraphs):
        t = (p.text or "").strip()
        if not t:
            continue
        if any(phrase in t for phrase in kill_phrases):
            p._element.getparent().remove(p._element)

def fill_keyword_table(table, keywords: list[dict], max_rows: int = 10):
    # table has header + 2 placeholder rows + "..." row. We'll replace by header + N rows.
    # Keep header row, then clear remaining rows and rebuild.
    while len(table.rows) > 1:
        tbl = table._tbl
        tbl.remove(table.rows[1]._tr)

    # Insert up to max_rows keywords
    for kw in keywords[:max_rows]:
        row = table.add_row().cells
        row[0].text = str(kw.get("keyword", kw.get("kw", "")) or "")
        row[1].text = str(kw.get("position", kw.get("pos", "")) or "")
        row[2].text = str(kw.get("volume", kw.get("vol", "")) or "")
        row[3].text = str(kw.get("traffic", kw.get("traf", "")) or "")
        row[4].text = str(kw.get("value", kw.get("traffic_value", "")) or "")
        row[5].text = str(kw.get("url", kw.get("ranking_url", "")) or "")

def fill_refdomains_table(table, refdomains: list[dict], max_rows: int = 10):
    # header row only, then build
    while len(table.rows) > 1:
        tbl = table._tbl
        tbl.remove(table.rows[1]._tr)

    for rd in refdomains[:max_rows]:
        row = table.add_row().cells
        row[0].text = str(rd.get("domain", rd.get("refdomain", "")) or "")
        row[1].text = str(rd.get("domain_rating", rd.get("dr", "")) or "")
        row[2].text = str(rd.get("links", rd.get("backlinks", "")) or "")
        row[3].text = str(rd.get("dofollow_links", rd.get("dofollow", "")) or "")
        row[4].text = str(rd.get("traffic", rd.get("organic_traffic", "")) or "")

def render_docx_full(template_path: Path, mapping: dict, keywords: list[dict], refdomains: list[dict]) -> BytesIO:
    doc = Document(str(template_path))

    # replace paragraphs
    for p in doc.paragraphs:
        replace_in_paragraph(p, mapping)

    # replace tables cells
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                replace_in_cell(cell, mapping)

    # expand keyword table (table index 5 in your template)
    if len(doc.tables) >= 6:
        fill_keyword_table(doc.tables[5], keywords, max_rows=10)

    # expand refdomains table (table index 8)
    if len(doc.tables) >= 9:
        fill_refdomains_table(doc.tables[8], refdomains, max_rows=10)

    # remove instruction paragraphs
    remove_instruction_paragraphs(doc)

    # final cleanup: if placeholders remain, blank them
    for p in doc.paragraphs:
        if PLACEHOLDER_RE.search(p.text or ""):
            p.text = PLACEHOLDER_RE.sub("", p.text).strip()

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


# ===========================
# XLSX TEMPLATE RENDER
# ===========================
def clear_sheet_from_row(ws, start_row: int):
    # delete all rows from start_row to end
    maxr = ws.max_row
    if maxr >= start_row:
        ws.delete_rows(start_row, maxr - start_row + 1)

def append_rows(ws, rows: list[list]):
    for r in rows:
        ws.append(r)

def slug_to_title(url: str) -> str:
    try:
        path = urlparse(url).path.strip("/")
        if not path:
            return ""
        last = path.split("/")[-1]
        last = re.sub(r"[-_]+", " ", last).strip()
        return last.title()
    except Exception:
        return ""

def suggest_h1(current_title: str, url: str) -> str:
    t = (current_title or "").strip()
    if t and t.lower() != "missing":
        return t[:70]
    s = slug_to_title(url)
    return s[:70] if s else ""

def suggest_title(current_title: str, url: str) -> str:
    t = (current_title or "").strip()
    if not t or t.lower() == "missing":
        t = slug_to_title(url)
    # trim to ~60 chars
    return (t[:60]).strip()

def suggest_meta(current_meta: str, title: str) -> str:
    m = (current_meta or "").strip()
    if m and m.lower() != "missing":
        return m[:155].strip()
    t = (title or "").strip()
    return (t[:150]).strip()

def suggest_alt(image_url: str, page_url: str) -> str:
    name = ""
    try:
        name = urlparse(image_url).path.split("/")[-1]
    except Exception:
        pass
    name = re.sub(r"\.(png|jpg|jpeg|webp|gif|svg)$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"[-_]+", " ", name).strip()
    if not name:
        name = slug_to_title(page_url)
    return name[:80]

def render_xlsx_full(template_path: Path, issue_rows_by_sheet: dict, max_rows_per_sheet: int) -> BytesIO:
    wb = openpyxl.load_workbook(str(template_path))

    # For each issue sheet: clear placeholder row2 and fill
    for sheet_name, rows in issue_rows_by_sheet.items():
        if sheet_name not in wb.sheetnames:
            continue
        ws = wb[sheet_name]
        clear_sheet_from_row(ws, 2)
        if rows:
            append_rows(ws, rows[:max_rows_per_sheet])

    out = BytesIO()
    wb.save(out)
    out.seek(0)
    return out


# ===========================
# UI
# ===========================
with st.sidebar:
    st.markdown("### System Status")
    st.write("Gemini:", "✅" if GEMINI_AVAILABLE else "❌")
    st.write("Claude:", "✅" if CLAUDE_AVAILABLE else "❌")
    st.write("Ahrefs:", "✅" if AHREFS_AVAILABLE else "❌")

st.title("CLAUDIO — SEO Auditor (Template Output)")

audit_type = st.radio("Audit Type", ["Basic", "Full (Ahrefs Site Audit Project)"])

provider_options = []
if GEMINI_AVAILABLE:
    provider_options.append("Gemini")
if CLAUDE_AVAILABLE:
    provider_options.append("Claude")

if not provider_options:
    st.error("No AI provider configured. Add GOOGLE_API_KEY and/or ANTHROPIC_API_KEY in Streamlit Secrets.")
    st.stop()

provider = st.selectbox("AI Provider", provider_options, index=0)

gemini_model = st.text_input("Gemini model", value="gemini-2.0-flash")
claude_model = st.text_input("Claude model", value="claude-3-5-sonnet-20241022")

country = st.text_input("Country (Ahrefs)", value="us")
max_urls_per_issue = st.number_input("Max URLs per issue (Excel)", min_value=10, max_value=2000, value=300, step=50)
debug_ahrefs = st.checkbox("Debug Ahrefs responses", value=False)

url_input = st.text_input("Website URL", placeholder="https://example.com")

run_btn = st.button("Generate Audit")

if run_btn:
    if not url_input:
        st.error("Enter a URL.")
        st.stop()

    domain = normalize_domain(url_input)
    if not domain:
        st.error("Could not parse domain from URL.")
        st.stop()

    audit_date = datetime.utcnow().strftime("%B %Y")

    # ---------------------------
    # BASIC DATA
    # ---------------------------
    progress = st.progress(0)
    status = st.empty()
    status.write("Analyzing page...")
    progress.progress(15)

    basic_data = {}
    try:
        basic_data = analyze_basic_site(url_input)
    except Exception as e:
        basic_data = {"_error": str(e)}

    # ---------------------------
    # FULL: AHREFS COLLECTION
    # ---------------------------
    metrics = {}
    kw_payload = {}
    backlinks_payload = {}
    anchors_payload = {}
    refdomains_payload = {}
    competitors_payload = {}
    sa_projects = {}
    sa_project = None
    sa_project_id = None
    sa_issues_payload = {}
    issues_list = []

    issue_counts = {}     # sheet_key -> count
    issue_ids = {}        # sheet_key -> issue_id
    issue_rows_by_sheet = {}  # sheet_name -> rows to write in Excel

    if audit_type.startswith("Full"):
        if not AHREFS_AVAILABLE:
            st.error("Ahrefs key missing. Full audit needs AHREFS_API_KEY.")
            st.stop()

        status.write("Fetching Ahrefs (Site Explorer)...")
        progress.progress(30)
        metrics = get_site_explorer_metrics(domain)
        kw_payload = get_organic_keywords(domain, country=country, limit=50)
        backlinks_payload = get_backlinks_sample(domain, limit=30)
        anchors_payload = get_anchors(domain, limit=20)
        refdomains_payload = get_refdomains(domain, limit=20)
        competitors_payload = get_organic_competitors(domain, country=country, limit=5)

        status.write("Resolving Ahrefs Site Audit project...")
        progress.progress(45)
        sa_projects = site_audit_projects()
        sa_project, sa_project_id = pick_project_for_domain(sa_projects, domain)

        if not sa_project_id:
            if debug_ahrefs:
                st.subheader("Debug: Site Audit Projects raw")
                st.json(sa_projects)
            st.error(f"No Ahrefs Site Audit project found for domain: {domain}")
            st.stop()

        status.write("Fetching Site Audit issues...")
        progress.progress(55)
        sa_issues_payload = site_audit_issues(sa_project_id)
        issues_list = extract_issue_list(sa_issues_payload)

        if debug_ahrefs:
            with st.expander("Debug: Site Audit issues raw"):
                st.json(sa_issues_payload)

        # Map issues -> your template sheets
        ISSUE_MAP = {
            "H1 Missing": ["missing h1", "h1 missing"],
            "Multiple H1": ["multiple h1", "more than one h1"],
            "Duplicate Titles": ["duplicate title"],
            "Duplicate Meta": ["duplicate meta description", "duplicate description"],
            "Title Too Long": ["title too long", "meta title too long"],
            "Title Too Short": ["title too short", "meta title too short"],
            "Meta Too Long": ["meta description too long", "description too long"],
            "Meta Too Short": ["meta description too short", "description too short"],
            "Missing Canonical": ["missing canonical"],
            "Broken Internal": ["broken internal", "internal link", "links to broken page", "broken link to"],
            "Broken External": ["broken external", "external link"],
            "Redirect Chains": ["redirect chain", "redirects chain"],
            "Orphan Pages": ["orphan page", "orphaned page"],
            "Missing Alt Text": ["missing alt", "alt text"],
            "Broken Images": ["broken image"],
            "Thin Content": ["thin content", "low word count", "below 300 words"],
            # extra (Word-only table):
            "ROBOTS_MISSING": ["missing robots.txt", "robots.txt is missing"],
            "SITEMAP_MISSING": ["missing xml sitemap", "sitemap.xml is missing", "missing sitemap"],
            "HTTPS_ISSUES": ["mixed content", "http/https mixed"],
        }

        # Get issue ids + counts
        for sheet_name, pats in ISSUE_MAP.items():
            iid, cnt = find_issue_id(issues_list, pats)
            issue_ids[sheet_name] = iid
            issue_counts[sheet_name] = cnt

        # Fetch page explorer rows for the Excel sheets (only for actual sheets + count>0)
        status.write("Fetching affected URLs for Excel sheets...")
        progress.progress(70)

        for sheet_name in [
            "H1 Missing","Multiple H1","Duplicate Titles","Duplicate Meta","Title Too Long","Title Too Short",
            "Meta Too Long","Meta Too Short","Missing Canonical","Broken Internal","Broken External","Redirect Chains",
            "Orphan Pages","Missing Alt Text","Broken Images","Thin Content"
        ]:
            iid = issue_ids.get(sheet_name)
            cnt = issue_counts.get(sheet_name, 0)
            if not iid or cnt <= 0:
                issue_rows_by_sheet[sheet_name] = []
                continue

            rows = fetch_pages_for_issue(sa_project_id, iid, max_rows=max_urls_per_issue)

            # Convert Ahrefs rows -> your sheet columns
            formatted = []
            if sheet_name in ["H1 Missing", "Multiple H1", "Duplicate Titles", "Duplicate Meta",
                              "Title Too Long","Title Too Short","Meta Too Long","Meta Too Short","Thin Content"]:
                for r in rows:
                    url = r.get("url") or r.get("page_url") or r.get("address") or ""
                    title = r.get("title") or r.get("meta_title") or r.get("page_title") or ""
                    meta = r.get("meta_description") or r.get("description") or ""
                    wc = r.get("word_count") or r.get("words") or r.get("content_word_count") or ""
                    # priority: use fixed from template row2 when present; we set sensible defaults
                    pr = "HIGH" if sheet_name in ["H1 Missing","Duplicate Titles","Duplicate Meta"] else "MEDIUM"
                    if sheet_name in ["Thin Content"]:
                        pr = "MEDIUM"
                    suggested = ""
                    if sheet_name in ["H1 Missing", "Multiple H1"]:
                        suggested = suggest_h1(title, url)
                    elif sheet_name in ["Duplicate Titles","Title Too Long","Title Too Short"]:
                        suggested = suggest_title(title, url)
                    elif sheet_name in ["Duplicate Meta","Meta Too Long","Meta Too Short"]:
                        suggested = suggest_meta(meta, title)
                    elif sheet_name == "Thin Content":
                        suggested = "Expand content to match search intent; add sections, FAQs, examples; aim for 700–1200 words where relevant."
                    formatted.append([url, title, meta, wc, pr, suggested])

            elif sheet_name in ["Missing Canonical"]:
                # URL, Current Canonical, Recommended Canonical, Priority, Suggested Fix
                for r in rows:
                    url = r.get("url") or r.get("page_url") or ""
                    current = r.get("canonical") or r.get("current_canonical") or ""
                    recommended = url
                    pr = "HIGH"
                    fix = "Add a self-referencing canonical tag (or correct it to the preferred URL)."
                    formatted.append([url, current, recommended, pr, fix])

            elif sheet_name in ["Broken Internal","Broken External"]:
                # Source URL, Broken Link URL, HTTP Status, Anchor Text, Priority, Suggested Fix
                for r in rows:
                    source = r.get("source_url") or r.get("url") or r.get("page_url") or ""
                    broken = r.get("broken_url") or r.get("link_url") or r.get("target_url") or ""
                    status_code = r.get("status") or r.get("http_status") or r.get("status_code") or ""
                    anchor = r.get("anchor") or r.get("anchor_text") or ""
                    pr = "HIGH" if sheet_name == "Broken Internal" else "MEDIUM"
                    fix = "Update the link to a valid URL (or remove it). If moved, link directly to the final destination."
                    formatted.append([source, broken, status_code, anchor, pr, fix])

            elif sheet_name in ["Redirect Chains"]:
                # Initial URL, Redirect Chain, Final URL, Chain Length, Priority
                for r in rows:
                    initial = r.get("initial_url") or r.get("url") or ""
                    chain = r.get("chain") or r.get("redirect_chain") or r.get("chain_path") or ""
                    final = r.get("final_url") or r.get("destination_url") or ""
                    length = r.get("length") or r.get("chain_length") or ""
                    pr = "MEDIUM"
                    formatted.append([initial, chain, final, length, pr])

            elif sheet_name in ["Orphan Pages"]:
                # URL, Estimated Traffic, Priority, Suggested Fix
                for r in rows:
                    url = r.get("url") or r.get("page_url") or ""
                    traf = r.get("traffic") or r.get("estimated_traffic") or ""
                    pr = "MEDIUM"
                    fix = "Add internal links from relevant hub/category pages and ensure it’s in navigation/sitemaps where appropriate."
                    formatted.append([url, traf, pr, fix])

            elif sheet_name in ["Missing Alt Text"]:
                # Page URL, Image URL, Priority, Suggested Alt Text
                for r in rows:
                    page = r.get("page_url") or r.get("url") or ""
                    img = r.get("image_url") or r.get("url_image") or r.get("asset_url") or ""
                    pr = "LOW"
                    alt = suggest_alt(img, page)
                    formatted.append([page, img, pr, alt])

            elif sheet_name in ["Broken Images"]:
                # Page URL, Broken Image URL, HTTP Status, Priority, Suggested Fix
                for r in rows:
                    page = r.get("page_url") or r.get("url") or ""
                    img = r.get("broken_image_url") or r.get("image_url") or r.get("asset_url") or ""
                    status_code = r.get("status") or r.get("http_status") or r.get("status_code") or ""
                    pr = "LOW"
                    fix = "Fix the image URL, upload missing asset, or remove the broken image reference."
                    formatted.append([page, img, status_code, pr, fix])

            issue_rows_by_sheet[sheet_name] = formatted

        if debug_ahrefs:
            with st.expander("Debug: Example mapped sheet rows"):
                for k, v in list(issue_rows_by_sheet.items())[:3]:
                    st.write(k, "rows:", len(v))
                    st.json(v[:2])

    # ---------------------------
    # Build CONTEXT for prompt
    # ---------------------------
    status.write("Building AI context...")
    progress.progress(80)

    top_keywords = []
    kw_items = safe_get(kw_payload, "keywords", default=None)
    if kw_items is None:
        kw_items = safe_get(kw_payload, "data", default=[]) if isinstance(kw_payload, dict) else []
    if isinstance(kw_items, list):
        for it in kw_items[:10]:
            top_keywords.append({
                "keyword": it.get("keyword") or it.get("kw"),
                "position": it.get("position") or it.get("pos"),
                "volume": it.get("volume") or it.get("vol"),
                "traffic": it.get("traffic") or it.get("traf"),
                "value": it.get("traffic_value") or it.get("value"),
                "url": it.get("url") or it.get("ranking_url"),
            })

    # keyword distribution
    dist = {"1_3": 0, "4_10": 0, "11_20": 0, "21_50": 0, "51_100": 0}
    for it in kw_items[:100] if isinstance(kw_items, list) else []:
        pos = it.get("position") or it.get("pos")
        try:
            pos = int(pos)
        except Exception:
            continue
        if 1 <= pos <= 3: dist["1_3"] += 1
        elif 4 <= pos <= 10: dist["4_10"] += 1
        elif 11 <= pos <= 20: dist["11_20"] += 1
        elif 21 <= pos <= 50: dist["21_50"] += 1
        elif 51 <= pos <= 100: dist["51_100"] += 1

    # Site Explorer metrics extraction (flexible)
    m = safe_get(metrics, "metrics", default=metrics) if isinstance(metrics, dict) else {}
    domain_rating = m.get("domain_rating") or m.get("dr") or 0
    ahrefs_rank = m.get("ahrefs_rank") or m.get("rank") or ""
    backlinks_total = m.get("backlinks") or 0
    refdomains_total = m.get("refdomains") or m.get("referring_domains") or 0
    organic_keywords = m.get("organic_keywords") or 0
    organic_traffic = m.get("organic_traffic") or 0
    dofollow_backlinks = m.get("dofollow_backlinks") or m.get("dofollow") or ""
    dofollow_refdomains = m.get("dofollow_refdomains") or ""

    # Competitors list
    competitors = []
    comp_items = safe_get(competitors_payload, "competitors", default=None)
    if comp_items is None:
        comp_items = safe_get(competitors_payload, "data", default=[]) if isinstance(competitors_payload, dict) else []
    if isinstance(comp_items, list):
        for c in comp_items[:5]:
            competitors.append({
                "domain": c.get("domain") or c.get("target") or "",
                "domain_rating": c.get("domain_rating") or c.get("dr") or "",
                "refdomains": c.get("refdomains") or c.get("referring_domains") or "",
                "keywords": c.get("organic_keywords") or c.get("keywords") or "",
                "traffic": c.get("organic_traffic") or c.get("traffic") or "",
                "traffic_value": c.get("traffic_value") or c.get("value") or "",
                "common_keywords": c.get("common_keywords") or "",
            })

    context = {
        "domain": domain,
        "audit_date": audit_date,
        "basic_data": basic_data,
        "site_explorer": {
            "domain_rating": domain_rating,
            "ahrefs_rank": ahrefs_rank,
            "backlinks_total": backlinks_total,
            "refdomains_total": refdomains_total,
            "organic_keywords": organic_keywords,
            "organic_traffic": organic_traffic,
            "dofollow_backlinks": dofollow_backlinks,
            "dofollow_refdomains": dofollow_refdomains,
        },
        "site_audit": {
            "project_id": sa_project_id,
            "issue_counts": issue_counts,
        } if audit_type.startswith("Full") else {},
        "top_keywords": top_keywords,
        "keyword_distribution": dist,
        "competitors": competitors,
    }

    # ---------------------------
    # AI SECTIONS
    # ---------------------------
    status.write("Generating AI narrative blocks...")
    progress.progress(90)

    prompt_path = PROMPT_FULL if audit_type.startswith("Full") else PROMPT_BASIC
    prompt_text = load_prompt(prompt_path).replace("{{CONTEXT_JSON}}", json.dumps(context, ensure_ascii=False, indent=2))

    ai = run_llm(prompt_text, provider=provider, gemini_model=gemini_model, claude_model=claude_model)
    if ai.get("_parse_error"):
        st.error("AI output was not valid JSON. Enable debug or tighten the prompt.")
        st.code(ai.get("_raw", "")[:4000])
        st.stop()

    # ---------------------------
    # Build DOCX placeholder mapping
    # ---------------------------
    content_issues_count = sum(issue_counts.get(k, 0) for k in [
        "H1 Missing","Multiple H1","Duplicate Titles","Duplicate Meta","Title Too Long","Title Too Short",
        "Meta Too Long","Meta Too Short","Thin Content","Missing Alt Text","Broken Images"
    ])
    technical_issues_count = sum(issue_counts.get(k, 0) for k in [
        "Missing Canonical","Broken Internal","Broken External","Redirect Chains","Orphan Pages",
        "ROBOTS_MISSING","SITEMAP_MISSING","HTTPS_ISSUES"
    ])

    mapping = {
        "{{DOMAIN}}": domain,
        "{{AUDIT_DATE}}": audit_date,

        "{{DOMAIN_RATING}}": domain_rating,
        "{{REFERRING_DOMAINS}}": refdomains_total,
        "{{ORGANIC_KEYWORDS}}": organic_keywords,
        "{{ORGANIC_TRAFFIC}}": organic_traffic,

        "{{CONTENT_ISSUES_COUNT}}": content_issues_count,
        "{{TECHNICAL_ISSUES_COUNT}}": technical_issues_count,

        "{{CONTENT_PRIORITY}}": priority_from_count(content_issues_count),
        "{{TECHNICAL_PRIORITY}}": priority_from_count(technical_issues_count),

        "{{BACKLINK_OPP_COUNT}}": refdomains_total,
        "{{COMPETITIVE_GAPS_COUNT}}": len(competitors),

        "{{EXECUTIVE_SUMMARY}}": ai.get("executive_summary", ""),
        "{{CONTENT_AUDIT_SUMMARY}}": ai.get("content_audit_summary", ""),
        "{{TECHNICAL_AUDIT_SUMMARY}}": ai.get("technical_audit_summary", ""),
        "{{KEYWORD_OVERVIEW}}": ai.get("keyword_overview", ""),
        "{{BACKLINK_OBSERVATIONS}}": ai.get("backlink_observations", ""),
        "{{COMPETITIVE_ANALYSIS}}": ai.get("competitive_analysis", ""),

        "{{MISSING_H1_COUNT}}": issue_counts.get("H1 Missing", 0),
        "{{MULTIPLE_H1_COUNT}}": issue_counts.get("Multiple H1", 0),
        "{{DUP_TITLES_COUNT}}": issue_counts.get("Duplicate Titles", 0),
        "{{DUP_META_COUNT}}": issue_counts.get("Duplicate Meta", 0),

        "{{TITLE_LONG_COUNT}}": issue_counts.get("Title Too Long", 0),
        "{{TITLE_SHORT_COUNT}}": issue_counts.get("Title Too Short", 0),
        "{{META_LONG_COUNT}}": issue_counts.get("Meta Too Long", 0),
        "{{META_SHORT_COUNT}}": issue_counts.get("Meta Too Short", 0),
        "{{THIN_CONTENT_COUNT}}": issue_counts.get("Thin Content", 0),
        "{{MISSING_ALT_COUNT}}": issue_counts.get("Missing Alt Text", 0),
        "{{BROKEN_IMAGES_COUNT}}": issue_counts.get("Broken Images", 0),

        "{{TITLE_LONG_PRIORITY}}": priority_from_count(issue_counts.get("Title Too Long", 0)),
        "{{TITLE_SHORT_PRIORITY}}": priority_from_count(issue_counts.get("Title Too Short", 0)),
        "{{META_LONG_PRIORITY}}": priority_from_count(issue_counts.get("Meta Too Long", 0)),
        "{{META_SHORT_PRIORITY}}": priority_from_count(issue_counts.get("Meta Too Short", 0)),
        "{{THIN_CONTENT_PRIORITY}}": priority_from_count(issue_counts.get("Thin Content", 0)),
        "{{MISSING_ALT_PRIORITY}}": priority_from_count(issue_counts.get("Missing Alt Text", 0)),
        "{{BROKEN_IMAGES_PRIORITY}}": priority_from_count(issue_counts.get("Broken Images", 0)),

        "{{MISSING_CANONICAL_COUNT}}": issue_counts.get("Missing Canonical", 0),
        "{{BROKEN_INTERNAL_COUNT}}": issue_counts.get("Broken Internal", 0),
        "{{BROKEN_EXTERNAL_COUNT}}": issue_counts.get("Broken External", 0),
        "{{REDIRECT_CHAINS_COUNT}}": issue_counts.get("Redirect Chains", 0),
        "{{ORPHAN_PAGES_COUNT}}": issue_counts.get("Orphan Pages", 0),

        "{{MISSING_CANONICAL_PRIORITY}}": priority_from_count(issue_counts.get("Missing Canonical", 0)),
        "{{BROKEN_INTERNAL_PRIORITY}}": priority_from_count(issue_counts.get("Broken Internal", 0)),
        "{{BROKEN_EXTERNAL_PRIORITY}}": priority_from_count(issue_counts.get("Broken External", 0)),
        "{{REDIRECT_CHAINS_PRIORITY}}": priority_from_count(issue_counts.get("Redirect Chains", 0)),
        "{{ORPHAN_PAGES_PRIORITY}}": priority_from_count(issue_counts.get("Orphan Pages", 0)),

        "{{ROBOTS_MISSING}}": issue_counts.get("ROBOTS_MISSING", 0),
        "{{SITEMAP_MISSING}}": issue_counts.get("SITEMAP_MISSING", 0),
        "{{HTTPS_ISSUES_COUNT}}": issue_counts.get("HTTPS_ISSUES", 0),

        "{{ROBOTS_PRIORITY}}": priority_from_count(issue_counts.get("ROBOTS_MISSING", 0)),
        "{{SITEMAP_PRIORITY}}": priority_from_count(issue_counts.get("SITEMAP_MISSING", 0)),
        "{{HTTPS_PRIORITY}}": priority_from_count(issue_counts.get("HTTPS_ISSUES", 0)),

        "{{KW_POS_1_3}}": dist["1_3"],
        "{{KW_POS_4_10}}": dist["4_10"],
        "{{KW_POS_11_20}}": dist["11_20"],
        "{{KW_POS_21_50}}": dist["21_50"],
        "{{KW_POS_51_100}}": dist["51_100"],

        # Backlink metrics table placeholders
        "{{DR}}": domain_rating,
        "{{AHREFS_RANK}}": ahrefs_rank,
        "{{BACKLINKS}}": backlinks_total,
        "{{DOFOLLOW_BACKLINKS}}": dofollow_backlinks,
        "{{REFDOMAINS}}": refdomains_total,
        "{{DOFOLLOW_REFDOMAINS}}": dofollow_refdomains,
    }

    # Quick wins (5)
    qw = ai.get("quick_wins", []) if isinstance(ai.get("quick_wins"), list) else []
    while len(qw) < 5:
        qw.append({"action": "", "impact": "Medium", "effort": "Low"})
    for i in range(5):
        mapping[f"{{{{QUICK_WIN_{i+1}}}}}"] = qw[i].get("action", "")
        mapping[f"{{{{QW{i+1}_IMPACT}}}}"] = qw[i].get("impact", "Medium")
        mapping[f"{{{{QW{i+1}_EFFORT}}}}"] = qw[i].get("effort", "Low")

    # Competitors (fill up to 5)
    mapping["{{YOUR_DR}}"] = domain_rating
    mapping["{{YOUR_REFDOM}}"] = refdomains_total
    mapping["{{YOUR_KW}}"] = organic_keywords
    mapping["{{YOUR_TRAFFIC}}"] = organic_traffic
    mapping["{{YOUR_VALUE}}"] = ""  # not always available

    for i in range(5):
        c = competitors[i] if i < len(competitors) else {}
        mapping[f"{{{{COMP_{i+1}}}}}"] = c.get("domain", "")
        mapping[f"{{{{COMP_{i+1}_DR}}}}"] = c.get("domain_rating", "")
        mapping[f"{{{{COMP_{i+1}_REFDOM}}}}"] = c.get("refdomains", "")
        mapping[f"{{{{COMP_{i+1}_KW}}}}"] = c.get("keywords", "")
        mapping[f"{{{{COMP_{i+1}_TRAFFIC}}}}"] = c.get("traffic", "")
        mapping[f"{{{{COMP_{i+1}_VALUE}}}}"] = c.get("traffic_value", "")

    # Refdomains list for Word table
    rd_items = safe_get(refdomains_payload, "refdomains", default=None)
    if rd_items is None:
        rd_items = safe_get(refdomains_payload, "data", default=[]) if isinstance(refdomains_payload, dict) else []
    refdomains_list = rd_items if isinstance(rd_items, list) else []

    # ---------------------------
    # Render outputs
    # ---------------------------
    status.write("Rendering templates (DOCX/XLSX)...")
    progress.progress(98)

    # DOCX
    docx_out = render_docx_full(DOCX_TEMPLATE_FULL, mapping, top_keywords, refdomains_list)

    # XLSX only for Full
    xlsx_out = None
    if audit_type.startswith("Full"):
        xlsx_out = render_xlsx_full(XLSX_TEMPLATE_FULL, issue_rows_by_sheet, max_rows_per_issue)

    progress.progress(100)
    status.write("Done.")

    st.success("Audit generated.")

    # Preview AI blocks
    with st.expander("AI blocks (JSON)"):
        st.json(ai)

    # Downloads
    st.subheader("Download")
    st.download_button(
        "Download Word report (.docx)",
        data=docx_out,
        file_name=f"SEO_Audit_{domain}_{datetime.utcnow().strftime('%Y%m%d')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )

    if xlsx_out:
        st.download_button(
            "Download Tasks workbook (.xlsx)",
            data=xlsx_out,
            file_name=f"SEO_Tasks_{domain}_{datetime.utcnow().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
