from enum import Enum, auto

from toolshed.ui import *

WIDTH, HEIGHT = 320, 320
ROWS, COLS = 10, 10
CELL_W = WIDTH // ROWS

PLAYER_RAD_SNOW_INC = 0.1
PLAYER_IFRAMES = 60
PLAYER_SEC_TO_MELTING = 3
INITIAL_PLAYER_RAD = 10
ITEMS_COUNT = 5
OBSTACLE_PENALTY_MULTIPLIER = 0.9
OBSTACLE_RADIUS = CELL_W // 2
MINIMUM_PLAYER_RAD = INITIAL_PLAYER_RAD * OBSTACLE_PENALTY_MULTIPLIER

LORE_PADDING = 10

WHITE = (252, 252, 252)

class ASN(Enum): 
    LeftClick = auto()
    RightClick = auto()

    Tree1 = auto()
    Tree2 = auto()
    Tree3 = auto()

    TrampledSnow1 = auto()
    TrampledSnow2 = auto()
    TrampledSnow3 = auto()

    Hat = auto()
    Carrot = auto()
    Coal = auto()
    Buttons = auto()
    Scarf = auto()

    Title = auto()

atlas_offset = {
    ASN.LeftClick: (16, 16, 16, 16), 
    ASN.RightClick: (32, 16, 16, 16), 

    ASN.Tree1: (0, 32, 16, 16),
    ASN.Tree2: (16, 32, 16, 16),
    ASN.Tree3: (32, 32, 16, 16),

    ASN.TrampledSnow1: (0, 48, 16, 16),
    ASN.TrampledSnow2: (16, 48, 16, 16),
    ASN.TrampledSnow3: (32, 48, 16, 16),

    ASN.Hat: (80, 0, 16, 16),
    ASN.Carrot: (96, 0, 16, 16),
    ASN.Coal: (112, 0, 16, 16),
    ASN.Buttons: (128, 0, 16, 16),
    ASN.Scarf: (144, 0, 16, 16), 

    ASN.Title: (0, 99, 186, 13)
}

def init_ui(fsr: FontSpriteWriter, assets) -> SceneManager: 
    sc = SceneManager() 
    init_ui_main_menu(sc, fsr, assets)  
    return sc 


def init_ui_main_menu(sc: SceneManager, fsr: FontSpriteWriter, assets): 
    ui = UI(fsr) 
    sw, sh = fsr.sprite_w, fsr.sprite_h

    s = 'Play'
    node = ToolshedButtonNode(tag=s, bounds=pg.Rect(WIDTH//2, HEIGHT // 2, len(s)*sw, sh)) 
    node.text = s
    node.center_align = True
    node.secondary_color = Color((245, 232, 255))
    node.secondary_shadow = Color((100, 100, 100))
    node.hoverable = True
    node.init()
    ui.insert(node)

    s = 'Quit'
    node = ToolshedButtonNode(tag=s, bounds=pg.Rect(WIDTH//2, HEIGHT // 2 + node.bounds.h*2, len(s)*sw, sh)) 
    node.text = s
    node.center_align = True
    node.secondary_color = Color((245, 232, 255))
    node.secondary_shadow = Color((100, 100, 100))
    node.hoverable = True
    node.init()
    ui.insert(node)

    sc.insert('main-menu', ui)

levels = {
    'tutorial': {
        'grid_dims': (10, 10), 
        'player_pos': (6, 8), 
        'items': [
            (8, 8), 
            (1, 8), 
            (1, 1), 
            (8, 1), 
            (3, 4)
        ], 
        'obstacles': [
            (3, 2), 
            (1, 6), 
            (2, 6), 
            (2, 7), 
            (3, 7), 
            (7, 0), 
            (8, 2), 
            (7, 2), 
            (5, 4), 
            (5, 5), 
            (6, 4), 
            (5, 3), 
            (4, 4)
        ]
    }, 

    'main': { 
        'grid_dims': (30, 30), 
        'player_pos': (15, 15), 
        'items': [
            (4, 23),
            (8, 8), 
            (24, 10), 
            (8, 1), 
            (27, 25)
        ], 
        'obstacles': [
            (19, 0), (8, 0), (22, 26), (19, 9), (9, 8), (11, 5), (2, 2), (0, 14), (13, 8), (26, 5), (21, 0), (1, 15), (26, 14), (24, 26), (18, 19), (27, 6), (28, 5), (8, 2), (9, 1), (19, 11), (3, 24), (5, 21), (29, 6), (13, 19), (18, 12), (10, 29), (26, 25), (13, 28), (3, 8), (20, 24), (17, 7), (12, 29), (26, 0), (13, 12), (18, 5), (24, 21), (25, 20), (1, 28), (7, 23), (23, 13), (29, 29), (20, 26), (19, 6), (0, 2), (14, 28), (26, 2), (24, 14), (7, 7), (18, 7), (26, 20), (25, 22), (2, 29), (9, 7), (3, 21), (23, 24), (15, 4), (26, 4), (18, 0), (1, 14), (7, 9), (25, 24), (22, 0), (28, 4), (23, 26), (24, 0), (13, 9), (26, 6), (7, 2), (1, 16), (18, 11), (11, 27), (2, 24), (25, 26), (20, 5), (20, 14), (6, 24), (9, 2), (12, 19), (4, 24), (1, 0), (17, 18), (25, 1), (19, 15), (1, 9), (11, 11), (11, 29), (0, 29), (21, 6), (15, 20), (22, 13), (15, 29), (29, 28), (21, 24), (27, 3), (26, 1), (25, 3), (16, 0), (28, 29), (16, 9), (21, 8), (23, 14), (14, 11), (21, 26), (27, 14), (17, 13), (19, 10), (10, 7), (11, 6), (0, 15), (29, 5), (26, 24), (6, 21), (12, 7), (4, 21), (17, 6), (28, 24), (16, 4), (10, 18), (0, 17), (13, 20), (18, 13), (26, 26), (12, 9), (7, 22), (17, 8), (0, 1), (25, 0), (19, 14), (5, 24), (28, 26), (11, 19), (11, 28), (0, 28), (24, 13), (16, 18), (1, 29), (27, 2), (5, 8), (22, 24), (9, 6), (14, 20), (2, 0), (14, 29), (2, 9), (3, 29), (26, 3), (6, 9), (7, 8), (24, 24)
        ]
    }
}
