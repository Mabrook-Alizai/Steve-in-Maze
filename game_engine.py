import pygame
import random
import heapq
import math
import os
from settings import *

class MenuState:
    """THE FACE: Handles the Main Menu logic, animations, and input."""
    def __init__(self, sound_manager):
        self.sound_manager = sound_manager
        self.scroll_x = 0
        self.scroll_speed = 1.0 
        self.start_ticks = pygame.time.get_ticks()
        
        # Start Menu Music (Standard)
        self.sound_manager.play_bgm('menu')
        
        self.options = [
            "Easy", 
            "Normal", 
            "Hard", 
            "VS AI", 
            "Easy Peasy",
            "Quit Game"
        ]
        
        self.descriptions = [
            "Tiny 12-row maze. Perfect for warming up.",
            "Standard 18-row maze. A balanced challenge.",
            "Massive 25-row maze. Don't get lost!",
            "Race a Bot! Collect items & steal points.",
            "Very easy and nothing to worry about, hehe",
            "Exit to Desktop."
        ]
        
        self.selected_index = 0
        
        self.splash_text = random.choice([
            "Swaza ma!", "Shai Shai ma kawa!", "Gaazara!", 
            "Don't hug Creepers!", "100% Python!", "Watch out for TNT!",
            "Nether Update!", "SLAIN BY ENDERMAN!", "Ghast incoming!"
        ])
        
        self.tips = [
            "Tip: Creepers explode if you get too close!",
            "Tip: Use Energy Drinks (2) to become invincible.",
            "Tip: Ender Pearls (1) teleport you to safety.",
            "Tip: In VS Mode, steal points by hitting the bot!",
            "Tip: Endermen teleport randomly. Watch out!",
            "Tip: Ghasts shoot where you ARE, not where you're going."
        ]
        self.current_tip = random.choice(self.tips)
        
        self.tip_state = "FADE_IN"
        self.tip_alpha = 0
        self.tip_timer = 0
        self.tip_display_duration = 300 
        self.tip_fade_speed = 5 

    def update(self):
        self.scroll_x += self.scroll_speed
        
        if self.tip_state == "FADE_IN":
            self.tip_alpha += self.tip_fade_speed
            if self.tip_alpha >= 255:
                self.tip_alpha = 255
                self.tip_state = "VISIBLE"
                self.tip_timer = 0
        elif self.tip_state == "VISIBLE":
            self.tip_timer += 1
            if self.tip_timer > self.tip_display_duration:
                self.tip_state = "FADE_OUT"
        elif self.tip_state == "FADE_OUT":
            self.tip_alpha -= self.tip_fade_speed
            if self.tip_alpha <= 0:
                self.tip_alpha = 0
                self.current_tip = random.choice(self.tips)
                self.tip_state = "FADE_IN"

    def handle_input(self, event):
        if event.key == pygame.K_UP:
            self.selected_index = (self.selected_index - 1) % len(self.options)
        elif event.key == pygame.K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.options)
        elif event.key == pygame.K_RETURN:
            return self.selected_index
        return None

class GameState:
    """THE BRAIN: Handles all logic, rules, AI moving, and grid management."""
    def __init__(self, rows, mode, sound_manager):
        self.mode = mode 
        self.sound = sound_manager
        
        # Start appropriate music logic
        if mode == "hell": self.sound.play_bgm('hell')
        else: self.sound.play_bgm('normal')

        # DYNAMIC GRID SIZING
        self.rows = rows
        available_height = SCREEN_HEIGHT - UI_HEIGHT
        self.cell_size = available_height // self.rows
        self.cols = SCREEN_WIDTH // self.cell_size
        if self.cols % 2 == 0: self.cols -= 1
        if self.rows % 2 == 0: self.rows -= 1 
        
        self.grid = []
        self.path_taken = []
        self.player_last_dir = (0, 0) 
        
        # Movement Logic
        self.move_timer = 0
        self.base_move_delay = 3
        self.move_delay = self.base_move_delay
        self.step_sound_timer = 0 
        
        # Buff/Debuff Timers (Frames)
        self.speed_boost_timer = 0
        self.ai_slow_timer = 0
        self.player_slow_timer = 0 
        self.ai_speed_boost_timer = 0
        self.invincible_timer = 0 
        
        # VS Mode Specifics
        self.has_key = False
        self.key_spawned = False
        self.has_shield = False
        self.heart_spawned = False
        self.game_time = 0 
        self.key_pos = None
        self.heart_pos = None
        
        # Hell Mode Inventory & Spawners
        self.pearl_count = 0
        self.has_energy_drink = False
        self.pearl_spawn_timer = 10 * FPS 
        self.drink_spawn_timer = 12 * FPS
        self.pearl_on_map = False
        self.drink_on_map = False
        self.high_score = 0
        
        # State Flags
        self.game_active = True
        self.game_won = False
        self.game_over_text = ""
        self.death_type = None 
        self.paused = False
        self.status_message = ""
        self.status_timer = 0
        
        # Entities
        self.user_score = 0
        self.rewards = [] 
        self.bots = []
        self.bombs = []
        self.creepers = [] 
        self.ghasts = [] 
        self.ghast_spawn_timer = 0 
        self.fire_charges = [] 
        self.enderman = None 
        self.explosion_marks = [] 
        
        # Solo Mode specific
        self.ai_path_display = []
        self.ai_draw_index = 0
        
        # Countdown Logic
        self.start_ticks = pygame.time.get_ticks()
        self.warmup_duration = 3000 if mode == "hell" else 5000
        self.is_warming_up = True if mode in ["vs_ai", "hell"] else False
        
        # Load High Score for Hell Mode
        if self.mode == "hell":
            self.load_high_score()

        # 1. Initialize & Generate
        self._init_grid()
        self._generate_maze(1, 1)
        self._create_loops()
        
        # 2. Set Start/End
        self.player_pos = [1, 1]
        self.grid[1][1] = 0
        self.path_taken.append(tuple(self.player_pos))
        
        self.goal_pos = [self.rows - 2, self.cols - 2]
        if self.grid[self.goal_pos[0]][self.goal_pos[1]] == 1:
             found = False
             for r in range(self.rows - 2, 0, -1):
                 for c in range(self.cols - 2, 0, -1):
                     if self.grid[r][c] == 0:
                         self.goal_pos = [r, c]
                         found = True
                         break
                 if found: break

        # 3. Setup Mode Specifics
        self._setup_entities()

    def _init_grid(self):
        for r in range(self.rows):
            row = []
            for c in range(self.cols): row.append(1) 
            self.grid.append(row)

    def _generate_maze(self, start_r, start_c):
        stack = [(start_r, start_c)]
        self.grid[start_r][start_c] = 0
        while stack:
            current_r, current_c = stack[-1]
            directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
            random.shuffle(directions)
            found_neighbor = False
            for dr, dc in directions:
                nr, nc = current_r + dr, current_c + dc
                if 0 < nr < self.rows - 1 and 0 < nc < self.cols - 1 and self.grid[nr][nc] == 1:
                    self.grid[current_r + dr // 2][current_c + dc // 2] = 0
                    self.grid[nr][nc] = 0
                    stack.append((nr, nc))
                    found_neighbor = True
                    break 
            if not found_neighbor: stack.pop()

    def _create_loops(self):
        num_walls_to_remove = (self.rows * self.cols) // 20 
        for _ in range(num_walls_to_remove):
            r = random.randint(1, self.rows - 2)
            c = random.randint(1, self.cols - 2)
            if self.grid[r][c] == 1: self.grid[r][c] = 0

    def _setup_entities(self):
        if self.mode == "vs_ai":
            # Bot initialized with speed 7 (faster) and cooldown field
            self.bots.append({'pos': [1, 1], 'path': [], 'timer': 0, 'state': 'THINKING', 'base_speed': 7, 'speed': 7, 'score': 0, 'cooldown': 0})
            self._generate_rewards(5)
        elif self.mode == "hell":
            start_r, start_c = 1, self.cols - 2
            while self.grid[start_r][start_c] == 1 and start_c > 0: start_c -= 1
            self.bots.append({'pos': [start_r, start_c], 'path': [], 'timer': 0, 'state': 'CHASING', 'base_speed': 11, 'speed': 11, 'repath_timer': 0, 'id': 0})
            self._generate_rewards(7) 
            self.spawn_creeper() 
            
    def load_high_score(self):
        try:
            with open("highscore.txt", "r") as f:
                self.high_score = int(f.read())
        except:
            self.high_score = 0

    def save_high_score(self):
        try:
            with open("highscore.txt", "w") as f:
                f.write(str(self.high_score))
        except:
            pass

    def _generate_rewards(self, count=1):
        if self.mode == "vs_ai":
            if self.game_time > 5 * FPS:
                choices = ['points', 'swiftness', 'slowness']
                weights = [90, 5, 5]
            else: choices = ['points']; weights = [100]
        else: choices = ['points']; weights = [100]

        added = 0
        attempts = 0
        while added < count and attempts < 1000:
            attempts += 1
            r = random.randint(1, self.rows - 2)
            c = random.randint(1, self.cols - 2)
            if self.grid[r][c] == 0:
                pos = (r, c)
                collision = False
                if pos == tuple(self.player_pos) or pos == tuple(self.goal_pos): collision = True
                if self.key_pos and pos == self.key_pos: collision = True
                if self.heart_pos and pos == self.heart_pos: collision = True
                for rew in self.rewards: 
                    if rew['pos'] == pos: collision = True
                if not collision:
                    rew_type = random.choices(choices, weights=weights, k=1)[0]
                    if rew_type == 'points':
                        pt_types = [{'color': PURPLE, 'val': 20}, {'color': ORANGE, 'val': 10}, {'color': PINK, 'val': 5}]
                        data = random.choice(pt_types)
                        self.rewards.append({'pos': pos, 'type': 'points', 'color': data['color'], 'val': data['val']})
                    else:
                        color = CYAN_POTION if rew_type == 'swiftness' else BROWN_POTION
                        self.rewards.append({'pos': pos, 'type': rew_type, 'color': color, 'val': 0})
                    added += 1

    def spawn_specific_item(self, item_type):
        for _ in range(100):
            r = random.randint(1, self.rows - 2)
            c = random.randint(1, self.cols - 2)
            pos = (r, c)
            if self.grid[r][c] == 0 and pos != tuple(self.player_pos) and pos != tuple(self.goal_pos):
                collision = False
                for rew in self.rewards:
                    if rew['pos'] == pos: collision = True
                if not collision:
                    if item_type == 'pearl':
                        self.rewards.append({'pos': pos, 'type': 'pearl', 'color': PEARL_COLOR, 'val': 0})
                        self.pearl_on_map = True
                    elif item_type == 'energy_drink':
                        self.rewards.append({'pos': pos, 'type': 'energy_drink', 'color': CYAN_POTION, 'val': 0})
                        self.drink_on_map = True
                    return

    def spawn_key(self):
        center_r, center_c = self.rows // 2, self.cols // 2
        for r in range(center_r - 5, center_r + 5):
            for c in range(center_c - 5, center_c + 5):
                if 0 < r < self.rows and 0 < c < self.cols and self.grid[r][c] == 0:
                    if (r,c) != tuple(self.player_pos):
                        self.key_pos = (r, c)
                        self.key_spawned = True
                        return

    def spawn_heart(self):
        for _ in range(50):
            r = random.randint(1, self.rows - 2)
            c = random.randint(1, self.cols - 2)
            if self.grid[r][c] == 0 and (r,c) != tuple(self.player_pos):
                self.heart_pos = (r, c)
                self.heart_spawned = True
                return

    def spawn_hell_bot(self):
        for _ in range(50):
            r = random.randint(1, self.rows - 2)
            c = random.randint(1, self.cols - 2)
            if self.grid[r][c] == 0:
                dist = abs(r - self.player_pos[0]) + abs(c - self.player_pos[1])
                if dist > 15:
                    self.bots.append({'pos': [r, c], 'path': [], 'timer': 0, 'state': 'CHASING', 'base_speed': 11, 'speed': 11, 'repath_timer': 0, 'id': len(self.bots)})
                    return

    def spawn_creeper(self):
        for _ in range(50):
            r = random.randint(1, self.rows - 2)
            c = random.randint(1, self.cols - 2)
            if self.grid[r][c] == 0 and (r,c) != tuple(self.player_pos):
                axis = random.choice([0, 1])
                self.creepers.append({'pos': [r, c], 'axis': axis, 'dir': 1, 'start_pos': [r, c], 'range': 10, 'timer': 0, 'speed': 15, 'fuse': 90, 'radius': 3, 'state': 'PATROL', 'blink_timer': 0})
                return

    def spawn_enderman(self):
        for _ in range(50):
            r = random.randint(1, self.rows - 2)
            c = random.randint(1, self.cols - 2)
            if self.grid[r][c] == 0 and (abs(r - self.player_pos[0]) + abs(c - self.player_pos[1]) > 5):
                self.enderman = {'pos': [r, c], 'duration': 10 * FPS, 'teleport_timer': 0, 'teleport_interval': int(1.5 * FPS)}
                return

    def spawn_ghast(self):
        side = random.randint(0, 3)
        if side == 0: start = (-5, random.randint(0, self.cols)); end = (self.rows + 5, random.randint(0, self.cols))
        elif side == 1: start = (random.randint(0, self.rows), self.cols + 5); end = (random.randint(0, self.rows), -5)
        elif side == 2: start = (self.rows + 5, random.randint(0, self.cols)); end = (-5, random.randint(0, self.cols))
        else: start = (random.randint(0, self.rows), -5); end = (random.randint(0, self.rows), self.cols + 5)
        mid_r, mid_c = self.rows // 2, self.cols // 2
        control = (mid_r + random.randint(-10, 10), mid_c + random.randint(-10, 10))
        self.ghasts.append({'p0': start, 'p1': control, 'p2': end, 't': 0.0, 'speed': 0.0015, 'pos': start, 'shoot_timer': random.randint(90, 120)})

    def spawn_fire_charge(self, start_pos, target_pos):
        sr, sc = start_pos; tr, tc = target_pos
        dr = tr - sr; dc = tc - sc
        magnitude = math.sqrt(dr*dr + dc*dc)
        if magnitude > 0:
            speed = 0.3
            vel_r = (dr / magnitude) * speed; vel_c = (dc / magnitude) * speed
            self.fire_charges.append({'pos': [sr, sc], 'velocity': [vel_r, vel_c]})

    def get_astar_path(self, start, end):
        start, end = tuple(start), tuple(end)
        queue = [(0, 0, start, [start])]; visited = set()
        while queue:
            f, g, current, path = heapq.heappop(queue)
            if current == end: return path
            if current in visited: continue
            visited.add(current)
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = current[0] + dr, current[1] + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr][nc] == 0:
                    h = abs(nr - end[0]) + abs(nc - end[1])
                    heapq.heappush(queue, (g + 1 + h, g + 1, (nr, nc), path + [(nr, nc)]))
        return []

    def use_pearl(self):
        if self.pearl_count > 0:
            self.pearl_count -= 1
            self.sound.play_sfx('pearl') 
            threats = []
            for b in self.bots: threats.append(tuple(b['pos']))
            for c in self.creepers: threats.append(tuple(c['pos']))
            if self.enderman: threats.append(tuple(self.enderman['pos']))
            best_spot = self.player_pos
            max_safety = -1
            for _ in range(20):
                r = random.randint(1, self.rows - 2); c = random.randint(1, self.cols - 2)
                if self.grid[r][c] == 0:
                    min_dist = float('inf')
                    for t in threats:
                        dist = abs(r - t[0]) + abs(c - t[1])
                        if dist < min_dist: min_dist = dist
                    if not threats: min_dist = 0 
                    if min_dist > max_safety: max_safety = min_dist; best_spot = [r, c]
            self.player_pos = best_spot

    def use_energy_drink(self):
        if self.has_energy_drink:
            self.has_energy_drink = False
            self.sound.play_sfx('drink') 
            self.invincible_timer = 6 * FPS 
            self.speed_boost_timer = 6 * FPS 

    def update(self):
        if self.paused or not self.game_active: return
        if self.is_warming_up:
            if pygame.time.get_ticks() - self.start_ticks > self.warmup_duration:
                self.is_warming_up = False
            return 
        self.game_time += 1

        if self.mode == "vs_ai":
            if self.game_time > 450 and not self.heart_spawned: self.spawn_heart()
            self.move_delay = self.base_move_delay
            if self.player_slow_timer > 0: self.player_slow_timer -= 1; self.move_delay = 8 
            elif self.speed_boost_timer > 0: self.speed_boost_timer -= 1; self.move_delay = 1 
            if self.ai_slow_timer > 0: self.ai_slow_timer -= 1; [bot.update({'speed': bot['base_speed'] + 15}) for bot in self.bots]
            elif self.ai_speed_boost_timer > 0: self.ai_speed_boost_timer -= 1; [bot.update({'speed': max(2, bot['base_speed'] - 4)}) for bot in self.bots]
            else: [bot.update({'speed': bot['base_speed']}) for bot in self.bots]

        if self.mode == "hell":
            if not self.pearl_on_map:
                self.pearl_spawn_timer -= 1
                if self.pearl_spawn_timer <= 0: self.spawn_specific_item('pearl'); self.pearl_spawn_timer = 10 * FPS 
            if not self.drink_on_map:
                self.drink_spawn_timer -= 1
                if self.drink_spawn_timer <= 0: self.spawn_specific_item('energy_drink'); self.drink_spawn_timer = 15 * FPS 
            if self.invincible_timer > 0: self.invincible_timer -= 1; self.move_delay = 1 
            else: self.move_delay = self.base_move_delay
            for b in self.bombs: b['timer'] -= 1
            self.bombs = [b for b in self.bombs if b['timer'] > 0]
            if self.ghast_spawn_timer > 0: self.ghast_spawn_timer -= 1
            if len(self.ghasts) < 2 and self.ghast_spawn_timer <= 0:
                chance = 0.002 if len(self.ghasts) == 0 else 0.0005
                if random.random() < chance: self.spawn_ghast(); self.ghast_spawn_timer = 13 * FPS

            for g in self.ghasts[:]:
                g['t'] += g['speed']
                if g['t'] > 1.0: self.ghasts.remove(g)
                else:
                    t = g['t']; u = 1 - t; tt = t * t; uu = u * u
                    r = (uu * g['p0'][0]) + (2 * u * t * g['p1'][0]) + (tt * g['p2'][0])
                    c = (uu * g['p0'][1]) + (2 * u * t * g['p1'][1]) + (tt * g['p2'][1])
                    g['pos'] = (r, c)
                    g['shoot_timer'] -= 1
                    if g['shoot_timer'] <= 0: self.spawn_fire_charge(g['pos'], self.player_pos); g['shoot_timer'] = random.randint(90, 120)

            for fc in self.fire_charges[:]:
                fc['pos'][0] += fc['velocity'][0]; fc['pos'][1] += fc['velocity'][1]
                fr, fc_col = fc['pos']
                if not (-10 < fr < self.rows + 10 and -10 < fc_col < self.cols + 10): self.fire_charges.remove(fc); continue
                dist_r = abs(fr - self.player_pos[0]); dist_c = abs(fc_col - self.player_pos[1])
                if math.sqrt(dist_r*dist_r + dist_c*dist_c) < 0.5 and self.invincible_timer <= 0:
                    self.game_active = False; self.game_won = False; self.death_type = "explosion"; self.game_over_text = "TRIED TO DODGE GHAST!"

            if self.enderman:
                self.enderman['duration'] -= 1; self.enderman['teleport_timer'] += 1
                if tuple(self.enderman['pos']) == tuple(self.player_pos) and self.invincible_timer <= 0:
                    self.game_active = False; self.game_won = False; self.death_type = "explosion"; self.game_over_text = "SLAIN BY ENDERMAN!"
                if self.enderman['teleport_timer'] >= self.enderman['teleport_interval']:
                    self.enderman['teleport_timer'] = 0
                    for _ in range(10):
                        r = random.randint(1, self.rows - 2); c = random.randint(1, self.cols - 2)
                        if self.grid[r][c] == 0: self.enderman['pos'] = [r, c]; break
                if self.enderman['duration'] <= 0: self.enderman = None
            else:
                if self.game_time > 10 * FPS and self.game_time % 90 == 0 and random.random() < 0.30: self.spawn_enderman()

            for c_idx, creep in enumerate(self.creepers):
                dist_r = abs(creep['pos'][0] - self.player_pos[0]); dist_c = abs(creep['pos'][1] - self.player_pos[1])
                in_radius = max(dist_r, dist_c) <= creep['radius']
                if in_radius:
                    creep['state'] = 'FUSE'; creep['fuse'] -= 1; creep['blink_timer'] = creep.get('blink_timer', 0) + 1
                    
                    if creep['fuse'] == 119:
                         self.sound.play_sfx('creeper', self.player_pos, creep['pos'])

                    if creep['fuse'] <= 0:
                        self.explosion_marks.append(tuple(creep['pos'])); self.creepers.pop(c_idx)
                        if in_radius and self.invincible_timer <= 0: self.game_active = False; self.game_won = False; self.death_type = "explosion"; self.game_over_text = "BLOWN UP BY CREEPER!"
                        continue
                else:
                    creep['state'] = 'PATROL'; 
                    if creep['fuse'] < 90: creep['fuse'] += 0.5 
                if creep['state'] == 'PATROL':
                    creep['timer'] += 1
                    if creep['timer'] >= creep['speed']:
                        creep['timer'] = 0
                        dr, dc = (1, 0) if creep['axis'] == 0 else (0, 1)
                        dr *= creep['dir']; dc *= creep['dir']
                        nr, nc = creep['pos'][0] + dr, creep['pos'][1] + dc
                        start_dist = abs(nr - creep['start_pos'][0]) + abs(nc - creep['start_pos'][1])
                        if (0 < nr < self.rows and 0 < nc < self.cols and self.grid[nr][nc] == 0 and start_dist <= creep['range']): creep['pos'] = [nr, nc]
                        else: creep['dir'] *= -1

        for i, bot in enumerate(self.bots):
            bot['timer'] += 1
            # Cooldown logic for VS AI
            if bot.get('cooldown', 0) > 0: bot['cooldown'] -= 1

            if self.mode == "vs_ai":
                if tuple(bot['pos']) == tuple(self.player_pos) and bot.get('cooldown', 0) <= 0:
                    if self.has_shield:
                        self.has_shield = False
                        self.game_over_text = "Shield Blocked Theft!"
                        bot['cooldown'] = 60 # IMMUNITY after hitting shield
                    else:
                        steal_amount = min(10, self.user_score); self.user_score -= steal_amount; bot['score'] += steal_amount
                        bot['cooldown'] = 60 # IMMUNITY after stealing

                if bot['state'] == 'THINKING' and bot['timer'] >= 30:
                    target = None; best_dist = float('inf')
                    for rew in self.rewards:
                        dist = abs(bot['pos'][0]-rew['pos'][0]) + abs(bot['pos'][1]-rew['pos'][1])
                        if dist < best_dist: best_dist, target = dist, rew['pos']
                    if not target: target = tuple(self.goal_pos)
                    bot['path'] = self.get_astar_path(bot['pos'], target); bot['path'].pop(0) if len(bot['path']) > 0 else None
                    bot['state'] = 'MOVING'; bot['timer'] = 0
                elif bot['state'] == 'MOVING' and bot['timer'] >= bot['speed']:
                    bot['timer'] = 0
                    if bot['path']:
                        bot['pos'] = list(bot['path'].pop(0))
                        for j in range(len(self.rewards)-1, -1, -1):
                            if self.rewards[j]['pos'] == tuple(bot['pos']):
                                r = self.rewards[j]
                                if r['type'] == 'points': bot['score'] += r['val']
                                elif r['type'] == 'swiftness': self.ai_speed_boost_timer = 5 * FPS
                                elif r['type'] == 'slowness': self.player_slow_timer = 5 * FPS
                                self.rewards.pop(j); bot['state'] = 'THINKING'
                        if bot['pos'] == self.goal_pos and bot['score'] > 0:
                            self.game_active = False; self.game_won = False; self.game_over_text = f"AI Wins! Score: {bot['score']}"
                    else: bot['state'] = 'THINKING'

            elif self.mode == "hell":
                if random.random() < 0.005: self.bombs.append({'pos': tuple(bot['pos']), 'timer': 15 * FPS})
                bot['repath_timer'] = bot.get('repath_timer', 0) + 1
                if bot['repath_timer'] > 10 or not bot['path']:
                    target = list(self.player_pos)
                    if i > 0:
                        pred_r = self.player_pos[0] + self.player_last_dir[0] * 4; pred_c = self.player_pos[1] + self.player_last_dir[1] * 4
                        pred_r = max(1, min(self.rows - 2, pred_r)); pred_c = max(1, min(self.cols - 2, pred_c))
                        if self.grid[pred_r][pred_c] == 0: target = [pred_r, pred_c]
                    bot['path'] = self.get_astar_path(bot['pos'], target); bot['path'].pop(0) if len(bot['path']) > 0 else None
                    bot['repath_timer'] = 0
                if bot['timer'] >= bot['speed']:
                    bot['timer'] = 0
                    if bot['path']:
                        bot['pos'] = list(bot['path'].pop(0))
                        if bot['pos'] == self.player_pos and self.invincible_timer <= 0:
                            self.game_active = False; self.game_won = False; self.death_type = "caught"; self.game_over_text = "CAUGHT! GAME OVER."

        if self.mode == "solo" and self.game_won:
             total = len(self.ai_path_display); self.ai_draw_index = min(total, self.ai_draw_index + max(1, total // (10*30)))
    
    def move_player(self, dx, dy):
        if self.paused or not self.game_active or self.is_warming_up: return
        self.player_last_dir = (dy, dx)
        new_r, new_c = self.player_pos[0] + dy, self.player_pos[1] + dx
        
        if self.grid[new_r][new_c] == 0:
            self.player_pos = [new_r, new_c]
            
            # Step Sound Control (Only play every 15 frames/steps to avoid spam)
            self.step_sound_timer += 1
            if self.step_sound_timer > 3: # Play sound every 4th movement update approx
                 self.sound.play_sfx('walk')
                 self.step_sound_timer = 0

            # Only record path in Solo mode
            if self.mode == "solo": self.path_taken.append((new_r, new_c))
            
            for b in self.bombs:
                if tuple(self.player_pos) == b['pos'] and self.invincible_timer <= 0:
                    self.game_active = False; self.game_won = False; self.death_type = "explosion"; self.game_over_text = "BOOM! YOU HIT A TNT."
            
            # Enderman Collision
            if self.mode == "hell" and self.enderman and tuple(self.player_pos) == tuple(self.enderman['pos']) and self.invincible_timer <= 0:
                self.game_active = False; self.game_won = False; self.death_type = "explosion"; self.game_over_text = "SLAIN BY ENDERMAN!"

            if self.mode == "vs_ai" and self.key_spawned and not self.has_key:
                if tuple(self.player_pos) == self.key_pos: self.has_key = True; self.key_pos = None 

            if self.mode == "vs_ai" and self.heart_spawned and not self.has_shield:
                if tuple(self.player_pos) == self.heart_pos: self.has_shield = True; self.heart_pos = None

            if self.mode in ["vs_ai", "hell"]:
                for i in range(len(self.rewards)-1, -1, -1):
                    if self.rewards[i]['pos'] == tuple(self.player_pos):
                        r = self.rewards[i]
                        if r['type'] == 'points':
                            self.user_score += r['val']
                            if self.mode == "hell":
                                if self.user_score > self.high_score:
                                    self.high_score = self.user_score
                                    self.save_high_score()
                            if self.mode == "vs_ai" and not self.key_spawned: self.spawn_key()
                        elif r['type'] == 'swiftness': self.speed_boost_timer = 5 * FPS 
                        elif r['type'] == 'slowness': self.ai_slow_timer = 5 * FPS 
                        elif r['type'] == 'pearl':
                            if self.pearl_count < 5: self.pearl_count += 1; self.pearl_on_map = False; self.pearl_spawn_timer = 10 * FPS
                        elif r['type'] == 'energy_drink':
                            if not self.has_energy_drink: self.has_energy_drink = True; self.drink_on_map = False; self.drink_spawn_timer = 15 * FPS
                        self.rewards.pop(i)
                        
                        if self.mode == "hell":
                            self._generate_rewards(1)
                            if r.get('color') == PURPLE: self.spawn_hell_bot()
                            elif r.get('color') == ORANGE: [bot.update({'speed': max(2, bot['speed'] - 1)}) for bot in self.bots]

            if self.player_pos == self.goal_pos:
                if self.mode == "solo":
                    self.game_won = True; self.death_type = "win"
                    self.ai_path_display = self.get_astar_path((1,1), self.goal_pos)
                    self.game_over_text = f"SOLVED! You: {len(self.path_taken)} | AI: {len(self.ai_path_display)}"
                elif self.mode == "vs_ai":
                    if self.has_key: 
                        if self.user_score > 0: self.game_active = False; self.game_won = True; self.death_type = "win"; self.game_over_text = f"You Win! Score: {self.user_score}"
                    else: pass 
                elif self.mode == "hell":
                    self.game_active = False; self.game_won = True; self.death_type = "win"; self.game_over_text = f"SURVIVED! Score: {self.user_score}"