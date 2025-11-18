"""
Load test report generator.

Parses Locust results and generates HTML reports.
Identifies bottlenecks and compares against previous runs.
"""

import json
import os
from datetime import datetime
from pathlib import Path


def parse_locust_stats(csv_file):
    """Parse Locust CSV stats file."""
    import csv
    stats = {}
    
    if not os.path.exists(csv_file):
        return stats
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip aggregated row
            if row.get('Type', '').strip() == '' or row.get('Name', '').strip() == 'Aggregated':
                continue
            
            endpoint = row.get('Name', '').strip()
            if endpoint:
                try:
                    stats[endpoint] = {
                        'requests': int(row.get('Request Count', 0)),
                        'failures': int(row.get('Failure Count', 0)),
                        'median_response_time': float(row.get('Median Response Time', 0)),
                        'average_response_time': float(row.get('Average Response Time', 0)),
                        'min_response_time': float(row.get('Min Response Time', 0)),
                        'max_response_time': float(row.get('Max Response Time', 0)),
                        'requests_per_second': float(row.get('Requests/s', 0)),
                    }
                except (ValueError, KeyError) as e:
                    # Skip rows with invalid data
                    continue
    
    return stats


def generate_html_report(stats, output_file='stress_tests/reports/report.html'):
    """Generate HTML report from stats."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Load Test Report - {timestamp}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            h1 {{
                color: #333;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                background-color: white;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .warning {{
                color: orange;
                font-weight: bold;
            }}
            .error {{
                color: red;
                font-weight: bold;
            }}
            .success {{
                color: green;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h1>Load Test Report</h1>
        <p>Generated: {timestamp}</p>
        
        <h2>Endpoint Performance</h2>
        <table>
            <tr>
                <th>Endpoint</th>
                <th>Requests</th>
                <th>Failures</th>
                <th>Median RT (ms)</th>
                <th>Avg RT (ms)</th>
                <th>Min RT (ms)</th>
                <th>Max RT (ms)</th>
                <th>RPS</th>
                <th>Status</th>
            </tr>
    """.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    for endpoint, data in stats.items():
        failure_rate = (data['failures'] / data['requests'] * 100) if data['requests'] > 0 else 0
        status_class = 'success'
        status_text = 'OK'
        
        if failure_rate > 1:
            status_class = 'error'
            status_text = 'HIGH FAILURE RATE'
        elif data['average_response_time'] > 1000:
            status_class = 'warning'
            status_text = 'SLOW'
        
        html += f"""
            <tr>
                <td>{endpoint}</td>
                <td>{data['requests']}</td>
                <td>{data['failures']}</td>
                <td>{data['median_response_time']:.2f}</td>
                <td>{data['average_response_time']:.2f}</td>
                <td>{data['min_response_time']:.2f}</td>
                <td>{data['max_response_time']:.2f}</td>
                <td>{data['requests_per_second']:.2f}</td>
                <td class="{status_class}">{status_text}</td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"Report generated: {output_file}")


def identify_bottlenecks(stats):
    """Identify performance bottlenecks."""
    bottlenecks = []
    
    for endpoint, data in stats.items():
        issues = []
        
        if data['average_response_time'] > 1000:
            issues.append(f"Slow response time: {data['average_response_time']:.2f}ms")
        
        failure_rate = (data['failures'] / data['requests'] * 100) if data['requests'] > 0 else 0
        if failure_rate > 1:
            issues.append(f"High failure rate: {failure_rate:.2f}%")
        
        if data['requests_per_second'] < 1:
            issues.append(f"Low throughput: {data['requests_per_second']:.2f} RPS")
        
        if issues:
            bottlenecks.append({
                'endpoint': endpoint,
                'issues': issues
            })
    
    return bottlenecks


def main():
    """Main function to generate report."""
    # Try different possible CSV filenames
    csv_files = [
        'stress_tests/reports/locust_stats.csv',
        'stress_tests/reports/locust_stats_stats.csv',
    ]
    
    csv_file = None
    for f in csv_files:
        if os.path.exists(f):
            csv_file = f
            break
    
    if not csv_file:
        print(f"Stats file not found. Tried: {csv_files}")
        print("Run load tests first to generate stats.")
        return
    
    stats = parse_locust_stats(csv_file)
    
    if not stats:
        print("No stats found in CSV file.")
        return
    
    # Generate HTML report
    generate_html_report(stats)
    
    # Identify bottlenecks
    bottlenecks = identify_bottlenecks(stats)
    
    if bottlenecks:
        print("\nPerformance Bottlenecks Identified:")
        print("=" * 60)
        for bottleneck in bottlenecks:
            print(f"\nEndpoint: {bottleneck['endpoint']}")
            for issue in bottleneck['issues']:
                print(f"  - {issue}")
    else:
        print("\nNo significant bottlenecks identified.")


if __name__ == '__main__':
    main()

