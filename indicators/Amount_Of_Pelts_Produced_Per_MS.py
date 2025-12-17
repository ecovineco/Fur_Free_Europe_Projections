import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# -----------------------------
# Projection function for scenario S1
# -----------------------------
def run_projection_S1(df):
    """
    Perform historical + projected pelts per Member State (MS) and species.

    Args:
        df (pd.DataFrame): Historical data with columns ["Country", "Year", "Species", "Produced_Pelts_Number"]

    Returns:
        pelts_proj (pd.DataFrame): Historical + projected data (2010–2040)
    """
    if df.empty:
        return pd.DataFrame(columns=['MS','Species','Year','Pelts'])

    # -----------------------------
    # 1. Prepare historical data
    # -----------------------------
    pelts = df.rename(columns={"Country": "MS", "Produced_Pelts_Number": "Pelts"})
    pelts["Year"] = pelts["Year"].astype(int)
    pelts["Pelts"] = pd.to_numeric(pelts["Pelts"], errors='coerce').fillna(0)
    pelts = pelts[pelts["Species"] != "All species"][['MS', 'Year', 'Species', 'Pelts']]

    # Ensure all years 2010–2024 exist per MS × Species (fill missing with 0)
    all_years = np.arange(2010, 2025)
    ms_list = pelts['MS'].unique()
    species_list = pelts['Species'].unique()
    historical_rows = []
    for ms in ms_list:
        for sp in species_list:
            df_sub = pelts[(pelts['MS']==ms) & (pelts['Species']==sp)]
            for y in all_years:
                val = df_sub.loc[df_sub['Year']==y,'Pelts'].iloc[0] if y in df_sub['Year'].values else 0
                historical_rows.append({'MS': ms, 'Species': sp, 'Year': y, 'Pelts': val})
    pelts_hist = pd.DataFrame(historical_rows)

    # -----------------------------
    # 2. Projection per MS × Species
    # -----------------------------
    def project_MS_species(df_MS_s):
        df_MS_s = df_MS_s.sort_values('Year')
        MS_name = df_MS_s['MS'].iloc[0]
        spec = df_MS_s['Species'].iloc[0]
        last_obs_val = df_MS_s['Pelts'].iloc[-1]
        future_years = np.arange(2025, 2041)

        # Country-specific projection rules
        if last_obs_val <= 0:
            future_vals = np.zeros_like(future_years)
        elif MS_name=="Lithuania" and spec in ["mink","chinchilla"]:
            base = df_MS_s.loc[df_MS_s['Year']==2024,'Pelts'].iloc[0] if 2024 in df_MS_s['Year'].values else last_obs_val
            future_vals = np.array([base, 0.5*base] + [0]*(len(future_years)-2))
        elif MS_name=="Latvia" and spec=="mink":
            base = df_MS_s.loc[df_MS_s['Year']==2024,'Pelts'].iloc[0] if 2024 in df_MS_s['Year'].values else last_obs_val
            future_vals = np.array([base, 2/3*base, 1/3*base] + [0]*(len(future_years)-3))
        elif MS_name=="Latvia" and spec!="mink":
            future_vals = np.zeros_like(future_years)
        elif MS_name=="Romania" and spec in ["mink","chinchilla"]:
            base = df_MS_s.loc[df_MS_s['Year']==2024,'Pelts'].iloc[0] if 2024 in df_MS_s['Year'].values else last_obs_val
            future_vals = np.array([base, 0.5*base] + [0]*(len(future_years)-2))
        elif MS_name=="Poland":
            base = df_MS_s.loc[df_MS_s['Year']==2024,'Pelts'].iloc[0] if 2024 in df_MS_s['Year'].values else last_obs_val
            T_start, T_end = 2026, 2033
            D = T_end - T_start + 1
            step = base / D
            future_vals = []
            for y in future_years:
                if y==2025:
                    future_vals.append(base)
                elif T_start <= y <= T_end:
                    future_vals.append(max(base - step*(y-2025),0))
                elif y>T_end:
                    future_vals.append(0)
                else:
                    future_vals.append(base)
            future_vals = np.array(future_vals)
        else:
            # Default market-driven CAGR projection
            nz = df_MS_s[df_MS_s['Pelts']>0]
            if len(nz)<2:
                future_vals = np.full_like(future_years, last_obs_val, dtype=float)
            else:
                first_year, last_year_nz = nz['Year'].iloc[0], nz['Year'].iloc[-1]
                first_val, last_val_nz = nz['Pelts'].iloc[0], nz['Pelts'].iloc[-1]
                r = (last_val_nz/first_val)**(1/(last_year_nz-first_year))-1
                r = max(min(r, 0.0), -0.2)  # Cap decline at -20%, no growth
                future_vals = np.array([last_obs_val*(1+r)**(y-2024) for y in future_years])

        df_future = pd.DataFrame({'MS': MS_name, 'Species': spec, 'Year': future_years, 'Pelts': future_vals})
        return pd.concat([df_MS_s, df_future], ignore_index=True)

    # Apply projections
    pelts_proj = pelts_hist.groupby(['MS','Species'], group_keys=False).apply(project_MS_species).reset_index(drop=True)

    return pelts_proj

def make_figures_S1(df_proj):
    """
    Generate plots per country and EU totals.
    Uses fixed species colors for consistency.
    No log scale.
    """
    if df_proj.empty:
        return

    figures_folder = Path("data/output/S1_output/figures")
    figures_folder.mkdir(parents=True, exist_ok=True)

    # Fixed species colors
    species_colors = {
        "Mink": "#1f77b4",
        "Chinchilla": "#ff7f0e",
        "Raccoon dog": "#2ca02c",
        "Fox": "#d62728",
        "All species": "#9467bd"
    }

    # -----------------------------
    # 1. Per country
    # -----------------------------
    for ms in df_proj['MS'].unique():

        df_ms = df_proj[df_proj['MS'] == ms].groupby(['Year','Species'], as_index=False)['Pelts'].sum()
        df_pivot = df_ms.pivot(index='Year', columns='Species', values='Pelts').fillna(0)
        if df_pivot.sum().sum() == 0:
            continue

        fig, ax = plt.subplots()
        for spec in df_pivot.columns:
            if df_pivot[spec].sum() > 0:
                color = species_colors.get(spec, "#1f77b4")  # default if species not in dict
                ax.plot(df_pivot.index, df_pivot[spec], label=spec, color=color)

        ax.set_title(f"Amount_Of_Pelts_Produced_Per_{ms}_per_species")
        ax.set_xlabel("Year")
        ax.set_ylabel("Number of Pelts")
        ax.legend()
        ax.grid(True, linestyle="--", linewidth=0.5)

        fig.tight_layout()
        fig.savefig(figures_folder / f"Amount_Of_Pelts_Produced_Per_{ms}_per_species.png")
        plt.close(fig)

    # -----------------------------
    # 2. EU totals
    # -----------------------------
    df_eu = df_proj.groupby(['Year','Species'], as_index=False)['Pelts'].sum()
    df_eu_pivot = df_eu.pivot(index='Year', columns='Species', values='Pelts').fillna(0)

    fig, ax = plt.subplots()
    for spec in df_eu_pivot.columns:
        if df_eu_pivot[spec].sum() > 0:
            color = species_colors.get(spec, "#1f77b4")
            ax.plot(df_eu_pivot.index, df_eu_pivot[spec], label=spec, color=color)

    ax.set_title("Amount_Of_Pelts_Produced_Per_MS_EU_total_per_species")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Pelts")
    ax.legend()
    ax.grid(True, linestyle="--", linewidth=0.5)

    fig.tight_layout()
    fig.savefig(figures_folder / "Amount_Of_Pelts_Produced_Per_MS_EU_total_per_species.png")
    plt.close(fig)
