"""
Python file for indicator: Amount_Fur_Companies_Per_MS
Contains two public functions for scenario S1:
- run_projection_S1(df)
- make_figures_S1(df)
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from figure_theme import Theme

# ---------------------------------------------------------
# CONSTANTS & FILE PATHS
# ---------------------------------------------------------
OUTPUT_BASE_DIR = Path("data/output/S1_output")
PROJECTED_DATA_FILE = OUTPUT_BASE_DIR / "projected_data.xlsx"
PRODUCTION_SHEET = "Amount_Of_Pelts_Produced_Per_MS"

def run_projection_S1(df_historical):
    """
    Projects the number of fur farms based on the proportional decline of pelt production.
    """
    if not PROJECTED_DATA_FILE.exists():
        raise FileNotFoundError(f"Could not find {PROJECTED_DATA_FILE}.")

    # Load production driver
    df_production = pd.read_excel(PROJECTED_DATA_FILE, sheet_name=PRODUCTION_SHEET)

    # Aggressively clean historical data to handle empty/whitespace cells in Sector
    df_historical["Fur Industry Sector"] = df_historical["Fur Industry Sector"].fillna("Farming").astype(str).str.strip()
    # Force any empty string or 'nan' to 'Farming' to ensure the filter works
    df_historical.loc[df_historical["Fur Industry Sector"].isin(["", "nan"]), "Fur Industry Sector"] = "Farming"

    # Filter Settings
    target_sector = "Farming"
    target_species = "All Species"

    # Aggregate production per Country and Year using 'Pelts' header
    df_prod_agg = df_production.groupby(["Country", "Year"], as_index=False)["Pelts"].sum()

    # Filter historical farm data for 2024
    df_farms_2024 = df_historical[
        (df_historical["Year"] == 2024) & 
        (df_historical["Fur Industry Sector"] == target_sector) & 
        (df_historical["Species"] == target_species)
    ].copy()

    projection_rows = []
    future_years = range(2025, 2041)

    for _, row in df_farms_2024.iterrows():
        country_name = row["Country"]
        farms_count_2024 = row["Number of Farms"]
        
        ms_pelt_data = df_prod_agg[df_prod_agg["Country"] == country_name]
        
        # Extract baseline pelts for 2024
        baseline_series = ms_pelt_data.loc[ms_pelt_data["Year"] == 2024, "Pelts"]
        pelts_2024 = baseline_series.item() if not baseline_series.empty else 0

        for year in future_years:
            future_series = ms_pelt_data.loc[ms_pelt_data["Year"] == year, "Pelts"]
            pelts_future = future_series.item() if not future_series.empty else 0

            # Proportionality rule: projection based on pelt decline
            if pelts_2024 > 0:
                scale_ratio = pelts_future / pelts_2024
                projected_farms = farms_count_2024 * scale_ratio
            else:
                projected_farms = 0

            projection_rows.append({
                "Country": country_name,
                "Fur Industry Sector": "Farming", # Explicitly set to Farming
                "Species": target_species,
                "Year": year,
                "Number of Farms": projected_farms
            })

    # Combine historical and projection
    df_projections = pd.DataFrame(projection_rows)
    
    # Define and clean output headers as requested
    output_headers = ["Country", "Fur Industry Sector", "Species", "Year", "Number of Farms"]
    df_historical_clean = df_historical[output_headers].copy()
    # Force Farming label on all historical rows as well
    df_historical_clean["Fur Industry Sector"] = "Farming"
    
    df_final = pd.concat([df_historical_clean, df_projections], ignore_index=True)
    
    return df_final[output_headers]

def make_figures_S1(df_final):
    """
    Generates time-series plots for the Number of Farms.
    """
    # Filter for the relevant data subset (All Species)
    df_plot = df_final[
        (df_final["Fur Industry Sector"] == "Farming") &
        (df_final["Species"] == "All Species")
    ]

    # --- Per Country Plots ---
    unique_countries = df_plot["Country"].unique()
    for country in unique_countries:
        country_data = df_plot[df_plot["Country"] == country].sort_values("Year")
        
        # Only plot if there's projected activity after 2024
        if not (country_data.loc[country_data["Year"] > 2024, "Number of Farms"] > 0).any():
            continue

        fig, ax = plt.subplots()
        ax.plot(
            country_data["Year"], 
            country_data["Number of Farms"], 
            label="All Species",
            color=Theme.COLORS["All Species"]
        )

        ax.set_title(f"Projected Number of Fur Farms in {country}")
        ax.set_xlabel("Year")
        ax.set_ylabel("Number of Farms")
        ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        ax.legend(loc="upper right")

        # Save output
        save_path = OUTPUT_BASE_DIR / "figures" / f"Amount_Fur_Companies_Per_MS_Farms_{country}.png"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path)
        plt.close(fig)

    # --- EU-27 Aggregate Plot ---
    eu_total_series = df_plot.groupby("Year", as_index=False)["Number of Farms"].sum()
    
    if not eu_total_series.empty:
        fig_eu, ax_eu = plt.subplots()
        ax_eu.plot(
            eu_total_series["Year"], 
            eu_total_series["Number of Farms"], 
            label="EU-27 Total",
            color=Theme.COLORS["All Species"]
        )
        
        ax_eu.set_yscale('log')
        # Add these three lines:
        ax_eu.set_yticks([100,250,500, 1000, 2500, 5000, 10000])
        ax_eu.get_yaxis().set_major_formatter(plt.ScalarFormatter())
        ax_eu.get_yaxis().set_minor_formatter(plt.NullFormatter())
        ax_eu.set_title("Projected Total Number of Fur Farms in the EU (All Species)")
        ax_eu.set_xlabel("Year")
        ax_eu.set_ylabel("Number of Farms")
        ax_eu.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        ax_eu.legend(loc="upper right")
        
        plt.savefig(OUTPUT_BASE_DIR / "figures" / "Amount_Fur_Companies_Per_MS_Farms_EU_Total.png")
        plt.close(fig_eu)