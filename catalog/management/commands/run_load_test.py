"""
Management command to run Locust load tests.

Usage:
    python manage.py run_load_test --scenario=normal --users=50 --spawn-rate=2 --duration=10m
    python manage.py run_load_test --scenario=practice --users=100 --spawn-rate=5
"""

import os
import subprocess
import sys

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run Locust load tests with predefined scenarios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--scenario',
            type=str,
            default='normal',
            choices=['normal', 'practice', 'payment', 'mixed', 'spike'],
            help='Load test scenario to run'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Number of concurrent users'
        )
        parser.add_argument(
            '--spawn-rate',
            type=int,
            default=2,
            help='Users to spawn per second'
        )
        parser.add_argument(
            '--duration',
            type=str,
            default='10m',
            help='Test duration (e.g., 10m, 5m, 1h)'
        )
        parser.add_argument(
            '--host',
            type=str,
            default='http://localhost:8000',
            help='Target host URL'
        )
        parser.add_argument(
            '--headless',
            action='store_true',
            help='Run in headless mode (no web UI)'
        )
        parser.add_argument(
            '--html-report',
            type=str,
            default=None,
            help='Path to save HTML report'
        )

    def handle(self, *args, **options):
        scenario = options['scenario']
        users = options['users']
        spawn_rate = options['spawn_rate']
        duration = options['duration']
        host = options['host']
        headless = options['headless']
        html_report = options['html_report']

        # Locust file path
        locustfile = os.path.join(
            settings.BASE_DIR,
            'stress_tests',
            'locustfile.py'
        )

        if not os.path.exists(locustfile):
            self.stdout.write(
                self.style.ERROR(f'Locust file not found: {locustfile}')
            )
            return

        # Build Locust command
        cmd = [
            'locust',
            '-f', locustfile,
            '--host', host,
            '--users', str(users),
            '--spawn-rate', str(spawn_rate),
            '--run-time', duration,
        ]

        if headless:
            cmd.append('--headless')
            if html_report:
                cmd.extend(['--html', html_report])
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Running in interactive mode. Open http://localhost:8089 to view results.'
                )
            )

        # Select user class based on scenario
        user_classes = {
            'normal': 'MixedTrafficUser',
            'practice': 'PracticeExamUser',
            'payment': 'PaymentUser',
            'mixed': 'MixedTrafficUser',
            'spike': 'MixedTrafficUser',
        }

        user_class = user_classes.get(scenario, 'MixedTrafficUser')
        cmd.extend(['--user-class', user_class])

        self.stdout.write(
            self.style.SUCCESS(
                f'Running load test scenario: {scenario}\n'
                f'Users: {users}, Spawn Rate: {spawn_rate}/s, Duration: {duration}\n'
                f'Target: {host}'
            )
        )

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'Load test failed: {e}')
            )
            sys.exit(1)
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    'Locust not found. Install it with: pip install locust'
                )
            )
            sys.exit(1)

