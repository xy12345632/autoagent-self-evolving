from typing import Any, Callable, Dict, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import logging

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, timezone: str = "Asia/Shanghai"):
        self._scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()},
            job_defaults={
                "coalesce": False,
                "max_instances": 3,
                "misfire_grace_time": 60
            },
            timezone=timezone
        )
        self._task_results: Dict[str, Any] = {}
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        def on_job_executed(event):
            self._task_results[event.job_id] = {
                "status": "success",
                "retval": event.retval,
                "scheduled_time": event.scheduled_run_time
            }
            logger.info(f"Job {event.job_id} executed successfully")

        def on_job_error(event):
            self._task_results[event.job_id] = {
                "status": "error",
                "exception": str(event.exception),
                "scheduled_time": event.scheduled_run_time
            }
            logger.error(f"Job {event.job_id} failed: {event.exception}")

        self._scheduler.add_listener(on_job_executed, EVENT_JOB_EXECUTED)
        self._scheduler.add_listener(on_job_error, EVENT_JOB_ERROR)

    def start(self):
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self, wait: bool = True):
        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
            logger.info("Scheduler shutdown")

    def add_job(
        self,
        func: Callable,
        trigger: BaseTrigger,
        args: Optional[List] = None,
        id: Optional[str] = None,
        name: Optional[str] = None,
        **kwargs
    ):
        job = self._scheduler.add_job(
            func,
            trigger,
            args=args or [],
            id=id,
            name=name,
            **kwargs
        )
        logger.info(f"Job added: {id or job.id}")
        return job

    def remove_job(self, job_id: str):
        try:
            self._scheduler.remove_job(job_id)
            logger.info(f"Job removed: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        jobs = self._scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
                "pending": job.pending
            }
            for job in jobs
        ]

    def pause_job(self, job_id: str) -> bool:
        try:
            self._scheduler.pause_job(job_id)
            logger.info(f"Job paused: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        try:
            self._scheduler.resume_job(job_id)
            logger.info(f"Job resumed: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {e}")
            return False

    def run_job(self, job_id: str) -> bool:
        try:
            job = self._scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=None)
                logger.info(f"Job triggered manually: {job_id}")
                return True
            else:
                logger.warning(f"Job not found: {job_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to run job {job_id}: {e}")
            return False

    def get_task_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._task_results.get(job_id)

    def reschedule_job(self, job_id: str, trigger: BaseTrigger):
        try:
            self._scheduler.reschedule_job(job_id, trigger=trigger)
            logger.info(f"Job rescheduled: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to reschedule job {job_id}: {e}")
            return False
