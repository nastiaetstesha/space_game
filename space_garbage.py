import asyncio
import random
from animation import draw_frame, get_frame_size
from obstacles import Obstacle, obstacles, obstacles_in_last_collisions
from explosion import explode
from game_scenario import get_garbage_delay_tics
import state
from timing import sleep

SPAWN_INTERVAL = 10


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom.
    Сolumn position will stay same, as specified on start."""
    rows_num, cols_num = canvas.getmaxyx()

    frame_h, frame_w = get_frame_size(garbage_frame)

    column = max(1, min(column, cols_num - frame_w - 1))

    row = 0.0

    obstacle = Obstacle(
        int(row), int(column), frame_h, frame_w, uid=id(garbage_frame)
        )
    obstacles.append(obstacle)

    try:
        while row < rows_num:
            if obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(obstacle)
                center_r = obstacle.row + frame_h // 2
                center_c = obstacle.column + frame_w // 2
                await explode(canvas, center_r, center_c)
                break

            draw_frame(canvas, round(row), column, garbage_frame)
            await asyncio.sleep(0)
            draw_frame(
                canvas, round(row), column, garbage_frame, negative=True
                )

            row += speed

            obstacle.row = int(row)
            obstacle.column = int(column)

            if row >= rows_num:
                break
    finally:
        if obstacle in obstacles:
            obstacles.remove(obstacle)


async def fill_orbit_with_garbage(canvas, coroutines, frames):
    '''Continuously launch garbage-fall coroutines to populate orbit.'''

    max_r, max_c = canvas.getmaxyx()
    while True:
        delay = get_garbage_delay_tics(state.year)
        if delay is None:
            await sleep()
            continue

        frame = random.choice(frames)
        width = max(len(line) for line in frame.splitlines())
        col = random.randint(1, max_c - width - 1)

        state.coroutines.append(
            fly_garbage(canvas, col, frame, speed=random.uniform(0.3, 0.8))
        )

        await sleep(delay)
