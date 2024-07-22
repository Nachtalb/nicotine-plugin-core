"""This module provides a :class:`PeriodicJob` class for running a job
periodically in the background.

Such jobs can be used e.g. to check for updates of the plugin, to detect
changes in the plugin settings by a user, send heartbeats to a server or
many other tasks that need to be done periodically.

.. seealso:: :class:`PeriodicJob` for examples and usage.
"""

from threading import Event, Thread
from time import sleep, time
from typing import Any, Callable, Optional, Union

__all__ = ["PeriodicJob"]


class PeriodicJob(Thread):
    """Periodic job running as a daemon thread in the background

    Note:
        * The thread will always be started daemonized.
        * The thread will run the update function every delay seconds.
        * The thread will check if it is at least every min_delay seconds.
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

    Args:
        update (:obj:`Callable[..., Any]`): Function to run every delay seconds
        delay (:obj:`Union[int, Callable[..., int]]`, optional): Delay between updates in seconds
            as an integer or a function returning an integer
        name (:obj:`str`, optional): Name of the thread
        before_start (:obj:`Optional[Callable[..., Any]]`, optional): Function to run before the thread starts
        min_delay (:obj:`int`, optional): Minimum delay between checks in seconds

    Attributes:
        update (:obj:`Callable[..., Any]`): Function to run every delay seconds
        before_start (:obj:`Optional[Callable[..., Any]]`): Function to run before the thread starts
        delay (:obj:`Union[int, Callable[..., int]]`): Delay between updates in seconds
        last_run (:obj:`float`): Time of the last update
    """

    last_run: float = 0.0

    def __init__(
        self,
        update: Callable[..., Any],
        delay: Union[int, Callable[..., int]] = 1,
        name: str = "",
        before_start: Optional[Callable[..., Any]] = None,
        min_delay: int = 1,
    ) -> None:
        super().__init__(name=name, daemon=True)
        self.update = update
        self.before_start = before_start
        self.delay = delay
        self._min_delay = min_delay

        self._stopped = Event()
        self._can_run = Event()
        self._can_run.set()

    def pause(self) -> None:
        """Pause the thread execution

        Note:
            The thread will not be stopped, just paused.
        """
        self._can_run.clear()

    def resume(self) -> None:
        """Resume the thread execution

        Note:
            The thread will not be started, just resumed.
        """
        self._can_run.set()

    def time_to_work(self) -> bool:
        """Check if it is time to work

        Returns:
            :obj:`bool`: True if it is time to work, False otherwise
        """
        if not self._can_run.is_set():
            return False

        delay = self.delay() if callable(self.delay) else self.delay

        if not delay:
            return False

        if not self.last_run:
            return True

        return time() - self.last_run > delay

    def wait_for_time_to_work(self) -> bool:
        """Wait for the time to work

        Returns:
            :obj:`bool`: True if it is time to work, False if the thread should stop completely
        """
        while True:
            self._can_run.wait()
            if self._stopped.is_set():
                return False
            if self.time_to_work():
                return True
            sleep(self._min_delay)

    def run(self) -> None:
        """Run the thread

        Warning:
            Do not call this method directly, use :meth:`start` instead.
        """
        if self.before_start:
            self.before_start()
        while not self._stopped.is_set() and self.wait_for_time_to_work():
            self.update()
            self.last_run = time()

    def stop(self, wait: bool = True) -> None:
        """Stop the thread

        Args:
            wait (:obj:`bool`, optional): Wait for the thread to stop
        """
        self.pause()
        self._stopped.set()
        self.resume()

        if wait and self.is_alive():
            self.join()
