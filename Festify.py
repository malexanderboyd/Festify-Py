import asyncio
import enum
import logging
import sys

import aiohttp

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
_LOGGER.addHandler(handler)


def is_callback(func) -> bool:
    """Check if function is safe to be called in the event loop."""
    return getattr(func, '_hass_callback', False) is True


class CoreState(enum.Enum):
    """Represent the current state of Home Assistant."""

    not_running = 'NOT_RUNNING'
    starting = 'STARTING'
    running = 'RUNNING'
    stopping = 'STOPPING'

    def __str__(self) -> str:
        """Return the event."""
        return self.value  # type: ignore


class Festify:

    def __init__(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.state = CoreState.not_running
        self._pending_tasks = []
        self._stopped = None
        self.exit_code = 0

    async def async_run(self) -> int:
        """Festify main entry point"""

        if self.state == CoreState.running:
            raise RuntimeError("Festify is already running")

        self._stopped = asyncio.Event()

        await self.async_start()

        await self._stopped.wait()
        return self.exit_code

    async def async_start(self) -> None:
        _LOGGER.info('Starting Festify')
        self.state = CoreState.running
        try:
            await self.async_block_till_done()
        except:
            _LOGGER.exception('Exception while starting Festify')

        await asyncio.sleep(0)

        self.state = CoreState.running

    async def async_block_till_done(self) -> None:

        await asyncio.sleep(0)

        while self._pending_tasks:
            pending = [task for task in self._pending_tasks if not task.done()]
            self._pending_tasks.clear()
            if pending:
                await asyncio.wait(pending)
            else:
                await asyncio.sleep(0)

    def add_job(self, target, *args) -> None:
        if target is None:
            raise ValueError('Cannot add job when target is None')
        self.loop.call_soon_threadsafe(self.async_add_job, target, *args)

    def async_add_job(self, target, *args):

        task = None

        if asyncio.iscoroutine(target):
            task = self.loop.create_task(target)
        elif is_callback(target):
            return self.loop.call_soon(target)
        elif asyncio.iscoroutinefunction(target):
            task = self.loop.create_task(target(*args))

        if task is not None:
            self._pending_tasks.append(task)

        return task


async def print_preview(url):
    # conn to server
    async with aiohttp.ClientSession() as session:
        # create requests
        async with session.get(url) as response:
            response = await response.text()

            lines = list(filter(lambda line: len(line) > 0, response.split('\n')))
            print('-' * 80)
            for line in lines[:3]:
                print(line)
            print()


def asyncio_run(main, *, debug: bool = False):
    """Minimal re-implementation of asyncio.run (since 3.7)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_debug(debug)
    try:
        return loop.run_until_complete(main)
    finally:
        asyncio.set_event_loop(None)  # type: ignore # not a bug
        loop.close()


def main():
    pages = [
        'http://textfiles.com/adventure/amforever.txt',
        'http://textfiles.com/adventure/ballyhoo.txt',
        'http://textfiles.com/adventure/bardstale.txt',
    ]

    festify = Festify()

    asyncio_run(festify.async_run(), debug=True)

    for page in pages:
        festify.async_add_job(print_preview, page)


main()
