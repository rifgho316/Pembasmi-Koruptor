import pygame
import math
import sys
import random
import os

# --- INISIALISASI PYGAME & AUDIO ---
pygame.init()
pygame.font.init()
pygame.mixer.init() 

# Memuat file suara (jika file tidak ada, game akan tetap jalan tanpa error)
try:
    if os.path.exists('shoot.wav'):
        shoot_sfx = pygame.mixer.Sound('shoot.wav')
    else: shoot_sfx = None
    
    if os.path.exists('hurt.wav'):
        hurt_sfx = pygame.mixer.Sound('hurt.wav')
    else: hurt_sfx = None
except:
    shoot_sfx = None
    hurt_sfx = None

WIDTH = 1280
HEIGHT = 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retro FPS - The Glitched Rat")
clock = pygame.time.Clock()

pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

# --- PENGATURAN LAYAR & HUD ---
HUD_HEIGHT = 160
VIEW_HEIGHT = HEIGHT - HUD_HEIGHT

# --- 1. PETA GAME ---
world_map = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,0,0,1,0,1,1,0,0,1,1,0,1],
    [1,0,0,1,0,0,0,0,0,0,0,0,0,1,0,1],
    [1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,1,0,1,1,1,0,0,1,0,0,0,1],
    [1,0,1,0,1,0,0,0,1,0,0,1,1,1,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
]
TILE_SIZE = 64
MAP_WIDTH = len(world_map[0]) * TILE_SIZE
MAP_HEIGHT = len(world_map) * TILE_SIZE

# --- 2. PEMAIN ---
player_x = 96.0 
player_y = 96.0
player_angle = 0.0
FOV = math.pi / 3  
SPEED = 4.0        
MOUSE_SENSITIVITY = 0.002 

player_health = 100
pain_timer = 0
attack_cooldown = 0
game_over = False

# --- 3. STATUS & ENTITAS ---
has_weapon = False       
ammo_count = 50

# Daftar Entitas (Item & Tikus Raksasa)
entities = [
    {'id': 'gun_pickup', 'type': 'item', 'x': 350.0, 'y': 350.0, 'active': True},
    # Tikus Normal (Mengejar)
    {'id': 'rat_1', 'type': 'monster', 'x': 600.0, 'y': 350.0, 'active': True, 'hp': 4, 'speed': 2.0},
    {'id': 'rat_2', 'type': 'monster', 'x': 800.0, 'y': 150.0, 'active': True, 'hp': 4, 'speed': 2.0},
    {'id': 'rat_3', 'type': 'monster', 'x': 700.0, 'y': 250.0, 'active': True, 'hp': 4, 'speed': 2.0},
    # Tikus Glitch (Terjebak di pinggir tembok koordinat [2][2])
    {'id': 'rat_stuck', 'type': 'monster', 'x': 160.0, 'y': 128.0, 'active': True, 'hp': 4, 'speed': 0.0}
]

bullets = []
recoil_timer = 0
muzzle_flash_timer = 0

# --- FONT ---
font_huge = pygame.font.Font(None, 90)
font_large = pygame.font.Font(None, 40)
font_small = pygame.font.Font(None, 28)

z_buffer = [0] * WIDTH

def cast_rays():
    pygame.draw.rect(screen, (30, 30, 30), (0, 0, WIDTH, VIEW_HEIGHT // 2)) 
    pygame.draw.rect(screen, (50, 40, 30), (0, VIEW_HEIGHT // 2, WIDTH, VIEW_HEIGHT // 2)) 

    for x in range(0, WIDTH, 4):
        ray_angle = (player_angle - FOV / 2.0) + (x / WIDTH) * FOV
        distance_to_wall = 0
        hit_wall = False
        eye_x = math.cos(ray_angle)
        eye_y = math.sin(ray_angle)
        
        while not hit_wall and distance_to_wall < 1200:
            distance_to_wall += 1
            test_x = int((player_x + eye_x * distance_to_wall) / TILE_SIZE)
            test_y = int((player_y + eye_y * distance_to_wall) / TILE_SIZE)
            
            if test_x < 0 or test_x >= len(world_map[0]) or test_y < 0 or test_y >= len(world_map):
                hit_wall = True
                distance_to_wall = 1200
            elif world_map[test_y][test_x] == 1:
                hit_wall = True

        corrected_distance = distance_to_wall * math.cos(ray_angle - player_angle)
        if corrected_distance <= 0: corrected_distance = 0.1 
        
        for w in range(4):
            if x + w < WIDTH:
                z_buffer[x + w] = corrected_distance
        
        ceiling = (VIEW_HEIGHT / 2.0) - (VIEW_HEIGHT / corrected_distance) * 30
        floor = VIEW_HEIGHT - ceiling
        wall_height = floor - ceiling
        
        shade = max(0, 255 - int(corrected_distance * 0.3))
        color = (int(shade * 0.5), int(shade * 0.6), int(shade * 0.5)) 
        pygame.draw.rect(screen, color, (x, ceiling, 4, wall_height))

def render_sprites():
    render_list = []
    
    for ent in entities:
        if ent['active']:
            dist = math.hypot(ent['x'] - player_x, ent['y'] - player_y)
            render_list.append({'obj': ent, 'dist': dist, 'cat': ent['type']})
            
    for b in bullets:
        if b['active']:
            dist = math.hypot(b['x'] - player_x, b['y'] - player_y)
            render_list.append({'obj': b, 'dist': dist, 'cat': 'bullet'})

    render_list.sort(key=lambda item: item['dist'], reverse=True)

    for item in render_list:
        obj = item['obj']
        dist = item['dist']
        cat = item['cat']
        
        if dist < 10: continue 
        
        dx = obj['x'] - player_x
        dy = obj['y'] - player_y
        
        item_angle = math.atan2(dy, dx)
        diff_angle = item_angle - player_angle
        
        while diff_angle > math.pi: diff_angle -= 2 * math.pi
        while diff_angle < -math.pi: diff_angle += 2 * math.pi
        
        if abs(diff_angle) < FOV:
            screen_x = (WIDTH / 2) + (diff_angle / (FOV / 2)) * (WIDTH / 2)
            
            if 0 <= int(screen_x) < WIDTH:
                # Z-Buffer Check (Jika tertutup tembok, tidak digambar. Ini yang membuat tikus terlihat terpotong)
                if z_buffer[int(screen_x)] < dist:
                    continue

            size = (VIEW_HEIGHT / dist) * 40
            item_y = (VIEW_HEIGHT / 2) + (VIEW_HEIGHT / dist) * 10
            
            if cat == 'item':
                rect = pygame.Rect(screen_x - size / 4, item_y, size / 2, size / 2)
                pygame.draw.rect(screen, (255, 215, 0), rect) 
                
            elif cat == 'monster':
                body_y = item_y - size/3
                pygame.draw.circle(screen, (100, 100, 100), (int(screen_x - size/3), int(body_y - size/4)), int(size/4))
                pygame.draw.circle(screen, (100, 100, 100), (int(screen_x + size/3), int(body_y - size/4)), int(size/4))
                pygame.draw.circle(screen, (140, 140, 140), (int(screen_x), int(body_y)), int(size/2))
                pygame.draw.circle(screen, (255, 0, 0), (int(screen_x - size/5), int(body_y - size/6)), int(size/8))
                pygame.draw.circle(screen, (255, 0, 0), (int(screen_x + size/5), int(body_y - size/6)), int(size/8))
                pygame.draw.polygon(screen, (255, 150, 150), [
                    (screen_x, body_y + size/4), 
                    (screen_x - size/6, body_y + size/1.5), 
                    (screen_x + size/6, body_y + size/1.5)
                ])
                
            elif cat == 'bullet':
                b_size = max(2, int(size / 6))
                pygame.draw.circle(screen, (255, 100, 0), (int(screen_x), int(item_y - size/4)), b_size + 2) 
                pygame.draw.circle(screen, (255, 255, 0), (int(screen_x), int(item_y - size/4)), b_size)     

def update_entities_and_collision():
    global player_health, pain_timer, attack_cooldown
    
    for b in bullets:
        if not b['active']: continue
        b['x'] += math.cos(b['angle']) * b['speed']
        b['y'] += math.sin(b['angle']) * b['speed']
        
        map_x = int(b['x'] / TILE_SIZE)
        map_y = int(b['y'] / TILE_SIZE)
        if map_x < 0 or map_x >= len(world_map[0]) or map_y < 0 or map_y >= len(world_map):
            b['active'] = False
            continue
        if world_map[map_y][map_x] == 1:
            b['active'] = False
            continue
            
        for ent in entities:
            if ent['type'] == 'monster' and ent['active']:
                dist = math.hypot(b['x'] - ent['x'], b['y'] - ent['y'])
                if dist < 40: 
                    ent['hp'] -= 1
                    b['active'] = False 
                    if ent['hp'] <= 0:
                        ent['active'] = False 
                    break

    for ent in entities:
        if ent['type'] == 'monster' and ent['active']:
            dist = math.hypot(player_x - ent['x'], player_y - ent['y'])
            
            # Jika speed > 0, tikus bisa jalan mengejar
            if 50 < dist < 600 and ent['speed'] > 0:
                dx = (player_x - ent['x']) / dist
                dy = (player_y - ent['y']) / dist
                
                new_ent_x = ent['x'] + dx * ent['speed']
                new_ent_y = ent['y'] + dy * ent['speed']
                
                if world_map[int(ent['y'] / TILE_SIZE)][int(new_ent_x / TILE_SIZE)] == 0:
                    ent['x'] = new_ent_x
                if world_map[int(new_ent_y / TILE_SIZE)][int(ent['x'] / TILE_SIZE)] == 0:
                    ent['y'] = new_ent_y
                    
            # Logika terkena Serangan dan Suara Sakit
            elif dist <= 50:
                if attack_cooldown == 0:
                    player_health -= 15
                    pain_timer = 20
                    attack_cooldown = 60
                    
                    # Putar suara kesakitan jika file ada
                    if hurt_sfx:
                        hurt_sfx.play()
                        
                    if player_health < 0: player_health = 0

def draw_player_ui():
    global recoil_timer, muzzle_flash_timer
    
    if not has_weapon:
        pygame.draw.rect(screen, (224, 172, 105), (WIDTH//2 - 250, VIEW_HEIGHT - 120, 80, 120), border_radius=20) 
        pygame.draw.rect(screen, (224, 172, 105), (WIDTH//2 + 170, VIEW_HEIGHT - 120, 80, 120), border_radius=20) 
    else:
        recoil_offset = 0
        if recoil_timer > 0:
            recoil_offset = recoil_timer * 3
            recoil_timer -= 1
            
        gun_x = WIDTH // 2
        gun_y = VIEW_HEIGHT + recoil_offset
        
        barrel_poly = [
            (gun_x - 40, gun_y),          
            (gun_x - 20, gun_y - 200),    
            (gun_x + 20, gun_y - 200),    
            (gun_x + 40, gun_y)           
        ]
        pygame.draw.polygon(screen, (50, 50, 50), barrel_poly)
        
        core_poly = [
            (gun_x - 10, gun_y - 50),
            (gun_x - 5, gun_y - 150),
            (gun_x + 5, gun_y - 150),
            (gun_x + 10, gun_y - 50)
        ]
        pygame.draw.polygon(screen, (0, 200, 255), core_poly)
        
        pygame.draw.rect(screen, (224, 172, 105), (gun_x - 45, gun_y - 80, 90, 80), border_radius=15) 

        if muzzle_flash_timer > 0:
            flash_y = gun_y - 220
            pygame.draw.circle(screen, (255, 255, 0), (gun_x, flash_y), 30 + random.randint(-5, 5))
            pygame.draw.circle(screen, (255, 100, 0), (gun_x, flash_y), 15)
            muzzle_flash_timer -= 1

def draw_doom_hud():
    global pain_timer
    
    pygame.draw.rect(screen, (50, 50, 50), (0, VIEW_HEIGHT, WIDTH, HUD_HEIGHT))
    pygame.draw.rect(screen, (30, 30, 30), (0, VIEW_HEIGHT, WIDTH, 5))
    pygame.draw.rect(screen, (30, 30, 30), (0, HEIGHT - 5, WIDTH, 5))

    red_txt = (255, 50, 50)
    grey_txt = (180, 180, 180)

    screen.blit(font_huge.render(str(ammo_count), True, red_txt), (100, VIEW_HEIGHT + 35))
    screen.blit(font_large.render("AMMO", True, grey_txt), (90, VIEW_HEIGHT + 110))

    screen.blit(font_huge.render(f"{player_health}%", True, red_txt), (330, VIEW_HEIGHT + 35))
    screen.blit(font_large.render("HEALTH", True, grey_txt), (330, VIEW_HEIGHT + 110))

    face_rect = (WIDTH//2 - 60, VIEW_HEIGHT + 15, 120, 130)
    pygame.draw.rect(screen, (20, 20, 20), face_rect) 
    pygame.draw.rect(screen, (100, 100, 100), face_rect, 4) 
    
    if pain_timer > 0:
        pygame.draw.rect(screen, (200, 50, 50), face_rect)
        pygame.draw.rect(screen, (100, 100, 100), face_rect, 4) 
        pygame.draw.rect(screen, (255, 120, 120), (WIDTH//2 - 45, VIEW_HEIGHT + 30, 90, 100)) 
        pygame.draw.rect(screen, (0, 0, 0), (WIDTH//2 - 30, VIEW_HEIGHT + 55, 20, 5)) 
        pygame.draw.rect(screen, (0, 0, 0), (WIDTH//2 + 10, VIEW_HEIGHT + 55, 20, 5)) 
        pygame.draw.rect(screen, (50, 0, 0), (WIDTH//2 - 20, VIEW_HEIGHT + 85, 40, 25)) 
        pygame.draw.rect(screen, (255, 255, 255), (WIDTH//2 - 15, VIEW_HEIGHT + 88, 30, 5)) 
        pain_timer -= 1
    else:
        pygame.draw.rect(screen, (224, 172, 105), (WIDTH//2 - 45, VIEW_HEIGHT + 30, 90, 100))
        pygame.draw.rect(screen, (0, 0, 0), (WIDTH//2 - 25, VIEW_HEIGHT + 55, 15, 8)) 
        pygame.draw.rect(screen, (0, 0, 0), (WIDTH//2 + 10, VIEW_HEIGHT + 55, 15, 8)) 
        pygame.draw.rect(screen, (0, 0, 0), (WIDTH//2 - 20, VIEW_HEIGHT + 95, 40, 5)) 
        pygame.draw.rect(screen, (0, 0, 0), (WIDTH//2 - 20, VIEW_HEIGHT + 90, 5, 10)) 
        pygame.draw.rect(screen, (0, 0, 0), (WIDTH//2 + 15, VIEW_HEIGHT + 90, 5, 10)) 

    screen.blit(font_huge.render("0%", True, red_txt), (WIDTH//2 + 170, VIEW_HEIGHT + 35))
    screen.blit(font_large.render("ARMOR", True, grey_txt), (WIDTH//2 + 150, VIEW_HEIGHT + 110))

    ammo_types = ["BULL", "SHEL", "RCKT", "CELL"]
    ammo_values = [str(ammo_count), " 0", " 0", " 0"]
    for i in range(4):
        screen.blit(font_small.render(ammo_types[i], True, grey_txt), (WIDTH - 250, VIEW_HEIGHT + 25 + i * 30))
        screen.blit(font_small.render(ammo_values[i], True, red_txt), (WIDTH - 150, VIEW_HEIGHT + 25 + i * 30))

# --- 4. GAME LOOP ---
running = True
while running:
    if player_health <= 0:
        game_over = True

    if attack_cooldown > 0:
        attack_cooldown -= 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            if event.button == 1 and has_weapon and ammo_count > 0 and recoil_timer == 0:
                ammo_count -= 1
                recoil_timer = 15       
                muzzle_flash_timer = 3  
                
                if shoot_sfx:
                    shoot_sfx.play()
                
                bullets.append({
                    'x': player_x,
                    'y': player_y,
                    'angle': player_angle,
                    'speed': 25.0, 
                    'active': True
                })

    if not game_over:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]: running = False

        mouse_dx, mouse_dy = pygame.mouse.get_rel()
        player_angle += mouse_dx * MOUSE_SENSITIVITY

        move_x = move_y = 0
        if keys[pygame.K_w]:
            move_x += math.cos(player_angle) * SPEED
            move_y += math.sin(player_angle) * SPEED
        if keys[pygame.K_s]:
            move_x -= math.cos(player_angle) * SPEED
            move_y -= math.sin(player_angle) * SPEED
        if keys[pygame.K_a]:
            move_x += math.cos(player_angle - math.pi / 2) * SPEED
            move_y += math.sin(player_angle - math.pi / 2) * SPEED
        if keys[pygame.K_d]:
            move_x += math.cos(player_angle + math.pi / 2) * SPEED
            move_y += math.sin(player_angle + math.pi / 2) * SPEED
            
        new_x = player_x + move_x
        new_y = player_y + move_y
        if 0 <= new_x < MAP_WIDTH and 0 <= player_y < MAP_HEIGHT:
            if world_map[int(player_y / TILE_SIZE)][int(new_x / TILE_SIZE)] == 0:
                player_x = new_x
        if 0 <= player_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
            if world_map[int(new_y / TILE_SIZE)][int(player_x / TILE_SIZE)] == 0:
                player_y = new_y

        for ent in entities:
            if ent['type'] == 'item' and ent['active']:
                dist = math.hypot(player_x - ent['x'], player_y - ent['y'])
                if dist < 50:
                    ent['active'] = False
                    has_weapon = True

        update_entities_and_collision()

    screen.fill((0, 0, 0)) 
    
    cast_rays()           
    render_sprites()      
    draw_player_ui()      
    draw_doom_hud()       
    
    if game_over:
        s = pygame.Surface((WIDTH, VIEW_HEIGHT)) 
        s.set_alpha(180) 
        s.fill((255, 0, 0)) 
        screen.blit(s, (0,0))
        screen.blit(font_huge.render("YOU DIED", True, (255, 255, 255)), (WIDTH//2 - 150, VIEW_HEIGHT//2 - 45))

    pygame.draw.circle(screen, (0, 255, 0), (WIDTH // 2, VIEW_HEIGHT // 2), 3)
    
    pygame.display.flip()  
    clock.tick(60)         

pygame.mouse.set_visible(True)
pygame.event.set_grab(False)
pygame.quit()
sys.exit()