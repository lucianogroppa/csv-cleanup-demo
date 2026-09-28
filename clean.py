"""Clean a small fictional product export. Python 3.10+, standard library only."""

import argparse
import csv
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

FIELDS = ["sku", "name", "category", "price_usd", "stock"]
CLEAN_FIELDS = FIELDS + ["source_row"]
REVIEW_FIELDS = ["source_row", "reason"] + FIELDS
CATEGORIES = {"accessory": "Accessories", "accessories": "Accessories",
              "stationery": "Stationery", "home": "Home"}


def normalize(raw):
    row = {key: value.strip() for key, value in raw.items()}
    row["sku"] = row["sku"].upper()
    if not re.fullmatch(r"SKU-[A-Z0-9]{3}", row["sku"]):
        raise ValueError("SKU must look like SKU-001")
    row["name"] = " ".join(row["name"].split())
    if not row["name"]:
        raise ValueError("Name is required")
    category = CATEGORIES.get(row["category"].casefold())
    if category is None:
        raise ValueError("Unknown category")
    row["category"] = category
    if not re.fullmatch(r"[0-9]{1,6}(\.[0-9]{1,2})?", row["price_usd"]):
        raise ValueError("Price must be nonnegative USD with at most two decimals")
    row["price_usd"] = f"{Decimal(row['price_usd']):.2f}"
    if not re.fullmatch(r"[0-9]{1,6}", row["stock"]):
        raise ValueError("Stock must be a nonnegative whole number")
    row["stock"] = str(int(row["stock"]))
    return row


def process(path):
    groups = defaultdict(list)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"Expected columns: {', '.join(FIELDS)}")
        for number, raw in enumerate(reader, 2):
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"Record {number}: wrong number of fields")
            try:
                normalized, error = normalize(raw), None
            except ValueError as exc:
                normalized, error = None, str(exc)
            # Missing IDs remain separate; all versions of a present ID are reviewed together.
            key = raw["sku"].strip().upper() or ("missing", number)
            groups[key].append((number, raw, normalized, error))

    clean, review = [], []
    for group in groups.values():
        valid = [item[2] for item in group if item[2] is not None]
        conflict = len(group) > 1 and (len(valid) != len(group) or any(row != valid[0] for row in valid))
        for index, (number, raw, normalized, error) in enumerate(group):
            if conflict:
                reason = "Conflicting SKU; review all versions"
                if error:
                    reason += f"; {error}"
            elif error:
                reason = error
            elif index:
                reason = f"Exact duplicate of row {group[0][0]} after normalization"
            else:
                clean.append({**normalized, "source_row": number})
                continue
            review.append({"source_row": number, "reason": reason, **raw})
    clean.sort(key=lambda row: row["source_row"])
    review.sort(key=lambda row: row["source_row"])
    assert sum(map(len, groups.values())) == len(clean) + len(review)
    return clean, review


def write_csv(path, fields, rows):
    def safe(value):
        value = str(value)
        return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: safe(row[field]) for field in fields} for row in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="New output directory")
    args = parser.parse_args()
    try:
        clean, review = process(args.input)
        args.out.mkdir(parents=True, exist_ok=False)
        write_csv(args.out / "clean.csv", CLEAN_FIELDS, clean)
        write_csv(args.out / "review.csv", REVIEW_FIELDS, review)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(f"{len(clean)} clean, {len(review)} review; {len(clean) + len(review)} input rows reconciled")


if __name__ == "__main__":
    main()
