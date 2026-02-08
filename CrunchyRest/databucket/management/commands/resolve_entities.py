"""
Entity resolution batch job.

Matches Tracxn records with Crunchbase records and creates unified Company records.
Runs as a periodic job (cron or Celery beat).

Usage:
    python manage.py resolve_entities
    python manage.py resolve_entities --dry-run
    python manage.py resolve_entities --limit 100
"""

from django.core.management import BaseCommand
from databucket.models import Crunchbase, TracxnRaw, Company
from databucket.entity_resolver import (
    EntityResolver,
    AUTO_MERGE_THRESHOLD,
    REVIEW_THRESHOLD,
)
from tqdm import tqdm


class Command(BaseCommand):
    help = 'Match Tracxn records with Crunchbase and create unified Company records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be matched without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit number of records to process (0 = no limit)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed matching information'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        verbose = options['verbose']

        resolver = EntityResolver()

        # Get all unmatched Tracxn records
        queryset = TracxnRaw.objects.filter(matched=False)
        
        if limit > 0:
            queryset = queryset[:limit]
        
        total_count = queryset.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No unmatched Tracxn records found.'))
            return

        self.stdout.write(f'Processing {total_count} unmatched Tracxn records...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes will be made'))

        stats = {
            'auto_merged': 0,
            'queued_for_review': 0,
            'no_match': 0,
            'errors': 0,
        }

        for tx in tqdm(queryset.iterator(), total=total_count, desc='Resolving'):
            try:
                best_match, best_score = self._find_best_match(resolver, tx, verbose)
                
                if best_score >= AUTO_MERGE_THRESHOLD:
                    if not dry_run:
                        resolver.merge(best_match, tx, best_score)
                    stats['auto_merged'] += 1
                    if verbose:
                        self.stdout.write(f"  AUTO MERGE: {tx.name} -> {best_match.name} ({best_score:.2f})")
                        
                elif best_score >= REVIEW_THRESHOLD:
                    if not dry_run:
                        resolver.queue_for_review(best_match, tx, best_score)
                    stats['queued_for_review'] += 1
                    if verbose:
                        self.stdout.write(f"  REVIEW: {tx.name} -> {best_match.name} ({best_score:.2f})")
                        
                else:
                    # No good match found - create Company from Tracxn alone
                    if not dry_run:
                        resolver.create_from_tracxn(tx)
                    stats['no_match'] += 1
                    if verbose:
                        self.stdout.write(f"  NO MATCH: {tx.name} (best: {best_score:.2f})")
                        
            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(self.style.ERROR(f"Error processing {tx.name}: {e}"))

        # Print summary
        self.stdout.write('')
        self.stdout.write('=' * 50)
        self.stdout.write('Entity Resolution Summary')
        self.stdout.write('=' * 50)
        self.stdout.write(f"  Auto-merged:        {stats['auto_merged']}")
        self.stdout.write(f"  Queued for review:  {stats['queued_for_review']}")
        self.stdout.write(f"  No match (Tracxn only): {stats['no_match']}")
        self.stdout.write(f"  Errors:             {stats['errors']}")
        self.stdout.write('=' * 50)
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                'This was a dry run. Run without --dry-run to apply changes.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('Entity resolution complete!'))

    def _find_best_match(self, resolver: EntityResolver, tx: TracxnRaw, verbose: bool):
        """
        Find the best Crunchbase match for a Tracxn record.
        
        Strategy:
        1. Try exact domain match first (fast, indexed)
        2. Fall back to fuzzy name search
        
        Returns:
            Tuple of (best_match, best_score)
        """
        best_match = None
        best_score = 0.0

        # Step 1: Try domain match first (fast, indexed lookup)
        if tx.normalized_domain:
            cb = Crunchbase.objects.filter(
                normalized_domain=tx.normalized_domain
            ).first()
            
            if cb:
                score = resolver.compute_score(cb, tx)
                if score > best_score:
                    best_match, best_score = cb, score
                    
                # If domain matches and score is high, skip fuzzy search
                if best_score >= AUTO_MERGE_THRESHOLD:
                    return best_match, best_score

        # Step 2: Fall back to fuzzy name search
        if tx.name:
            name_regex = resolver.build_name_regex(tx.name)
            candidates = Crunchbase.objects.filter(
                name__iregex=name_regex
            )[:20]  # Limit candidates for performance
            
            for cb in candidates:
                score = resolver.compute_score(cb, tx)
                if score > best_score:
                    best_match, best_score = cb, score

        return best_match, best_score
