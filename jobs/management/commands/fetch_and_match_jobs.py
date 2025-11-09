"""
Django management command to fetch jobs and match them to users.
"""
from django.core.management.base import BaseCommand
from jobs.services.fetcher import fetch_all_sources
from jobs.services.matcher import match_and_notify
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch job postings from all sources and match them to users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Fetch jobs but do not send emails',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('  Fetch and Match Jobs Command'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write('')
        
        # Step 1: Fetch jobs
        self.stdout.write('Step 1: Fetching jobs from all sources...')
        try:
            fetch_results = fetch_all_sources()
            
            total_fetched = sum(fetch_results.values())
            self.stdout.write(self.style.SUCCESS(f'  ✓ Fetched {total_fetched} new jobs'))
            
            for source, count in fetch_results.items():
                self.stdout.write(f'    - {source}: {count} jobs')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error fetching jobs: {e}'))
            return
        
        self.stdout.write('')
        
        # Step 2: Match and notify
        if dry_run:
            self.stdout.write(self.style.WARNING('Step 2: Skipped (dry-run mode)'))
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Run without --dry-run to match and notify users'))
        else:
            self.stdout.write('Step 2: Matching jobs to users and sending notifications...')
            try:
                match_results = match_and_notify()
                
                self.stdout.write(self.style.SUCCESS(f'  ✓ Processed {match_results["users_processed"]} users'))
                self.stdout.write(f'    - Jobs matched: {match_results["jobs_matched"]}')
                self.stdout.write(f'    - Emails sent: {match_results["emails_sent"]}')
                
                if match_results['errors'] > 0:
                    self.stdout.write(self.style.WARNING(f'    - Errors: {match_results["errors"]}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error matching/notifying: {e}'))
                import traceback
                self.stdout.write(traceback.format_exc())
                return
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('  Complete!'))
        self.stdout.write(self.style.SUCCESS('='*60))
