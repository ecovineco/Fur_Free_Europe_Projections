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
# We need the projected number of farms to drive this environmental indicator
OUTPUT_BASE_DIR = Path("data/output/S1_output")
PROJECTED_FARMS_FILE = OUTPUT_BASE_DIR / "projected_data.xlsx"
FARMS_SHEET = "Amount_Fur_Companies_Per_MS"

def run_projection_S1(df_historical):
    """
    Projects Agricultural Land Occupation based on the number of fur farms.

    Methodology:
    1. Calculate total EU land occupation for 'Feed' and 'Other farm inputs' in 2024.
    2. Calculate total EU fur farms in 2024.
    3. Derive a 'Land Occupation per Farm' coefficient (km2/farm).
    4. Apply this coefficient to the projected number of farms for every Member State 
       and year (2010-2040).

    Args:
        df_historical (pd.DataFrame): Input data from ID28 sheet.

    Returns:
        pd.DataFrame: Projected agricultural land occupation with headers matching input.
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
    # Filter for specific inputs that drive land use
    target_sectors = ["Feed", "Other farm inputs"]
    
    # Filter input dataframe for the baseline year and relevant sectors
    # Assuming the input df contains EU aggregate data as shown in the screenshot
    land_data_2024 = df_historical[
        (df_historical["Year"] == 2024) &
        (df_historical["Species"] == "All Species") &
        (df_historical["Fur Industry Sector"].isin(target_sectors)) & 
        (df_historical["Environmental Metric"] == "Agricultural land occupation")
    ]
    
    # Sum the 'Value' column (km2)
    total_agricultural_land_occupation = land_data_2024["Value"].sum()
    
    if total_agricultural_land_occupation == 0:
        print("[WARNING] Total Agricultural Land Occupation for 2024 is 0. Check input data.")

    # B. Calculate Total Number of Farms in EU (2024)
    # We sum the farm counts across all Member States for 2024
    farms_2024_rows = df_farms[
        (df_farms["Year"] == 2024) &
        (df_farms["Fur Industry Sector"] == "Farming") &
        (df_farms["Species"] == "All Species")
    ]
    
    # Ensure numerical stability
    farms_2024_rows["Number of Farms"] = pd.to_numeric(farms_2024_rows["Number of Farms"], errors='coerce').fillna(0)
    total_farms_EU_2024 = farms_2024_rows["Number of Farms"].sum()

    # C. Calculate Coefficient (Land Occupation per Farm)
    if total_farms_EU_2024 > 0:
        agricultural_land_occupation_per_farm = total_agricultural_land_occupation / total_farms_EU_2024
    else:
        agricultural_land_occupation_per_farm = 0
        
    # print(f"[INFO] Land Occ. Coeff: {agricultural_land_occupation_per_farm:.6f} km2/farm "
    #       f"(Based on {total_agricultural_land_occupation} km2 / {total_farms_EU_2024} farms)")

    # ---------------------------------------------------------
    # 3. Generate Projections (2010 - 2040)
    # ---------------------------------------------------------
    projection_rows = []
    
    # We iterate through the existing Farm Projections (which cover 2010-2040 and all MS)
    # We filter for the "Farming" sector to get the farm count
    target_farm_data = df_farms[
        (df_farms["Fur Industry Sector"] == "Farming") &
        (df_farms["Species"] == "All Species")
    ]

    for _, row in target_farm_data.iterrows():
        country = row["Country"]
        year = row["Year"]
        n_farms = pd.to_numeric(row["Number of Farms"], errors='coerce') or 0
        
        # Skip "European Union" aggregate rows if they exist in the farm file 
        # (we build country-level data first)
        if country == "European Union":
            continue

        # CALCULATION: Apply the coefficient
        projected_land_value = n_farms * agricultural_land_occupation_per_farm
        
        # Create output row matching the input file structure
        projection_rows.append({
            "Country": country,
            "Environmental Metric": "Agricultural land occupation",
            "Species": "All Species",
            "Fur Industry Sector": "Farming",  # Attributed to the farming activity
            "Value": projected_land_value,
            "Metric Unit": "km2",
            "Year": year
        })

    # ---------------------------------------------------------
    # 4. Format Output
    # ---------------------------------------------------------
    df_projection = pd.DataFrame(projection_rows)
    
    # Define required column order matching the screenshot
    output_headers = [
        "Country", 
        "Environmental Metric", 
        "Species", 
        "Fur Industry Sector", 
        "Value", 
        "Metric Unit", 
        "Year"
    ]
    
    return df_projection[output_headers]


def make_figures_S1(df_proj):
    """
    Generates figures for Agricultural Land Occupation.
    1. Per Member State (km2 over time)
    2. EU-27 Aggregate (km2 over time)
    """
    if df_proj.empty:
        return

    Theme.apply_global()
    output_figures_dir = OUTPUT_BASE_DIR / "figures"
    output_figures_dir.mkdir(parents=True, exist_ok=True)

    # Filter strictly for the data we just generated
    df_plot = df_proj[
        (df_proj["Environmental Metric"] == "Agricultural land occupation") &
        (df_proj["Species"] == "All Species")
    ]

    # ---------------------------------------------------------
    # 1. Per Member State Plots
    # ---------------------------------------------------------
    countries = df_plot["Country"].unique()
    
    for country in countries:
        ms_data = df_plot[df_plot["Country"] == country].sort_values("Year")
        
        # Only plot if there is non-zero data after 2024
        future_data = ms_data[ms_data["Year"] > 2024]
        if future_data.empty or (future_data["Value"] <= 0).all():
            continue

        fig, ax = plt.subplots()
        
        ax.plot(
            ms_data["Year"], 
            ms_data["Value"], 
            label="All Species",
            color=Theme.COLORS["All Species"]
        )

        ax.set_title(f"Projected Agricultural Land Occupation of Fur Farming in {country} (in km2)")
        ax.set_xlabel("Year")
        ax.set_ylabel("Agricultural Land Occupation (km2)")
        
        # Format Y-axis with commas
        ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.1f}'))
        ax.legend(loc="upper right")
        
        plt.savefig(output_figures_dir / f"ID28_AgriculturalLandOccupation_{country}.png")
        plt.close(fig)

    # ---------------------------------------------------------
    # 2. EU Aggregate Plot
    # ---------------------------------------------------------
    # Sum values across all countries for each year
    eu_total = df_plot.groupby("Year", as_index=False)["Value"].sum()
    
    if not eu_total.empty:
        fig_eu, ax_eu = plt.subplots()
        
        ax_eu.plot(
            eu_total["Year"], 
            eu_total["Value"], 
            label="EU-27 Total",
            color=Theme.COLORS["All Species"]
        )
        
        ax_eu.set_title("Projected Agricultural Land Occupation of Fur Farming in EU (All Species)")
        ax_eu.set_xlabel("Year")
        ax_eu.set_ylabel("Agricultural Land Occupation (km2)")
        
        # Format Y-axis with commas
        ax_eu.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        ax_eu.legend(loc="upper right")
        
        plt.savefig(output_figures_dir / "ID28_AgriculturalLandOccupation_EU_Total.png")
        plt.close(fig_eu)