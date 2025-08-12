import asyncio
from animation import draw_frame, get_frame_size


GAMEOVER_FRAME = r"""
                                                                                                   
                                                            ,----..                                
  ,----..                         ____                     /   /   \                               
 /   /   \                      ,'  , `.                  /   .     :                              
|   :     :                  ,-+-,.' _ |                 .   /   ;.  \                     __  ,-. 
.   |  ;. /               ,-+-. ;   , ||                .   ;   /  ` ;     .---.         ,' ,'/ /| 
.   ; /--`    ,--.--.    ,--.'|'   |  || ,---.          ;   |  ; \ ; |   /.  ./|  ,---.  '  | |' | 
;   | ;  __  /       \  |   |  ,', |  |,/     \         |   :  | ; | ' .-' . ' | /     \ |  |   ,' 
|   : |.' .'.--.  .-. | |   | /  | |--'/    /  |        .   |  ' ' ' :/___/ \: |/    /  |'  :  /   
.   | '_.' : \__\/: . . |   : |  | ,  .    ' / |        '   ;  \; /  |.   \  ' .    ' / ||  | '    
'   ; : \  | ," .--.; | |   : |  |/   '   ;   /|         \   \  ',  /  \   \   '   ;   /|;  : |    
'   | '/  .'/  /  ,.  | |   | |`-'    '   |  / |          ;   :    /    \   \  '   |  / ||  , ;    
|   :    / ;  :   .'   \|   ;/        |   :    |           \   \ .'      \   \ |   :    | ---'     
 \   \ .'  |  ,     .-./'---'          \   \  /             `---`         '---" \   \  /           
  `---`     `--`---'                    `----'                                   `----'            
"""


async def show_gameover(canvas, text_frame=GAMEOVER_FRAME):
    """Нарисовать 'Game Over' по центру"""
    max_r, max_c = canvas.getmaxyx()
    h, w = get_frame_size(text_frame)
    row = max_r // 2 - h // 2
    col = max_c // 2 - w // 2

    while True:
        draw_frame(canvas, row, col, text_frame)
        await asyncio.sleep(0)
