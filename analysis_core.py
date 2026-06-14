import pandas as pd
import numpy as np

DATA_FILE = "HHS_UAC_Data.csv"


def load_raw_data(path: str = DATA_FILE) -> pd.DataFrame:
    df = pd.read_csv(path)

    rename_map = {
        "Date": "date",
        "Children apprehended and placed in CBP custody*": "cbp_intake",
        "Children in CBP custody": "cbp_load",
        "Children transferred out of CBP custody": "cbp_to_hhs_transfers",
        "Children in HHS Care": "hhs_load",
        "Children discharged from HHS Care": "hhs_discharges",
    }
    df = df.rename(columns=rename_map)

    # Robust date parsing
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Remove rows where date could not be parsed
    df = df.dropna(subset=["date"]).copy()

    numeric_cols = [
        "cbp_intake",
        "cbp_load",
        "cbp_to_hhs_transfers",
        "hhs_load",
        "hhs_discharges",
    ]

    for col in numeric_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values("date").reset_index(drop=True)
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df["weekday"] = df["date"].dt.day_name()
    df["month"] = df["date"].dt.to_period("M").astype(str)

    # Use nullable integer type to avoid NA conversion crash
    iso_calendar = df["date"].dt.isocalendar()
    df["week"] = iso_calendar.week.astype("Int64")

    df["is_weekend"] = df["weekday"].isin(["Saturday", "Sunday"])
    return df


def safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.mask(denominator == 0)
    return numerator.div(denominator)


def compute_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df["transfer_efficiency"] = safe_ratio(
        df["cbp_to_hhs_transfers"],
        df["cbp_load"]
    )

    df["discharge_effectiveness"] = safe_ratio(
        df["hhs_discharges"],
        df["hhs_load"]
    )

    df["pipeline_throughput_daily"] = safe_ratio(
        df["hhs_discharges"],
        df["cbp_intake"]
    )

    df["net_cbp"] = df["cbp_intake"] - df["cbp_to_hhs_transfers"]
    df["net_hhs"] = df["cbp_to_hhs_transfers"] - df["hhs_discharges"]

    df["backlog_accumulation_rate"] = (
        df["net_hhs"].rolling(window=7, min_periods=1).mean()
    )

    # Optional trend helpers
    df["transfer_efficiency_7d"] = df["transfer_efficiency"].rolling(7, min_periods=1).mean()
    df["discharge_effectiveness_7d"] = df["discharge_effectiveness"].rolling(7, min_periods=1).mean()

    return df


def compute_outcome_stability(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.groupby("month", as_index=False)
        .agg(
            discharge_effectiveness_mean=("discharge_effectiveness", "mean"),
            discharge_effectiveness_std=("discharge_effectiveness", "std"),
            hhs_discharges_mean=("hhs_discharges", "mean"),
            hhs_discharges_std=("hhs_discharges", "std"),
        )
    )

    monthly["discharge_effectiveness_std"] = monthly["discharge_effectiveness_std"].fillna(0)
    monthly["hhs_discharges_std"] = monthly["hhs_discharges_std"].fillna(0)

    monthly["outcome_stability_score"] = 1 - (
        monthly["discharge_effectiveness_std"] /
        monthly["discharge_effectiveness_mean"].replace(0, np.nan)
    )

    monthly["outcome_stability_score"] = (
        monthly["outcome_stability_score"]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
        .clip(0, 1)
    )

    return monthly


def compute_overall_kpis(df: pd.DataFrame) -> dict:
    total_transfers = df["cbp_to_hhs_transfers"].sum()
    total_cbp_load = df["cbp_load"].sum()
    total_discharges = df["hhs_discharges"].sum()
    total_hhs_load = df["hhs_load"].sum()
    total_intake = df["cbp_intake"].sum()

    transfer_efficiency_ratio = (
        total_transfers / total_cbp_load if total_cbp_load != 0 else np.nan
    )
    discharge_effectiveness_index = (
        total_discharges / total_hhs_load if total_hhs_load != 0 else np.nan
    )
    pipeline_throughput = (
        total_discharges / total_intake if total_intake != 0 else np.nan
    )

    backlog_accumulation_rate = df["backlog_accumulation_rate"].mean()

    return {
        "transfer_efficiency_ratio": transfer_efficiency_ratio,
        "discharge_effectiveness_index": discharge_effectiveness_index,
        "pipeline_throughput": pipeline_throughput,
        "backlog_accumulation_rate": backlog_accumulation_rate,
    }


def compute_weekday_analysis(df: pd.DataFrame) -> pd.DataFrame:
    weekday_order = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]

    weekday_summary = (
        df.groupby("weekday", as_index=False)
        .agg(
            avg_transfer_efficiency=("transfer_efficiency", "mean"),
            avg_discharge_effectiveness=("discharge_effectiveness", "mean"),
            avg_net_hhs=("net_hhs", "mean"),
        )
    )

    weekday_summary["weekday"] = pd.Categorical(
        weekday_summary["weekday"],
        categories=weekday_order,
        ordered=True
    )
    weekday_summary = weekday_summary.sort_values("weekday")
    return weekday_summary


def prepare_data(path: str = DATA_FILE):
    df = load_raw_data(path)
    df = add_time_features(df)
    df = compute_daily_metrics(df)
    monthly_outcome = compute_outcome_stability(df)
    weekday_summary = compute_weekday_analysis(df)
    return df, monthly_outcome, weekday_summary


if __name__ == "__main__":
    df_all, monthly_outcome_all, weekday_summary_all = prepare_data()
    print(df_all.head())
    print(monthly_outcome_all.head())
    print(weekday_summary_all.head())