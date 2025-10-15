# Open Data Policy Monitor — U.S. Academic & Government Sources

### Overview
This project automatically searches for, summarizes, and reports on recent (past 7 days) developments in **U.S. open data and open science policy**, focusing on academic and federal agency activity.

It:
1. Gathers recent web articles and policy news using SERPAPI.  
2. Queries structured RSS feeds (e.g., NIH, NSF, OSTP).  
3. Summarizes findings via OpenAI GPT models.  
4. Generates a report containing:  
   - Individual content summaries  
   - A meta-summary highlighting key trends  
   - Explicit instruction: *“Do not fabricate or infer connections.”*  
5. Saves the report in /reports
6. Emails the report automatically every Sunday

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


