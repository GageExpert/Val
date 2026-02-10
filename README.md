# AI-Assisted Valuation

Educational equity research modeling tool (not investment advice). The app pulls SEC XBRL data, normalizes it into a canonical format, forecasts all line items, and produces DCF + comps outputs with sensitivity analysis.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## SEC Notes

The app pulls SEC Company Facts via the public API and caches responses in `.cache/`. A proper User-Agent is required by the SEC.

## Tests

```bash
python -m unittest
```

## Disclaimer

This tool is for educational purposes only and does not constitute investment advice.
