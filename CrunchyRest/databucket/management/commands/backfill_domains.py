"""
Backfill normalized_domain field for existing Crunchbase records.

Usage:
    python manage.py backfill_domains
"""

from django.core.management import BaseCommand
from databucket.models import Crunchbase
from utils.domain import normalize_domain
from tqdm import tqdm


class Command(BaseCommand):
    help = 'Backfill normalized_domain field for existing Crunchbase records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process per batch (default: 100)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']

        # Get all records without normalized_domain
        queryset = Crunchbase.objects.filter(normalized_domain__isnull=True)
        total_count = queryset.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No records need backfilling.'))
            return

        self.stdout.write(f'Found {total_count} records without normalized_domain')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes will be made'))

        updated_count = 0
        skipped_count = 0

        # Process in batches
        for record in tqdm(queryset.iterator(), total=total_count, desc='Backfilling'):
            website = record.website
            domain = normalize_domain(website)

            if domain:
                if not dry_run:
                    record.normalized_domain = domain
                    record.save(update_fields=['normalized_domain'])
                updated_count += 1
            else:
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done! Updated: {updated_count}, Skipped (no valid domain): {skipped_count}'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                'This was a dry run. Run without --dry-run to apply changes.'
            ))
