import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, Any
from pyzeebe import Job
from .base_worker import BaseCamunda8Worker
import traceback
import random

logger = logging.getLogger(__name__)

class TenderReviewWorker(BaseCamunda8Worker):
    """Worker implementation for Tender Application Review process."""

    PROCESS_ID = "tender_application_review"

    def __init__(self, worker_id: str):
        """Initialize the worker and register task handlers."""
        logger.info(f"Initializing TenderReviewWorker with ID: {worker_id}")
        super().__init__(worker_id)
        
        logger.info("Registering task handlers...")
        
        # Register task handlers for the process
        self.worker.task('start_process')(self.handle_start_process)
        self.worker.task('purchase_expert_review')(self.handle_purchase_expert_review)
        self.worker.task('check_purchase_expert_decision')(self.handle_check_purchase_expert_decision)
        
        logger.info("Task handlers registered successfully")

    def _log_job_details(self, job: Job, task_name: str):
        """Helper method to log job details."""
        logger.info("=" * 50)
        logger.info(f"Received {task_name} task")
        logger.info(f"Job Key: {job.key}")
        logger.info(f"Process Instance Key: {job.process_instance_key}")
        logger.info(f"Element ID: {job.element_id}")
        logger.info(f"Element Instance Key: {job.element_instance_key}")
        logger.info(f"Worker: {job.worker}")
        
        # Convert mappingproxy to dict for JSON serialization
        custom_headers = dict(job.custom_headers) if job.custom_headers else {}
        variables = dict(job.variables) if job.variables else {}
        
        logger.info(f"Custom Headers: {json.dumps(custom_headers, indent=2)}")
        logger.info(f"Variables: {json.dumps(variables, indent=2)}")
        logger.info("=" * 50)

    async def handle_start_process(self, job: Job) -> Dict[str, Any]:
        """Handle the start process task."""
        try:
            self._log_job_details(job, "Start Process")
            
            variables = dict(job.variables)  # Convert to regular dict
            application_id = variables.get('applicationId')
            logger.info(f"Processing start task for application {application_id}")
            
            # Process the task
            logger.info("Updating process status and timestamps")
            result = {
                'startTime': datetime.now().isoformat(),
                'status': 'IN_REVIEW',
                'currentStep': 'PURCHASE_EXPERT_REVIEW'
            }
            
            logger.info(f"Task completed successfully. Returning result: {json.dumps(result, indent=2)}")
            return result
            
        except Exception as e:
            error_msg = f"Error in start process task: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
            try:
                await job.fail(message=error_msg)
            except Exception as fail_error:
                logger.error(f"Error failing job: {str(fail_error)}")
            return {}

    async def handle_purchase_expert_review(self, job: Job) -> Dict[str, Any]:
        """Handle the purchase expert review task."""
        try:
            self._log_job_details(job, "Purchase Expert Review")
            
            variables = dict(job.variables)  # Convert to regular dict
            application_id = variables.get('applicationId')
            logger.info(f"Processing purchase expert review for application {application_id}")
            
            # Process the task with delays to simulate work
            logger.info("Starting purchase expert review process...")
            logger.info("Step 1/3: Checking application details")
            await asyncio.sleep(3)  # Wait 3 seconds
            
            logger.info("Step 2/3: Creating human task for expert review")
            await asyncio.sleep(4)  # Wait 4 seconds
            
            logger.info("Step 3/3: Waiting for human input...")
            await asyncio.sleep(3)  # Wait 3 seconds
            
            # Create human task
            task_id = str(job.key)  # Use the job key as the task ID
            logger.info("=" * 50)
            logger.info("HUMAN TASK CREATED - USE THIS INFORMATION TO COMPLETE THE TASK:")
            logger.info(f"Task ID: {task_id}")
            logger.info(f"Application ID: {application_id}")
            logger.info("To complete this task, run one of these commands:")
            logger.info(f"python manage.py complete_human_task --task-id {task_id} --decision approve")
            logger.info(f"python manage.py complete_human_task --task-id {task_id} --decision reject")
            logger.info("=" * 50)
            
            # Return task information
            result = {
                'purchaseExpertReview': {
                    'reviewerId': 'PE001',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'PENDING_DECISION',
                    'taskId': task_id,
                    'assignee': 'purchase.expert@company.com'
                },
                'status': 'AWAITING_DECISION',
                'currentStep': 'CHECK_PURCHASE_EXPERT_DECISION'
            }
            
            logger.info(f"Human task created successfully. Returning result: {json.dumps(result, indent=2)}")
            return result
            
        except Exception as e:
            error_msg = f"Error in purchase expert review: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
            try:
                await job.fail(message=error_msg)
            except Exception as fail_error:
                logger.error(f"Error failing job: {str(fail_error)}")
            return {}

    async def handle_check_purchase_expert_decision(self, job: Job) -> Dict[str, Any]:
        """Handle checking the purchase expert's decision."""
        try:
            self._log_job_details(job, "Check Purchase Expert Decision")
            
            variables = dict(job.variables)
            application_id = variables.get('applicationId')
            task_id = variables.get('purchaseExpertReview', {}).get('taskId')
            
            logger.info(f"Checking decision for application {application_id}, task {task_id}")
            
            # Get the decision from the variables
            decision = variables.get('decision', 'REJECTED')  # Default to REJECTED if no decision
            is_approved = variables.get('is_approved', False)  # Default to False if not set
            comment = variables.get('comment', 'No comment provided')
            
            result = {
                'purchaseExpertReview': {
                    **variables.get('purchaseExpertReview', {}),  # Keep existing review data
                    'status': 'COMPLETED',
                    'decision': decision,
                    'decisionTimestamp': datetime.now().isoformat(),
                    'comments': comment
                },
                'status': 'COMPLETED',
                'currentStep': 'COMPLETED',
                'is_approved': is_approved
            }
            
            logger.info(f"Decision processed. Returning result: {json.dumps(result, indent=2)}")
            return result
            
        except Exception as e:
            error_msg = f"Error checking purchase expert decision: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
            try:
                await job.fail(message=error_msg)
            except Exception as fail_error:
                logger.error(f"Error failing job: {str(fail_error)}")
            return {} 