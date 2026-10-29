# Web Scraper → Excel / CSV

Python scraper that collects a full product catalog and exports it to a clean, formatted Excel
file and a CSV. Demo target: [books.toscrape.com](https://books.toscrape.com), a sandbox shop made for scraping practice.

## Features
- Automatic pagination (stops when pages run out)
- Retries with backoff on network errors, polite delay between requests
- Extracts title, price, star rating, availability and product URL
- Excel output with styled header, frozen header row, filters and number formatting
- CSV output that opens correctly in Excel (UTF-8 BOM)
- Unit tests on saved HTML, so parsing is checked without hitting the site

## Usage
```bash
pip install -r requirements.txt
python scraper.py --pages 5 --output books.xlsx
```

| Option | Default | Description |
|---|---|---|
| `--pages` | 50 | Maximum number of pages |
| `--output` | products.xlsx | Excel file name (CSV is saved next to it) |
| `--delay` | 1.0 | Seconds between requests |

## Tests
```bash
pytest
```

## Adapting to another site
Change `BASE_URL` and the CSS selectors in `parse_page()`. The same structure works for
e-commerce catalogs, real estate listings, job boards, business directories and price monitoring.
