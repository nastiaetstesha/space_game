import curses
from engine import draw


def main():
    curses.update_lines_cols()
    curses.wrapper(draw)


if __name__ == '__main__':
    main()
