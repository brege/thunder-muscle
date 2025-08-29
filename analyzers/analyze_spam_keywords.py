#!/usr/bin/env python3
"""
Spam keyword analysis tool for Thunder Muscle
Analyzes frequency of marketing/spam keywords over time
"""
import json
import sys
import argparse
import re
from collections import defaultdict
from datetime import datetime

# Add lib to path before importing custom modules
sys.path.append("lib")

from output import write_data  # noqa: E402


def extract_date_components(date_str):
    """Extract year, month from date string"""
    try:
        dt = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
        return dt.year, dt.month
    except (ValueError, TypeError):
        return None, None


def check_spam_keywords(email, keyword_patterns):
    """Check if email contains spam keywords"""
    subject = email.get("subject", "").lower()
    body = email.get("body", "").lower()
    combined_text = f"{subject} {body}"

    matches = []
    for pattern_name, pattern in keyword_patterns.items():
        if re.search(pattern, combined_text, re.IGNORECASE):
            matches.append(pattern_name)

    return matches


def analyze_spam_keywords(emails, keyword_patterns):
    """Analyze spam keyword frequency over time"""
    # Monthly data
    monthly_data = defaultdict(
        lambda: {
            "total_emails": 0,
            "spam_emails": 0,
            "keyword_matches": defaultdict(int),
            "spam_percentage": 0.0,
        }
    )

    # Yearly data
    yearly_data = defaultdict(
        lambda: {
            "total_emails": 0,
            "spam_emails": 0,
            "keyword_matches": defaultdict(int),
            "spam_percentage": 0.0,
        }
    )

    total_processed = 0
    total_spam = 0

    for email in emails:
        year, month = extract_date_components(email.get("date", ""))
        if not year:
            continue

        month_key = f"{year}-{month:02d}"

        # Count total emails
        monthly_data[month_key]["total_emails"] += 1
        yearly_data[year]["total_emails"] += 1
        total_processed += 1

        # Check for spam keywords
        spam_matches = check_spam_keywords(email, keyword_patterns)

        if spam_matches:
            monthly_data[month_key]["spam_emails"] += 1
            yearly_data[year]["spam_emails"] += 1
            total_spam += 1

            # Track which keywords matched
            for keyword in spam_matches:
                monthly_data[month_key]["keyword_matches"][keyword] += 1
                yearly_data[year]["keyword_matches"][keyword] += 1

    # Calculate percentages
    for data in monthly_data.values():
        if data["total_emails"] > 0:
            data["spam_percentage"] = (data["spam_emails"] / data["total_emails"]) * 100

    for data in yearly_data.values():
        if data["total_emails"] > 0:
            data["spam_percentage"] = (data["spam_emails"] / data["total_emails"]) * 100

    return {
        "summary": {
            "total_emails_analyzed": total_processed,
            "total_spam_emails": total_spam,
            "overall_spam_percentage": (
                (total_spam / total_processed * 100) if total_processed > 0 else 0
            ),
            "keyword_patterns": keyword_patterns,
        },
        "by_month": dict(monthly_data),
        "by_year": dict(yearly_data),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analyze spam keyword frequency over time"
    )
    parser.add_argument("input_file", help="Input email dataset (JSON)")
    parser.add_argument("--output", help="Output file")
    parser.add_argument(
        "--format", choices=["json", "csv"], default="json", help="Output format"
    )
    parser.add_argument("--keywords", help="Custom keyword patterns (JSON file)")

    args = parser.parse_args()

    # Default spam keyword patterns
    default_patterns = {
        "survey": r"\b(survey|questionnaire|feedback|review)\b",
        "rate_us": r"\b(rate\s+us|rating|review\s+us|tell\s+us\s+what)\b",
        "take_minutes": r"\b(take\s+\d+\s+minutes?|quick\s+survey|brief\s+survey)\b",
        "satisfaction": r"\b(satisfaction|experience|service|how\s+did\s+we\s+do)\b",
        "win_prizes": r"\b(win|prize|reward|gift\s+card|enter\s+to\s+win)\b",
        "limited_time": r"\b(limited\s+time|expires|hurry|act\s+now|don't\s+miss)\b",
        "unsubscribe_bait": r"\b(unsubscribe|opt\s+out|remove|preferences)\b",
    }

    # Load custom keywords if provided
    if args.keywords:
        with open(args.keywords, "r") as f:
            custom_patterns = json.load(f)
            default_patterns.update(custom_patterns)

    # Load emails
    with open(args.input_file, "r") as f:
        emails = json.load(f)

    print(f"Analyzing {len(emails)} emails for spam keywords...")

    # Analyze spam patterns
    analysis_data = analyze_spam_keywords(emails, default_patterns)

    # Output results
    if args.output:
        write_data(analysis_data, args.output, args.format)
        print(f"Spam analysis saved to {args.output} ({args.format})")
    else:
        # Console output
        summary = analysis_data["summary"]
        print("\nSpam Keyword Analysis Summary:")
        print(f"  Total emails: {summary['total_emails_analyzed']}")
        print(f"  Spam emails: {summary['total_spam_emails']}")
        print(f"  Spam percentage: {summary['overall_spam_percentage']:.2f}%")

        print("\nTop spam years:")
        yearly_sorted = sorted(
            analysis_data["by_year"].items(),
            key=lambda x: x[1]["spam_percentage"],
            reverse=True,
        )

        for year, data in yearly_sorted[:5]:
            if data["total_emails"] > 10:  # Only show years with meaningful data
                print(
                    f"  {year}: {data['spam_emails']}/{data['total_emails']} "
                    f"({data['spam_percentage']:.1f}%)"
                )


if __name__ == "__main__":
    main()
