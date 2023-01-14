# -*- coding: utf-8 -*-
import os
import csv
import math
import random
import pygame
from PIL import Image, ImageDraw

# глобальные параметры, функции и объекты для игры
pygame.init()
screen_size = (1024, 768)
screen = pygame.display.set_mode(screen_size)
screen_rect = (0, 0, screen_size[0], screen_size[1])
FPS = 30


# загрузка изображений
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
    def __init__(self, sheet, columns, rows, x, y, group, anim_speed):
        super().__init__(group)
        self.add(all_sprites)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)
        self.anim_speed = anim_speed

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))

    def update(self):
        if self.anim_speed != 0:
            self.cur_frame += self.anim_speed / FPS
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

    def update(self):
        if self.fade == 1:
            self.fade_in()
        elif self.fade == -1:
            self.fade_out()

    def fade_in(self):
        a = self.image.get_alpha() - self.spd / FPS
        if a <= 0:
            self.fade = 0
            a = 0
            self.loaded = True
        self.image.set_alpha(int(a))

    def fade_out(self):
        a = self.image.get_alpha() + self.spd / FPS
        if a >= 255:
            self.fade = 0
            a = 255
            for obj in scene_objects:
                obj.kill()
            global state, next_state
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
        self.lim = screen_size[0]
        self.vel = vel

    def update(self):
        self.y += self.vel / FPS
        self.y %= self.lim
        self.pic1.rect.y = int(self.y)
        self.pic2.rect.y = int(self.y) - self.lim

    def kill(self):
        self.pic1.kill()
        self.pic2.kill()


class BossBackGround(BackGround):
    def __init__(self, vel, anim_speed):
        super().__init__(bgrnd_boss_frames[0], vel)
        self.frames = bgrnd_boss_frames
        self.anim_speed = anim_speed
        self.cur_frame = 0

    def update(self):
        super().update()
        self.cur_frame += self.anim_speed / FPS
        if self.cur_frame >= len(self.frames):
            self.cur_frame -= (int(self.cur_frame) // len(self.frames)) * len(self.frames)
        self.pic1.image = self.frames[int(self.cur_frame)]
        self.pic2.image = self.frames[int(self.cur_frame)]


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


class PressZToStartText(Sprite):
    def __init__(self, image):
        super().__init__(sprite_group)
        self.image = image
        self.rect = self.image.get_rect()
        self.image.set_alpha(0)
        self.rect.centerx = screen_size[0] // 2
        self.rect.centery = screen_size[1] // 4 * 3


class Instructions(Sprite):
    def __init__(self):
        super().__init__(sprite_group)
        self.image = instr_image
        self.rect = self.image.get_rect()
        self.image.set_alpha(0)
        self.rect.x = 10
        self.rect.y = 10


class CurLevelText(Sprite):
    def __init__(self):
        super().__init__(sprite_group)
        self.image = load_image("ttl_current_level.png", -1)
        self.rect = self.image.get_rect()
        self.image.set_alpha(0)
        self.rect.centerx = screen_size[0] // 4 * 3 - 100
        self.rect.centery = screen_size[1] // 3


class CurLevel(AnimatedSprite):
    def __init__(self):
        super().__init__(load_image("ttl_numbers.png", -1), 5, 2, 0, 0, sprite_group, 0)
        self.image = self.frames[int(data_dict["lvl"]) - 1]
        self.color_key = self.image.get_at((0, 0))
        self.image = pygame.transform.scale(self.image, (25, 25))
        self.rect = self.image.get_rect()
        self.rect.centerx = screen_size[0] // 4 * 3
        self.rect.centery = screen_size[1] // 3 - 5
        self.image.set_colorkey(self.color_key)
        self.image.set_alpha(0)

    def reset(self):
        self.image = self.frames[int(data_dict["lvl"]) - 1]
        self.image = pygame.transform.scale(self.image, (25, 25))
        self.image.set_colorkey(self.color_key)


# классы для основной игры
class Player(AnimatedSprite):
    def __init__(self, sheet, columns, rows, x, y, group, speed, vel, inv_t, mask):
        super().__init__(sheet, columns, rows, x, y, group, speed)
        self.rect = self.image.get_bounding_rect()
        self.mask = mask
        self.x = x
        self.y = y
        self.n_x = x
        self.n_y = y
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
        self.n_x += self.vel * self.movex / FPS / (2 if self.slow else 1)
        self.n_y += self.vel * self.movey / FPS / (2 if self.slow else 1)
        self.x = self.n_x
        self.y = self.n_y
        self.rect.centerx = self.x
        self.rect.centery = self.y
        if self.rect.colliderect(tborder.rect):
            self.rect.y = tborder.rect.y + 1
            self.n_y = self.y = self.rect.centery
        elif self.rect.colliderect(bborder.rect):
            self.rect.y = bborder.rect.y - self.rect.size[1]
            self.n_y = self.y = self.rect.centery
        if self.rect.colliderect(lborder.rect):
            self.rect.x = lborder.rect.x + 1
            self.n_x = self.x = self.rect.centerx
        elif self.rect.colliderect(rborder.rect):
            self.rect.x = rborder.rect.x - self.rect.size[0]
            self.n_x = self.x = self.rect.centerx
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
            if not self.inv and self.alive():
                global state, next_state, fade
                if health_bar.health > 1:
                    # уменьшить кол-во оставшихся жизней
                    if fade.fade == 0:
                        health_bar.health -= 1
                        pygame.mixer.Sound.play(hit_sound)
                        self.inv = True
                        self.hit_t = time
                        self.shake_dist = 20
                    else:
                        # в случае поражения
                        health_bar.health = 0
                        state = "game_over"
                        next_state = "game"
                        fade.fade = 0
                        fade.image.set_alpha(0)
                projectile.kill()


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


# ограничение движения в пределах экрана
class Border(Sprite):
    def __init__(self, x1, y1, x2, y2):
        super().__init__(sprite_group)
        if x1 == x2:
            self.image = pygame.Surface([1, y2 - y1])
            self.rect = pygame.Rect(x1, y1, 1, y2 - y1)
        else:
            self.image = pygame.Surface([x2 - x1, 1])
            self.rect = pygame.Rect(x1, y1, x2 - x1, 1)
        self.image.set_alpha(0)


# атакующая звезда, спукающаяся вниз и затем разрывающаяся
class Star(Sprite):
    def __init__(self, x, y, vel, rot_spd):
        super().__init__(enemies_group)
        scene_objects.append(self)
        self.image = star_image
        self.color_key = star_image.get_at((0, 0))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.boss_fight = data_dict["lvl"] == str(levels)
        self.x = x
        self.y = y if not self.boss_fight else screen_size[1] - y
        self.rect.centerx = self.x
        self.rect.centery = self.y
        self.vel = vel
        self.rot_spd = rot_spd
        self.rot = 0
        self.accel = self.vel / 2.5
        self.rot_accel = self.rot_spd

    # кружение и движение вниз
    def update(self):
        # кружение и движение вниз
        self.y += self.vel / FPS if not self.boss_fight else -self.vel / FPS
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
                # разрыв звезды
                self.rot_spd = 0
                pygame.mixer.Sound.stop(star_explode_sound)
                pygame.mixer.Sound.play(star_explode_sound)
                for i in range(5):
                    ShotPiece(self.x, self.y, 400, i * 72 + self.rot, star_piece_image)
                self.kill()
        # применение изменений
        self.image = pygame.transform.rotate(star_image, self.rot)
        self.image.set_colorkey(self.color_key)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        player.check_hit(self)
        if self.boss_fight:
            boss.check_hit(self)


# вражеские пули, которые выпускают другие объекты
class ShotPiece(Sprite):
    def __init__(self, x, y, vel, rot, image):
        super().__init__(enemies_group)
        scene_objects.append(self)
        self.image = pygame.transform.rotate(image, rot)
        self.color_key = image.get_at((0, 0))
        self.image.set_colorkey(self.color_key)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.x = x
        self.y = y
        self.vel = vel
        self.rot = rot / 360 * 2 * math.pi
        self.boss_fight = data_dict["lvl"] == str(levels)

    def update(self):
        self.vel += 800 / FPS
        self.x -= math.sin(self.rot) * self.vel / FPS
        self.y -= math.cos(self.rot) * self.vel / FPS
        if not self.rect.colliderect(screen_rect):
            self.kill()
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        player.check_hit(self)
        if self.boss_fight:
            boss.check_hit(self)


class BlackHole(Sprite):
    def __init__(self, x, y, spd):
        super().__init__(enemies_group)
        scene_objects.append(self)
        ref = Image.open("data/blackhole_generator.png")
        self.pix = ref.load()
        self.x = x
        self.y = y
        self.spd = spd
        self.alph = 0
        self.color_key = (0, 0, 0, 255)
        self.make_blackhole()
        self.image = pygame.transform.scale(self.image, (1, 1))
        self.mask = pygame.mask.from_surface(self.image)
        self.image.set_alpha(0)
        self.rect = self.image.get_rect()
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        self.fx = BlackHoleFX(self)

    def update(self):
        self.offset()
        self.make_blackhole()
        self.alph += self.spd / FPS
        if self.alph >= 255:
            self.spd = -self.spd / 2
            self.alph = 255
        elif self.alph < 0:
            self.kill()
            return
        self.image.set_alpha(int(self.alph))
        self.pull()

    def offset(self):
        p_temp = self.pix[0, 0]
        for j in range(50 - 1):
            self.pix[0, j] = self.pix[0, j + 1]
        self.pix[0, -1] = p_temp

    def make_blackhole(self):
        img = Image.new("RGB", (151, 151), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        for i in range(49, -1, -1):
            draw.ellipse(((49 - i) * 3, (49 - i) * 3, i * 3 + 1, i * 3 + 1), fill=self.pix[0, i], width=1)
        self.image = pygame.transform.scale(pygame.image.fromstring(img.tobytes(), img.size, img.mode),
                                            (int((self.alph / 255 * 150 + 1) * (
                                                        math.sin(time / 50) + 10) / 10),
                                            int((self.alph / 255 * 150 + 1) * (
                                                        math.sin(time / 50) + 10) / 10)))
        self.rect = self.image.get_rect()
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        self.image.set_colorkey(self.color_key)

    def pull(self):
        if not player.inv:
            d_x = player.x - self.x
            d_y = player.y - self.y
            d = math.sqrt(d_x ** 2 + d_y ** 2)
            if d <= self.image.get_size()[0] / 2:
                player.check_hit(self)
            else:
                vel = (self.alph / 17 * 3) ** 3 / d
                vel_x = vel * d_x / d
                vel_y = vel * d_y / d
                player.n_x -= vel_x / FPS
                player.n_y -= vel_y / FPS

    def kill(self):
        self.fx.kill()
        super().kill()


class BlackHoleFX(Sprite):
    def __init__(self, blackhole):
        super().__init__(enemies_group)
        self.b_hole = blackhole
        self.orig_im = load_image("blackhole_clouds.png")
        self.image = self.orig_im
        self.color_key = self.image.get_at((0, 0))
        self.rect = self.image.get_rect()
        self.rect.centerx = self.b_hole.x
        self.rect.centery = self.b_hole.y

    def update(self):
        self.image = pygame.transform.scale(self.orig_im, (int(self.b_hole.alph ** 2 / 255 + 1),
                                                           int(self.b_hole.alph ** 2 / 255 + 1)))
        self.image = pygame.transform.rotate(self.image, int(time / 2))
        self.image.set_alpha(self.b_hole.alph // 2)
        self.image.set_colorkey(self.color_key)
        self.rect = self.image.get_rect()
        self.rect.centerx = self.b_hole.x
        self.rect.centery = self.b_hole.y


class LaserBlaster(AnimatedSprite):
    def __init__(self, x, y):
        super().__init__(laser_blaster_anim_sheet, 3, 3, x, y, enemies_group, 0)
        scene_objects.append(self)
        self.x = x
        self.y = y
        self.rot = 0
        self.image = laser_blaster_image
        self.orig_im = laser_blaster_image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        self.state = "appear"
        self.handle = LaserBlasterHandle(self)

    def update(self):
        self.mask = pygame.mask.from_surface(self.image)
        if self.state == "appear":
            self.appear()
            self.aim()
            self.rect.centerx = int(self.x)
            self.rect.centery = int(self.y)
            player.check_hit(self)
        elif self.state == "shoot":
            self.shoot()
            player.check_hit(self)
        else:
            super().update()
            self.image = pygame.transform.rotate(self.frames[int(self.cur_frame)], int(self.rot))
            self.image.set_colorkey(self.image.get_at((0, 0)))
            self.mask = pygame.mask.from_surface(self.image)
            self.rect = self.image.get_rect()
            if int(self.cur_frame) == len(self.frames) - 1:
                self.anim_speed = 0
            self.disappear()

    def appear(self):
        if self.x > screen_size[0] // 2:
            if self.x > screen_size[0] - 100:
                self.x -= 100 / FPS
            else:
                self.x = screen_size[0] - 100
                self.state = "shoot"
        else:
            if self.x < 100:
                self.x += 100 / FPS
            else:
                self.x = 100
                self.state = "shoot"

    def aim(self):
        a = (self.x - player.x)
        b = (self.y - player.y)
        c = math.sqrt(a ** 2 + b ** 2)
        if c != 0:
            ang_r = math.asin(b / c)
            ang_d = ang_r / math.pi * 180
            self.rot = ang_d if a <= 0 else 180 - ang_d
            self.image = pygame.transform.rotate(self.orig_im, int(self.rot))
            self.mask = pygame.mask.from_surface(self.image)
            self.rect = self.image.get_rect()

    def shoot(self):
        pygame.mixer.Sound.stop(laser_sound)
        pygame.mixer.Sound.play(laser_sound)
        ShotPiece(self.x, self.y, 1000, self.rot - 90, pygame.transform.scale(load_image("laser_shot.png"), (46, 46)))
        self.anim_speed = 24
        self.state = "disappear"

    def disappear(self):
        if self.x > screen_size[0] // 2:
            if self.x < 1174:
                self.x += 450 / FPS
            else:
                self.kill()
                return
        else:
            if self.x > -150:
                self.x -= 450 / FPS
            else:
                self.kill()
                return
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        player.check_hit(self)

    def kill(self):
        self.handle.kill()
        super().kill()


class LaserBlasterHandle(Sprite):
    def __init__(self, laser_blaster):
        super().__init__(enemies_group)
        self.blstr = laser_blaster
        if self.blstr.x > screen_size[0] - 100:
            self.image = pygame.transform.flip(laser_blaster_handle_image, True, False)
        else:
            self.image = laser_blaster_handle_image
        self.rect = self.image.get_rect()
        self.rect.centerx = int(self.blstr.x)
        self.rect.centery = int(self.blstr.y)

    def update(self):
        self.rect.centerx = int(self.blstr.x)
        self.rect.centery = int(self.blstr.y)


class Boss(AnimatedSprite):
    def __init__(self):
        super().__init__(boss_body, 1, 1, screen_size[0] // 2, screen_size[1] // 2, boss_group, 0)
        scene_objects.append(self)
        self.x = screen_size[0] // 2
        self.y = screen_size[1] // 2
        self.rot = 0
        self.orig_im = boss_body
        self.image = boss_body
        self.rect = self.image.get_rect()
        self.color_key = self.image.get_at((screen_size[0] // 2, screen_size[0] // 2))
        self.image.set_colorkey(self.color_key)
        self.rect.centerx = self.x
        self.rect.centery = self.y
        self.xsize = self.rect.w
        self.ysize = self.rect.h
        self.children = [BadGuy(), Engine(boss_engine1, boss_engine1_inv), Engine(boss_engine2, boss_engine2_inv)]

    def update(self):
        self.sin_pulse(self, self.orig_im)
        for child in self.children:
            self.sin_pulse(child, child.orig_im)
        if fade.fade == 0 and self.children[0].health == 0:
            global next_state
            next_state = "win"
            fade.fade = -1
            fade.image = white
            fade.image.set_alpha(0)

    def sin_pulse(self, part, orig_im):
        part.image = pygame.transform.scale(orig_im,
                                            (int(part.xsize * (math.sin(time / 1000) / 2 + 20.5) / 20),
                                             int(part.ysize * (math.sin(time / 1000) / 2 + 20.5) / 20)))
        part.rect = part.image.get_rect()
        part.image.set_colorkey(part.color_key)
        part.rect.centerx = part.x
        part.rect.centery = part.y

    def kill(self):
        for child in self.children:
            child.kill()
        super().kill()

    def check_hit(self, projectile):
        for child in self.children:
            if pygame.sprite.collide_mask(child, projectile) and child.health > 0 and projectile.alive():
                if child != self.children[0] or (child == self.children[0] and
                                                 all([i.health <= 0 for i in self.children if i != self.children[0]])):
                    # уменьшить кол-во жизни части босса
                    self.sin_pulse(child, child.inv_im)
                    pygame.mixer.Sound.stop(boss_hit_sound)
                    pygame.mixer.Sound.play(boss_hit_sound)
                    child.health -= 1
                    if child.health <= 0:
                        # в случае уничтожения
                        child.health = 0
                        pygame.mixer.Sound.stop(boss_explode_sound)
                        pygame.mixer.Sound.play(boss_explode_sound)
                        player.hit_t = time
                        player.shake_dist = 20
                projectile.kill()


class BadGuy(AnimatedSprite):
    def __init__(self):
        super().__init__(boss_enemie, 1, 1, screen_size[0] // 2, screen_size[1] // 2, boss_group, 0)
        self.x = screen_size[0] // 2
        self.y = screen_size[1] // 2
        self.rot = 0
        self.orig_im = boss_enemie
        self.inv_im = boss_enemie_inv
        self.image = boss_enemie
        self.color_key = self.image.get_at((0, 0))
        self.image.set_colorkey(self.color_key)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.centerx = self.x
        self.rect.centery = self.y
        self.xsize = self.rect.w
        self.ysize = self.rect.h
        self.health = 10


class Engine(AnimatedSprite):
    def __init__(self, image, inv_im):
        super().__init__(image, 1, 1, screen_size[0] // 2, screen_size[1] // 2, boss_group, 0)
        self.x = screen_size[0] // 2
        self.y = screen_size[1] // 2
        self.rot = 0
        self.orig_im = image
        self.inv_im = inv_im
        self.image = image
        self.color_key = self.image.get_at((0, 0))
        self.image.set_colorkey(self.color_key)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.centerx = self.x
        self.rect.centery = self.y
        self.xsize = self.rect.w
        self.ysize = self.rect.h
        self.health = 10


# инициализация переменных в игре
# визуальная часть
all_sprites = SpriteGroup()
sprite_group = SpriteGroup()
player_group = SpriteGroup()
enemies_group = SpriteGroup()
boss_group = SpriteGroup()
overlap_group = SpriteGroup()
running = True
state = "start_screen"
next_state = "game"
time = 0
black = pygame.transform.scale(load_image('fade_transition.png'), screen_size)
white = pygame.transform.scale(load_image('fade_transition2.png'), screen_size)
bgrnd = BackGround(load_image('bgrnd_space.png'), 50)
fade = FadeTransition(black, 256)
star_image = load_image("star_normal.png")
star_piece_image = load_image("star_piece.png")
instr_image = load_image("ttl_controls.png", -1)
laser_blaster_handle_image = load_image("laser_blaster_handle.png")
laser_blaster_image = load_image("laser_blaster_idle.png")
laser_blaster_anim_sheet = load_image("laser_blaster_anim_sheet.png")
boss_body = load_image("boss_back_part.png")
boss_enemie = load_image("boss_cockpit.png")
boss_enemie_inv = load_image("boss_cockpit_inv.png")
boss_engine1 = load_image("boss_engine1.png")
boss_engine1_inv = load_image("boss_engine1_inv.png")
boss_engine2 = load_image("boss_engine2.png")
boss_engine2_inv = load_image("boss_engine2_inv.png")
bgrnd_boss_frames = [load_image(f"boss_background_anim/bgrnd_space_boss{i}.png") for i in range(60)]
clock = pygame.time.Clock()
logo = None
start = None
player = None
health_bar = None
boss = None
# звуки
start_sound = pygame.mixer.Sound("data/snd_start.ogg")
hit_sound = pygame.mixer.Sound("data/snd_hit.ogg")
star_explode_sound = pygame.mixer.Sound("data/snd_star_explode.ogg")
die_sound = pygame.mixer.Sound("data/snd_die.ogg")
revive_sound = pygame.mixer.Sound("data/snd_revive.ogg")
you_won_sound = pygame.mixer.Sound("data/snd_you_won.ogg")
win_sound = pygame.mixer.Sound("data/snd_win.ogg")
del_sound = pygame.mixer.Sound("data/snd_delete_data.ogg")
laser_sound = pygame.mixer.Sound("data/snd_laser.ogg")
boss_hit_sound = pygame.mixer.Sound("data/snd_boss_hit.ogg")
boss_explode_sound = pygame.mixer.Sound("data/snd_boss_explode.ogg")
# контроль объектов в сцене
scene_objects = []
camera = Camera()
tborder = Border(-1, -1, screen_size[0] + 1, -1)
bborder = Border(-1, screen_size[1] + 1, screen_size[0] + 1, screen_size[1] + 1)
lborder = Border(-1, -1, -1, screen_size[1] + 1)
rborder = Border(screen_size[0] + 1, -1, screen_size[0] + 1, screen_size[1] + 1)
# информация о прогрессе игры
levels = 5
player_data_read = open("data/player_data.ini", mode="r")
data = [list(i.split("=")) for i in player_data_read.read().split("\n")]
data_dict = dict()
for i in data:
    data_dict[i[0]] = i[1]
player_data_read.close()


def make_level():
    generate_level = open(f'data/lvl_0{data_dict["lvl"]}.csv', mode="w")
    res_str = ["time\ttype\tx\ty\tspeed\trot_spd"]
    for i in range(35):
        v = random.randint(0, 7)
        if v == 0:
            res_str.append(
                f"{i * 1500}\tb_hole\t{random.randint(200, 824)}\t{random.randint(200, 568)}"
                f"\t{random.randint(30, 120)}")
        elif v in range(1, 3):
            res_str.append(f"{i * 1500}\tl_blast\t{random.choice((1174, -150))}\t{random.randint(100, 668)}")
        else:
            res_str.append(
                f"{i * 1500}\tstar\t{random.randint(100, 924)}\t-100\t{int((random.randint(115, 220) / 10) ** 2)}"
                f"\t{random.randint(1, 360)}")
    res_str.append(f"{38 * 1500}\twin")
    generate_level.write("\n".join(res_str))
    generate_level.close()


# инициализация и воспроизведение работы экрана запуска игры
def start_screen():
    global logo, start, scene_objects, running, state, next_state, time
    logo = Logo(load_image('ttl_logo.png'))
    start = PressZToStartText(load_image('ttl_start.png', 0))
    instr = Instructions()
    lvl = CurLevel()
    lvl_txt = CurLevelText()
    scene_objects = [logo, start, instr, lvl, lvl_txt]

    pygame.mixer.music.load('data/mus_start_screen.wav')
    pygame.mixer.music.play(-1)

    while running and state == "start_screen":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z and fade.fade == 0:
                    start.image.set_alpha(0)
                    instr.image.set_alpha(0)
                    lvl.image.set_alpha(0)
                    lvl_txt.image.set_alpha(0)
                    bgrnd.vel = 0
                    logo.stop = True
                    fade.fade = -1
                    pygame.mixer.music.stop()
                    pygame.mixer.Sound.play(start_sound)
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_DELETE and fade.fade == 0:
                    pygame.mixer.Sound.stop(del_sound)
                    pygame.mixer.Sound.play(del_sound)
                    data_dict["lvl"] = "1"
                    lvl.reset()
        time += 1000 / FPS
        bgrnd.update()
        sprite_group.update()
        overlap_group.update()
        if fade.loaded:
            start.image.set_alpha(255)
            instr.image.set_alpha(255)
            lvl.image.set_alpha(255)
            lvl_txt.image.set_alpha(255)
            fade.loaded = False
        sprite_group.draw(screen)
        overlap_group.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()
    fade.fade = 1
    bgrnd.vel = 50
    time = 0
    next_state = "game_over"
    for obj in scene_objects:
        obj.kill()
    scene_objects.clear()


# инициализация и воспроизведение работы игры
def game():
    global player, health_bar, scene_objects, boss, running, state, next_state, time, data_dict, levels, fade, bgrnd
    player = Player(load_image("player_ship_anim_sheet.png", -1), 4, 1,
                    screen_size[0] // 2, screen_size[1] // 2, player_group, 6, 400, 1200,
                    pygame.mask.from_surface(load_image("player_ship.png", -1)))
    health_bar = HealthBar(load_image("health_bar_anim_sheet.png"), 3, 2, 20, 20, player_group)
    scene_objects = [health_bar]
    auto_gen_level = True
    next_action_time = 0
    if int(data_dict["lvl"]) == levels:
        bgrnd.kill()
        bgrnd = BossBackGround(50, 30)
        boss = Boss()
        pygame.mixer.music.load('data/mus_boss_fight.wav')
        global tborder, bborder, rborder, lborder
        tborder.kill()
        rborder.kill()
        lborder.kill()
        tborder = Border(-1, 230, screen_size[0] + 1, 230)
        lborder = Border(30, -1, 30, screen_size[1] + 1)
        rborder = Border(screen_size[0] - 30, -1, screen_size[0] - 30, screen_size[1] + 1)
    else:
        auto_gen_level = False
        if data_dict["lvl"] == "4":
            make_level()
        try:
            with open(f'data/lvl_0{data_dict["lvl"]}.csv', encoding="utf8") as csvfile:
                reader = csv.DictReader(csvfile, delimiter='\t', quotechar='"')
                actions = list(reader)
        except pygame.error as message:
            print('Не удаётся загрузить:', f'data/lvl_0{data_dict["lvl"]}.csv')
            raise SystemExit(message)
        if int(data_dict["lvl"]) % 2 == 0:
            pygame.mixer.music.load('data/mus_meh_music.wav')
        else:
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
                if event.key == pygame.K_ESCAPE:
                    running = False
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
        if auto_gen_level:
            if next_action_time <= time:
                v = random.randint(0, 7)
                if v == 0:
                    BlackHole(random.randint(200, 824), random.randint(300, 568), random.randint(30, 120))
                elif v in range(1, 3):
                    LaserBlaster(random.choice((1174, -150)), random.randint(350, 668))
                else:
                    Star(random.randint(100, 924), -100, int((random.randint(115, 200) / 10) ** 2),
                         random.randint(1, 360))
                next_action_time += 1000
        else:
            performed = []
            for action in actions:
                if int(action["time"]) <= time:
                    if action["type"] == "star":
                        Star(int(action["x"]), int(action["y"]), int(action["speed"]), int(action["rot_spd"]))
                    elif action["type"] == "b_hole":
                        BlackHole(int(action["x"]), int(action["y"]), int(action["speed"]))
                    elif action["type"] == "l_blast":
                        LaserBlaster(int(action["x"]), int(action["y"]))
                    elif action["type"] == "win":
                        next_state = "win"
                        fade.fade = -1
                        fade.image = white
                        fade.image.set_alpha(0)
                    performed.append(action)
            for action in performed:
                actions.remove(action)
        bgrnd.update()
        sprite_group.update()
        boss_group.update()
        player_group.update()
        enemies_group.update()
        overlap_group.update()
        for obj in all_sprites:
            if obj.rect is not None:
                camera.apply(obj)
        screen.fill(pygame.Color("black"))
        sprite_group.draw(screen)
        boss_group.draw(screen)
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
    if state == "win":
        data_dict["lvl"] = str(int(data_dict["lvl"]) + 1)
    for obj in scene_objects:
        obj.kill()
    scene_objects.clear()


def game_over():
    global player, bgrnd, scene_objects, running, state, next_state, time, fade
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
                if event.key == pygame.K_ESCAPE:
                    running = False
        screen.fill(pygame.Color("Black"))
        time += 1000 / FPS
        sprite_group.update()
        overlap_group.update()
        sprite_group.draw(screen)
        overlap_group.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()
    time = 0
    fade.fade = 1
    broken_ship.kill()
    player.kill()
    bgrnd = BackGround(load_image('bgrnd_space.png'), 50)
    fade.spd = 256
    for obj in scene_objects:
        obj.kill()
    scene_objects.clear()


def game_won():
    global player, bgrnd, scene_objects, running, state, next_state, time, fade, data_dict, levels
    victory_screen = pygame.sprite.Sprite(sprite_group)
    if int(data_dict["lvl"]) <= levels:
        victory_screen.image = pygame.transform.scale(load_image("win_image.png", -1), screen_size)
        next_state = "game"
        pygame.mixer.Sound.play(win_sound)
    else:
        victory_screen.image = pygame.transform.scale(load_image("game_won.png", -1), screen_size)
        next_state = "quit"
        data_dict["lvl"] = str(int(data_dict["lvl"]) - 1)
        pygame.mixer.Sound.play(you_won_sound)
    victory_screen.rect = victory_screen.image.get_rect()
    victory_screen.rect.centerx = screen_size[0] // 2
    victory_screen.rect.centery = screen_size[1] // 2
    bgrnd.kill()
    fade.spd = 200
    fade.image = white
    fade.image.set_alpha(255)
    scene_objects = [victory_screen]
    fade.fade = 1
    player.kill()

    while running and state == "win":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z and fade.fade == 0:
                    if next_state != "quit":
                        fade.fade = -1
                        pygame.mixer.Sound.play(start_sound)
                if event.key == pygame.K_ESCAPE:
                    running = False
        screen.fill(pygame.Color("Black"))
        time += 1000 / FPS
        sprite_group.update()
        overlap_group.update()
        sprite_group.draw(screen)
        overlap_group.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()
    time = 0
    fade.fade = 1
    for obj in scene_objects:
        obj.kill()
    bgrnd = BackGround(load_image('bgrnd_space.png'), 50)
    fade.spd = 256
    for obj in scene_objects:
        obj.kill()
    scene_objects.clear()


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
    # сохранение всех изменённых данных
    player_data_write = open("data/player_data.ini", mode="w")
    res_str = []
    for k, v in data_dict.items():
        res_str.append(k + "=" + v)
    player_data_write.write("\n".join(res_str))
    player_data_write.close()
