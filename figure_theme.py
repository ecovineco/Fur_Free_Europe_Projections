# figure_theme.py
import matplotlib.pyplot as plt

class Theme:
    FIG_SIZE = (10, 6)
    TITLE_SIZE = 16
    LABEL_SIZE = 14
    TICK_SIZE = 12
    LEGEND_SIZE = 12
    COLORS = {
        "default": "#1f77b4"
    }
    LINE_STYLE = {
        "solid": "-",
        "dashed": "--",
        "dotted": ":"
    }

    @staticmethod
    def apply_global():
        plt.rcParams.update({
            "figure.figsize": Theme.FIG_SIZE,
            "axes.titlesize": Theme.TITLE_SIZE,
            "axes.labelsize": Theme.LABEL_SIZE,
            "xtick.labelsize": Theme.TICK_SIZE,
            "ytick.labelsize": Theme.TICK_SIZE,
            "legend.fontsize": Theme.LEGEND_SIZE
        })
