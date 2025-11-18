"""
Management command to run performance benchmarks.

Usage:
    python manage.py run_benchmarks
    python manage.py run_benchmarks --benchmark-only
    python manage.py run_benchmarks --compare
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import os
import sys


class Command(BaseCommand):
    help = 'Run performance benchmarks using pytest-benchmark'

    def add_arguments(self, parser):
        parser.add_argument(
            '--benchmark-only',
            action='store_true',
            help='Run only benchmark tests'
        )
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare against previous benchmark results'
        )
        parser.add_argument(
            '--save',
            type=str,
            default=None,
            help='Save benchmark results to file'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )

    def handle(self, *args, **options):
        benchmark_only = options['benchmark_only']
        compare = options['compare']
        save = options['save']
        verbose = options['verbose']

        # Benchmark directory
        benchmark_dir = os.path.join(
            settings.BASE_DIR,
            'stress_tests',
            'benchmarks'
        )

        if not os.path.exists(benchmark_dir):
            self.stdout.write(
                self.style.ERROR(f'Benchmark directory not found: {benchmark_dir}')
            )
            return

        # Build pytest command
        cmd = [
            'pytest',
            benchmark_dir,
            '--benchmark-only' if benchmark_only else '--benchmark-autosave',
            '-v' if verbose else '',
        ]

        if compare:
            cmd.append('--benchmark-compare')
        
        if save:
            cmd.extend(['--benchmark-save', save])

        # Remove empty strings
        cmd = [c for c in cmd if c]

        self.stdout.write(
            self.style.SUCCESS('Running performance benchmarks...')
        )

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'Benchmark failed: {e}')
            )
            sys.exit(1)
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    'pytest not found. Install it with: pip install pytest pytest-benchmark'
                )
            )
            sys.exit(1)

