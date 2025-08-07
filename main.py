import curses
import random
import time
import os
from itertools import cycle
import asyncio

import animation
import space_garbage

TIC_TIMEOUT = 0.1
FRAMES_DIR = os.path.join(os.path.dirname(__file__), 'frames')
GARBAGE_DIR = os.path.join(os.path.dirname(__file__), 'garbage')
coroutines = []


BLINK_FRAMES = [
    (curses.A_DIM,    20),
    (curses.A_NORMAL,  3),
    (curses.A_BOLD,    5),
    (curses.A_NORMAL,  3),
]
TOTAL_TICKS = sum(cnt for _, cnt in BLINK_FRAMES)


def load_frame(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


spaceship_frames = [
    load_frame(os.path.join(FRAMES_DIR, 'rocket_frame_1.txt')),
    load_frame(os.path.join(FRAMES_DIR, 'rocket_frame_2.txt')),
]


garbage_frames = []

for fname in os.listdir(GARBAGE_DIR):
    if fname.endswith('.txt'):
        garbage_frames.append(load_frame(os.path.join(GARBAGE_DIR, fname)))


def blink(canvas, row, col, symbol='*', offset=0, frames=BLINK_FRAMES):
    async def _blink():

        for _ in range(offset):
            await asyncio.sleep(0)
        while True:
            for attr, count in frames:
                for _ in range(count):
                    canvas.addstr(row, col, symbol, attr)
                    await asyncio.sleep(0)
    return _blink()


def animate_spaceship(canvas, pos, frames, pause=TIC_TIMEOUT):
    async def _anim():
        prev = frames[-1]
        prev_pos = dict(pos)
        iter_frames = cycle(frames)
        while True:
            frame = next(iter_frames)
            curr_pos = {'row': pos['row'], 'col': pos['col']}
            animation.draw_frame(
                canvas, prev_pos['row'], prev_pos['col'], prev, negative=True
                )
            animation.draw_frame(
                canvas, curr_pos['row'], curr_pos['col'], frame, negative=False
                )
            ticks = int(pause / TIC_TIMEOUT)
            for _ in range(ticks):
                await asyncio.sleep(0)

            prev, prev_pos = frame, curr_pos
    return _anim()


def control_spaceship(canvas, pos, ship_h, ship_w):
    async def _control():
        max_r, max_c = canvas.getmaxyx()
        min_r, min_c = 1, 1
        max_rpos = max_r - ship_h - 1
        max_cpos = max_c - ship_w - 1
        while True:
            dr, dc, _ = animation.read_controls(canvas)
            nr = pos['row'] + dr
            nc = pos['col'] + dc
            pos['row'] = min(max(min_r, nr), max_rpos)
            pos['col'] = min(max(min_c, nc), max_cpos)
            await asyncio.sleep(0)
    return _control()


async def fire(canvas, start_r, start_c, rows_speed=-0.3, cols_speed=0):
    r, c = start_r, start_c
    canvas.addstr(round(r), round(c), '*')
    await asyncio.sleep(0)
    canvas.addstr(round(r), round(c), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(r), round(c), ' ')
    r += rows_speed
    c += cols_speed
    sym = '-' if cols_speed else '|'
    max_r, max_c = canvas.getmaxyx()
    curses.beep()
    while 0 < r < max_r and 0 < c < max_c:
        canvas.addstr(round(r), round(c), sym)
        await asyncio.sleep(0)
        canvas.addstr(round(r), round(c), ' ')
        r += rows_speed
        c += cols_speed


def draw(canvas):
    global coroutines
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas.border()

    max_r, max_c = canvas.getmaxyx()
    ship_h, ship_w = animation.get_frame_size(spaceship_frames[0])

    for _ in range(100):
        r = random.randint(1, max_r - 2)
        c = random.randint(1, max_c - 2)
        sym = random.choice('+*.:')
        phase = random.randrange(TOTAL_TICKS)
        coroutines.append(blink(canvas, r, c, sym, offset=phase))

    coroutines.append(
        space_garbage.fill_orbit_with_garbage(canvas, coroutines, garbage_frames)
    )
                     
    mid_r, mid_c = max_r // 2, max_c // 2
    coroutines.append(fire(canvas, mid_r, mid_c, rows_speed=-0.3, cols_speed=0))

    pos = {'row': mid_r, 'col': mid_c}
    coroutines.append(control_spaceship(canvas, pos, ship_h, ship_w))
    coroutines.append(animate_spaceship(canvas, pos, spaceship_frames))

    try:
        while coroutines:
            for coro in coroutines.copy():
                try:
                    coro.send(None)
                except StopIteration:
                    coroutines.remove(coro)
            canvas.border()
            canvas.refresh()
            time.sleep(TIC_TIMEOUT)
    except KeyboardInterrupt:
        pass


def main():
    curses.update_lines_cols()
    curses.wrapper(draw)


if __name__ == '__main__':
    main()
