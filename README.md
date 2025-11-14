# Open Data / Science Policy Monitor — U.S. Academic & Government Updates

### Overview
This project automatically searches for, summarizes, and reports on recent (past 7 days) developments in **U.S. open data and science policy**, focusing on academic and federal agency activity.

It:
1. Gathers recent web articles and policy news from:
   a. Queries of RSS feeds (e.g., NIH, NSF, OSTP)
   b. Broad Google searches of science news sites (via SERPAPI)  
   c. General Google search for keywords (via SERPAPI)    
3. Summarizes findings via OpenAI GPT models with: 
   a. Explicit instruction: *“Do not fabricate or infer connections.”*
   b. Source citation with URL for human verification
4. Generates a report containing:  
   a. Meta-summary highlighting key trends
   b. Individual content summaries  
5. Saves the report in /reports and emails the TXT automatically every Sunday

---

### Runtime
| Section | Time | Description |
|----------|------|-------------|
| Data collection | ~10–20s | 20 entries typical |
| Summarization | ~2–4 min | Depends on entry count |
| Report saving / email | <10s | Markdown + notification |
| **Total** | **2–5 min** | Typical end-to-end run |

---

### Cost Estimates (OpenAI API)
Typical run (20 summaries + meta-summary):  
• ~6,000–8,000 input tokens  
• ~2,000–3,000 output tokens  
→ ~$0.02–$0.05 using `gpt-4o-mini`

---

### Configuration Notes
1. **API Keys:**  
   Define `OPENAI_API_KEY`, `SERPAPI_KEY`, and Gmail credentials in Section 2.  

2. **Token Budget:**  
   `MAX_TOKENS_BUDGET = 12000` (adjust for truncation or cost).  

3. **Custom Sources:**  
   Edit the `search_queries` list in Section 3 to monitor new topics or agencies.

---

### Troubleshooting
- `name 'client' is not defined` → rerun Section 2  
- API quota errors → check OpenAI billing  
- Gmail auth errors → verify app password or use Gmail API  

---

### Scheduling
Run weekly via:
- GitHub Actions 


