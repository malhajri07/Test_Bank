"""
Poll Paylink for the status of payments stuck in pending/created states.

Paylink has no server-to-server webhook in this integration, so if a customer
pays and never returns to the callback URL (closed tab, lost connection,
session expired), their payment stays pending and fulfillment never runs.

Run this periodically (e.g. every 5 minutes via cron / Cloud Scheduler) to
catch those cases.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from payments import reconciliation
from payments.models import Payment


class Command(BaseCommand):
    help = 'Reconcile pending Paylink payments by querying the gateway and fulfilling paid ones.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-age-minutes',
            type=int,
            default=2,
            help='Only poll payments older than this many minutes (default: 2).',
        )
        parser.add_argument(
            '--max-age-hours',
            type=int,
            default=24,
            help='Ignore payments older than this (likely abandoned) (default: 24).',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=200,
            help='Maximum number of payments to poll per run (default: 200).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List candidates without calling Paylink or mutating state.',
        )

    def handle(self, *args, **options):
        min_age = options['min_age_minutes']
        max_age = options['max_age_hours']
        limit = options['limit']
        dry_run = options['dry_run']

        now = timezone.now()
        cutoff_old = now - timedelta(minutes=min_age)
        cutoff_abandoned = now - timedelta(hours=max_age)

        candidates = (
            Payment.objects
            .filter(
                payment_provider='paylink',
                status__in=('pending', 'created'),
                provider_session_id__isnull=False,
                created_at__gte=cutoff_abandoned,
                updated_at__lte=cutoff_old,
            )
            .exclude(provider_session_id='')
            .order_by('created_at')[:limit]
        )

        candidates = list(candidates)
        total = len(candidates)
        self.stdout.write(f'Found {total} pending payment(s) to reconcile.')

        if dry_run:
            for p in candidates:
                self.stdout.write(
                    f'  [dry-run] payment={p.pk} user={p.user_id} session={p.provider_session_id} age={now - p.created_at}'
                )
            return

        counts = {
            reconciliation.PAID: 0,
            reconciliation.CANCELLED: 0,
            reconciliation.PENDING: 0,
            reconciliation.ALREADY_PROCESSED: 0,
            reconciliation.MISSING_SESSION: 0,
            reconciliation.ERROR: 0,
        }

        for payment in candidates:
            result = reconciliation.reconcile_payment(payment)
            counts[result] = counts.get(result, 0) + 1
            self.stdout.write(f'  payment={payment.pk} → {result}')

        summary = ', '.join(f'{k}={v}' for k, v in counts.items() if v)
        self.stdout.write(self.style.SUCCESS(f'Done. {summary or "no changes"}.'))
