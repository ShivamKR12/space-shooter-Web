import asyncio
import pygame 
from os.path import join
import sys
import os
from random import randint, uniform

# PyInstaller path setup for bundled assets
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

# general setup
pygame.init()
info = pygame.display.Info()
WINDOW_WIDTH = info.current_w if info.current_w > 0 else 1280
WINDOW_HEIGHT = info.current_h if info.current_h > 0 else 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Space Shooter')

# Set pygame window icon
pygame_icon = pygame.image.load(join('images', 'player.png'))
pygame.display.set_icon(pygame_icon)

# assets
star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
meteor_surf = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
explosion_frames = [pygame.image.load(join('images', 'explosion', f'{i}.png')).convert_alpha() for i in range(21)]

laser_sound = pygame.mixer.Sound(join('audio', 'laser.ogg'))
laser_sound.set_volume(0.5)
explosion_sound = pygame.mixer.Sound(join('audio', 'explosion.ogg'))
game_music = pygame.mixer.Sound(join('audio', 'game_music.ogg'))
game_music.set_volume(0.4)

class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player.png')).convert_alpha()
        self.rect = self.image.get_frect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.direction = pygame.Vector2()
        self.speed = 300

        # cooldown 
        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = 400

        # mask 
        self.mask = pygame.mask.from_surface(self.image)
    
    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = (int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])) or (int(keys[pygame.K_d]) - int(keys[pygame.K_a]))
        self.direction.y = (int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])) or (int(keys[pygame.K_s]) - int(keys[pygame.K_w]))
        self.direction = self.direction.normalize() if self.direction else self.direction 
        self.rect.center += self.direction * self.speed * dt

        recent_keys = pygame.key.get_just_pressed()
        if recent_keys[pygame.K_SPACE] and self.can_shoot:
            Laser(laser_surf, self.rect.midtop, (all_sprites, laser_sprites)) 
            self.can_shoot = False
            self.laser_shoot_time = pygame.time.get_ticks()
            laser_sound.play()
        
        self.laser_timer()

class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center = (randint(0, WINDOW_WIDTH),randint(0, WINDOW_HEIGHT)))
        
class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf 
        self.rect = self.image.get_frect(midbottom = pos)
    
    def update(self, dt):
        self.rect.centery -= 400 * dt
        if self.rect.bottom < 0:
            self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_surf = surf
        self.image = surf
        self.rect = self.image.get_frect(center = pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 3000
        self.direction = pygame.Vector2(uniform(-0.5, 0.5),1)
        self.speed = randint(400,500)
        self.rotation_speed = randint(40,80)
        self.rotation = 0
    
    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()
        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)
        self.rect = self.image.get_frect(center = self.rect.center)

class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(center = pos)
        explosion_sound.play()
    
    def update(self, dt):
        self.frame_index += 20 * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.kill()

all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
player = None
game_over = False
start_ticks = 0

def display_score():
    if not game_over:
        score = (pygame.time.get_ticks() - start_ticks) // 100
    else:
        score = final_score
    text_surf = font.render(str(score), True, (240,240,240))
    text_rect = text_surf.get_frect(midbottom = (WINDOW_WIDTH / 2, WINDOW_HEIGHT - 50))
    display_surface.blit(text_surf, text_rect)
    pygame.draw.rect(display_surface, (240,240,240), text_rect.inflate(20,10).move(0,-8), 5, 10)

def reset_game():
    global player, game_over, start_ticks
    all_sprites.empty()
    meteor_sprites.empty()
    laser_sprites.empty()
    for _ in range(20):
        Star(all_sprites, star_surf)
    player = Player(all_sprites)
    game_over = False
    start_ticks = pygame.time.get_ticks()

async def main():
    global game_over, final_score
    clock = pygame.time.Clock()
    game_music.play(loops=-1)
    
    meteor_event = pygame.event.custom_type()
    pygame.time.set_timer(meteor_event, 200)

    reset_game()
    final_score = 0
    running = True

    while running:
        dt = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            if not game_over and event.type == meteor_event:
                x, y = randint(0, WINDOW_WIDTH), randint(-200, -100)
                Meteor(meteor_surf, (x, y), (all_sprites, meteor_sprites))
            if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                reset_game()

        if not game_over:
            all_sprites.update(dt)
            if pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask):
                game_over = True
                final_score = (pygame.time.get_ticks() - start_ticks) // 100
            for laser in laser_sprites:
                if pygame.sprite.spritecollide(laser, meteor_sprites, True):
                    laser.kill()
                    AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)

        display_surface.fill('#3a2e3f')
        all_sprites.draw(display_surface)
        display_score()

        if game_over:
            over_surf = font.render('Game Over - Press SPACE to Play Again', True, (240, 240, 240))
            over_rect = over_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
            display_surface.blit(over_surf, over_rect)

        pygame.display.update()
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    asyncio.run(main())
