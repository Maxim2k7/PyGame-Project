# -*- coding: utf-8 -*-
import pygame
import os
import math
import random

# глобальные параметры, функции и объекты для игры
pygame.init()
screen_size = (1024, 768)
screen = pygame.display.set_mode(screen_size)
screen_rect = (0, 0, screen_size[0], screen_size[1])
FPS = 30


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


class SpriteGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

    def get_event(self, event):
        for sprite in self:
            sprite.get_event(event)


class Sprite(pygame.sprite.Sprite):
    def __init__(self, group):
        super().__init__(group)
        self.add(all_sprites)
        self.rect = None


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, group, speed):
        super().__init__(group)
        self.add(all_sprites)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)
        self.speed = speed

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))

    def update(self):
        self.cur_frame += self.speed / FPS
        if self.cur_frame >= len(self.frames):
            self.cur_frame -= (int(self.cur_frame) // len(self.frames)) * len(self.frames)
        self.image = self.frames[int(self.cur_frame)]


class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0

    def apply(self, obj):
        obj.rect.x += self.x
        obj.rect.y += self.y

    def update(self, target):
        self.x = target[0]
        self.y = target[1]


# переход от сцены к сцене
class FadeTransition(pygame.sprite.Sprite):
    def __init__(self, image, spd):
        super().__init__(overlap_group)
        self.image = image
        self.rect = self.image.get_rect()
        self.fade = 1
        self.loaded = False
        self.spd = spd

    def update(self, next_state):
        if self.fade == 1:
            self.fade_in()
        elif self.fade == -1:
            self.fade_out(next_state)

    def fade_in(self):
        a = self.image.get_alpha() - self.spd / FPS
        if a <= 0:
            self.fade = 0
            a = 0
            self.loaded = True
        self.image.set_alpha(int(a))

    def fade_out(self, next_state):
        a = self.image.get_alpha() + self.spd / FPS
        if a >= 255:
            self.fade = 0
            a = 255
            for obj in scene_objects:
                obj.kill()
            global state
            state = next_state
        self.image.set_alpha(int(a))


# части заднего плана
class BackGroundPart(Sprite):
    def __init__(self, image):
        super().__init__(sprite_group)
        self.image = image
        self.rect = self.image.get_rect()


class BackGround:
    def __init__(self, image, vel):
        self.pic1 = BackGroundPart(image)
        self.pic2 = BackGroundPart(image)
        self.y = 0
        self.lim = screen_size[1]
        self.vel = vel

    def update(self):
        self.y += self.vel / FPS
        self.y %= self.lim
        self.pic1.rect.y = int(self.y)
        self.pic2.rect.y = int(self.y) - screen_size[1]

    def kill(self):
        self.pic1.kill()
        self.pic2.kill()


# классы для начального экрана игры
class Logo(Sprite):
    def __init__(self, image):
        super().__init__(sprite_group)
        self.orig_im = image
        self.image = image
        self.rect = self.image.get_rect()
        self.xsize = self.image.get_size()[0]
        self.ysize = self.image.get_size()[1]
        self.stop = False

    def update(self):
        if not self.stop:
            self.image = pygame.transform.scale(self.orig_im, (int(self.xsize * (math.sin(time / 1000) + 10) / 10),
                                                               int(self.ysize * (math.sin(time / 1000) + 10) / 10)))
            self.rect = self.image.get_rect()
            self.rect.centerx = screen_size[0] // 2
            self.rect.centery = screen_size[1] // 2


class StartGame(Sprite):
    def __init__(self, image):
        super().__init__(sprite_group)
        self.image = image
        self.rect = self.image.get_rect()
        self.image.set_alpha(0)
        self.rect.centerx = screen_size[0] // 2
        self.rect.centery = screen_size[1] // 4 * 3


# классы для основной игры
class Player(AnimatedSprite):
    def __init__(self, sheet, columns, rows, x, y, group, speed, vel, inv_t, mask):
        super().__init__(sheet, columns, rows, x, y, group, speed)
        self.rect = self.image.get_bounding_rect()
        self.mask = mask
        self.x = x
        self.y = y
        self.rect.centerx = x
        self.rect.centery = y
        self.movex = 0
        self.movey = 0
        self.vel = vel
        self.inv = False
        self.inv_t = inv_t
        self.hit_t = -inv_t
        self.shake_dist = 0
        self.slow = False

    def update(self):
        super().update()
        self.x += self.vel * self.movex / FPS / (2 if self.slow else 1)
        self.y += self.vel * self.movey / FPS / (2 if self.slow else 1)
        self.rect.centerx = self.x
        self.rect.centery = self.y
        if self.rect.colliderect(tborder.rect):
            self.rect.y = 0
            self.y = self.rect.centery
        elif self.rect.colliderect(bborder.rect):
            self.rect.y = screen_size[1] - self.rect.size[1]
            self.y = self.rect.centery
        if self.rect.colliderect(lborder.rect):
            self.rect.x = 0
            self.x = self.rect.centerx
        elif self.rect.colliderect(rborder.rect):
            self.rect.x = screen_size[0] - self.rect.size[0]
            self.x = self.rect.centerx
        if self.inv:
            self.image.set_alpha(255 - self.image.get_alpha())
            if time - self.hit_t > self.inv_t:
                self.inv = False
        else:
            self.image.set_alpha(255)
        camera.update((random.randint(int(-self.shake_dist), int(self.shake_dist)),
                       random.randint(int(-self.shake_dist), int(self.shake_dist))))
        if self.shake_dist > 0:
            self.shake_dist -= 20 / FPS
        else:
            self.shake_dist = 0

    def check_hit(self, projectile):
        offset_x = int(projectile.rect.centerx - self.rect.centerx)
        offset_y = int(projectile.rect.centery - self.rect.centery)
        if self.mask.overlap(self.mask, (offset_x, offset_y)):
            if not self.inv:
                if health_bar.health > 1:
                    health_bar.health -= 1
                    pygame.mixer.Sound.play(hit_sound)
                    self.inv = True
                    self.hit_t = time
                    self.shake_dist = 20
                else:
                    self.die()
                projectile.kill()

    def die(self):
        health_bar.health = 0
        global state, next_state
        state = "game_over"
        next_state = "game"

    def win(self):
        pass

class HealthBar(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, group):
        super().__init__(group)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.health = 5
        self.image = self.frames[5 - self.health]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))

    def update(self):
        self.image = self.frames[5 - self.health]


class Border(Sprite):
    def __init__(self, x1, y1, x2, y2):
        super().__init__(sprite_group)
        if x1 == x2:
            self.image = pygame.Surface([1, y2 - y1])
            self.rect = pygame.Rect(x1, y1, 1, y2 - y1)
        else:
            self.image = pygame.Surface([x2 - x1, 1])
            self.rect = pygame.Rect(x1, y1, x2 - x1, 1)


class Star(Sprite):
    def __init__(self, x, y, vel, rot_spd):
        super().__init__(enemies_group)
        scene_objects.append(self)
        self.image = star_image
        self.mask_image = star_mask_image
        self.color_key = star_image.get_at((0, 0))
        self.mask = pygame.mask.from_surface(self.mask_image)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.x = x
        self.y = y
        self.vel = vel
        self.rot_spd = rot_spd
        self.rot = 0
        self.accel = self.vel / 2.5
        self.rot_accel = self.rot_spd

    def update(self):
        self.y += self.vel / FPS
        self.rot += self.rot_spd / FPS
        if self.rot >= 360:
            self.rot -= (int(self.rot) // 360) * 360
        if self.vel > 0:
            self.vel -= self.accel / FPS
        else:
            self.vel = 0
            if self.rot_spd > 0:
                self.rot_spd -= self.rot_accel / FPS
            else:
                self.rot_spd = 0
                pygame.mixer.Sound.stop(star_explode_sound)
                pygame.mixer.Sound.play(star_explode_sound)
                for i in range(5):
                    StarPiece(self.x, self.y, 400, i * 72 + self.rot)
                scene_objects.remove(self)
                self.kill()
        self.image = pygame.transform.rotate(star_image, self.rot)
        self.mask_image = pygame.transform.rotate(star_mask_image, self.rot)
        self.image.set_colorkey(self.color_key)
        self.mask_image.set_colorkey(self.color_key)
        self.mask = pygame.mask.from_surface(self.mask_image)
        self.rect = self.image.get_rect()
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        player.check_hit(self)


class StarPiece(Sprite):
    def __init__(self, x, y, vel, rot):
        super().__init__(enemies_group)
        scene_objects.append(self)
        self.image = pygame.transform.rotate(star_piece_image, rot)
        self.mask_image = pygame.transform.rotate(star_piece_mask_image, rot)
        self.rect = self.image.get_rect()
        self.color_key = star_piece_image.get_at((0, 0))
        self.image.set_colorkey(self.color_key)
        self.mask = pygame.mask.from_surface(self.mask_image)
        self.rect.centerx = x
        self.rect.centery = y
        self.x = x
        self.y = y
        self.vel = vel
        self.rot = rot / 360 * 2 * math.pi

    def update(self):
        self.vel += 800 / FPS
        self.x -= math.sin(self.rot) * self.vel / FPS
        self.y -= math.cos(self.rot) * self.vel / FPS
        if not self.rect.colliderect(screen_rect):
            scene_objects.remove(self)
            self.kill()
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        player.check_hit(self)


# инициализация переменных в игре
all_sprites = SpriteGroup()
sprite_group = SpriteGroup()
player_group = SpriteGroup()
enemies_group = SpriteGroup()
overlap_group = SpriteGroup()
running = True
state = "start_screen"
next_state = "game"
time = 0
black = pygame.transform.scale(load_image('fade_transition.png'), screen_size)
white = pygame.transform.scale(load_image('fade_transition2.png'), screen_size)
bgrnd = BackGround(pygame.transform.scale(load_image('bgrnd_space.png'), screen_size), 50)
fade = FadeTransition(black, 256)
star_image = load_image("star_normal.png")
star_mask_image = load_image("star_mask.png")
star_anim = load_image("star_breaking_anim_sheet.png")
star_piece_image = load_image("star_piece.png")
star_piece_mask_image = load_image("star_piece_mask.png")
clock = pygame.time.Clock()
logo = None
start = None
player = None
health_bar = None
start_sound = pygame.mixer.Sound("data/snd_start.ogg")
hit_sound = pygame.mixer.Sound("data/snd_hit.ogg")
star_explode_sound = pygame.mixer.Sound("data/snd_starexplode.ogg")
die_sound = pygame.mixer.Sound("data/snd_die.ogg")
revive_sound = pygame.mixer.Sound("data/snd_revive.ogg")
scene_objects = []
camera = Camera()
tborder = Border(-1, -1, screen_size[0] + 1, -1)
bborder = Border(-1, screen_size[1] + 1, screen_size[0] + 1, screen_size[1] + 1)
lborder = Border(-1, -1, -1, screen_size[1] + 1)
rborder = Border(screen_size[0] + 1, -1, screen_size[0] + 1, screen_size[1] + 1)
levels = 2
player_data_read = open("data/player_data.ini", mode="r")
data = [list(i.split("=")) for i in player_data_read.read().split("\n")]
data_dict = dict()
for i in data:
    data_dict[i[0]] = i[1]
player_data_read.close()


# инициализация и воспроизведение работы экрана запуска игры
def start_screen():
    global logo, start, scene_objects, running, state, next_state, time
    logo = Logo(load_image('ttl_logo.png'))
    start = StartGame(load_image('ttl_start.png', 0))
    scene_objects = [logo, start]

    pygame.mixer.music.load('data/mus_start_screen.wav')
    pygame.mixer.music.play(-1)

    while running and state == "start_screen":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z and fade.fade == 0:
                    start.image.set_alpha(0)
                    bgrnd.vel = 0
                    logo.stop = True
                    fade.fade = -1
                    pygame.mixer.music.stop()
                    pygame.mixer.Sound.play(start_sound)
        time += 1000 / FPS
        bgrnd.update()
        sprite_group.update()
        overlap_group.update(next_state)
        if fade.loaded:
            start.image.set_alpha(255)
            fade.loaded = False
        sprite_group.draw(screen)
        overlap_group.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()
    fade.fade = 1
    bgrnd.vel = 50
    time = 0
    next_state = "game_over"


# инициализация и воспроизведение работы игры
def game():
    global player, health_bar, scene_objects, running, state, next_state, time, data_dict, levels
    player = Player(load_image("player_ship_anim_sheet.png", -1), 4, 1,
                    screen_size[0] // 2, screen_size[1] // 2, player_group, 6, 400, 1200,
                    pygame.mask.from_surface(load_image("player_ship.png", -1)))
    health_bar = HealthBar(load_image("health_bar_anim_sheet.png"), 3, 2, 20, 20, sprite_group)
    scene_objects = [health_bar]
    import csv
    try:
        with open(f'data/lvl_0{data_dict["lvl"]}.csv', encoding="utf8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t', quotechar='"')
            actions = list(reader)
    except pygame.error as message:
        print('Не удаётся загрузить:', f'data/lvl_0{data_dict["lvl"]}.csv')
        raise SystemExit(message)
    pygame.mixer.music.load('data/mus_acid_cool.wav')
    pygame.mixer.music.play(-1)

    active = [False, False, False, False]
    while running and state == "game":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    player.movey += -1
                    active[0] = True
                if event.key == pygame.K_DOWN:
                    player.movey += 1
                    active[1] = True
                if event.key == pygame.K_LEFT:
                    player.movex += -1
                    active[2] = True
                if event.key == pygame.K_RIGHT:
                    player.movex += 1
                    active[3] = True
                if event.key == pygame.K_x:
                    player.slow = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_UP and active[0]:
                    player.movey -= -1
                if event.key == pygame.K_DOWN and active[1]:
                    player.movey -= 1
                if event.key == pygame.K_LEFT and active[2]:
                    player.movex -= -1
                if event.key == pygame.K_RIGHT and active[3]:
                    player.movex -= 1
                if event.key == pygame.K_x:
                    player.slow = False
        time += 1000 / FPS
        performed = []
        for action in actions:
            if int(action["time"]) <= time:
                if action["type"] == "star":
                    Star(int(action["x"]), int(action["y"]), int(action["vel"]), int(action["rot_spd"]))
                if action["type"] == "win":
                    next_state = "game"
                    state = "win"
                    if int(data_dict["lvl"]) < levels:
                        data_dict["lvl"] = str(int(data_dict["lvl"]) + 1)
                performed.append(action)
        for action in performed:
            actions.remove(action)
        bgrnd.update()
        sprite_group.update()
        player_group.update()
        enemies_group.update()
        overlap_group.update(next_state)
        for obj in all_sprites:
            if obj.rect is not None:
                camera.apply(obj)
        screen.fill(pygame.Color("black"))
        sprite_group.draw(screen)
        player_group.draw(screen)
        enemies_group.draw(screen)
        overlap_group.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()
        camera.update((-camera.x, -camera.y))
        for obj in all_sprites:
            if obj.rect is not None:
                camera.apply(obj)
    pygame.mixer.music.stop()
    pygame.mixer.Sound.stop(hit_sound)
    pygame.mixer.Sound.stop(star_explode_sound)
    bgrnd.vel = 50
    time = 0
    for obj in scene_objects:
        obj.kill()


def game_over():
    global player, bgrnd, scene_objects, running, state, next_state, time
    broken_ship = pygame.sprite.Sprite(sprite_group)
    broken_ship.image = load_image("player_ship_broken.png", -1)
    broken_ship.rect = broken_ship.image.get_rect().move((player.rect.x, player.rect.y))
    bgrnd.kill()
    fade.spd = 200
    fade.image = white
    fade.image.set_alpha(0)
    scene_objects = []

    pygame.mixer.Sound(die_sound).play()
    while running and state == "game_over":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z and fade.fade == 0:
                    fade.fade = -1
                    pygame.mixer.music.stop()
                    pygame.mixer.Sound.play(revive_sound)
        screen.fill(pygame.Color("Black"))
        time += 1000 / FPS
        sprite_group.update()
        overlap_group.update(next_state)
        sprite_group.draw(screen)
        overlap_group.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()
    time = 0
    fade.fade = 1
    broken_ship.kill()
    player.kill()
    bgrnd = BackGround(pygame.transform.scale(load_image('bgrnd_space.png'), screen_size), 50)
    fade.spd = 256


def game_won():
    global player, bgrnd, scene_objects, running, state, next_state, time
    broken_ship = pygame.sprite.Sprite(sprite_group)
    broken_ship.image = load_image("player_ship_broken.png", -1)
    broken_ship.rect = broken_ship.image.get_rect().move((player.rect.x, player.rect.y))
    bgrnd.kill()
    fade.spd = 200
    fade.image = white
    fade.image.set_alpha(0)
    scene_objects = []

    pygame.mixer.Sound(die_sound).play()
    while running and state == "win":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z and fade.fade == 0:
                    fade.fade = -1
                    pygame.mixer.music.stop()
                    pygame.mixer.Sound.play(revive_sound)
        screen.fill(pygame.Color("Purple"))
        time += 1000 / FPS
        sprite_group.update()
        overlap_group.update(next_state)
        sprite_group.draw(screen)
        overlap_group.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()
    time = 0
    fade.fade = 1
    broken_ship.kill()
    player.kill()
    bgrnd = BackGround(pygame.transform.scale(load_image('bgrnd_space.png'), screen_size), 50)
    fade.spd = 256


# запуск действий
if __name__ == "__main__":
    start_screen()
    while running:
        game()
        if state == "game_over":
            game_over()
        else:
            game_won()
    pygame.quit()
    player_data_write = open("data/player_data.ini", mode="w")
    res_str = []
    for k, v in data_dict.items():
        res_str.append(k + "=" + v)
    player_data_write.write("\n".join(res_str))
    player_data_write.close()