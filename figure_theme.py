# figure_theme.py
import matplotlib.pyplot as plt
from cycler import cycler

class Theme:
    FIG_SIZE = (10, 6)
    TITLE_SIZE = 16
    LABEL_SIZE = 14
    TICK_SIZE = 12
    LEGEND_SIZE = 12
    LINE_WIDTH = 2

    # Define species colors globally here
    COLORS = {
        "Mink": "#1f77b4",
        "Chinchilla": "#ff7f0e",
        "Raccoon dog": "#2ca02c",
        "Fox": "#d62728",
        "All species": "#9467bd",  # not used in per-country plots
        "default": "#1f77b4"
    }

    @staticmethod
    def apply_global():
        """
        Apply global styling: figure size, font sizes, grid, line width,
        and species-specific colors that are automatically used in plots.
        """
        # Create a color cycle that repeats species colors in a fixed order
        species_order = ["Mink", "Chinchilla", "Raccoon dog", "Fox", "All species"]
        color_cycle = [Theme.COLORS.get(s, Theme.COLORS["default"]) for s in species_order]

        plt.rcParams.update({
            "figure.figsize": Theme.FIG_SIZE,
            "axes.titlesize": Theme.TITLE_SIZE,
            "axes.labelsize": Theme.LABEL_SIZE,
            "xtick.labelsize": Theme.TICK_SIZE,
            "ytick.labelsize": Theme.TICK_SIZE,
            "legend.fontsize": Theme.LEGEND_SIZE,
            "lines.linewidth": Theme.LINE_WIDTH,
            "axes.prop_cycle": cycler(color=color_cycle),
            "grid.linestyle": "--",
            "grid.linewidth": 0.5
        })
