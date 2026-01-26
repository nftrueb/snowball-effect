from dataclasses import dataclass, field
from typing import List, Tuple 
from copy import copy 

import pygame as pg

from .font import FontSpriteWriter, Dialogue

@dataclass
class Color: 
    val: Tuple[int]

@dataclass
class Node: 
    tag: str  = ''
    bounds: pg.Rect = None
    children: List['Node'] = field(default_factory=list)
    hoverable: bool = False 
    hovered: bool = False
    active: bool = True
    debug: bool = False
    z_idx: int = 0
    # sound: pg.Sound | None = None

    def __repr__(self): 
        s = f'Node(tag={self.tag}  bounds={self.bounds}  children=[\n'
        if len(self.children) == 0: 
            s = s[:-1]
        for node in self.children: 
            s += '  ' + str(node) + '\n'
        s += '])'
        return s
    
    def draw(self, surf): 
        print(f'[ WARN ] Attempted to draw node: {self}') 

    def hover(self): 
        if self.hoverable and not self.hovered and self.active: 
            self.hovered = True 

            # if self.sound: 
            #     self.sound.play()

            return True 
        return False

    
@dataclass
class ImgNode(Node): 
    img: pg.Surface = None
    img_inv: pg.Surface = None 

    def draw(self, surf): 
        img = self.img 
        if self.hovered and self.img_inv: 
            img = self.img_inv
        surf.blit(img, self.bounds)

@dataclass
class TextNode(Node): 
    text: str = ''
    underline: bool = False
    color: Color | None = field(default_factory=lambda: Color((0,0,0)))
    secondary_color: Color | None = None
    shadow_color: Color | None = None
    font_writer: FontSpriteWriter = None

    def draw(self, surf): 
        try: 
            color = self.color.val
            dialogue = Dialogue(self.text, self.bounds)
            dialogue.underline = self.underline or self.hovered
            dialogue.shadow_color = None

            if self.hovered: 
                if self.secondary_color is not None: 
                    color = self.secondary_color.val
                
                if self.shadow_color is not None: 
                    dialogue.shadow_color = self.shadow_color.val

            self.font_writer.render(surf, dialogue, color=color)  
        except Exception as ex: 
            print(f'Caught exception on line: {ex.__traceback__.tb_lineno}: {ex}')

@dataclass
class RectNode(Node): 
    width: int = 1 
    color: Color = field(default_factory=lambda: Color((0,0,0)))

    def draw(self, surf): 
        width = 0 if self.hovered else 1
        pg.draw.rect(surf, self.color.val, self.bounds, width)

@dataclass
class TextFieldNode(Node): 
    buffer: str = ''  
    focus: bool = True 
    cursor_idx: int = 0
    render_grid: List[List[int]] = field(default_factory=list)
    updating_highlight: bool = False
    highlight_start_idx: int = 0
    highlight_end_idx: int = 0
    font_writer: FontSpriteWriter = None 
    extendable: bool = False
    align_center: bool = False

    def draw(self, surf): 
        cursor_idx = self.cursor_idx
        if not self.focus or self.highlight_start_idx != self.highlight_end_idx:
            cursor_idx = None

        if self.extendable: 
            if self.align_center: 
                self.bounds.x += self.bounds.w // 2
            
            w, _ = self.font_writer.get_size(self.buffer)
            self.bounds.w = w

            if self.align_center: 
                self.bounds.x -= self.bounds.w // 2

        dialogue = Dialogue(
            text = self.buffer, 
            bounding_box = self.bounds, 
            cursor_idx = cursor_idx, 
            highlight_start = min(self.highlight_start_idx, self.highlight_end_idx),
            highlight_end = max(self.highlight_start_idx, self.highlight_end_idx)
        )

        self.render_grid = self.font_writer.render(surf, dialogue)

    def update(self, event: pg.Event): 
        if not self.focus: 
            return 
        
        # insert new unicode character into buffer
        punctuation = { ' ', '.', ':', '/', '-', '[', ']' }
        if event.unicode and (event.unicode.isalnum() or event.unicode in punctuation): 
            self.remove_highlight_section()
            self.buffer = self.buffer[:self.cursor_idx] + event.unicode + self.buffer[self.cursor_idx:]
            self.cursor_idx += 1

        # remove characters from buffer
        if event.key == pg.K_BACKSPACE: 
            # delete characters if a highlighted section was not already deleted
            if not self.remove_highlight_section():
                self.buffer = self.buffer[:self.cursor_idx-1] + self.buffer[self.cursor_idx:]
                self.cursor_idx = max(self.cursor_idx-1, 0)

        # move cursor left and right
        if event.key == pg.K_LEFT: 
            self.cursor_idx = max(self.cursor_idx-1, 0) 
        elif event.key == pg.K_RIGHT: 
            self.cursor_idx = min(self.cursor_idx+1, len(self.buffer))

    def remove_highlight_section(self): 
        if self.highlight_start_idx != self.highlight_end_idx:
            lower = min(self.highlight_start_idx, self.highlight_end_idx)
            upper = max(self.highlight_start_idx, self.highlight_end_idx)
            self.buffer = self.buffer[:lower] + self.buffer[upper:]
            self.cursor_idx = lower
            self.highlight_start_idx = 0 
            self.highlight_end_idx = 0
            return True 
        return False

    def set_cursor_idx(self, mouse_pos, sprite_dims): 
        mx, my = self.normalize_mouse_coords(mouse_pos, sprite_dims)
        self.cursor_idx = self.render_grid[my][mx]

    def set_start_highlight(self, mouse_pos, sprite_dims): 
        mx, my = self.normalize_mouse_coords(mouse_pos, sprite_dims)
        self.highlight_start_idx = self.render_grid[my][mx]
        self.highlight_end_idx = self.render_grid[my][mx] 
        self.updating_highlight = True

    def set_end_highlight(self, mouse_pos, sprite_dims): 
        col, row = self.normalize_mouse_coords(mouse_pos, sprite_dims)
        self.highlight_end_idx = self.render_grid[row][col] 

    def normalize_mouse_coords(self, mouse_pos, sprite_dims) -> Tuple[int, int]: 
        mx, my = mouse_pos
        sw, sh = sprite_dims

        # shift mouse coords 
        mx = min(mx, self.bounds.x+self.bounds.w)
        mx = max(mx, self.bounds.x)

        my = min(my, self.bounds.y+self.bounds.h)
        my = max(my, self.bounds.y)

        mx -= self.bounds.x 
        my -= self.bounds.y 

        # shift mx forward or backward based on where on the font sprite was clicked 
        if mx % sw < sw // 2: 
            mx -= mx % sw
        else: 
            mx += sw

        # normalize mouse coords to integer index values for interacting with render_grid
        # cap the index value by the max rows and cols of grid in case of extra space in bounds rect
        mx = min(int(mx // sw), len(self.render_grid[0])-1)
        my = min(int(my // sh), len(self.render_grid)-1)

        return mx, my

@dataclass
class CheckboxNode(Node): 
    checkbox_bounds: pg.Rect = None
    checked: bool = False 
    color: Color = field(default_factory=lambda: Color((0,0,0)))
    secondary_color: Color | None = None
    shadow_color: Color | None = None
    box_fill_color: Color = field(default_factory=lambda: Color((0,0,0)))
    dialogue: Dialogue = None
    text: str = ''

    def init(self): 
        # add variable length text rect to initial bounds
        rect = pg.Rect(
            self.bounds.x+self.bounds.w+4, 
            self.bounds.y+1, 
            len(self.text) * 8, 
            8
        )
        self.dialogue = Dialogue(self.text, rect)

        # extend bounds to encompass text
        self.checkbox_bounds = copy(self.bounds)
        self.bounds = pg.Rect (
            self.bounds.x, 
            self.bounds.y, 
            rect.x + rect.w - self.bounds.x, 
            max(rect.y + rect.h - self.bounds.y, self.bounds.h)
        )

        return self
    
    def draw(self, surf): 
        try: 
            # draw outline of checkbox
            pg.draw.rect(surf, self.color.val, self.checkbox_bounds, width=1)

            # draw inside of checkbox if checked
            if self.checked: 
                rect = pg.Rect(
                    self.checkbox_bounds.x+2, 
                    self.checkbox_bounds.y+2, 
                    self.checkbox_bounds.w-4, 
                    self.checkbox_bounds.h-4
                )
                pg.draw.rect(surf, self.box_fill_color.val, rect)
            
            # draw text to right side
            if self.dialogue:
                self.dialogue.underline = self.hovered

                color = self.color.val
                if self.hovered and self.secondary_color is not None: 
                    color = self.secondary_color.val
                
                self.dialogue.shadow_color = None 
                if self.hovered and self.shadow_color is not None: 
                    self.dialogue.shadow_color = self.shadow_color.val 

                self.font_writer.render(surf, self.dialogue, color)

        except Exception as ex: 
            print(f'Caught exception on line: {ex.__traceback__.tb_lineno}: {ex}')

    def handle_input(self): 
        self.checked = not self.checked

@dataclass
class SingleChoiceNode(Node): 
    nodes: List[Node] = None
    font_writer: FontSpriteWriter = None

    def insert(self, node): 
        if not isinstance(node, CheckboxNode): 
            print('[ ERROR ] Failed to insert node in SingleChoiceNode... not a CheckboxNode')
            return 
        
        node.font_writer = self.font_writer
        self.nodes.append(node)

        if self.bounds is None: 
            self.bounds = node.bounds.copy() 
            return 
        extend_bounds(self, node.bounds)
        

    def draw(self, surf): 
        for node in self.nodes: 
            if not isinstance(node, Node): 
                print(f'[ ERROR ] SingleChoiceNode has invalid data in nodes list: {node}')
                return 
            
            node.draw(surf)

    def handle_input(self, checkbox_node): 
        for node in self.nodes: 
            if node == checkbox_node:
                continue 
            node.checked = False 
        checkbox_node.checked = True

@dataclass 
class PopoutNode(Node): 
    nodes: List[Node] = field(default_factory=list)
    panel_bounds: pg.Rect = None 
    panel_width: int = 2
    panel_bg_color: Color = field(default_factory=lambda: Color((0xff, 0xff, 0xff)))
    panel_border_color: Color = field(default_factory=lambda: Color((0, 0, 0)))
    panel_buffer: int = 2
    hover_color: Color = field(default_factory=lambda: Color((0xbf, 0xbf, 0xbf)))
    expanded: bool = False 
    img: pg.Surface = None
    img_inv: pg.Surface = None 

    def draw(self, surf): 
        img = self.img 
        if self.hovered and self.img_inv: 
            img = self.img_inv
        surf.blit(img, self.bounds) 

        if self.expanded: 
            pg.draw.rect(surf, self.panel_bg_color.val, self.panel_bounds, width=0)
            pg.draw.rect(surf, self.panel_border_color.val, self.panel_bounds, self.panel_width)

        # draw hover highlight
        # for idx, node in enumerate(self.nodes): 
        #     if node.hovered: 
        #         rect = pg.Rect(
        #             self.panel_bounds.x + self.panel_buffer + self.panel_width, 
        #             self.panel_bounds.y + self.panel_buffer + self.panel_width + ((self.panel_bounds.h-self.panel_buffer*2-self.panel_width) // len(self.nodes)) * idx, 
        #             self.panel_bounds.w - self.panel_buffer*2 - self.panel_width*2, 
        #             (self.panel_bounds.h - self.panel_buffer*2 - self.panel_width*2) // len(self.nodes)
        #         )
        #         pg.draw.rect(surf, self.hover_color.val, rect)

    def toggle_expand(self): 
        self.expanded = not self.expanded
        for node in self.nodes: 
            node.active = not node.active

@dataclass
class ToolshedButtonNode(Node): 
    text: str = ''
    width: int | None = None 
    primary_color: Color = field(default_factory=lambda: Color(val=(0,0,0)))
    primary_shadow: Color = None

    secondary_color: Color | None = field(default_factory=lambda: Color(val=(255,255,255)))
    secondary_shadow: Color | None = None

    frame_color: Color = field(default_factory=lambda: Color(val=(0,0,0)))
    background_color: Color = field(default_factory=lambda: Color(val=(255,255,255)))

    font_writer: FontSpriteWriter = None
    dialogue: Dialogue = None
    center_align: bool = False

    def init(self, text=None): 
        # shift bounds if center-aligned
        if self.center_align: 
            self.bounds.x -= self.bounds.w//2 
            self.bounds.y -= self.bounds.h//2
        
        if text: 
            self.text = text
        self.dialogue = Dialogue(text, self.bounds.copy())

        # shift bounds to encompass frame of button
        self.bounds.x -= 5
        self.bounds.y -= 3 
        self.bounds.w += 9 
        self.bounds.h += 7

        return self 

    def draw_frame(self, surf): 
        points = (
            ( self.bounds.x,                 self.bounds.y+self.bounds.h-3 ), 
            ( self.bounds.x,                 self.bounds.y+2               ), 
            ( self.bounds.x+2,               self.bounds.y                 ), 
            ( self.bounds.x+self.bounds.w-3, self.bounds.y                 ), 
            ( self.bounds.x+self.bounds.w-1, self.bounds.y+2               ), 
            ( self.bounds.x+self.bounds.w-1, self.bounds.y+self.bounds.h-3 ), 
            ( self.bounds.x+self.bounds.w-3, self.bounds.y+self.bounds.h-1 ), 
            ( self.bounds.x+2,               self.bounds.y+self.bounds.h-1 )
        )
        width = 0 if self.hovered else 1
        pg.draw.polygon(surf, self.background_color.val, points, width=0)
        pg.draw.polygon(surf, self.frame_color.val, points, width)

    def draw(self, surf): 
        try: 
            self.draw_frame(surf)

            dialogue = Dialogue(self.text, self.dialogue.bounding_box)
            dialogue.shadow_color = None 
            if self.hovered and self.secondary_shadow is not None: 
                dialogue.shadow_color = self.secondary_shadow.val 

            elif self.primary_shadow is not None: 
                dialogue.shadow_color = self.primary_shadow.val

            color = self.secondary_color.val if self.hovered else self.primary_color.val

            self.font_writer.render(surf, dialogue, color)
        except Exception as ex: 
            print(f'Caught exception on line: {ex.__traceback__.tb_lineno}: {ex}')

class UI: 
    ROOT_TAG = 'root'

    def __init__(self, font_writer: FontSpriteWriter=None, debug=False): 
        self.root = Node(tag=self.ROOT_TAG, bounds=None)
        self.font_writer = font_writer
        self.debug = debug

    def __repr__(self): 
        s = f'UI(\n{self.root}\n)'
        return s 
	
    def draw(self, surf: pg.Surface): 
        if self.debug:
            rect = pg.Rect(
                self.root.bounds.x-1, 
                self.root.bounds.y-1, 
                self.root.bounds.w+2, 
                self.root.bounds.h+2
            )
            pg.draw.rect(surf, (255,0,0), rect, width=1)

        for node in reversed(self.root.children): 
            if not node.active: 
                continue 

            try: 
                node.draw(surf)
            except Exception as ex: 
                print(f'[ ERROR ] Failed to draw node of type {node.__class__.__name__}: {ex}')

            if node.debug and node.bounds is not None: 
                pg.draw.rect(surf, (255,0,0), node.bounds, width=1)

    def insert(self, new_node: Node): 
        if isinstance(new_node, TextFieldNode) or isinstance(new_node, TextNode) or isinstance(new_node, CheckboxNode) or isinstance(new_node, ToolshedButtonNode): 
            new_node.font_writer = self.font_writer
            
        if self.root.bounds is None: 
            self.root.children.append(new_node) 
            self.root.bounds = copy(new_node.bounds)
            return 
        
        # no node was found so insert at current level
        self.root.children.append(new_node)
        self.root.children.sort(key=lambda x: x.z_idx, reverse=True)
        extend_bounds(self.root, new_node.bounds)
        
    def insert_recursive(self, node: Node, input: Node): 
        pass 

    def remove(self): 
        pass 

    def get_node_by_tag(self, tag): 
        nodes = list(filter(lambda x: x.tag == tag, self.root.children))
        return None if len(nodes) == 0 else nodes[0]
    
    def get_nodes_by_type(self, node_type) -> List[Node]:
        return list(filter(lambda x: isinstance(x, node_type), self.root.children))

    def get_node(self, pos): 
        return self.get_node_rec(self.root, pos)

    def get_node_rec(self, parent_node, pos: Tuple[float]): 
        if not parent_node.bounds.collidepoint(pos): 
            return None
        
        # position was found to be in bounding box, loop through all nodes to find 
        for node in parent_node.children: 
            if not node.active: 
                continue 

            if isinstance(node, PopoutNode) and node.expanded and node.panel_bounds.collidepoint(pos): 
                return None
            
            if node.bounds.collidepoint(pos): 
                return node 
            
        return None

def extend_bounds(node, new_bounds): 
    if new_bounds is None: 
        print('[ DEBUG ] tried extending bounds of node with None object')
        return 
    
    if new_bounds.x + new_bounds.w > node.bounds.x + node.bounds.w: 
        node.bounds.w = new_bounds.x + new_bounds.w - node.bounds.x

    if new_bounds.x < node.bounds.x: 
        node.bounds.w = node.bounds.x - new_bounds.x + node.bounds.w
        node.bounds.x = new_bounds.x

    if new_bounds.y + new_bounds.h > node.bounds.y + node.bounds.h: 
        node.bounds.h = new_bounds.y + new_bounds.h - node.bounds.y

    if new_bounds.y < node.bounds.y: 
        node.bounds.h = node.bounds.y - new_bounds.y + node.bounds.h
        node.bounds.y = new_bounds.y

class SceneManager: 
    def __init__(self): 
        self.scene_to_ui = {}
        self.current_scene = None
        self.current_hovered: str = ''

    def insert(self, scene_name: str, ui: UI): 
        self.scene_to_ui[scene_name] = copy(ui)
        if len(self.scene_to_ui.keys()) == 1: 
            self.current_scene = scene_name

    def draw(self, frame: pg.Surface): 
        if self.current_scene == None: 
            return 
        self.scene_to_ui[self.current_scene].draw(frame) 

    def change_scene(self, new_scene: str, mouse_pos: Tuple[float]): 
        # change scene
        self.current_scene = new_scene

        # clear hover state for all nodes
        self.clear_node_state()

        # set hover on node in new scene
        if new_scene is not None:
            node = self.get_node(mouse_pos)
            if node is not None:
                node.hover()

        # remove focus
        self.remove_focus_from_text_fields()

        # collapse popout
        self.close_popout_nodes()

        self.current_hovered = ''

    def get_node(self, mouse_pos): 
        if self.current_scene == None: 
            return 
        return self.scene_to_ui[self.current_scene].get_node(mouse_pos)
    
    def get_node_by_tag(self, tag, all_uis=False): 
        # either search all UIs or only active UI
        if all_uis: 
            for ui in self.scene_to_ui.values(): 
                node = ui.get_node_by_tag(tag)
                if node is not None: 
                    return node 
            return None 

        if self.current_scene == None: 
            return None 
        
        return self.scene_to_ui[self.current_scene].get_node_by_tag(tag)
    
    def get_nodes_by_type(self, node_type) -> List[Node]: 
        return self.scene_to_ui[self.current_scene].get_nodes_by_type(node_type)

    def get_current_ui(self): 
        return self.scene_to_ui[self.current_scene]
    
    def clear_node_state(self): 
        if self.current_scene is None or self.current_scene not in self.scene_to_ui: 
            return
        for node in self.scene_to_ui[self.current_scene].root.children: 
            node.hovered = False
            if isinstance(node, SingleChoiceNode): 
                for child in node.nodes: 
                    child.hovered = False
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)

    def remove_focus_from_text_fields(self, exception: str=None): 
        if self.current_scene is None or self.current_scene not in self.scene_to_ui: 
            return
        for node in self.get_nodes_by_type(TextFieldNode): 
            if node.tag == exception: 
                continue 
            node.focus = False 
            node.highlight_start_idx = 0 
            node.highlight_end_idx = 0
            node.updating_highlight = False 

    def get_focused_text_field(self) -> TextFieldNode | None: 
        for node in self.get_nodes_by_type(TextFieldNode): 
            if node.focus: 
                return node 
        return None

    def close_popout_nodes(self): 
        if self.current_scene is None or self.current_scene not in self.scene_to_ui: 
            return 
        for node in self.get_nodes_by_type(PopoutNode): 
            if node.expanded:
                node.toggle_expand()

    def set_focus_on_text_field(self, tag): 
        node = self.get_node_by_tag(tag)
        if node: 
            node.focus = True

    def clear_text_field(self, tag) -> str: 
        node: TextFieldNode = self.get_node_by_tag(tag)
        if not node: 
            return ''
        word = node.buffer
        node.buffer = ''
        node.cursor_idx = 0
        return word
    
    def hover(self, node): 
        # check it node can have hover state
        if not node.hover(): 
            return 

        # change cursor type based on node
        if isinstance(self, TextFieldNode): 
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_IBEAM)
        else: 
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)

        # update reference to the last hovered node
        if node.tag != self.current_hovered: 
            old_node = self.get_node_by_tag(self.current_hovered)
            self.current_hovered = node.tag

            if old_node is None: 
                print(f'[ INFO ] Could not find reference to hovered node: {self.current_hovered}')
                return
            old_node.hovered = False
            
        
