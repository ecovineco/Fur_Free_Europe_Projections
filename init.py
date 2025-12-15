import pandas as pd
from pathlib import Path

# -----------------------------
# Configuration
# -----------------------------
scenario = "S0"

indicators_list = [
    "Fur_EU_Industry_Cost_Account", "Amount_Of_Pelts_Produced_Per_MS",
    "Amount_Fur_Companies_Per_MS", "ID2", "ID3", "ID4", "ID5",
    "ID7", "ID9", "ID10", "ID11", "ID14", "ID15", "ID16",
    "ID19", "ID22", "ID25", "ID26", "ID27", "ID28"
]

# -----------------------------
# Paths
# -----------------------------
data_folder = Path("data")
output_folder = data_folder / "output" / f"{scenario}_output"
figures_folder = output_folder / "figures"
output_file = output_folder / "projected_data.xlsx"

indicators_folder = Path("indicators")

# -----------------------------
# 1. Create indicator .py files
# -----------------------------
def create_indicator_files():
    indicators_folder.mkdir(exist_ok=True)

    for indicator in indicators_list:
        file_path = indicators_folder / f"{indicator}.py"

        if file_path.exists():
            print(f"[INFO] Indicator file exists: {file_path}")
            continue

        file_path.write_text(
            f'''"""
Indicator: {indicator}
Scenario: {scenario}
"""

def run_projection_{scenario}(df):
    """
    Generate projection data for indicator {indicator}
    """
    # TODO: implement projection logic
    return df


def make_figures_{scenario}(df, theme=None):
    """
    Create figures for indicator {indicator}
    """
    # TODO: implement figures using df and theme
    pass
'''
        )
        print(f"[INFO] Created indicator file: {file_path}")

# -----------------------------
# 2. Create output folders
# -----------------------------
def create_output_folders():
    output_folder.mkdir(parents=True, exist_ok=True)
    figures_folder.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Output folder created: {output_folder}")
    print(f"[INFO] Figures folder created: {figures_folder}")

# -----------------------------
# 3. Create empty Excel output
# -----------------------------
def create_empty_output_excel():
    with pd.ExcelWriter(output_file) as writer:
        for indicator in indicators_list:
            pd.DataFrame().to_excel(writer, sheet_name=indicator, index=False)

        pd.DataFrame(
            columns=["Indicator", "Scenario", "Generated", "Timestamp"]
        ).to_excel(writer, sheet_name="projection_log", index=False)

    print(f"[INFO] Empty output Excel created: {output_file}")

# -----------------------------
# Main init
# -----------------------------
def main():
    print("[INFO] Running initialization...")
    create_indicator_files()
    create_output_folders()
    create_empty_output_excel()
    print("[INFO] Initialization complete ✔")

# -----------------------------
# Run init
# -----------------------------
if __name__ == "__main__":
    main()
