"""Create review plots from the paper classification workbook.

Run from the repository root with:

    python post_processing/review_plotting.py

The script writes individual PNG plots to post_processing/plots by default.
"""

from __future__ import annotations

import argparse
import itertools
import math
import re
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKBOOK = ROOT / "paper classification ML.xlsx"
DEFAULT_SHEET = "Review_Matrix"
DEFAULT_OUTPUT_DIR = ROOT / "post_processing" / "plots"

REQUIRED_COLUMNS = [
    "Authors",
    "Year",
    "Publisher / venue",
    "Battery chemistry",
    "Dataset",
    "NN architecture",
]

BAR_COLORS = [
    "#2563eb",
    "#0891b2",
    "#16a34a",
    "#f59e0b",
    "#dc2626",
    "#7c3aed",
    "#db2777",
    "#4b5563",
]


def wrap_label(value: object, width: int = 34) -> str:
    """Wrap long axis labels without changing the underlying category."""
    text = str(value)
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def add_bar_labels(ax: plt.Axes, orientation: str) -> None:
    if orientation == "vertical":
        for patch in ax.patches:
            height = patch.get_height()
            if not np.isfinite(height):
                continue
            ax.annotate(
                f"{int(height)}",
                (patch.get_x() + patch.get_width() / 2, height),
                ha="center",
                va="bottom",
                fontsize=9,
                xytext=(0, 3),
                textcoords="offset points",
            )
    else:
        for patch in ax.patches:
            width = patch.get_width()
            if not np.isfinite(width):
                continue
            ax.annotate(
                f"{int(width)}",
                (width, patch.get_y() + patch.get_height() / 2),
                ha="left",
                va="center",
                fontsize=9,
                xytext=(4, 0),
                textcoords="offset points",
            )


def plot_vertical_counts(
    counts: pd.Series,
    title: str,
    xlabel: str,
    ylabel: str,
    output_path: Path,
    color: str = BAR_COLORS[0],
) -> None:
    counts = counts.dropna()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(counts.index.astype(str), counts.values, color=color, edgecolor="#111827", linewidth=0.5)
    ax.set_title(title, fontsize=16, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    add_bar_labels(ax, "vertical")
    fig.autofmt_xdate(rotation=0)
    save_figure(fig, output_path)


def plot_horizontal_counts(
    counts: pd.Series,
    title: str,
    xlabel: str,
    ylabel: str,
    output_path: Path,
    color: str = BAR_COLORS[1],
    label_width: int = 34,
) -> None:
    counts = counts.dropna().sort_values(ascending=True)
    height = max(5.5, 0.38 * len(counts) + 1.8)
    fig, ax = plt.subplots(figsize=(12, height))
    ax.barh(range(len(counts)), counts.values, color=color, edgecolor="#111827", linewidth=0.35)
    ax.set_yticks(range(len(counts)))
    ax.set_yticklabels([wrap_label(label, label_width) for label in counts.index])
    ax.set_title(title, fontsize=16, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    ax.margins(x=0.08)
    add_bar_labels(ax, "horizontal")
    save_figure(fig, output_path)


def extract_year(value: object) -> float:
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)) and np.isfinite(value):
        return int(value)
    match = re.search(r"(?:19|20)\d{2}", str(value))
    if match:
        return int(match.group(0))
    return np.nan


def clean_venue(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = " ".join(str(value).split())
    if not text:
        return None
    # Most rows are "Journal name, publisher"; the requested venue is the journal/conference.
    return text.split(",", 1)[0].strip()


def clean_editorial_publisher(value: object) -> str | None:
    """Group venue strings by editorial publisher for a compact summary plot."""
    if pd.isna(value):
        return None

    text = " ".join(str(value).split())
    if not text:
        return None

    publisher_text = text.split(",", 1)[-1].strip() if "," in text else text
    lower = publisher_text.lower()
    if "elsevier" in lower:
        return "Elsevier"
    if "ieee" in lower:
        return "IEEE"
    if "mdpi" in lower:
        return "MDPI"
    if "springer" in lower or "nature portfolio" in lower:
        return "Springer Nature"
    if "iop publishing" in lower or "electrochemical society" in lower or re.search(r"\becs\b", lower):
        return "IOP / ECS"
    if "aip publishing" in lower:
        return "AIP Publishing"
    if "american chemical society" in lower or re.search(r"\bacs\b", lower):
        return "ACS"
    if "sage" in lower:
        return "SAGE"
    if "frontiers" in lower:
        return "Frontiers"
    if "public library of science" in lower or "plos" in lower:
        return "PLOS"
    if "peerj" in lower:
        return "PeerJ"
    if "wiley" in lower or "john wiley" in lower:
        return "Wiley"
    if "higher education press" in lower:
        return "Higher Education Press"

    if "," in text:
        return publisher_text or "Other / not reported"

    return "Other / not reported"


def classify_chemistries(value: object) -> list[str]:
    if pd.isna(value):
        return ["Unknown / not reported"]

    text = " ".join(str(value).split())
    lower = text.lower()
    labels: list[str] = []

    rules = [
        (
            "Lithium-ion LFP",
            [
                r"\blfp\b",
                r"lifepo4",
                r"li\s*fe\s*po4",
                r"lithium iron phosphate",
            ],
        ),
        (
            "Lithium-ion NMC/NCM",
            [
                r"\bnmc\b",
                r"\bncm\b",
                r"\blinmc\b",
                r"li\s*\(\s*ni\s*co\s*mn\s*\)\s*o2",
                r"nickel[-\s]*manganese[-\s]*cobalt",
                r"nickel[-\s]*cobalt[-\s]*manganese",
                r"ternary lithium",
            ],
        ),
        (
            "Lithium-ion NCA",
            [
                r"\bnca\b",
                r"nickel[-\s]*cobalt[-\s]*alumin",
                r"li[0-9.]*ni[0-9.]*co[0-9.]*al",
            ],
        ),
        (
            "Lithium-ion LMO",
            [
                r"\blmo\b",
                r"limn2o4",
                r"lithium manganese oxide",
            ],
        ),
    ]

    for label, patterns in rules:
        if any(re.search(pattern, lower, flags=re.IGNORECASE) for pattern in patterns):
            labels.append(label)

    if _has_explicit_lco(lower):
        labels.append("Lithium-ion LCO")

    if "lead-acid" in lower or "lead acid" in lower:
        labels.append("Lead-acid")

    if "sodium-ion" in lower or "sodium ion" in lower:
        labels.append("Sodium-ion")

    if labels:
        return sorted(set(labels))

    if "lithium" in lower or "li-ion" in lower or "li ion" in lower:
        return ["Lithium-ion unspecified"]

    return ["Unknown / not reported"]


def _has_explicit_lco(lower_text: str) -> bool:
    lco_terms = [r"\blco\b", r"licoo2", r"li\s*co\s*o2", r"lithium cobalt oxide"]
    uncertainty_terms = [
        "commonly",
        "conventionally",
        "not stated",
        "not explicitly",
        "not reported",
        "not specified",
    ]
    for pattern in lco_terms:
        match = re.search(pattern, lower_text)
        if not match:
            continue
        window = lower_text[max(0, match.start() - 120) : match.end() + 120]
        if any(term in window for term in uncertainty_terms):
            continue
        return True
    return False


def classify_datasets(value: object) -> list[str]:
    if pd.isna(value):
        return ["Unknown / not reported"]

    text = " ".join(str(value).split())
    lower = text.lower()
    labels: list[str] = []

    if re.search(r"randomized[-\s]*use|random walk|\brw\d+\b|\brw set\b", lower):
        labels.append("NASA Random Walk")
    elif re.search(r"\bnasa\b|b0005|b0006|b0007|b0018|\bb5\b|\bb6\b|\bb7\b|\bb18\b", lower):
        labels.append("NASA PCoE")

    dataset_rules = [
        ("CALCE", [r"\bcalce\b", r"\bcs2[_\s-]*\d+\b", r"\bcs[_\s-]*(35|36|37|38)\b", r"university of maryland"]),
        (
            "MIT-Stanford-TRI / Severson",
            [
                r"\bseverson\b",
                r"data\.matr\.io",
                r"toyota research institute",
                r"\btri\b",
                r"\battia\b",
                r"a123 systems",
                r"fast[-\s]*charging dataset",
            ],
        ),
        ("Oxford", [r"\boxford\b"]),
        ("HUST", [r"\bhust\b"]),
        ("TJU", [r"\btju\b"]),
        ("XJTU", [r"\bxjtu\b"]),
        ("SNL / Sandia", [r"\bsnl\b", r"\bsandia\b"]),
    ]

    for label, patterns in dataset_rules:
        if any(re.search(pattern, lower, flags=re.IGNORECASE) for pattern in patterns):
            labels.append(label)

    if re.search(r"self[-\s]*built|authors?' own|own laboratory|laboratory experiments|proprietary", lower):
        labels.append("Custom / authors' own")

    if labels:
        return sorted(set(labels))

    if "public" in lower:
        return ["Other public dataset"]

    return ["Other / unspecified"]


ARCHITECTURE_RULES = [
    ("Convolutional", "CNN", r"\bcnn\b|conv1d|conv2d|convolutional neural network"),
    ("Convolutional", "TCN", r"\btcn\b|temporal convolutional"),
    ("Convolutional", "ResNet", r"\bresnet\d*\b|residual cnn|residual convolution"),
    ("Convolutional", "GNN / GCN", r"\bgnn\b|\bgcn\b|graph convolution"),
    ("Recurrent", "BiLSTM", r"\bbi[-\s]*lstm\b|bidirectional lstm"),
    ("Recurrent", "LSTM", r"(?<!bi[-\s])\blstm\b"),
    ("Recurrent", "BiGRU", r"\bbi[-\s]*gru\b|bidirectional gru"),
    ("Recurrent", "GRU", r"(?<!bi[-\s])\bgru\b"),
    ("Recurrent", "RNN", r"\brnn\b|recurrent neural network"),
    ("Recurrent", "ESN", r"\besn\b|echo state network"),
    ("Attention-based", "Transformer", r"\btransformer\b"),
    ("Attention-based", "Vision Transformer / ViT", r"\bvit\b|vision transformer"),
    ("Attention-based", "Informer", r"\binformer\b"),
    ("Attention-based", "Temporal Pattern Attention", r"\btpa\b|temporal pattern attention"),
    ("Attention-based", "Attention", r"\battention\b|multi[-\s]*head attention|self[-\s]*attention"),
]


def count_architecture_terms(values: pd.Series) -> dict[str, Counter]:
    counts: dict[str, Counter] = {
        "Convolutional": Counter(),
        "Recurrent": Counter(),
        "Attention-based": Counter(),
    }

    for value in values.dropna().astype(str):
        lower = value.lower()
        found: set[tuple[str, str]] = set()
        for family, label, pattern in ARCHITECTURE_RULES:
            if re.search(pattern, lower, flags=re.IGNORECASE):
                found.add((family, label))

        # Prefer specific bidirectional labels over their generic counterparts.
        if ("Recurrent", "BiLSTM") in found:
            found.discard(("Recurrent", "LSTM"))
        if ("Recurrent", "BiGRU") in found:
            found.discard(("Recurrent", "GRU"))
        if ("Attention-based", "Vision Transformer / ViT") in found:
            found.discard(("Attention-based", "Transformer"))
        if ("Attention-based", "Temporal Pattern Attention") in found:
            found.discard(("Attention-based", "Attention"))

        for family, label in found:
            counts[family][label] += 1

    return counts


def plot_neural_network_families(counts_by_family: dict[str, Counter], output_path: Path) -> None:
    families = ["Convolutional", "Recurrent", "Attention-based"]
    colors = {
        "Convolutional": "#2563eb",
        "Recurrent": "#f59e0b",
        "Attention-based": "#16a34a",
    }
    max_items = max((len(counts_by_family[family]) for family in families), default=1)
    fig_height = max(5.5, 0.48 * max_items + 2.0)
    fig, axes = plt.subplots(1, 3, figsize=(18, fig_height), sharex=False)

    for ax, family in zip(axes, families):
        counts = pd.Series(counts_by_family[family]).sort_values(ascending=True)
        if counts.empty:
            ax.text(0.5, 0.5, "No matches", ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            continue

        ax.barh(range(len(counts)), counts.values, color=colors[family], edgecolor="#111827", linewidth=0.35)
        ax.set_yticks(range(len(counts)))
        ax.set_yticklabels([wrap_label(label, 24) for label in counts.index])
        ax.set_title(family, fontsize=14, fontweight="bold")
        ax.set_xlabel("Number of papers")
        ax.grid(axis="x", alpha=0.25)
        ax.set_axisbelow(True)
        ax.margins(x=0.18)
        add_bar_labels(ax, "horizontal")

    fig.suptitle("Neural Network Architectures by Family", fontsize=17, fontweight="bold")
    fig.tight_layout()
    save_figure(fig, output_path)


def parse_authors(value: object) -> list[str]:
    if pd.isna(value):
        return []
    text = " ".join(str(value).replace("\n", " ").split())
    if not text:
        return []

    parts = re.split(r"\s*(?:,|;|\band\b)\s*", text)
    authors: list[str] = []
    for part in parts:
        name = re.sub(r"\bet\s+al\.?$", "", part.strip(), flags=re.IGNORECASE).strip()
        if len(name) < 2:
            continue
        authors.append(name)
    return list(dict.fromkeys(authors))


def build_author_graph(author_values: pd.Series) -> nx.Graph:
    graph = nx.Graph()
    publication_counts: Counter = Counter()

    for value in author_values:
        authors = parse_authors(value)
        if not authors:
            continue
        publication_counts.update(authors)
        for author in authors:
            graph.add_node(author)
        for source, target in itertools.combinations(authors, 2):
            if graph.has_edge(source, target):
                graph[source][target]["weight"] += 1
            else:
                graph.add_edge(source, target, weight=1)

    for author, count in publication_counts.items():
        graph.nodes[author]["publications"] = count

    return graph


def filter_author_graph(graph: nx.Graph, min_publications: int, max_nodes: int) -> nx.Graph:
    if graph.number_of_nodes() <= max_nodes and min_publications <= 1:
        return graph.copy()

    keep = [
        node
        for node, data in graph.nodes(data=True)
        if int(data.get("publications", 0)) >= min_publications
    ]

    if len(keep) < 10:
        keep = sorted(
            graph.nodes,
            key=lambda node: (
                int(graph.nodes[node].get("publications", 0)),
                graph.degree(node),
                node,
            ),
            reverse=True,
        )[:max_nodes]

    if len(keep) > max_nodes:
        keep = sorted(
            keep,
            key=lambda node: (
                int(graph.nodes[node].get("publications", 0)),
                graph.degree(node),
                node,
            ),
            reverse=True,
        )[:max_nodes]

    return graph.subgraph(keep).copy()


def community_colors(graph: nx.Graph) -> dict[str, str]:
    palette = [
        "#22d3ee",
        "#f59e0b",
        "#2563eb",
        "#ef4444",
        "#a855f7",
        "#84cc16",
        "#14b8a6",
        "#f97316",
        "#eab308",
        "#ec4899",
        "#10b981",
        "#6366f1",
    ]

    if graph.number_of_edges() > 0:
        communities = list(nx.algorithms.community.greedy_modularity_communities(graph, weight="weight"))
    else:
        communities = [{node} for node in graph.nodes]

    colors: dict[str, str] = {}
    for index, community in enumerate(communities):
        color = palette[index % len(palette)]
        for node in community:
            colors[node] = color
    return colors


def component_grid_layout(graph: nx.Graph, seed: int = 42) -> dict[str, np.ndarray]:
    """Lay disconnected author communities out as separate readable islands."""
    components = sorted(nx.connected_components(graph), key=len, reverse=True)
    if not components:
        return {}

    columns = max(1, math.ceil(math.sqrt(len(components))))
    rows = math.ceil(len(components) / columns)
    cell_width = 7.0
    cell_height = 5.8

    positions: dict[str, np.ndarray] = {}
    for index, component in enumerate(components):
        subgraph = graph.subgraph(component)
        size = subgraph.number_of_nodes()

        if size == 1:
            local_positions = {next(iter(component)): np.array([0.0, 0.0])}
        elif size <= 12:
            local_positions = nx.circular_layout(subgraph, scale=1.35 + 0.30 * size)
        else:
            local_positions = nx.spring_layout(
                subgraph,
                seed=seed + index,
                k=1.1 / math.sqrt(size),
                iterations=500,
                scale=1.1 + 0.10 * size,
                weight="weight",
            )

        column = index % columns
        row = index // columns
        center = np.array(
            [
                (column - (columns - 1) / 2) * cell_width,
                ((rows - 1) / 2 - row) * cell_height,
            ]
        )
        for node, position in local_positions.items():
            positions[node] = np.asarray(position) + center

    return positions


def plot_author_network(graph: nx.Graph, output_path: Path, max_labels: int = 80) -> None:
    if graph.number_of_nodes() == 0:
        fig, ax = plt.subplots(figsize=(10, 6), facecolor="black")
        ax.set_facecolor("black")
        ax.text(0.5, 0.5, "No author data found", ha="center", va="center", color="white", fontsize=16)
        ax.set_axis_off()
        save_figure(fig, output_path)
        return

    pos = component_grid_layout(graph)
    colors = community_colors(graph)

    node_sizes = [
        120 + 115 * math.sqrt(int(graph.nodes[node].get("publications", 1))) + 20 * graph.degree(node)
        for node in graph.nodes
    ]
    edge_widths = [0.55 + 0.45 * graph[source][target].get("weight", 1) for source, target in graph.edges]
    node_colors = [colors.get(node, "#22d3ee") for node in graph.nodes]

    fig, ax = plt.subplots(figsize=(16, 12), facecolor="black")
    ax.set_facecolor("black")

    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        width=edge_widths,
        edge_color="#d1d5db",
        alpha=0.58,
    )
    nx.draw_networkx_nodes(
        graph,
        pos,
        ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        linewidths=0.65,
        edgecolors="#f8fafc",
        alpha=0.96,
    )

    label_nodes = sorted(
        graph.nodes,
        key=lambda node: (
            int(graph.nodes[node].get("publications", 0)),
            graph.degree(node),
            node,
        ),
        reverse=True,
    )[:max_labels]
    labels = {node: node for node in label_nodes}
    nx.draw_networkx_labels(
        graph,
        pos,
        labels=labels,
        ax=ax,
        font_size=7.0,
        font_color="#111827",
        bbox={
            "boxstyle": "round,pad=0.22,rounding_size=0.6",
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.94,
        },
    )

    ax.set_title("Author Collaboration Network", fontsize=20, fontweight="bold", color="white", pad=18)
    ax.set_axis_off()
    ax.margins(0.10)
    save_figure(fig, output_path)


def explode_counts(series: pd.Series, classifier) -> pd.Series:
    counter: Counter = Counter()
    for value in series:
        counter.update(classifier(value))
    return pd.Series(counter).sort_values(ascending=False)


def load_review_matrix(workbook: Path, sheet_name: str) -> pd.DataFrame:
    if not workbook.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook}")

    df = pd.read_excel(workbook, sheet_name=sheet_name)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Workbook is missing required columns: {', '.join(missing)}")
    return df


def create_plots(
    workbook: Path,
    sheet_name: str,
    output_dir: Path,
    author_min_publications: int,
    author_max_nodes: int,
) -> list[Path]:
    sns.set_theme(style="whitegrid", context="notebook")
    df = load_review_matrix(workbook, sheet_name)
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []

    year_counts = (
        df["Year"]
        .map(extract_year)
        .dropna()
        .astype(int)
        .value_counts()
        .sort_index()
    )
    path = output_dir / "01_publications_by_year.png"
    plot_vertical_counts(
        year_counts,
        "Amount of Publications by Year",
        "Year",
        "Number of papers",
        path,
        color=BAR_COLORS[0],
    )
    written.append(path)

    venue_counts = df["Publisher / venue"].map(clean_venue).dropna().value_counts()
    path = output_dir / "02_publications_by_publisher_venue.png"
    plot_horizontal_counts(
        venue_counts,
        "Amount of Publications by Publisher Venue",
        "Number of papers",
        "Publisher venue",
        path,
        color=BAR_COLORS[2],
        label_width=42,
    )
    written.append(path)

    editorial_counts = df["Publisher / venue"].map(clean_editorial_publisher).dropna().value_counts()
    path = output_dir / "02b_publications_by_editorial_publisher.png"
    plot_horizontal_counts(
        editorial_counts,
        "Amount of Publications by Editorial Publisher",
        "Number of papers",
        "Editorial publisher",
        path,
        color=BAR_COLORS[5],
        label_width=30,
    )
    written.append(path)

    chemistry_counts = explode_counts(df["Battery chemistry"], classify_chemistries)
    path = output_dir / "03_battery_chemistry.png"
    plot_horizontal_counts(
        chemistry_counts,
        "Battery Chemistry",
        "Number of papers",
        "Chemistry",
        path,
        color=BAR_COLORS[3],
        label_width=32,
    )
    written.append(path)

    dataset_counts = explode_counts(df["Dataset"], classify_datasets)
    path = output_dir / "04_dataset_used_amount.png"
    plot_horizontal_counts(
        dataset_counts,
        "Dataset Used Amount",
        "Number of papers",
        "Dataset",
        path,
        color=BAR_COLORS[4],
        label_width=34,
    )
    written.append(path)

    architecture_counts = count_architecture_terms(df["NN architecture"])
    path = output_dir / "05_neural_networks_by_family.png"
    plot_neural_network_families(architecture_counts, path)
    written.append(path)

    author_graph = build_author_graph(df["Authors"])
    filtered_author_graph = filter_author_graph(author_graph, author_min_publications, author_max_nodes)
    path = output_dir / "06_author_collaboration_network.png"
    plot_author_network(filtered_author_graph, path, max_labels=min(author_max_nodes, 80))
    written.append(path)

    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate plots from the review classification workbook.")
    parser.add_argument("--input", type=Path, default=DEFAULT_WORKBOOK, help="Path to the Excel workbook.")
    parser.add_argument("--sheet", default=DEFAULT_SHEET, help="Worksheet name to read.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory where PNG plots are saved.")
    parser.add_argument(
        "--author-min-publications",
        type=int,
        default=2,
        help="Minimum publication count for authors shown in the network plot.",
    )
    parser.add_argument(
        "--author-max-nodes",
        type=int,
        default=120,
        help="Maximum number of author nodes shown in the network plot.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    written = create_plots(
        workbook=args.input,
        sheet_name=args.sheet,
        output_dir=args.output_dir,
        author_min_publications=max(1, args.author_min_publications),
        author_max_nodes=max(10, args.author_max_nodes),
    )
    print("Created plots:")
    for path in written:
        print(f" - {path}")


if __name__ == "__main__":
    main()
