
class AtlasManager:
    def __init__(self, sprite_sheet: pg.Surface, offsets): 
        self.sprite_sheet = sprite_sheet 
        self.offsets = offsets

    def get_sprite(self, sprite_name) -> pg.Surface: 
        return self.sprite_sheet.subsurface(self.offsets[sprite_name]) 
    
    def get_atlas(self): 
        return self.sprite_sheet