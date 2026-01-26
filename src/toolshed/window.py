import pygame as pg 
from dataclasses import dataclass 
from typing import Tuple

from . import get_logger

logger = get_logger()

def get_window_scale(base_size, scaled_size):
        return min(scaled_size[0] // base_size[0], scaled_size[1] // base_size[1])

@dataclass
class EventContext:
    mouse_pos: Tuple[float, float] = (0,0)

class PygameContext: 
    def __init__(self, base_dims, title='Toolshed Window', icon_path=None, fps=60, screen_info_pkg=True): 
        pg.init()

        # record the base dimensions as separate vars 
        self.base_dims = base_dims

        # get monitor info and record the scale and screen dimensions
        if screen_info_pkg: 
            from screeninfo import get_monitors

            monitors = get_monitors()
            target_monitor_idx = 1 if len(monitors) > 1 else 0
            target_monitor_dims = (monitors[target_monitor_idx].width, monitors[target_monitor_idx].height)
            logger.info(f'Using monitor dimensions: {target_monitor_dims}')

            horiz = target_monitor_dims[0] - base_dims[0]
            vert  = target_monitor_dims[1] - base_dims[1]
            max_scale_dims = [target_monitor_dims[0], target_monitor_dims[1]]
            idx = 0 if horiz < vert else 1
            max_scale_dims[idx] *= 0.7
            self.scale = get_window_scale(base_dims, tuple(max_scale_dims))

        else: 
            info = pg.display.Info()
            self.scale = get_window_scale(base_dims, (info.current_w * .7, info.current_h))

        self.scaled_dims = (base_dims[0] * self.scale, base_dims[1] * self.scale)
        self.screen_dims = self.scaled_dims

        # instantiate screen object 
        self.screen = pg.display.set_mode(self.scaled_dims, pg.RESIZABLE)
        pg.display.set_caption(title)
        self.frame = pg.Surface(base_dims)
        self.clock = pg.Clock() 
        self.fps = fps

        if icon_path is not None: 
            try: 
                pg.display.set_icon(pg.image.load(icon_path).convert_alpha())
            except: 
                print(f'[ INFO ] Failed to load and set icon image at path: {icon_path}')
    
    def quit(self): 
        pg.quit()

    def finish_drawing_frame(self): 
        scaled_frame = pg.transform.scale(self.frame, self.scaled_dims)
        fw, fh = self.scaled_dims
        sw, sh = self.screen_dims

        self.screen.fill((0,0,0))
        self.screen.blit(scaled_frame, ((sw-fw)/2, (sh-fh)/2))
        pg.display.update()
        self.clock.tick(self.fps)

    def get_scaled_mouse_pos(self): 
        mx, my = pg.mouse.get_pos()
        sw, sh = self.screen_dims
        fw, fh = self.scaled_dims
        bufx, bufy = (sw - fw) / 2, (sh - fh) /2

        try: 
            mx = (mx - bufx) / self.scale
            my = (my - bufy) / self.scale
        except: 
            pass 

        return (mx, my)
    
    def update_screen_dims(self, w, h): 
        self.scale = get_window_scale(self.base_dims, (w, h))
        self.scaled_dims = (self.base_dims[0] * self.scale, self.base_dims[1] * self.scale)
        self.screen_dims = (w, h)
    
    def get_event_context(self) -> EventContext: 
        return EventContext(self.get_scaled_mouse_pos())
