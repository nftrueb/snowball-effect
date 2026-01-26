from . import get_logger

logger = get_logger()

def ease_in_quint(x): 
    return x**5

def ease_out_quint(x): 
    return 1 - (1 - x)**5

def ease_in_out_cubic(x):
    return 4 * x**3 if x < 0.5 else 1 - (-2 * x + 2)**3 / 2

class Mover: 
    def __init__(self, draw_fn, easing_fn, animation_frames=60, active=True): 
        self.draw_fn = draw_fn
        self.easing_fn = easing_fn
        
        self.animating = False
        self.animation_frames = animation_frames
        self.frames = 0 

        self.active = active

    def update(self): 
        if not self.animating or not self.active: 
            return 
        
        self.frames += 1
        if self.frames >= self.animation_frames: 
            self.stop_animating()

    def get_easing_value(self): 
        return self.easing_fn(self.frames / self.animation_frames) if self.animating else None

    def start_animating(self): 
        if self.animating: 
            raise Exception('Already animating mover... failed to start animating')
        
        if not self.active:
            raise Exception('Animation cannot start in Mover because it\'s not active')
        
        self.animating = True
        self.frames = 0 

    def stop_animating(self): 
        self.animating = False
        self.frames = 0  

    def draw(self, surf): 
        if not self.active: 
            return 
        self.draw_fn(self, surf)

class PosMover(Mover): 
    def __init__(self, pos, draw_fn, easing_fn, animation_frames=60, retain_path=True, loop=False): 
        super().__init__(draw_fn, easing_fn, animation_frames)
        self.pos = pos  
        self.animating_start_pos = None
        self.retain_path = retain_path
        self.loop = loop 
        self.path = []
        self.target_idx = None 

    def update(self): 
        if not self.active or not self.animating: 
            return 
        
        target = self.get_current_target()
        y = self.get_easing_value()
        self.pos = (
            (target[0] - self.animating_start_pos[0]) * y + self.animating_start_pos[0], 
            (target[1] - self.animating_start_pos[1]) * y + self.animating_start_pos[1]
        ) 
        super().update()

    def get_current_target(self): 
        return (
            self.path[self.target_idx] 
            if self.target_idx is not None and self.target_idx < len(self.path)
            else None
        )

    def start_animating(self):
        try: 
            super().start_animating()
        except: 
            logger.error('Failed to start animation of Mover')

        if self.target_idx is None: 
            self.target_idx = 0 
        self.animating_start_pos = self.pos  

    def stop_animating(self):
        super().stop_animating()

        # check if target is at the end of its path... continue animating if not
        self.target_idx += 1
        if self.loop: 
            self.target_idx %= len(self.path)

        if self.target_idx < len(self.path): 
            self.start_animating()

        else:  
            self.target_idx = None
            self.animating_start_pos = None 
            if not self.retain_path: 
                self.path.clear()        

    def add_to_path(self, target): 
        self.path.append(target) 
    
class Animation: 
    current_sprite_idx: int | None
    frame_counter: int | None

    def __init__(self, sprites=None): 
        # holds tuples of (sprite surface, frame limit for this sprite)
        self.sprites = []
        if sprites is not None: 
            self.sprites = sprites 

        self.current_sprite_idx = None
        self.frame_counter = None

    def play(self): 
        self.current_sprite_idx = 0 
        self.frame_counter = 0  

    def cancel(self): 
        self.current_sprite_idx = None 
        self.frame_counter = None   

    def toggle(self): 
        if self.current_sprite_idx is None: 
            self.play() 
        else: 
            self.cancel()

    def update(self): 
        if self.current_sprite_idx is None or self.frame_counter is None: 
            return 

        # increment frame counter and check if sprite idx needs to be incremented
        _, frame_limit = self.sprites[self.current_sprite_idx]
        self.frame_counter += 1 
        if self.frame_counter >= frame_limit: 
            self.current_sprite_idx += 1
            self.frame_counter = 0

        # reset vars and return if animation has finished
        if self.current_sprite_idx >= len(self.sprites): 
            self.frame_counter = None 
            self.current_sprite_idx = None  

    def get_current_sprite(self): 
        if self.current_sprite_idx is None: 
            return None 
        
        return self.sprites[self.current_sprite_idx][0]
