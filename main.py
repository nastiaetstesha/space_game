import asyncio
import curses
import random
from itertools import cycle
import os

import animation 

TIC_TIMEOUT = 0.1

FRAMES_DIR = os.path.join(os.path.dirname(__file__), 'frames')

BLINK_FRAMES = [
    (curses.A_DIM,    20),
    (curses.A_NORMAL,  3),
    (curses.A_BOLD,    5),
    (curses.A_NORMAL,  3),
]
TOTAL_TICKS = sum(cnt for _, cnt in BLINK_FRAMES)


def load_frames(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


spaceship_frames = [
    load_frames(os.path.join(FRAMES_DIR, 'rocket_frame_1.txt')),
    load_frames(os.path.join(FRAMES_DIR, 'rocket_frame_2.txt')),
]


async def blink(canvas, row, column, symbol='*', offset_ticks=0, *, frames):

    for _ in range(offset_ticks):
        await asyncio.sleep(0)

    while True:
        for attr, repeats in frames:
            for _ in range(repeats):
                canvas.addstr(row, column, symbol, attr)
                await asyncio.sleep(0)


async def animate_spaceship(canvas, pos, frames, pause=TIC_TIMEOUT):
    prev_frame = frames[-1]
    prev_pos = dict(pos)
    frame_iter = cycle(frames)

    while True:
        frame = next(frame_iter)
        curr_pos = {'row': pos['row'], 'col': pos['col']}

        animation.draw_frame(canvas,
                             prev_pos['row'], prev_pos['col'],
                             prev_frame,
                             negative=True)

        animation.draw_frame(canvas,
                             curr_pos['row'], curr_pos['col'],
                             frame,
                             negative=False)

        await asyncio.sleep(pause)

        prev_frame = frame
        prev_pos = curr_pos


async def control_spaceship(canvas, pos, ship_rows, ship_cols):
    """
    Каждые TIC_TIMEOUT читаем стрелки и правим pos['row'], pos['col'].
    """
    max_row, max_col = canvas.getmaxyx()
    min_row = 1
    max_pos_row = max_row - ship_rows - 1
    min_col = 1
    max_pos_col = max_col - ship_cols - 1

    while True:
        d_row, d_col, _ = animation.read_controls(canvas)
        new_row = pos['row'] + d_row
        new_col = pos['col'] + d_col

        pos['row'] = min(max(min_row, new_row), max_pos_row)
        pos['col'] = min(max(min_col, new_col), max_pos_col)
        await asyncio.sleep(TIC_TIMEOUT)


async def draw(canvas):
    TIC_TIMEOUT = 0.1
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas.border()

    max_row, max_col = canvas.getmaxyx()
    ship_rows, ship_cols = animation.get_frame_size(spaceship_frames[0])

    tasks = []

    for _ in range(100):
        row = random.randint(1, max_row - 2)
        column = random.randint(1, max_col - 2)
        symbol = random.choice('+*.:')
        phase = random.randrange(TOTAL_TICKS)
        tasks.append(asyncio.create_task(
            blink(
                canvas,
                row,
                column,
                symbol,
                offset_ticks=phase,
                frames=BLINK_FRAMES
                )
        ))

    center_row, center_col = max_row // 2, max_col // 2

    tasks.append(asyncio.create_task(
        fire(canvas, center_row, center_col,
             rows_speed=-0.3, columns_speed=0)
    ))

    pos = {
        'row': max_row // 2,
        'col': max_col // 2,
    }

    tasks.append(asyncio.create_task(
        control_spaceship(canvas, pos, ship_rows, ship_cols)
    ))

    tasks.append(asyncio.create_task(
        animate_spaceship(canvas, pos, spaceship_frames)
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