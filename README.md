# Fur Free Europe Projections

## 1. Introduction
This project generates **economic, environmental, and social projections** for the fur market across various indicators and EU Member States. It is designed to be modular, supporting multi-scenario projections (currently focused on **Scenario S1**) and consistent visual output.

The project is implemented in **Python** and handles:
- Automated project initialization and stub generation.
- Data loading from multi-tab Excel workbooks.
- Indicator-specific projection logic (e.g., CAGR, market-specific phase-outs).
- Standardized figure generation using a centralized theme.

---

## 2. File Structure
The project follows a strict directory hierarchy to ensure modularity:
```bash
project_root/
│
├── data/
│   ├── input/
│   │   └── input.xlsx               # Source data (one tab per indicator)
│   └── output/
│       └── S1_output/               # Results for Scenario S1
│           ├── projected_data.xlsx  # Combined historical + projected data
│           └── figures/             # Generated charts and visualizations
│
├── indicators/                      # Indicator-specific logic
│   ├── Amount_Of_Pelts_Produced_Per_MS.py
│   ├── ID2.py
│   └── ... (20+ indicators)
│
├── figure_theme.py                  # Global matplotlib styling
├── init.py                          # Environment setup script
├── main.py                          # Primary execution workflow
└── README.md                        # Documentation
```
---

## 3. Getting Started: `init.py`
The `init.py` script initializes the project environment. It performs the following tasks:
1. Creates the `indicators/` folder and generates **Scenario S0 stub files** (Note: these should be updated to S1 to match the current workflow).
2. Sets up the output directory structure for the configured scenario.
3. Generates an empty `projected_data.xlsx` file with tabs for all listed indicators and a `projection_log`.

**Usage:**
[PLACEHOLDER: INIT_USAGE]

---

## 4. Main Workflow: `main.py`
The `main.py` script is the primary entry point for running projections. It manages:
- **Data Loading:** Reads input from `data/input/input.xlsx`.
- **Projection Execution:** Dynamically imports indicator modules and runs scenario-specific projection functions.
- **Result Persistence:** Saves projected data to Excel and maintains a `projection_log` to track runs.
- **Visualization:** Calls figure generation functions using the global `Theme`.

**Configuration:**
Users can toggle `overwrite_previous_projection` and specify which indicators to process in the `if __name__ == "__main__":` block.

---

## 5. Global Styling: `figure_theme.py`
To ensure all charts are consistent, the `Theme` class centralizes matplotlib parameters:
- Standardized figure sizes and font sizes for titles, labels, and legends.
- Predefined color palettes and line styles.
- A `apply_global()` method to inject these settings into the active session.

---

## 6. High-Level Workflow
1. **Initialize:** Run `init.py` to set up folders and stubs.
2. **Populate Input:** Place your raw data in `data/input/input.xlsx`.
3. **Execute:** Run `main.py` to generate projections and figures.
4. **Review:** Check `data/output/S1_output/` for the final Excel report and chart images.