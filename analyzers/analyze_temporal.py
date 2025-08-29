#!/usr/bin/env python3
"""
Temporal analysis tool using tm.py API and lib output adapters
"""
import json
import sys
import argparse
from collections import defaultdict
from datetime import datetime

# Add lib to path before importing custom modules
sys.path.append("lib")

from output import write_data  # noqa: E402
from config import load_config, get_output_format  # noqa: E402


def parse_email_date(date_str):
    """Parse email date string to datetime object"""
    try:
        return datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def analyze_by_year(emails):
    """Analyze email patterns by year"""
    yearly_data = defaultdict(lambda: {"total": 0, "with_body": 0})

    for email in emails:
        date_obj = parse_email_date(email.get("date", ""))
        if date_obj:
            year = date_obj.year
            yearly_data[year]["total"] += 1
            if email.get("has_body"):
                yearly_data[year]["with_body"] += 1

    return dict(yearly_data)


def analyze_by_month(emails, year=None):
    """Analyze email patterns by month (optionally for specific year)"""
    monthly_data = defaultdict(lambda: {"total": 0, "with_body": 0})

    for email in emails:
        date_obj = parse_email_date(email.get("date", ""))
        if date_obj:
            if year is None or date_obj.year == year:
                month_key = f"{date_obj.year}-{date_obj.month:02d}"
                monthly_data[month_key]["total"] += 1
                if email.get("has_body"):
                    monthly_data[month_key]["with_body"] += 1

    return dict(monthly_data)


def analyze_by_weekday(emails):
    """Analyze email patterns by day of week"""
    weekday_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    weekday_data = defaultdict(lambda: {"total": 0, "with_body": 0})

    for email in emails:
        date_obj = parse_email_date(email.get("date", ""))
        if date_obj:
            weekday = weekday_names[date_obj.weekday()]
            weekday_data[weekday]["total"] += 1
            if email.get("has_body"):
                weekday_data[weekday]["with_body"] += 1

    return dict(weekday_data)


def analyze_by_hour(emails):
    """Analyze email patterns by hour of day"""
    hourly_data = defaultdict(lambda: {"total": 0, "with_body": 0})

    for email in emails:
        date_obj = parse_email_date(email.get("date", ""))
        if date_obj:
            hour = date_obj.hour
            hourly_data[hour]["total"] += 1
            if email.get("has_body"):
                hourly_data[hour]["with_body"] += 1

    return dict(hourly_data)


def get_date_range(emails):
    """Get the date range of the dataset"""
    dates = []
    for email in emails:
        date_obj = parse_email_date(email.get("date", ""))
        if date_obj:
            dates.append(date_obj)

    if dates:
        return min(dates), max(dates)
    return None, None


def main():
    parser = argparse.ArgumentParser(description="Temporal analysis for email datasets")
    parser.add_argument("input_file", help="Input dataset file")
    parser.add_argument(
        "--analysis",
        choices=["year", "month", "weekday", "hour", "summary"],
        default="summary",
        help="Type of temporal analysis (default: summary)",
    )
    parser.add_argument("--year", type=int, help="Specific year for monthly analysis")
    parser.add_argument("--output", help="Output file for analysis results")
    parser.add_argument(
        "--format", choices=["json", "csv", "yaml"], help="Output format"
    )

    args = parser.parse_args()

    config = load_config()

    with open(args.input_file, "r") as f:
        emails = json.load(f)

    # Perform analysis based on type
    if args.analysis == "year":
        results = analyze_by_year(emails)
        analysis_data = [
            {
                "year": year,
                "total_emails": data["total"],
                "emails_with_body": data["with_body"],
                "body_percentage": (
                    (data["with_body"] / data["total"] * 100)
                    if data["total"] > 0
                    else 0
                ),
            }
            for year, data in sorted(results.items())
        ]
    elif args.analysis == "month":
        results = analyze_by_month(emails, args.year)
        analysis_data = [
            {
                "month": month,
                "total_emails": data["total"],
                "emails_with_body": data["with_body"],
                "body_percentage": (
                    (data["with_body"] / data["total"] * 100)
                    if data["total"] > 0
                    else 0
                ),
            }
            for month, data in sorted(results.items())
        ]
    elif args.analysis == "weekday":
        results = analyze_by_weekday(emails)
        weekday_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        analysis_data = [
            {
                "weekday": day,
                "total_emails": results[day]["total"],
                "emails_with_body": results[day]["with_body"],
                "body_percentage": (
                    (results[day]["with_body"] / results[day]["total"] * 100)
                    if results[day]["total"] > 0
                    else 0
                ),
            }
            for day in weekday_order
            if day in results
        ]
    elif args.analysis == "hour":
        results = analyze_by_hour(emails)
        analysis_data = [
            {
                "hour": hour,
                "total_emails": data["total"],
                "emails_with_body": data["with_body"],
                "body_percentage": (
                    (data["with_body"] / data["total"] * 100)
                    if data["total"] > 0
                    else 0
                ),
            }
            for hour, data in sorted(results.items())
        ]
    else:  # summary
        start_date, end_date = get_date_range(emails)
        yearly = analyze_by_year(emails)
        weekday = analyze_by_weekday(emails)

        analysis_data = {
            "dataset_info": {
                "total_emails": len(emails),
                "emails_with_body": sum(1 for e in emails if e.get("has_body")),
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None,
                },
            },
            "by_year": yearly,
            "by_weekday": weekday,
        }

    # Output results
    if args.output:
        output_format = args.format or get_output_format(config)
        format_used = write_data(analysis_data, args.output, output_format)
        print(f"Temporal analysis saved to {args.output} ({format_used})")
    else:
        # Console output
        if args.analysis == "summary":
            info = analysis_data["dataset_info"]
            print("Temporal Analysis Summary:")
            print(f"  Total emails: {info['total_emails']}")
            print(f"  With bodies: {info['emails_with_body']}")
            if info["date_range"]["start"]:
                print(
                    f"  Date range: {info['date_range']['start'][:10]} "
                    f"to {info['date_range']['end'][:10]}"
                )

            print("\nTop 5 years by volume:")
            yearly_sorted = sorted(
                analysis_data["by_year"].items(),
                key=lambda x: x[1]["total"],
                reverse=True,
            )
            for year, data in yearly_sorted[:5]:
                print(f"  {year}: {data['total']} emails")
        else:
            print(f"Temporal Analysis ({args.analysis}):")
            for item in analysis_data:
                key = list(item.keys())[0]
                print(
                    f"  {item[key]}: {item['total_emails']} emails "
                    f"({item['body_percentage']:.1f}% with bodies)"
                )


if __name__ == "__main__":
    main()
