from dataclasses import dataclass
from typing import Tuple, Callable

import pygame as pg 

from . import get_logger
from .window import PygameContext
from .particles import ParticleManager, PulseParticle
from .vector import Vector

logger = get_logger()

@dataclass
class Mouse: 
    rad: int 
    x: float = 0
    y: float = 0
    outline_color: Tuple[int, int, int] = (50,50,50)
    fill_color: Tuple[int, int, int] = (50,50,50)
    particles_color: Tuple[int, int, int] = (50,50,50)
    weight: int = 1
    click_particles: bool = False
    trail_particles: bool = False
    mouse_pressed_event_handler: Callable = None
    pressed: bool = False 
    particle_timer: int = 15

    def init(self):
        pg.mouse.set_visible(False)
        logger.info('Initialized custom cursor and set mouse visible to FALSE')

    def pos(self): 
        return self.x, self.y

    def draw(self, surf): 
        if self.pressed: 
            pg.draw.circle(surf, self.fill_color, self.pos(), self.rad)
        pg.draw.circle(surf, self.outline_color, self.pos(), self.rad, self.weight)

    def update(self, mpos): 
        self.x, self.y = mpos
        if pg.mouse.get_visible(): 
            pg.mouse.set_visible(False)

    def handle_event(self, event: pg.Event, pm: ParticleManager | None = None ): 
        rad = self.rad 
        make_particle = False 
        if event.type == pg.MOUSEBUTTONDOWN: 
            self.pressed = True 
            if self.mouse_pressed_event_handler is not None: 
                self.mouse_pressed_event_handler(self)

            make_particle = self.click_particles

        elif event.type == pg.MOUSEBUTTONUP: 
            self.pressed = False
            make_particle = self.click_particles

        elif event.type in { pg.MOUSEMOTION, pg.MOUSEWHEEL }: 
            rad *= 0.5
            make_particle = self.trail_particles

        if make_particle and pm is not None: 
            pm.add_particle(
                PulseParticle(
                    Vector(self.x, self.y), 
                    Vector(0,0), 
                    self.particle_timer, 
                    color=self.particles_color, 
                    rad = rad
                )
            )

def toggle_mouse_trail(mouse: Mouse): 
    mouse.trail_particles = not mouse.trail_particles 
