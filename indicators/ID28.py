"""
Python file for indicator: ID28 (Agricultural Land Occupation)
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
PROJECTED_FARMS_FILE = OUTPUT_BASE_DIR / "projected_data.xlsx"
FARMS_SHEET = "Amount_Fur_Companies_Per_MS"

# Species specific colors for consistency
SPECIES_COLORS = {
    "Mink": "#1f77b4",
    "Chinchilla": "#ff7f0e",
    "Raccoon dog": "#2ca02c",
    "Fox": "#d62728",
    "All Species": "#9467bd"
}

def run_projection_S1(df_historical):
    """
    Projects Agricultural Land Occupation per species based on projected number of farms.

    Methodology:
    1. Calculate total EU land occupation for 'Feed' and 'Other farm inputs' in 2024.
    2. Calculate total EU fur farms in 2024.
    3. Derive a 'Land Occupation per Farm' coefficient (km2/farm).
    4. Apply this coefficient to the projected number of farms for every Member State,
       species, and year (2010-2040).
    """
    # ---------------------------------------------------------
    # 1. Load Projected Farms Data (The Driver)
    # ---------------------------------------------------------
    if not PROJECTED_FARMS_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {PROJECTED_FARMS_FILE}. "
            "The farm projection (Amount_Fur_Companies_Per_MS) must run before ID28."
        )

    df_farms = pd.read_excel(PROJECTED_FARMS_FILE, sheet_name=FARMS_SHEET)

    # ---------------------------------------------------------
    # 2. Calculate Baseline Metrics (2024)
    # ---------------------------------------------------------
    
    # A. Calculate Total Agricultural Land Occupation in EU (2024)
    target_sectors = ["Feed", "Other farm inputs"]
    
    land_data_2024 = df_historical[
        (df_historical["Year"] == 2024) &
        (df_historical["Species"] == "All Species") &
        (df_historical["Fur Industry Sector"].isin(target_sectors)) & 
        (df_historical["Environmental Metric"] == "Agricultural land occupation")
    ]
    
    total_agricultural_land_occupation = land_data_2024["Value"].sum()
    
    if total_agricultural_land_occupation == 0:
        print("[WARNING] Total Agricultural Land Occupation for 2024 is 0. Check input data.")

    # B. Calculate Total Number of Farms in EU (2024)
    # Filter for Farming sector and sum All Species to get the baseline divisor
    farms_2024_rows = df_farms[
        (df_farms["Year"] == 2024) &
        (df_farms["Fur Industry Sector"] == "Farming")
    ]
    
    total_farms_EU_2024 = farms_2024_rows["Number of Farms"].sum()

    # C. Calculate Coefficient (Land Occupation per Farm)
    if total_farms_EU_2024 > 0:
        agricultural_land_occupation_per_farm = total_agricultural_land_occupation / total_farms_EU_2024
    else:
        agricultural_land_occupation_per_farm = 0

    # ---------------------------------------------------------
    # 3. Generate Projections (2010 - 2040) per Species
    # ---------------------------------------------------------
    projection_rows = []
    
    # We iterate through the existing Farm Projections (species-specific)
    target_farm_data = df_farms[
        (df_farms["Fur Industry Sector"] == "Farming") &
        (df_farms["Species"].str.lower() != "All Species")
    ]

    for _, row in target_farm_data.iterrows():
        country = row["Country"]
        year = row["Year"]
        species = row["Species"]
        n_farms = pd.to_numeric(row["Number of Farms"], errors='coerce') or 0
        
        if country == "European Union":
            continue

        # Apply the global coefficient to specific species farm counts
        projected_land_value = n_farms * agricultural_land_occupation_per_farm
        
        # Create output row matching the output_headers structure exactly
        projection_rows.append({
            "Country": country,
            "Environmental Metric": "Agricultural land occupation", # Added
            "Species": species,
            "Fur Industry Sector": "Farming",                   # Added
            "Value": projected_land_value,
            "Metric Unit": "km2",                                   # Changed from 'Unit'
            "Year": year
        })


    df_projection = pd.DataFrame(projection_rows)
    
    output_headers = [
        "Country", "Environmental Metric", "Species", 
        "Fur Industry Sector", "Value", "Metric Unit", "Year"
    ]
    
    return df_projection[output_headers]


def make_figures_S1(df_proj):
    """
    Generates figures for Agricultural Land Occupation.
    Plots individual species and an aggregated 'All Species' curve.
    """
    if df_proj.empty:
        return

    Theme.apply_global()
    output_figures_dir = OUTPUT_BASE_DIR / "figures"
    output_figures_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # 1. Per Member State Plots
    # ---------------------------------------------------------
    countries = df_proj["Country"].unique()
    
    for ms in countries:
        df_ms = df_proj[df_proj["Country"] == ms]
        
        # Calculate aggregate for plotting only
        df_ms_agg = df_ms.groupby("Year")["Value"].sum().reset_index()
        
        # Only plot if there is activity after 2025
        if df_ms_agg[df_ms_agg["Year"] > 2025]["Value"].sum() <= 0:
            continue

        fig, ax = plt.subplots()

        # A. Plot individual species
        for spec in df_ms["Species"].unique():
            df_spec = df_ms[df_ms["Species"] == spec].sort_values("Year")
            if df_spec["Value"].sum() > 0:
                ax.plot(
                    df_spec["Year"], 
                    df_spec["Value"], 
                    label=spec,
                    color=SPECIES_COLORS.get(spec, "#333333")
                )

        # B. Plot 'All Species' aggregate
        ax.plot(
            df_ms_agg["Year"], 
            df_ms_agg["Value"], 
            label="All Species",
            color=SPECIES_COLORS["All Species"],
            linewidth=4,
            alpha=0.7
        )

        ax.set_title(f"Projected Agricultural Land Occupation in {ms} (in km2)")
        ax.set_ylabel("Agricultural Land Occupation (km2)")
        ax.legend(loc="upper right")
        
        clean_ms = ms.replace(" ", "_")
        plt.savefig(output_figures_dir / f"ID28_AgriculturalLandOccupation_{clean_ms}.png", bbox_inches='tight')
        plt.close(fig)

    # ---------------------------------------------------------
    # 2. EU Aggregate Plot
    # ---------------------------------------------------------
    df_eu_species = df_proj.groupby(["Year", "Species"])["Value"].sum().reset_index()
    df_eu_total = df_proj.groupby("Year")["Value"].sum().reset_index()
    
    if not df_eu_total.empty and df_eu_total[df_eu_total["Year"] > 2025]["Value"].sum() > 0:
        fig, ax = plt.subplots()
        
        for spec in df_eu_species["Species"].unique():
            df_spec = df_eu_species[df_eu_species["Species"] == spec].sort_values("Year")
            if df_spec["Value"].sum() > 0:
                ax.plot(
                    df_spec["Year"], 
                    df_spec["Value"], 
                    label=spec,
                    color=SPECIES_COLORS.get(spec, "#333333")
                )

        ax.plot(
            df_eu_total["Year"], 
            df_eu_total["Value"], 
            label="EU-27 Total (All Species)",
            color=SPECIES_COLORS["All Species"],
            linewidth=4,
            alpha=0.7
        )
        
        ax.set_title("Projected Total Agricultural Land Occupation in EU")
        ax.set_ylabel("Agricultural Land Occupation (km2)")
        ax.legend(loc="upper right")
        
        plt.savefig(output_figures_dir / "ID28_AgriculturalLandOccupation_EU_Total.png", bbox_inches='tight')
        plt.close(fig)