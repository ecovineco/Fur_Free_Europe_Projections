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

output_folder = Path(f"output/{scenario}_output")
figures_folder = output_folder / "figures"
output_file = output_folder / "projected_data.xlsx"

# -----------------------------
# 1. Create folders
# -----------------------------
def create_folders():
    output_folder.mkdir(parents=True, exist_ok=True)
    figures_folder.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Folders created: {output_folder}, {figures_folder}")

# -----------------------------
# 2. Create empty Excel file
# -----------------------------
def create_empty_excel(indicators, file_path):
    with pd.ExcelWriter(file_path) as writer:
        for indicator in indicators:
            pd.DataFrame().to_excel(writer, sheet_name=indicator, index=False)
        pd.DataFrame(columns=["Indicator","Scenario","Generated","Timestamp"]).to_excel(writer, sheet_name="projection_log", index=False)
    print(f"[INFO] Empty Excel created at {file_path}")

# -----------------------------
# 3. Create indicator .py files
# -----------------------------
def create_indicator_files(indicators, folder="indicators"):
    folder_path = Path(folder)
    folder_path.mkdir(exist_ok=True)
    for indicator in indicators:
        file_path = folder_path / f"{indicator}.py"
        if not file_path.exists():
            file_path.write_text(
                f"""\"\"\"
Python file for indicator: {indicator}
Contains two public functions for scenario {scenario}:
- run_projection_{scenario}(df)
- make_figures_{scenario}(df, theme)
\"\"\"

def run_projection_{scenario}(df):
    # TODO: implement projection
    return df

def make_figures_{scenario}(df, theme=None):
    # TODO: implement figures using df and theme
    pass
"""
            )
            print(f"[INFO] Created {file_path}")
        else:
            print(f"[INFO] File already exists: {file_path}")

# -----------------------------
# 4. Main initialization
# -----------------------------
def main():
    create_folders()
    create_empty_excel(indicators_list, output_file)
    create_indicator_files(indicators_list)
    print("[INFO] Initialization complete!")

# -----------------------------
# Run initialization
# -----------------------------
if __name__ == "__main__":
    main()
