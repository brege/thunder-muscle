#!/usr/bin/env python3
"""
Domain analysis tool using tm.py API and lib output adapters
"""
import json
import subprocess
import sys
import argparse
from collections import Counter
sys.path.append('lib')
from output import write_data
from config import load_config, get_output_format

def get_pattern_emails(input_file, pattern='unsubscribe'):
    """Get emails containing pattern using tm.py"""
    cmd = ['python3', 'tm.py', 'query', input_file, '/tmp/pattern_matches.json', 
           '--pattern', pattern, '--format', 'json']
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error querying emails: {result.stderr}")
        sys.exit(1)
    
    with open('/tmp/pattern_matches.json', 'r') as f:
        return json.load(f)

def analyze_top_domains(emails, threshold=0.95):
    """Find domains producing threshold% of pattern-matching emails"""
    domain_counts = Counter(email['from_domain'] for email in emails)
    total = len(emails)
    
    sorted_domains = domain_counts.most_common()
    cumulative = 0
    top_domains = []
    
    for domain, count in sorted_domains:
        cumulative += count
        percentage = count / total * 100
        cumulative_percentage = cumulative / total
        
        top_domains.append({
            'domain': domain,
            'count': count,
            'percentage': percentage,
            'cumulative_percentage': cumulative_percentage
        })
        
        if cumulative_percentage >= threshold:
            break
    
    return top_domains, cumulative / total

def main():
    parser = argparse.ArgumentParser(description='Domain analysis for email patterns')
    parser.add_argument('input_file', help='Input dataset file')
    parser.add_argument('compare_pattern', help='Domain pattern to compare (e.g., wsu.edu)')
    parser.add_argument('--pattern', default='unsubscribe', help='Email content pattern to analyze (default: unsubscribe)')
    parser.add_argument('--output', help='Output file for analysis results')
    parser.add_argument('--format', choices=['json', 'csv', 'yaml'], help='Output format')
    parser.add_argument('--threshold', type=float, default=0.95, help='Coverage threshold (default: 0.95)')
    
    args = parser.parse_args()
    
    config = load_config()
    
    pattern_emails = get_pattern_emails(args.input_file, args.pattern)
    top_domains, coverage = analyze_top_domains(pattern_emails, args.threshold)
    
    # Get comparison emails
    domain_pattern = args.compare_pattern if not args.compare_pattern.startswith('*.') else args.compare_pattern
    cmd = ['python3', 'tm.py', 'filter', args.input_file, '/tmp/compare_emails.json',
           '--domain', domain_pattern, '--format', 'json']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    with open('/tmp/compare_emails.json', 'r') as f:
        compare_emails = json.load(f)
    
    # Prepare analysis results
    analysis_results = {
        'pattern_analysis': {
            'pattern': args.pattern,
            'total_emails': len(pattern_emails),
            'coverage_threshold': args.threshold,
            'actual_coverage': coverage,
            'top_domains': top_domains
        },
        'comparison': {
            'pattern': args.compare_pattern,
            'total_emails': len(compare_emails),
            'domains': list(set(email['from_domain'] for email in compare_emails))
        }
    }
    
    # Find overlap
    compare_domains = set(email['from_domain'] for email in compare_emails)
    top_domain_names = set(d['domain'] for d in top_domains)
    overlap = list(compare_domains.intersection(top_domain_names))
    analysis_results['overlap'] = overlap
    
    if args.output:
        output_format = args.format or get_output_format(config)
        format_used = write_data(analysis_results, args.output, output_format)
        print(f"Analysis saved to {args.output} ({format_used})")
    else:
        # Console output
        print(f"Pattern Analysis ('{args.pattern}'):")
        print(f"  Total pattern emails: {len(pattern_emails)}")
        print(f"  Top domains cover {coverage*100:.1f}% of pattern volume:")
        for i, domain_info in enumerate(top_domains, 1):
            print(f"    {i:2d}. {domain_info['domain']:<30} {domain_info['count']:>5} ({domain_info['percentage']:>5.1f}%)")
        print(f"\nComparison with {args.compare_pattern}:")
        print(f"  Total {args.compare_pattern} emails: {len(compare_emails)}")
        if overlap:
            print(f"  Overlap domains: {', '.join(overlap)}")
        else:
            print(f"  No overlap between top pattern domains and {args.compare_pattern}")

if __name__ == "__main__":
    main()