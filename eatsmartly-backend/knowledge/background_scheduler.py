"""
Background Task Scheduler
Manages scheduled tasks like product scraping without blocking the server
"""
import logging
import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class BackgroundTaskScheduler:
    """Manages background tasks with scheduling"""
    
    def __init__(self):
        """Initialize the scheduler"""
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.last_scrape_result = None
        logger.info("✅ Background Task Scheduler initialized")
    
    def start(self):
        """Start the scheduler"""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                self.is_running = True
                logger.info("✅ Background scheduler started")
            else:
                logger.info("ℹ️  Scheduler already running")
        except Exception as e:
            logger.error(f"❌ Error starting scheduler: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("✅ Background scheduler stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
    
    def add_job(
        self,
        func: Callable,
        trigger_type: str = "interval",
        minutes: int = 60,
        job_id: str = None,
        **kwargs
    ):
        """
        Add a job to the scheduler
        
        Args:
            func: Function to execute
            trigger_type: "interval" or "cron"
            minutes: Interval in minutes (for interval trigger)
            job_id: Unique job identifier
            **kwargs: Additional arguments for the trigger
        """
        try:
            if trigger_type == "interval":
                trigger = IntervalTrigger(minutes=minutes)
            elif trigger_type == "cron":
                trigger = CronTrigger(**kwargs)
            else:
                raise ValueError(f"Unknown trigger type: {trigger_type}")
            
            job_id = job_id or f"job_{datetime.now().timestamp()}"
            
            # Remove existing job if it exists
            existing_job = self.scheduler.get_job(job_id)
            if existing_job:
                self.scheduler.remove_job(job_id)
            
            self.scheduler.add_job(
                func,
                trigger,
                id=job_id,
                name=f"Job: {job_id}",
                replace_existing=True
            )
            
            logger.info(f"✅ Added job: {job_id} (trigger: {trigger_type})")
            return {"success": True, "job_id": job_id}
            
        except Exception as e:
            logger.error(f"❌ Error adding job: {e}")
            return {"success": False, "error": str(e)}
    
    def remove_job(self, job_id: str):
        """Remove a job from the scheduler"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"✅ Removed job: {job_id}")
            return {"success": True, "job_id": job_id}
        except Exception as e:
            logger.error(f"❌ Error removing job: {e}")
            return {"success": False, "error": str(e)}
    
    def get_jobs(self):
        """Get all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger),
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
            })
        return jobs
    
    async def schedule_product_scraping(
        self,
        interval_hours: int = 24,
        job_id: str = "background_product_scraper"
    ):
        """
        Schedule the product scraper to run at intervals
        
        Args:
            interval_hours: How often to run scraper (in hours)
            job_id: Unique identifier for the job
        """
        try:
            from agents.background_scraper import get_scraper
            
            async def scrape_job():
                """Wrapper function for the scraper"""
                logger.info(f"\n{'='*80}")
                logger.info(f"⏰ SCHEDULED SCRAPER RUN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*80}")
                
                try:
                    scraper = get_scraper()
                    result = await scraper.run_full_scrape_cycle()
                    
                    self.last_scrape_result = result
                    
                    if result.get("success"):
                        db_results = result.get("database_results", {})
                        logger.info(f"\n✅ SCRAPER SUCCESS!")
                        logger.info(f"   Products added: {db_results.get('total_added', 0)}")
                        logger.info(f"   Products skipped: {db_results.get('total_skipped', 0)}")
                    else:
                        logger.error(f"❌ SCRAPER FAILED: {result.get('error')}")
                    
                except Exception as e:
                    logger.error(f"❌ Scraper job error: {e}")
                    self.last_scrape_result = {"success": False, "error": str(e)}
                
                logger.info(f"{'='*80}\n")
            
            self.add_job(
                scrape_job,
                trigger_type="interval",
                minutes=interval_hours * 60,
                job_id=job_id
            )
            
            logger.info(f"✅ Product scraper scheduled to run every {interval_hours} hours")
            return {
                "success": True,
                "job_id": job_id,
                "interval_hours": interval_hours
            }
            
        except Exception as e:
            logger.error(f"❌ Error scheduling scraper: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_last_scrape_result(self) -> Optional[Dict[str, Any]]:
        """Get the result of the last scheduled scrape"""
        return self.last_scrape_result
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "is_running": self.is_running,
            "jobs": self.get_jobs(),
            "last_scrape_result": self.last_scrape_result,
            "status_updated_at": datetime.now().isoformat()
        }


# Global scheduler instance
_scheduler: Optional[BackgroundTaskScheduler] = None


def get_scheduler() -> BackgroundTaskScheduler:
    """Get or create scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundTaskScheduler()
    return _scheduler


async def initialize_background_tasks():
    """Initialize background tasks when server starts"""
    try:
        logger.info("\n" + "=" * 80)
        logger.info("🚀 INITIALIZING BACKGROUND TASKS")
        logger.info("=" * 80)
        
        scheduler = get_scheduler()
        scheduler.start()
        
        # Schedule product scraper to run every 24 hours
        result = await scheduler.schedule_product_scraping(
            interval_hours=24,
            job_id="background_product_scraper"
        )
        
        if result.get("success"):
            logger.info("✅ Background tasks initialized successfully")
        else:
            logger.error(f"⚠️  Error initializing background tasks: {result.get('error')}")
        
        logger.info("=" * 80 + "\n")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error initializing background tasks: {e}")
        return {"success": False, "error": str(e)}


async def shutdown_background_tasks():
    """Shut down background tasks when server stops"""
    try:
        scheduler = get_scheduler()
        scheduler.stop()
        logger.info("✅ Background tasks shut down")
    except Exception as e:
        logger.error(f"⚠️  Error shutting down background tasks: {e}")
