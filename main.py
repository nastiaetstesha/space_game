import curses
import random
import time
import os
from itertools import cycle
import asyncio

import animation


class DummySleep:
    def __init__(self, delay):
        self.delay = delay

    def __await__(self):

        yield None
        return


asyncio.sleep = lambda delay: DummySleep(delay)


tic_timeout = 0.1
FRAMES_DIR = os.path.join(os.path.dirname(__file__), 'frames')


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


def blink(canvas, row, col, symbol='*', offset=0, frames=BLINK_FRAMES):
    async def _blink():
        # initial offset
        for _ in range(offset):
            await asyncio.sleep(0)
        while True:
            for attr, count in frames:
                for _ in range(count):
                    canvas.addstr(row, col, symbol, attr)
                    await asyncio.sleep(0)
    return _blink()


def animate_spaceship(canvas, pos, frames, pause=tic_timeout):
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
            await asyncio.sleep(pause)
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
            await asyncio.sleep(tic_timeout)
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


def run_event_loop(canvas, coros):
    try:
        while coros:
            for coro in coros.copy():
                try:
                    coro.send(None)
                except StopIteration:
                    coros.remove(coro)
            canvas.border()
            canvas.refresh()
            time.sleep(tic_timeout)
    except KeyboardInterrupt:
        return


def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas.border()
    max_r, max_c = canvas.getmaxyx()
    ship_h, ship_w = animation.get_frame_size(spaceship_frames[0])

    coros = []

    for _ in range(100):
        r = random.randint(1, max_r-2)
        c = random.randint(1, max_c-2)
        sym = random.choice('+*.:')
        phase = random.randrange(TOTAL_TICKS)
        coros.append(blink(canvas, r, c, sym, offset=phase))

    mid_r, mid_c = max_r//2, max_c//2
    coros.append(fire(canvas, mid_r, mid_c, rows_speed=-0.3, cols_speed=0))

    pos = {'row': mid_r, 'col': mid_c}
    coros.append(control_spaceship(canvas, pos, ship_h, ship_w))
    coros.append(animate_spaceship(canvas, pos, spaceship_frames))

    run_event_loop(canvas, coros)


def main():
    curses.update_lines_cols()
    curses.wrapper(draw)


if __name__ == '__main__':
    main()
