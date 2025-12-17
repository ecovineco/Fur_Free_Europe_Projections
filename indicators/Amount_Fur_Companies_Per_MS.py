import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from figure_theme import Theme

# -----------------------------
# Configuration Constants
# -----------------------------
# Derived from report: 44,700 ha / 4,700 farms in 2025 (approx 9.51 ha/farm)
AREA_PER_FARM_HA = 9.51 

def run_projection_S1(df):
    """
    Projects the number of Fur Farms and Farm Area based on production trends.
    
    Methodology:
    1. Farms(t) evolves proportionally to Production(t) relative to 2024.
    2. Farm Area(t) = Farms(t) * Average Area Per Farm (9.51 ha).

    Args:
        df (pd.DataFrame): Input data with columns:
            ["Country", "Fur Industry Sector", "Species", "Year", "Number of Farms", "Source"]

    Returns:
        pd.DataFrame: Projected data with columns:
            ["MS", "Species", "Year", "Farms", "Farm Area (ha)"]
    """
    # -----------------------------
    # 1. Load and Prepare Input Data
    # -----------------------------
    if df.empty:
        return pd.DataFrame()

    # Filter for specific sector and species as requested
    df = df[
        (df["Fur Industry Sector"] == "Fur Farming") & 
        (df["Species"] == "All species")
    ].copy()

    # Rename columns for consistency
    farms_hist = df.rename(columns={
        "Country": "MS", 
        "Number of Farms": "Farms"
    })[["MS", "Species", "Year", "Farms"]]

    # Ensure numeric types
    farms_hist["Year"] = farms_hist["Year"].astype(int)
    farms_hist["Farms"] = pd.to_numeric(farms_hist["Farms"], errors="coerce").fillna(0)

    # Calculate Historical Area
    farms_hist["Farm Area (ha)"] = farms_hist["Farms"] * AREA_PER_FARM_HA

    # -----------------------------
    # 2. Load Production Data (Driver)
    # -----------------------------
    # We need the production projections to calculate the trend ratio.
    # Assumes "Amount_Of_Pelts_Produced_Per_MS" has already run.
    prod_file = Path("data/output/S1_output/projected_data.xlsx")
    if not prod_file.exists():
        print(f"[WARNING] Production data not found at {prod_file}. Returning historical farms only.")
        return farms_hist

    try:
        df_prod = pd.read_excel(prod_file, sheet_name="Amount_Of_Pelts_Produced_Per_MS")
    except ValueError:
        print("[WARNING] Sheet 'Amount_Of_Pelts_Produced_Per_MS' not found. Returning historical farms only.")
        return farms_hist

    # Filter production for "All species" to match our farms data
    df_prod = df_prod[df_prod["Species"] == "All species"].copy()

    # -----------------------------
    # 3. Calculate Projections
    # -----------------------------
    projections = []
    
    # Iterate over each Member State present in the input data
    for ms in farms_hist["MS"].unique():
        # A. Get Baseline Farm Data (2024)
        ms_farms = farms_hist[farms_hist["MS"] == ms]
        if 2024 in ms_farms["Year"].values:
            base_farms_2024 = ms_farms.loc[ms_farms["Year"] == 2024, "Farms"].iloc[0]
        else:
            # If 2024 is missing, use the last available year
            base_farms_2024 = ms_farms.sort_values("Year")["Farms"].iloc[-1]

        # B. Get Production Trend Data for this MS
        ms_prod = df_prod[df_prod["MS"] == ms].sort_values("Year")
        
        if ms_prod.empty or 2024 not in ms_prod["Year"].values:
            # If no production data, assume 0 for future or flat? 
            # Report implies proportional to production, so no production = no farms.
            base_prod_2024 = 0
        else:
            base_prod_2024 = ms_prod.loc[ms_prod["Year"] == 2024, "Pelts"].iloc[0]

        # C. Project 2025-2040
        future_years = np.arange(2025, 2041)
        
        for year in future_years:
            # Get production for year t
            prod_t = ms_prod.loc[ms_prod["Year"] == year, "Pelts"].sum() if year in ms_prod["Year"].values else 0
            
            # Apply Formula: Farms_t = Farms_2024 * (Prod_t / Prod_2024)
            if base_prod_2024 > 0:
                ratio = prod_t / base_prod_2024
                farms_t = base_farms_2024 * ratio
            else:
                farms_t = 0
            
            # Calculate Land Use: Area_t = Farms_t * AreaPerFarm
            area_t = farms_t * AREA_PER_FARM_HA

            projections.append({
                "MS": ms,
                "Species": "All species",
                "Year": year,
                "Farms": farms_t,
                "Farm Area (ha)": area_t
            })

    # Combine History and Projections
    df_proj = pd.DataFrame(projections)
    final_df = pd.concat([farms_hist, df_proj], ignore_index=True).sort_values(["MS", "Year"])
    
    return final_df


def make_figures_S1(df_proj):
    """
    Generates plots for Number of Farms and Farm Area (ha).
    
    Outputs:
    1. Per MS: Farms and Area (only if >0 after 2025).
    2. EU Total: Farms and Area.
    """
    if df_proj.empty:
        return

    output_dir = Path("data/output/S1_output/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Color for "All species"
    COLOR_ALL_SPECIES = "#9467bd" 

    # -----------------------------
    # 1. Plots Per Member State
    # -----------------------------
    for ms in df_proj["MS"].unique():
        ms_data = df_proj[df_proj["MS"] == ms].sort_values("Year")
        
        # Check if relevant: Production/Farms > 0 after 2025
        post_2025 = ms_data[ms_data["Year"] > 2025]
        if post_2025["Farms"].sum() <= 0:
            continue

        # Plot A: Number of Farms
        fig, ax = plt.subplots()
        # Divide by 1000 for "in thousands" if needed, but farms are often small numbers.
        # However, to be consistent with requested style "in thousands":
        ax.plot(ms_data["Year"], ms_data["Farms"] / 1000, color=COLOR_ALL_SPECIES, label="All species")
        
        ax.set_title(f"Number of Farms: {ms} (in thousands)")
        ax.set_ylabel("Farms (Thousands)")
        ax.set_xlabel("Year")
        ax.legend()
        fig.tight_layout()
        fig.savefig(output_dir / f"Amount_Fur_Farms_{ms}.png")
        plt.close(fig)

        # Plot B: Farm Area
        fig, ax = plt.subplots()
        ax.plot(ms_data["Year"], ms_data["Farm Area (ha)"] / 1000, color=COLOR_ALL_SPECIES, label="All species")
        
        ax.set_title(f"Farm Area: {ms} (in thousands ha)")
        ax.set_ylabel("Area (Thousands ha)")
        ax.set_xlabel("Year")
        ax.legend()
        fig.tight_layout()
        fig.savefig(output_dir / f"Amount_Fur_Farm_Area_{ms}.png")
        plt.close(fig)

    # -----------------------------
    # 2. Plots for EU Total
    # -----------------------------
    eu_data = df_proj.groupby("Year")[["Farms", "Farm Area (ha)"]].sum().reset_index()

    # Plot A: EU Total Farms
    fig, ax = plt.subplots()
    ax.plot(eu_data["Year"], eu_data["Farms"] / 1000, color=COLOR_ALL_SPECIES, label="All species")
    
    ax.set_title("Total EU Number of Farms (in thousands)")
    ax.set_ylabel("Farms (Thousands)")
    ax.set_xlabel("Year")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "Amount_Fur_Farms_EU_Total.png")
    plt.close(fig)

    # Plot B: EU Total Area
    fig, ax = plt.subplots()
    ax.plot(eu_data["Year"], eu_data["Farm Area (ha)"] / 1000, color=COLOR_ALL_SPECIES, label="All species")
    
    ax.set_title("Total EU Farm Area (in thousands ha)")
    ax.set_ylabel("Area (Thousands ha)")
    ax.set_xlabel("Year")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "Amount_Fur_Farm_Area_EU_Total.png")
    plt.close(fig)