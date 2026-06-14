# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

from analysis_core import prepare_data, compute_overall_kpis

st.set_page_config(
    page_title="Care Transition Efficiency & Placement Analytics",
    layout="wide",
)

@st.cache_data
def load_prepared_data():
    return prepare_data()

df_full, monthly_outcome_full, weekday_summary_full = load_prepared_data()

st.sidebar.title("Filters & Settings")

min_date = df_full["date"].min().date()
max_date = df_full["date"].max().date()

date_range = st.sidebar.date_input(
    "Select date range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date,
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

mask = (
    (df_full["date"] >= pd.to_datetime(start_date)) &
    (df_full["date"] <= pd.to_datetime(end_date))
)
df = df_full.loc[mask].copy()

metric_options = [
    "Transfer Efficiency Ratio",
    "Discharge Effectiveness Index",
    "Pipeline Throughput",
    "Backlog Accumulation Rate",
    "Outcome Stability Score",
]
selected_metrics = st.sidebar.multiselect(
    "Select KPIs to display",
    metric_options,
    default=[
        "Transfer Efficiency Ratio",
        "Discharge Effectiveness Index",
        "Pipeline Throughput",
        "Backlog Accumulation Rate",
    ],
)

st.sidebar.subheader("Thresholds (for alerts)")
transfer_threshold = st.sidebar.slider(
    "Transfer efficiency minimum", 0.0, 1.0, 0.70, 0.01
)
discharge_threshold = st.sidebar.slider(
    "Discharge effectiveness minimum", 0.0, 1.0, 0.03, 0.01
)
backlog_threshold = st.sidebar.number_input(
    "Backlog accumulation max", value=0.0
)

overall_kpis = compute_overall_kpis(df)

monthly_outcome = monthly_outcome_full[
    monthly_outcome_full["month"].isin(df["month"].unique())
].copy()

weekday_summary = (
    df.groupby("weekday", as_index=False)
    .agg(
        avg_transfer_efficiency=("transfer_efficiency", "mean"),
        avg_discharge_effectiveness=("discharge_effectiveness", "mean"),
        avg_net_hhs=("net_hhs", "mean"),
    )
)

weekday_order = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]
weekday_summary["weekday"] = pd.Categorical(
    weekday_summary["weekday"],
    categories=weekday_order,
    ordered=True
)
weekday_summary = weekday_summary.sort_values("weekday")

st.title("Care Transition Efficiency & Placement Outcome Analytics")
st.caption(
    "CBP → HHS → Sponsor pipeline analytics for transfer speed, discharge performance, backlog detection, and outcome stability."
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if "Transfer Efficiency Ratio" in selected_metrics:
        st.metric(
            "Transfer Efficiency Ratio",
            f"{overall_kpis['transfer_efficiency_ratio']:.2f}"
            if pd.notna(overall_kpis["transfer_efficiency_ratio"]) else "NA"
        )

with col2:
    if "Discharge Effectiveness Index" in selected_metrics:
        st.metric(
            "Discharge Effectiveness Index",
            f"{overall_kpis['discharge_effectiveness_index']:.2f}"
            if pd.notna(overall_kpis["discharge_effectiveness_index"]) else "NA"
        )

with col3:
    if "Pipeline Throughput" in selected_metrics:
        st.metric(
            "Pipeline Throughput",
            f"{overall_kpis['pipeline_throughput']:.2f}"
            if pd.notna(overall_kpis["pipeline_throughput"]) else "NA"
        )

with col4:
    if "Backlog Accumulation Rate" in selected_metrics:
        st.metric(
            "Backlog Accumulation Rate",
            f"{overall_kpis['backlog_accumulation_rate']:.2f}"
            if pd.notna(overall_kpis["backlog_accumulation_rate"]) else "NA"
        )

if "Outcome Stability Score" in selected_metrics and not monthly_outcome.empty:
    st.metric(
        "Outcome Stability Score (avg)",
        f"{monthly_outcome['outcome_stability_score'].mean():.2f}"
    )

avg_transfer_eff = df["transfer_efficiency"].mean()
avg_discharge_eff = df["discharge_effectiveness"].mean()
avg_backlog = df["backlog_accumulation_rate"].mean()

if pd.notna(avg_transfer_eff) and avg_transfer_eff < transfer_threshold:
    st.error(
        f"Transfer efficiency ({avg_transfer_eff:.2f}) is below threshold ({transfer_threshold:.2f})."
    )

if pd.notna(avg_discharge_eff) and avg_discharge_eff < discharge_threshold:
    st.warning(
        f"Discharge effectiveness ({avg_discharge_eff:.2f}) is below threshold ({discharge_threshold:.2f})."
    )

if pd.notna(avg_backlog) and avg_backlog > backlog_threshold:
    st.warning(
        f"Backlog accumulation ({avg_backlog:.2f}) exceeds threshold ({backlog_threshold:.2f})."
    )

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Care Pipeline Flow",
    "Efficiency Panels",
    "Bottleneck Detection",
    "Outcome Trends",
    "Weekday Patterns",
])

with tab1:
    st.subheader("Care Pipeline Flow Visualization")

    fig1 = px.line(
        df,
        x="date",
        y=[
            "cbp_intake",
            "cbp_load",
            "cbp_to_hhs_transfers",
            "hhs_load",
            "hhs_discharges",
        ],
        title="Daily Flow Across CBP and HHS Stages",
        labels={"value": "Children count", "variable": "Metric"},
    )
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.subheader("Transfer & Discharge Efficiency")

    c1, c2 = st.columns(2)

    with c1:
        fig2 = px.line(
            df,
            x="date",
            y=["transfer_efficiency", "transfer_efficiency_7d"],
            title="Transfer Efficiency Ratio",
            labels={"value": "Ratio", "variable": "Series"},
        )
        fig2.update_yaxes(range=[0, 1])
        st.plotly_chart(fig2, use_container_width=True)

    with c2:
        fig3 = px.line(
            df,
            x="date",
            y=["discharge_effectiveness", "discharge_effectiveness_7d"],
            title="Discharge Effectiveness",
            labels={"value": "Ratio", "variable": "Series"},
        )
        st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.subheader("Backlog & Delay Identification")

    c1, c2 = st.columns(2)

    with c1:
        fig4 = px.line(
            df,
            x="date",
            y=["net_cbp", "net_hhs"],
            title="Net Flow at CBP and HHS",
            labels={"value": "Net flow", "variable": "Stage"},
        )
        st.plotly_chart(fig4, use_container_width=True)

    with c2:
        fig5 = px.line(
            df,
            x="date",
            y="backlog_accumulation_rate",
            title="Backlog Accumulation Rate (7-day rolling)",
            labels={"backlog_accumulation_rate": "Backlog rate"},
        )
        st.plotly_chart(fig5, use_container_width=True)

    st.write(f"Positive HHS backlog days: {(df['net_hhs'] > 0).sum()}")

with tab4:
    st.subheader("Outcome Trend Analysis")

    monthly_counts = (
        df.groupby("month", as_index=False)
        .agg(
            hhs_discharges=("hhs_discharges", "sum"),
            cbp_to_hhs_transfers=("cbp_to_hhs_transfers", "sum"),
        )
    )

    c1, c2 = st.columns(2)

    with c1:
        fig6 = px.bar(
            monthly_counts,
            x="month",
            y=["cbp_to_hhs_transfers", "hhs_discharges"],
            barmode="group",
            title="Monthly Transfers vs Discharges",
            labels={"value": "Children count", "variable": "Metric"},
        )
        st.plotly_chart(fig6, use_container_width=True)

    with c2:
        fig7 = px.line(
            monthly_outcome,
            x="month",
            y="outcome_stability_score",
            title="Outcome Stability Score by Month",
            labels={"outcome_stability_score": "Score"},
        )
        fig7.update_yaxes(range=[0, 1])
        st.plotly_chart(fig7, use_container_width=True)

with tab5:
    st.subheader("Weekday vs Weekend Transition Patterns")

    c1, c2 = st.columns(2)

    with c1:
        fig8 = px.bar(
            weekday_summary,
            x="weekday",
            y=["avg_transfer_efficiency", "avg_discharge_effectiveness"],
            barmode="group",
            title="Average Efficiency by Weekday",
            labels={"value": "Average ratio", "variable": "Metric"},
        )
        st.plotly_chart(fig8, use_container_width=True)

    with c2:
        fig9 = px.bar(
            weekday_summary,
            x="weekday",
            y="avg_net_hhs",
            title="Average HHS Net Flow by Weekday",
            labels={"avg_net_hhs": "Average net HHS flow"},
        )
        st.plotly_chart(fig9, use_container_width=True)

st.subheader("Filtered Data Preview")
st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)