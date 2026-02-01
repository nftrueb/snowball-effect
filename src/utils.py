from enum import Enum, auto

from toolshed.ui import *

WIDTH, HEIGHT = 320, 320
ROWS, COLS = 10, 10
CELL_W = WIDTH // ROWS

PLAYER_RAD_SNOW_INC = 0.1
PLAYER_IFRAMES = 60
PLAYER_SEC_TO_MELTING = 3

INITIAL_PLAYER_RAD = 10
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
            (11, 11), (11, 11), (11, 11), (13, 12), (14, 11), (14, 11), (17, 13), (18, 13), (18, 12), 
            (17, 18), (16, 18), (16, 18), (18, 19), (18, 19), (16, 0), (18, 0), (19, 0), (21, 0), (22, 0),
            (1, 9), (2, 9), (3, 8), (5, 8), (6, 9), (7, 9), (7, 8), (7, 7), (9, 7), (9, 8), (9, 6), 
            (0, 1), (0, 2), (1, 0), (2, 0), (2, 2), (7, 2), (8, 2), (9, 2), (9, 1), (8, 0), 
            (3, 21), (4, 21), (5, 21), (6, 21), (7, 22), (7, 23), (6, 24), (5, 24), (4, 24), (3, 24), (2, 24),
            (20, 24), (21, 24), (22, 24), (23, 24), (24, 24), (24, 26), (23, 26), (22, 26), (21, 26), (20, 26), (24, 24), 
            (25, 24), (26, 24), (26, 26), (25, 26), (24, 26), (28, 24), (28, 26), 
            (26, 25), (25, 22), (24, 21), (25, 20), (26, 20), (24, 0), (25, 0), (26, 0), (26, 1),
            (25, 1), (26, 2), (27, 2), (27, 3), (28, 4), (29, 5), (29, 6), (28, 5), 
            (17, 8), (17, 7), (17, 6), (18, 5), (19, 6), (18, 7), (16, 4), (15, 4), (11, 5), (11, 6), (12, 7), (13, 8), (12, 9), 
            (16, 4), (16, 9), (18, 7), (13, 9), (10, 7), (29, 29), (29, 28), (28, 29),
            (10, 29), (10, 29), (11, 29), (12, 29), (14, 29), (15, 29), (14, 28), (14, 28), (13, 28), (11, 28), (11, 27),
            (0, 28), (0, 29), (1, 29), (2, 29), (1, 28), (3, 29), 
            (0, 14), (1, 14), (0, 14), (0, 15), (1, 15), (1, 16), (0, 17), (0, 17), 
            (18, 11), (19, 10), (19, 11), (19, 9), (21, 8), (21, 8), (19, 14), (19, 15), (20, 14),
            (11, 19), (12, 19), (13, 19), (13, 20), (14, 20), (15, 20), (10, 18), 
            (20, 5), (21, 6), (25, 3), (26, 3), (26, 4), (26, 5), (26, 6), (27, 6),
            (22, 13), (23, 13), (23, 14), (24, 14), (24, 13), (26, 14), (27, 14), (26, 14)

        ]
    }
}
