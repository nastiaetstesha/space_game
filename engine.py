import curses
import random
import time
import os
from itertools import cycle
import asyncio

import animation
import space_garbage
from physics import update_speed
from obstacles import obstacles, show_obstacles, obstacles_in_last_collisions 
from gameover import show_gameover
from game_scenario import PHRASES, get_garbage_delay_tics
import state
from timing import sleep


TIC_TIMEOUT = state.TIC_TIMEOUT
TICS_PER_YEAR = max(1, int(1.5 / TIC_TIMEOUT))
FRAMES_DIR = os.path.join(os.path.dirname(__file__), 'frames')
GARBAGE_DIR = os.path.join(os.path.dirname(__file__), 'garbage')

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
                    await sleep()
    return _blink()


def animate_spaceship(canvas, pos, frames, pause=TIC_TIMEOUT):
    async def _anim():
        prev = frames[-1]
        prev_pos = dict(pos)
        iter_frames = cycle(frames)
        while True:
            if state.GAME_OVER:
                animation.draw_frame(canvas, prev_pos['row'], prev_pos['col'], prev, negative=True)
                return
            frame = next(iter_frames)
            curr_pos = {'row': pos['row'], 'col': pos['col']}
            animation.draw_frame(
                canvas, prev_pos['row'], prev_pos['col'], prev, negative=True
                )
            animation.draw_frame(
                canvas, curr_pos['row'], curr_pos['col'], frame, negative=False
                )
            # ticks = int(pause / TIC_TIMEOUT)
            await sleep(2)

            prev, prev_pos = frame, curr_pos
    return _anim()


async def control_spaceship(canvas, pos, ship_h, ship_w):

    row_speed = column_speed = 0.0
    while True:
        dr, dc, _ = animation.read_controls(canvas)
        row_speed, column_speed = update_speed(
            row_speed, column_speed,
            dr, dc,
            row_speed_limit=2, column_speed_limit=2
        )
        pos['row'] = min(
            max(1, pos['row'] + row_speed),
            canvas.getmaxyx()[0] - ship_h - 1
        )
        pos['col'] = min(
            max(1, pos['col'] + column_speed),
            canvas.getmaxyx()[1] - ship_w - 1
        )
        await sleep()


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
        row_i, col_i = round(r), round(c)

        hit = False
        for ob in obstacles:
            if ob.has_collision(row_i, col_i):
                obstacles_in_last_collisions.append(ob)
                return

        canvas.addstr(row_i, col_i, sym)
        await sleep()
        canvas.addstr(row_i, col_i, ' ')
        r += rows_speed
        c += cols_speed


async def run_spaceship_and_fire(canvas, coroutines, pos, ship_h, ship_w):
    """
     1) обновлять скорость и координаты корабля
     2) при нажатии пробела спаунить fire()
    """

    row_speed = col_speed = 0.0

    while True:
        dr, dc, is_space = animation.read_controls(canvas)

        row_speed, col_speed = update_speed(
            row_speed, col_speed,
            rows_direction=dr, columns_direction=dc
        )

        max_r, max_c = canvas.getmaxyx()
        new_r = min(max(1, pos['row'] + row_speed), max_r - ship_h - 1)
        new_c = min(max(1, pos['col'] + col_speed), max_c - ship_w - 1)
        pos['row'], pos['col'] = new_r, new_c

        if is_space and state.year >= 2020 and not state.GAME_OVER:
            state.coroutines.append(
                fire(canvas, pos['row'], pos['col'] + ship_w // 2)
            )
        ship_row = int(pos['row'])
        ship_col = int(pos['col'])
        crashed = any(ob.has_collision(ship_row, ship_col, ship_h, ship_w) for ob in obstacles)
        if crashed:
            state.GAME_OVER = True
            state.coroutines.append(show_gameover(canvas))
            return  # корабль исчезает: выходим из корутины - не исчез

        await asyncio.sleep(0)


async def run_time():
    while True:
        await sleep(state.TICS_PER_YEAR)
        state.year += 1
        if state.year in PHRASES:
            state.current_phrase = PHRASES[state.year]
            state.phrase_tics_left = state.TICS_PER_YEAR


async def draw_hud(hud):
    while True:
        hud.erase()
        rows, cols = hud.getmaxyx()
        hud.border()
        hud.addstr(1, 2, f"Year: {state.year}")
        if state.phrase_tics_left > 0 and state.current_phrase:
            msg = state.current_phrase[:max(0, cols-4)]
            hud.addstr(rows-2, max(2, (cols-len(msg))//2), msg)
            state.phrase_tics_left -= 1
        hud.refresh()
        await sleep()


def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas.border()

    max_r, max_c = canvas.getmaxyx()
    ship_h, ship_w = animation.get_frame_size(spaceship_frames[0])

    hud_height = 3
    hud = canvas.derwin(hud_height, max_c-2, max_r - hud_height - 1, 1)

    state.coroutines.append(run_time())
    state.coroutines.append(draw_hud(hud))

    for _ in range(100):
        r = random.randint(1, max_r - 2)
        c = random.randint(1, max_c - 2)
        sym = random.choice('+*.:')
        phase = random.randrange(TOTAL_TICKS)
        state.coroutines.append(blink(canvas, r, c, sym, offset=phase))

    state.coroutines.append(
        space_garbage.fill_orbit_with_garbage(
            canvas, state.coroutines, garbage_frames
            )
    )

    mid_r, mid_c = max_r // 2, max_c // 2
    pos = {'row': mid_r, 'col': mid_c}
    ship_h, ship_w = animation.get_frame_size(spaceship_frames[0])
    state.coroutines.append(
        run_spaceship_and_fire(canvas, state.coroutines, pos, ship_h, ship_w)
    )
    state.coroutines.append(
        animate_spaceship(canvas, pos, spaceship_frames)
    )
    if state.DEBUG_BOXES:
        state.coroutines.append(show_obstacles(canvas, obstacles))

    try:
        while state.coroutines:
            for coro in state.coroutines.copy():
                try:
                    coro.send(None)
                except StopIteration:
                    state.coroutines.remove(coro)
            canvas.border()
            canvas.refresh()
            time.sleep(TIC_TIMEOUT)
    except KeyboardInterrupt:
        pass

