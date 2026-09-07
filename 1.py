import pygame
import sys
import random
import math

pygame.init()

SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 650
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Rise of Nations - Village Developer Edition")

# Colors
SKY_TOP = (20, 35, 55)
SKY_BOT = (55, 90, 130)
BG_GRASS = (39, 139, 34)
GRASS_DARK = (30, 120, 26)
GRID_LINE = (34, 115, 30)
GOLD_THEME = (212, 175, 55)
GOLD_BAR = (244, 208, 63)
GOLD_DARK = (180, 140, 30)
ELIXIR_THEME = (155, 89, 182)
ELIXIR_BAR = (165, 105, 189)
ELIXIR_DARK = (120, 60, 150)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TEXT_MUTED = (180, 190, 200)
WALL_THEME = (120, 66, 18)
WALL_LIGHT = (160, 100, 40)
UI_MAIN_BG = (22, 32, 42)
UI_BORDER = (50, 70, 90)
BAR_BG = (35, 45, 55)
GREEN_HIGHLIGHT = (46, 204, 113)
RED_ALERT = (231, 76, 60)
WATER_BLUE = (30, 100, 150)
WOOD_BROWN = (90, 60, 30)
ENEMY_COLOR = (180, 40, 40)
ENEMY_DARK = (120, 20, 20)
SELECTION_COLOR = (0, 255, 100)

# Fonts
fonts = {}
for name, size, bold in [("sm", 12, True), ("md", 15, True), ("lg", 24, True), ("xl", 32, True), ("xs", 10, True), ("xxl", 42, True)]:
    try:
        fonts[name] = pygame.font.SysFont("Arial", size, bold=bold)
    except:
        fonts[name] = pygame.font.Font(None, size + 10)
font_sm, font_md, font_lg, font_xl, font_xs, font_xxl = fonts["sm"], fonts["md"], fonts["lg"], fonts["xl"], fonts["xs"], fonts["xxl"]

# Game Resources & States
gold = 500
elixir = 500
town_hall_lvl = 1
player_units = []
player_buildings = []
enemies = []
resource_timer = 0
particles = []
trees = []
combat_texts = []
camera_shake = 0
game_time = 0

# Building placement mode
placement_mode = None
placement_preview_valid = False

# Unit selection
selected_units = []
selection_start = None
is_dragging = False

# Wave system
wave_number = 0
wave_active = False
wave_cooldown = 0
wave_spawn_timer = 0
enemies_to_spawn = []
wave_announce_timer = 0
wave_announce_text = ""

# Level system
current_level = 1
max_level = 8
level_state = "playing"
level_announce_timer = 0
level_announce_text = ""
level_transition_timer = 0

# Building HP tracking
building_hp = {}

# Level definitions: (waves, enemies per wave, enemy types)
LEVELS = [
    {"name": "The Beginning", "waves": 2, "enemies_per_wave": (2, 3), "types": ["goblin"]},
    {"name": "First Threat", "waves": 2, "enemies_per_wave": (3, 4), "types": ["goblin", "goblin", "raider"]},
    {"name": "Dark Raiders", "waves": 2, "enemies_per_wave": (3, 5), "types": ["goblin", "raider", "raider"]},
    {"name": "Ogre March", "waves": 3, "enemies_per_wave": (2, 4), "types": ["goblin", "raider", "ogre"]},
    {"name": "Horde", "waves": 3, "enemies_per_wave": (4, 6), "types": ["goblin", "raider", "ogre", "raider"]},
    {"name": "Fortress Siege", "waves": 3, "enemies_per_wave": (4, 7), "types": ["raider", "ogre", "raider", "ogre"]},
    {"name": "Dark Legion", "waves": 4, "enemies_per_wave": (5, 7), "types": ["raider", "ogre", "raider", "ogre", "goblin"]},
    {"name": "The Final Stand", "waves": 4, "enemies_per_wave": (6, 8), "types": ["ogre", "raider", "ogre", "raider", "ogre"]},
]

# Generate trees
for _ in range(30):
    trees.append({
        "x": random.randint(80, SCREEN_WIDTH - 80),
        "y": random.randint(180, SCREEN_HEIGHT - 40),
        "size": random.uniform(8, 16),
        "shade": random.randint(0, 2)
    })

clock = pygame.time.Clock()
running = True

def draw_text(text, font, color, x, y, shadow=False):
    if shadow:
        shadow_surf = font.render(text, True, (0, 0, 0))
        screen.blit(shadow_surf, (x + 1, y + 1))
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))

def draw_rounded_rect(surface, color, rect, radius=6):
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return
    if radius > min(w, h) // 2:
        radius = min(w, h) // 2
    pygame.draw.rect(surface, color, (x + radius, y, w - 2 * radius, h))
    pygame.draw.rect(surface, color, (x, y + radius, w, h - 2 * radius))
    pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)

def spawn_particles(x, y, color, count=8):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(0.5, 2.5)
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed - 1,
            "life": random.randint(20, 40),
            "max_life": 40,
            "color": color,
            "size": random.uniform(2, 5)
        })

def dist(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def is_valid_placement(x, y, w, h):
    if x < 20 or x + w > SCREEN_WIDTH - 20 or y < 150 or y + h > SCREEN_HEIGHT - 20:
        return False
    for b in player_buildings:
        if abs(b["x"] - x) < 50 and abs(b["y"] - y) < 50:
            return False
    if abs(x + w//2 - 70) < 100 and abs(y + h//2 - 360) < 120:
        return False
    for t in trees:
        if abs(x + w//2 - t["x"]) < 25 and abs(y + h//2 - t["y"]) < 25:
            return False
    return True

def get_enemy_type_stats(e_type):
    if e_type == "goblin":
        return {"hp": 30, "speed": 1.5, "damage": 5, "attack_cooldown": 30, "size": 7}
    elif e_type == "ogre":
        return {"hp": 80, "speed": 0.7, "damage": 15, "attack_cooldown": 60, "size": 12}
    else:
        return {"hp": 50, "speed": 1.2, "damage": 8, "attack_cooldown": 40, "size": 9}

def spawn_enemy(e_type, x, y):
    stats = get_enemy_type_stats(e_type)
    enemies.append({
        "x": x, "y": y,
        "type": e_type,
        "hp": stats["hp"], "max_hp": stats["hp"],
        "speed": stats["speed"],
        "damage": stats["damage"],
        "attack_cooldown": stats["attack_cooldown"],
        "attack_timer": 0,
        "size": stats["size"],
        "target": None,
        "walk_frame": random.uniform(0, math.pi * 2),
        "angle": math.pi
    })

def start_level():
    global current_level, wave_number, wave_active, enemies_to_spawn, wave_announce_timer, wave_announce_text, level_state
    wave_number = 0
    level_state = "playing"
    next_wave()

def next_wave():
    global wave_number, wave_active, enemies_to_spawn, wave_announce_timer, wave_announce_text
    if current_level > max_level:
        return
    level_data = LEVELS[current_level - 1]
    if wave_number >= level_data["waves"]:
        return
    wave_number += 1
    wave_active = True
    wave_announce_text = f"Level {current_level} - Wave {wave_number}/{level_data['waves']}"
    wave_announce_timer = 90

    min_e, max_e = level_data["enemies_per_wave"]
    total_enemies = random.randint(min_e, max_e)
    enemies_to_spawn = []
    for _ in range(total_enemies):
        e_type = random.choice(level_data["types"])
        enemies_to_spawn.append(e_type)
    random.shuffle(enemies_to_spawn)

def spawn_next_enemy():
    if not enemies_to_spawn:
        return
    e_type = enemies_to_spawn.pop(0)
    x = SCREEN_WIDTH + 20
    y = random.randint(200, 550)
    spawn_enemy(e_type, x, y)
    spawn_particles(x - 10, y, ENEMY_COLOR, 5)

def check_level_complete():
    global level_state, level_announce_timer, level_announce_text, gold, elixir, current_level
    if wave_active:
        return False
    if enemies:
        return False
    if wave_number < LEVELS[current_level - 1]["waves"]:
        return False
    level_state = "complete"
    level_announce_text = f"LEVEL {current_level} COMPLETE!"
    level_announce_timer = 180
    gold += 200
    elixir += 200
    return True

def advance_level():
    global current_level, level_state, level_announce_timer, level_announce_text
    if current_level < max_level:
        current_level += 1
        level_announce_text = f"--- LEVEL {current_level}: {LEVELS[current_level - 1]['name']} ---"
        level_announce_timer = 120
        level_state = "transition"
    else:
        level_state = "won"
        level_announce_text = "YOU WIN! ALL LEVELS COMPLETE!"
        level_announce_timer = 9999

# --- START GAME ---
start_level()

# === MAIN LOOP ===
while running:
    clock.tick(60)
    game_time += 1
    mouse_x, mouse_y = pygame.mouse.get_pos()
    keys = pygame.key.get_pressed()
    shift_held = pygame.key.get_mods() & pygame.KMOD_SHIFT

    # --- Background: Sky Gradient ---
    for i in range(140):
        ratio = i / 140
        r = int(SKY_TOP[0] + (SKY_BOT[0] - SKY_TOP[0]) * ratio)
        g = int(SKY_TOP[1] + (SKY_BOT[1] - SKY_TOP[1]) * ratio)
        b = int(SKY_TOP[2] + (SKY_BOT[2] - SKY_TOP[2]) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))

    # Ground
    for i in range(140, SCREEN_HEIGHT):
        shade = random.randint(-5, 5)
        r = max(0, min(255, BG_GRASS[0] + shade))
        g = max(0, min(255, BG_GRASS[1] + shade))
        b = max(0, min(255, BG_GRASS[2] + shade))
        pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))

    # Perspective Grid
    for i in range(-200, SCREEN_WIDTH + 400, 70):
        alpha = max(30, min(120, 120 - (i + 200) * 0.1))
        pygame.draw.line(screen, (*GRID_LINE[:2], max(0, int(alpha))), (i, 140), (i - 150, SCREEN_HEIGHT), 1)
    for j in range(140, SCREEN_HEIGHT, 50):
        alpha = max(40, min(100, 100 - (j - 140) * 0.3))
        pygame.draw.line(screen, (*GRID_LINE[:2], max(0, int(alpha))), (0, j), (SCREEN_WIDTH, j), 1)

    # Draw Trees
    for t in trees:
        shade = t["shade"]
        s = t["size"]
        tx, ty = t["x"], t["y"]
        pygame.draw.ellipse(screen, (20, 60, 16), (tx - s * 0.6, ty + s * 0.3, s * 1.2, s * 0.4))
        trunk_color = (70 + shade * 10, 45 + shade * 5, 20)
        pygame.draw.rect(screen, trunk_color, (tx - 2, ty - s * 0.2, 4, s * 0.6))
        foliage_colors = [(34, 120 + shade * 10, 28), (40, 140 + shade * 10, 32), (28, 100 + shade * 10, 22)]
        for i, (fc, off) in enumerate(zip(foliage_colors, [(-s * 0.3, -s * 0.5), (s * 0.3, -s * 0.3), (0, -s * 0.7)])):
            pygame.draw.circle(screen, fc, (int(tx + off[0]), int(ty + off[1])), int(s * 0.45 - i * 2))

    # Announcements
    if wave_announce_timer > 0:
        wave_announce_timer -= 1
        alpha = min(255, wave_announce_timer * 5)
        try:
            a_surf = pygame.Surface((SCREEN_WIDTH, 80), pygame.SRCALPHA)
            a_text = font_xxl.render(wave_announce_text, True, (255, 200, 50))
            a_rect = a_text.get_rect(center=(SCREEN_WIDTH // 2, 40))
            a_surf.blit(a_text, a_rect)
            a_surf.set_alpha(alpha)
            screen.blit(a_surf, (0, 250))
        except:
            draw_text(wave_announce_text, font_lg, GOLD_THEME, SCREEN_WIDTH // 2 - 150, 280, shadow=True)

    if level_announce_timer > 0:
        level_announce_timer -= 1
        alpha = min(255, level_announce_timer * 4)
        try:
            a_surf = pygame.Surface((SCREEN_WIDTH, 80), pygame.SRCALPHA)
            color = (50, 255, 100) if "COMPLETE" in level_announce_text else (255, 200, 50)
            a_text = font_xxl.render(level_announce_text, True, color)
            a_rect = a_text.get_rect(center=(SCREEN_WIDTH // 2, 40))
            a_surf.blit(a_text, a_rect)
            a_surf.set_alpha(alpha)
            screen.blit(a_surf, (0, 250))
        except:
            draw_text(level_announce_text, font_lg, GREEN_HIGHLIGHT if "COMPLETE" in level_announce_text else GOLD_THEME, SCREEN_WIDTH // 2 - 200, 280, shadow=True)

    # Level transition
    if level_state == "transition" and level_announce_timer <= 0:
        start_level()

    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                if placement_mode:
                    placement_mode = None
                cost = 25 if town_hall_lvl == 1 else 40
                if elixir >= cost:
                    elixir -= cost
                    ux = 150
                    uy = random.randint(220, 580)
                    player_units.append({
                        "x": ux, "y": uy,
                        "type": "barbarian", "speed": 1.2,
                        "angle": random.uniform(0, math.pi * 2),
                        "hp": 50, "max_hp": 50,
                        "target_x": None, "target_y": None,
                        "attack_target": None,
                        "walk_frame": random.uniform(0, math.pi * 2),
                        "attack_timer": 0,
                        "damage": 8,
                        "attack_cooldown": 30,
                        "range": 25
                    })
                    spawn_particles(ux, uy, (230, 126, 34), 6)

            if event.key == pygame.K_2:
                if placement_mode:
                    placement_mode = None
                cost = 50 if town_hall_lvl == 1 else 80
                if elixir >= cost:
                    elixir -= cost
                    ux = 150
                    uy = random.randint(220, 580)
                    player_units.append({
                        "x": ux, "y": uy,
                        "type": "wizard", "speed": 0.9,
                        "angle": random.uniform(0, math.pi * 2),
                        "hp": 30, "max_hp": 30,
                        "target_x": None, "target_y": None,
                        "attack_target": None,
                        "walk_frame": random.uniform(0, math.pi * 2),
                        "attack_timer": 0,
                        "damage": 12,
                        "attack_cooldown": 40,
                        "range": 80
                    })
                    spawn_particles(ux, uy, (52, 152, 219), 6)

            if event.key == pygame.K_g:
                mine = next((b for b in player_buildings if b["type"] == "gold_mine"), None)
                if not mine:
                    if gold >= 100:
                        placement_mode = "gold_mine"
                else:
                    upgrade_cost = mine["level"] * 150
                    if gold >= upgrade_cost and mine["level"] < 5:
                        gold -= upgrade_cost
                        mine["level"] += 1
                        spawn_particles(mine["x"] + 27, mine["y"] + 27, GOLD_THEME, 12)

            if event.key == pygame.K_e:
                collector = next((b for b in player_buildings if b["type"] == "elixir_collector"), None)
                if not collector:
                    if gold >= 100:
                        placement_mode = "elixir_collector"
                else:
                    upgrade_cost = collector["level"] * 150
                    if gold >= upgrade_cost and collector["level"] < 5:
                        gold -= upgrade_cost
                        collector["level"] += 1
                        spawn_particles(collector["x"] + 27, collector["y"] + 27, ELIXIR_THEME, 12)

            if event.key == pygame.K_w:
                if gold >= 50:
                    placement_mode = "wall"

            if event.key == pygame.K_u and town_hall_lvl == 1:
                if gold >= 300 and elixir >= 300:
                    gold -= 300
                    elixir -= 300
                    town_hall_lvl = 2
                    spawn_particles(70, 360, GOLD_THEME, 20)
                    spawn_particles(70, 360, ELIXIR_THEME, 20)
                    camera_shake = 10

            if event.key == pygame.K_ESCAPE:
                placement_mode = None
                selected_units = []
                is_dragging = False
                selection_start = None

            if event.key == pygame.K_TAB:
                selected_units = []

            if event.key == pygame.K_RETURN:
                if level_state == "complete":
                    advance_level()
                elif level_state == "won":
                    pass

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            if event.button == 1:
                if placement_mode:
                    if my > 145:
                        place_x = mx - 27
                        place_y = my - 27
                        w, h = (55, 55) if placement_mode != "wall" else (24, 55)
                        if is_valid_placement(place_x, place_y, w, h):
                            if placement_mode == "gold_mine":
                                gold -= 100
                                player_buildings.append({"x": place_x, "y": place_y, "type": "gold_mine", "level": 1})
                                spawn_particles(place_x + 27, place_y + 27, GOLD_THEME, 10)
                            elif placement_mode == "elixir_collector":
                                gold -= 100
                                player_buildings.append({"x": place_x, "y": place_y, "type": "elixir_collector", "level": 1})
                                spawn_particles(place_x + 27, place_y + 27, ELIXIR_THEME, 10)
                            elif placement_mode == "wall":
                                gold -= 50
                                player_buildings.append({"x": place_x, "y": place_y, "type": "wall", "level": 1})
                                spawn_particles(place_x + 12, place_y + 27, WALL_THEME, 6)
                            placement_mode = None
                else:
                    if my > 145:
                        found = None
                        for u in player_units:
                            if dist(mx, my, u["x"], u["y"]) < 15:
                                found = u
                                break
                        if found:
                            if shift_held:
                                if found in selected_units:
                                    selected_units.remove(found)
                                else:
                                    selected_units.append(found)
                            else:
                                selected_units = [found]
                            is_dragging = False
                            selection_start = None
                        else:
                            if not shift_held:
                                selected_units = []
                            selection_start = (mx, my)
                            is_dragging = True

            if event.button == 3:
                if my > 145 and not placement_mode:
                    if selected_units:
                        target_enemy = None
                        for e in enemies:
                            if dist(mx, my, e["x"], e["y"]) < 20:
                                target_enemy = e
                                break
                        for u in selected_units:
                            u["target_x"] = mx
                            u["target_y"] = my
                            u["attack_target"] = target_enemy

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and is_dragging and selection_start:
                sx, sy = selection_start
                ex, ey = pygame.mouse.get_pos()
                rect_x1 = min(sx, ex)
                rect_y1 = min(sy, ey)
                rect_x2 = max(sx, ex)
                rect_y2 = max(sy, ey)

                if abs(ex - sx) > 5 or abs(ey - sy) > 5:
                    for u in player_units:
                        if rect_x1 <= u["x"] <= rect_x2 and rect_y1 <= u["y"] <= rect_y2:
                            if u not in selected_units:
                                selected_units.append(u)

                is_dragging = False
                selection_start = None

    # Wave spawning logic
    if level_state == "playing":
        if wave_active:
            wave_spawn_timer += 1
            spawn_interval = max(20, 40 - wave_number * 2)
            if wave_spawn_timer >= spawn_interval and enemies_to_spawn:
                spawn_next_enemy()
                wave_spawn_timer = 0
            if not enemies_to_spawn and not enemies:
                wave_active = False
                level_data = LEVELS[current_level - 1]
                if wave_number >= level_data["waves"]:
                    check_level_complete()
                else:
                    wave_cooldown = 120
        else:
            if wave_cooldown > 0:
                wave_cooldown -= 1
            elif level_state == "playing":
                next_wave()

    # Resource Generation
    resource_timer += 1
    if resource_timer >= 60:
        gold += 5 * town_hall_lvl
        elixir += 5 * town_hall_lvl
        for b in player_buildings:
            if b["type"] == "gold_mine":
                gold += b["level"] * 12
                spawn_particles(b["x"] + 27, b["y"], GOLD_DARK, 2)
            if b["type"] == "elixir_collector":
                elixir += b["level"] * 12
                spawn_particles(b["x"] + 27, b["y"], ELIXIR_DARK, 2)
        resource_timer = 0

    # Update Player Units
    for p in player_units:
        p["walk_frame"] += 0.05
        if p["attack_timer"] > 0:
            p["attack_timer"] -= 1

        if p["attack_target"]:
            if p["attack_target"] in enemies:
                ex, ey = p["attack_target"]["x"], p["attack_target"]["y"]
                d = dist(p["x"], p["y"], ex, ey)
                if d > p["range"]:
                    angle = math.atan2(ey - p["y"], ex - p["x"])
                    p["x"] += math.cos(angle) * p["speed"]
                    p["y"] += math.sin(angle) * p["speed"]
                    p["angle"] = angle
                else:
                    if p["attack_timer"] == 0:
                        p["attack_target"]["hp"] -= p["damage"]
                        p["attack_timer"] = p["attack_cooldown"]
                        spawn_particles(ex, ey, (255, 200, 50), 3)
                        if p["attack_target"]["hp"] <= 0:
                            enemies.remove(p["attack_target"])
                            spawn_particles(ex, ey, ENEMY_COLOR, 10)
                            gold += 10
                            p["attack_target"] = None
            else:
                p["attack_target"] = None

        if p["target_x"] is not None and not p["attack_target"]:
            d = dist(p["x"], p["y"], p["target_x"], p["target_y"])
            if d > 5:
                angle = math.atan2(p["target_y"] - p["y"], p["target_x"] - p["x"])
                p["x"] += math.cos(angle) * p["speed"]
                p["y"] += math.sin(angle) * p["speed"]
                p["angle"] = angle
            else:
                p["target_x"] = p["target_y"] = None

        if not p["attack_target"] and not p.get("target_x"):
            nearest = None
            nearest_d = 150
            for e in enemies:
                d = dist(p["x"], p["y"], e["x"], e["y"])
                if d < nearest_d:
                    nearest_d = d
                    nearest = e
            if nearest:
                p["attack_target"] = nearest

        if p["target_x"] is None and not p["attack_target"]:
            p["x"] += math.cos(p["angle"]) * p["speed"] * 0.3
            p["y"] += math.sin(p["angle"]) * p["speed"] * 0.3
            if p["x"] > SCREEN_WIDTH - 100 or p["x"] < 120 or p["y"] > SCREEN_HEIGHT - 50 or p["y"] < 180:
                p["angle"] += math.pi
                p["x"] = max(120, min(SCREEN_WIDTH - 100, p["x"]))
                p["y"] = max(180, min(SCREEN_HEIGHT - 50, p["y"]))

    # Update Enemies
    for e in enemies[:]:
        e["walk_frame"] += 0.05
        if e["attack_timer"] > 0:
            e["attack_timer"] -= 1

        target_building = None
        target_building_dist = 99999
        for b in player_buildings:
            d = dist(e["x"], e["y"], b["x"], b["y"])
            if d < target_building_dist:
                target_building_dist = d
                target_building = b

        th_dist = dist(e["x"], e["y"], 70, 360)
        if th_dist < target_building_dist:
            target_building = None
            target_building_dist = th_dist

        if th_dist < 40:
            if e["attack_timer"] == 0:
                e["attack_timer"] = e["attack_cooldown"]
                if not hasattr(e, "_th_hit"):
                    e._th_hit = 0
                e._th_hit += 1
                spawn_particles(70, 360, (255, 100, 50), 5)
                if e._th_hit >= 20:
                    spawn_particles(70, 360, RED_ALERT, 20)
                    camera_shake = 8
                    e._th_hit = 0
                    gold -= 50
                    elixir -= 50
            continue

        if target_building and target_building_dist < 35:
            if e["attack_timer"] == 0:
                e["attack_timer"] = e["attack_cooldown"]
                b_key = id(target_building)
                if b_key not in building_hp:
                    building_hp[b_key] = {"hp": 200, "max_hp": 200}
                building_hp[b_key]["hp"] -= e["damage"]
                spawn_particles(target_building["x"] + 27, target_building["y"] + 27, (255, 100, 50), 4)
                if building_hp[b_key]["hp"] <= 0:
                    player_buildings.remove(target_building)
                    spawn_particles(target_building["x"] + 27, target_building["y"] + 27, RED_ALERT, 15)
                    camera_shake = 5
            continue

        nearest_unit = None
        nearest_unit_d = 40
        for p in player_units:
            d = dist(e["x"], e["y"], p["x"], p["y"])
            if d < nearest_unit_d:
                nearest_unit_d = d
                nearest_unit = p
        if nearest_unit:
            if e["attack_timer"] == 0:
                e["attack_timer"] = e["attack_cooldown"]
                nearest_unit["hp"] -= e["damage"]
                spawn_particles(nearest_unit["x"], nearest_unit["y"], RED_ALERT, 4)
                if nearest_unit["hp"] <= 0:
                    player_units.remove(nearest_unit)
                    selected_units[:] = [u for u in selected_units if u in player_units]
                    spawn_particles(nearest_unit["x"], nearest_unit["y"], (200, 200, 200), 10)
            continue

        if target_building:
            angle = math.atan2(target_building["y"] - e["y"], target_building["x"] - e["x"])
        else:
            angle = math.atan2(360 - e["y"], 70 - e["x"])
        e["angle"] = angle
        e["x"] += math.cos(angle) * e["speed"]
        e["y"] += math.sin(angle) * e["speed"]

        if e["x"] < -50 or e["x"] > SCREEN_WIDTH + 50 or e["y"] < 100 or e["y"] > SCREEN_HEIGHT + 50:
            enemies.remove(e)

    # Update Particles
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.05
        p["life"] -= 1
        p["size"] *= 0.97
        if p["life"] <= 0 or p["size"] < 0.5:
            particles.remove(p)

    # Camera shake decay
    if camera_shake > 0:
        camera_shake *= 0.85
        if camera_shake < 0.5:
            camera_shake = 0

    shake_x = random.randint(-int(camera_shake), int(camera_shake)) if camera_shake > 1 else 0
    shake_y = random.randint(-int(camera_shake), int(camera_shake)) if camera_shake > 1 else 0

    # === DRAWING ===
    th_x, th_y = 20 + shake_x, 270 + shake_y
    th_color = (84, 110, 122) if town_hall_lvl == 1 else (192, 57, 43)
    th_trim = GOLD_THEME if town_hall_lvl == 2 else (100, 100, 100)

    pygame.draw.rect(screen, (20, 30, 20), (th_x - 5, th_y + 10, 130, 200), border_radius=4)
    pygame.draw.rect(screen, th_color, (th_x, th_y, 120, 190), border_radius=4)
    roof_points = [(th_x - 10, th_y + 20), (th_x + 60, th_y - 20), (th_x + 130, th_y + 20)]
    pygame.draw.polygon(screen, th_trim, roof_points)
    pygame.draw.polygon(screen, WHITE, roof_points, 2)
    pygame.draw.rect(screen, GOLD_BAR, (th_x + 40, th_y + 120, 40, 70), border_radius=3)
    pygame.draw.circle(screen, WHITE, (th_x + 70, th_y + 160), 3)
    for wx, wy in [(th_x + 15, th_y + 50), (th_x + 80, th_y + 50)]:
        pygame.draw.rect(screen, (200, 220, 240), (wx, wy, 20, 25), border_radius=2)
        pygame.draw.rect(screen, th_trim, (wx, wy, 20, 25), 2)
    flag_x = th_x + 60
    flag_y = th_y - 20
    pygame.draw.line(screen, WOOD_BROWN, (flag_x, flag_y), (flag_x, flag_y + 40), 3)
    flag_color = (192, 57, 43) if town_hall_lvl == 2 else GOLD_THEME
    flag_pts = [(flag_x, flag_y), (flag_x + 30, flag_y + 8), (flag_x, flag_y + 16)]
    pygame.draw.polygon(screen, flag_color, flag_pts)
    draw_text(f"Lvl {town_hall_lvl}", font_xs, GOLD_BAR, th_x + 40, th_y + 5, shadow=True)
    if town_hall_lvl == 2:
        glow_surf = pygame.Surface((140, 220), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (192, 57, 43, 30), (0, 0, 140, 220), border_radius=4)
        screen.blit(glow_surf, (th_x - 10, th_y - 10))

    # Draw Buildings
    for b in player_buildings:
        bx, by = b["x"] + shake_x, b["y"] + shake_y
        b_key = id(b)
        hp_val = building_hp.get(b_key, {}).get("hp", 200)
        max_hp = building_hp.get(b_key, {}).get("max_hp", 200)

        if b["type"] == "gold_mine":
            w, h = 55, 55
            b_color = GOLD_THEME
            pygame.draw.rect(screen, (20, 40, 20), (bx + 5, by + 5, w, h), border_radius=4)
            pygame.draw.rect(screen, b_color, (bx, by, w, h), border_radius=4)
            roof_pts = [(bx - 5, by + 8), (bx + w // 2, by - 8), (bx + w + 5, by + 8)]
            pygame.draw.polygon(screen, GOLD_DARK, roof_pts)
            pygame.draw.polygon(screen, GOLD_BAR, roof_pts, 2)
            pygame.draw.arc(screen, (60, 40, 10), (bx + 17, by + 30, 20, 24), 0, math.pi, 3)
            pygame.draw.rect(screen, WOOD_BROWN, (bx + 12, by - 5, 30, 14), border_radius=2)
            draw_text(f"L{b['level']}", font_xs, GOLD_BAR, bx + 17, by - 4, shadow=True)
            if random.random() < 0.1:
                spawn_particles(bx + random.randint(5, 50), by + random.randint(5, 50), GOLD_BAR, 1)

        elif b["type"] == "elixir_collector":
            w, h = 55, 55
            b_color = ELIXIR_THEME
            pygame.draw.rect(screen, (20, 30, 40), (bx + 5, by + 5, w, h), border_radius=8)
            pygame.draw.rect(screen, b_color, (bx, by, w, h), border_radius=8)
            pygame.draw.ellipse(screen, ELIXIR_DARK, (bx + 5, by - 8, w - 10, 20))
            pygame.draw.ellipse(screen, ELIXIR_BAR, (bx + 5, by - 8, w - 10, 20), 2)
            pygame.draw.circle(screen, ELIXIR_BAR, (bx + w // 2, by + h // 2), 12)
            pygame.draw.circle(screen, WHITE, (bx + w // 2, by + h // 2), 4)
            pygame.draw.rect(screen, WOOD_BROWN, (bx + 12, by - 5, 30, 14), border_radius=2)
            draw_text(f"L{b['level']}", font_xs, ELIXIR_BAR, bx + 17, by - 4, shadow=True)
            if random.random() < 0.1:
                spawn_particles(bx + random.randint(5, 50), by + random.randint(5, 50), ELIXIR_BAR, 1)

        else:
            w, h = 24, 55
            pygame.draw.rect(screen, (20, 30, 20), (bx + 3, by + 3, w, h))
            for row in range(5):
                wy2 = by + row * 11
                wx2 = bx + (row % 2) * 6
                stone_color = (WALL_THEME[0] + row * 5, WALL_THEME[1] + row * 3, WALL_THEME[2])
                pygame.draw.rect(screen, stone_color, (wx2, wy2, w, 10))
                pygame.draw.rect(screen, WALL_LIGHT, (wx2, wy2, w, 10), 1)
            for c in range(3):
                cx = bx + c * 8
                pygame.draw.rect(screen, WALL_THEME, (cx, by - 5, 6, 5))
                pygame.draw.rect(screen, WALL_LIGHT, (cx, by - 5, 6, 5), 1)

        pygame.draw.rect(screen, WHITE, (bx, by, w, h), 2)

        if b_key in building_hp:
            hp_ratio = building_hp[b_key]["hp"] / building_hp[b_key]["max_hp"]
            bar_w = w
            bar_h = 3
            bar_x = bx
            bar_y = by - 8
            pygame.draw.rect(screen, BLACK, (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
            hp_color = GREEN_HIGHLIGHT if hp_ratio > 0.5 else (RED_ALERT if hp_ratio < 0.25 else GOLD_BAR)
            pygame.draw.rect(screen, hp_color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

    # Placement Preview
    if placement_mode and mouse_y > 145:
        pv_x = mouse_x - 27
        pv_y = mouse_y - 27
        pv_w, pv_h = (55, 55) if placement_mode != "wall" else (24, 55)
        valid = is_valid_placement(pv_x, pv_y, pv_w, pv_h)
        preview_surf = pygame.Surface((pv_w, pv_h), pygame.SRCALPHA)
        preview_surf.fill((0, 255, 0, 40) if valid else (255, 0, 0, 40))
        pygame.draw.rect(preview_surf, (0, 255, 0, 160) if valid else (255, 0, 0, 160), (0, 0, pv_w, pv_h), 2)
        screen.blit(preview_surf, (pv_x + shake_x, pv_y + shake_y))
        label = {"gold_mine": "Gold Mine", "elixir_collector": "Elixir Collector", "wall": "Wall"}
        draw_text(label.get(placement_mode, ""), font_xs, WHITE, pv_x + shake_x, pv_y + shake_y - 12, shadow=True)
        draw_text("Click to place | Right-click/Esc cancel", font_xs, TEXT_MUTED, SCREEN_WIDTH // 2 - 100, 148, shadow=True)

    # Draw Player Units
    for p in player_units:
        ux, uy = int(p["x"]) + shake_x, int(p["y"]) + shake_y
        col = (230, 126, 34) if p["type"] == "barbarian" else (52, 152, 219)
        dark_col = (180, 80, 10) if p["type"] == "barbarian" else (30, 100, 180)

        if p in selected_units:
            pygame.draw.circle(screen, SELECTION_COLOR, (ux, uy), 14, 2)

        pygame.draw.ellipse(screen, (15, 40, 12), (ux - 10, uy + 6, 20, 8))
        bob = math.sin(p["walk_frame"] * 3) * 2
        pygame.draw.circle(screen, col, (ux, uy + int(bob)), 9)
        pygame.draw.circle(screen, (min(255, col[0] + 60), min(255, col[1] + 60), min(255, col[2] + 60)), (ux - 2, uy - 3 + int(bob)), 4)

        if p["type"] == "barbarian":
            weapon_x = ux + 8
            weapon_y = uy - 3 + int(bob)
            swing = math.sin(p["walk_frame"] * 2) * 3
            pygame.draw.line(screen, (150, 150, 150), (weapon_x, weapon_y), (weapon_x + 5, weapon_y - 5 + swing), 2)
            pygame.draw.line(screen, dark_col, (weapon_x + 3, weapon_y - 3 + swing), (weapon_x + 8, weapon_y - 8 + swing), 3)
            pygame.draw.circle(screen, dark_col, (ux - 5, uy + int(bob)), 4)
            pygame.draw.circle(screen, WHITE, (ux - 5, uy + int(bob)), 4, 1)
        else:
            staff_x = ux + 7
            staff_y = uy - 5 + int(bob)
            pygame.draw.line(screen, (100, 60, 30), (staff_x, staff_y + 10), (staff_x, staff_y - 5), 2)
            orb_glow = abs(math.sin(game_time * 0.05)) * 20
            try:
                pygame.draw.circle(screen, (100, 200, 255, int(orb_glow)), (staff_x, staff_y - 5), 5 + int(orb_glow * 0.2))
            except:
                pygame.draw.circle(screen, (100, 200, 255), (staff_x, staff_y - 5), 5)
            pygame.draw.circle(screen, WHITE, (staff_x, staff_y - 5), 3)

        hp_ratio = p["hp"] / p["max_hp"]
        bar_w = 20
        bar_h = 3
        bar_x = ux - bar_w // 2
        bar_y = uy - 16 + int(bob)
        pygame.draw.rect(screen, BLACK, (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        hp_color = GREEN_HIGHLIGHT if hp_ratio > 0.5 else (RED_ALERT if hp_ratio < 0.25 else GOLD_BAR)
        pygame.draw.rect(screen, hp_color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

    # Draw Enemies
    for e in enemies:
        ux, uy = int(e["x"]) + shake_x, int(e["y"]) + shake_y
        size = e["size"]
        col = ENEMY_COLOR
        dark_col = ENEMY_DARK

        pygame.draw.ellipse(screen, (15, 20, 12), (ux - size, uy + size // 2, size * 2, size // 2))
        bob = math.sin(e["walk_frame"] * 3) * 2

        pygame.draw.circle(screen, col, (ux, uy + int(bob)), size)
        pygame.draw.circle(screen, dark_col, (ux - 2, uy - 2 + int(bob)), size - 3)

        eye_color = (255, 200, 50) if e["type"] == "goblin" else (255, 50, 50)
        pygame.draw.circle(screen, eye_color, (ux - 3, uy - 2 + int(bob)), 2)
        pygame.draw.circle(screen, eye_color, (ux + 3, uy - 2 + int(bob)), 2)

        if e["type"] == "ogre":
            pygame.draw.circle(screen, (60, 30, 10), (ux, uy - size + int(bob)), size // 2)
            pygame.draw.circle(screen, dark_col, (ux, uy - size + int(bob)), size // 2, 1)
        elif e["type"] == "raider":
            pygame.draw.line(screen, (100, 100, 100), (ux + size, uy - 2 + int(bob)), (ux + size + 6, uy - 6 + int(bob)), 2)
            pygame.draw.line(screen, dark_col, (ux, uy - size + int(bob)), (ux + 3, uy - size - 4 + int(bob)), 2)

        hp_ratio = e["hp"] / e["max_hp"]
        bar_w = size * 2 + 4
        bar_h = 3
        bar_x = ux - bar_w // 2
        bar_y = uy - size - 6 + int(bob)
        pygame.draw.rect(screen, BLACK, (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        hp_color = GREEN_HIGHLIGHT if hp_ratio > 0.5 else (RED_ALERT if hp_ratio < 0.25 else GOLD_BAR)
        pygame.draw.rect(screen, hp_color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

    # Selection box
    if is_dragging and selection_start:
        sx, sy = selection_start
        ex, ey = pygame.mouse.get_pos()
        rect_x = min(sx, ex)
        rect_y = min(sy, ey)
        rect_w = abs(ex - sx)
        rect_h = abs(ey - sy)
        s_surf = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
        s_surf.fill((0, 255, 100, 20))
        pygame.draw.rect(s_surf, (0, 255, 100, 160), (0, 0, rect_w, rect_h), 2)
        screen.blit(s_surf, (rect_x + shake_x, rect_y + shake_y))

    # Draw Particles
    for p in particles:
        alpha = int((p["life"] / p["max_life"]) * 255)
        size = max(1, int(p["size"]))
        try:
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color = (*p["color"], alpha)
            pygame.draw.circle(surf, color, (size, size), size)
            screen.blit(surf, (int(p["x"]) + shake_x - size, int(p["y"]) + shake_y - size))
        except:
            pass

    # === UI PANEL ===
    ui_x, ui_y = 15, 15
    ui_w, ui_h = SCREEN_WIDTH - 30, 125
    draw_rounded_rect(screen, UI_MAIN_BG, (ui_x, ui_y, ui_w, ui_h))
    pygame.draw.rect(screen, UI_BORDER, (ui_x, ui_y, ui_w, ui_h), 2, border_radius=6)

    # Gold Section
    icon_size = 20
    pygame.draw.circle(screen, GOLD_THEME, (55, 38), icon_size // 2)
    draw_text("G", font_md, WHITE, 49, 31)
    draw_text("GOLD RESERVE", font_xs, TEXT_MUTED, 72, 26)
    pygame.draw.rect(screen, BAR_BG, (50, 48, 170, 14), border_radius=3)
    gold_fill = min(170, max(0, (gold / 2000) * 170))
    if gold_fill > 0:
        draw_rounded_rect(screen, GOLD_BAR, (50, 48, int(gold_fill), 14))
    draw_text(f"{int(gold)} / 2000", font_sm, WHITE, 55, 66, shadow=True)

    # Elixir Section
    pygame.draw.circle(screen, ELIXIR_THEME, (270, 38), icon_size // 2)
    draw_text("E", font_md, WHITE, 264, 31)
    draw_text("ELIXIR STOCK", font_xs, TEXT_MUTED, 287, 26)
    pygame.draw.rect(screen, BAR_BG, (265, 48, 170, 14), border_radius=3)
    elixir_fill = min(170, max(0, (elixir / 2000) * 170))
    if elixir_fill > 0:
        draw_rounded_rect(screen, ELIXIR_BAR, (265, 48, int(elixir_fill), 14))
    draw_text(f"{int(elixir)} / 2000", font_sm, WHITE, 270, 66, shadow=True)

    # Center: Empire Status
    level_data = LEVELS[current_level - 1]
    if level_state == "playing":
        status_text = f"Level {current_level}: {level_data['name']} - Wave {wave_number}/{level_data['waves']}"
    elif level_state == "complete":
        status_text = f"Level {current_level} COMPLETE! Press ENTER for next level"
    elif level_state == "transition":
        status_text = f"Preparing Level {current_level}..."
    elif level_state == "won":
        status_text = "YOU WIN! All levels completed!"
    else:
        status_text = f"Level {current_level}: {level_data['name']}"
    draw_text("EMPIRE COMMAND", font_xs, TEXT_MUTED, 460, 22)
    draw_text(status_text, font_md, GOLD_THEME, 460, 40, shadow=True)
    draw_text(f"Town Hall Level {town_hall_lvl}", font_xs, TEXT_MUTED, 460, 62)

    # Age progress bar
    if town_hall_lvl == 1:
        draw_text("Next Age: 300G / 300E", font_xs, TEXT_MUTED, 460, 80)
        progress = min(1.0, (min(gold, elixir) / 300) if min(gold, elixir) < 300 else 1.0)
        pygame.draw.rect(screen, BAR_BG, (460, 96, 200, 8), border_radius=4)
        if progress > 0:
            draw_rounded_rect(screen, GOLD_THEME, (460, 96, int(200 * progress), 8))
    else:
        draw_text("AGE MAXIMIZED", font_sm, GOLD_THEME, 460, 85)

    # Right Side: Action Commands
    cmd_x = 740
    cmds = [
        ("[1] Recruit Barbarian", "25 Elixir", (230, 126, 34)),
        ("[2] Recruit Blue Wizard", "50 Elixir", (52, 152, 219)),
    ]
    mine = next((b for b in player_buildings if b["type"] == "gold_mine"), None)
    collector = next((b for b in player_buildings if b["type"] == "elixir_collector"), None)

    if not mine:
        cmds.append(("[G] Build Gold Mine", "100 Gold", GOLD_THEME))
    elif mine["level"] < 5:
        cmds.append((f"[G] Upgrade Mine Lv.{mine['level']}", f"{mine['level']*150} Gold", GOLD_THEME))
    else:
        cmds.append(("[G] Gold Mine MAXED", "", TEXT_MUTED))

    if not collector:
        cmds.append(("[E] Build Elixir Collect", "100 Gold", ELIXIR_THEME))
    elif collector["level"] < 5:
        cmds.append((f"[E] Upgrade Collect Lv.{collector['level']}", f"{collector['level']*150} Gold", ELIXIR_THEME))
    else:
        cmds.append(("[E] Collector MAXED", "", TEXT_MUTED))

    cmds.append(("[W] Stone Wall", "50 Gold", WALL_THEME))
    if town_hall_lvl == 1:
        cmds.append(("[U] Upgrade Age", "300G / 300E", GOLD_THEME))
    else:
        cmds.append(("[U] Age MAXED", "", TEXT_MUTED))

    for i, (label, cost, color) in enumerate(cmds):
        cy = 22 + i * 20
        if i < 2:
            icon_rect = (cmd_x - 5, cy - 2, 155, 18)
            draw_rounded_rect(screen, (35, 50, 65), icon_rect, 3)
        draw_text(label, font_xs, WHITE, cmd_x, cy, shadow=True)
        if cost:
            draw_text(cost, font_xs, color, cmd_x + 155, cy, shadow=True)

    # Bottom shortcut bar
    bar_y = SCREEN_HEIGHT - 35
    pygame.draw.rect(screen, UI_MAIN_BG, (15, bar_y, SCREEN_WIDTH - 30, 25), border_radius=4)
    draw_text("[1]Barbarian [2]Wizard [G]Mine [E]Elixir [W]Wall [U]Upgrade | Drag:Select Shift+Click:Add R-Click:Move/Attack", font_xs, TEXT_MUTED, 30, SCREEN_HEIGHT - 28)

    # === MINIMAP ===
    mm_x, mm_y = SCREEN_WIDTH - 155, SCREEN_HEIGHT - 165
    mm_w, mm_h = 140, 125
    draw_rounded_rect(screen, (10, 15, 20, 200), (mm_x, mm_y, mm_w, mm_h))
    pygame.draw.rect(screen, UI_BORDER, (mm_x, mm_y, mm_w, mm_h), 1, border_radius=4)
    draw_text("MINIMAP", font_xs, TEXT_MUTED, mm_x + 5, mm_y + 2)

    def to_minimap(gx, gy):
        rx = mm_x + 10 + (gx / SCREEN_WIDTH) * (mm_w - 20)
        ry = mm_y + 14 + ((gy - 140) / (SCREEN_HEIGHT - 140)) * (mm_h - 20)
        return int(rx), int(ry)

    for b in player_buildings:
        mx, my = to_minimap(b["x"], b["y"])
        if b["type"] == "gold_mine":
            pygame.draw.rect(screen, GOLD_THEME, (mx - 2, my - 2, 4, 4))
        elif b["type"] == "elixir_collector":
            pygame.draw.rect(screen, ELIXIR_THEME, (mx - 2, my - 2, 4, 4))
        else:
            pygame.draw.rect(screen, WALL_THEME, (mx - 2, my - 2, 4, 4))

    th_mx, th_my = to_minimap(70, 360)
    pygame.draw.rect(screen, (192, 57, 43) if town_hall_lvl == 2 else GOLD_THEME, (th_mx - 3, th_my - 3, 6, 6))

    for p in player_units:
        mx, my = to_minimap(p["x"], p["y"])
        col = (230, 126, 34) if p["type"] == "barbarian" else (52, 152, 219)
        screen.set_at((mx, my), col)

    for e in enemies:
        mx, my = to_minimap(e["x"], e["y"])
        screen.set_at((mx, my), (255, 50, 50))

    view_rect = pygame.Rect(mm_x + 10, mm_y + 14, mm_w - 20, mm_h - 20)
    pygame.draw.rect(screen, (255, 255, 255, 60), view_rect, 1)

    # === STATS PANEL ===
    stat_x = SCREEN_WIDTH - 155
    stat_y = 145
    stat_w = 140
    stat_h = 125
    draw_rounded_rect(screen, (15, 20, 30, 200), (stat_x, stat_y, stat_w, stat_h))
    pygame.draw.rect(screen, UI_BORDER, (stat_x, stat_y, stat_w, stat_h), 1, border_radius=4)
    draw_text("KINGDOM STATS", font_xs, TEXT_MUTED, stat_x + 5, stat_y + 3)
    draw_text(f"Level: {current_level}/{max_level}", font_xs, WHITE, stat_x + 5, stat_y + 20)
    draw_text(f"Units: {len(player_units)}", font_xs, WHITE, stat_x + 5, stat_y + 36)
    draw_text(f"Buildings: {len(player_buildings)}", font_xs, WHITE, stat_x + 5, stat_y + 52)
    total_gold_rate = town_hall_lvl * 5 + sum(b["level"] * 12 for b in player_buildings if b["type"] == "gold_mine")
    total_elixir_rate = town_hall_lvl * 5 + sum(b["level"] * 12 for b in player_buildings if b["type"] == "elixir_collector")
    draw_text(f"Gold/sec: {total_gold_rate}", font_xs, GOLD_BAR, stat_x + 5, stat_y + 68)
    draw_text(f"Elixir/sec: {total_elixir_rate}", font_xs, ELIXIR_BAR, stat_x + 5, stat_y + 84)

    if wave_active:
        remaining = len(enemies) + len(enemies_to_spawn)
        draw_text(f"Hostiles: {remaining}", font_xs, (255, 150, 50), stat_x + 5, stat_y + 104)
    elif level_state == "complete":
        draw_text("LEVEL DONE!", font_xs, GREEN_HIGHLIGHT, stat_x + 5, stat_y + 104)
    else:
        draw_text("Preparing...", font_xs, GREEN_HIGHLIGHT, stat_x + 5, stat_y + 104)

    # Level complete overlay
    if level_state == "complete":
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))
        draw_text(f"LEVEL {current_level} COMPLETE!", font_xxl, GREEN_HIGHLIGHT, SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 50, shadow=True)
        draw_text(f"+200 Gold, +200 Elixir", font_lg, GOLD_THEME, SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 10, shadow=True)
        draw_text("Press ENTER for next level", font_md, WHITE, SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 50, shadow=True)

    if level_state == "won":
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        draw_text("YOU WIN!", font_xxl, GOLD_THEME, SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 60, shadow=True)
        draw_text("All 8 Levels Complete!", font_lg, WHITE, SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2, shadow=True)
        draw_text("Your Kingdom Stands Strong!", font_md, GOLD_BAR, SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 + 50, shadow=True)

    pygame.display.flip()

pygame.quit()
sys.exit()
