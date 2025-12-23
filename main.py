import pandas as pd
from pathlib import Path
from datetime import datetime
import importlib

from figure_theme import Theme

# -----------------------------
# Configuration
# -----------------------------
scenario = "S1"
overwrite_previous_projection = True

# Paths
data_folder = Path("data")
input_file = data_folder / "input" / "input.xlsx"
output_folder = data_folder / "output" / f"{scenario}_output"
output_file = output_folder / "projected_data.xlsx"
figures_folder = output_folder / "figures"

theme = Theme()
Theme.apply_global()
# -----------------------------
# Functions
# -----------------------------
def load_projection_log(output_file):
    """Load projection log from Excel or create empty if not exists"""
    if output_file.exists():
        xls = pd.ExcelFile(output_file)
        if "projection_log" in xls.sheet_names:
            return xls.parse("projection_log")
    return pd.DataFrame(columns=["Indicator", "Scenario", "Generated", "Timestamp"])

def load_input_for_indicator(indicator):
    """Load input sheet for a single indicator"""
    try:
        return pd.read_excel(input_file, sheet_name=indicator)
    except ValueError:
        print(f"[WARNING] No input sheet for {indicator}, using empty DataFrame")
        return pd.DataFrame()

def run_projection(indicator, input_df, projection_log):
    """Run the projection function for one indicator"""
    try:
        mod = importlib.import_module(f"indicators.{indicator}")
    except ModuleNotFoundError:
        print(f"[WARNING] Module not found for {indicator}, skipping")
        return pd.DataFrame(), projection_log

    already_generated = (
        not projection_log.empty
        and ((projection_log["Indicator"] == indicator) & 
             (projection_log["Scenario"] == scenario)).any()
    )

    df_proj = pd.DataFrame()
    if already_generated and not overwrite_previous_projection:
        print(f"[INFO] Skipping projection for {indicator}: already in log")
        # Load existing projection
        if output_file.exists():
            try:
                df_proj = pd.read_excel(output_file, sheet_name=indicator)
            except ValueError:
                df_proj = pd.DataFrame()
    else:
        run_func_name = f"run_projection_{scenario}"
        if hasattr(mod, run_func_name):
            df_proj = getattr(mod, run_func_name)(input_df)
            print(f"[INFO] Projection completed for {indicator}")
        else:
            print(f"[INFO] No projection function for {indicator} ({scenario}), skipping")
            return pd.DataFrame(), projection_log

        # Update projection log
        projection_log = projection_log[
            ~((projection_log["Indicator"] == indicator) & 
              (projection_log["Scenario"] == scenario))
        ]
        projection_log = pd.concat(
            [
                projection_log,
                pd.DataFrame({
                    "Indicator": [indicator],
                    "Scenario": [scenario],
                    "Generated": [True],
                    "Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                })
            ],
            ignore_index=True
        )

    return df_proj, projection_log

def save_projection_and_log(indicator, df_proj, projection_log):
    """Save one indicator's projection and updated log to Excel"""
    if isinstance(df_proj, tuple):
        # unpack if accidentally returned as tuple
        df_proj = df_proj[0]

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_file, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df_proj.to_excel(writer, sheet_name=indicator, index=False)
        projection_log.to_excel(writer, sheet_name="projection_log", index=False)



def generate_figures(indicator, df_proj, projection_log):
    """Generate figures for one indicator if projection exists in log"""
    try:
        mod = importlib.import_module(f"indicators.{indicator}")
    except ModuleNotFoundError:
        print(f"[WARNING] Module not found for {indicator}, skipping figures")
        return

    if ((projection_log["Indicator"] == indicator) & 
        (projection_log["Scenario"] == scenario)).any():

        fig_func_name = f"make_figures_{scenario}"
        if hasattr(mod, fig_func_name):
            getattr(mod, fig_func_name)(df_proj)
            print(f"[INFO] Figures generated for {indicator}")

# -----------------------------
# Workflow function
# -----------------------------
def run_scenario_projections(
    indicators,
    do_projection=True,
    do_figures=True
):
    """Run projections and/or figures for a list of indicators"""
    projection_log = load_projection_log(output_file)

    for indicator in indicators:
        # 1. Load input
        input_df = load_input_for_indicator(indicator)

        df_proj = pd.DataFrame()
        if do_projection:
            # 2. Run projection
            df_proj, projection_log = run_projection(indicator, input_df, projection_log)
            # 3. Save projection and log immediately
            save_projection_and_log(indicator, df_proj, projection_log)
        else:
            # Load existing projection for figures
            if output_file.exists():
                try:
                    df_proj = pd.read_excel(output_file, sheet_name=indicator)
                except ValueError:
                    df_proj = pd.DataFrame()

        if do_figures:
            # 4. Generate figures
            generate_figures(indicator, df_proj, projection_log)

    print(f"[INFO] Finished {scenario} workflow\nData: {output_file}\nFigures: {figures_folder}/")

# -----------------------------
# Run example
# -----------------------------
if __name__ == "__main__":
    # Process only "Amount_Of_Pelts_Produced_Per_MS"
    indicators_of_interest = [
        "Amount_Of_Pelts_Produced_Per_MS", "Amount_Fur_Companies_Per_MS", "ID28", "ID19", "ID25", "ID26", "ID27"
    ]
    
    # Set to True to perform both projection and figures generation
    run_scenario_projections(indicators_of_interest, do_projection=True, do_figures=True)

