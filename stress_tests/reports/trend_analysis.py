"""
Performance trend analysis.

Tracks performance over time and identifies regressions.
"""

import json
import os
from datetime import datetime
from pathlib import Path


def load_benchmark_results(benchmark_dir='stress_tests/reports/benchmarks'):
    """Load benchmark results from storage."""
    results = []
    
    if not os.path.exists(benchmark_dir):
        return results
    
    for file in Path(benchmark_dir).glob('*.json'):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                results.append({
                    'file': file.name,
                    'timestamp': datetime.fromtimestamp(file.stat().st_mtime),
                    'data': data
                })
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    # Sort by timestamp
    results.sort(key=lambda x: x['timestamp'])
    
    return results


def compare_benchmarks(old_result, new_result):
    """Compare two benchmark results."""
    comparisons = []
    
    if 'benchmarks' not in old_result['data'] or 'benchmarks' not in new_result['data']:
        return comparisons
    
    old_benchmarks = {b['name']: b for b in old_result['data']['benchmarks']}
    new_benchmarks = {b['name']: b for b in new_result['data']['benchmarks']}
    
    for name, new_bench in new_benchmarks.items():
        if name in old_benchmarks:
            old_bench = old_benchmarks[name]
            
            old_mean = old_bench.get('stats', {}).get('mean', 0)
            new_mean = new_bench.get('stats', {}).get('mean', 0)
            
            if old_mean > 0:
                change_percent = ((new_mean - old_mean) / old_mean) * 100
                
                comparisons.append({
                    'name': name,
                    'old_mean': old_mean,
                    'new_mean': new_mean,
                    'change_percent': change_percent,
                    'regression': change_percent > 10  # 10% slower is regression
                })
    
    return comparisons


def generate_trend_report(output_file='stress_tests/reports/trend_report.html'):
    """Generate trend analysis report."""
    results = load_benchmark_results()
    
    if len(results) < 2:
        print("Need at least 2 benchmark runs to generate trend report.")
        return
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Performance Trend Analysis</title>
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
            .regression {{
                color: red;
                font-weight: bold;
            }}
            .improvement {{
                color: green;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h1>Performance Trend Analysis</h1>
        <p>Generated: {timestamp}</p>
    """.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Compare latest with previous
    latest = results[-1]
    previous = results[-2]
    
    comparisons = compare_benchmarks(previous, latest)
    
    if comparisons:
        html += """
        <h2>Performance Comparison</h2>
        <p>Comparing: {previous_time} vs {latest_time}</p>
        <table>
            <tr>
                <th>Benchmark</th>
                <th>Previous Mean (s)</th>
                <th>Current Mean (s)</th>
                <th>Change</th>
                <th>Status</th>
            </tr>
        """.format(
            previous_time=previous['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            latest_time=latest['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        )
        
        for comp in comparisons:
            status_class = 'regression' if comp['regression'] else 'improvement'
            status_text = 'REGRESSION' if comp['regression'] else 'OK'
            change_sign = '+' if comp['change_percent'] > 0 else ''
            
            html += f"""
            <tr>
                <td>{comp['name']}</td>
                <td>{comp['old_mean']:.6f}</td>
                <td>{comp['new_mean']:.6f}</td>
                <td>{change_sign}{comp['change_percent']:.2f}%</td>
                <td class="{status_class}">{status_text}</td>
            </tr>
            """
        
        html += "</table>"
    
    html += """
    </body>
    </html>
    """
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"Trend report generated: {output_file}")
    
    # Print regressions
    regressions = [c for c in comparisons if c['regression']]
    if regressions:
        print("\nPerformance Regressions Detected:")
        print("=" * 60)
        for reg in regressions:
            print(f"{reg['name']}: {reg['change_percent']:.2f}% slower")


def main():
    """Main function."""
    generate_trend_report()


if __name__ == '__main__':
    main()

