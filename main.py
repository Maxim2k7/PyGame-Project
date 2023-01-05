# -*- coding: utf-8 -*-
import pygame
import os
import sys
import math


# глобальные параметры, функции и объекты для игры
pygame.init()
screen_size = (1024, 768)
screen = pygame.display.set_mode(screen_size)
screen_rect = (0, 0, screen_size[0], screen_size[1])
FPS = 30


def terminate():
    pygame.quit()
    sys.exit


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
        self.rect = None

    def get_event(self, event):
        pass


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, group, speed):
        super().__init__(group)
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


# переход от сцены к сцене
class Fade_Transition(Sprite):
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
class Back_Ground_Part(Sprite):
    def __init__(self, image):
        super().__init__(sprite_group)
        self.image = image
        self.rect = self.image.get_rect()


class Back_Ground:
    def __init__(self, image, vel):
        self.pic1 = Back_Ground_Part(image)
        self.pic2 = Back_Ground_Part(image)
        self.y = 0
        self.lim = screen_size[1]
        self.vel = vel

    def update(self):
        self.y += self.vel / FPS
        self.y %= self.lim
        self.pic1.rect.y = int(self.y)
        self.pic2.rect.y = int(self.y) - screen_size[1]


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


class Start_Game(Sprite):
    def __init__(self, image):
        super().__init__(sprite_group)
        self.image = image
        self.rect = self.image.get_rect()
        self.image.set_alpha(0)
        self.rect.centerx = screen_size[0] // 2
        self.rect.centery = screen_size[1] // 4 * 3


# классы для основной игры
class Player(AnimatedSprite):
    def __init__(self, sheet, columns, rows, x, y, group, speed, vel):
        super().__init__(sheet, columns, rows, x, y, group, speed)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_bounding_rect()
        self.x = x
        self.y = y
        self.rect.centerx = x
        self.rect.centery = y
        self.movex = 0
        self.movey = 0
        self.vel = vel

    def update(self):
        super().update()
        self.x += self.vel * self.movex / FPS
        self.y += self.vel * self.movey / FPS
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


class Border(pygame.sprite.Sprite):
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
        self.image = star_image
        self.color_key = star_image.get_colorkey()
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.x = x
        self.y = y
        self.vel = vel
        self.rot_spd = rot_spd
        self.rot = 0

    def update(self):
        self.y += self.vel / FPS
        self.rot += self.rot_spd / FPS
        if self.vel > 0:
            self.vel -= 100 / FPS
        else:
            self.vel = 0
        self.image = pygame.transform.rotate(star_image, self.rot)
        self.image.set_colorkey(self.color_key)
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)


# инициализация переменных в игре
sprite_group = SpriteGroup()
player_group = SpriteGroup()
enemies_group = SpriteGroup()
overlap_group = SpriteGroup()
running = True
state = "start_screen"
time = 0
bgrnd = Back_Ground(pygame.transform.scale(load_image('bgrnd_space.png'), screen_size), 50)
fade = Fade_Transition(pygame.transform.scale(load_image('fade_transition.png'), screen_size), 255)
star_image = load_image("star_normal.png", -1)
star_anim = load_image("star_breaking_anim_sheet.png", -1)
star_piece = load_image("star_piece.png", -1)
clock = pygame.time.Clock()
logo = None
start = None
player = None
start_sound = pygame.mixer.Sound("data/snd_start.ogg")
scene_objects = []
tborder = Border(-1, -1, screen_size[0] + 1, -1)
bborder = Border(-1, screen_size[1] + 1, screen_size[0] + 1, screen_size[1] + 1)
lborder = Border(-1, -1, -1, screen_size[1] + 1)
rborder = Border(screen_size[0] + 1, -1, screen_size[0] + 1, screen_size[1] + 1)


# инициализация и воспроизведение работы экрана запуска игры
def start_screen():
    global logo, start, scene_objects, running, state, time
    logo = Logo(load_image('ttl_logo.png'))
    start = Start_Game(load_image('ttl_start.png', 0))
    scene_objects = [logo, start]

    pygame.mixer.music.load('data/mus_start_screen.wav')
    pygame.mixer.music.play(-1)

    while running and state == "start_screen":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and fade.fade == 0:
                    start.image.set_alpha(0)
                    bgrnd.vel = 0
                    logo.stop = True
                    fade.fade = -1
                    pygame.mixer.music.stop()
                    pygame.mixer.Sound.play(start_sound)
        time += 1000 / FPS
        bgrnd.update()
        sprite_group.update()
        overlap_group.update("game")
        if fade.loaded:
            start.image.set_alpha(255)
            fade.loaded = False
        sprite_group.draw(screen)
        overlap_group.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()
    logo = None
    start = None
    fade.fade = 1
    bgrnd.vel = 50


# инициализация и воспроизведение работы игры
def game():
    global player, scene_objects, running, state, time
    player = Player(load_image("player_ship_anim_sheet.png", -1), 4, 1,
                    screen_size[0] // 2, screen_size[1] // 2, player_group, 6, 200)
    scene_objects = [player]
    import csv
    with open('data/lvl_01.csv', encoding="utf8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t', quotechar='"')
        attacks = list(reader)
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
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_UP and active[0]:
                    player.movey -= -1
                if event.key == pygame.K_DOWN and active[1]:
                    player.movey -= 1
                if event.key == pygame.K_LEFT and active[2]:
                    player.movex -= -1
                if event.key == pygame.K_RIGHT and active[3]:
                    player.movex -= 1
        time += 1000 / FPS
        performed = []
        for attack in attacks:
            if int(attack["time"]) <= time:
                if attack["type"] == "star":
                    Star(int(attack["x"]), int(attack["y"]), int(attack["vel"]), int(attack["rot_spd"]))
                performed.append(attack)
        for attack in performed:
            attacks.remove(attack)
        bgrnd.update()
        sprite_group.update()
        player_group.update()
        enemies_group.update()
        overlap_group.update("game")
        sprite_group.draw(screen)
        player_group.draw(screen)
        enemies_group.draw(screen)
        overlap_group.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()
    player = None
    fade.fade = 1
    bgrnd.vel = 50


# запуск действий
if __name__ == "__main__":
    start_screen()
    game()
    pygame.quit()