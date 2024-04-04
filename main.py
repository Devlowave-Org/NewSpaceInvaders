import pyxel

direction_offset = {
    0: (0, 1),  # Down
    1: (0, -1),  # Up
    2: (-1, 0),  # Left
    3: (1, 0)  # Right
}


class Spaceship:
    def __init__(self):
        self.x = pyxel.mouse_x
        self.y = pyxel.mouse_y
        self.velocity = 0.15
        self.velocity_x = 0
        self.velocity_y = 0
        self.direction = 3
        self.previous_direction_x = 3

    def update(self):
        self.keyboard_input()
        self.update_position_and_velocity()

    def keyboard_input(self):
        direction_keys = {0: (pyxel.KEY_DOWN, pyxel.KEY_S, pyxel.GAMEPAD1_BUTTON_DPAD_DOWN),
                          1: (pyxel.KEY_UP, pyxel.KEY_Z, pyxel.GAMEPAD1_BUTTON_DPAD_UP),
                          2: (pyxel.KEY_LEFT, pyxel.KEY_Q, pyxel.GAMEPAD1_BUTTON_DPAD_LEFT),
                          3: (pyxel.KEY_RIGHT, pyxel.KEY_D, pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)}

        for direction_nbr, (key1, key2, key3) in direction_keys.items():
            if pyxel.btn(key1) or pyxel.btn(key2) or pyxel.btn(key3):
                self.direction = direction_nbr
                if direction_nbr >= 2:
                    self.previous_direction_x = direction_nbr

                self.velocity_x += direction_offset[direction_nbr][0] * self.velocity
                self.velocity_y += direction_offset[direction_nbr][1] * self.velocity

    def update_position_and_velocity(self):
        self.velocity_x *= 0.9
        self.velocity_y *= 0.9
        self.x += self.velocity_x
        self.y += self.velocity_y

    def draw(self):
        # fire_spaceship = {(self.x, self.y, 0, 155, 82, 23, 23, 0), ()}
        w = 24
        sprite_v = 82 if abs(self.velocity_x) > 0.9 or abs(self.velocity_y) > 0.9 else 189
        sprite_w = -w if self.direction == 2 or (self.direction < 2 and self.previous_direction_x == 2) else w

        pyxel.blt(self.x, self.y, 0, 155, sprite_v, sprite_w, 23, 0)


class App:
    def __init__(self):
        pyxel.init(224, 248, "Pac-Man", 65, pyxel.KEY_ESCAPE, 10)
        pyxel.load("theme.pyxres")
        self.spaceship = Spaceship()
        pyxel.run(self.update, self.draw)

    def update(self):
        self.spaceship.update()

    def draw(self):
        pyxel.cls(0)
        self.spaceship.draw()


App()
