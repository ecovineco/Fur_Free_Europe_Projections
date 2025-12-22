"""
Python file for indicator: Amount_Fur_Companies_Per_MS
Contains two public functions for scenario S1:
- run_projection_S1(df)
- make_figures_S1(df_final)
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

# Colors for plotting
SPECIES_COLORS = {
    "Mink": "#1f77b4",
    "Chinchilla": "#ff7f0e",
    "Raccoon dog": "#2ca02c",
    "Fox": "#d62728",
    "All Species": "#9467bd"
}

def run_projection_S1(df_historical):
    """
    Projects the number of fur farms per species based on the proportional 
    change of pelt production relative to the 2025 baseline.
    """
    if df_historical.empty:
        return pd.DataFrame()

    if not PROJECTED_DATA_FILE.exists():
        print(f"[WARNING] Could not find {PROJECTED_DATA_FILE}. Returning historical data only.")
        return df_historical

    # 1. Load production driver (Pelts)
    #    Expected columns in production sheet: MS, Species, Year, Pelts
    try:
        df_production = pd.read_excel(PROJECTED_DATA_FILE, sheet_name=PRODUCTION_SHEET)
    except ValueError:
        print(f"[WARNING] Sheet {PRODUCTION_SHEET} not found. Returning historical data only.")
        return df_historical

    # 2. Clean Historical Data
    #    Filter for 'Farming' (or 'Farming') and ensure Year is int
    df_clean = df_historical.copy()
    df_clean["Fur Industry Sector"] = df_clean["Fur Industry Sector"].fillna("Farming").astype(str).str.strip()
    # Normalize sector names to "Fur Farming" for consistency
    df_clean.loc[df_clean["Fur Industry Sector"].isin(["", "nan", "Farming"]), "Fur Industry Sector"] = "Farming"
    
    target_sector = "Farming"
    df_clean["Year"] = pd.to_numeric(df_clean["Year"], errors="coerce").fillna(0).astype(int)
    df_clean["Number of Farms"] = pd.to_numeric(df_clean["Number of Farms"], errors="coerce").fillna(0)

    # 3. Get Baseline Data (Year 2025)
    #    We only want species-specific rows, explicitly excluding pre-calculated 'All Species' if present
    df_farms_2025 = df_clean[
        (df_clean["Year"] == 2025) & 
        (df_clean["Fur Industry Sector"] == target_sector) &
        (df_clean["Species"].str.lower() != "all species")
    ].copy()

    # Pre-process Production Data for fast lookup
    # Pivot so we can quickly look up [Year, MS, Species] -> Pelts
    # Ensure production dataframe uses same naming conventions (MS vs Country)
    if "Country" in df_production.columns and "MS" not in df_production.columns:
        df_production = df_production.rename(columns={"Country": "MS"})
    
    prod_pivot = df_production.groupby(["MS", "Species", "Year"])["Pelts"].sum()

    projection_rows = []
    # Project for years 2010 to 2040
    # We include 2025 in the loop logic or just append the actual 2025 rows later. 
    # The prompt asks to exclude 2025 from calculation since we have it, but add it to output.
    all_years = range(2010, 2041)

    for _, row in df_farms_2025.iterrows():
        ms = row["Country"] # Input uses 'Country'
        species = row["Species"]
        farms_2025 = row["Number of Farms"]
        source_2025 = row.get("Source", "Historical")

        # Get production in baseline year (2025) for this MS and Species
        try:
            prod_2025 = prod_pivot.loc[(ms, species, 2025)]
        except KeyError:
            prod_2025 = 0

        for year in all_years:
            if year == 2025:
                # Use the actual historical value provided in the input
                projection_rows.append({
                    "Country": ms,
                    "Fur Industry Sector": target_sector,
                    "Species": species,
                    "Year": year,
                    "Number of Farms": farms_2025,
                    "Source": source_2025
                })
                continue

            # For other years, use the ratio of production
            try:
                prod_t = prod_pivot.loc[(ms, species, year)]
            except KeyError:
                prod_t = 0
            
            if prod_2025 > 0:
                farms_t = farms_2025 * (prod_t / prod_2025)
            else:
                farms_t = 0

            projection_rows.append({
                "Country": ms,
                "Fur Industry Sector": target_sector,
                "Species": species,
                "Year": year,
                "Number of Farms": farms_t,
                "Source": "Projected (S1)"
            })

    # 4. Construct Final DataFrame
    df_final = pd.DataFrame(projection_rows)
    
    # Ensure standard columns are present
    output_headers = ["Country", "Fur Industry Sector", "Species", "Year", "Number of Farms", "Source"]
    # Add Source column if missing (logic above handles it, but safety check)
    if "Source" not in df_final.columns:
        df_final["Source"] = "Projected (S1)"
        
    return df_final[output_headers]


def make_figures_S1(df_final):
    """
    Generates time-series plots for the Number of Farms.
    Plots curves for each individual species AND a calculated 'All Species' curve.
    """
    if df_final.empty:
        return

    # Apply the global theme
    Theme.apply_global()

    # Filter for relevant sector
    df_farming = df_final[df_final["Fur Industry Sector"] == "Farming"].copy()

    # Define output folder
    figures_folder = OUTPUT_BASE_DIR / "figures"
    figures_folder.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # 1. Per Member State Plots
    # ---------------------------------------------------------
    countries = df_farming["Country"].unique()
    
    for ms in countries:
        df_ms = df_farming[df_farming["Country"] == ms]
        
        # Calculate "All Species" aggregate for this MS
        df_ms_agg = df_ms.groupby("Year")["Number of Farms"].sum().reset_index()
        
        # Check if there is any activity > 0 after 2025
        # (Using the aggregate to check viability)
        if df_ms_agg[df_ms_agg["Year"] > 2025]["Number of Farms"].sum() <= 0:
            continue

        fig, ax = plt.subplots()

        # A. Plot individual species
        species_list = df_ms["Species"].unique()
        for spec in species_list:
            df_spec = df_ms[df_ms["Species"] == spec].sort_values("Year")
            # Only plot species that have non-zero values at some point
            if df_spec["Number of Farms"].sum() > 0:
                ax.plot(
                    df_spec["Year"], 
                    df_spec["Number of Farms"], 
                    label=spec,
                    color=SPECIES_COLORS.get(spec, "#333333")
                )

        ax.set_title(f"Projected Number of Farms: {ms}")
        ax.set_ylabel("Number of Farms")
        ax.legend(loc="upper right")
        
        # Save figure
        clean_ms = ms.replace(" ", "_")
        plt.savefig(figures_folder / f"Amount_Fur_Companies_{clean_ms}_Farms.png", bbox_inches='tight')
        plt.close(fig)

    # ---------------------------------------------------------
    # 2. EU-27 Aggregate Plot
    # ---------------------------------------------------------
    # Group by Year and Species to get EU totals per species
    df_eu_species = df_farming.groupby(["Year", "Species"])["Number of Farms"].sum().reset_index()
    # Group by Year to get EU total for "All Species"
    df_eu_total = df_farming.groupby("Year")["Number of Farms"].sum().reset_index()

    if not df_eu_total.empty and df_eu_total[df_eu_total["Year"] > 2025]["Number of Farms"].sum() > 0:
        fig, ax = plt.subplots()
        
        # A. Plot individual species totals
        for spec in df_eu_species["Species"].unique():
            df_spec = df_eu_species[df_eu_species["Species"] == spec].sort_values("Year")
            if df_spec["Number of Farms"].sum() > 0:
                ax.plot(
                    df_spec["Year"], 
                    df_spec["Number of Farms"], 
                    label=spec,
                    color=SPECIES_COLORS.get(spec, "#333333")
                )

        # B. Plot "All Species" total
        ax.plot(
            df_eu_total["Year"], 
            df_eu_total["Number of Farms"], 
            label="All Species",
            color=SPECIES_COLORS.get("All Species", "#9467bd"),
            linewidth=3,
            alpha=0.8
        )

        ax.set_title("Projected Total Number of Farms in EU")
        ax.set_ylabel("Number of Farms")
        ax.legend(loc="upper right")
        
        plt.savefig(figures_folder / "Amount_Fur_Companies_EU_Total_Farms.png", bbox_inches='tight')
        plt.close(fig)