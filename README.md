# FOLU Social Listening Dashboard

Static dashboard analisis sentimen dan social listening untuk diskursus **FOLU Talks / FOLU Net Sink 2030** lintas Instagram, YouTube, TikTok, dan web/media.

## Outputs

- `index.html` — dashboard static deploy-ready.
- `data/folu_social_listening_report.xlsx` — Excel report dengan sheet posts, comments, summaries, topics, risks.
- `data/folu_social_comments_sentiment.csv` — komentar sosial dengan sentiment/topic/risk.
- `data/folu_posts_master.csv` — metadata post/video/reel lintas platform.
- `data/dashboard_data.json` — payload ringkas untuk dashboard.

## Current dataset snapshot

Generated at: see `data/dashboard_data.json`.

Includes:

- Instagram comments from Kemenhut FOLU Talks scrape.
- YouTube comments from Kemenhut FOLU Talks streams scrape.
- TikTok FOLU/FOLU Net Sink posts and comments scrape.
- Website/media discourse excerpts as context, separated from public social comments.

## Method notes

- Sentiment uses transparent rule-based Indonesian/English lexicon for auditability.
- Topic clusters and risk flags use keyword rules, not black-box model outputs.
- Public export anonymizes comment authors as hashes.
- Scraping status is disclosed in the dashboard. For TikTok, BYOB discovery worked; Obscura was attempted but returned blank/eval-null, so extractor/API/session fallback was used.

## Local verification

```bash
python build_dashboard.py
python -m http.server 4173
# open http://localhost:4173
```

## Deploy

This is a static site and can be deployed directly to Vercel.
