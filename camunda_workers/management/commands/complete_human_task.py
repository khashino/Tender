import logging
import asyncio
import aiohttp
import json
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Complete a human task in the tender review process'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task-id',
            type=str,
            required=True,
            help='The task ID to complete'
        )
        parser.add_argument(
            '--decision',
            type=str,
            choices=['approve', 'reject'],
            required=True,
            help='The decision to make (approve/reject)'
        )
        parser.add_argument(
            '--comment',
            type=str,
            default='Task reviewed and decision made',
            help='Optional comment for the decision'
        )

    def handle(self, *args, **options):
        """Run the async task completion."""
        try:
            logger.info("Starting task completion command")
            asyncio.run(self.async_handle(*args, **options))
        except Exception as e:
            error_msg = f'Error completing task: {str(e)}'
            logger.error(error_msg)
            self.stderr.write(self.style.ERROR(error_msg))

    async def async_handle(self, *args, **options):
        """Async handler for completing the task."""
        try:
            # Get parameters
            task_id = options['task_id']
            decision = options['decision']
            comment = options['comment']
            
            logger.info(f"Completing task {task_id} with decision: {decision}")
            logger.info(f"Additional comment: {comment}")
            
            # Prepare variables for task completion
            variables = {
                'decision': decision.upper(),
                'comment': comment,
                'status': 'COMPLETED',
                'is_approved': decision == 'approve'
            }
            
            logger.info(f"Prepared variables: {variables}")
            
            # Complete the task using REST API
            try:
                # Zeebe REST API endpoint for completing jobs
                api_url = f"http://localhost:26500/jobs/{task_id}/complete"
                
                logger.info(f"Sending complete task request to: {api_url}")
                
                payload = {
                    'variables': variables
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        api_url,
                        json=payload,
                        headers={
                            'Content-Type': 'application/json'
                        }
                    ) as response:
                        response_text = await response.text()
                        if response.status in [200, 204]:
                            success_msg = f'Successfully completed task {task_id} with decision: {decision}'
                            logger.info(success_msg)
                            self.stdout.write(self.style.SUCCESS(success_msg))
                        else:
                            error_msg = f'Failed to complete task. Status: {response.status}, Response: {response_text}'
                            logger.error(error_msg)
                            self.stderr.write(self.style.ERROR(error_msg))
                            raise Exception(error_msg)
                            
            except Exception as e:
                error_msg = f'Failed to complete task: {str(e)}'
                logger.error(error_msg)
                self.stderr.write(self.style.ERROR(error_msg))
                raise
            
        except Exception as e:
            error_msg = f'Error in task completion: {str(e)}'
            logger.error(error_msg)
            self.stderr.write(self.style.ERROR(error_msg))
            raise 