# figure_theme.py
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

class Theme:
    """
    Centralized theme configuration. 
    Everything is contained within apply_global to match the requested visual style.
    """
    COLORS = {
        "Mink": "#1f77b4",         
        "Chinchilla": "#ff7f0e",   
        "Raccoon dog": "#2ca02c",  
        "Fox": "#d62728",          
        "All Species": "#9467bd",  
        "default": "#7f7f7f"       
    }
    @staticmethod
    def apply_global():
        """
        Apply all global styling, grid settings, and axis formatting in one place.
        """
        # 1. Base RC Parameters for the "Curve Style"
        plt.rcParams.update({
            # Figure size and Fonts
            "figure.figsize": (10, 6),
            "font.family": "sans-serif",
            "axes.titlesize": 14,
            "axes.titleweight": "bold", # Bold title like in the example
            "axes.labelsize": 12,
            
            # Line and Marker style (The "Curves" and "Balls")
            "lines.linewidth": 3,     # Thickness of the curve
            "lines.marker": "o",        # The "Balls" (circular markers)
            "lines.markersize": 5,      # Size of the "Balls"
            
            # Grid style (The light background grid)
            "axes.grid": True,
            "grid.color": "#E6E6E6",    # Light gray color for the lines
            "grid.linestyle": "-",      # Solid grid lines
            "grid.linewidth": 1.0,
            "axes.axisbelow": True,     # Puts grid behind the curves
            
            # Spines (The "Box" around the plot)
            "axes.spines.top": False,   # Remove top border
            "axes.spines.right": False, # Remove right border
            
            # Legend style
            "legend.fontsize": 10,
            "legend.frameon": False,    # Remove box around legend
            
            # Tick labels
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        })

        # 2. Advanced Axis Formatting (Using Hooks)
        # We use a 'callback' to apply number formatting and rotation automatically 
        # to every axis created after this function is called.
        def setup_axis(ax):
            # Y-Axis: Number format (adds commas: e.g., 4,000 instead of 4000)
            ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
            
            # X-Axis: Label rotation (45-degree angle for years)
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

        # This tells matplotlib to run 'setup_axis' every time a new plot is made
        plt.gcf().add_axobserver(setup_axis)