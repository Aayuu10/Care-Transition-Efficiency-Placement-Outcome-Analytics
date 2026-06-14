# Care Transition Efficiency & Placement Outcome Analytics

This repository contains a complete data analytics and dashboard project that reframes the **HHS Unaccompanied Children Program (UCP)** dataset from a capacity-monitoring lens to a **care pipeline efficiency and placement outcome** lens.

The system models the pipeline:

> **CBP custody → HHS care → Sponsor placement**

and focuses on **how effectively children move through this pipeline over time**, not just how many children are in custody at any moment.

---

## 📂 Project Structure

```bash
care_transition_analytics/
├── HHS_UAC_Data.csv                              # Daily UCP dataset (Aug–Dec 2025)
├── analysis_core.py                              # Data loading, preprocessing, metrics & KPIs
├── app.py                                        # Streamlit dashboard
└── care_transition_research_paper.md             # Full research paper (IEEE-style)
```

---

## 🎯 Project Objectives

This project addresses four core questions:

- How efficiently are children transferred from **CBP to HHS**?
- Are **discharges** from HHS keeping pace with **inflows**?
- When and where do **care backlogs** accumulate?
- Are **placement outcomes** stable over time or becoming more volatile?

To answer these, the project:

- Models the care pipeline as a **multi-stage flow system**
- Defines and computes **process efficiency metrics**
- Identifies **backlog and delay patterns**
- Builds an **interactive Streamlit dashboard** for live analytics

---

## 📊 Dataset Overview

The project uses the official **HHS Unaccompanied Children Program** daily dataset for August–December 2025. Each row represents a reporting date with the following fields:

| Column | Description |
|--------|-------------|
| `Date` | Reporting date |
| `Children apprehended and placed in CBP custody*` | Daily CBP intake volume |
| `Children in CBP custody` | Active CBP care load |
| `Children transferred out of CBP custody` | Transfers from CBP to HHS |
| `Children in HHS Care` | Active HHS care load |
| `Children discharged from HHS Care` | Daily discharges / sponsor placements |

Numeric fields such as `Children in HHS Care` include thousands separators (e.g. `"2,484"`), which are cleaned before analysis. [file:42]

---

## 🧮 Metrics & Key Performance Indicators (KPIs)

The analysis computes several **transition efficiency** and **outcome stability** metrics:

### 1. Transfer Efficiency Ratio (TER)

Measures how efficiently children are transferred from **CBP custody to HHS care**:

\[
TER_t = \frac{\text{Children transferred out of CBP custody}_t}{\text{Children in CBP custody}_t}
\]

High TER ⇒ faster CBP→HHS transitions on that day.

### 2. Discharge Effectiveness (DE)

Measures how effectively HHS discharges children from care:

\[
DE_t = \frac{\text{Children discharged from HHS Care}_t}{\text{Children in HHS Care}_t}
\]

High DE ⇒ HHS is discharging children at a higher rate relative to current load.

### 3. Pipeline Throughput (PTR)

Relates **system exits** to **system entries**:

\[
PTR_t = \frac{\text{Children discharged from HHS Care}_t}{\text{Children apprehended and placed in CBP custody*}_t}
\]

Aggregate PTR over a period indicates whether discharges keep pace with CBP intake.

### 4. Net Flows & Backlog Accumulation Rate (BAR)

Net flows:

\[
NetCBP_t = \text{CBP intake}_t - \text{Transfers}_t
\]

\[
NetHHS_t = \text{Transfers}_t - \text{Discharges}_t
\]

Backlog Accumulation Rate (BAR):

\[
BAR_t = \text{7-day rolling mean of } NetHHS_t
\]

Positive BAR ⇒ sustained HHS backlog buildup (inflows > outflows).

### 5. Outcome Stability Score (OSS)

Measures **stability** of discharge performance per month:

\[
OSS_m = 1 - \frac{\sigma_{DE,m}}{\mu_{DE,m}}
\]

- \(\mu_{DE,m}\) = mean daily Discharge Effectiveness for month \(m\)  
- \(\sigma_{DE,m}\) = standard deviation of daily DE for month \(m\)  
- OSS ∈ [0, 1]; higher = more stable placement outcomes.

---

## 🧱 Code Architecture

### `analysis_core.py`

Core responsibilities:

- Load and clean the CSV:
  - Parse dates
  - Strip thousands separators
  - Convert numerics safely
- Engineer time features:
  - Weekday, ISO week, month, weekend indicator
- Compute daily metrics:
  - TER, DE, PTR (daily)
  - NetCBP, NetHHS
  - Backlog Accumulation Rate (7-day rolling)
- Aggregate KPIs:
  - TER, DEI, PTR, BAR over filtered period
- Compute:
  - Monthly Outcome Stability Score (OSS)
  - Weekday-level summaries (weekday vs weekend patterns)

Exposed functions:

- `prepare_data(path=...)` → `(df, monthly_outcome, weekday_summary)`
- `compute_overall_kpis(df)` → dict of KPIs

### `app.py` (Streamlit Dashboard)

The Streamlit app is the **interactive front-end** for all analytics. It:

- Loads preprocessed data via `prepare_data()`
- Provides **sidebar controls**:
  - Date range filter
  - KPI selection (TER, DEI, PTR, BAR, OSS)
  - Threshold sliders for alerts
- Displays **top-level KPI cards**:
  - Transfer Efficiency Ratio
  - Discharge Effectiveness Index
  - Pipeline Throughput
  - Backlog Accumulation Rate
  - Outcome Stability Score (avg)
- Raises **alert messages** when:
  - TER < configured threshold
  - DE < configured threshold
  - BAR > configured threshold

---

## 📈 Dashboard Modules

The app is organized into multiple tabs:

### 1. Care Pipeline Flow

- Multi-line Plotly chart showing:
  - CBP intake
  - CBP load
  - CBP→HHS transfers
  - HHS care load
  - HHS discharges
- Visualizes the entire CBP→HHS→Sponsor pipeline over time.

### 2. Transfer & Discharge Efficiency

- Line charts for:
  - Transfer Efficiency Ratio (with 7-day rolling average)
  - Discharge Effectiveness (with 7-day rolling average)
- Helps identify **efficiency dips** and **trend changes**.

### 3. Bottleneck Detection

- Net flow charts:
  - `NetCBP` and `NetHHS` over time
- Backlog chart:
  - Backlog Accumulation Rate (7-day rolling)
- Summary of days with **positive HHS backlog**, indicating accumulation.

### 4. Outcome Trends & Stability

- Monthly bar chart:
  - Total transfers vs total discharges
- Line chart:
  - Outcome Stability Score (OSS) by month
- Focus on **medium-term trends and stability** of placements.

### 5. Weekday Patterns

- Average TER & DE by weekday
- Average NetHHS by weekday
- Highlights **weekday vs weekend** effectiveness and backlog patterns.

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/care_transition_analytics.git
cd care_transition_analytics
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
# .venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If you don’t have a `requirements.txt` yet, a minimal version looks like:

```text
pandas
numpy
streamlit
plotly
```

### 4. Run the Dashboard

```bash
streamlit run app.py
```

Then open the URL shown in the terminal (usually `http://localhost:8501`).

---

## 🧪 How to Use the Dashboard

1. **Select a date range** in the sidebar to focus on a specific period.
2. **Toggle KPIs** you care about in the KPI selection control.
3. Set **thresholds** for:
   - Transfer efficiency
   - Discharge effectiveness
   - Backlog accumulation
4. Explore each tab:
   - `Care Pipeline Flow` to see end-to-end movement
   - `Efficiency Panels` for TER/DE trends
   - `Bottleneck Detection` for backlogs
   - `Outcome Trends` for monthly behavior and OSS
   - `Weekday Patterns` for weekday vs weekend dynamics

This workflow supports both **operational monitoring** and **research/EDA** use cases.

---

## 💡 Future Enhancements

Planned / possible extensions:

- Facility- or region-level analysis (if disaggregated data is available)
- Length-of-stay modeling and survival analysis
- Integration with real-time data feeds
- Role-based views (policy vs operations vs analytics)
- Authentication and deployment to cloud (e.g. Streamlit Cloud / AWS)

---

## ⚖️ Disclaimer

This project uses publicly available, aggregate-level data from the HHS Unaccompanied Children Program. It focuses on **process efficiency metrics** and does not make claims about individual-level outcomes or legal decisions. The analyses and visualizations are for educational and analytical purposes.

---

## 🙋‍♂️ Author

**Aayush Koli**  
Data Scientist / AI-ML Engineer  
- Focus: ML systems, LLM pipelines, and full-stack AI analytics  
- This project was developed as part of a care transition analytics assignment with Unified Mentor.

If you have suggestions, issues, or want to extend this project, feel free to open an issue or submit a pull request.
