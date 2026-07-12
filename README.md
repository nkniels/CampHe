# CampHe

> A lightweight Progressive Web App (PWA) to track health campaigns in Cameroon.

![CampHe Banner](./frontend/icon-192.png)

---

## Overview

**CampHe** (Cameroon Health) aggregates active and upcoming health campaigns — vaccinations, awareness drives, free screenings, and humanitarian health interventions — from 10 curated official, media, NGO, and aggregator sources across Cameroon. It is built entirely with **Vanilla HTML/CSS/JS** on the frontend and a **Python scraper** on the backend.

## Features

- 🏥 Aggregates from **10 sources** (government, media, NGO, UN aggregators)
- 📱 **Installable PWA** with offline support via Service Worker
- ⚡ **Real-time skeleton loading** while data fetches
- 🌐 Fully **bilingual-aware** scraping (French & English sources)
- 🤖 **Automated daily CI/CD** via GitHub Actions — no manual updates needed

---

## Project Structure

```
CampHe/
├── frontend/             # PWA files served to users
│   ├── index.html        # App shell
│   ├── styles.css        # Design system (glassmorphism, Cameroon palette)
│   ├── app.js            # Data fetching & rendering logic
│   ├── sw.js             # Service Worker (offline caching)
│   ├── manifest.json     # PWA manifest
│   ├── icon-192.png      # App icon (192x192)
│   ├── icon-512.png      # App icon (512x512)
│   └── data/
│       └── campaigns.json  # Auto-updated by the scraper pipeline
│
├── backend/              # Python scraper pipeline
│   ├── base_scraper.py   # Abstract base class (HTTP, schema, ID generation)
│   ├── sources.py        # 10 source-specific scrapers (one class per site)
│   ├── scraper.py        # Orchestrator: runs all scrapers, deduplicates, saves
│   └── requirements.txt  # Python dependencies
│
└── .github/
    └── workflows/
        └── scraper.yml   # GitHub Actions: daily run + auto-commit
```

---

## Scraping Sources

| Source | Category | Method |
|---|---|---|
| [MINSANTE](https://www.minsante.cm) | Government | HTML |
| [CDNSS-MINSANTE](https://www.cdnss-minsante.cm) | Government | HTML |
| [Cameroon Tribune](https://www.cameroon-tribune.cm) | Media | HTML |
| [Actu Cameroun](https://actucameroun.com/category/sante/) | Media | HTML |
| [CRTV](https://www.crtv.cm) | Media | HTML + keyword filter |
| [WHO Cameroon](https://www.afro.who.int/countries/cameroon) | NGO | HTML |
| [CDC Cameroon](https://www.cdc.gov/global-health/countries/cameroon.html) | NGO | HTML |
| [Intl Medical Corps](https://internationalmedicalcorps.org/country/cameroon/) | NGO | HTML |
| [ReliefWeb](https://reliefweb.int) | Aggregator | **JSON REST API** |
| [CAP-One Health](https://www.cap-onehealth.com) | Aggregator | HTML |

---

## Getting Started

### Frontend

Serve the frontend directory with any static server:

```bash
cd frontend
python -m http.server 8080
# Open http://localhost:8080
```

### Backend Scraper

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run all scrapers
python backend/scraper.py

# Run a single source
python backend/scraper.py --source "ReliefWeb"

# Preview without writing to disk
python backend/scraper.py --dry-run
```

### Tuning Selectors

The HTML scrapers in `backend/sources.py` use best-guess CSS selectors annotated with `TODO` comments. To validate them:

1. Open the `SOURCE_URL` of a scraper in your browser.
2. Right-click a news item → **Inspect**.
3. Find selectors for: article container, title, date, description, link.
4. Update the corresponding `parse()` method.
5. Run `python backend/scraper.py --source "Source Name" --dry-run` to verify.

---

## CI/CD

The GitHub Actions workflow (`.github/workflows/scraper.yml`) runs **daily at 06:00 UTC** and auto-commits any changes to `frontend/data/campaigns.json`. You can also trigger it manually from the **Actions** tab in GitHub with an optional `--source` filter.

---

## License

MIT
