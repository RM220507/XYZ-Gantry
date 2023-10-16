class Position_2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def convert3D(self, z=0):
        return Position(self.x, self.y, z)

class Position:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def subtract(self, pos):
        self.x -= pos.x
        self.y -= pos.y
        self.z -= pos.z

    def add(self, pos):
        self.x += pos.x
        self.y += pos.y
        self.z += pos.z

    def within(self, pos):
        return 0 <= self.x <= pos.x and 0 <= self.y <= pos.y and 0 <= self.z <= pos.z

    def copy(self):
        return Position(self.x, self.y, self.z)

    def return_value(self):
        return f"{self.x} {self.y} {self.z}"

    def set_from_pos(self, pos):
        self.x = pos.x
        self.y = pos.y
        self.z = pos.z

    def floor_div(self, factor):
        x = self.x // factor
        y = self.y // factor
        z = self.z // factor
        return Position(x, y, z)
