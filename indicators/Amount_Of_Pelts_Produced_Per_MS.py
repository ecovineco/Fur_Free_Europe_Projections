import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def run_projection_S1(df):
    """Calculates historical and projected pelt production per Member State and species.

    This function processes historical data (2010–2024) and applies specific 
    legal phase-out or market-driven rules to project production until 2040.

    Args:
        df (pd.DataFrame): Historical data with columns:
            ["Country", "Year", "Species", "Produced_Pelts_Number"].

    Returns:
        pd.DataFrame: A combined DataFrame of historical and projected data (2010–2040)
            with columns ["MS", "Species", "Year", "Pelts"].
    """
    if df.empty:
        return pd.DataFrame(columns=['MS', 'Species', 'Year', 'Pelts'])

    # --- 1. Data Cleaning and Preparation ---
    pelts_data = df.rename(columns={"Country": "MS", "Produced_Pelts_Number": "Pelts"})
    pelts_data["Year"] = pelts_data["Year"].astype(int)
    pelts_data["Pelts"] = pd.to_numeric(pelts_data["Pelts"], errors='coerce').fillna(0)
    
    # Filter out aggregate rows and keep only individual species
    pelts_data = pelts_data[pelts_data["Species"] != "All species"][['MS', 'Year', 'Species', 'Pelts']]

    # Ensure a complete grid for 2010–2024 (filling missing observations with 0)
    historical_years = np.arange(2010, 2025)
    member_states = pelts_data['MS'].unique()
    species_list = pelts_data['Species'].unique()
    
    complete_historical_records = []
    for ms in member_states:
        for species in species_list:
            subset = pelts_data[(pelts_data['MS'] == ms) & (pelts_data['Species'] == species)]
            for year in historical_years:
                # Extract value if year exists, otherwise default to 0
                val = subset.loc[subset['Year'] == year, 'Pelts'].iloc[0] if year in subset['Year'].values else 0
                complete_historical_records.append({'MS': ms, 'Species': species, 'Year': year, 'Pelts': val})
    
    historical_df = pd.DataFrame(complete_historical_records)

    # --- 2. Projection Logic ---
    def apply_projection_rules(group_df):
        """Applies MS-specific legal bans or CAGR trends to a single MS/Species group."""
        group_df = group_df.sort_values('Year')
        ms_name = group_df['MS'].iloc[0]
        species_name = group_df['Species'].iloc[0]
        last_observed_pelt_count = group_df['Pelts'].iloc[-1]
        projection_years = np.arange(2025, 2041)

        # A: Check for existing zero production
        if last_observed_pelt_count <= 0:
            projected_values = np.zeros_like(projection_years)

        # B: Lithuania (LT) - Phase out by 2027
        elif ms_name == "Lithuania" and species_name in ["mink", "chinchilla"]:
            base_val = group_df.loc[group_df['Year'] == 2024, 'Pelts'].iloc[0] if 2024 in group_df['Year'].values else last_observed_pelt_count
            projected_values = np.array([base_val, 0.5 * base_val] + [0] * (len(projection_years) - 2))

        # C: Latvia (LV) - Phase out by 2028
        elif ms_name == "Latvia" and species_name == "mink":
            base_val = group_df.loc[group_df['Year'] == 2024, 'Pelts'].iloc[0] if 2024 in group_df['Year'].values else last_observed_pelt_count
            projected_values = np.array([base_val, (2/3) * base_val, (1/3) * base_val] + [0] * (len(projection_years) - 3))
        elif ms_name == "Latvia" and species_name != "mink":
            projected_values = np.zeros_like(projection_years)

        # D: Romania (RO) - Phase out by 2027
        elif ms_name == "Romania" and species_name in ["mink", "chinchilla"]:
            base_val = group_df.loc[group_df['Year'] == 2024, 'Pelts'].iloc[0] if 2024 in group_df['Year'].values else last_observed_pelt_count
            projected_values = np.array([base_val, 0.5 * base_val] + [0] * (len(projection_years) - 2))

        # E: Poland (PL) - 8-year linear phase-out ending 2033
        elif ms_name == "Poland":
            base_val = group_df.loc[group_df['Year'] == 2024, 'Pelts'].iloc[0] if 2024 in group_df['Year'].values else last_observed_pelt_count
            PHASE_OUT_START, PHASE_OUT_END = 2026, 2033
            DURATION = PHASE_OUT_END - PHASE_OUT_START + 1
            annual_reduction_step = base_val / DURATION
            
            projected_values = []
            for year in projection_years:
                if year == 2025:
                    projected_values.append(base_val)
                elif PHASE_OUT_START <= year <= PHASE_OUT_END:
                    reduction = annual_reduction_step * (year - 2025)
                    projected_values.append(max(base_val - reduction, 0))
                else: # year > 2033
                    projected_values.append(0)
            projected_values = np.array(projected_values)

        # F: Market-driven CAGR for all other MS (Group C)
        else:
            active_years = group_df[group_df['Pelts'] > 0]
            if len(active_years) < 2:
                projected_values = np.full_like(projection_years, last_observed_pelt_count, dtype=float)
            else:
                start_yr, end_yr = active_years['Year'].iloc[0], active_years['Year'].iloc[-1]
                val_start, val_end = active_years['Pelts'].iloc[0], active_years['Pelts'].iloc[-1]
                
                # Compound Annual Growth Rate
                cagr = (val_end / val_start)**(1 / (end_yr - start_yr)) - 1
                # Cap the trend: maximum 20% decline, no growth allowed
                clamped_rate = max(min(cagr, 0.0), -0.2)
                
                projected_values = np.array([last_observed_pelt_count * (1 + clamped_rate)**(yr - 2024) for yr in projection_years])

        future_df = pd.DataFrame({
            'MS': ms_name, 
            'Species': species_name, 
            'Year': projection_years, 
            'Pelts': projected_values
        })
        return pd.concat([group_df, future_df], ignore_index=True)

    # Apply projection logic per group
    final_projection = historical_df.groupby(['MS', 'Species'], group_keys=False).apply(apply_projection_rules).reset_index(drop=True)
    return final_projection

def make_figures_S1(df_proj):
    """Generates visualization charts for pelt production by country and EU total.

    Creates PNG charts for each Member State and one aggregate EU chart.
    Y-axis values are normalized to thousands for readability. Plots are only
    generated if there is non-zero production projected after 2024.

    Args:
        df_proj (pd.DataFrame): The combined historical and projected dataset.
    """
    if df_proj.empty:
        return

    output_dir = Path("data/output/S1_output/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Standardized color palette for species consistency
    SPECIES_COLORS = {
        "Mink": "#1f77b4",
        "Chinchilla": "#ff7f0e",
        "Raccoon dog": "#2ca02c",
        "Fox": "#d62728",
        "All species": "#9467bd"
    }

    # --- 1. Generate Individual Member State Plots ---
    for ms in df_proj['MS'].unique():
        ms_data = df_proj[df_proj['MS'] == ms].groupby(['Year', 'Species'], as_index=False)['Pelts'].sum()
        
        # Filtering logic: Only plot if at least one species has production > 0 after 2024
        post_2024_data = ms_data[ms_data['Year'] > 2024]
        if post_2024_data['Pelts'].sum() <= 0:
            continue

        pivot_data = ms_data.pivot(index='Year', columns='Species', values='Pelts').fillna(0)
        
        fig, ax = plt.subplots()
        for species in pivot_data.columns:
            if pivot_data[species].sum() > 0:
                # Plotting values in thousands
                ax.plot(
                    pivot_data.index, 
                    pivot_data[species] / 1000, 
                    label=species, 
                    color=SPECIES_COLORS.get(species, "#1f77b4")
                )

        ax.set_title(f"Total Pelt Production in {ms} (in Thousands of Pelts)") 
        ax.set_xlabel("Year")
        ax.set_ylabel("Number of Pelts (Thousands)")
        ax.legend()
        ax.grid(True, linestyle="--", linewidth=0.5)

        fig.tight_layout()
        fig.savefig(output_dir / f"Amount_Of_Pelts_Produced_Per_{ms}_per_species.png")
        plt.close(fig)

    # --- 2. Generate Aggregate EU Total Plot ---
    eu_totals = df_proj.groupby(['Year', 'Species'], as_index=False)['Pelts'].sum()
    
    # Only generate EU plot if there is projected production post-2024
    if eu_totals[eu_totals['Year'] > 2024]['Pelts'].sum() > 0:
        eu_pivot = eu_totals.pivot(index='Year', columns='Species', values='Pelts').fillna(0)

        fig, ax = plt.subplots()
        for species in eu_pivot.columns:
            if eu_pivot[species].sum() > 0:
                # Plotting values in thousands
                ax.plot(
                    eu_pivot.index, 
                    eu_pivot[species] / 1000, 
                    label=species, 
                    color=SPECIES_COLORS.get(species, "#1f77b4")
                )

        ax.set_title("Total Pelt Production in EU (in Thousands of Pelts)")
        ax.set_xlabel("Year")
        ax.set_ylabel("Number of Pelts (Thousands)")
        ax.legend()
        ax.grid(True, linestyle="--", linewidth=0.5)

        fig.tight_layout()
        fig.savefig(output_dir / "Amount_Of_Pelts_Produced_Per_MS_EU_total_per_species.png")
        plt.close(fig)