import asyncio
import random
from animation import draw_frame, get_frame_size
from main import sleep
from obstacles import Obstacle, obstacles, obstacles_in_last_collisions


SPAWN_INTERVAL = 10


# async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
#     """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
#     rows_number, columns_number = canvas.getmaxyx()

#     column = max(column, 0)
#     column = min(column, columns_number - 1)

#     row = 0

#     while row < rows_number:
#         draw_frame(canvas, row, column, garbage_frame)
#         await asyncio.sleep(0)
#         draw_frame(canvas, row, column, garbage_frame, negative=True)
#         row += speed
async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_num, cols_num = canvas.getmaxyx()

    frame_h, frame_w = get_frame_size(garbage_frame)

    column = max(1, min(column, cols_num - frame_w - 1))

    row = 0.0

    obstacle = Obstacle(int(row), int(column), frame_h, frame_w, uid=id(garbage_frame))
    obstacles.append(obstacle)

    try:
        while row < rows_num:
            if obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(obstacle)
                break
            
            draw_frame(canvas, round(row), column, garbage_frame)
            await asyncio.sleep(0)
            draw_frame(canvas, round(row), column, garbage_frame, negative=True)

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
        frame = random.choice(frames)
        width = max(len(line) for line in frame.splitlines())
        col = random.randint(1, max_c - width - 1)

        coroutines.append(
            fly_garbage(canvas, col, frame, speed=random.uniform(0.3, 0.8))
        )

        await sleep(SPAWN_INTERVAL)