import math

class Vector: 
    def __init__(self, x, y): 
        self.x = x 
        self.y = y 
        self.mag = self.get_magnitude()

    def __repr__(self): 
        return (f'Vector(x={self.x}  y={self.y})')
    
    def __eq__(self, other): 
        return self.x == other.x and self.y == other.y
    
    def __copy__(self): 
        return Vector(self.x, self.y) 
    
    def set_x(self, x): 
        self.x = x
        self.mag = self.get_magnitude()

    def set_y(self, y): 
        self.y = y
        self.mag = self.get_magnitude()

    def unpack(self): 
        return self.x, self.y

    def add(self, v): 
        self.x += v.x 
        self.y += v.y 

    def subtract(self, v): 
        v.scale(-1)
        self.x += v.x 
        self.y += v.y 

    def get_magnitude(self): 
        return math.sqrt(self.x**2 + self.y**2)

    def norm(self): 
        try: 
            self.x /= self.mag
            self.y /= self.mag  
        except ZeroDivisionError as e: 
            print(f'ERROR: could not normalize vector: {e}')

    def scale(self, n): 
        self.x *= n 
        self.y *= n
        self.mag = self.get_magnitude()

    def clamp(self, n): 
        if self.mag > n: 
            self.norm()
            self.scale(n)
