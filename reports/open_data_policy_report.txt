<a href="https://colab.research.google.com/github/1heidi/open-data-monitor/blob/main/Open_AI_Sci_Policy.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>


```python
# ================================================================
# 📊 OPEN DATA POLICY MONITOR — U.S. ACADEMIC & GOVERNMENT SOURCES
# ================================================================
#
# 🧭 OVERVIEW:
# This Google Colab notebook automatically searches for, summarizes,
# and reports on recent developments (previous 7 days)in **U.S. open data and open
# science policy**, particularly those relevant to academia and
# federal agencies.
#
# The system:
#   1. Gathers recent web articles and news (via SERPAPI).
#   2. Optionally queries structured feeds (e.g., NASA, NIH, NSF, OSTP, etc.).
#   3. Summarizes each finding using OpenAI GPT models, with
#   4. Produces a formatted Markdown report (.md) with explicit instructions "DO NOT fabricate or infer connections"
#        • Individual article summaries
#        • A meta-summary highlighting key policy trends
#   5. Saves the report in `/content/open_data_monitor/`
#      (or Google Drive if mounted).
#   6. Optionally emails the report to you (via Gmail API or SMTP).
#
# ------------------------------------------------
# 📂 EXPECTED OUTPUTS:
# ------------------------------------------------
#   • Markdown report file:
#       e.g., /content/open_data_monitor/open_data_policy_report_YYYYMMDD_HHMM.md
#   • Console output showing:
#       ✅ Collection and summarization progress
#       💰 Token usage + estimated cost
#       ⚠️ Warnings for token limits or missing API keys
#
# ------------------------------------------------
# ⏱️ RUNTIME ESTIMATES:
# ------------------------------------------------
#   • Section 3 (collection): ~10–20 seconds (20 entries typical)
#   • Section 4 (summarization): ~2–4 minutes
#   • Section 5 (report saving/email): <10 seconds
#
# Total: 2–5 minutes (depending on entry count and connection speed)
#
# ------------------------------------------------
# 💰 COST ESTIMATES (OpenAI API):
# ------------------------------------------------
#   • Typical run (20 summaries + meta-summary):
#       ≈ 6,000–8,000 input tokens
#       ≈ 2,000–3,000 output tokens
#       → ~$0.02–$0.05 using `gpt-4o-mini`
#
# Adjusting parameters or model choice (e.g., `gpt-4o` or `gpt-3.5-turbo`)
# will change cost and speed proportionally.
#
# CHECK USAGE HERE: https://platform.openai.com/settings/organization/limits
# ------------------------------------------------
# ⚙️ CONFIGURATION NOTES:
# ------------------------------------------------
# 1️⃣ API KEYS:
#     • Set your SERPAPI_KEY and OPENAI_API_KEY in Section 2.
#     • Gmail settings (if emailing) also live in Section 2.
#
# 2️⃣ TOKEN BUDGET CONTROL:
#     • The token limit for summarization is set in SECTION 3.
#     • Look for this line:
#           MAX_TOKENS_BUDGET = 12000
#       → Reduce it to conserve cost or prevent truncation warnings.
#       → Increase it if you consistently hit truncation and have budget.
#
# 3️⃣ ADDING SOURCES OR QUERIES:
#     • Modify the `search_queries` list in SECTION 3.
#     • Each string represents a Google-style search with logical operators.
#
# ------------------------------------------------
# 🧩 TROUBLESHOOTING:
# ------------------------------------------------
#   • If "name 'client' is not defined": rerun Section 2 to reinitialize API clients.
#   • If API quota errors appear, check your OpenAI billing page.
#   • If Gmail auth fails, verify that your credentials are correct or use the Gmail API.
#
# ------------------------------------------------
# 🕒 SCHEDULING:
# ------------------------------------------------
#   • To run weekly, use Colab’s "Schedule notebook" feature or
#     connect via Google Apps Script / GitHub Actions.
#
# ------------------------------------------------
# ✍️ AUTHOR / MAINTAINER:
# ------------------------------------------------
#   • Custom notebook by ChatGPT (GPT-5), configured for monitoring
#     U.S. open data policy and academic open science developments.
# ================================================================

```


```python
# ===========================================================
# ⚙️ SECTION 1: SETUP & INSTALLS
# ===========================================================
# Installs dependencies and imports necessary libraries.
# -----------------------------------------------------------

!pip install -q openai feedparser google-auth-oauthlib google-auth-httplib2 google-api-python-client requests

import os
import json
import time
import feedparser
import requests
from datetime import datetime
from time import perf_counter, sleep
from openai import OpenAI

# ✅ Confirm setup
print("✅ Environment setup complete and libraries imported successfully.")

```

    ✅ Environment setup complete and libraries imported successfully.



```python
# ===========================================================
# ⚙️ SECTION 2: CONFIGURATION & API KEYS
# ===========================================================
#
# Purpose:
#   • Define API keys and feature toggles for the notebook
#   • Configure Gmail sender settings (optional)
#   • Control token budgeting and cost tracking
# -----------------------------------------------------------

import os
from datetime import datetime

# ---------- Part A. OpenAI + SERPAPI Keys ----------

# 👇 Paste your actual keys between the quotes

import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

# ---------- Part B. SERPAPI Usage (Optional) ----------

# Toggle SERPAPI usage (False = RSS only)
USE_SERPAPI = True

# ---------- Part B. Gmail (Optional — Section 5) ----------

SEND_EMAIL = True  # toggle emailing on/off

# ---------- Part C. Store keys securely in environment ----------

if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
if SERPAPI_KEY:
    os.environ["SERPAPI_KEY"] = SERPAPI_KEY
if GMAIL_APP_PASSWORD:
    os.environ["GMAIL_APP_PASSWORD"] = GMAIL_APP_PASSWORD

# ---------- Part D. Token Budget + Cost Tracking ----------

TOKEN_BUDGET = 20_000  # soft token limit per run

# GPT-4 Turbo (approx) pricing
COST_PER_1K_INPUT = 0.01
COST_PER_1K_OUTPUT = 0.03

def estimate_cost(input_tokens, output_tokens):
    """Estimate total API cost based on token usage."""
    return round(
        (input_tokens / 1000 * COST_PER_1K_INPUT) +
        (output_tokens / 1000 * COST_PER_1K_OUTPUT), 4
    )

# ---------- Part E. Session Metadata ----------

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
print(f"✅ Configuration loaded. Run ID: {RUN_ID}")
print(f"   SERPAPI enabled: {USE_SERPAPI}")
print(f"   Token budget: {TOKEN_BUDGET:,} tokens\n")

```

    ✅ Configuration loaded. Run ID: 20251014_145558
       SERPAPI enabled: True
       Token budget: 20,000 tokens
    



```python
# ===========================================================
# 3A. SETUP + SOURCES
# ===========================================================
import feedparser, requests, time, json

print("✅ Section 3A loaded: Feedparser + Requests imported.")

SOURCES = [
    {"name": "White House OSTP Blog", "url": "https://www.whitehouse.gov/ostp/feed/"},
    {"name": "NSF Science Matters News", "url": "https://new.nsf.gov/rss.xml"},
    {"name": "NIH Extramural Nexus", "url": "https://nexus.od.nih.gov/all/feed/"},
    {"name": "DOE Office of Science News", "url": "https://www.energy.gov/science/listings/office-science-news/rss.xml"},
    {"name": "The Scholarly Kitchen", "url": "https://scholarlykitchen.sspnet.org/feed/"},
    {"name": "SPARC Open Access News", "url": "https://sparcopen.org/news/feed/"},
    {"name": "Research Data Alliance Blog", "url": "https://www.rd-alliance.org/blog/feed"},
    {"name": "OpenAIRE Blog", "url": "https://www.openaire.eu/feed"},
    {"name": "CODATA Blog", "url": "https://codata.org/feed/"},
    {"name": "JCU Sci Policy", "url": "http://cssp-jnu.blogspot.com/feeds/posts/default?alt=rss"},
    {"name": "Journ Sci Policy", "url": "https://www.sciencepolicyjournal.org/blog/feed"},
    {"name": "Sci4All", "url": "https://sciencepolicyforall.wordpress.com/feed/"},
    {"name": "PLOS Sci Policy", "url": "https://journals.plos.org/plosone/browse/science_policy"}
]

print(f"📡 Loaded {len(SOURCES)} RSS sources.")
```

    ✅ Section 3A loaded: Feedparser + Requests imported.
    📡 Loaded 13 RSS sources.



```python
# ===========================================================
# 3B. FETCH + PARSE RSS FEEDS (and optional SERPAPI)
# ===========================================================
# - Collects recent posts from configured RSS feeds
# - (Optional) adds SERPAPI search results about "open data policy"
# - Produces a clean list of dicts: entries = [{title, link, source, summary, published}]
# -----------------------------------------------------------

import hashlib
import datetime as dt

print("🚀 Section 3B starting...")

# ------------------------------
# Helper: Safe extract text fields
# ------------------------------
def safe_get(entry, key):
    try:
        val = entry.get(key, "")
        return val if val else ""
    except Exception:
        return ""

# ------------------------------
# Fetch RSS Feeds
# ------------------------------
entries = []
for s in SOURCES:
    name = s["name"]
    url = s["url"]
    try:
        feed = feedparser.parse(url)
        count = 0
        for e in feed.entries[:10]:  # cap per source for speed
            title = safe_get(e, "title")
            link = safe_get(e, "link")
            summary = safe_get(e, "summary") or safe_get(e, "description")
            published = safe_get(e, "published") or safe_get(e, "updated") or ""
            # Normalize date to ISO
            try:
                published_dt = dt.datetime(*e.published_parsed[:6])
                published = published_dt.strftime("%Y-%m-%d")
            except Exception:
                pass
            # skip if no title or link
            if not title or not link:
                continue
            entries.append({
                "title": title.strip(),
                "link": link.strip(),
                "source": name,
                "summary": summary.strip(),
                "published": published,
            })
            count += 1
        print(f"✅ {name}: {count} entries fetched.")
    except Exception as ex:
        print(f"⚠️ Failed to parse {name}: {ex}")

print(f"📚 Total entries collected so far: {len(entries)}")

# ------------------------------
# Optional: SERPAPI augmentation
# ------------------------------
if USE_SERPAPI and os.environ.get("SERPAPI_KEY"):
    import requests

    print("🔍 Fetching supplemental results from SERPAPI (Google News)...")
    q = "U.S. open data OR open science policy site:.gov OR site:.edu"
    serp_url = f"https://serpapi.com/search.json?engine=google_news&q={q}&api_key={os.environ['SERPAPI_KEY']}"
    try:
        resp = requests.get(serp_url, timeout=30)
        data = resp.json()
        for art in data.get("news_results", [])[:10]:
            entries.append({
                "title": art.get("title", ""),
                "link": art.get("link", ""),
                "source": "SERPAPI",
                "summary": art.get("snippet", ""),
                "published": art.get("date", ""),
            })
        print("✅ SERPAPI results added.")
    except Exception as ex:
        print(f"⚠️ SERPAPI fetch failed: {ex}")
else:
    print("🔎 SERPAPI skipped (disabled or no API key).")

# ------------------------------
# Deduplicate by title hash
# ------------------------------
seen = set()
deduped = []
for e in entries:
    h = hashlib.md5(e["title"].encode("utf-8")).hexdigest()
    if h not in seen:
        deduped.append(e)
        seen.add(h)

entries = deduped
print(f"🧹 Deduplicated. Final entry count: {len(entries)}")

# ------------------------------
# Preview a few
# ------------------------------
print("\n📋 Sample entries:")
for e in entries[:5]:
    print(f"• {e['source']}: {e['title']} ({e['published']})")

print("\n✅ Section 3B complete — entries ready for summarization.")

```

    🚀 Section 3B starting...


    ✅ White House OSTP Blog: 0 entries fetched.

    


    ✅ NSF Science Matters News: 0 entries fetched.


    ✅ NIH Extramural Nexus: 0 entries fetched.


    ✅ DOE Office of Science News: 0 entries fetched.


    ✅ The Scholarly Kitchen: 10 entries fetched.


    ✅ SPARC Open Access News: 10 entries fetched.


    ✅ Research Data Alliance Blog: 0 entries fetched.


    ✅ OpenAIRE Blog: 0 entries fetched.


    ✅ CODATA Blog: 9 entries fetched.


    ✅ JCU Sci Policy: 10 entries fetched.


    ✅ Journ Sci Policy: 10 entries fetched.
    ✅ Sci4All: 10 entries fetched.


    ✅ PLOS Sci Policy: 0 entries fetched.
    📚 Total entries collected so far: 59
    🔍 Fetching supplemental results from SERPAPI (Google News)...


    ✅ SERPAPI results added.
    🧹 Deduplicated. Final entry count: 69
    
    📋 Sample entries:
    • The Scholarly Kitchen: Five Tips for Hosting a Sustainable Event (2025-10-14)
    • The Scholarly Kitchen: Welcoming a New Chef in the Kitchen and Saying Thanks to a Few Departing Chefs (2025-10-14)
    • The Scholarly Kitchen: Three Years After the Launch of ChatGPT, Do We Know Where This Is Heading? (2025-10-13)
    • The Scholarly Kitchen: SSP’s Generations Fund Crosses the Finish Line (2025-10-10)
    • The Scholarly Kitchen: Guest Post — The Economics of AI in Academic Research (2025-10-09)
    
    ✅ Section 3B complete — entries ready for summarization.



```python
# ===========================================================
# 🗞️ SECTION 3C: RSS FEED COLLECTION (with Date Filter)
# ===========================================================
# Purpose:
#   • Collects posts from trusted sources (see SOURCES in 3A)
#   • Filters to include only items published within the last `days_back` days
#   • Returns a structured list for summarization
#
# Notes:
#   - Default = last 7 days, adjustable by changing `days_back`
#   - Feeds missing publication dates are skipped (to avoid false positives)
#   - Each entry includes: title, link, summary, source, published_date
# -----------------------------------------------------------

from datetime import datetime, timedelta
import feedparser

def collect_sources(days_back=7):
    """
    Pull top posts from each RSS source published within the last `days_back` days.
    Returns list of dicts with title, link, summary, and source.
    """
    entries = []
    cutoff_date = datetime.now() - timedelta(days=days_back)
    print(f"🗞️ Collecting RSS feed updates (last {days_back} days)...")

    for src in SOURCES:
        print(f"→ Fetching {src['name']} ...")
        try:
            feed = feedparser.parse(src["url"])
            for entry in feed.entries[:10]:  # grab up to 10, then filter
                # Try to get published date
                published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
                if not published_parsed:
                    continue  # skip if no date

                published_date = datetime(*published_parsed[:6])
                if published_date < cutoff_date:
                    continue  # skip older entries

                entries.append({
                    "source": src["name"],
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": published_date.strftime("%Y-%m-%d"),
                })
        except Exception as e:
            print(f"⚠️ Failed to parse {src['name']}: {e}")

    print(f"✅ RSS feed collection complete — {len(entries)} entries found within {days_back} days.\n")
    return entries

print("✅ Section 3B loaded: RSS collector ready.")

```

    ✅ Section 3B loaded: RSS collector ready.



```python
# ===========================================================
# 🔍 SECTION 3D: SERPAPI SEARCH (Past Week Only)
# ===========================================================
# Purpose:
#   • Runs Google searches via SERPAPI for open data / open science policy updates
#   • Limits results to the past week using tbs=qdr:w
#   • Returns structured list of recent search hits
#
# Notes:
#   - Respects free-tier (100 searches/month)
#   - Each query retrieves up to 3 results
#   - Works seamlessly with `collect_sources()` from Section 3B
# -----------------------------------------------------------

import requests
import time

# --- Keyword search queries (tuned for policy updates) ---
SEARCH_QUERIES = [
    "open science policy site:whitehouse.gov OR site:ostp.gov",
    "research data sharing policy site:.gov",
    "federal open data initiative",
    "open access mandate university research",
    "data management plan compliance US federal agency",
    "FAIR data principles higher education US",
    "open research infrastructure policy America",
    "OSTP Nelson memo implementation",
    "cost of research",
    "FAIR F&A",
    "indirect costs",
    "open access publishing",
]

def collect_serpapi_results():
    """
    Run SERPAPI searches (past week only).
    Only executes if SERPAPI_KEY and USE_SERPAPI are set.
    """
    results = []
    if not USE_SERPAPI:
        print("⚙️ SERPAPI disabled in config — skipping web search.\n")
        return results
    if not SERPAPI_KEY:
        print("❌ SERPAPI_KEY not provided — skipping web search.\n")
        return results

    print("🔎 Running SERPAPI keyword searches (past week)...")

    for query in SEARCH_QUERIES:
        try:
            print(f"→ Searching: {query}")
            url = f"https://serpapi.com/search.json?q={query}&engine=google&api_key={SERPAPI_KEY}&num=3&tbs=qdr:w"
            resp = requests.get(url)

            if resp.status_code != 200:
                print(f"⚠️ SERPAPI returned status {resp.status_code} for query '{query}'")
                continue

            data = resp.json()
            organic_results = data.get("organic_results", [])[:3]

            for item in organic_results:
                results.append({
                    "source": "SERPAPI Google Search",
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "summary": item.get("snippet", ""),
                    "published": "Past week (SERPAPI)",
                })

            time.sleep(2)  # prevent free-tier rate-limit errors

        except Exception as e:
            print(f"⚠️ SERPAPI query failed for '{query}': {e}")

    print(f"✅ SERPAPI collection complete — {len(results)} results gathered.\n")
    return results

serpapi_results = collect_serpapi_results()

```

    🔎 Running SERPAPI keyword searches (past week)...
    → Searching: open science policy site:whitehouse.gov OR site:ostp.gov


    → Searching: research data sharing policy site:.gov


    → Searching: federal open data initiative


    → Searching: open access mandate university research


    → Searching: data management plan compliance US federal agency


    → Searching: FAIR data principles higher education US


    → Searching: open research infrastructure policy America


    → Searching: OSTP Nelson memo implementation


    → Searching: cost of research


    → Searching: FAIR F&A


    → Searching: indirect costs


    → Searching: open access publishing


    ✅ SERPAPI collection complete — 32 results gathered.
    



```python
# ===========================================================
# 3E. TOKEN BUDGET ESTIMATION
# ===========================================================
def estimate_token_usage(entries, avg_chars_per_token=4, tokens_per_summary=500, token_budget=TOKEN_BUDGET):
    total_chars = sum(len(e.get("summary", "")) for e in entries)
    estimated_input_tokens = total_chars // avg_chars_per_token
    estimated_output_tokens = len(entries) * tokens_per_summary
    total_estimated = estimated_input_tokens + estimated_output_tokens

    print("\n🧮 TOKEN BUDGET ESTIMATE")
    print(f"  Input text: ~{estimated_input_tokens:,} tokens")
    print(f"  Summaries:  ~{estimated_output_tokens:,} tokens")
    print(f"  Total est.: ~{total_estimated:,} tokens")
    print(f"  Budget cap: {token_budget:,} tokens")

    if total_estimated > token_budget:
        print("⚠️ WARNING: Estimated usage exceeds token budget! Truncating entries.")
        entries = entries[:max(1, token_budget // tokens_per_summary)]
        print(f"✅ Truncated list to {len(entries)} entries.\n")
    else:
        print("✅ Within safe token budget.\n")

    return entries

print("✅ Section 3D loaded: Token estimation ready.")

```

    ✅ Section 3D loaded: Token estimation ready.



```python
# ===========================================================
# 3F. RUN DATA COLLECTION PIPELINE
# ===========================================================
def gather_all_sources():
    start = time.time()
    print("\n🚀 Starting data collection pipeline...\n")

    rss_entries = collect_sources()
    print(f"🕒 RSS collection done in {time.time() - start:.2f}s.\n")

    serp_entries = collect_serpapi_results()
    print(f"🕒 SERPAPI search done in {time.time() - start:.2f}s.\n")

    all_entries = rss_entries + serp_entries
    print(f"📦 Combined {len(all_entries)} total entries.\n")

    all_entries = estimate_token_usage(all_entries, token_budget=TOKEN_BUDGET)
    print(f"🏁 Total runtime: {time.time() - start:.2f}s\n")

    return all_entries

print("✅ Section 3E loaded: Ready to execute full pipeline.")

```

    ✅ Section 3E loaded: Ready to execute full pipeline.



```python
# ===========================================================
# 3G. MANUAL EXECUTION
# ===========================================================
print("\n=== RUNNING SECTION 3 ===\n")
entries = gather_all_sources()
print(f"\n✅ Done! Gathered {len(entries)} entries total.\n")

```

    
    === RUNNING SECTION 3 ===
    
    
    🚀 Starting data collection pipeline...
    
    🗞️ Collecting RSS feed updates (last 7 days)...
    → Fetching White House OSTP Blog ...
    → Fetching NSF Science Matters News ...


    → Fetching NIH Extramural Nexus ...


    → Fetching DOE Office of Science News ...
    → Fetching The Scholarly Kitchen ...


    → Fetching SPARC Open Access News ...
    → Fetching Research Data Alliance Blog ...


    → Fetching OpenAIRE Blog ...


    → Fetching CODATA Blog ...


    → Fetching JCU Sci Policy ...


    → Fetching Journ Sci Policy ...


    → Fetching Sci4All ...
    → Fetching PLOS Sci Policy ...


    ✅ RSS feed collection complete — 9 entries found within 7 days.
    
    🕒 RSS collection done in 7.96s.
    
    🔎 Running SERPAPI keyword searches (past week)...
    → Searching: open science policy site:whitehouse.gov OR site:ostp.gov


    → Searching: research data sharing policy site:.gov


    → Searching: federal open data initiative


    → Searching: open access mandate university research


    → Searching: data management plan compliance US federal agency


    → Searching: FAIR data principles higher education US


    → Searching: open research infrastructure policy America


    → Searching: OSTP Nelson memo implementation


    → Searching: cost of research


    → Searching: FAIR F&A


    → Searching: indirect costs


    → Searching: open access publishing


    ✅ SERPAPI collection complete — 32 results gathered.
    
    🕒 SERPAPI search done in 33.24s.
    
    📦 Combined 41 total entries.
    
    
    🧮 TOKEN BUDGET ESTIMATE
      Input text: ~3,020 tokens
      Summaries:  ~20,500 tokens
      Total est.: ~23,520 tokens
      Budget cap: 20,000 tokens
    ⚠️ WARNING: Estimated usage exceeds token budget! Truncating entries.
    ✅ Truncated list to 40 entries.
    
    🏁 Total runtime: 33.24s
    
    
    ✅ Done! Gathered 40 entries total.
    



```python
# ===========================================================
# 🧠 SECTION 4: Summaries + Meta-Summary WITH NUMBERED REFERENCES
# ===========================================================
# - Produces meta-summary bullets and deterministically maps each bullet
#   to supporting sources (title + numbered reference) drawn from the collected entries.
# - Only includes numbered references (no inline links).
# - Output sections:
#     1. META-SUMMARY WITH NUMBERED REFERENCES
#     2. DETAILED SUMMARIES (with numbered references, no links)
#     3. REFERENCES (unique supporting sources)
# -----------------------------------------------------------

import re
import time
import unicodedata
from collections import defaultdict, Counter
from datetime import datetime
import openai

client = openai.OpenAI(api_key=OPENAI_API_KEY)  # ✅ uses your existing API key variable

# Config (will use globals if set)
MODEL = globals().get("MODEL_NAME", "gpt-3.5-turbo")
PER_SUMMARY_MAX_TOKENS = globals().get("PER_SUMMARY_MAX_TOKENS", 400)
SUMMARY_PAUSE = globals().get("SUMMARY_PAUSE", 0.8)
META_MAX_TOKENS = 400
USE_AI_FOR_INDIVIDUAL_SUMMARIES = True
SAVE_TO_FILE = True

_STOPWORDS = {
    "the","and","for","that","with","from","this","which","their","have","has","are","was",
    "were","will","would","could","should","about","within","between","among","these","those",
    "such","also","not","new","use","used","using","may","can","us","our","more","most","over"
}

def _normalize_text(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKC", str(t))
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _strip_source_phrases(text):
    """
    Safely strip phrases like 'The recent update from XYZ:', 'According to ABC:', etc.
    Only removes well-formed, prefatory attribution lines.
    """
    if not text:
        return text

    # Match patterns like "The recent update from XYZ:" or "According to ABC,"
    pattern = re.compile(
        r'^\s*(?:The\s+)?(?:recent\s+)?(?:update|report|post|article|news)?\s*'
        r'(?:from|by|via)?\s*([A-Z][A-Za-z\s&,\-.]{1,60})[:,\-–—]\s+',
        re.IGNORECASE
    )

    match = pattern.match(text)
    if match:
        return text[match.end():].strip()

    return text

def _tokenize_for_matching(t):
    t = _normalize_text(t).lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    words = [w for w in t.split() if len(w) >= 4 and w not in _STOPWORDS]
    return words

def _ai_summarize_entry(text, source, link):
    text = _normalize_text(text)
    if not text:
        return "(No text available.)"
    cli = globals().get("client", None)
    if not cli:
        return f"[OFFLINE] {source}: {text[:280]}..."
    prompt = (
        f"Summarize this recent update from {source} about U.S. open data or open science policy. "
        "Only use facts present in the text. DO NOT MAKE UP facts, dates, or sources.\n\n"
        f"Source link: {link}\n\nText:\n{text[:4000]}"
    )
    try:
        resp = cli.chat.completions.create(
            model=MODEL,
            messages=[{"role":"user","content":prompt}],
            max_tokens=PER_SUMMARY_MAX_TOKENS,
        )
        s = resp.choices[0].message.content.strip()
        time.sleep(SUMMARY_PAUSE)
        return s
    except Exception as e:
        print(f"⚠️ AI summarization failed for source {source}: {e}")
        return f"[OFFLINE] {source}: {text[:280]}..."

def _ai_meta_bullets(summaries_list):
    cli = globals().get("client", None)
    if not cli:
        return ""
    prompt = (
          "You are a concise policy analyst. From the following short summaries of recent updates "
          "about U.S. open data and open science policy, produce exactly FIVE numbered, concise key takeaways. "
          "Each takeaway should be 1–2 sentences and focus on distinct insights — avoid overlap or repetition. "
          "Do not mention or reference any sources (e.g., 'according to...'). "
          "Use only the information explicitly present in the summaries. "
          "Do not infer or add new information. "
          "Return only the 5 numbered bullets, with no extra text.\n\n"
          "Summaries:\n\n" + "\n\n".join(summaries_list)
    )
    try:
        resp = cli.chat.completions.create(
            model=MODEL,
            messages=[{"role":"user","content":prompt}],
            max_tokens=META_MAX_TOKENS,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("⚠️ Meta-summary API call failed:", e)
        return ""

def _parse_numbered_bullets(text):
    if not text:
        return []
    lines = text.splitlines()
    bullets = []
    pattern = re.compile(r'^\s*(?:\d+\.)\s*(.+)$')
    for ln in lines:
        m = pattern.match(ln)
        if m:
            bullets.append(m.group(1).strip())
    if bullets:
        return bullets
    for ln in lines:
        ln2 = ln.strip()
        if ln2.startswith('- ') or ln2.startswith('* '):
            bullets.append(ln2[2:].strip())
    if not bullets:
        parts = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        return parts[:5]
    return bullets[:5]

def _match_bullet_to_sources(bullet, items, top_k=5):
    btoks = set(_tokenize_for_matching(bullet))
    scores = []
    for it in items:
        title = it.get("title","")
        summary = it.get("summary","")
        source = it.get("source","")
        candidate_text = " ".join([title, summary, source])
        ctoks = set(_tokenize_for_matching(candidate_text))
        overlap = btoks & ctoks
        score = len(overlap)
        title_toks = set(_tokenize_for_matching(title))
        score += len(btoks & title_toks)
        scores.append((score, it))
    scored = [it for score,it in sorted(scores, key=lambda x: x[0], reverse=True) if score>0]
    return scored[:top_k]

def generate_report_with_refs(entries, use_ai_for_individual=USE_AI_FOR_INDIVIDUAL_SUMMARIES):
    if not entries:
        print("❌ No entries provided to generate_report_with_refs().")
        return "", {}

    t0 = time.time()
    print(f"🧠 Generating summaries for {len(entries)} entries...")

    items = []
    for e in entries:
        title = e.get("title","(no title)")
        link = e.get("link","")
        source = e.get("source","")
        raw_text = e.get("summary","") or e.get("content","") or ""
        summary = _ai_summarize_entry(raw_text, source, link) if use_ai_for_individual else raw_text or "(no text)"
        summary = _strip_source_phrases(summary)
        items.append({
            "title": _normalize_text(title),
            "link": _normalize_text(link),
            "source": _normalize_text(source),
            "summary": _normalize_text(summary),
            "published": e.get("published","")
        })

    s_texts = [f"{it['title']}: {it['summary']}" for it in items]
    meta_raw = _ai_meta_bullets(s_texts)
    bullets = _parse_numbered_bullets(meta_raw)

    if not bullets:
        print("⚠️ Model did not produce numbered bullets — using heuristic fallback.")
        all_tokens = []
        for it in items:
            all_tokens += _tokenize_for_matching(it['summary'])
        common = [w for w,_ in Counter(all_tokens).most_common(10)]
        bullets = [f"Frequent theme: {w}" for w in common[:5]]

    print(f"🔎 Parsed {len(bullets)} meta bullets. Mapping bullets to supporting sources...")

    bullet_mappings = []
    all_cited = {}
    ref_counter = 1
    ref_numbers = {}

    for b in bullets:
        matched = _match_bullet_to_sources(b, items, top_k=6)
        formatted_nums = []
        for m in matched:
            title = m.get("title","(no title)")
            link = m.get("link","")
            if title not in ref_numbers:
                ref_numbers[title] = ref_counter
                all_cited[ref_counter] = (title, link)
                ref_counter += 1
            formatted_nums.append(f"[{ref_numbers[title]}]")
        bullet_mappings.append((b, formatted_nums))

    # --- Report Construction ---
    timestamp = datetime.now().strftime("%B %d, %Y")
    header = f"OPEN DATA POLICY MONITOR REPORT\nGenerated on {timestamp}\n\n"

    # === META-SUMMARY WITH NUMBERED REFERENCES ===
    header += "============================================================\n"
    header += "🔗 META-SUMMARY WITH NUMBERED REFERENCES\n"
    header += "============================================================\n\n"

    meta_block = ""
    for i,(b,refs) in enumerate(bullet_mappings, start=1):
        ref_str = " ".join(refs) if refs else "(no match)"
        meta_block += f"{i}. {b} {ref_str}\n\n"

   # === DETAILED SUMMARIES ===
    details_block = "\n\n============================================================\n"
    details_block += "📖 DETAILED SUMMARIES (only entries supporting meta-summary bullets)\n"
    details_block += "============================================================\n\n"
    for it in items:
        title = it['title']
        source = it['source']
        link = it['link']
        ref_num = ref_numbers.get(title, None)

        # ✅ Skip entries that don't have a reference number
        if not ref_num:
            continue

        details_block += f"TITLE: {title} [{ref_num}]\nSOURCE: {source}\n\n{it['summary']}\n"
        details_block += "-"*60 + "\n"

    # === REFERENCES (unique supporting sources) ===
    refs_block = "\n============================================================\n"
    refs_block += "📚 REFERENCES (unique supporting sources)\n"
    refs_block += "============================================================\n\n"
    if all_cited:
        for num, (title, link) in all_cited.items():
            if link:
                refs_block += f"{num}. {title} — {link}\n"
            else:
                refs_block += f"{num}. {title}\n"
    else:
        refs_block += "(No sources were matched to bullets.)\n"

    footer = "\n" + "="*60 + "\n"
    runtime = round(time.time() - t0, 2)
    total_in = sum(len(it['summary'])//4 for it in items)
    total_out = sum((len(b)//4) for b in bullets) + 200
    est_cost = round((total_in/1000)*0.01 + (total_out/1000)*0.03, 4)
    footer += f"RUNTIME: {runtime} s\nESTIMATED TOKENS: {total_in + total_out}\nESTIMATED COST (USD): ${est_cost}\n"
    footer += "="*60 + "\n"

    report_text = header + meta_block + details_block + refs_block + footer

    if SAVE_TO_FILE:
        # Detect if running in Colab
        if os.path.exists("/content"):
            save_dir = "/content/open_data_monitor"
        else:
            save_dir = "reports"

        os.makedirs(save_dir, exist_ok=True)
        fname = os.path.join(save_dir, f"open_data_policy_report_{datetime.now().strftime('%Y%m%d')}.md")

        try:
            with open(fname, "w", encoding="utf-8") as fh:
                fh.write(report_text)
            print(f"💾 Report saved to {fname}")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")

    stats = {
        "entries": len(entries),
        "bullets": len(bullets),
        "runtime_s": runtime,
        "estimated_cost_usd": est_cost,
    }
    print("\n✅ Section 4 complete — meta-summary, detailed summaries, and references generated.")
    return report_text, stats

# -------------------- Run now (if entries exist) --------------------
if "entries" in globals() and entries:
    report_text, section4_stats = generate_report_with_refs(
        entries,
        use_ai_for_individual=USE_AI_FOR_INDIVIDUAL_SUMMARIES
    )

    print("\n--- META-SUMMARY PREVIEW ---\n")
    print("\n".join(report_text.splitlines()[:30]))

    # ✅ Save the generated report to the "reports" folder
    import os
    os.makedirs("reports", exist_ok=True)
    output_filename = f"reports/open_data_policy_report_{datetime.now().strftime('%Y-%m-%d')}.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"💾 Report written to {output_filename}")

else:
    print("⚠️ `entries` not found — run Section 3 first.")

```

    🧠 Generating summaries for 40 entries...


    🔎 Parsed 5 meta bullets. Mapping bullets to supporting sources...
    💾 Report saved to reports/open_data_policy_report_20251014.md
    
    ✅ Section 4 complete — meta-summary, detailed summaries, and references generated.
    
    --- META-SUMMARY PREVIEW ---
    
    OPEN DATA POLICY MONITOR REPORT
    Generated on October 14, 2025
    
    ============================================================
    🔗 META-SUMMARY WITH NUMBERED REFERENCES
    ============================================================
    
    1. Open data and open science policies are crucial for safeguarding public access to reliable government data and protecting data integrity in research. [1] [2] [3] [4] [5] [6]
    
    2. The implementation of AI in scholarly publishing has led to advancements in ethical writing tools, AI-driven discovery, and automated peer review, streamlining research workflows. [7] [8] [5] [2] [9] [10]
    
    3. Generative AI tools like ChatGPT have shifted from experimental phases to integration, enhancing research creation and evaluation but leaving long-term impacts uncertain. [7] [8] [11] [12] [5] [9]
    
    4. Initiatives like WorldFAIR+ and CDIF are crucial for promoting data interoperability and collaboration, highlighting the importance of sustainable pathways in research. [13] [6] [14] [8] [4] [5]
    
    5. The involvement of foreign adversaries in exploiting U.S. academic institutions necessitates potential changes in open data and open science policy to protect research and innovation infrastructure. [15] [5] [16] [2] [11] [17]
    
    
    
    ============================================================
    📖 DETAILED SUMMARIES (only entries supporting meta-summary bullets)
    ============================================================
    
    TITLE: Five Tips for Hosting a Sustainable Event [14]
    SOURCE: The Scholarly Kitchen
    
    The recent update from The Scholarly Kitchen discusses five tips for hosting a sustainable event and how event planners are balancing deeper connections with the impact on the planet. It does not mention anything specific about U.S. open data or open science policy.
    ------------------------------------------------------------
    TITLE: Welcoming a New Chef in the Kitchen and Saying Thanks to a Few Departing Chefs [12]
    SOURCE: The Scholarly Kitchen
    💾 Report written to reports/open_data_policy_report_2025-10-14.txt



```python
# ===========================================================
# 📨 SECTION 5: Save
# ===========================================================
# Saves the final report to a date-stamped file, prints, but doees not email yet it
# using Gmail SMTP (requires an App Password, not your normal password).
# -----------------------------------------------------------

import os
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Mailing
EMAIL_SUBJECT = "📊 Open Data Policy Monitor Weekly Report"

def save_and_email_report(report_text):
    """Save the report locally and send it via Gmail."""
    if not report_text:
        print("❌ No report_text found — run Section 4 first.")
        return

    # --- Save the report safely depending on environment ---
    if os.path.exists("/content"):  # Running in Colab
        SAVE_DIR = "/content/open_data_monitor"
    else:  # Running in GitHub Actions or locally
        SAVE_DIR = "reports"

    os.makedirs(SAVE_DIR, exist_ok=True)
    print(f"📂 Using save directory: {SAVE_DIR}")
    print(f"🧭 Current working directory: {os.getcwd()}")

    # Use only Month-Day-Year for both file name and report header
    timestamp = datetime.now().strftime("%B-%d-%Y")       # e.g., October-09-2025
    readable_stamp = datetime.now().strftime("%B %d, %Y")  # e.g., October 09, 2025

    filename = os.path.join(SAVE_DIR, f"open_data_policy_report_{timestamp}.md")

    # Prepend readable timestamp to the top of the report
    header = f"# Open Data Policy Monitor\n🗓️ Generated on {readable_stamp}\n\n"
    full_report = header + report_text

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_report)
        print(f"💾 Report saved successfully:\n   {filename}")
    except Exception as e:
        print(f"⚠️ Could not save report: {e}")

    # Optional: automatically email after saving
    try:
        send_email(filename)
    except Exception as e:
        print(f"📧 Email sending failed: {e}")

    # --- Prepare email ---
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_RECIPIENT
    msg["Subject"] = EMAIL_SUBJECT

    body = (
        f"Attached is the latest Open Data Policy Monitor report.\n\n"
        f"🗓️ Generated on {readable_stamp}\n\n"
        "The full text is also included below.\n\n"
        f"{report_text}"
    )
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # --- Send email via Gmail SMTP ---
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"📨 Email successfully sent to {EMAIL_RECIPIENT}")
    except smtplib.SMTPAuthenticationError:
        print("⚠️ Gmail rejected your login — check your App Password or 2FA settings.")
    except Exception as e:
        print(f"⚠️ Failed to send email: {e}")

# --- Run the function ---
if "report_text" in globals() and report_text:
    print("Report generated but not emailed.")
else:
    print("⚠️ No report_text variable found. Please run Section 4 first.")

```

    Report generated but not emailed.

