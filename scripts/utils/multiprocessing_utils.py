import concurrent.futures
import multiprocessing
from typing import Callable, List

from climatemaps.logger import logger


def run_tasks_in_parallel(
    tasks: List[tuple], worker_function: Callable, num_processes: int
) -> None:
    total = len(tasks)
    executor = None

    try:
        executor = concurrent.futures.ProcessPoolExecutor(max_workers=num_processes)
        futures = {executor.submit(worker_function, *task): task for task in tasks}

        for counter, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            progress = int((counter / total) * 100)
            logger.info(f"Completed: {result} | Progress: {progress}%")

    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt received! Shutting down executor...")
        for future in futures:
            future.cancel()
        if executor:
            executor.shutdown(wait=False, cancel_futures=True)
        _terminate_child_processes()
        raise

    finally:
        if executor:
            executor.shutdown(wait=True)


def _terminate_child_processes() -> None:
    children = multiprocessing.active_children()
    if not children:
        logger.info("No child processes to terminate.")
        return

    logger.info(f"Terminating {len(children)} child processes...")
    for proc in children:
        logger.info(f"Terminating child process PID={proc.pid}")
        proc.terminate()

    for proc in children:
        try:
            proc.join(timeout=3)
        except Exception:
            pass

    remaining = [p for p in children if p.is_alive()]
    if remaining:
        logger.warning(f"Force killing {len(remaining)} remaining processes...")
        for proc in remaining:
            logger.warning(f"Force killing process PID={proc.pid}")
            proc.kill()
            try:
                proc.join(timeout=2)
            except Exception:
                pass

    logger.info("All child processes terminated.")
