from dataclasses import dataclass
from typing import List, Tuple

import pygame as pg 

@dataclass
class Dialogue: 
	text: str 
	bounding_box: pg.Rect
	underline: bool = False 
	word_wrap: bool = True 
	cursor_idx: int | None = None 
	highlight_start: int | None = None
	highlight_end: int | None = None 
	shadow_color: Tuple[int] = None
	debug: bool = False

class FontSpriteWriter: 
	def __init__(self, sprite_sheet, sprite_w=8, sprite_h=8, highlight_color=(150,150,150)): 
		self.sprite_w = sprite_w 
		self.sprite_h = sprite_h 
		self.highlight_color = highlight_color

		# key: color
		# value: font sprite sheet
		self.default_color = (255, 255, 255)
		self.fonts = {
			self.default_color: sprite_sheet
		}
		
		self.font_offset = {}
		for i in range(10): 
			self.font_offset[str(i)] = (i*sprite_w, sprite_h)

		for i in range(26): 
			self.font_offset[chr(i+65)] = (sprite_w * i, 0)

		self.font_offset[' '] = (10 * sprite_w, sprite_h)
		self.font_offset['.'] = (11 * sprite_w, sprite_h)
		self.font_offset[','] = (12 * sprite_w, sprite_h)
		self.font_offset['%'] = (14 * sprite_w, sprite_h)
		self.font_offset['!'] = (15 * sprite_w, sprite_h)
		self.font_offset['?'] = (16 * sprite_w, sprite_h)
		self.font_offset[':'] = (17 * sprite_w, sprite_h)
		self.font_offset['/'] = (18 * sprite_w, sprite_h)
		self.font_offset['-'] = (19 * sprite_w, sprite_h)
		self.font_offset['*'] = (20 * sprite_w, sprite_h)
		self.font_offset['['] = (21 * sprite_w, sprite_h)
		self.font_offset[']'] = (22 * sprite_w, sprite_h)
		self.font_offset['<'] = (23 * sprite_w, sprite_h)
		self.font_offset['>'] = (24 * sprite_w, sprite_h)

		self.font_offset['('] = (21 * sprite_w, sprite_h)
		self.font_offset[')'] = (22 * sprite_w, sprite_h)

	def __repr__(self): 
		s = '' 
		for key, value in self.font_offset.items(): 
			s += f'{key}: {value} |'
		return s 
	
	def get_sprite_dims(self):
		return (self.sprite_w, self.sprite_h)
	
	def get_size(self, text): 
		return (len(text) * self.sprite_w, self.sprite_h)
	
	def get_font_mapped_from_color(self, color) -> pg.Surface: 
		if color in self.fonts: 
			return self.fonts[color]
		
		new_color_font = self.fonts[(255,255,255)].copy()
		new_color_font.fill(color, special_flags=pg.BLEND_RGB_MULT)
		self.fonts[color] = new_color_font
		print(f'[ DEBUG ] Created new font tint for {color}')
		return new_color_font

	def render(self, surf: pg.Surface, dialogue: Dialogue, color: Tuple[int] | None = None) -> List[List[int]]: 
		# tint font and store in dictionary if not created yet
		font = self.get_font_mapped_from_color(color if color else self.default_color)
		shadow_font = None 
		if dialogue.shadow_color: 
			shadow_font = self.get_font_mapped_from_color(dialogue.shadow_color)

		rect = dialogue.bounding_box
		pos = (rect[0], rect[1])
		dim = (rect[2], rect[3])
		cols, rows = dim[0] // self.sprite_w, dim[1] // self.sprite_h

		if shadow_font: 
			dim = (dim[0]+1, dim[1]+1)

		# render grid holds the char idx that is (or should be) rendered in that position
		# getting location of rendered char is non-trival because of word wrapping
		render_grid = [[len(dialogue.text) for _ in range(cols+1)] for i in range(rows)]

		highlighting: bool = (
			dialogue.highlight_start is not None and dialogue.highlight_end is not None
		)

		# create a variable length surface to contain the entire string
		string_surf = pg.Surface(dim)
		string_surf.set_colorkey((255,0,255))
		string_surf.fill((255, 0, 255))
		
		i, j = 0, 0
		word_start_idx = None
		for idx, character in enumerate(dialogue.text): 
			# found start of new word ... check if it needs to be wrapped
			if word_start_idx is None: 
				word_end_idx = dialogue.text.find(' ', idx) 
				if word_end_idx == -1: 
					word_end_idx = len(dialogue.text)

				# wrap to next line
				if word_end_idx-idx + j > cols and i+1 < rows: 
					for k in range(cols-j+1): 
						render_grid[i][j+k] = idx
					i += 1
					j = 0

			if j == 0 and character == ' ': 
				# render cursor on previous line
				if dialogue.cursor_idx == idx: 
					cursor_pos = (pos[0] + cols*self.sprite_w-1, pos[1] + (i-1)*self.sprite_h)
					pg.draw.line(surf, (0,0,0), cursor_pos, (cursor_pos[0], cursor_pos[1] + self.sprite_h))
				
				if i != 0: 
					render_grid[i-1][cols] = idx
				continue 

			try: 
				# record char idx in render grid
				render_grid[i][j] = idx
			except: 
				print(f'[ ERROR ] Failed to entire text in grid: {dialogue.text}')

			if character.isspace(): 
				word_start_idx = None

			# shift lowercase letters to upper case
			if 'a' <= character <= 'z': 
				character = chr(ord(character)-32) 

			# draw background highlight
			if highlighting: 
				if dialogue.highlight_start <= idx < dialogue.highlight_end:
					pg.draw.rect(
						string_surf, 
						self.highlight_color, 
						pg.Rect(j*self.sprite_w, i*self.sprite_h, self.sprite_w, self.sprite_h)
					)

			# draw cursor
			if dialogue.cursor_idx == idx: 
				cursor_pos = (pos[0] + j*self.sprite_w-1, pos[1] + i*self.sprite_h)
				pg.draw.line(surf, (0,0,0), cursor_pos, (cursor_pos[0], cursor_pos[1] + self.sprite_h))

			# self.font maps character to the offset in the sprite sheet
			area = (self.font_offset[character][0], self.font_offset[character][1], self.sprite_w, self.sprite_h)

			# shadow with offset 1 pixel to right and down
			if shadow_font: 
				string_surf.blit(
					shadow_font, 
					dest=(j*self.sprite_w+1, i*self.sprite_h+1), 
					area=area
				)

			# blit foreground character
			string_surf.blit(
				font, 
				dest=(j*self.sprite_w, i*self.sprite_h), 
				area=area
			)

			# increment column for next character
			j += 1
			if j >= cols: 
				if i == rows-1: 
					break 
				i += 1
				j = 0

		# draw cursor at end of last char if not already drawn
		if dialogue.cursor_idx == len(dialogue.text): 
			cursor_pos = (pos[0] + j*self.sprite_w-1, pos[1] + i*self.sprite_h)
			pg.draw.line(surf, (0,0,0), cursor_pos, (cursor_pos[0], cursor_pos[1] + self.sprite_h))

		# copy last row of render_grid for highlighting updates
		if i != rows-1: 
			for k in range(1, rows-i): 
				render_grid[i+k] = render_grid[i]
			
		# draw outline of bounding box
		if dialogue.debug: 
			pg.draw.rect(surf,(255,0,0), (pos[0], pos[1], dim[0]-1, dim[1]-1), width=1)

		# draw text 
		surf.blit(string_surf, dest=pos)

		if dialogue.underline: 
			y_offset = 0 if shadow_font is None else -1
			dim = ( min(len(dialogue.text)*self.sprite_w, dim[0]), dim[1] + y_offset )
			start = (pos[0] - 2, pos[1] + dim[1] + 2)
			end = (pos[0] + dim[0] + 1, pos[1] + dim[1] + 2)
			pg.draw.line(surf, dialogue.shadow_color if dialogue.shadow_color else self.default_color, start, end, width=1)

		return render_grid
