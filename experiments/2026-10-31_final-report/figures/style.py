from pathlib import Path

import matplotlib as mpl

mpl.use("pgf")
import matplotlib.pyplot as plt

COLUMN_IN = 3.03
FULL_IN = 6.5

INK = "#222222"
MUTED = "#595959"
GRID = "#E3E3E3"

CONDITIONS = {
    "English CoT": {"color": "#0072B2", "marker": "s", "ls": "-", "hatch": ""},
    "Hindi CoT": {"color": "#D55E00", "marker": "o", "ls": "-", "hatch": "///"},
    "en-CoT": {"color": "#009E73", "marker": "D", "ls": "-", "hatch": "\\\\\\"},
    "CLP": {"color": "#CC79A7", "marker": "^", "ls": "--", "hatch": "xxx"},
    "Hinglish CoT": {"color": "#E69F00", "marker": "v", "ls": "-.", "hatch": "..."},
    "English direct": {"color": "#56B4E9", "marker": "P", "ls": ":", "hatch": "---"},
    "Hindi direct": {"color": "#8C8C8C", "marker": "X", "ls": ":", "hatch": "+++"},
}

ALIASES = {
    "Standard CoT": "English CoT",
    "Hindi en-CoT": "en-CoT",
    "Hindi en-cot": "en-CoT",
    "Hindi CLP": "CLP",
    "Hinglish": "Hinglish CoT",
    "Direct": "Hindi direct",
}

LANGUAGE = {
    "English": {"color": "#0072B2", "marker": "s", "ls": "-", "hatch": ""},
    "Hindi": {"color": "#D55E00", "marker": "o", "ls": "-", "hatch": "///"},
}

BINARY = {"off": "#0072B2", "on": "#D55E00", 0: "#0072B2", 1: "#D55E00"}

DIFFICULTY = {
    "short": "#C6DBEF",
    "medium": "#9ECAE1",
    "long": "#6BAED6",
    "very_long": "#2171B5",
    "very_very_long": "#08306B",
}

DIFFICULTY_LABEL = {
    "short": "Short",
    "medium": "Medium",
    "long": "Long",
    "very_long": "Very long",
    "very_very_long": "V. v. long",
}

TASK_LABEL = {
    "date_addition": "Date addition",
    "date_subtraction": "Date subtraction",
    "date_duration": "Date duration",
    "date_recurrence": "Date recurrence",
    "day_of_week": "Day of week",
    "interval_date": "Interval date",
    "time_addition": "Time addition",
    "time_subtraction": "Time subtraction",
    "time_duration": "Time duration",
}

INSERTION = {
    "none": {"color": "#BDBDBD", "hatch": "", "label": "No distractor"},
    "similar": {"color": "#D55E00", "hatch": "///", "label": "Time-related"},
    "dissimilar": {"color": "#0072B2", "hatch": "...", "label": "Unrelated"},
}


def condition(name):
    return CONDITIONS[ALIASES.get(name, name)]


def apply():
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["TeX Gyre Termes"],
        "pgf.texsystem": "lualatex",
        "pgf.rcfonts": False,
        "pgf.preamble": "\\usepackage{fontspec}\\setmainfont{TeX Gyre Termes}",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "legend.frameon": False,
        "legend.handlelength": 1.8,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "axes.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "lines.linewidth": 1.2,
        "lines.markersize": 4,
        "errorbar.capsize": 1.5,
        "patch.linewidth": 0.4,
        "hatch.linewidth": 0.4,
        "text.color": INK,
    })


def save(fig, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".pdf"))
    fig.savefig(path.with_suffix(".png"), dpi=200)
    plt.close(fig)
