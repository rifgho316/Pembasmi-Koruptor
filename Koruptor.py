import pygame
import math
import sys
import random
import os

pygame.init()
pygame.font.init()

WIDTH = 1280
HEIGHT = 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("FPS Retro - Sprite Kustom & Emoji Dinamis")
clock = pygame.time.Clock()

pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

HUD_HEIGHT = 160
VIEW_HEIGHT = HEIGHT - HUD_HEIGHT
view_surface = pygame.Surface((WIDTH, VIEW_HEIGHT))

shoot_sfx = None
hurt_sfx = None
rat_sfx = None
boss_sfx = None

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

player_x = 96.0 
player_y = 96.0
player_angle = 0.0
FOV = math.pi / 3  
SPEED = 4.0        
MOUSE_SENSITIVITY = 0.002 

player_health = 100
player_armor = 0    
pain_timer = 0
attack_cooldown = 0
game_over = False

kill_count = 0 
boss_spawn_counter = 0 

has_weapon = False       
max_mag = 12
current_mag = 12
reserve_ammo = 24
reload_timer = 0
RELOAD_TIME = 60 

MAX_DEPTH = 450.0 
spawn_timer = 0
rat_sound_timer = 0 
boss_sound_timer = 0

entities = [
    {'id': 'gun_pickup', 'type': 'item', 'x': 350.0, 'y': 350.0, 'active': True},
    {'id': 'mon_1', 'type': 'monster', 'x': 400.0, 'y': 200.0, 'active': True, 'hp': 2, 'speed': 1.6, 'offset': random.random()}
]

bullets = []
recoil_timer = 0
muzzle_flash_timer = 0

font_huge = pygame.font.Font(None, 90)
font_large = pygame.font.Font(None, 40)
font_small = pygame.font.Font(None, 28)
z_buffer = [0] * WIDTH

def apply_fog(color, intensity):
    return (int(color[0] * intensity), int(color[1] * intensity), int(color[2] * intensity))

def cast_rays():
    pygame.draw.rect(view_surface, (5, 5, 5), (0, 0, WIDTH, VIEW_HEIGHT // 2)) 
    pygame.draw.rect(view_surface, (10, 10, 10), (0, VIEW_HEIGHT // 2, WIDTH, VIEW_HEIGHT // 2)) 

    for x in range(0, WIDTH, 4):
        ray_angle = (player_angle - FOV / 2.0) + (x / WIDTH) * FOV
        distance_to_wall = 0
        hit_wall = False
        eye_x = math.cos(ray_angle)
        eye_y = math.sin(ray_angle)
        
        while not hit_wall and distance_to_wall < MAX_DEPTH:
            distance_to_wall += 1
            test_x = int((player_x + eye_x * distance_to_wall) / TILE_SIZE)
            test_y = int((player_y + eye_y * distance_to_wall) / TILE_SIZE)
            
            if test_x < 0 or test_x >= len(world_map[0]) or test_y < 0 or test_y >= len(world_map):
                hit_wall = True
                distance_to_wall = MAX_DEPTH
            elif world_map[test_y][test_x] == 1:
                hit_wall = True

        corrected_distance = distance_to_wall * math.cos(ray_angle - player_angle)
        if corrected_distance <= 0: corrected_distance = 0.1 
        for w in range(4):
            if x + w < WIDTH: z_buffer[x + w] = corrected_distance
        
        ceiling = (VIEW_HEIGHT / 2.0) - (VIEW_HEIGHT / corrected_distance) * 30
        floor = VIEW_HEIGHT - ceiling
        wall_height = floor - ceiling
        
        if distance_to_wall >= MAX_DEPTH:
            color = (0, 0, 0) 
        else:
            intensity = max(0, 1.0 - (corrected_distance / MAX_DEPTH))
            color = (int(50 * intensity), int(60 * intensity), int(50 * intensity)) 
            
        pygame.draw.rect(view_surface, color, (x, ceiling, 4, wall_height))

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
        
        if dist > MAX_DEPTH or dist < 10: continue 
            
        intensity = max(0, 1.0 - (dist / MAX_DEPTH))
        dx = obj['x'] - player_x
        dy = obj['y'] - player_y
        item_angle = math.atan2(dy, dx)
        diff_angle = item_angle - player_angle
        
        while diff_angle > math.pi: diff_angle -= 2 * math.pi
        while diff_angle < -math.pi: diff_angle += 2 * math.pi
        
        if abs(diff_angle) < FOV:
            screen_x = (WIDTH / 2) + (diff_angle / (FOV / 2)) * (WIDTH / 2)
            
            if 0 <= int(screen_x) < WIDTH:
                if z_buffer[int(screen_x)] < dist: continue

            base_size = (VIEW_HEIGHT / dist) * 40
            size = base_size * 1.5 if cat == 'boss' else base_size
            item_y = (VIEW_HEIGHT / 2) + (VIEW_HEIGHT / dist) * 10
            hover = math.sin(pygame.time.get_ticks() * 0.005) * 5
            rect = pygame.Rect(screen_x - size / 4, item_y + hover, size / 2, size / 2)
            
            if cat == 'item': 
                pygame.draw.rect(view_surface, apply_fog((255, 215, 0), intensity), rect) 
            elif cat == 'ammo': 
                box_color = apply_fog((60, 70, 50), intensity)
                stripe_color = apply_fog((200, 30, 30), intensity)
                bullet_tip = apply_fog((255, 215, 0), intensity)
                
                pygame.draw.rect(view_surface, box_color, rect)
                pygame.draw.rect(view_surface, stripe_color, (rect.x, rect.y + size*0.2, rect.width, size*0.15))
                for i in range(3):
                    pygame.draw.rect(view_surface, bullet_tip, (rect.x + size*0.08 + i*size*0.15, rect.y - size*0.1, size*0.08, size*0.1))

            elif cat == 'armor': 
                shield_blue = apply_fog((30, 100, 200), intensity)
                shield_border = apply_fog((180, 180, 180), intensity)
                
                shield_poly = [
                    (screen_x - size*0.25, item_y + hover - size*0.1), 
                    (screen_x + size*0.25, item_y + hover - size*0.1), 
                    (screen_x + size*0.25, item_y + hover + size*0.2), 
                    (screen_x, item_y + hover + size*0.4),             
                    (screen_x - size*0.25, item_y + hover + size*0.2)  
                ]
                pygame.draw.polygon(view_surface, shield_blue, shield_poly)
                pygame.draw.polygon(view_surface, shield_border, shield_poly, max(2, int(size*0.04)))
                pygame.draw.line(view_surface, shield_border, (screen_x, item_y + hover - size*0.1), (screen_x, item_y + hover + size*0.4), max(1, int(size*0.04)))

            elif cat == 'health': 
                med_white = apply_fog((220, 220, 220), intensity)
                med_red = apply_fog((200, 30, 30), intensity)
                pygame.draw.rect(view_surface, med_white, rect)
                
                c_w = size * 0.15
                c_h = size * 0.35
                pygame.draw.rect(view_surface, med_red, (screen_x - c_w/2, item_y + hover + size/4 - c_h/2, c_w, c_h))
                pygame.draw.rect(view_surface, med_red, (screen_x - c_h/2, item_y + hover + size/4 - c_w/2, c_h, c_w))
                
            elif cat == 'monster':
                breathe = math.sin(pygame.time.get_ticks() * 0.01 + obj['offset'] * 10) * (size/15)
                body_y = item_y - size/3 + breathe
                head_y = body_y - size*0.2
                
                b_dark = apply_fog((10, 10, 10), intensity)
                b_light = apply_fog((230, 230, 230), intensity)
                b_gray = apply_fog((100, 100, 100), intensity)
                
                pygame.draw.polygon(view_surface, b_dark, [(screen_x - size*0.4, body_y + size*0.6), (screen_x + size*0.4, body_y + size*0.6), (screen_x + size*0.25, body_y), (screen_x - size*0.25, body_y)])
                pygame.draw.polygon(view_surface, b_gray, [(screen_x, body_y + size*0.45), (screen_x - size*0.2, body_y + size*0.1), (screen_x - size*0.1, body_y)])
                pygame.draw.polygon(view_surface, b_gray, [(screen_x, body_y + size*0.45), (screen_x + size*0.2, body_y + size*0.1), (screen_x + size*0.1, body_y)])
                pygame.draw.polygon(view_surface, b_light, [(screen_x, body_y + size*0.4), (screen_x - size*0.12, body_y), (screen_x + size*0.12, body_y)])
                pygame.draw.polygon(view_surface, b_dark, [(screen_x - size*0.04, body_y + size*0.05), (screen_x + size*0.04, body_y + size*0.05), (screen_x + size*0.02, body_y + size*0.35), (screen_x - size*0.02, body_y + size*0.35)])
                pygame.draw.line(view_surface, b_light, (screen_x - size*0.03, body_y + size*0.1), (screen_x + size*0.03, body_y + size*0.15), max(1, int(size*0.02)))
                pygame.draw.line(view_surface, b_light, (screen_x - size*0.03, body_y + size*0.2), (screen_x + size*0.03, body_y + size*0.25), max(1, int(size*0.02)))

                pygame.draw.circle(view_surface, b_dark, (int(screen_x - size*0.28), int(head_y - size*0.2)), int(size*0.18))
                pygame.draw.circle(view_surface, b_light, (int(screen_x - size*0.28), int(head_y - size*0.2)), int(size*0.12))
                for i in range(3): pygame.draw.line(view_surface, b_dark, (int(screen_x - size*0.28), int(head_y - size*0.2)), (int(screen_x - size*0.28 - size*0.05), int(head_y - size*0.2 - i*size*0.04)), max(1, int(size*0.01)))

                pygame.draw.circle(view_surface, b_dark, (int(screen_x + size*0.28), int(head_y - size*0.2)), int(size*0.18))
                pygame.draw.circle(view_surface, b_light, (int(screen_x + size*0.28), int(head_y - size*0.2)), int(size*0.12))
                for i in range(3): pygame.draw.line(view_surface, b_dark, (int(screen_x + size*0.28), int(head_y - size*0.2)), (int(screen_x + size*0.28 + size*0.05), int(head_y - size*0.2 - i*size*0.04)), max(1, int(size*0.01)))

                spiky_hair = [(screen_x - size*0.15, head_y - size*0.25), (screen_x - size*0.1, head_y - size*0.4), (screen_x - size*0.05, head_y - size*0.3), (screen_x, head_y - size*0.45), (screen_x + size*0.05, head_y - size*0.3), (screen_x + size*0.1, head_y - size*0.4), (screen_x + size*0.15, head_y - size*0.25)]
                pygame.draw.polygon(view_surface, b_dark, spiky_hair)

                pygame.draw.ellipse(view_surface, b_light, (int(screen_x - size*0.25), int(head_y - size*0.3), int(size*0.5), int(size*0.55)))
                pygame.draw.circle(view_surface, b_dark, (int(screen_x - size*0.1), int(head_y - size*0.08)), int(size*0.06))
                pygame.draw.circle(view_surface, b_light, (int(screen_x - size*0.11), int(head_y - size*0.09)), int(size*0.02))
                pygame.draw.circle(view_surface, b_dark, (int(screen_x + size*0.1), int(head_y - size*0.08)), int(size*0.06))
                pygame.draw.circle(view_surface, b_light, (int(screen_x + size*0.09), int(head_y - size*0.09)), int(size*0.02))
                pygame.draw.polygon(view_surface, b_dark, [(screen_x - size*0.05, head_y + size*0.1), (screen_x + size*0.05, head_y + size*0.1), (screen_x, head_y + size*0.15)])
                pygame.draw.line(view_surface, b_dark, (int(screen_x - size*0.1), int(head_y + size*0.2)), (int(screen_x + size*0.1), int(head_y + size*0.2)), max(2, int(size*0.02)))
                pygame.draw.line(view_surface, b_dark, (int(screen_x), int(head_y + size*0.15)), (int(screen_x), int(head_y + size*0.2)), max(2, int(size*0.02)))
                pygame.draw.line(view_surface, b_dark, (int(screen_x - size*0.15), int(head_y + size*0.1)), (int(screen_x - size*0.45), int(head_y + size*0.02)), max(1, int(size*0.015)))
                pygame.draw.line(view_surface, b_dark, (int(screen_x - size*0.15), int(head_y + size*0.15)), (int(screen_x - size*0.45), int(head_y + size*0.12)), max(1, int(size*0.015)))
                pygame.draw.line(view_surface, b_dark, (int(screen_x - size*0.15), int(head_y + size*0.2)), (int(screen_x - size*0.40), int(head_y + size*0.22)), max(1, int(size*0.015)))
                pygame.draw.line(view_surface, b_dark, (int(screen_x + size*0.15), int(head_y + size*0.1)), (int(screen_x + size*0.45), int(head_y + size*0.02)), max(1, int(size*0.015)))
                pygame.draw.line(view_surface, b_dark, (int(screen_x + size*0.15), int(head_y + size*0.15)), (int(screen_x + size*0.45), int(head_y + size*0.12)), max(1, int(size*0.015)))
                pygame.draw.line(view_surface, b_dark, (int(screen_x + size*0.15), int(head_y + size*0.2)), (int(screen_x + size*0.40), int(head_y + size*0.22)), max(1, int(size*0.015)))

            elif cat == 'boss':
                breathe = math.sin(pygame.time.get_ticks() * 0.02 + obj['offset'] * 10) * (size/20)
                body_y = item_y - size/3 + breathe
                
                b_dark = apply_fog((15, 10, 15), intensity)
                b_mid = apply_fog((35, 25, 35), intensity)
                blood = apply_fog((150, 0, 0), intensity)
                bone = apply_fog((200, 200, 180), intensity)
                e_glow = apply_fog((255, 0, 0), intensity)

                pygame.draw.ellipse(view_surface, b_dark, (int(screen_x - size*0.7), int(body_y - size*0.3), int(size*1.4), int(size*0.8)))
                for i in range(5):
                    lx = screen_x + math.sin(obj['offset'] * 10 + i * 2) * size * 0.5
                    ly = body_y + math.cos(obj['offset'] * 10 + i * 2) * size * 0.2
                    pygame.draw.circle(view_surface, b_mid, (int(lx), int(ly)), int(size*0.25))

                for i in range(3):
                    hx = screen_x - size*0.4 + (i * size*0.4)
                    hy = body_y - size*0.1 + math.sin(pygame.time.get_ticks()*0.005 + i + obj['offset']) * size*0.15
                    pygame.draw.ellipse(view_surface, b_dark, (int(hx - size*0.2), int(hy - size*0.15), int(size*0.4), int(size*0.3)))
                    pygame.draw.rect(view_surface, blood, (int(hx - size*0.15), int(hy), int(size*0.3), int(size*0.15)))
                    for j in range(4): pygame.draw.rect(view_surface, bone, (int(hx - size*0.12 + j*size*0.07), int(hy), int(size*0.04), int(size*0.08)))
                    pygame.draw.circle(view_surface, e_glow, (int(hx - size*0.1), int(hy - size*0.1)), int(size*0.04))
                    pygame.draw.circle(view_surface, e_glow, (int(hx + size*0.1), int(hy - size*0.1)), int(size*0.04))

                for i in range(7):
                    ex = screen_x + math.cos(i*2.1) * size * 0.6
                    ey = body_y + math.sin(i*3.4) * size * 0.3
                    pygame.draw.circle(view_surface, e_glow, (int(ex), int(ey)), int(size*0.03))

                pygame.draw.line(view_surface, b_mid, (int(screen_x - size*0.5), int(body_y)), (int(screen_x - size*0.7), int(body_y + size*0.4)), max(2, int(size/10)))
                pygame.draw.circle(view_surface, bone, (int(screen_x - size*0.7), int(body_y + size*0.4)), int(size*0.05))
                pygame.draw.line(view_surface, b_mid, (int(screen_x + size*0.4), int(body_y)), (int(screen_x + size*0.6), int(body_y + size*0.4)), max(2, int(size/10)))
                pygame.draw.circle(view_surface, bone, (int(screen_x + size*0.6), int(body_y + size*0.4)), int(size*0.05))
                
            elif cat == 'bullet':
                b_size = max(3, int(size / 5))
                pygame.draw.circle(view_surface, (255, 100, 0), (int(screen_x), int(item_y - size/4)), b_size + 3) 
                pygame.draw.circle(view_surface, (255, 255, 200), (int(screen_x), int(item_y - size/4)), b_size)     

def update_entities_and_collision():
    global player_health, player_armor, pain_timer, attack_cooldown
    global spawn_timer, rat_sound_timer, boss_sound_timer, entities, kill_count, boss_spawn_counter
    
    if rat_sound_timer > 0: rat_sound_timer -= 1
    if boss_sound_timer > 0: boss_sound_timer -= 1
    
    min_rat_dist = 9999
    min_boss_dist = 9999
    
    for ent in entities:
        if ent['active']:
            d = math.hypot(player_x - ent['x'], player_y - ent['y'])
            if ent['type'] == 'monster' and d < min_rat_dist: min_rat_dist = d
            if ent['type'] == 'boss' and d < min_boss_dist: min_boss_dist = d

    if rat_sound_timer == 0 and min_rat_dist < MAX_DEPTH and rat_sfx:
        rat_sfx.set_volume(max(0.0, 1.0 - (min_rat_dist / MAX_DEPTH)))
        rat_sfx.play()
        rat_sound_timer = 90

    if boss_sound_timer == 0 and min_boss_dist < MAX_DEPTH and boss_sfx:
        boss_sfx.set_volume(max(0.0, 1.0 - (min_boss_dist / MAX_DEPTH)))
        boss_sfx.play()
        boss_sound_timer = 150 

    spawn_timer += 1
    if spawn_timer >= 120: 
        spawn_timer = 0
        while True:
            rx = random.randint(1, len(world_map[0])-2)
            ry = random.randint(1, len(world_map)-2)
            if world_map[ry][rx] == 0:
                sx = rx * TILE_SIZE + TILE_SIZE/2
                sy = ry * TILE_SIZE + TILE_SIZE/2
                if math.hypot(sx - player_x, sy - player_y) > 300: 
                    entities.append({'id': f'mon_{pygame.time.get_ticks()}', 'type': 'monster', 'x': sx, 'y': sy, 'active': True, 'hp': 2, 'speed': 1.6, 'offset': random.random()})
                    break

    for b in bullets:
        if not b['active']: continue
        b['x'] += math.cos(b['angle']) * b['speed']
        b['y'] += math.sin(b['angle']) * b['speed']
        
        map_x = int(b['x'] / TILE_SIZE)
        map_y = int(b['y'] / TILE_SIZE)
        if map_x < 0 or map_x >= len(world_map[0]) or map_y < 0 or map_y >= len(world_map):
            b['active'] = False; continue
        if world_map[map_y][map_x] == 1:
            b['active'] = False; continue
            
        for ent in entities:
            if ent['type'] in ['monster', 'boss'] and ent['active']:
                dist = math.hypot(b['x'] - ent['x'], b['y'] - ent['y'])
                hitbox = 60 if ent['type'] == 'boss' else 40
                if dist < hitbox: 
                    ent['hp'] -= 1
                    b['active'] = False 
                    
                    if ent['hp'] <= 0: 
                        ent['active'] = False 
                        kill_count += 1 
                        
                        if ent['type'] == 'monster':
                            boss_spawn_counter += 1
                            if boss_spawn_counter >= 10:
                                boss_spawn_counter = 0
                                while True:
                                    rx = random.randint(1, len(world_map[0])-2)
                                    ry = random.randint(1, len(world_map)-2)
                                    if world_map[ry][rx] == 0:
                                        sx = rx * TILE_SIZE + TILE_SIZE/2
                                        sy = ry * TILE_SIZE + TILE_SIZE/2
                                        if math.hypot(sx - player_x, sy - player_y) > 300:
                                            entities.append({'id': f'boss_{pygame.time.get_ticks()}', 'type': 'boss', 'x': sx, 'y': sy, 'active': True, 'hp': 25, 'speed': 0.8, 'offset': random.random()})
                                            break
                            
                            roll = random.random()
                            if roll <= 0.80: drop_type = 'ammo'
                            elif roll <= 0.95: drop_type = 'armor'
                            else: drop_type = 'health'
                            entities.append({'id': f'drop_{random.random()}', 'type': drop_type, 'x': ent['x'], 'y': ent['y'], 'active': True})
                        
                        elif ent['type'] == 'boss':
                            for _ in range(3):
                                roll = random.random()
                                if roll <= 0.60: drop_type = 'ammo'
                                elif roll <= 0.90: drop_type = 'armor'
                                else: drop_type = 'health'
                                entities.append({'id': f'drop_{random.random()}', 'type': drop_type, 'x': ent['x']+random.randint(-20,20), 'y': ent['y']+random.randint(-20,20), 'active': True})
                    break

    for ent in entities:
        if ent['type'] in ['monster', 'boss'] and ent['active']:
            dist = math.hypot(player_x - ent['x'], player_y - ent['y'])
            
            if 45 < dist < MAX_DEPTH: 
                dx = (player_x - ent['x']) / dist
                dy = (player_y - ent['y']) / dist
                
                new_ent_x = ent['x'] + dx * ent['speed']
                new_ent_y = ent['y'] + dy * ent['speed']
                
                if world_map[int(ent['y'] / TILE_SIZE)][int(new_ent_x / TILE_SIZE)] == 0:
                    ent['x'] = new_ent_x
                if world_map[int(new_ent_y / TILE_SIZE)][int(ent['x'] / TILE_SIZE)] == 0:
                    ent['y'] = new_ent_y
                    
            elif dist <= 45: 
                if attack_cooldown == 0:
                    damage = 30 if ent['type'] == 'boss' else 10
                    if player_armor > 0:
                        player_armor -= damage
                        if player_armor < 0:
                            player_health += player_armor 
                            player_armor = 0
                    else:
                        player_health -= damage

                    pain_timer = 20
                    attack_cooldown = 60
                    if player_health <= 0: player_health = 0

    entities[:] = [e for e in entities if e['active']]

def draw_player_ui():
    global recoil_timer, muzzle_flash_timer, reload_timer
    
    if not has_weapon:
        pygame.draw.rect(view_surface, (180, 130, 90), (WIDTH//2 - 250, VIEW_HEIGHT - 120, 80, 120), border_radius=10) 
        pygame.draw.rect(view_surface, (180, 130, 90), (WIDTH//2 + 170, VIEW_HEIGHT - 120, 80, 120), border_radius=10) 
    else:
        if reload_timer > 0:
            recoil_offset = 300 
        else:
            recoil_offset = recoil_timer * 3 if recoil_timer > 0 else 0
            
        if recoil_timer > 0: recoil_timer -= 1
            
        gun_x = WIDTH // 2
        gun_y = VIEW_HEIGHT + recoil_offset
        
        barrel_poly = [(gun_x - 40, gun_y), (gun_x - 20, gun_y - 200), (gun_x + 20, gun_y - 200), (gun_x + 40, gun_y)]
        pygame.draw.polygon(view_surface, (40, 40, 40), barrel_poly)
        core_poly = [(gun_x - 10, gun_y - 50), (gun_x - 5, gun_y - 150), (gun_x + 5, gun_y - 150), (gun_x + 10, gun_y - 50)]
        pygame.draw.polygon(view_surface, (0, 150, 200), core_poly)
        
        if muzzle_flash_timer > 0 and reload_timer == 0:
            flash_y = gun_y - 220
            pygame.draw.circle(view_surface, (255, 255, 0), (gun_x, flash_y), 30 + random.randint(-5, 5))
            pygame.draw.circle(view_surface, (255, 100, 0), (gun_x, flash_y), 15)
            muzzle_flash_timer -= 1

def draw_doom_hud():
    global pain_timer
    
    pygame.draw.rect(screen, (30, 30, 30), (0, VIEW_HEIGHT, WIDTH, HUD_HEIGHT))
    pygame.draw.rect(screen, (15, 15, 15), (0, VIEW_HEIGHT, WIDTH, 5))
    pygame.draw.rect(screen, (15, 15, 15), (0, HEIGHT - 5, WIDTH, 5))

    red_txt = (200, 30, 30)
    grey_txt = (120, 120, 120)

    ammo_text = f"{current_mag}/{reserve_ammo}" if has_weapon else "0"
    screen.blit(font_huge.render(ammo_text, True, red_txt), (80, VIEW_HEIGHT + 35))
    screen.blit(font_large.render("PELURU", True, grey_txt), (90, VIEW_HEIGHT + 110))

    screen.blit(font_huge.render(f"{player_health}%", True, red_txt), (330, VIEW_HEIGHT + 35))
    screen.blit(font_large.render("NYAWA", True, grey_txt), (330, VIEW_HEIGHT + 110))

    face_center_x = WIDTH // 2
    face_center_y = VIEW_HEIGHT + 80
    
    face_rect = (face_center_x - 60, face_center_y - 65, 120, 130)
    pygame.draw.rect(screen, (10, 10, 10), face_rect) 
    pygame.draw.rect(screen, (60, 60, 60), face_rect, 4) 
    
    if pain_timer > 0:
        pygame.draw.rect(screen, (120, 20, 20), face_rect)
        pygame.draw.rect(screen, (60, 60, 60), face_rect, 4) 

    emoji_res = 28
    emoji_surf = pygame.Surface((emoji_res, emoji_res), pygame.SRCALPHA)
    
    pygame.draw.circle(emoji_surf, (255, 215, 0), (emoji_res//2, emoji_res//2), emoji_res//2 - 1)
    
    if player_health <= 0:
        pygame.draw.line(emoji_surf, (30,30,30), (7, 8), (11, 12), 2)
        pygame.draw.line(emoji_surf, (30,30,30), (11, 8), (7, 12), 2)
        pygame.draw.line(emoji_surf, (30,30,30), (17, 8), (21, 12), 2)
        pygame.draw.line(emoji_surf, (30,30,30), (21, 8), (17, 12), 2)
        pygame.draw.rect(emoji_surf, (30,30,30), (10, 16, 8, 7))
        pygame.draw.rect(emoji_surf, (255,255,255), (11, 16, 6, 2)) 
    elif pain_timer > 0:
        pain_timer -= 1
        pygame.draw.line(emoji_surf, (30,30,30), (7, 8), (11, 10), 2)
        pygame.draw.line(emoji_surf, (30,30,30), (7, 12), (11, 10), 2)
        pygame.draw.line(emoji_surf, (30,30,30), (21, 8), (17, 10), 2)
        pygame.draw.line(emoji_surf, (30,30,30), (21, 12), (17, 10), 2)
        pygame.draw.lines(emoji_surf, (30,30,30), False, [(7, 17), (10, 20), (14, 17), (18, 20), (21, 17)], 2)
    else:
        pygame.draw.rect(emoji_surf, (30,30,30), (8, 9, 3, 4))
        pygame.draw.rect(emoji_surf, (30,30,30), (17, 9, 3, 4))
        pygame.draw.rect(emoji_surf, (30,30,30), (7, 17, 14, 2))
        pygame.draw.rect(emoji_surf, (230, 100, 130), (12, 19, 5, 5))
        pygame.draw.rect(emoji_surf, (30,30,30), (14, 19, 1, 3))

    scaled_emoji = pygame.transform.scale(emoji_surf, (96, 96))
    screen.blit(scaled_emoji, (face_center_x - 48, face_center_y - 48))

    screen.blit(font_huge.render(f"{player_armor}%", True, red_txt), (WIDTH//2 + 170, VIEW_HEIGHT + 35))
    screen.blit(font_large.render("TAMENG", True, grey_txt), (WIDTH//2 + 150, VIEW_HEIGHT + 110))

    ammo_types = ["MAG", "SISA", "ROKET", "SEL"]
    ammo_values = [str(current_mag), str(reserve_ammo), " 0", " 0"]
    for i in range(4):
        screen.blit(font_small.render(ammo_types[i], True, grey_txt), (WIDTH - 250, VIEW_HEIGHT + 25 + i * 30))
        screen.blit(font_small.render(ammo_values[i], True, red_txt), (WIDTH - 150, VIEW_HEIGHT + 25 + i * 30))

pygame.mixer.init()
try:
    if os.path.exists('shoot.wav'): shoot_sfx = pygame.mixer.Sound('shoot.wav')
    if os.path.exists('hurt.wav'): hurt_sfx = pygame.mixer.Sound('hurt.wav')
    if os.path.exists('rat.wav'): rat_sfx = pygame.mixer.Sound('rat.wav')
    if os.path.exists('boss.wav'): boss_sfx = pygame.mixer.Sound('boss.wav')
except:
    pass

running = True
while running:
    if player_health <= 0: game_over = True
    if attack_cooldown > 0: attack_cooldown -= 1

    if reload_timer > 0:
        reload_timer -= 1
        if reload_timer == 0:
            needed = max_mag - current_mag
            if reserve_ammo >= needed:
                current_mag += needed
                reserve_ammo -= needed
            else:
                current_mag += reserve_ammo
                reserve_ammo = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            if event.button == 1 and has_weapon and current_mag > 0 and recoil_timer == 0 and reload_timer == 0:
                current_mag -= 1 
                recoil_timer = 15       
                muzzle_flash_timer = 3  
                if shoot_sfx: shoot_sfx.play()
                
                bullets.append({'x': player_x, 'y': player_y, 'angle': player_angle, 'speed': 25.0, 'active': True})

    if not game_over:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]: running = False

        if keys[pygame.K_r] and has_weapon and current_mag < max_mag and reserve_ammo > 0 and reload_timer == 0:
            reload_timer = RELOAD_TIME

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
            if world_map[int(player_y / TILE_SIZE)][int(new_x / TILE_SIZE)] == 0: player_x = new_x
        if 0 <= player_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
            if world_map[int(new_y / TILE_SIZE)][int(player_x / TILE_SIZE)] == 0: player_y = new_y

        for ent in entities:
            if ent['type'] in ['item', 'ammo', 'armor', 'health'] and ent['active']:
                if math.hypot(player_x - ent['x'], player_y - ent['y']) < 50:
                    ent['active'] = False
                    
                    if ent['type'] == 'item': 
                        has_weapon = True
                    elif ent['type'] == 'ammo': 
                        reserve_ammo += 12 
                    elif ent['type'] == 'armor': 
                        player_armor = min(100, player_armor + 30) 
                    elif ent['type'] == 'health': 
                        player_health = min(100, player_health + 80) 

        update_entities_and_collision()
        
        min_rat_dist = 9999
        min_boss_dist = 9999
        for ent in entities:
            if ent['active']:
                d = math.hypot(player_x - ent['x'], player_y - ent['y'])
                if ent['type'] == 'monster' and d < min_rat_dist: min_rat_dist = d
                if ent['type'] == 'boss' and d < min_boss_dist: min_boss_dist = d

        if rat_sound_timer == 0 and min_rat_dist < MAX_DEPTH and rat_sfx:
            rat_sfx.set_volume(max(0.0, 1.0 - (min_rat_dist / MAX_DEPTH)))
            rat_sfx.play()
            rat_sound_timer = 90

        if boss_sound_timer == 0 and min_boss_dist < MAX_DEPTH and boss_sfx:
            boss_sfx.set_volume(max(0.0, 1.0 - (min_boss_dist / MAX_DEPTH)))
            boss_sfx.play()
            boss_sound_timer = 150

    view_surface.fill((0, 0, 0)) 
    cast_rays()         
    render_sprites()      
    draw_player_ui()      
    
    PIXEL_SCALE = 6 
    small_view = pygame.transform.scale(view_surface, (WIDTH // PIXEL_SCALE, VIEW_HEIGHT // PIXEL_SCALE))
    pixelated_view = pygame.transform.scale(small_view, (WIDTH, VIEW_HEIGHT))
    
    screen.fill((0, 0, 0))
    screen.blit(pixelated_view, (0, 0))
    
    draw_doom_hud()       
    
    screen.blit(font_large.render(f"DIBASMI: {kill_count}", True, (255, 0, 0)), (20, 20))
    
    if reload_timer > 0:
        screen.blit(font_large.render("MENGISI PELURU...", True, (255, 255, 0)), (WIDTH//2 - 120, VIEW_HEIGHT//2 + 50))
    elif has_weapon and current_mag == 0 and reserve_ammo > 0:
        screen.blit(font_large.render("TEKAN 'R' UNTUK MENGISI PELURU", True, (255, 0, 0)), (WIDTH//2 - 200, VIEW_HEIGHT//2 + 50))
    elif has_weapon and current_mag == 0 and reserve_ammo == 0:
        screen.blit(font_large.render("PELURU HABIS!", True, (255, 0, 0)), (WIDTH//2 - 100, VIEW_HEIGHT//2 + 50))

    if game_over:
        s = pygame.Surface((WIDTH, VIEW_HEIGHT)) 
        s.set_alpha(180) 
        s.fill((150, 0, 0)) 
        screen.blit(s, (0,0))
        screen.blit(font_huge.render("TUMBANG OLEH KORUPSI", True, (255, 255, 255)), (WIDTH//2 - 380, VIEW_HEIGHT//2 - 45))
        screen.blit(font_large.render(f"TOTAL DIBASMI: {kill_count}", True, (255, 255, 0)), (WIDTH//2 - 120, VIEW_HEIGHT//2 + 40))

    pygame.draw.circle(screen, (0, 255, 0), (WIDTH // 2, VIEW_HEIGHT // 2), 2)
    
    pygame.display.flip()  
    clock.tick(60)         

pygame.mouse.set_visible(True)
pygame.event.set_grab(False)
pygame.quit()
sys.exit()
