"""
Python file for indicator: ID19
Contains two public functions for scenario S1:
- run_projection_S1(df)
- make_figures_S1(df, theme)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from figure_theme import Theme

# ---------------------------------------------------------
# CONSTANTS & FILE PATHS
# ---------------------------------------------------------
OUTPUT_BASE_DIR = Path("data/output/S1_output")
PELTS_FILE = OUTPUT_BASE_DIR / "projected_data.xlsx"
PELTS_SHEET = "Amount_Of_Pelts_Produced_Per_MS"

# Species to break down for Farming
FARMING_SPECIES = ["Mink", "Fox", "Raccoon dog", "Chinchilla"]

# Column Mapping: { Output Name : (2024 Input Column, 2028 Input Column) }
INDICATOR_MAPPING = {
    "Produced Quantity (in tonnes)": (
        "Produced Quantity (in tonnes)",
        "Projected produced quantity (in tonnes) by taking phase-outs and upcoming bans into account"
    ),
    "Value (in million €)": (
        "Value (in million €)",
        "Projected value (in million €) by taking phase-outs and upcoming bans into account"
    ),
    "Number of jobs": (
        "Number of jobs",
        "Projected number of jobs by taking phase-outs and upcoming bans into account"
    ),
    "GVA (in million €)": (
        "GVA (in million €)",
        "Projected GVA (in million €) by taking phase-outs and upcoming bans into account"
    ),
    "Profit (in million €)": (
        "Profit (in million €)",
        "Projected Profit (in million €) by taking phase-outs and upcoming bans into account"
    ),
    "Tax Returns (in million €)": (
        "Tax Returns (in million €)",
        "Projected Tax Returns (in million €) by taking phase-outs and upcoming bans into account"
    )
}

TARGET_SECTORS = [
    "Feed", 
    "Farming", 
    "Auction, agency", 
    "Tanning, dressing, dyeing", 
    "Product manufacturing", 
    "Wholesale", 
    "Retail sale"
]

def run_projection_S1(df_input):
    """
    Projects economic indicators (Value, Jobs, Profit, etc.) for the Fur Industry.
    
    Logic:
    1. All Sectors (All Species):
       - 2010-2023: Backcasting proportional to Pelt Production.
       - 2025-2028: Linear interpolation between 2024 baseline and 2028 target.
       - 2029-2040: Scales proportional to Total EU Pelt Production.
    2. Farming Sector (Species Breakdown):
       - Apportioned from Farming (All Species) based on pelt production share.
    """
    # ---------------------------------------------------------
    # 1. Load Drivers (EU Pelt Production)
    # ---------------------------------------------------------
    if not PELTS_FILE.exists():
        print(f"[WARNING] {PELTS_FILE} not found. Cannot run ID19 projection.")
        return pd.DataFrame()

    try:
        df_pelts = pd.read_excel(PELTS_FILE, sheet_name=PELTS_SHEET)
    except ValueError:
        print(f"[WARNING] Sheet {PELTS_SHEET} not found in {PELTS_FILE}.")
        return pd.DataFrame()

    # Pre-calculate aggregated pelts for lookups
    # 1. Total EU Pelts (All Species) per year
    total_pelts_series = df_pelts.groupby("Year")["Pelts"].sum()
    
    # 2. Total EU Pelts per Species per year
    species_pelts_df = df_pelts.groupby(["Year", "Species"])["Pelts"].sum()

    def get_total_pelts(year):
        return total_pelts_series.get(year, 0)
    
    def get_species_pelts(year, species):
        # Handle potential case sensitivity or missing species
        try:
            return species_pelts_df.loc[(year, species)]
        except KeyError:
            # Fallback for capitalization differences
            try:
                return species_pelts_df.loc[(year, species.lower())]
            except KeyError:
                return 0

    pelts_2024 = get_total_pelts(2024) 
    pelts_2028 = get_total_pelts(2028) 

    # ---------------------------------------------------------
    # 2. Prepare Input Data (Baseline 2024 & Target 2028)
    # ---------------------------------------------------------
    df_baseline = df_input[
        (df_input["Country"] == "European Union") &
        (df_input["Species"] == "All Species") &
        (df_input["Year"] == 2024)
    ].copy()

    # ---------------------------------------------------------
    # 3. Generate Projections (2010 - 2040)
    # ---------------------------------------------------------
    projection_rows = []
    years_range = range(2010, 2041)

    for sector in TARGET_SECTORS:
        sector_row = df_baseline[df_baseline["Fur Industry Sector"] == sector]
        
        if sector_row.empty:
            continue
            
        sector_row = sector_row.iloc[0]
        
        # --- A. Calculate "All Species" Trajectory for this Sector ---
        sector_trajectory = {y: {} for y in years_range}

        for out_col, (col_2024, col_2028) in INDICATOR_MAPPING.items():
            val_2024 = pd.to_numeric(sector_row.get(col_2024, 0), errors="coerce") or 0
            val_2028_target = pd.to_numeric(sector_row.get(col_2028, 0), errors="coerce") or 0

            # 1. Backcasting (2010 - 2023)
            for t in range(2010, 2024):
                pelts_t = get_total_pelts(t)
                val_t = val_2024 * (pelts_t / pelts_2024) if pelts_2024 > 0 else 0
                sector_trajectory[t][out_col] = val_t

            # 2. Interpolation (2024 - 2028)
            for t in range(2024, 2029):
                if t == 2024: val_t = val_2024
                elif t == 2028: val_t = val_2028_target
                else: val_t = val_2024 + (val_2028_target - val_2024) * (t - 2024) / 4.0
                sector_trajectory[t][out_col] = val_t

            # 3. Scaling (2029 - 2040)
            base_val_Scaling = val_2028_target
            for t in range(2029, 2041):
                pelts_t = get_total_pelts(t)
                val_t = base_val_Scaling * (pelts_t / pelts_2028) if pelts_2028 > 0 else 0
                sector_trajectory[t][out_col] = val_t

        # --- B. Create Rows for "All Species" ---
        for t in years_range:
            row_data = {
                "Country": "European Union",
                "Species": "All Species",
                "Fur Industry Sector": sector,
                "Year": t
            }
            # Fill indicators
            for ind_name in INDICATOR_MAPPING.keys():
                row_data[ind_name] = sector_trajectory[t][ind_name]
            
            # Calculate Ratio
            jobs = row_data.get("Number of jobs", 0)
            turnover = row_data.get("Value (in million €)", 0)
            row_data["Ratio of FTE employment to sector turnover (€ million)"] = jobs / turnover if turnover != 0 else 0

            projection_rows.append(row_data)

            # --- C. Create Rows for Specific Species (Farming Only) ---
            if sector == "Farming":
                # Get total values for this year (All Species) from the trajectory we just calculated
                total_farming_vals = sector_trajectory[t]
                total_prod_eu_t = get_total_pelts(t)

                for species in FARMING_SPECIES:
                    prod_eu_s_t = get_species_pelts(t, species)
                    
                    # Calculate Share: Prod_s / Prod_Total
                    share = prod_eu_s_t / total_prod_eu_t if total_prod_eu_t > 0 else 0

                    spec_row_data = {
                        "Country": "European Union",
                        "Species": species,
                        "Fur Industry Sector": "Farming",
                        "Year": t
                    }
                    
                    # Apportion Indicators
                    # Value, GVA, Profit, Tax, Quantity -> Proportional to Pelts (share)
                    # Jobs -> Proportional to Value (which is proportional to share)
                    for ind_name in INDICATOR_MAPPING.keys():
                        total_val = total_farming_vals.get(ind_name, 0)
                        spec_row_data[ind_name] = total_val * share
                    
                    # Recalculate Ratio for species (should be identical to Total if math holds, but calculated explicitly)
                    s_jobs = spec_row_data.get("Number of jobs", 0)
                    s_val = spec_row_data.get("Value (in million €)", 0)
                    spec_row_data["Ratio of FTE employment to sector turnover (€ million)"] = s_jobs / s_val if s_val != 0 else 0
                    
                    projection_rows.append(spec_row_data)

    # ---------------------------------------------------------
    # 4. Final Formatting
    # ---------------------------------------------------------
    df_projection = pd.DataFrame(projection_rows)
    
    output_headers = [
        "Country", "Species", "Fur Industry Sector", "Year", 
        "Produced Quantity (in tonnes)", "Value (in million €)", 
        "Ratio of FTE employment to sector turnover (€ million)", 
        "Number of jobs", "GVA (in million €)", "Profit (in million €)", 
        "Tax Returns (in million €)"
    ]

    if df_projection.empty:
        return pd.DataFrame(columns=output_headers)

    return df_projection[output_headers]


def make_figures_S1(df):
    """
    Generates figures for ID19.
    1. Stacked Bar Charts (All Sectors combined) for each indicator.
    2. Line Charts (Farming Only) per species for each indicator.
    """
    if df.empty:
        return

    Theme.apply_global()
    output_dir = Path("data/output/S1_output/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Filter for EU
    df_eu = df[df["Country"] == "European Union"].copy()
    if df_eu.empty:
        return

    # List of indicators to plot
    # (Column Name, Filename Suffix, Y-Axis Label)
    indicators = [
        ("Value (in million €)", "Value", "Value (Million €)"),
        ("GVA (in million €)", "GVA", "GVA (Million €)"),
        ("Profit (in million €)", "Profit", "Profit (Million €)"),
        ("Number of jobs", "Jobs", "Jobs"),
        ("Tax Returns (in million €)", "Tax_Returns", "Tax Returns (Million €)"),
        ("Produced Quantity (in tonnes)", "Quantity", "Quantity (Tonnes)")
    ]

    # ---------------------------------------------------------
    # 1. Stacked Bar Charts (All Sectors, All Species)
    # ---------------------------------------------------------
    # Filter: All Species
    df_all_spec = df_eu[df_eu["Species"] == "All Species"].copy()

    for col, suffix, ylabel in indicators:
        # Pivot: Index=Year, Columns=Sector, Values=Indicator
        pivot_df = df_all_spec.pivot_table(index="Year", columns="Fur Industry Sector", values=col, aggfunc="sum").fillna(0)
        
        if pivot_df.sum().sum() == 0:
            continue

        fig, ax = plt.subplots()
        
        # Plot stacked bar
        # We use a distinct color map or manual colors if we had them per sector. 
        # Using default matplotlib cycle for sectors.
        pivot_df.plot(kind='bar', stacked=True, ax=ax, width=0.8)

        ax.set_title(f"Projected EU Fur Industry {suffix} (All Sectors)")
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Year")
        ax.legend(title="Sector", bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Reduce X-axis clutter (show every 5th year label if dense)
        # Bar plots have categorical X-axis by default.
        # Let's keep all years but ensure rotation
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        
        # Format Y-Axis with commas
        ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        plt.tight_layout()
        plt.savefig(output_dir / f"Fur_Industry_{suffix}_Stacked.png")
        plt.close(fig)

    # ---------------------------------------------------------
    # 2. Line Charts (Farming Only, Per Species)
    # ---------------------------------------------------------
    # Filter: Farming Sector, Specific Species (Exclude 'All Species')
    df_farming = df_eu[
        (df_eu["Fur Industry Sector"] == "Farming") & 
        (df_eu["Species"] != "All Species")
    ].copy()

    if not df_farming.empty:
        for col, suffix, ylabel in indicators:
            # Check if data exists
            if df_farming[col].sum() == 0:
                continue

            fig, ax = plt.subplots()
            
            # Pivot for plotting: Index=Year, Columns=Species
            pivot_species = df_farming.pivot_table(index="Year", columns="Species", values=col, aggfunc="sum").fillna(0)
            
            for species in pivot_species.columns:
                ax.plot(
                    pivot_species.index, 
                    pivot_species[species], 
                    label=species, 
                    color=Theme.COLORS.get(species, "#333333")
                )

            ax.set_title(f"Farming {suffix} by Species")
            ax.set_ylabel(ylabel)
            ax.set_xlabel("Year")
            ax.legend(loc="upper right")
            
            ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
            
            plt.tight_layout()
            plt.savefig(output_dir / f"Farming_{suffix}_by_Species.png")
            plt.close(fig)