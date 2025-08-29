#!/usr/bin/env python3
"""
Spam trends plotting tool for Thunder Muscle
Creates visualizations showing spam keyword frequency over time
"""
import json
import sys
import argparse
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path

# Add lib to path before importing custom modules
sys.path.append("lib")


def create_spam_timeline(
    spam_data, output_file, title="Spam Trends", display_method="save"
):
    """Create timeline plot showing spam percentage over time"""
    monthly_data = spam_data.get("by_month", {})

    if not monthly_data:
        print("No monthly data found")
        return

    # Prepare data for plotting
    dates = []
    percentages = []
    total_counts = []
    spam_counts = []

    for month_key, data in sorted(monthly_data.items()):
        if data["total_emails"] > 5:  # Only include months with meaningful data
            try:
                date_obj = datetime.strptime(month_key, "%Y-%m")
                dates.append(date_obj)
                percentages.append(data["spam_percentage"])
                total_counts.append(data["total_emails"])
                spam_counts.append(data["spam_emails"])
            except ValueError:
                continue

    if not dates:
        print("No valid date data found")
        return

    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # Top plot: Spam percentage over time
    ax1.plot(dates, percentages, linewidth=2, color="red", alpha=0.8)
    ax1.fill_between(dates, percentages, alpha=0.3, color="red")
    ax1.set_title(f"{title} - Spam Percentage Over Time", fontsize=14, pad=15)
    ax1.set_ylabel("Spam Percentage (%)", fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Bottom plot: Total email volume
    ax2.bar(
        dates,
        total_counts,
        alpha=0.6,
        color="steelblue",
        width=20,
        label="Total Emails",
    )
    ax2.bar(dates, spam_counts, alpha=0.8, color="red", width=20, label="Spam Emails")
    ax2.set_title("Email Volume (Total vs Spam)", fontsize=14, pad=15)
    ax2.set_xlabel("Date", fontsize=12)
    ax2.set_ylabel("Email Count", fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis="y")
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Format x-axis
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

    plt.tight_layout()

    # Handle display method
    if display_method in ["save", "both"]:
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Spam timeline saved to {output_file}")

    if display_method in ["show", "both"]:
        plt.show()
    else:
        plt.close()


def create_keyword_breakdown(
    spam_data, output_file, title="Spam Keywords", display_method="save"
):
    """Create bar chart showing most common spam keywords"""
    yearly_data = spam_data.get("by_year", {})

    # Aggregate keyword counts across all years
    keyword_totals = {}
    for year_data in yearly_data.values():
        for keyword, count in year_data.get("keyword_matches", {}).items():
            keyword_totals[keyword] = keyword_totals.get(keyword, 0) + count

    if not keyword_totals:
        print("No keyword data found")
        return

    # Sort by frequency
    sorted_keywords = sorted(keyword_totals.items(), key=lambda x: x[1], reverse=True)
    keywords = [k for k, v in sorted_keywords[:10]]  # Top 10
    counts = [v for k, v in sorted_keywords[:10]]

    # Create bar chart
    fig, ax = plt.subplots(figsize=(12, 6))

    bars = ax.bar(keywords, counts, color="orange", alpha=0.7)
    ax.set_title(f"{title} - Most Common Spam Keywords", fontsize=14, pad=15)
    ax.set_xlabel("Keyword Pattern", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.grid(True, alpha=0.3, axis="y")

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{int(height)}",
            ha="center",
            va="bottom",
        )

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Handle display method
    if display_method in ["save", "both"]:
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Keyword breakdown saved to {output_file}")

    if display_method in ["show", "both"]:
        plt.show()
    else:
        plt.close()


def create_yearly_heatmap(
    spam_data, output_file, title="Spam Trends", display_method="save"
):
    """Create heatmap showing spam percentage by year and keyword"""
    yearly_data = spam_data.get("by_year", {})

    if not yearly_data:
        print("No yearly data found")
        return

    # Get all keywords and years (filter to meaningful spam period 2010+)
    all_keywords = set()
    all_years = set()

    for year, data in yearly_data.items():
        year_int = int(year)
        if year_int >= 2010:  # Focus on post-2010 when marketing spam became prevalent
            all_years.add(year_int)
            for keyword in data.get("keyword_matches", {}):
                # Skip unsubscribe_bait to avoid GDPR false positives
                if keyword != "unsubscribe_bait":
                    all_keywords.add(keyword)

    if not all_keywords:
        print("No keyword data for heatmap")
        return

    # Create matrix
    keywords_list = sorted(list(all_keywords))
    years_list = sorted(list(all_years))

    matrix = []
    for keyword in keywords_list:
        row = []
        for year in years_list:
            if year >= 2010:  # Only include post-2010 data
                year_data = yearly_data.get(str(year), {})
                keyword_count = year_data.get("keyword_matches", {}).get(keyword, 0)
                total_emails = year_data.get("total_emails", 1)
                percentage = (
                    (keyword_count / total_emails * 100) if total_emails > 0 else 0
                )
                row.append(percentage)
            else:
                row.append(0)
        matrix.append(row)

    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 8))

    im = ax.imshow(matrix, cmap="Reds", aspect="auto")

    # Set ticks and labels
    ax.set_xticks(range(len(years_list)))
    ax.set_yticks(range(len(keywords_list)))
    ax.set_xticklabels(years_list)
    ax.set_yticklabels(keywords_list)

    # Rotate x-axis labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    # Add colorbar
    cbar = plt.colorbar(im)
    cbar.set_label("Spam Percentage (%)", rotation=270, labelpad=15)

    ax.set_title(f"{title} - Spam Keywords by Year (Heatmap)", fontsize=14, pad=15)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Keyword Pattern", fontsize=12)

    plt.tight_layout()

    # Handle display method
    if display_method in ["save", "both"]:
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Spam heatmap saved to {output_file}")

    if display_method in ["show", "both"]:
        plt.show()
    else:
        plt.close()


def main():
    parser = argparse.ArgumentParser(description="Generate spam trend visualizations")
    parser.add_argument("input_file", help="Input spam analysis data (JSON)")
    parser.add_argument(
        "--plot-type",
        choices=["timeline", "keywords", "heatmap", "all"],
        default="all",
        help="Type of plot to generate",
    )
    parser.add_argument(
        "--output-dir", default="output/plots", help="Output directory for plots"
    )
    parser.add_argument("--title", default="Spam Analysis", help="Title for the plots")
    parser.add_argument(
        "--display",
        choices=["show", "save", "both"],
        default="save",
        help="How to handle plots",
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load spam analysis data
    with open(args.input_file, "r") as f:
        spam_data = json.load(f)

    print("Generating spam trend plots...")

    # Generate plots based on type
    if args.plot_type in ["timeline", "all"]:
        timeline_file = output_dir / "spam_timeline.png"
        create_spam_timeline(spam_data, timeline_file, args.title, args.display)

    if args.plot_type in ["keywords", "all"]:
        keywords_file = output_dir / "spam_keywords.png"
        create_keyword_breakdown(spam_data, keywords_file, args.title, args.display)

    if args.plot_type in ["heatmap", "all"]:
        heatmap_file = output_dir / "spam_heatmap.png"
        create_yearly_heatmap(spam_data, heatmap_file, args.title, args.display)


if __name__ == "__main__":
    main()
