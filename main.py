import pandas as pd
from pathlib import Path
from datetime import datetime
import importlib
from figure_theme import Theme

# -----------------------------
# Configuration
# -----------------------------
scenario = "S0"
override_previous_projection = False

# Folder paths
output_folder = Path(f"output/{scenario}_output")
output_file = output_folder / "projected_data.xlsx"
figures_folder = output_folder / "figures"

theme = Theme()

# -----------------------------
# Function: load input data
# -----------------------------
def load_input_data(input_file, indicators):
    xls = pd.ExcelFile(input_file)
    return {sheet: xls.parse(sheet) for sheet in xls.sheet_names if sheet in indicators}

# -----------------------------
# Function: load or initialize output
# -----------------------------
def load_or_initialize_output(output_file):
    if output_file.exists():
        xls = pd.ExcelFile(output_file)
        projected_data = {sheet: xls.parse(sheet) for sheet in xls.sheet_names if sheet != "projection_log"}
        projection_log = xls.parse("projection_log") if "projection_log" in xls.sheet_names else pd.DataFrame(columns=["Indicator","Scenario","Generated","Timestamp"])
    else:
        projected_data = {}
        projection_log = pd.DataFrame(columns=["Indicator","Scenario","Generated","Timestamp"])
    return projected_data, projection_log

# -----------------------------
# Function: run projection & figures for one indicator
# -----------------------------
def run_projections_for_indicator(indicator, input_data, projected_data, projection_log, scenario, figures_folder, override, theme):
    try:
        mod = importlib.import_module(f"indicators.{indicator}")
    except ModuleNotFoundError:
        print(f"[WARNING] Module for {indicator} not found, skipping")
        return projected_data, projection_log

    already_generated = (indicator in projected_data) and (scenario in projection_log.query("Indicator == @indicator")["Scenario"].values if not projection_log.empty else False)

    if already_generated and not override:
        print(f"[INFO] Skipping {indicator}, projections already exist")
        df_proj = projected_data.get(indicator)
    else:
        run_func_name = f"run_projection_{scenario}"
        if hasattr(mod, run_func_name):
            df_proj = getattr(mod, run_func_name)(input_data.get(indicator, pd.DataFrame()))
            projected_data[indicator] = df_proj
            # Update projection log
            projection_log = projection_log[~((projection_log["Indicator"]==indicator) & (projection_log["Scenario"]==scenario))]
            projection_log = pd.concat([projection_log, pd.DataFrame({
                "Indicator": [indicator],
                "Scenario": [scenario],
                "Generated": [True],
                "Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            })], ignore_index=True)
        else:
            print(f"[INFO] Projection function for {indicator} {scenario} not implemented")
            return projected_data, projection_log

    # Run figure function
    fig_func_name = f"make_figures_{scenario}"
    if hasattr(mod, fig_func_name):
        getattr(mod, fig_func_name)(df_proj, theme=theme)

    return projected_data, projection_log

# -----------------------------
# Function: save projected data to Excel
# -----------------------------
def save_projected_data(projected_data, projection_log, output_file):
    with pd.ExcelWriter(output_file) as writer:
        for sheet_name, df in projected_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        projection_log.to_excel(writer, sheet_name="projection_log", index=False)

# -----------------------------
# Main function
# -----------------------------
def main(indicators_list, input_file):
    # Step 1: load input
    input_data = load_input_data(input_file, indicators_list)

    # Step 2: load or initialize output
    projected_data, projection_log = load_or_initialize_output(output_file)

    # Step 3: run projections and figures
    for indicator in indicators_list:
        projected_data, projection_log = run_projections_for_indicator(
            indicator, input_data, projected_data, projection_log,
            scenario, figures_folder, override_previous_projection, theme
        )

    # Step 4: save results
    save_projected_data(projected_data, projection_log, output_file)
    print(f"[INFO] Finished S0 projections. Data saved to {output_file}, figures to {figures_folder}/")

# -----------------------------
# Run main
# -----------------------------
if __name__ == "__main__":
    # Example usage:
    # Replace with the indicators you want to run projections for
    example_indicators = [
        "Fur_EU_Industry_Cost_Account", "Amount_Of_Pelts_Produced_Per_MS",
        "Amount_Fur_Companies_Per_MS", "ID2", "ID3", "ID4"
    ]
    main(example_indicators, input_file="data/input.xlsx")
