import pygame
import os
import sys
import math


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


pygame.init()
screen_size = (1024, 768)
screen = pygame.display.set_mode(screen_size)
FPS = 60


class ScreenFrame(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.rect = (0, 0, screen_size[0], screen_size[1])


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


class Logo(Sprite):
    def __init__(self, image):
        super().__init__(sprite_group)
        self.orig_im = image
        self.image = image
        self.rect = self.image.get_rect()
        self.xsize = self.image.get_size()[0]
        self.ysize = self.image.get_size()[1]
        self.time = 0

    def update(self):
        self.time += 1 / FPS
        self.image = pygame.transform.scale(self.orig_im, (int(self.xsize * (math.sin(self.time) + 10) / 10),
                                                           int(self.ysize * (math.sin(self.time) + 10) / 10)))
        self.rect = self.image.get_rect()
        self.rect.centerx = screen_size[0] // 2
        self.rect.centery = screen_size[1] // 2


class Start(Sprite):
    def __init__(self, image):
        super().__init__(sprite_group)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.centerx = screen_size[0] // 2
        self.rect.centery = screen_size[1] // 4 * 3



sprite_group = SpriteGroup()
player = None
running = True
bgrnd = Back_Ground(pygame.transform.scale(load_image('bgrnd_space.png'), screen_size), 50)
logo = Logo(load_image('ttl_logo.png'))
start = Start(load_image('ttl_start.png', 0))
clock = pygame.time.Clock()


def terminate():
    pygame.quit()
    sys.exit


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    bgrnd.update()
    logo.update()
    sprite_group.draw(screen)
    clock.tick(FPS)
    pygame.display.flip()
pygame.quit()