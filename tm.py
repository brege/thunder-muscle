#!/usr/bin/env python3
"""
Thunder Muscle - Thunderbird email dataset API
"""
import sqlite3
import json
import re
import argparse
from pathlib import Path
import sys
sys.path.append('lib')
from output import write_data
from config import load_config, get_profile_path, get_output_format, get_data_directory

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

def extract_complete_dataset(profile_path, output_file, output_format='json'):
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
    
    format_used = write_data(emails, output_file, output_format)
    
    with_bodies = sum(1 for e in emails if e['has_body'])
    print(f"Extracted {len(emails)} emails ({with_bodies} with bodies) to {output_file} ({format_used})")

def filter_emails(input_file, output_file, output_format='json', **filters):
    """Filter emails by various criteria"""
    with open(input_file, 'r') as f:
        emails = json.load(f)
    
    results = emails
    
    for key, value in filters.items():
        if key == 'domain' and value:
            if value.startswith('*.'):
                # Wildcard pattern like *.edu
                domain_suffix = value[2:].lower()
                results = [e for e in results if e.get('from_domain', '').lower().endswith(domain_suffix)]
            else:
                # Exact domain match or regex
                try:
                    domain_regex = re.compile(value, re.IGNORECASE)
                    results = [e for e in results if domain_regex.search(e.get('from_domain', ''))]
                except re.error:
                    # Fall back to exact match if regex is invalid
                    results = [e for e in results if e.get('from_domain', '').lower() == value.lower()]
        elif key == 'year' and value:
            results = [e for e in results if value in str(e.get('date', ''))]
        elif key == 'subject_contains' and value:
            results = [e for e in results if value.lower() in e.get('subject', '').lower()]
        elif key == 'has_body' and value:
            results = [e for e in results if e.get('has_body') == True]
        elif key == 'limit' and value:
            results = results[:int(value)]
    
    format_used = write_data(results, output_file, output_format)
    
    print(f"Filtered to {len(results)} emails, saved to {output_file} ({format_used})")

def query_emails(input_file, pattern=None, case_sensitive=False):
    """Query emails matching pattern, return matching emails"""
    with open(input_file, 'r') as f:
        emails = json.load(f)
    
    if not pattern:
        return emails
    
    flags = 0 if case_sensitive else re.IGNORECASE
    regex = re.compile(pattern, flags)
    
    matches = []
    for email in emails:
        if regex.search(email.get('subject', '')) or \
           (email.get('has_body') and regex.search(email.get('body', ''))):
            matches.append(email)
    
    return matches


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
    extract_parser.add_argument('--profile', help='Path to Thunderbird profile')
    extract_parser.add_argument('--output', help='Output file')
    extract_parser.add_argument('--format', choices=['json', 'csv', 'yaml'], help='Output format')
    
    # Filter command
    filter_parser = subparsers.add_parser('filter', help='Filter emails')
    filter_parser.add_argument('input_file', help='Input JSON file')
    filter_parser.add_argument('output_file', help='Output file')
    filter_parser.add_argument('--domain', help='Filter by domain')
    filter_parser.add_argument('--year', help='Filter by year')
    filter_parser.add_argument('--subject-contains', help='Filter by subject content')
    filter_parser.add_argument('--has-body', action='store_true', help='Only emails with bodies')
    filter_parser.add_argument('--limit', type=int, help='Limit results')
    filter_parser.add_argument('--format', choices=['json', 'csv', 'yaml'], help='Output format')
    
    # Query command  
    query_parser = subparsers.add_parser('query', help='Query emails matching pattern')
    query_parser.add_argument('input_file', help='Input JSON file')
    query_parser.add_argument('output_file', help='Output file')
    query_parser.add_argument('--pattern', help='Pattern to search for')
    query_parser.add_argument('--case-sensitive', action='store_true', help='Case sensitive search')
    query_parser.add_argument('--format', choices=['json', 'csv', 'yaml'], help='Output format')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show dataset statistics')
    stats_parser.add_argument('input_file', help='Input JSON file')
    
    args = parser.parse_args()
    
    try:
        config = load_config()
        
        if args.command == 'extract':
            profile = get_profile_path(config, args.profile)
            data_dir = get_data_directory(config)
            output = args.output or f"{data_dir}/complete_dataset.json"
            output_format = args.format or get_output_format(config)
            extract_complete_dataset(profile, output, output_format)
        elif args.command == 'filter':
            output_format = args.format or get_output_format(config)
            filter_emails(args.input_file, args.output_file, output_format,
                         domain=args.domain, year=args.year, 
                         subject_contains=args.subject_contains,
                         has_body=args.has_body, limit=args.limit)
        elif args.command == 'query':
            output_format = args.format or get_output_format(config)
            results = query_emails(args.input_file, args.pattern, args.case_sensitive)
            format_used = write_data(results, args.output_file, output_format)
            print(f"Found {len(results)} matching emails, saved to {args.output_file} ({format_used})")
        elif args.command == 'stats':
            stats(args.input_file)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)