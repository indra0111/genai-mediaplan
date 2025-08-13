import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import concurrent.futures
import json
from genai_mediaplan.utils.forecast_data_api_based import export_table_as_json
from genai_mediaplan.utils.update_forecast_data_in_slides import update_forecast_data_for_cohort
from genai_mediaplan.utils.logger import get_logger

logger = get_logger(__name__)

class ForecastDataScheduler:
    """Scheduler for refreshing cohort datas"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    def _setup_jobs(self):
        """Setup scheduled jobs"""
        # Add scheduled job for cohort data refresh
        self.scheduler.add_job(
            self._scheduled_refresh_cohort_data,
            CronTrigger(day='1-7', day_of_week='sun', hour=22, minute=0),
            id='refresh_cohort_data',
            name='Refresh Cohort Data Weekly',
            replace_existing=True,
            max_instances=1
        )
        logger.info("Scheduled jobs configured")
    
    async def _scheduled_refresh_cohort_data(self):
        """Scheduled job to refresh cohort data"""
        try:
            logger.info("Starting scheduled cohort data refresh...")
            
            # Run in background thread to avoid blocking
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, self.scheduled_refresh_cohort_data)
            
            logger.info("Scheduled cohort data refresh completed successfully")
        except Exception as e:
            logger.error(f"Error in scheduled cohort data refresh: {e}")

    def scheduled_refresh_cohort_data(self):
        try:
            with open('mediaplan_responses.json', 'r') as f:
                data = json.loads(f.read())
            logger.info(f"Starting to refresh all cohort data... Found {len(data)} cohorts")
            for cohort_name in data.keys():
                logger.info(f"Processing cohort: {cohort_name}")
                try:
                    presentation_id = data[cohort_name].get('google_slides_url', '').replace("https://docs.google.com/presentation/d/", "")
                    if not presentation_id:
                        logger.warning(f"No presentation ID found for cohort {cohort_name}, skipping")
                        continue
                    data_to_update = export_table_as_json(cohort_name)
                    forecast_data = data_to_update['results']
                    logger.info(f"Updating data for {cohort_name} with presentation ID {presentation_id}")
                    logger.debug(f"Found {len(forecast_data.keys())} forecast data keys for {cohort_name}")
                    update_forecast_data_for_cohort(forecast_data, presentation_id)
                    logger.info(f"Successfully updated data for {cohort_name}")
                except Exception as e:
                    logger.error(f"Failed to update data for {cohort_name}: {str(e)}")
                    continue
            logger.info("Successfully refreshed all cohort data.")
        
        except Exception as e:
            logger.error(f"Failed to refresh cohort data: {str(e)}")
            
    def start(self):
        """Start the scheduler"""
        try:
            self._setup_jobs()
            self.scheduler.start()
            logger.info("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def get_status(self):
        """Get scheduler status and job information"""
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time),
                    "trigger": str(job.trigger)
                })
            
            return {
                "scheduler_running": self.scheduler.running,
                "jobs": jobs
            }
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {
                "scheduler_running": False,
                "jobs": [],
                "error": str(e)
            }
    
    async def trigger_refresh(self):
        """Manually trigger the cohort data refresh"""
        try:
            logger.info("Manually triggering cohort data refresh...")
            
            # Run in background thread to avoid blocking
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, self._scheduled_refresh_cohort_data)
            
            logger.info("Manual cohort data refresh completed successfully")
            return {"message": "Manual cohort data refresh completed successfully"}
        except Exception as e:
            logger.error(f"Error in manual cohort data refresh: {e}")
            raise e

# Global scheduler instance
scheduler = ForecastDataScheduler()