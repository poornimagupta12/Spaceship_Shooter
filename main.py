import pygame 
from os.path import join, exists
from random import randint, uniform

pygame.init()
pygame.mixer.init()

WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
fullscreen = False

# Safe sound loading
def load_sound(path):
    if exists(path):
        try:
            return pygame.mixer.Sound(path)
        except pygame.error as e:
            print(f"Failed to load sound {path}: {e}")
            return None
    else:
        print(f"Sound file not found: {path}")
        return None

class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player.png')).convert_alpha()
        self.rect = self.image.get_rect(midbottom = (WINDOW_WIDTH / 2, WINDOW_HEIGHT - 30))
        self.direction = pygame.Vector2()
        self.speed = 300

        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = 400

        self.mask = pygame.mask.from_surface(self.image)

        self.lives = 3
        self.is_invincible = False
        self.invincibility_time = 0
        self.invincibility_duration = 2000

    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()
        self.rect.centerx += self.direction.x * self.speed * dt

        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WINDOW_WIDTH)

        if keys[pygame.K_SPACE] and self.can_shoot:
            Laser(laser_surf, self.rect.midtop, (all_sprites, laser_sprites)) 
            self.can_shoot = False
            self.laser_shoot_time = pygame.time.get_ticks()
            if laser_sound:
                laser_sound.play()

        self.laser_timer()

        if self.is_invincible:
            if pygame.time.get_ticks() - self.invincibility_time > self.invincibility_duration:
                self.is_invincible = False

class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(center = (randint(0, WINDOW_WIDTH),randint(0, WINDOW_HEIGHT)))

class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf 
        self.rect = self.image.get_rect(midbottom = pos)

    def update(self, dt):
        self.rect.centery -= 400 * dt
        if self.rect.bottom < 0:
            self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_surf = surf
        self.image = surf
        self.rect = self.image.get_rect(center = pos)
        self.direction = pygame.Vector2(uniform(-0.1, 0.1), 1)
        self.speed = randint(160, 200)
        self.rotation_speed = randint(40, 80)
        self.rotation = 0
        self.missed = False

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)
        self.rect = self.image.get_rect(center = self.rect.center)
        if self.rect.top > WINDOW_HEIGHT:
            self.missed = True
            self.kill()

class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center = pos)
        if explosion_sound:
            explosion_sound.play()

    def update(self, dt):
        self.frame_index += 20 * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.kill()

def collisions():
    global game_state, final_score

    if not player.is_invincible:
        collision_sprites = pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask)
        if collision_sprites:
            player.lives -= 1
            player.is_invincible = True
            player.invincibility_time = pygame.time.get_ticks()
            if player.lives <= 0:
                game_state = 'game_over'
                pygame.mixer.music.stop()

    for laser in laser_sprites:
        collided_sprites = pygame.sprite.spritecollide(laser, meteor_sprites, True)
        if collided_sprites:
            laser.kill()
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)
            final_score += len(collided_sprites) * 10

def display_lives():
    heart_size = 40
    for i in range(player.lives):
        heart_img = pygame.transform.scale(heart_surf, (heart_size, heart_size))
        heart_rect = heart_img.get_rect(topleft=(20 + i * (heart_size + 10), 20))
        display_surface.blit(heart_img, heart_rect)

def display_score():
    score_surf = font.render(f'Score: {final_score}', True, (255, 255, 255))
    score_rect = score_surf.get_rect(topright=(WINDOW_WIDTH - 20, 20))
    display_surface.blit(score_surf, score_rect)

def draw_start_screen():
    display_surface.fill('#3a2e3f')
    title_surf = font.render('Press SPACE to Start', True, (255, 255, 255))
    title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
    display_surface.blit(title_surf, title_rect)
    pygame.display.update()

def draw_game_over():
    display_surface.fill('#1e1e1e')
    over_surf = font.render('Game Over', True, (255, 60, 60))
    over_rect = over_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
    display_surface.blit(over_surf, over_rect)

    score_surf = font.render(f'Score: {final_score}', True, (255, 255, 255))
    score_rect = score_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
    display_surface.blit(score_surf, score_rect)

    restart_surf = font.render('Press R to Restart or Q to Quit', True, (255, 255, 255))
    restart_rect = restart_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))
    display_surface.blit(restart_surf, restart_rect)
    pygame.display.update()

def draw_pause_screen():
    pause_surf = font.render('Paused - Press P to Resume', True, (255, 255, 255))
    pause_rect = pause_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
    display_surface.blit(pause_surf, pause_rect)
    pygame.display.update()

pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
fullscreen = False
flags = pygame.RESIZABLE

display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
pygame.display.set_caption('Space shooter')
clock = pygame.time.Clock()

star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
meteor_surf = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
heart_surf = pygame.image.load(join('images', 'heart.png')).convert_alpha()
font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
explosion_frames = [pygame.image.load(join('images', 'explosion', f'{i}.png')).convert_alpha() for i in range(21)]

laser_sound = load_sound(join('audio', 'laser.wav'))
explosion_sound = load_sound(join('audio', 'explosion.wav'))
game_music_path = join('audio', 'game_music.wav')

all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
for i in range(20):
    Star(all_sprites, star_surf) 
player = Player(all_sprites)

meteor_event = pygame.event.custom_type()
initial_spawn_interval = 1000  # Start slower
pygame.time.set_timer(meteor_event, initial_spawn_interval)
last_meteor_time = pygame.time.get_ticks()
spawn_interval = initial_spawn_interval
meteor_count = 0

level_up_interval = 5000
last_level_up = pygame.time.get_ticks()

missed_meteors = 0
final_score = 0
game_state = 'start'
running = True

while running:
    dt = clock.tick() / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                fullscreen = not fullscreen
                if fullscreen:
                    display_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    WINDOW_WIDTH, WINDOW_HEIGHT = display_surface.get_size()
                else:
                    WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
                    display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
            if event.key == pygame.K_p and game_state == 'playing':
                game_state = 'paused'
            elif event.key == pygame.K_p and game_state == 'paused':
                game_state = 'playing'

    if game_state == 'start':
        draw_start_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.lives = 3
                    all_sprites.empty()
                    laser_sprites.empty()
                    meteor_sprites.empty()
                    for i in range(20):
                        Star(all_sprites, star_surf)
                    player = Player(all_sprites)
                    meteor_count = 0
                    missed_meteors = 0
                    pygame.time.set_timer(meteor_event, initial_spawn_interval)
                    last_level_up = pygame.time.get_ticks()
                    spawn_interval = initial_spawn_interval
                    final_score = 0
                    if exists(game_music_path):
                        pygame.mixer.music.load(game_music_path)
                        pygame.mixer.music.play(-1)
                    else:
                        print(f"Game music not found: {game_music_path}")
                    game_state = 'playing'
        continue

    elif game_state == 'game_over':
        draw_game_over()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_state = 'start'
                elif event.key == pygame.K_q:
                    running = False
        continue

    elif game_state == 'paused':
        draw_pause_screen()
        continue

    if event.type == meteor_event and game_state == 'playing':
        if len(meteor_sprites) < 15:
            x, y = randint(50, WINDOW_WIDTH - 50), randint(-150, -50)
            Meteor(meteor_surf, (x, y), (all_sprites, meteor_sprites))
            meteor_count += 1

    current_time = pygame.time.get_ticks()
    if current_time - last_level_up > level_up_interval:
        last_level_up = current_time
        spawn_interval = max(200, spawn_interval - 100)
        pygame.time.set_timer(meteor_event, spawn_interval)

    if game_state == 'playing':
        all_sprites.update(dt)

        for meteor in meteor_sprites:
            if meteor.missed:
                missed_meteors += 1
                meteor.missed = False
                if not player.is_invincible:
                    player.lives -= 1
                    player.is_invincible = True
                    player.invincibility_time = pygame.time.get_ticks()
                    if player.lives <= 0:
                        game_state = 'game_over'
                        pygame.mixer.music.stop()

        collisions()

        display_surface.fill('#3a2e3f')
        display_lives()
        display_score()
        all_sprites.draw(display_surface)
        pygame.display.update()

pygame.quit()
