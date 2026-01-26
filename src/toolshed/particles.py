from typing import Tuple
from dataclasses import dataclass

import pygame as pg 

from .vector import Vector

class ParticleManager: 
    def __init__(self): 
        self.particles = []

    def add_particle(self, p): 
        self.particles.append(p)

    def draw(self, surf): 
        for p in self.particles: 
            p.draw(surf)

    def update(self): 
        for p in self.particles: 
            p.update() 

        self.particles = list(filter(lambda x: x.alive, self.particles))

    def clear(self): 
        self.particles = []

@dataclass
class Particle: 
    pos: Vector 
    vel: Vector
    timer: int 
    id: int | None = None
    color: Tuple[int] = (0,0,0)
    alive: bool = True
    dampening: float | None = None

    def __repr__(self): 
        return f'Particle(pos=({self.pos.x, self.pos.y})  alive={self.alive})'

    def update(self): 
        if not self.alive: 
            return 

        self.pos.add(self.vel)
        self.timer -= 1
        self.alive = self.timer > 0

        if self.dampening is not None: 
            self.vel.x *= self.dampening
            self.vel.y *= self.dampening

        # TODO 
        # rotational veloctiy 
        # growing/shrinking 

    def kill(self): 
        self.alive = False 

@dataclass
class RectParticle(Particle): 
    dim: Vector = None

    def draw(self, surf): 
        x, y = self.pos.unpack()
        w, h = self.dim.unpack()
        r = pg.Rect(x, y, w, h)
        pg.draw.rect(surf, self.color, r)

@dataclass
class CircParticle(Particle): 
    rad: int = 3

    def draw(self, surf, draw_pos=None): 
        pos = self.pos.unpack() if draw_pos is None else draw_pos
        pg.draw.circle(surf, self.color, pos, self.rad) 

@dataclass
class CircGravityParticle(CircParticle): 
    def update(self):
        super().update()
        self.vel.y += .1

@dataclass
class PulseParticle(CircParticle): 
    def draw(self, surf, draw_pos=None): 
        pg.draw.circle(surf, self.color, self.pos.unpack(), self.rad, width=1) 

    def update(self):
        super().update()
        self.rad += .3

@dataclass 
class EllipseParticle(Particle): 
    w: float = 0
    h: float = 0
    w_inc: float = 0 
    h_inc: float = 0

    def draw(self, surf): 
        w, h = self.w, self.h
        pg.draw.ellipse(surf, self.color, pg.Rect(self.pos.x - w//2, self.pos.y - h//2, w, h) , 1)

    def update(self): 
        super().update()
        self.w += self.w_inc
        self.h += self.h_inc
        
