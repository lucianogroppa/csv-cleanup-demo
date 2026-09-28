# CSV cleanup demo

**Synthetic, AI-assisted portfolio demonstration.** All products and values are fictional. This is not paid or client work.

A small product export mixes whitespace, category labels, duplicate SKUs and invalid values. `clean.py` validates and normalizes the rows, writes usable records to `clean.csv`, and sends excluded records with a reason to `review.csv`. The original CSV stays untouched.

## Run

Python 3.10+; no packages to install. From this directory:

```sh
python3 -m unittest -v
python3 clean.py input/products.csv --out rerun
```

The included `output/` was generated with `python3 clean.py input/products.csv --out output`. The sample prints:

```text
4 clean, 6 review; 10 input rows reconciled
```

Open `output/clean.csv` and `output/review.csv` to inspect the result. The CLI requires a **new** output directory and refuses to overwrite an existing one, including the input directory.

## Rules

The exact header is `sku,name,category,price_usd,stock`. SKUs use `SKU-001` style. Surrounding spaces are trimmed; names have repeated whitespace collapsed; categories accept `accessory`/`accessories`, `stationery`, and `home` without regard to case. Prices use a decimal point, at most two decimal places, no currency symbol or grouping, and stock is a nonnegative whole number. Values are USD for demonstration.

Rows are grouped by normalized SKU. For an exact duplicate after normalization, the first row is kept and later copies go to review. If versions of a SKU differ or any version is invalid, **every version** goes to review. Missing SKUs are reviewed individually. Bad CSV columns or field counts stop the run before output is created. Formula-like text is prefixed with an apostrophe in exported CSV cells for spreadsheet safety.

The script holds rows in memory and reports only the first validation error on each row. It is intended for small exports, with no claim of production throughput or business impact.
