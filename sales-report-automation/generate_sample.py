"""Generate a realistic demo sales CSV so the report can be tried without real data."""

import random
from datetime import date, timedelta

import pandas as pd

PRODUCTS = {"Laptop": 899.0, "Monitor": 229.0, "Keyboard": 59.0, "Mouse": 29.0, "Headphones": 129.0}
REGIONS = ["North", "South", "East", "West"]


def main(rows: int = 600, seed: int = 42) -> None:
    rng = random.Random(seed)
    start = date(2026, 1, 1)
    records = []
    for _ in range(rows):
        product = rng.choice(list(PRODUCTS))
        records.append({
            "date": start + timedelta(days=rng.randint(0, 272)),
            "product": product,
            "region": rng.choice(REGIONS),
            "quantity": rng.randint(1, 5),
            "unit_price": PRODUCTS[product],
        })
    pd.DataFrame(records).sort_values("date").to_csv("sample_data/sales.csv", index=False)
    print(f"Wrote {rows} rows to sample_data/sales.csv")


if __name__ == "__main__":
    main()
