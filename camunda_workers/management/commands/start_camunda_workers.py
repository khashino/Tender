import logging
import asyncio
import signal
import sys
import traceback
from django.core.management.base import BaseCommand
from camunda_workers.example_worker import ExampleWorker
from camunda_workers.tender_review_worker import TenderReviewWorker

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start Camunda 8 workers'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.should_exit = False
        self.worker = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--worker',
            type=str,
            help='Specific worker to start (e.g., tender_review)'
        )

    def handle(self, *args, **options):
        """Run the async worker."""
        # Set up logging to stdout
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Starting Camunda workers management command")
        
        # Set up signal handlers for Windows
        if sys.platform == 'win32':
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Run the async event loop
            asyncio.run(self.async_handle(*args, **options))
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.should_exit = True
        except Exception as e:
            logger.error(f"Error running worker: {str(e)}")
            logger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
        finally:
            if self.worker:
                try:
                    # Create a new event loop for cleanup
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.worker.stop())
                    loop.close()
                except Exception as e:
                    logger.error(f"Error stopping worker: {str(e)}")
                    logger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
            logger.info("Worker stopped")

    def _signal_handler(self, signum, frame):
        """Handle signals for Windows."""
        logger.info(f"Received signal {signum}")
        self.should_exit = True

    async def async_handle(self, *args, **options):
        """Async handler for running the worker."""
        try:
            worker_name = options.get('worker')
            
            if worker_name == 'tender_review':
                logger.info("Starting tender review worker...")
                self.worker = TenderReviewWorker(worker_id='tender_review_worker')
                
                # Set up signal handlers for non-Windows platforms
                if sys.platform != 'win32':
                    loop = asyncio.get_event_loop()
                    loop.add_signal_handler(signal.SIGINT, self.handle_shutdown)
                    loop.add_signal_handler(signal.SIGTERM, self.handle_shutdown)
                
                self.stdout.write(self.style.SUCCESS(f'Starting worker: {worker_name}'))
                self.stdout.write('Press Ctrl+C to stop the worker')
                
                # Start the worker and keep it running
                try:
                    await self.worker.start()
                except Exception as e:
                    logger.error(f"Worker start failed: {str(e)}")
                    logger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
                    raise
                
                # Keep the event loop running until shutdown signal
                while not self.should_exit:
                    await asyncio.sleep(1)
                
            else:
                self.stdout.write(self.style.WARNING(f'Unknown worker type: {worker_name}'))
                self.stdout.write('Available workers: tender_review')
                return
                
        except Exception as e:
            logger.error(f"Failed to start worker: {str(e)}")
            logger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
            raise

    def handle_shutdown(self):
        """Handle shutdown signal."""
        logger.info("Received shutdown signal")
        self.should_exit = True 