import os
import logging
import asyncio
from typing import Dict, Any, Optional
from pyzeebe import ZeebeWorker, ZeebeClient, Job, create_insecure_channel
from django.conf import settings

logger = logging.getLogger(__name__)

class BaseCamunda8Worker:
    """Base class for Camunda 8 workers using Zeebe."""
    
    def __init__(self, worker_id: str):
        """Initialize the worker with configuration."""
        logger.info(f"Initializing base worker with ID: {worker_id}")
        
        # Store the worker_id
        self.worker_id = worker_id
        
        # Get configuration from Django settings or environment variables
        self.zeebe_hostname = getattr(settings, 'ZEEBE_HOSTNAME', os.getenv('ZEEBE_HOSTNAME', 'localhost'))
        self.zeebe_port = int(getattr(settings, 'ZEEBE_PORT', os.getenv('ZEEBE_PORT', '26500')))
        self.use_tls = getattr(settings, 'ZEEBE_USE_TLS', False)
        
        logger.info(f"Zeebe configuration: hostname={self.zeebe_hostname}, port={self.zeebe_port}, tls={self.use_tls}")
        
        try:
            # Create the gRPC channel
            logger.info("Creating gRPC channel...")
            self.channel = create_insecure_channel(f"{self.zeebe_hostname}:{self.zeebe_port}")
            logger.info("gRPC channel created successfully")
            
            # Initialize Zeebe worker and client
            logger.info("Initializing Zeebe worker...")
            self.worker = ZeebeWorker(
                grpc_channel=self.channel,
                name=worker_id,  # Use the worker_id directly here
                max_connection_retries=10
            )
            logger.info("ZeebeWorker initialized successfully")
            
            logger.info("Initializing Zeebe client...")
            self.client = ZeebeClient(
                grpc_channel=self.channel,
                max_connection_retries=10
            )
            logger.info("ZeebeClient initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing worker: {str(e)}")
            raise

    async def handle_job(self, job: Job) -> Dict[str, Any]:
        """
        Main job handler to be implemented by subclasses.
        
        Args:
            job: The Zeebe job to process
            
        Returns:
            Dict[str, Any]: Variables to be passed back to the workflow
        """
        raise NotImplementedError("Subclasses must implement handle_job method")

    def task_handler(self, task_type: str, timeout_ms: Optional[int] = None):
        """Decorator to register a task handler."""
        logger.info(f"Registering task handler for type: {task_type}")
        return self.worker.task(task_type, timeout_ms=timeout_ms)

    async def start(self):
        """Start the worker to handle jobs."""
        logger.info("Starting worker...")
        try:
            logger.info("Connecting to Zeebe...")
            await self.worker.work()
            logger.info("Worker started and connected to Zeebe successfully")
        except Exception as e:
            logger.error(f"Failed to start worker: {str(e)}")
            raise

    async def stop(self):
        """Stop the worker."""
        logger.info("Stopping worker...")
        try:
            # Stop accepting new jobs
            logger.info("Stopping worker from accepting new jobs...")
            await self.worker.stop()
            logger.info("Worker stopped accepting new jobs")
            
            # Close the gRPC channel
            if hasattr(self.channel, 'close'):
                logger.info("Closing gRPC channel...")
                await self.channel.close()
                logger.info("gRPC channel closed successfully")
            
            logger.info("Worker stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping worker: {str(e)}")
            raise

    async def complete_job(self, job: Job, variables: Optional[Dict[str, Any]] = None):
        """Complete a job with variables."""
        try:
            logger.info(f"Completing job {job.key} with variables: {variables}")
            await job.complete(variables or {})
            logger.info(f"Job {job.key} completed successfully")
        except Exception as e:
            logger.error(f"Error completing job {job.key}: {str(e)}")
            raise

    async def fail_job(self, job: Job, message: str):
        """Fail a job with the given message."""
        logger.error(f"Failing job {job.key} with message: {message}")
        try:
            await job.fail(message=message)
            logger.info(f"Job {job.key} failed successfully")
        except Exception as e:
            logger.error(f"Error failing job: {str(e)}")
            raise

    async def error_job(self, job: Job, error_code: str, error_message: str = None):
        """Throw a BPMN error for a job."""
        try:
            logger.info(f"Throwing BPMN error for job {job.key}: {error_code} - {error_message}")
            await job.error(error_code=error_code, error_message=error_message)
            logger.info(f"BPMN error thrown successfully for job {job.key}")
        except Exception as e:
            logger.error(f"Error throwing BPMN error for job {job.key}: {str(e)}")
            raise

    async def create_process_instance(self, bpmn_process_id: str, variables: Dict[str, Any] = None):
        """Create a new process instance."""
        logger.info(f"Creating process instance for {bpmn_process_id}")
        logger.info(f"Process variables: {variables}")
        try:
            result = await self.client.run_process(
                bpmn_process_id=bpmn_process_id,
                variables=variables or {}
            )
            logger.info(f"Process instance created successfully: {result.process_instance_key}")
            return result
        except Exception as e:
            logger.error(f"Failed to create process instance: {str(e)}")
            raise

    async def complete_task(self, task_id: str, variables: Dict[str, Any]):
        """Complete a task with the given variables."""
        logger.info(f"Completing task {task_id} with variables: {variables}")
        
        # Create a temporary worker to handle the task
        task_worker = ZeebeWorker(
            grpc_channel=self.channel,
            name=f"task_completer_{task_id}",
            max_jobs_to_activate=1,
            timeout=10000,  # 10 seconds
            max_running_jobs=1,
            poll_interval=100  # 100ms
        )
        
        # Define the task handler
        @task_worker.task(task_type="io.camunda.zeebe:userTask")
        async def handle_task(job: Job):
            if str(job.key) == task_id:
                logger.info(f"Found matching task {task_id}, completing with variables")
                return variables
            else:
                logger.info(f"Task {job.key} does not match target task {task_id}, skipping")
                return None
        
        try:
            # Start the worker
            logger.info("Starting task worker")
            await task_worker.work()
            
            # Wait for a short time to allow the worker to process the task
            await asyncio.sleep(5)
            
            logger.info("Task completion attempt finished")
        finally:
            # Stop the worker
            logger.info("Stopping task worker")
            await task_worker.stop()
            logger.info("Task worker stopped") 