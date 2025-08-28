#!/usr/bin/env python3
"""
Thunder Muscle - Single unified tool for Thunderbird email analysis
"""
import sqlite3
import json
import re
import argparse
from pathlib import Path

def extract_domain(email_addr):
    """Extract domain from email address"""
    if not email_addr:
        return "unknown"
    email_str = str(email_addr)
    match = re.search(r'<([^>]+)>|([^\s<>]+@[^\s<>]+)', email_str)
    if match:
        email_clean = match.group(1) or match.group(2)
        domain_match = re.search(r'@([a-zA-Z0-9.-]+)', email_clean)
        return domain_match.group(1).lower() if domain_match else "malformed"
    return "malformed"

def extract_complete_dataset(profile_path, output_file):
    """Extract complete email dataset from Gloda"""
    db_path = Path(profile_path) / "global-messages-db.sqlite"
    if not db_path.exists():
        raise FileNotFoundError(f"Gloda database not found at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    sql = """
        SELECT 
            m.headerMessageID,
            datetime(m.date/1000000, 'unixepoch') as date_formatted,
            t.c3author as from_field,
            t.c4recipients as to_field,
            t.c1subject as subject,
            t.c0body as body_text,
            fl.name as folder_path
        FROM messages m
        LEFT JOIN messagesText_content t ON m.id = t.docid  
        LEFT JOIN folderLocations fl ON m.folderID = fl.id
        ORDER BY m.date DESC
    """
    
    print("Extracting complete dataset from Thunderbird Gloda...")
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    emails = []
    for row in rows:
        msg_id, date, from_field, to_field, subject, body_text, folder_path = row
        emails.append({
            'message_id': f'<{msg_id}>' if msg_id and not msg_id.startswith('<') else msg_id or '',
            'date': date or '',
            'from': from_field or '',
            'from_domain': extract_domain(from_field or ''),
            'to': to_field or '',
            'subject': subject or '',
            'folder': folder_path or '',
            'body': body_text or '',
            'has_body': bool(body_text)
        })
    
    conn.close()
    
    with open(output_file, 'w') as f:
        json.dump(emails, f, indent=2)
    
    with_bodies = sum(1 for e in emails if e['has_body'])
    print(f"Extracted {len(emails)} emails ({with_bodies} with bodies) to {output_file}")

def filter_emails(input_file, output_file, **filters):
    """Filter emails by various criteria"""
    with open(input_file, 'r') as f:
        emails = json.load(f)
    
    results = emails
    
    for key, value in filters.items():
        if key == 'domain' and value:
            results = [e for e in results if e.get('from_domain', '').lower() == value.lower()]
        elif key == 'year' and value:
            results = [e for e in results if value in str(e.get('date', ''))]
        elif key == 'subject_contains' and value:
            results = [e for e in results if value.lower() in e.get('subject', '').lower()]
        elif key == 'has_body' and value:
            results = [e for e in results if e.get('has_body') == True]
        elif key == 'limit' and value:
            results = results[:int(value)]
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Filtered to {len(results)} emails, saved to {output_file}")

def analyze_content(input_file, pattern="unsubscribe", case_sensitive=False):
    """Analyze email content for patterns"""
    with open(input_file, 'r') as f:
        emails = json.load(f)
    
    flags = 0 if case_sensitive else re.IGNORECASE
    regex = re.compile(pattern, flags)
    
    # Analyze both subjects and bodies
    subject_matches = []
    body_matches = []
    
    for email in emails:
        if regex.search(email.get('subject', '')):
            subject_matches.append(email['message_id'])
        if email.get('has_body') and regex.search(email.get('body', '')):
            body_matches.append(email['message_id'])
    
    total_emails = len(emails)
    emails_with_bodies = sum(1 for e in emails if e.get('has_body'))
    
    print(f"Content analysis for pattern: '{pattern}'")
    print(f"  Total emails analyzed: {total_emails}")
    print(f"  Emails with bodies: {emails_with_bodies}")
    print(f"  Matches in subjects: {len(subject_matches)}/{total_emails} ({len(subject_matches)/total_emails*100:.1f}%)")
    if emails_with_bodies > 0:
        print(f"  Matches in bodies: {len(body_matches)}/{emails_with_bodies} ({len(body_matches)/emails_with_bodies*100:.1f}%)")

def stats(input_file):
    """Show dataset statistics"""
    with open(input_file, 'r') as f:
        emails = json.load(f)
    
    domains = {}
    years = {}
    folders = {}
    with_bodies = 0
    
    for email in emails:
        # Count domains
        domain = email.get('from_domain', 'unknown')
        domains[domain] = domains.get(domain, 0) + 1
        
        # Count years
        date = email.get('date', '')
        year = date[:4] if len(date) >= 4 else 'unknown'
        years[year] = years.get(year, 0) + 1
        
        # Count folders
        folder = email.get('folder', 'unknown')
        folders[folder] = folders.get(folder, 0) + 1
        
        if email.get('has_body'):
            with_bodies += 1
    
    print(f"Dataset Statistics:")
    print(f"  Total emails: {len(emails)}")
    print(f"  Emails with bodies: {with_bodies}")
    print(f"  Unique domains: {len(domains)}")
    print(f"  Date range: {min(years.keys())} to {max(years.keys())}")
    print(f"\nTop 10 domains:")
    for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    {domain}: {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Thunder Muscle - Thunderbird email analysis')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract complete dataset from Thunderbird')
    extract_parser.add_argument('--profile', required=True, help='Path to Thunderbird profile')
    extract_parser.add_argument('--output', default='data/complete_dataset.json', help='Output file')
    
    # Filter command
    filter_parser = subparsers.add_parser('filter', help='Filter emails')
    filter_parser.add_argument('input_file', help='Input JSON file')
    filter_parser.add_argument('output_file', help='Output JSON file')
    filter_parser.add_argument('--domain', help='Filter by domain')
    filter_parser.add_argument('--year', help='Filter by year')
    filter_parser.add_argument('--subject-contains', help='Filter by subject content')
    filter_parser.add_argument('--has-body', action='store_true', help='Only emails with bodies')
    filter_parser.add_argument('--limit', type=int, help='Limit results')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze email content')
    analyze_parser.add_argument('input_file', help='Input JSON file')
    analyze_parser.add_argument('--pattern', default='unsubscribe', help='Pattern to search for')
    analyze_parser.add_argument('--case-sensitive', action='store_true', help='Case sensitive search')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show dataset statistics')
    stats_parser.add_argument('input_file', help='Input JSON file')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'extract':
            extract_complete_dataset(args.profile, args.output)
        elif args.command == 'filter':
            filter_emails(args.input_file, args.output_file,
                         domain=args.domain, year=args.year, 
                         subject_contains=args.subject_contains,
                         has_body=args.has_body, limit=args.limit)
        elif args.command == 'analyze':
            analyze_content(args.input_file, args.pattern, args.case_sensitive)
        elif args.command == 'stats':
            stats(args.input_file)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)