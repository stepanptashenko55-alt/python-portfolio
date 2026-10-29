# Sales Report Automation

Turns a raw sales export (CSV from a CRM, shop or POS) into a ready-to-send Excel report in one command.
What usually takes an hour of manual work in Excel now takes a second.

## What the report contains
| Sheet | Content |
|---|---|
| Summary | Total revenue, orders, units, average order value, best product, best region |
| By month | Orders and revenue per month + line chart |
| By product | Units and revenue per product + bar chart |
| By region | Revenue per region per month (pivot table) |
| Raw data | Cleaned source data with a calculated revenue column |

All sheets have styled headers, frozen header rows, auto column widths and number formatting.

## Usage
```bash
pip install -r requirements.txt
python generate_sample.py                     # creates demo data in sample_data/sales.csv
python report.py sample_data/sales.csv --output sales_report.xlsx
```

Input CSV columns: `date, product, region, quantity, unit_price`.
Missing columns are reported with a clear error; empty rows are skipped.

## Possible extensions
Scheduled runs (daily/weekly), sending the report by email or Telegram, reading from Google Sheets
or a database, PDF export, custom KPIs per client.
