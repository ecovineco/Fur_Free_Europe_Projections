"""
Python file for indicator: ID27 (Environmental Impacts)
Contains two public functions for scenario S1:
- run_projection_S1(df)
- make_figures_S1(df, theme)
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from figure_theme import Theme

# ---------------------------------------------------------
# CONSTANTS & FILE PATHS
# ---------------------------------------------------------
OUTPUT_BASE_DIR = Path("data/output/S1_output")
PELTS_FILE = OUTPUT_BASE_DIR / "projected_data.xlsx"
PELTS_SHEET = "Amount_Of_Pelts_Produced_Per_MS"

TARGET_SECTORS = ["Feed", "Other farm inputs", "Farming"]

def run_projection_S1(df_input):
    """
    Projects Environmental Metrics based on Pelt Production.
    
    Methodology:
    1. Calculate Total EU Pelt Production in 2024.
    2. Derive Impact Coefficient per Pelt for each Sector and Metric in 2024:
       Coeff = Value_2024 / Pelts_2024
    3. Project future values: Value_t = Coeff * Pelts_t
    """
    # ---------------------------------------------------------
    # 1. Load Drivers (EU Pelt Production)
    # ---------------------------------------------------------
    if not PELTS_FILE.exists():
        print(f"[WARNING] {PELTS_FILE} not found. Cannot run ID27 projection.")
        return pd.DataFrame()

    try:
        df_pelts = pd.read_excel(PELTS_FILE, sheet_name=PELTS_SHEET)
    except ValueError:
        print(f"[WARNING] Sheet {PELTS_SHEET} not found in {PELTS_FILE}.")
        return pd.DataFrame()

    # Calculate Total EU Pelts (All Species) per year
    # We sum across all countries to get the EU total
    if "Species" in df_pelts.columns and "All Species" in df_pelts["Species"].values:
        eu_pelts_series = df_pelts[df_pelts["Species"] == "All Species"].groupby("Year")["Pelts"].sum()
    elif "Species" in df_pelts.columns and "All species" in df_pelts["Species"].values:
        eu_pelts_series = df_pelts[df_pelts["Species"] == "All species"].groupby("Year")["Pelts"].sum()
    else:
        # Fallback: sum everything by year
        eu_pelts_series = df_pelts.groupby("Year")["Pelts"].sum()

    def get_total_pelts(year):
        return eu_pelts_series.get(year, 0)

    pelts_2024 = get_total_pelts(2024)

    if pelts_2024 == 0:
        print("[WARNING] Total EU Pelt production in 2024 is 0. Coefficients cannot be calculated.")
        return pd.DataFrame()

    # ---------------------------------------------------------
    # 2. Prepare Input Data (Baseline 2024)
    # ---------------------------------------------------------
    # Filter for EU / All Species / 2024 and relevant sectors
    df_baseline = df_input[
        (df_input["Country"] == "European Union") &
        (df_input["Species"] == "All Species") &
        (df_input["Year"] == 2024) &
        (df_input["Fur Industry Sector"].isin(TARGET_SECTORS))
    ].copy()

    if df_baseline.empty:
        print("[WARNING] No baseline data found for ID27 (EU, All Species, 2024).")
        return pd.DataFrame()

    # ---------------------------------------------------------
    # 3. Generate Projections (2010 - 2040)
    # ---------------------------------------------------------
    projection_rows = []
    years_range = range(2010, 2041)
    
    # Identify unique metrics present in the data (e.g., "Climate change", "Water use", etc.)
    metrics = df_baseline["Environmental Metric"].unique()

    for metric in metrics:
        for sector in TARGET_SECTORS:
            # Get baseline value for this specific Metric + Sector combo
            row = df_baseline[
                (df_baseline["Environmental Metric"] == metric) & 
                (df_baseline["Fur Industry Sector"] == sector)
            ]
            
            if row.empty:
                continue
            
            val_2024 = pd.to_numeric(row["Value"].iloc[0], errors="coerce") or 0
            unit = row["Metric Unit"].iloc[0]

            # Calculate Coefficient: Impact per Pelt
            impact_per_pelt = val_2024 / pelts_2024

            # Generate Time Series
            for year in years_range:
                pelts_t = get_total_pelts(year)
                projected_value = impact_per_pelt * pelts_t
                
                projection_rows.append({
                    "Country": "European Union",
                    "Species": "All Species",
                    "Fur Industry Sector": sector,
                    "Year": year,
                    "Environmental Metric": metric,
                    "Value": projected_value,
                    "Metric Unit": unit
                })

    # ---------------------------------------------------------
    # 4. Final Formatting
    # ---------------------------------------------------------
    df_projection = pd.DataFrame(projection_rows)
    
    # Define column order matching input
    output_headers = [
        "Country", "Species", "Fur Industry Sector", "Year", 
        "Environmental Metric", "Value", "Metric Unit"
    ]

    if df_projection.empty:
        return pd.DataFrame(columns=output_headers)

    return df_projection[output_headers]


def make_figures_S1(df):
    """
    Generates Stacked Bar Charts for each Environmental Metric.
    X-axis: Year
    Stacks: Fur Industry Sectors (Feed, Other farm inputs, Farming)
    """
    if df.empty:
        return

    Theme.apply_global()
    output_dir = Path("data/output/S1_output/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Filter for EU and All Species
    df_plot = df[
        (df["Country"] == "European Union") & 
        (df["Species"] == "All Species")
    ].copy()

    # Get list of metrics to plot
    metrics = df_plot["Environmental Metric"].unique()

    for metric in metrics:
        df_metric = df_plot[df_plot["Environmental Metric"] == metric]
        
        # Pivot: Index=Year, Columns=Sector, Values=Value
        pivot_df = df_metric.pivot_table(
            index="Year", 
            columns="Fur Industry Sector", 
            values="Value", 
            aggfunc="sum"
        ).fillna(0)

        # Reindex to ensure consistent stacking order (Feed on bottom)
        # Only include sectors that exist in the pivot
        available_sectors = [s for s in TARGET_SECTORS if s in pivot_df.columns]
        pivot_df = pivot_df.reindex(columns=available_sectors)

        if pivot_df.sum().sum() == 0:
            continue
            
        # Determine Unit for Label
        unit = df_metric["Metric Unit"].iloc[0] if "Metric Unit" in df_metric.columns else ""

        fig, ax = plt.subplots()
        
        # Plot Stacked Bar
        pivot_df.plot(kind='bar', stacked=True, ax=ax, width=0.8)

        # Styling
        ax.set_title(f"Projected EU Fur Industry Impact: {metric}")
        ax.set_ylabel(f"{metric} ({unit})")
        ax.set_xlabel("Year")
        ax.legend(title="Sector", loc="upper right")
        
        # Format X-axis labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        
        # Format Y-axis with commas
        # Use a flexible formatter that handles small decimals (common in env metrics) or large numbers
        from matplotlib.ticker import FuncFormatter
        def value_formatter(x, p):
            if x >= 1000:
                return f'{x:,.0f}'
            elif x >= 1:
                return f'{x:,.2f}'
            else:
                return f'{x:,.4g}'
        
        ax.get_yaxis().set_major_formatter(FuncFormatter(value_formatter))

        plt.tight_layout()
        
        # Save filename
        safe_name = metric.replace(" ", "_").replace("/", "_").replace(":", "")
        plt.savefig(output_dir / f"ID27_Waste_Generated_{safe_name}.png")
        plt.close(fig)