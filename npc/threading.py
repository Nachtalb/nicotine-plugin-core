"""This module provides a :class:`PeriodicJob` class for running a job
periodically in the background.

Such jobs can be used e.g. to check for updates of the plugin, to detect
changes in the plugin settings by a user, send heartbeats to a server or
many other tasks that need to be done periodically.

.. seealso:: :class:`PeriodicJob` for examples and usage.
"""

import logging
from threading import Event, Thread
from time import time
from typing import Any, Callable, Optional, Union
from uuid import uuid4

from .logging import NLogHandler


class PeriodicJob(Thread):
    """Periodic job running as a daemon thread in the background

    Note:
        * The thread will always be started daemonized.
        * The thread will run the update function every delay seconds.
        * The thread can be paused and resumed.
        * The thread can be stopped.

    Example:

        .. code-block:: python

            def update():
                now = datetime.now().strftime("%H:%M:%S")
                print(f"Hello World! {now}")

            job = PeriodicJob(update, delay=2)
            job.start()
            # Hello World! 00:00:00
            # Hello World! 00:00:02
            # Hello World! 00:00:04
            job.pause()
            sleep(5)
            job.resume()
            # Hello World! 00:00:09
            # Hello World! 00:00:11
            job.stop()

    .. versionremoved:: 0.5.0 :attr:`npc.PeriodicJob.min_delay` removed to make the waiting for next run non GIL blocking

    .. versionadded:: 0.5.0
        :attr:`npc.PeriodicJob.all_jobs` - list of all running jobs,
        :attr:`npc.PeriodicJob.log` - Logging for jobs,
        :attr:`npc.PeriodicJob.id` - Unique ID of the job,
        :meth:`npc.PeriodicJob.set_log_level` - To change the log level for a job

    .. versionchanged:: 0.5.0
        :attr:`_stopped` -> :attr:`_stop_event`,
        :attr:`_can_run` -> :attr:`_pause_event`,
        :attr:`npc.PeriodicJob.last_run` - Is now a instance variable rather than class variable
                           which could have caused unexpected behaviour

    Args:
        update (:obj:`Callable`): Function to run every delay seconds
        delay (:obj:`int` | :obj:`Callable`, optional): Delay between updates in seconds
            as an integer or a function returning an integer
        name (:obj:`str`, optional): Name of the thread
        before_start (:obj:`Callable`, optional): Function to run before the thread starts

    Attributes:
        id (:obj:`str`): Unique ID of the job
        log (:obj:`logging.Logger`): Logger for the job
        update (:obj:`Callable`): Function to run every delay seconds
        before_start (:obj:`Callable`, optional): Function to run before the thread starts
        delay (:obj:`int` | :obj:`Callable`): Delay between updates in seconds
        last_run (:obj:`float`): Time of the last update
        all_jobs (:obj:`list`): List of all running jobs
    """

    all_jobs: list["PeriodicJob"] = []

    def __init__(
        self,
        update: Callable[..., Any],
        delay: Union[int, Callable[..., int]] = 1,
        name: str = "PeriodicJob",
        before_start: Optional[Callable[..., Any]] = None,
    ) -> None:
        super().__init__(name=name, daemon=True)
        self.id = str(uuid4())[:8]
        self.all_jobs.append(self)

        handler = NLogHandler()
        format = logging.Formatter(
            "%(name)s - %(levelname)s - %(message)s"
        )  # %(asctime)s not needed as it's already added by n+
        handler.setFormatter(format)
        self.log = logging.Logger(f"{name} ({self.id})")
        self.log.addHandler(handler)

        self.log.info("Created")
        self.update = update
        self.before_start = before_start
        self.delay = delay
        self.last_run: float = 0.0

        # Events
        self._stop_event = Event()
        self._pause_event = Event()
        self._pause_event.set()  # Set means "Running", Clear means "Paused"

    def set_log_level(self, level: Union[str, int]) -> None:
        """Set the log level for the job

        Args:
            level (:obj:`str` | :obj:`int`): Log level as a string or integer
        """
        self.log.setLevel(level)
        # This should be done in the logging module, but for some reason it doesn't work
        # so we have to clear the cache manually
        self.log._cache.clear()  # type: ignore[attr-defined]

    def pause(self) -> None:
        """Pause the thread execution."""
        self._pause_event.clear()
        self.log.info("Paused")

    def resume(self) -> None:
        """Resume the thread execution."""
        self._pause_event.set()
        self.log.info("Resumed")

    def stop(self, wait: bool = True) -> None:
        """Stop the thread gracefully.

        Args:
            wait (:obj:`bool`, optional): Wait for the thread to stop
        """
        self._stop_event.set()
        # Ensure we aren't stuck in a pause wait
        self._pause_event.set()

        if wait and self.is_alive():
            self.join()
        self.log.info("Stopped")

    def _get_current_delay(self) -> int:
        if callable(self.delay):
            return self.delay()
        return self.delay  # ty:ignore[invalid-return-type]

    def run(self) -> None:
        """Main loop for the thread.

        Warning:
            Do not call this method directly, use :meth:`threading.Thread.start` instead.
        """
        self.log.info("Started")

        if self.before_start:
            try:
                self.before_start()
            except Exception as e:
                self.log.exception(f"Error in before_start: {e}")

        while not self._stop_event.is_set():
            # 1. Check if paused
            self._pause_event.wait()
            if self._stop_event.is_set():
                break

            # 2. Calculate wait time
            delay = self._get_current_delay()
            now = time()
            time_since_last = now - self.last_run
            wait_time = max(0, delay - time_since_last)

            # 3. Wait efficiently (sleeps until time is up OR stop is called)
            if self._stop_event.wait(timeout=wait_time):
                break

            # 4. Run the Job safely
            try:
                self.log.debug("Running")
                self.update()
            except Exception as e:
                self.log.exception(f"Exception during update: {e}")

            self.last_run = time()
