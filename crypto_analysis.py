import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

df_16 = pd.read_csv(RAW_DIR / "coin_gecko_2022-03-16.csv")
df_17 = pd.read_csv(RAW_DIR / "coin_gecko_2022-03-17.csv")

df = pd.concat([df_16, df_17], ignore_index=True)
df["date"] = pd.to_datetime(df["date"])

clean_df = df.dropna(
    subset=["price", "1h", "24h", "7d", "24h_volume", "mkt_cap"]
).copy()

clean_df = (
    clean_df
    .sort_values(["coin", "date"])
    .drop_duplicates(subset=["coin", "date"], keep="last")
    .reset_index(drop=True)
)

clean_df["previous_price"] = clean_df.groupby("coin")["price"].shift(1)
clean_df["price_change"] = clean_df["price"] - clean_df["previous_price"]
clean_df["price_change_pct"] = (
    (clean_df["price"] - clean_df["previous_price"])
    / clean_df["previous_price"]
) * 100

clean_df["previous_mkt_cap"] = clean_df.groupby("coin")["mkt_cap"].shift(1)
clean_df["mkt_cap_change_pct"] = (
    (clean_df["mkt_cap"] - clean_df["previous_mkt_cap"])
    / clean_df["previous_mkt_cap"]
) * 100

def classify_performance(value):
    if pd.isna(value):
        return "No Previous Data"
    if value > 0:
        return "Gainer"
    if value < 0:
        return "Loser"
    return "No Change"

clean_df["performance"] = clean_df["price_change_pct"].apply(
    classify_performance
)

dod_df = clean_df[clean_df["date"] == pd.Timestamp("2022-03-17")].copy()

dashboard_df = dod_df[
    ["coin", "symbol", "date", "price", "previous_price",
     "price_change", "price_change_pct", "1h", "24h", "7d",
     "24h_volume", "mkt_cap", "mkt_cap_change_pct", "performance"]
].copy()

kpi_summary = pd.DataFrame({
    "KPI": [
        "Total Market Cap", "Total 24h Volume",
        "Average 24h Change", "Gainers", "Losers", "No Change"
    ],
    "Value": [
        dod_df["mkt_cap"].sum(),
        dod_df["24h_volume"].sum(),
        dod_df["24h"].mean(),
        (dod_df["price_change_pct"] > 0).sum(),
        (dod_df["price_change_pct"] < 0).sum(),
        (dod_df["price_change_pct"] == 0).sum()
    ]
})

clean_df.to_csv(PROCESSED_DIR / "combined_coin.csv", index=False)

with pd.ExcelWriter(PROCESSED_DIR / "crypto_analysis.xlsx", engine="openpyxl") as writer:
    clean_df.to_excel(writer, sheet_name="Clean_Data", index=False)
    dod_df.to_excel(writer, sheet_name="Day_Over_Day", index=False)

with pd.ExcelWriter(PROCESSED_DIR / "crypto_dashboard_data.xlsx", engine="openpyxl") as writer:
    clean_df.to_excel(writer, sheet_name="Clean_Data", index=False)
    dashboard_df.to_excel(writer, sheet_name="Dashboard_Data", index=False)
    kpi_summary.to_excel(writer, sheet_name="KPI_Summary", index=False)

print("Analysis completed.")
print("Raw records:", len(df))
print("Clean records:", len(clean_df))
print("March 17 records:", len(dod_df))
