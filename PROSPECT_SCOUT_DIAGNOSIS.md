# Prospect Scout Diagnosis: Why No Leads?

## The Problem
You are searching for "HVAC in Phoenix" and getting **0 qualified leads** (or very few).

## Root Causes

### 1. DuckDuckGo (DDGS) is a "Privacy Search"
DDGS is designed to *hide* user intent. It is not an SEO tool. It strips geolocation often.
-   **Impact**: Searching "HVAC" might return national brands (Trane, Carrier) or huge aggregators (Angi, Yelp) instead of local small businesses.
-   **Nova's Filter**: Nova looks for "bad websites" and "manual scheduling". If DDGS returns "Angi.com" or "Carrier Enterprise", Nova correctly scores them as **LOW** (Pass=False) because they are tech-savvy giants, not automation targets.

### 2. Search Query Specificity
Troy is generating queries like: `"HVAC in Phoenix reviews"`.
-   **Result**: This returns Yelp, Google Maps, and TripAdvisor pages.
-   **The Glitch**: The `href` (URL) collected is `yelp.com/...`, NOT the business's actual website.
-   **Nova's Logic**: Nova sees "Yelp" and rejects it because Yelp doesn't need an AI Agent.

### 3. Rate Limiting / Scraper Blocking
Many small business sites block python `requests` headers or have very slow load times.
-   **Impact**: `fetch_homepage_snippet` fails or returns empty text -> Nova sees empty text -> Scores 0.

## Recommendations for Alpha

### Immediate Fix (Code Tweak)
1.  **Relax Nova's Filter**: Lower the passing threshold from `7` to `5`.
2.  **Filter Aggregators**: Explicitly ignore results containing "yelp", "angi", "thumbtack" in `prospect_scout.py` so we don't waste time scoring them.

### Strategic Fix (Better Tooling)
1.  **Google Maps API (Places)**: This is the *gold standard* for local execution.
    -   Switch `prospect_scout.py` to use `google maps` search (costs money but 100x better data).
    -   Query: `Plumbers in Phoenix` -> Returns verified `website_url` field.
2.  **Firecrawl / Exa**: Use a dedicated scraping API (like Exa.ai or Firecrawl) designed for "Find me companies like X".

## Proposed Action Plan
I will patch `prospect_scout.py` right now to:
1.  **Ignore Aggregators** (Yelp, Angi, etc.).
2.  **Lower Score Threshold** to 5.
3.  **Debug Mode**: Print *why* a lead was rejected in the logs so we can see if it's hitting Yelp or just failing to load.
