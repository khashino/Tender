import logging
from typing import Dict, Any
from pyzeebe import Job
from .base_worker import BaseCamunda8Worker

logger = logging.getLogger(__name__)

class ExampleWorker(BaseCamunda8Worker):
    """Example worker implementation for Camunda 8."""

    def __init__(self, worker_id: str):
        super().__init__(worker_id)
        
        # Register the task handler using the decorator
        @self.task_handler('example-task')
        async def handle_example_task(job: Job) -> Dict[str, Any]:
            return await self.handle_job(job)

    async def handle_job(self, job: Job) -> Dict[str, Any]:
        """
        Handle the example job.
        
        This is where you implement your business logic.
        """
        try:
            # Get variables from the job
            variables = job.variables
            logger.info(f"Processing job {job.key} with variables: {variables}")

            # Example: Process a "data" variable
            data = variables.get('data')
            if not data:
                await self.fail_job(
                    job,
                    message="Missing required 'data' variable",
                    retries=job.retries - 1 if job.retries else 0
                )
                return {}

            # Example processing logic
            result = self._process_data(data)

            # Return variables to be passed back to the workflow
            return {
                'processedData': result,
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Error processing job {job.key}: {str(e)}")
            await self.fail_job(
                job,
                message=f"Job processing failed: {str(e)}",
                retries=job.retries - 1 if job.retries else 0
            )
            return {}

    def _process_data(self, data: str) -> str:
        """
        Example data processing method.
        Replace this with your actual business logic.
        """
        # Example: Convert data to uppercase
        return data.upper() 