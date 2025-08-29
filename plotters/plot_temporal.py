#!/usr/bin/env python3
"""
Temporal plotting tool for Thunder Muscle analysis results
"""
import json
import sys
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path

# Add lib to path before importing custom modules
sys.path.append("lib")


def parse_email_date(date_str):
    """Parse email date string to datetime object"""
    try:
        return datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def create_year_over_year_histogram(
    emails, output_file, title="Email Volume", display_method="save"
):
    """Create year-over-year stacked histogram by month"""
    # Parse dates and create month-year data
    monthly_data = {}

    for email in emails:
        date_obj = parse_email_date(email.get("date", ""))
        if date_obj:
            year = date_obj.year
            month = date_obj.month

            if year not in monthly_data:
                monthly_data[year] = {i: 0 for i in range(1, 13)}
            monthly_data[year][month] += 1

    if not monthly_data:
        print("No valid dates found in dataset")
        return

    # Convert to DataFrame for easier plotting
    df_data = []
    for year, months in monthly_data.items():
        for month, count in months.items():
            df_data.append(
                {
                    "year": year,
                    "month": month,
                    "count": count,
                    "month_name": datetime(2000, month, 1).strftime("%b"),
                }
            )

    df = pd.DataFrame(df_data)

    # Create pivot table for stacked histogram
    pivot_df = df.pivot_table(
        index="month_name", columns="year", values="count", fill_value=0
    )

    # Reorder months correctly
    month_order = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    pivot_df = pivot_df.reindex(month_order)

    # Create the stacked bar chart
    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot stacked bars
    pivot_df.plot(kind="bar", stacked=True, ax=ax, colormap="tab20", width=0.8)

    ax.set_title(f"{title} - Year over Year by Month", fontsize=16, pad=20)
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Email Count", fontsize=12)
    ax.legend(title="Year", bbox_to_anchor=(1.05, 1), loc="upper left")

    # Rotate x-axis labels
    plt.xticks(rotation=0)

    # Add grid for better readability
    ax.grid(True, alpha=0.3, axis="y")

    # Tight layout to prevent legend cutoff
    plt.tight_layout()

    # Handle display method
    if display_method in ["save", "both"]:
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Year-over-year histogram saved to {output_file}")

    if display_method in ["show", "both"]:
        plt.show()
    else:
        plt.close()  # Close if not showing

    # Show summary stats
    total_by_year = pivot_df.sum(axis=0).sort_index()
    print("\nEmail volume by year:")
    for year, count in total_by_year.items():
        print(f"  {year}: {count:,} emails")


def create_simple_timeline(
    emails, output_file, title="Email Timeline", display_method="save"
):
    """Create a simple timeline plot of email volume over time"""
    # Parse dates and aggregate by month
    monthly_counts = {}

    for email in emails:
        date_obj = parse_email_date(email.get("date", ""))
        if date_obj:
            month_key = date_obj.strftime("%Y-%m")
            monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1

    if not monthly_counts:
        print("No valid dates found in dataset")
        return

    # Sort by date
    sorted_months = sorted(monthly_counts.items())
    dates = [datetime.strptime(month, "%Y-%m") for month, _ in sorted_months]
    counts = [count for _, count in sorted_months]

    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(dates, counts, linewidth=2, color="steelblue")
    ax.fill_between(dates, counts, alpha=0.3, color="steelblue")

    ax.set_title(f"{title} - Timeline", fontsize=16, pad=20)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Emails per Month", fontsize=12)

    # Format x-axis
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_minor_locator(mdates.MonthLocator())

    # Rotate labels if needed
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    # Add grid
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Handle display method
    if display_method in ["save", "both"]:
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Timeline plot saved to {output_file}")

    if display_method in ["show", "both"]:
        plt.show()
    else:
        plt.close()  # Close if not showing


def main():
    parser = argparse.ArgumentParser(
        description="Generate temporal plots from email datasets"
    )
    parser.add_argument("input_file", help="Input dataset file (JSON)")
    parser.add_argument(
        "--plot-type",
        choices=["histogram", "timeline", "both"],
        default="histogram",
        help="Type of plot to generate",
    )
    parser.add_argument(
        "--output-dir", default="plots", help="Output directory for plots"
    )
    parser.add_argument("--title", default="Email Volume", help="Title for the plots")
    parser.add_argument(
        "--filter-domain", help="Filter emails by recipient domain (e.g., wsu.edu)"
    )
    parser.add_argument(
        "--display",
        choices=["show", "save", "both"],
        default="save",
        help="How to handle the plot (default: save)",
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Load emails
    with open(args.input_file, "r") as f:
        emails = json.load(f)

    # Filter by domain if specified
    if args.filter_domain:
        filtered_emails = []
        for email in emails:
            to_field = email.get("to", "").lower()
            if args.filter_domain.lower() in to_field:
                filtered_emails.append(email)
        emails = filtered_emails
        print(
            f"Filtered to {len(emails)} emails with recipient domain "
            f"'{args.filter_domain}'"
        )

    if not emails:
        print("No emails to plot after filtering")
        return

    # Generate plots
    if args.plot_type in ["histogram", "both"]:
        histogram_file = output_dir / "year_over_year_histogram.png"
        create_year_over_year_histogram(
            emails, histogram_file, args.title, args.display
        )

    if args.plot_type in ["timeline", "both"]:
        timeline_file = output_dir / "timeline.png"
        create_simple_timeline(emails, timeline_file, args.title, args.display)


if __name__ == "__main__":
    main()
