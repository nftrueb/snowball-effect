
from .logger import Logger 
from .font import FontSpriteWriter, Dialogue

logger = Logger()
def get_logger(): 
    return logger

debug = {}
def print_debug(surf: pg.Surface, fsr: FontSpriteWriter, color=(0,0,0)): 
    i = 0 
    for k, v in debug.items(): 
        s = str(k)
        if v is not None: 
            s += f': {v}'
        w, h = fsr.sprite_w, fsr.sprite_h
        fsr.render(surf, Dialogue(s, pg.Rect(1, (h+1)*i, len(s)*w, h)), color)
        i += 1