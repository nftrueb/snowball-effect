import asyncio
import math
from random import random, randint, choice
from time import time 
from typing import List

import pygame as pg

from toolshed import get_logger
from toolshed.window import PygameContext
from toolshed.font import FontSpriteWriter, Dialogue
from toolshed.vector import Vector
from toolshed.particles import ParticleManager, PulseParticle, CircParticle, EllipseParticle

from utils import *

logger = get_logger()


# TOOLSHED FUNCTIONS
# Toolshed Idea: Frame Counter Singleton for implementing game logic every n frames
class AtlasManager:
    def __init__(self, sprite_sheet: pg.Surface, offsets): 
        self.sprite_sheet = sprite_sheet 
        self.offsets = offsets

    def get_sprite(self, sprite_name) -> pg.Surface: 
        return self.sprite_sheet.subsurface(self.offsets[sprite_name]) 
    
    def get_atlas(self): 
        return self.sprite_sheet

def increment_to_limit(value, limit):
    if value is not None: 
        value += 1 
        if value >= limit: 
            value = None 
    return value 

def decrement_to_limit(value, limit=0):
    if value is not None: 
        value -= 1 
        if value <= limit: 
            value = None 
    return value 

def coords_to_grid_index(pos, cell_w): 
    return int(pos[0]) // cell_w, int(pos[1]) // cell_w

def grid_index_to_coords_centered(pos, cell_w): 
    scaled = list(multiply_tuple_by_int(pos, CELL_W))
    scaled[0] += CELL_W // 2
    scaled[1] += CELL_W // 2 
    return tuple(scaled)

def multiply_tuple_by_int(tup, scalar, idx=None): 
    if idx is None: 
        return tuple([value * scalar for value in tup])
    
    if idx >= len(tup) or idx < 0: 
        logger.error(f'Invalid args when multipying tuple by scalar: tuple={tup} scalar={scalar} idx={idx}')
        return tup 
    
    l = list(tuple)
    l[idx] *= scalar 
    return tuple(l)

def clamp(value, upper, lower=0): 
    if value > upper: 
        return upper 
    if value < lower: 
        return lower
    return value

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

# END NEW TOOLSHED FUNCTIONS 

# FROM TRAILS APP - src/utils.py
# returns (flipx, flipy, x, y)
# flipx = collided on x-axis and caller can decide to flip velx
# flipy = collided on y-axis and caller can decide to flip vely
# x = x coord of rect that ball collided with 
# y = y coord of rect that ball collided with 
def collide_circ_and_bounding_rect(x, y, rad, rect: pg.Rect) -> bool: 
    # vertical sides 
    if rect.x - rad <= x <= rect.x + rect.w + rad and rect.y <= y <= rect.y + rect.h:
        # check if x is overlapping on the left or right side of the hitbox
        if x + rad < rect.x + rect.w//2: 
            return (True, False, rect.x - rad, y)
        
        return (True, False, rect.x+rect.w + rad, y)

    # horizontal sides
    if rect.y - rad <= y <= rect.y + rect.h + rad and rect.x <= x <= rect.x + rect.w: 
        # check if y is overlapping on the upper or lower side of the hitbox
        if y + rad < rect.y + rect.h//2: 
            return (False, True, x, rect.y - rad)
         
        return (False, True, x, rect.y+rect.h + rad)

    return (False, False, x, y)


class Cell: 
    def __init__(self, pos): 
        self.pos = pos
        self.has_snow = True 
        self.asset = None 

class Grid: 
    def __init__(self, rows=ROWS, cols=COLS, debug=False): 
        self.grid = [[Cell((j, i)) for j in range(cols)] for i in range(rows)]
        self.debug = debug 
        logger.debug(f'Initialized grid with dimensions: (rows={rows}, cols={cols})')

    def get_dims(self): 
        return len(self.grid[0]), len(self.grid)
    
    def get_dims_pixels(self): 
        return multiply_tuple_by_int(self.get_dims(), CELL_W)
    
    def get_cell(self, pos): 
        j, i = pos
        dims = self.get_dims()
        if j >= dims[0] or j < 0 or i >= dims[1] or i < 0: 
            return None 
        return self.grid[i][j]

    def trample(self, pos): 
        if pos[0] >= WIDTH or pos[0] < 0 or pos[1] >= HEIGHT or pos[1] < 0: 
            return 
        
        j, i = int(pos[0]) // CELL_W, int(pos[1]) // CELL_W
        self.grid[i][j].has_snow = False

class Item: 
    def __init__(self, pos, asset: pg.Surface, active=True): 
        self.pos = pos # world coords
        self.r = CELL_W // 4
        self.asset = asset
        self.active = active

class Obstacle: 
    def __init__(self, pos, asset: pg.Surface, rand_offset=True): 
        self.pos = pos # world coords
        if rand_offset: 
            self.pos = (pos[0] + randint(-3, 3), pos[1] + randint(-3, 3))
        self.asset = pg.transform.scale(asset, (CELL_W, CELL_W))
        self.r = OBSTACLE_RADIUS

class Player: 
    def __init__(self, pos, camera, world_dims, radius=INITIAL_PLAYER_RAD, speed=1): 
        self.x, self.y = pos # world coordinates, not indexes
        self.camera: Camera = camera
        self.rad = radius
        self.speed = speed
        self.world_dims = world_dims

        self.last_inc = None

        self.iframes = None
        self.iframe_draw_state_red = False
    
    def pos(self): 
        return self.x, self.y
    
    def draw(self, surf): 
        color = WHITE
        if self.iframes is not None:
            if self.iframes % 10 == 0: 
                self.iframe_draw_state_red = not self.iframe_draw_state_red

            if self.iframe_draw_state_red: 
                color = (255,200,200)
        
        screen_pos = self.camera.get_player_pos_on_camera(self)
        pg.draw.circle(surf, color, screen_pos, self.rad)          # base white color 
        pg.draw.circle(surf, (150,150,150), screen_pos, self.rad, width=1) # outline 

    def update(self): 
        keys = pg.key.get_pressed() 
        if keys[pg.K_w]:
            if self.y - self.rad > 0: 
                self.y -= self.speed 

        elif keys[pg.K_a]:
            if self.x - self.rad > 0: 
                self.x -= self.speed 

        elif keys[pg.K_s]:
            if self.y + self.rad < self.world_dims[1]:
                self.y += self.speed 

        elif keys[pg.K_d]:
            if self.x + self.rad < self.world_dims[0]: 
                self.x += self.speed

        self.iframes = decrement_to_limit(self.iframes) 

        if self.last_inc is not None: 
            now = time()
            if now - self.last_inc > PLAYER_SEC_TO_MELTING: 
                self.rad *= OBSTACLE_PENALTY_MULTIPLIER
                self.last_inc = now 

            debug['ptimer'] = f'{(self.last_inc%100):.2f}'
        debug['r'] = f'{self.rad:.1f}'

class Camera: 
    # TODO Cannot draw grids that are smaller than camera view ... only same size or larger
    def __init__(self, pos, grid_dims): 
        self.x, self.y = pos # world position 
        self.grid_dims = grid_dims # indexes, not pixels
        logger.debug(f'Initialized Camera with pos: {self.x, self.y} and grid_dims: {grid_dims}')

    def get_tile_range(self): 
        j = clamp(self.x, (self.grid_dims[0] - COLS) * CELL_W) // CELL_W
        i = clamp(self.y, (self.grid_dims[1] - ROWS) * CELL_W) // CELL_W
        return int(j), int(i)
    
    def draw(self, surf: pg.Surface, p: Player, g: Grid, items: List[Item], obstacles: List[Obstacle], pm: ParticleManager): 
        clampedx = clamp(self.x, (self.grid_dims[0] - COLS) * CELL_W)
        clampedy = clamp(self.y, (self.grid_dims[1] - ROWS) * CELL_W)

        j, i = self.get_tile_range()
        extra_j = 0 if j == self.grid_dims[0] - COLS else 1
        extra_i = 0 if i == self.grid_dims[1] - ROWS else 1
        end_j = min(j + COLS + extra_j, self.grid_dims[0])
        end_i = min(i + ROWS + extra_i, self.grid_dims[1])
        camera_view = [
            row[j:end_j] for row in g.grid[i:end_i]
        ]

        # draw grid 
        x_off, y_off = clampedx % CELL_W, clampedy % CELL_W
        for row_idx, row in enumerate(camera_view): 
            for col_idx, cell in enumerate(row): 
                # light gray if trampled, else white
                color = WHITE   
                rect = pg.Rect(col_idx * CELL_W - x_off, row_idx * CELL_W - y_off, CELL_W, CELL_W)
                pg.draw.rect(surf, color, rect)

                if cell.asset is not None: 
                    w, h = cell.asset.get_size()
                    pad_w, pad_h = (CELL_W - w) // 2, (CELL_W - h) // 2
                    surf.blit(cell.asset, (col_idx * CELL_W - x_off + pad_w, row_idx * CELL_W - y_off + pad_h))

                if g.debug: 
                    pg.draw.rect(surf, (225,225,225), rect, width=1) # outline

        # draw items
        def item_in_camera_view(item: Item): 
            return ( 
                item.active
                and clampedx <= item.pos[0] <= clampedx + WIDTH * CELL_W
                and clampedy <= item.pos[1] <= clampedy + HEIGHT * CELL_W
            )
        for item in filter(item_in_camera_view, items): 
            pos = (item.pos[0] - clampedx, item.pos[1] - clampedy)
            pg.draw.circle(surf, (224, 229, 255), pos, radius=item.r)
            surf.blit(item.asset, (pos[0]-item.r, pos[1]-item.r))

        # draw obstacles 
        # TODO: make aura transparent
        for ob in obstacles: 
            pos = (ob.pos[0] - clampedx, ob.pos[1] - clampedy)
            pg.draw.circle(surf, (245, 232, 255), pos, radius=ob.r) 
            w, h = ob.asset.get_size()
            surf.blit(ob.asset, (pos[0] - w//2, pos[1] - h//2))

        # draw particles that go under player 
        # for particle in filter(lambda x: isinstance(x, EllipseParticle), pm.particles): 
        #     particle.draw(surf)

        # draw player
        color = WHITE
        if p.iframes is not None:
            if p.iframes % 10 == 0: 
                p.iframe_draw_state_red = not p.iframe_draw_state_red

            if p.iframe_draw_state_red: 
                color = (255,200,200)

        screen_pos = (p.x - clampedx, p.y - clampedy) 
        pg.draw.circle(surf, color, screen_pos, p.rad)          # base white color 
        pg.draw.circle(surf, (150,150,150), screen_pos, p.rad, width=1) # outline 

        # draw the rest of the particles 
        for particle in filter(lambda x: not isinstance(x, EllipseParticle), pm.particles):
            particle.draw(surf, draw_pos=(particle.pos.x - clampedx, particle.pos.y - clampedy))

    def update(self, old_pos, new_pos): 
        self.x += new_pos[0] - old_pos[0]
        self.y += new_pos[1] - old_pos[1]

def collide_player_item(p: Player, item: Item):
    return (p.x - item.pos[0])**2 + (p.y - item.pos[1])**2 + item.r < p.rad * 1.1

def collide_player_obstacle(player: Player, ob: Obstacle): 
    # flipx, flipy, _, _ = collide_circ_and_bounding_rect(player.x, player.y, player.rad, ob.col_box)
    return (player.x-ob.pos[0])**2 + (player.y-ob.pos[1])**2 < (player.rad + ob.r)**2

def consume_snow(player: Player, grid: Grid, pm: ParticleManager, am: AtlasManager): 
    pos = player.pos() 
    px, py = pos
    j, i = coords_to_grid_index(pos, CELL_W)
    tile = grid.get_cell((j, i))
    if tile is None or not tile.has_snow:
        return 

    tx, ty = j * CELL_W + CELL_W // 2, i * CELL_W + CELL_W // 2
    if (tx-px)**2 + (ty-py)**2 < player.rad**2: 
        tile.has_snow = False 
        player.rad += PLAYER_RAD_SNOW_INC
        player.last_inc = time() 

        trampled_assets = [ ASN.TrampledSnow1, ASN.TrampledSnow2, ASN.TrampledSnow3 ]
        tile.asset = pg.transform.scale(am.get_sprite(choice(trampled_assets)), (player.rad*2, player.rad*2))
        return True
    
    return False 
        # logger.debug(f'Player radius grew to {player.rad}')

        # h = player.rad/2
        # pm.add_particle(
        #     EllipseParticle(
        #         pos=Vector(player.x, player.y+player.rad-h//2), 
        #         vel=Vector(0,0), 
        #         timer=30, 
        #         color=(117, 138, 255), 
        #         w=player.rad, 
        #         h=player.rad/2, 
        #         w_inc=0.3, 
        #         h_inc=0
        #     )
        # )

def update_camera_and_player_pos(c: Camera, p: Player): 
    old_pos = p.pos()
    p.update()
    c.update(old_pos, p.pos())
    debug['p-pos'] = f'{(p.pos())}'

APP_INITIALIZED = False

class App: 
    class State: 
        Menu = 'Menu'
        Setup = 'Setup'
        Lore = 'Lore'
        Running = 'Running'
        Gameover = 'Gameover'
        Win = 'Win'
        Editing = 'Editing'

    def __init__(self): 
        # Initalize Pygame only if needed... will run this function again upon resets
        #if not pg.get_init(): 
        self.pc = PygameContext((WIDTH, HEIGHT), 'Snowball Effect - GJ Version', icon_path='assets/icon-1024.png', screen_info_pkg=False)
        self.level_name = None
        self.reset()

    def init_lore(self): 
        self.state = App.State.Lore 
        self.lore_idx = 0
        self.lore_played = True

    def load_level(self, name): 
        self.level_name = name
        level = levels[name]
        cols, rows = level['grid_dims']
        player_pos = grid_index_to_coords_centered(level['player_pos'], CELL_W)
        
        self.grid = Grid(cols=cols, rows=rows, debug=False)
        self.camera = Camera((player_pos[0] - WIDTH//2, player_pos[1] - HEIGHT//2), self.grid.get_dims())
        self.player = Player(player_pos, self.camera, self.grid.get_dims_pixels(), speed=1) 

        possible_items = [ ASN.Scarf, ASN.Hat, ASN.Buttons, ASN.Carrot, ASN.Coal ]
        for i in range(5): 
            item_type = choice(possible_items)
            possible_items.remove(item_type)
            self.items.append(
                Item(grid_index_to_coords_centered(level['items'][i], CELL_W), asset=self.am.get_sprite(item_type))
            )

        trees = [ ASN.Tree1, ASN.Tree2, ASN.Tree3 ]
        self.obstacles = [
            Obstacle(grid_index_to_coords_centered(pos, CELL_W), self.am.get_sprite(choice(trees))) 
            for pos in level['obstacles'] 
        ]
        self.start_time = time() 
        self.last_updated_time = self.start_time
        self.state = App.State.Setup

    def reset(self): 
        level_name = self.level_name
        
        atlas = pg.image.load('assets/atlas.png').convert_alpha()
        
        self.state = App.State.Menu
        self.lore_played = False
        self.lore_idx = None 
        self.lore = [
            'In the last snowfall of the year',
            'A new snowball must grow quickly', 
            'The spring will melt in due time', 
            'Find the snowman items (x5)', 
            'Move quickly and avoid trees', 
            'Remember . . .', 
            'youre very fragile'
        ]

        # fonts
        ratio = 12 / 9
        font = pg.image.load('assets/font-bold.png').convert_alpha()
        big_font = pg.transform.scale(font, (multiply_tuple_by_int(font.get_size(), ratio)))
        self.fsr = FontSpriteWriter(font, 9, 9)
        self.big_fsr = FontSpriteWriter(big_font, 12, 12)
    
        # assets
        self.am = AtlasManager(atlas, atlas_offset)
        self.sm: SceneManager = init_ui(self.fsr, self.am.get_atlas())
        
        self.running = True
        self.pm = ParticleManager()

        # game vars
        self.camera = None
        self.grid = None 
        self.player = None 
        self.items = []
        self.obstacles = []
        self.start_time = 0
        self.last_updated_time = 0
        self.snow_collected = 0 
        self.damaged_count = 0

        self.state = App.State.Menu

        # self.load_level('main')
        self.picked = []
        debug['state'] = self.state

        APP_INITIALIZED = True

        if level_name is not None: 
            self.load_level(level_name)
        logger.info(f'Successfully reloaded level: {self.level_name}')

    async def run(self): 
        try: 
            while self.running: 
                self.handle_event()
                self.update()
                self.draw()
                await asyncio.sleep(0)
        except (KeyboardInterrupt, asyncio.CancelledError): 
            logger.info('KeyboardInterrupt recorded... exiting now') 
        except Exception as ex: 
            logger.error(f'Error encounted in main game loop', ex) 

        pg.quit()
        print('Successfully exited program ...') 

    def draw(self): 
        self.pc.frame.fill((0,0,0))
        if self.state == App.State.Menu: 
            self.pc.frame.fill(WHITE)
            self.draw_menu(self.pc.frame)

        elif self.state == App.State.Lore: 
            self.draw_lore(self.pc.frame) 

        elif self.state in { App.State.Setup, App.State.Running, App.State.Gameover, App.State.Win, App.State.Editing }: 
            self.camera.draw(self.pc.frame, self.player, self.grid, self.items, self.obstacles, self.pm)

            if self.state == App.State.Gameover: 
                self.draw_gameover(self.pc.frame)

            elif self.state == App.State.Setup: 
                self.draw_setup(self.pc.frame)

            elif self.state == App.State.Win: 
                self.draw_win(self.pc.frame)

            if self.state in {App.State.Running, App.State.Gameover, App.State.Setup}:
                self.draw_timer(self.pc.frame)

        # print_debug(self.pc.frame, self.fsr)

        self.pc.finish_drawing_frame()

    def draw_timer(self, surf): 
        s = f'{(self.last_updated_time-self.start_time):.2f}s' 
        sw, sh = self.fsr.sprite_w, self.fsr.sprite_h
        l = len(s) * sw
        rect = pg.Rect(WIDTH-l-1, 1, l, sh+1)
        self.fsr.render(surf, Dialogue(s, rect), (3, 0,158))

    def draw_gameover(self, surf): 
        x, y, w, h = (WIDTH//5, HEIGHT//8*3, WIDTH//5*3, HEIGHT//4)
        pg.draw.rect(surf, (245, 232, 255), pg.Rect(x, y, w, h), border_radius=3)
        pg.draw.rect(surf, (82, 108, 255), pg.Rect(x, y, w, h), width=1, border_radius=3)

        s = 'GAME OVER'
        sw, sh = self.big_fsr.sprite_w, self.big_fsr.sprite_h
        l = len(s) * sw
        rect = pg.Rect(WIDTH//2 - l//2, y + 10, l, sh)
        self.big_fsr.render(surf, Dialogue(s, rect), (3, 0,158))

        s = 'Score:'
        sw, sh = self.big_fsr.sprite_w, self.big_fsr.sprite_h
        l = len(s) * sw
        rect = pg.Rect(WIDTH//2 - l + 1, y + h//2 - sh//2, l, sh)
        self.big_fsr.render(surf, Dialogue(s, rect), (3, 0,158))

        s = str(self.get_score())
        sw, sh = self.big_fsr.sprite_w, self.big_fsr.sprite_h
        l = len(s) * sw
        rect = pg.Rect(WIDTH//2 + 2, y + h//2 - sh//2, l, sh)
        self.big_fsr.render(surf, Dialogue(s, rect), (3, 0,158))

        s = 'restart'
        sw, sh = self.fsr.sprite_w, self.fsr.sprite_h
        l = len(s) * sw
        rect = pg.Rect(WIDTH//2 - 17 - 2 - l, y+h - 10 - sh, l, sh)
        self.fsr.render(surf, Dialogue(s, rect), (3, 0, 158))
        surf.blit(self.am.get_sprite(ASN.LeftClick), (WIDTH//2 - 16 - 4, y+h - 10 - 12))

        s = 'quit'
        sw, sh = self.fsr.sprite_w, self.fsr.sprite_h
        l = len(s) * sw
        rect = pg.Rect(WIDTH//2 + 22 + 2, y+h - 10 - sh, l, sh)
        self.fsr.render(surf, Dialogue(s, rect), (3, 0, 158))
        surf.blit(self.am.get_sprite(ASN.RightClick), (WIDTH//2 + 6, y+h - 10 - 12))

    def draw_setup(self, surf): 
        rect = pg.Rect(WIDTH//5, HEIGHT//5*2, WIDTH//5*3, HEIGHT//5)
        pg.draw.rect(surf, (245, 232, 255), rect, border_radius=3)
        pg.draw.rect(surf, (82, 108, 255), rect, width=1, border_radius=3)

        s = 'wasd to start'
        sw, sh = self.big_fsr.sprite_w, self.big_fsr.sprite_h
        l = len(s) * sw
        rect = pg.Rect(WIDTH//2 - l//2, HEIGHT//2 - sh//2, l, sh)
        self.big_fsr.render(surf, Dialogue(s, rect), (3, 0,158))

    def draw_win(self, surf): 
        x, y, w, h = (WIDTH//5, HEIGHT//8*3, WIDTH//5*3, HEIGHT//4)
        pg.draw.rect(surf, (245, 232, 255), pg.Rect(x, y, w, h), border_radius=3)
        pg.draw.rect(surf, (82, 108, 255), pg.Rect(x, y, w, h), width=1, border_radius=3)

        s = 'You Won!'
        sw, sh = self.big_fsr.sprite_w, self.big_fsr.sprite_h
        l = len(s) * sw
        rect = pg.Rect(WIDTH//2 - l//2, y + 10, l, sh)
        self.big_fsr.render(surf, Dialogue(s, rect), (3, 0,158))

        s = 'Score:'
        sw, sh = self.big_fsr.sprite_w, self.big_fsr.sprite_h
        l = len(s) * sw
        rect = pg.Rect(WIDTH//2 - l + 1, y + h//2 - sh//2, l, sh)
        self.big_fsr.render(surf, Dialogue(s, rect), (3, 0,158))

        s = str(self.get_score())
        sw, sh = self.big_fsr.sprite_w, self.big_fsr.sprite_h
        l = len(s) * sw
        rect = pg.Rect(WIDTH//2 + 2, y + h//2 - sh//2, l, sh)
        self.big_fsr.render(surf, Dialogue(s, rect), (3, 0,158))

        s = 'restart'
        sw, sh = self.fsr.sprite_w, self.fsr.sprite_h
        l = len(s) * sw
        rect = pg.Rect(WIDTH//2 - 17 - 2 - l, y+h - 10 - sh, l, sh)
        self.fsr.render(surf, Dialogue(s, rect), (3, 0, 158))
        surf.blit(self.am.get_sprite(ASN.LeftClick), (WIDTH//2 - 16 - 4, y+h - 10 - 12))

        s = 'quit'
        sw, sh = self.fsr.sprite_w, self.fsr.sprite_h
        l = len(s) * sw
        rect = pg.Rect(WIDTH//2 + 22 + 2, y+h - 10 - sh, l, sh)
        self.fsr.render(surf, Dialogue(s, rect), (3, 0, 158))
        surf.blit(self.am.get_sprite(ASN.RightClick), (WIDTH//2 + 6, y+h - 10 - 12))


    def draw_menu(self, surf: pg.Surface): 
        asset = self.am.get_sprite(ASN.Title)
        w, h = asset.get_size()
        surf.blit(asset, (WIDTH//2 - w//2, HEIGHT//5 - h//2))

        self.sm.draw(surf)

    def draw_lore(self, surf): 
        self.pc.frame.fill(WHITE)
        pad = LORE_PADDING
        lore_bounds_y = (HEIGHT - (self.fsr.sprite_h + pad) * len(self.lore)) // 2
        for idx, s in enumerate(self.lore[:self.lore_idx+1]):
            sw, sh = self.fsr.sprite_w, self.fsr.sprite_h
            l = len(s) * sw
            rect = pg.Rect(WIDTH//2-l//2, lore_bounds_y + (pad + sh) * idx, l, sh)
            self.fsr.render(surf, Dialogue(s, rect), (3, 0,158))

        if self.lore_idx < len(self.lore)-1: 
            surf.blit(self.am.get_sprite(ASN.LeftClick), (WIDTH-16-2, HEIGHT-16-2))
        else: 
            s = 'Tutorial'
            sw, sh = self.fsr.sprite_w, self.fsr.sprite_h
            l = len(s) * sw
            rect = pg.Rect(WIDTH//4-l//2, HEIGHT - 2 - 2*sh, l, sh)
            self.fsr.render(surf, Dialogue(s, rect), (3, 0,158))
            surf.blit(self.am.get_sprite(ASN.LeftClick), (WIDTH//4+l//2+2, HEIGHT-5-sh*2))

            s = 'Skip'
            sw, sh = self.fsr.sprite_w, self.fsr.sprite_h
            l = len(s) * sw
            rect = pg.Rect(WIDTH//4*3-l//2, HEIGHT - 2 - 2*sh, l, sh)
            self.fsr.render(surf, Dialogue(s, rect), (3, 0,158))
            surf.blit(self.am.get_sprite(ASN.RightClick), (WIDTH//4*3-l//2-2-16, HEIGHT-5-sh*2))

    # 1pt = .1 sec below 2 min ( if player won only )
    # 3pt = 1 snow collected
    # -5pt = damage
    def get_score(self):
        time_score = 0 
        if self.state == App.State.Win:
            time_score = 2 * 60 * 10 - int((self.last_updated_time - self.start_time) * 10)
        damage_score = -5 * self.damaged_count
        snow_score = self.snow_collected

        total_score = time_score + snow_score + damage_score
        return clamp(total_score, total_score+1, 0)


    def update(self): 
        self.pm.update() 

        if self.state != App.State.Running: 
            return 
        
        self.last_updated_time = time()
        
        update_camera_and_player_pos(self.camera, self.player)
        if consume_snow(self.player, self.grid, self.pm, self.am): 
            self.snow_collected += 1
            debug['snow'] = self.snow_collected

        active_items = list(filter(lambda item: item.active, self.items))
        for item in active_items:
            if collide_player_item(self.player, item): 
                item.active = False 
                if len(active_items) == 1: 
                    self.change_state(App.State.Win)
                    logger.debug(f'You finished in {(time()-self.start_time):.2f} seconds!')
                
                for _ in range(20): 
                    self.pm.add_particle(
                        CircParticle(
                            pos=Vector(self.player.x, self.player.y), 
                            vel=Vector((random()-0.5)*5, (random()-0.5)*5), 
                            color=(3, 0, 158), 
                            timer=randint(45, 60), 
                            dampening=0.9, 
                            rad=1
                        )
                    )

        for ob in self.obstacles: 
            ob.r = OBSTACLE_RADIUS + math.sin(time()+random()*2*math.pi)
            if collide_player_obstacle(self.player, ob) and self.player.iframes is None: 
                self.player.rad *= OBSTACLE_PENALTY_MULTIPLIER
                self.player.iframes = PLAYER_IFRAMES
                self.damaged_count += 1
                logger.debug(f'Player radius was reduced')  

                for _ in range(20): 
                    self.pm.add_particle(
                        CircParticle(
                            pos=Vector(self.player.x, self.player.y), 
                            vel=Vector((random()-0.5)*5, (random()-0.5)*5), 
                            color=(255,200,200), 
                            timer=randint(45, 60), 
                            dampening=0.9, 
                            rad=1
                        )
                    )

        if self.player.rad < MINIMUM_PLAYER_RAD: 
            self.change_state(App.State.Gameover) 
            logger.debug(f'GAMEOVER ... you died after {(time()-self.start_time):.2f} seconds')

    def handle_event(self):     
        mx, my = self.pc.get_event_context().mouse_pos
        wasd = {pg.K_w, pg.K_a, pg.K_s, pg.K_d}
        for event in pg.event.get(): 
            if event.type == pg.QUIT: 
                self.running = False 

            elif event.type == pg.VIDEORESIZE: 
                self.pc.update_screen_dims(event.w, event.h)

            elif event.type == pg.MOUSEMOTION: 
                node = self.sm.get_node((mx, my))
                if node is None: 
                    self.sm.clear_node_state()  
                else: 
                    self.sm.hover(node)

            elif event.type == pg.KEYUP: 
                pass
                # if event.key == pg.K_ESCAPE: 
                #     if self.state == App.State.Running: 
                #         self.change_state(App.State.Editing)
                #         self.picked = []

                # elif event.key == pg.K_SPACE: 
                #     if self.state == App.State.Editing: 
                #         logger.debug(f'{self.picked}')
                #         self.change_state(App.State.Running)

            elif event.type == pg.KEYDOWN: 
                if event.key in wasd: 
                    if self.state in App.State.Setup: 
                        self.change_state(App.State.Running)
                        self.player.last_inc = time()

            elif event.type == pg.MOUSEBUTTONUP: 
                logger.debug(f'Mouse clicked at ({mx:.{2}f}, {my:.{2}f}),{coords_to_grid_index((mx, my), CELL_W)}')
                node = self.sm.get_node((mx, my))
                if self.state == App.State.Menu: 
                    if node is not None: 
                        if self.sm.current_scene == 'main-menu': 
                            if node.tag == 'Play': 
                                self.sm.change_scene(None, (mx, my))
                                self.load_level('main') if self.lore_played else self.init_lore()

                            elif node.tag == 'Quit': 
                                self.running = False

                # elif self.state == App.State.Editing: 
                #     pos = coords_to_grid_index((mx, my), CELL_W)
                #     j, i = self.camera.get_tile_range()
                #     self.picked.append((pos[0]+j, pos[1]+i))

                elif self.state == App.State.Lore: 
                    if event.button in { pg.BUTTON_LEFT, pg.BUTTON_RIGHT }: 
                        self.lore_idx = increment_to_limit(self.lore_idx, len(self.lore)) 
                        if self.lore_idx is None: 
                            self.change_state(App.State.Setup)

                            if event.button == pg.BUTTON_RIGHT: 
                                self.load_level('main')
                            else: 
                                self.load_level('tutorial')

                if self.state in { App.State.Gameover, App.State.Win }:
                    if event.button == pg.BUTTON_RIGHT: 
                        self.reset()
                        self.change_state(App.State.Menu) 
                        self.sm.change_scene('main-menu', (mx, my))

                    if event.button == pg.BUTTON_LEFT: 
                        if self.state == App.State.Win: 
                            if self.level_name == 'tutorial': 
                                self.level_name = 'main'
                        self.reset()
                        self.change_state(App.State.Setup)
                                           

                self.pm.add_particle(
                    PulseParticle(
                        pos=Vector(mx, my), vel=Vector(0,0), 
                        timer=30, color=(117, 138, 255), rad=4
                    )
                )

    def change_state(self, new_state): 
        self.state =  new_state
        debug['state'] = new_state

if __name__ == '__main__': 
    app = App()
    asyncio.run(app.run())
