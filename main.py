import pyxel

direction_offset = {
    0: (0, 1),  # Down
    1: (0, -1),  # Up
    2: (-1, 0),  # Left
    3: (1, 0)  # Right
}


class Entity:
    def __init__(self, x, y, v=0.2, vx=0, vy=0, direction=3, slowdown=0.9):
        self.x, self.y = x, y
        self.velocity = v
        self.velocity_x, self.velocity_y = vx, vy
        self.direction = direction
        self.previous_direction_x = direction
        self.slowdown = slowdown

    def update_velocity(self):
        self.velocity_x *= self.slowdown
        self.velocity_y *= self.slowdown

    def update_position(self):
        self.x += self.velocity_x
        self.y += self.velocity_y


class Spaceship(Entity):
    def __init__(self, x, y, v):
        super().__init__(x, y, v)
        self.bullets = []

    def update(self):
        self.keyboard_input()
        self.update_velocity()
        self.update_position()
        self.shoot_bullets()
        self.del_bullets()
        for bullet in self.bullets:
            bullet.update()

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

    def draw(self):
        self.draw_bullets()
        self.draw_spaceship()

    def draw_spaceship(self):
        # fire_spaceship = {(self.x, self.y, 0, 155, 82, 23, 23, 0), ()}
        w = 24
        sprite_v = 82 if abs(self.velocity_x) > 0.9 or abs(self.velocity_y) > 0.9 else 189
        sprite_w = -w if self.direction == 2 or (self.direction < 2 and self.previous_direction_x == 2) else w

        pyxel.blt(self.x, self.y, 0, 155, sprite_v, sprite_w, 23)

    def draw_bullets(self):
        for bullet in self.bullets:
            bullet.draw()

    def shoot_bullets(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            vx = -1 if self.direction == 2 or (self.direction < 2 and self.previous_direction_x == 2) else 1
            self.bullets.append(Bullet(self.x + 10, self.y + 10, vx, 0, 10, 2, 1))

    def del_bullets(self):
        for bullet in self.bullets:
            if bullet.x > pyxel.width or bullet.x < 0 or bullet.y > pyxel.height or bullet.y < 0:
                self.bullets.remove(bullet)


class Bullet(Entity):
    def __init__(self, x, y, vx, vy, w, h, col):
        super().__init__(x, y, vx=vx, vy=vy)
        self.width = w
        self.height = h
        self.color = col

    def update(self):
        self.update_position()
        self.x += self.velocity_x

    def draw(self):
        pyxel.rect(self.x, self.y, self.width, self.height, self.color)


class App:
    def __init__(self):
        pyxel.init(224, 248, "Pac-Man", 65, pyxel.KEY_ESCAPE, 10)
        pyxel.load("theme.pyxres")
        self.spaceship = Spaceship(50, 50, 0.2)
        pyxel.run(self.update, self.draw)

    def update(self):
        self.spaceship.update()

    def draw(self):
        pyxel.cls(0)
        self.spaceship.draw()


App()
