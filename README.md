# Website Intelligence — AI Website Analysis & SEO Audit API

Website Intelligence is a FastAPI app that answers one question: what does this website actually say, and what should you do next? Paste a public URL, and the service extracts the real page content, sends it to an LLM, and returns a structured five-section business report. This README covers setup, the API, providers, and the model research behind the recommendation.

## What it does

- **Competitor vs your brand** — brand overview, category, services, at least three suggested competitors, strengths, gaps, and positioning opportunities.
- **Top 5 target search queries** — realistic queries for Google, Facebook, Instagram, LinkedIn and X, tagged with intent and audience. No invented search volumes.
- **SEO improvements** — primary, secondary and long-tail keywords, a rewritten SEO title, a human-friendly meta description, and supporting content ideas.
- **Top 5 services** — identified from the site's own copy, each with industry, customer, and benefit. Inferred items are labelled.
- **Target audience** — primary and secondary audiences, industries, business types, customer profiles, needs, and recommended marketing segments.

## Run it locally

You need Python 3.11+ or Docker. A Python 3.12 virtual environment was installed with uv, and the validation tests pass.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and enter at least one real provider API key.
uvicorn app.main:app --host 127.0.0.1 --port 4000
```

Open http://localhost:4000 or http://localhost:4000/docs.

With Docker: `docker build -t website-intelligence .` then `docker run --env-file .env -p 4000:4000 website-intelligence`.

```powershell
Invoke-RestMethod http://localhost:4000/link-analysis -Method Post -ContentType application/json -Body '{"url":"https://example.com"}'
python -m pytest -q
```

## Live sample request & response

Recorded on November 17, 2026 against https://www.python.org via the configured Groq provider (`openai/gpt-oss-120b`). The full response is committed as [`sample-response.json`](sample-response.json); an abridged excerpt:

```bash
curl -X POST http://localhost:4000/link-analysis \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.python.org"}'
```

```json
{
  "success": true,
  "website": "https://www.python.org",
  "brand": { "name": "Python", "category": "Programming Language / Software Development" },
  "analysis": {
    "competitor_analysis": { "competitors": ["JavaScript (unverified AI suggestion)", "Java (unverified AI suggestion)", "Ruby (unverified AI suggestion)"] },
    "target_search_queries": [ { "query": "download Python latest version", "platforms": ["Google"], "intent": "transactional", "business_relevance": "high" } ],
    "seo_improvements": { "primary_keyword": "Python programming language", "recommended_title": "Python – Download, Learn, and Build with the Leading Programming Language" },
    "top_services": [ { "name": "Web Development Frameworks", "evidence": "\"Web Development : Django , Pyramid , Bottle , Tornado , Flask , Litestar , FastAPI\"" } ],
    "target_audience": { "primary_audience": "Developers and programmers ranging from beginners to experienced professionals" }
  },
  "technical_seo": { "title": "Welcome to Python.org", "images_without_alt": 0, "structured_data": true, "issues": ["Use one descriptive H1.", "Review canonical URL configuration."] },
  "llm": { "provider": "groq", "model": "openai/gpt-oss-120b", "fallbacks": [] }
}
```

Service entries quote the page's own copy in their `evidence` field; competitors are labelled "unverified AI suggestion"; no search volumes are invented — the response shows none.

## Demo & proof

- `python -m pytest -q` → **8 passed** (see [`docs/pytest-output.txt`](docs/pytest-output.txt)).
- `GET /health` shows which providers are configured without exposing keys: `{"status":"ok","configured_providers":["groq"]}`.
- `POST /link-analysis` ran end-to-end in ~4.8s and returned the validated response above.
- Reported LLM output passed `Analysis`'s Pydantic validation with no retries or fallbacks.
- Demo UI screenshot of the five-section report: [`docs/demo-report.jpg`](docs/demo-report.jpg).
- A 90-second animated walkthrough of the app (opening → paste URL → five answers → `POST /link-analysis`) is included in this workspace at `videos/website-intelligence-demo/renders/video.mp4` (not committed to keep the repo lean).

## Providers and fallback

Configure any or all keys in `.env`. Missing keys are skipped. `PROVIDER_ORDER` controls sequential fallback.

Authentication errors, quota limits, timeouts, malformed JSON, and schema failures all advance to the next provider. If every provider fails, the API returns HTTP 503 with sanitized attempt metadata. Keys stay server-side. No fabricated offline LLM results are returned — if no provider can answer, you get an error, not a made-up report.

Models are configurable because availability varies by account. No credentials were supplied in this workspace, so live benchmarking was not possible here.

## What the response contains

A successful response includes `success`, `website`, `brand`, `analysis`, `technical_seo`, and `llm` provider/model/fallback metadata. Inside `analysis` you get `competitor_analysis`, `target_search_queries`, `seo_improvements`, `top_services`, and `target_audience`.

Services carry evidence/inferred fields. Competitors are unverified suggestions, not researched facts. Fewer services or competitors are returned when the evidence is thin — the API never pads results.

## How the extraction works (and its limits)

HTML-only extraction, capped at 2 MB and 24,000 text characters. JavaScript-only sites may be rejected. Redirect destinations are validated. Private or reserved addresses, credentials, and nonstandard ports are blocked.

One honest caveat: DNS validation and the HTTP connection are separate steps. Deploy behind an outbound proxy or firewall that blocks private networks, or DNS-rebinding attacks remain possible. This is a local application. Add authentication, request quotas, and concurrency limits before exposing it publicly.

No Core Web Vitals, crawl coverage, or live ranking claims are made — the technical SEO checks are deterministic and single-page.

## LLM model research and recommendation

Provider documentation consulted on November 17, 2026:

| Provider/model | Pricing source | Structured output | Practical assessment |
|---|---|---|---|
| Google Gemini 2.5 Flash | https://ai.google.dev/gemini-api/docs/pricing | JSON response MIME type | Default for economical extraction; validate account availability |
| OpenAI GPT-4.1 mini | https://developers.openai.com/api/docs/models/gpt-4.1-mini | JSON mode | Balanced fallback; published input/output rates $0.40/$1.60 per million tokens |
| Anthropic Haiku 5.5 | https://platform.claude.com/docs/en/about-claude/pricing | Prompted JSON validated locally | Published short-prompt input/output rates $0.10/$0.50 per million tokens; verify applicable tier |

Recommend Gemini as provisional primary, with GPT-4.1 mini and Anthropic as fallback. This is an engineering choice, not a measured quality winner. Compare provider results against a labelled collection of real websites before crowning a production winner.

Want the short version? Which model wins on cost, speed and accuracy? Nobody knows until you measure — context windows, tiers and prices vary, and this app bounds input well below typical model limits. Groq is an optional fourth OpenAI-compatible provider.

Budget estimate: 6,000 input and 2,000 output tokens costs about $0.0056 on GPT-4.1 mini or $0.0016 on the cited short-prompt Haiku rates, excluding retries. Latency and accuracy have not been benchmarked; allow up to 45 seconds per configured provider. Confirm Gemini pricing for the selected model and billing tier at the linked source before budgeting.

Cost levers, in order of impact: stop on the first validated success rather than paying every provider per request; clean text and bounded input to cut tokens; and add a content-hash cache with explicit expiration before production. No persistent cache is implemented yet.
