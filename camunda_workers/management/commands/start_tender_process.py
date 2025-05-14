import logging
import asyncio
from django.core.management.base import BaseCommand
from camunda_workers.tender_review_worker import TenderReviewWorker

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Starts a new tender review process instance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--application-id',
            type=str,
            required=True,
            help='The tender application ID'
        )

    def handle(self, *args, **options):
        """Run the async process starter."""
        try:
            asyncio.run(self.async_handle(*args, **options))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error starting process: {str(e)}'))

    async def async_handle(self, *args, **options):
        """Async handler for starting the process."""
        try:
            # Create a temporary worker instance to use its client
            worker = TenderReviewWorker(worker_id='process_starter')
            
            # Prepare process variables
            variables = {
                'applicationId': options['application_id'],
                'status': 'SUBMITTED',
                'currentStep': 'START_PROCESS'
            }

            # Start the process
            self.stdout.write(f'Starting tender review process for application {options["application_id"]}...')
            result = await worker.create_process_instance(
                bpmn_process_id=TenderReviewWorker.PROCESS_ID,
                variables=variables
            )
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully started process instance. Process ID: {result.process_instance_key}'
            ))
            
            # Clean up
            await worker.stop()
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Failed to start process: {str(e)}'))
            raise 