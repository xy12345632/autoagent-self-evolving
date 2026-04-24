from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future
import asyncio
import logging

logger = logging.getLogger(__name__)


class TaskExecutor:
    def __init__(self, max_workers: int = 4, max_retries: int = 3):
        self._max_workers = max_workers
        self._max_retries = max_retries
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._retry_count: Dict[str, int] = {}
        self._task_results: Dict[str, Any] = {}

    async def execute_task(self, task_id: str, func: Callable, *args, **kwargs) -> Any:
        self._tasks[task_id] = {
            "id": task_id,
            "status": "running",
            "start_time": datetime.now(),
            "func": func,
            "args": args,
            "kwargs": kwargs
        }

        try:
            logger.info(f"Executing task: {task_id}")

            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(self._executor, lambda: func(*args, **kwargs))

            self._tasks[task_id]["status"] = "completed"
            self._tasks[task_id]["end_time"] = datetime.now()
            self._task_results[task_id] = result
            logger.info(f"Task completed: {task_id}")

            return result

        except Exception as e:
            logger.error(f"Task failed: {task_id} - {e}")
            self._tasks[task_id]["status"] = "failed"
            self._tasks[task_id]["error"] = str(e)
            self._tasks[task_id]["end_time"] = datetime.now()

            retry_success = await self.retry_failed_task(task_id, func, *args, **kwargs)
            if retry_success:
                return self._task_results.get(task_id)
            raise

    async def execute_scheduled(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        result = await self.execute_task(task_id, func, *args, **kwargs)
        return {
            "task_id": task_id,
            "result": result,
            "status": self._tasks.get(task_id, {}).get("status", "unknown"),
            "timestamp": datetime.now().isoformat()
        }

    async def retry_failed_task(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ) -> bool:
        current_retry = self._retry_count.get(task_id, 0)

        if current_retry >= self._max_retries:
            logger.warning(f"Max retries reached for task: {task_id}")
            return False

        self._retry_count[task_id] = current_retry + 1
        logger.info(f"Retrying task: {task_id} (attempt {current_retry + 1}/{self._max_retries})")

        await asyncio.sleep(min(2 ** current_retry, 60))

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(self._executor, lambda: func(*args, **kwargs))

            self._tasks[task_id]["status"] = "completed"
            self._tasks[task_id]["retry_success"] = True
            self._task_results[task_id] = result
            self._retry_count[task_id] = 0
            return True

        except Exception as e:
            logger.error(f"Retry failed for task {task_id}: {e}")
            self._tasks[task_id]["status"] = "failed"
            return False

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        return list(self._tasks.values())

    def get_task_result(self, task_id: str) -> Optional[Any]:
        return self._task_results.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = "cancelled"
            logger.info(f"Task cancelled: {task_id}")
            return True
        return False

    def shutdown(self, wait: bool = True):
        self._executor.shutdown(wait=wait)
        logger.info("TaskExecutor shutdown")

    async def execute_batch(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        async def run_single(task_def: Dict[str, Any]) -> Dict[str, Any]:
            task_id = task_def.get("id", f"batch_{id(task_def)}")
            func = task_def["func"]
            args = task_def.get("args", [])
            kwargs = task_def.get("kwargs", {})
            result = await self.execute_task(task_id, func, *args, **kwargs)
            return {"task_id": task_id, "result": result}

        results = await asyncio.gather(*[run_single(t) for t in tasks], return_exceptions=True)
        return [
            r if not isinstance(r, Exception) else {"error": str(r)}
            for r in results
        ]
