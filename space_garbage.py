import asyncio
import random
from animation import draw_frame

SPAWN_INTERVAL = 10 


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed


async def fill_orbit_with_garbage(canvas, coroutines, frames):
    '''Continuously launch garbage-fall coroutines to populate orbit.'''

    max_r, max_c = canvas.getmaxyx()
    while True:
        frame = random.choice(frames)
        width = max(len(line) for line in frame.splitlines())
        col = random.randint(1, max_c - width - 1)

        coroutines.append(
            fly_garbage(canvas, col, frame, speed=random.uniform(0.3, 0.8))
        )

        for _ in range(SPAWN_INTERVAL):
            await asyncio.sleep(0)