import time
import asyncio
import curses
import random
from itertools import cycle
import os

import animation 


def load_frames(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# считаем, что все файлы кадров лежат в папке `frames/`
FRAMES_DIR = os.path.join(os.path.dirname(__file__), 'frames')


spaceship_frames = [
    load_frames(os.path.join(FRAMES_DIR, 'rocket_frame_1.txt')),
    load_frames(os.path.join(FRAMES_DIR, 'rocket_frame_2.txt')),
]


async def blink(canvas, row, column, symbol='*'):

    frames = [
            (curses.A_DIM,    20),
            (curses.A_NORMAL,  3),
            (curses.A_BOLD,    5),
            (curses.A_NORMAL,  3),
        ]
    
    total_ticks = sum(repeats for _, repeats in frames)

    phase = random.randint(0, total_ticks - 1)
    for _ in range(phase):
        await asyncio.sleep(0)
    while True:
        for attr, repeats in frames:
            for _ in range(repeats):
                canvas.addstr(row, column, symbol, attr)
                canvas.refresh()
                await asyncio.sleep(0)


async def animate_spaceship(canvas, row, column, frames, pause=0.1):
    prev_frame = frames[-1]
    for frame in cycle(frames):
        # 1) стереть то, что было
        animation.draw_frame(canvas, row, column, prev_frame, negative=True)
        # 2) нарисовать то, что стало
        animation.draw_frame(canvas, row, column, frame, negative=False)
        canvas.refresh()
        await asyncio.sleep(pause)
        # 3) запомним, что это теперь «предыдущее»
        prev_frame = frame
    # for frame in cycle(frames):
    #     # 1) заливаем фон под кораблём (чтобы старое пламя исчезло),
    #     #    но только в области кадра, а не везде целиком:
    #     animation.draw_frame(canvas, row, column, frame, negative=True)
    #     # 2) рисуем новый кадр:
    #     animation.draw_frame(canvas, row, column, frame, negative=False)
    #     canvas.refresh()
    #     await asyncio.sleep(pause)


async def draw(canvas):
    TIC_TIMEOUT = 0.1
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas.border()

    max_row, max_col = canvas.getmaxyx()

    tasks = []
    for _ in range(100):
        row = random.randint(1, max_row - 2)
        column = random.randint(1, max_col - 2)
        symbol = random.choice('+*.:')
        tasks.append(asyncio.create_task(blink(canvas, row, column, symbol)))

    center_row, center_col = max_row // 2, max_col // 2
    ship_row = center_row - (len(spaceship_frames[0].splitlines()) // 2)
    ship_col = center_col - (max(map(len, spaceship_frames[0].splitlines())) // 2)

    tasks.append(asyncio.create_task(
        fire(canvas, center_row, center_col,
             rows_speed=-0.3, columns_speed=0)
    ))

    tasks.append(asyncio.create_task(
        animate_spaceship(canvas, ship_row, ship_col, spaceship_frames)
        ))

    try:
        while True:
            canvas.border()
            canvas.refresh()
            await asyncio.sleep(TIC_TIMEOUT)
    except (asyncio.CancelledError, KeyboardInterrupt):
        for t in tasks:
            t.cancel()
        raise


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def main():
    curses.update_lines_cols()
    curses.wrapper(lambda stdscr: asyncio.run(draw(stdscr)))


if __name__ == '__main__':
    print("Frames directory:", FRAMES_DIR)
    print("Files:", os.listdir(FRAMES_DIR))
    print("Frame #1 sample:\n", spaceship_frames[0][:30])
    input("Нажмите Enter, чтобы запустить игру...")
    curses.update_lines_cols()
    curses.wrapper(lambda stdscr: asyncio.run(draw(stdscr)))