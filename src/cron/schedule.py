import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from src.ingestion.docs_ingest import ingest_documents

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.job = None

    async def scheduled_ingestion(self):
        """Scheduled task to run document ingestion"""
        try:
            logger.info(f"Starting scheduled document ingestion at {datetime.utcnow()}")
            count = await ingest_documents()
            logger.info(f"Completed ingestion. Processed {count} documents at {datetime.utcnow()}")
        except Exception as e:
            logger.error(f"Error during scheduled ingestion: {e}")

    def start_scheduler(self):
        """Start the scheduler with daily ingestion"""
        # Get schedule from environment variable or use default (2:00 AM UTC)
        cron_schedule = os.getenv("INGESTION_SCHEDULE", "0 2 * * *")  # Default: daily at 2:00 AM UTC
        
        try:
            # Parse cron schedule
            from apscheduler.triggers.cron import CronTrigger
            trigger = CronTrigger.from_crontab(cron_schedule)
            
            self.job = self.scheduler.add_job(
                self.scheduled_ingestion,
                trigger=trigger,
                id="daily_document_ingestion",
                name="Daily NVIDIA Documentation Ingestion",
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info(f"Scheduler started with document ingestion schedule: {cron_schedule}")
            
        except Exception as e:
            logger.error(f"Invalid cron schedule '{cron_schedule}': {e}")
            logger.info("Using default schedule: 0 2 * * * (daily at 2:00 AM UTC)")
            
            # Fallback to default schedule
            trigger = CronTrigger(hour=2, minute=0)
            self.job = self.scheduler.add_job(
                self.scheduled_ingestion,
                trigger=trigger,
                id="daily_document_ingestion",
                name="Daily NVIDIA Documentation Ingestion",
                replace_existing=True
            )
            self.scheduler.start()

    def stop_scheduler(self):
        """Stop the scheduler gracefully"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def get_scheduler_info(self):
        """Get scheduler information"""
        if self.job:
            return {
                "next_run_time": self.job.next_run_time,
                "trigger": str(self.job.trigger),
                "name": self.job.name
            }
        return {"status": "No active jobs"}

# Global scheduler instance
scheduler = Scheduler()

def start_scheduled_tasks():
    """Start all scheduled tasks"""
    scheduler.start_scheduler()

def stop_scheduled_tasks():
    """Stop all scheduled tasks"""
    scheduler.stop_scheduler()

if __name__ == "__main__":
    # For testing the scheduler
    async def test_scheduler():
        from src.database import connect_to_mongo
        await connect_to_mongo()
        
        # Start scheduler
        start_scheduled_tasks()
        
        # Run immediate ingestion for testing
        print("Running immediate ingestion for testing...")
        count = await ingest_documents()
        print(f"Test ingestion completed: {count} documents")
        
        # Keep running for a while
        try:
            await asyncio.sleep(300)  # 5 minutes
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
        finally:
            stop_scheduled_tasks()
    
    asyncio.run(test_scheduler())