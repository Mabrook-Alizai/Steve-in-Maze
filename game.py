import pygame
import sys
import heapq
import random
import math

# --- SETUP PYGAME FIRST TO GET SCREEN SIZE ---
pygame.init()

# Get the current resolution of the monitor
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Set Fullscreen Mode
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Mabrook's Maze: Nether Update")
clock = pygame.time.Clock()

# --- CONFIGURATION ---
# UI Height stays fixed, everything else scales
UI_HEIGHT = 80
FPS = 30 

# --- COLORS ---
WHITE = (255, 255, 255)
NETHER_FOG = (30, 0, 0)         
WALL_COLOR = (40, 40, 40)       
CYAN = (0, 255, 255)            
GREEN = (0, 255, 0)             
RED = (255, 0, 0)               
YELLOW = (255, 255, 0)          
BLUE_MENU = (100, 149, 237)
COUNTDOWN_COLOR = (255, 215, 0)
HELL_RED = (139, 0, 0)  
OVERLAY_BG = (0, 0, 0, 200) 
BOMB_COLOR = (10, 10, 10)       
BOMB_FUSE = (255, 69, 0)
CREEPER_AURA = (0, 0, 0, 100)   # Transparent black for detection zone
EXPLOSION_MARK = (10, 0, 0, 180) # Dark scorched earth
ENDERMAN_PURPLE = (148, 0, 211) # Bright Purple for outline
GHAST_SHADOW = (0, 0, 0, 100)   # Shadow for flying ghast

# Reward Colors 
PURPLE = (128, 0, 128)  
ORANGE = (255, 165, 0)  
PINK = (255, 105, 180) 
# Potion Colors (Fallback)
CYAN_POTION = (0, 255, 255)
BROWN_POTION = (139, 69, 19)
RED_HEART = (255, 0, 0)
GOLD_KEY = (255, 215, 0)

class GameState:
    """THE BRAIN: Handles all logic, rules, AI moving, and grid management."""
    def __init__(self, rows, mode):
        self.mode = mode 
        
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
        
        # Buff/Debuff Timers (Frames)
        self.speed_boost_timer = 0
        self.ai_slow_timer = 0
        self.player_slow_timer = 0 
        self.ai_speed_boost_timer = 0 
        
        # VS Mode Specifics
        self.has_key = False
        self.key_spawned = False
        self.has_shield = False
        self.heart_spawned = False
        self.game_time = 0 
        self.key_pos = None
        self.heart_pos = None
        
        # State Flags
        self.game_active = True
        self.game_won = False
        self.game_over_text = ""
        self.death_type = None # 'explosion' or 'caught' or 'win'
        self.paused = False
        
        # Scoring, AI & Hazards
        self.user_score = 0
        self.rewards = [] 
        self.bots = []
        self.bombs = []
        self.creepers = [] 
        self.ghasts = [] # Flying enemies
        self.fire_charges = [] # Ghast projectiles
        self.enderman = None # Dictionary when active
        self.explosion_marks = [] 
        
        # Solo Mode specific
        self.ai_path_display = []
        self.ai_draw_index = 0
        
        # Countdown Logic
        self.start_ticks = pygame.time.get_ticks()
        self.warmup_duration = 3000 if mode == "hell" else 5000
        self.is_warming_up = True if mode in ["vs_ai", "hell"] else False

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
            for c in range(self.cols):
                row.append(1) 
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
            if not found_neighbor:
                stack.pop()

    def _create_loops(self):
        num_walls_to_remove = (self.rows * self.cols) // 20 
        for _ in range(num_walls_to_remove):
            r = random.randint(1, self.rows - 2)
            c = random.randint(1, self.cols - 2)
            if self.grid[r][c] == 1:
                self.grid[r][c] = 0

    def _setup_entities(self):
        if self.mode == "vs_ai":
            self.bots.append({
                'pos': [1, 1], 'path': [], 'timer': 0, 'state': 'THINKING',
                'base_speed': 7, 
                'speed': 7, 
                'score': 0
            })
            self._generate_rewards(5)
        elif self.mode == "hell":
            start_r, start_c = 1, self.cols - 2
            while self.grid[start_r][start_c] == 1 and start_c > 0: start_c -= 1
            
            self.bots.append({
                'pos': [start_r, start_c], 'path': [], 'timer': 0, 'state': 'CHASING',
                'base_speed': 10, 
                'speed': 10, 
                'repath_timer': 0, 'id': 0
            })
            self._generate_rewards(7) 
            self.spawn_creeper() # Initial Creeper

    def _generate_rewards(self, count=1):
        # VS Mode includes potions
        if self.mode == "vs_ai":
            if self.game_time > 5 * FPS:
                choices = ['points', 'swiftness', 'slowness']
                weights = [90, 5, 5]
            else:
                choices = ['points']
                weights = [100]
        else:
            choices = ['points']
            weights = [100]

        added = 0
        while added < count:
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
                    self.bots.append({
                        'pos': [r, c], 'path': [], 'timer': 0, 'state': 'CHASING',
                        'base_speed': 10, 
                        'speed': 10, 
                        'repath_timer': 0, 'id': len(self.bots)
                    })
                    return

    def spawn_creeper(self):
        """Spawns a creeper with a patrol route"""
        for _ in range(50):
            r = random.randint(1, self.rows - 2)
            c = random.randint(1, self.cols - 2)
            if self.grid[r][c] == 0 and (r,c) != tuple(self.player_pos):
                # Decide Axis (0=Vertical, 1=Horizontal)
                axis = random.choice([0, 1])
                self.creepers.append({
                    'pos': [r, c],
                    'axis': axis,
                    'dir': 1,
                    'start_pos': [r, c],
                    'range': 10,
                    'timer': 0,
                    'speed': 15, # Slow patrol speed
                    'fuse': 90,  # 3 seconds * 30 FPS
                    'radius': 3, # Detection radius
                    'state': 'PATROL',
                    'blink_timer': 0 # New timer for smooth blinking
                })
                return

    def spawn_enderman(self):
        """Spawns an enderman for a short duration"""
        for _ in range(50):
            r = random.randint(1, self.rows - 2)
            c = random.randint(1, self.cols - 2)
            # Spawn away from player to be fair
            if self.grid[r][c] == 0 and (abs(r - self.player_pos[0]) + abs(c - self.player_pos[1]) > 5):
                self.enderman = {
                    'pos': [r, c],
                    'duration': 10 * FPS, # 10 seconds alive
                    'teleport_timer': 0,
                    'teleport_interval': int(1.5 * FPS) # 1.5s
                }
                return

    def spawn_ghast(self):
        """Spawns a Ghast that flies in a Bezier curve across the screen"""
        # 0: Top, 1: Right, 2: Bottom, 3: Left
        side = random.randint(0, 3)
        
        if side == 0: start = (-5, random.randint(0, self.cols)); end = (self.rows + 5, random.randint(0, self.cols))
        elif side == 1: start = (random.randint(0, self.rows), self.cols + 5); end = (random.randint(0, self.rows), -5)
        elif side == 2: start = (self.rows + 5, random.randint(0, self.cols)); end = (-5, random.randint(0, self.cols))
        else: start = (random.randint(0, self.rows), -5); end = (random.randint(0, self.rows), self.cols + 5)

        mid_r, mid_c = self.rows // 2, self.cols // 2
        control = (mid_r + random.randint(-10, 10), mid_c + random.randint(-10, 10))

        self.ghasts.append({
            'p0': start, 'p1': control, 'p2': end,
            't': 0.0, 'speed': 0.0015, 'pos': start,
            'shoot_timer': random.randint(60, 90) # Initial delay between 2-3 seconds
        })

    def spawn_fire_charge(self, start_pos, target_pos):
        """Shoots a fireball from start towards target"""
        sr, sc = start_pos
        tr, tc = target_pos
        
        # Calculate Direction Vector
        dr = tr - sr
        dc = tc - sc
        magnitude = math.sqrt(dr*dr + dc*dc)
        
        if magnitude > 0:
            # Normalize and multiply by speed (0.3 blocks per frame)
            speed = 0.3
            vel_r = (dr / magnitude) * speed
            vel_c = (dc / magnitude) * speed
            
            self.fire_charges.append({
                'pos': [sr, sc],
                'velocity': [vel_r, vel_c]
            })

    def get_astar_path(self, start, end):
        start, end = tuple(start), tuple(end)
        queue = [(0, 0, start, [start])]
        visited = set()
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

    def update(self):
        if self.paused or not self.game_active: return

        if self.is_warming_up:
            if pygame.time.get_ticks() - self.start_ticks > self.warmup_duration:
                self.is_warming_up = False
            return 

        self.game_time += 1

        # VS Mode Updates
        if self.mode == "vs_ai":
            if self.game_time > 450 and not self.heart_spawned:
                self.spawn_heart()
            
            self.move_delay = self.base_move_delay
            if self.player_slow_timer > 0:
                self.player_slow_timer -= 1
                self.move_delay = 8 
            elif self.speed_boost_timer > 0:
                self.speed_boost_timer -= 1
                self.move_delay = 1 
                
            if self.ai_slow_timer > 0:
                self.ai_slow_timer -= 1
                for bot in self.bots: bot['speed'] = bot['base_speed'] + 15 
            elif self.ai_speed_boost_timer > 0:
                self.ai_speed_boost_timer -= 1
                for bot in self.bots: bot['speed'] = max(2, bot['base_speed'] - 4) 
            else:
                for bot in self.bots: bot['speed'] = bot['base_speed']

        # Hell Mode Updates
        if self.mode == "hell":
            # Bombs
            for b in self.bombs:
                b['timer'] -= 1
            self.bombs = [b for b in self.bombs if b['timer'] > 0]
            
            # Spawn Ghasts
            ghast_count = len(self.ghasts)
            if ghast_count < 2:
                chance = 0.002 if ghast_count == 0 else 0.0005
                if random.random() < chance:
                    self.spawn_ghast()

            # Update Ghasts
            for g in self.ghasts[:]:
                g['t'] += g['speed']
                if g['t'] > 1.0:
                    self.ghasts.remove(g)
                else:
                    t = g['t']; u = 1 - t; tt = t * t; uu = u * u
                    r = (uu * g['p0'][0]) + (2 * u * t * g['p1'][0]) + (tt * g['p2'][0])
                    c = (uu * g['p0'][1]) + (2 * u * t * g['p1'][1]) + (tt * g['p2'][1])
                    g['pos'] = (r, c)
                    
                    # Fire Charge Logic (Timer based)
                    g['shoot_timer'] -= 1
                    if g['shoot_timer'] <= 0:
                        self.spawn_fire_charge(g['pos'], self.player_pos)
                        # Reset timer to random interval (2 to 3 seconds)
                        # 30 FPS * 2 = 60 frames, 30 FPS * 3 = 90 frames
                        g['shoot_timer'] = random.randint(60, 90)

            # Update Fire Charges
            for fc in self.fire_charges[:]:
                # Move
                fc['pos'][0] += fc['velocity'][0]
                fc['pos'][1] += fc['velocity'][1]
                
                # Bounds check (remove if far off screen)
                fr, fc_col = fc['pos']
                if not (-10 < fr < self.rows + 10 and -10 < fc_col < self.cols + 10):
                    self.fire_charges.remove(fc)
                    continue
                
                # Collision with Player (Distance < 0.5 blocks)
                dist_r = abs(fr - self.player_pos[0])
                dist_c = abs(fc_col - self.player_pos[1])
                if math.sqrt(dist_r*dist_r + dist_c*dist_c) < 0.5:
                    self.game_active = False; self.game_won = False
                    self.death_type = "explosion"
                    self.game_over_text = "TRIED TO DODGE GHAST!"

            # Enderman Logic
            if self.enderman:
                self.enderman['duration'] -= 1
                self.enderman['teleport_timer'] += 1
                if tuple(self.enderman['pos']) == tuple(self.player_pos):
                    self.game_active = False; self.game_won = False
                    self.death_type = "explosion"
                    self.game_over_text = "SLAIN BY ENDERMAN!"
                if self.enderman['teleport_timer'] >= self.enderman['teleport_interval']:
                    self.enderman['teleport_timer'] = 0
                    for _ in range(10):
                        r = random.randint(1, self.rows - 2)
                        c = random.randint(1, self.cols - 2)
                        if self.grid[r][c] == 0:
                            self.enderman['pos'] = [r, c]; break
                if self.enderman['duration'] <= 0: self.enderman = None
            else:
                if self.game_time > 10 * FPS:
                    if self.game_time % 90 == 0:
                        if random.random() < 0.30: self.spawn_enderman()

            # Creeper Logic
            for c_idx, creep in enumerate(self.creepers):
                dist_r = abs(creep['pos'][0] - self.player_pos[0])
                dist_c = abs(creep['pos'][1] - self.player_pos[1])
                in_radius = max(dist_r, dist_c) <= creep['radius']
                if in_radius:
                    creep['state'] = 'FUSE'
                    creep['fuse'] -= 1
                    creep['blink_timer'] = creep.get('blink_timer', 0) + 1
                    if creep['fuse'] <= 0:
                        self.explosion_marks.append(tuple(creep['pos']))
                        self.creepers.pop(c_idx)
                        if in_radius: 
                            self.game_active = False; self.game_won = False
                            self.death_type = "explosion"
                            self.game_over_text = "BLOWN UP BY CREEPER!"
                        continue
                else:
                    creep['state'] = 'PATROL'
                    if creep['fuse'] < 90: creep['fuse'] += 0.5 
                
                if creep['state'] == 'PATROL':
                    creep['timer'] += 1
                    if creep['timer'] >= creep['speed']:
                        creep['timer'] = 0
                        dr, dc = (1, 0) if creep['axis'] == 0 else (0, 1)
                        dr *= creep['dir']; dc *= creep['dir']
                        nr, nc = creep['pos'][0] + dr, creep['pos'][1] + dc
                        start_dist = abs(nr - creep['start_pos'][0]) + abs(nc - creep['start_pos'][1])
                        if (0 < nr < self.rows and 0 < nc < self.cols and 
                            self.grid[nr][nc] == 0 and start_dist <= creep['range']):
                            creep['pos'] = [nr, nc]
                        else:
                            creep['dir'] *= -1

        for i, bot in enumerate(self.bots):
            bot['timer'] += 1
            if self.mode == "vs_ai":
                if tuple(bot['pos']) == tuple(self.player_pos):
                    if self.has_shield:
                        self.has_shield = False 
                        self.game_over_text = "Shield Blocked Theft!" 
                    else:
                        steal_amount = min(10, self.user_score)
                        self.user_score -= steal_amount
                        bot['score'] += steal_amount

                if bot['state'] == 'THINKING' and bot['timer'] >= 30:
                    target = None
                    best_dist = float('inf')
                    for rew in self.rewards:
                        dist = abs(bot['pos'][0]-rew['pos'][0]) + abs(bot['pos'][1]-rew['pos'][1])
                        if dist < best_dist: best_dist, target = dist, rew['pos']
                    if not target: target = tuple(self.goal_pos)
                    bot['path'] = self.get_astar_path(bot['pos'], target)
                    if len(bot['path']) > 0: bot['path'].pop(0)
                    bot['state'] = 'MOVING'; bot['timer'] = 0
                elif bot['state'] == 'MOVING' and bot['timer'] >= bot['speed']:
                    bot['timer'] = 0
                    if bot['path']:
                        bot['pos'] = list(bot['path'].pop(0))
                        for j in range(len(self.rewards)-1, -1, -1):
                            if self.rewards[j]['pos'] == tuple(bot['pos']):
                                r = self.rewards[j]
                                if r['type'] == 'points':
                                    bot['score'] += r['val']
                                elif r['type'] == 'swiftness':
                                    self.ai_speed_boost_timer = 5 * FPS
                                elif r['type'] == 'slowness':
                                    self.player_slow_timer = 5 * FPS
                                self.rewards.pop(j)
                                bot['state'] = 'THINKING'
                        if bot['pos'] == self.goal_pos and bot['score'] > 0:
                            self.game_active = False; self.game_won = False
                            self.game_over_text = f"AI Wins! Score: {bot['score']}"
                    else: bot['state'] = 'THINKING'

            elif self.mode == "hell":
                if random.random() < 0.005:
                    self.bombs.append({'pos': tuple(bot['pos']), 'timer': 15 * FPS})

                bot['repath_timer'] = bot.get('repath_timer', 0) + 1
                if bot['repath_timer'] > 10 or not bot['path']:
                    target = list(self.player_pos)
                    if i > 0:
                        pred_r = self.player_pos[0] + self.player_last_dir[0] * 4
                        pred_c = self.player_pos[1] + self.player_last_dir[1] * 4
                        pred_r = max(1, min(self.rows - 2, pred_r))
                        pred_c = max(1, min(self.cols - 2, pred_c))
                        if self.grid[pred_r][pred_c] == 0: target = [pred_r, pred_c]
                    bot['path'] = self.get_astar_path(bot['pos'], target)
                    if len(bot['path']) > 0: bot['path'].pop(0)
                    bot['repath_timer'] = 0
                if bot['timer'] >= bot['speed']:
                    bot['timer'] = 0
                    if bot['path']:
                        bot['pos'] = list(bot['path'].pop(0))
                        if bot['pos'] == self.player_pos:
                            self.game_active = False; self.game_won = False
                            self.death_type = "caught"
                            self.game_over_text = "CAUGHT! GAME OVER."

        if self.mode == "solo" and self.game_won:
             total = len(self.ai_path_display)
             self.ai_draw_index = min(total, self.ai_draw_index + max(1, total // (10*30)))

    def move_player(self, dx, dy):
        if self.paused or not self.game_active or self.is_warming_up: return
        self.player_last_dir = (dy, dx)
        new_r, new_c = self.player_pos[0] + dy, self.player_pos[1] + dx
        
        if self.grid[new_r][new_c] == 0:
            self.player_pos = [new_r, new_c]
            if self.mode != "hell": self.path_taken.append((new_r, new_c))
            
            for b in self.bombs:
                if tuple(self.player_pos) == b['pos']:
                    self.game_active = False; self.game_won = False
                    self.death_type = "explosion"
                    self.game_over_text = "BOOM! YOU HIT A TNT."
            
            # Enderman Collision (Moving into him)
            if self.mode == "hell" and self.enderman:
                if tuple(self.player_pos) == tuple(self.enderman['pos']):
                    self.game_active = False; self.game_won = False
                    self.death_type = "explosion"
                    self.game_over_text = "SLAIN BY ENDERMAN!"

            if self.mode == "vs_ai" and self.key_spawned and not self.has_key:
                if tuple(self.player_pos) == self.key_pos:
                    self.has_key = True
                    self.key_pos = None 

            if self.mode == "vs_ai" and self.heart_spawned and not self.has_shield:
                if tuple(self.player_pos) == self.heart_pos:
                    self.has_shield = True
                    self.heart_pos = None

            if self.mode in ["vs_ai", "hell"]:
                for i in range(len(self.rewards)-1, -1, -1):
                    if self.rewards[i]['pos'] == tuple(self.player_pos):
                        r = self.rewards[i]
                        if r['type'] == 'points':
                            self.user_score += r['val']
                            if self.mode == "vs_ai" and not self.key_spawned: self.spawn_key()
                        elif r['type'] == 'swiftness': self.speed_boost_timer = 5 * FPS 
                        elif r['type'] == 'slowness': self.ai_slow_timer = 5 * FPS 
                        self.rewards.pop(i)
                        
                        if self.mode == "hell":
                            self._generate_rewards(1)
                            if r.get('color') == PURPLE: self.spawn_hell_bot()
                            elif r.get('color') == ORANGE:
                                for bot in self.bots: bot['speed'] = max(2, bot['speed'] - 1)

            if self.player_pos == self.goal_pos:
                if self.mode == "solo":
                    self.game_won = True
                    self.death_type = "win"
                    self.ai_path_display = self.get_astar_path((1,1), self.goal_pos)
                    self.game_over_text = f"SOLVED! You: {len(self.path_taken)} | AI: {len(self.ai_path_display)}"
                elif self.mode == "vs_ai":
                    if self.has_key: 
                        if self.user_score > 0:
                            self.game_active = False; self.game_won = True
                            self.death_type = "win"
                            self.game_over_text = f"You Win! Score: {self.user_score}"
                    else: pass 
                elif self.mode == "hell":
                    self.game_active = False; self.game_won = True
                    self.death_type = "win"
                    self.game_over_text = f"SURVIVED! Score: {self.user_score}"

class GameRenderer:
    """THE ARTIST: Handles drawing shapes, text, images and UI."""
    def __init__(self, screen):
        self.screen = screen
        self.font_small = pygame.font.SysFont("Arial", 24)
        self.font_large = pygame.font.SysFont("Arial", 50)
        self.font_huge = pygame.font.SysFont("Arial", 120)
        self.assets = {}
        self.wall_textures = []
        self.load_assets()

    def load_assets(self):
        files = {
            'steve': 'assets/steve.png',
            'portal': 'assets/portal.jpg',
            'piglin': 'assets/piglin.png',
            'vines': 'assets/vines.png',
            'tnt': 'assets/tnt.png',
            'win': 'assets/win.gif',
            'key': 'assets/key.png',
            'swiftness': 'assets/swiftness.png',
            'slowness': 'assets/slowness.png',
            'heart': 'assets/heart.png',
            'creeper': 'assets/creeper.png',
            'creeper_death': 'assets/creeper2.png',
            'explosion': 'assets/explosion.gif',
            'enderman': 'assets/enderman.png',
            'ghast': 'assets/ghast.png',
            'fire_charge': 'assets/fire_charge.png'
        }
        for key, filename in files.items():
            if key == 'win' or key == 'explosion':
                self.load_gif_frames(filename, key)
            else:
                try:
                    img = pygame.image.load(filename)
                    self.assets[key] = img
                except (pygame.error, FileNotFoundError):
                    self.assets[key] = None

        wall_files = ['assets/nether1.webp', 'assets/nether2.webp', 'assets/nether3.jpg']
        for wf in wall_files:
            try:
                img = pygame.image.load(wf)
                self.wall_textures.append(img)
            except (pygame.error, FileNotFoundError):
                pass

    def load_gif_frames(self, filename, key):
        try:
            from PIL import Image, ImageSequence
            pil_image = Image.open(filename)
            frames = []
            for frame in ImageSequence.Iterator(pil_image):
                frame = frame.convert('RGBA')
                data = frame.tobytes()
                size = frame.size
                mode = frame.mode
                pygame_image = pygame.image.frombytes(data, size, mode)
                pygame_image.set_colorkey((0, 255, 0))
                frames.append(pygame_image)
            self.assets[key] = frames
        except ImportError:
            print("Pillow library not found. Install via 'pip install Pillow'")
            try:
                img = pygame.image.load(filename)
                img.set_colorkey((0, 255, 0))
                self.assets[key] = [img]
            except:
                self.assets[key] = None
        except:
            self.assets[key] = None

    def get_scaled_asset(self, key, w, h):
        img = self.assets.get(key)
        if img and not isinstance(img, list):
            return pygame.transform.scale(img, (w, h))
        return None

    def draw_vines(self, margin_x, margin_y):
        vine_img = self.assets.get('vines')
        if not vine_img: return
        if margin_y > 0:
            scaled_h = pygame.transform.scale(vine_img, (SCREEN_WIDTH, margin_y))
            self.screen.blit(scaled_h, (0, UI_HEIGHT)) 
            self.screen.blit(scaled_h, (0, SCREEN_HEIGHT - margin_y)) 
        if margin_x > 0:
            scaled_v = pygame.transform.scale(vine_img, (margin_x, SCREEN_HEIGHT))
            self.screen.blit(scaled_v, (0, 0)) 
            self.screen.blit(scaled_v, (SCREEN_WIDTH - margin_x, 0)) 

    def draw_game(self, state):
        cell_size = state.cell_size
        margin_x = (SCREEN_WIDTH - (state.cols * cell_size)) // 2
        margin_y = UI_HEIGHT + (SCREEN_HEIGHT - UI_HEIGHT - (state.rows * cell_size)) // 2
        
        scaled_walls = []
        if self.wall_textures:
            for w_tex in self.wall_textures:
                scaled_walls.append(pygame.transform.scale(w_tex, (cell_size + 1, cell_size + 1)))

        self.screen.fill(WALL_COLOR) 
        
        for r in range(state.rows):
            for c in range(state.cols):
                x = margin_x + c * cell_size
                y = margin_y + r * cell_size
                if state.grid[r][c] == 1:
                    if scaled_walls:
                        tex_idx = (r * 7 + c * 13) % len(scaled_walls)
                        self.screen.blit(scaled_walls[tex_idx], (x, y))
                    else:
                        pygame.draw.rect(self.screen, WALL_COLOR, (x, y, cell_size + 1, cell_size + 1))
                else:
                    # Check for Explosion Mark
                    is_crater = False
                    for ex in state.explosion_marks:
                        dist = max(abs(r-ex[0]), abs(c-ex[1])) 
                        if dist <= 5: 
                            is_crater = True
                            break
                    if is_crater:
                        pygame.draw.rect(self.screen, EXPLOSION_MARK, (x, y, cell_size + 1, cell_size + 1))
                    else:
                        pygame.draw.rect(self.screen, NETHER_FOG, (x, y, cell_size + 1, cell_size + 1))
        
        self.draw_vines(margin_x, margin_y)

        # Draw Items (Rewards, Potions, Key, Heart, Bombs)
        pulse = math.sin(pygame.time.get_ticks() * 0.01) * 2
        
        for rew in state.rewards:
            r, c = rew['pos']
            cx = margin_x + c * cell_size + cell_size // 2
            cy = margin_y + r * cell_size + cell_size // 2
            
            if rew['type'] == 'points':
                pygame.draw.circle(self.screen, WHITE, (cx, cy), int(cell_size//3 + 3 + pulse))
                pygame.draw.circle(self.screen, rew['color'], (cx, cy), int(cell_size//3 + pulse))
            elif rew['type'] in ['swiftness', 'slowness']:
                img_key = rew['type']
                img = self.get_scaled_asset(img_key, cell_size, cell_size)
                if img:
                    self.screen.blit(img, (margin_x + c*cell_size, margin_y + r*cell_size))
                else:
                    pygame.draw.circle(self.screen, rew['color'], (cx, cy), int(cell_size//3))

        if state.mode == "vs_ai" and state.key_spawned and not state.has_key:
            kr, kc = state.key_pos
            k_img = self.get_scaled_asset('key', cell_size, cell_size)
            if k_img:
                self.screen.blit(k_img, (margin_x + kc*cell_size, margin_y + kr*cell_size))
            else:
                pygame.draw.rect(self.screen, GOLD_KEY, (margin_x + kc*cell_size + 5, margin_y + kr*cell_size + 5, cell_size-10, cell_size-10))

        if state.mode == "vs_ai" and state.heart_spawned and not state.has_shield:
            hr, hc = state.heart_pos
            h_img = self.get_scaled_asset('heart', cell_size, cell_size)
            if h_img:
                self.screen.blit(h_img, (margin_x + hc*cell_size, margin_y + hr*cell_size))
            else:
                pygame.draw.circle(self.screen, RED_HEART, (margin_x + hc*cell_size + cell_size//2, margin_y + hr*cell_size + cell_size//2), cell_size//3)

        tnt_img = self.get_scaled_asset('tnt', cell_size, cell_size)
        for b in state.bombs:
            br, bc = b['pos']
            bx = margin_x + bc * cell_size
            by = margin_y + br * cell_size
            if tnt_img:
                self.screen.blit(tnt_img, (bx, by))
            else:
                cx = bx + cell_size // 2
                cy = by + cell_size // 2
                pygame.draw.circle(self.screen, BOMB_COLOR, (cx, cy), cell_size//3)
                pygame.draw.circle(self.screen, BOMB_FUSE, (cx, cy), cell_size//6)

        creeper_img = self.get_scaled_asset('creeper', cell_size, cell_size)
        for creep in state.creepers:
            cr, cc = creep['pos']
            cx = margin_x + cc * cell_size
            cy = margin_y + cr * cell_size
            radius_px = creep['radius'] * cell_size * 2 + cell_size
            aura_surf = pygame.Surface((radius_px, radius_px), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, CREEPER_AURA, (radius_px//2, radius_px//2), radius_px//2)
            self.screen.blit(aura_surf, (cx + cell_size//2 - radius_px//2, cy + cell_size//2 - radius_px//2))
            
            if creeper_img:
                if creep['state'] == 'FUSE':
                    blink_speed = max(1, int(creep['fuse'] / 5)) 
                    if (creep.get('blink_timer', 0) // blink_speed) % 2 == 0:
                        flash_surf = creeper_img.copy()
                        flash_surf.fill((200, 200, 200), special_flags=pygame.BLEND_RGB_ADD)
                        scale_up = int(cell_size * 1.2)
                        flash_surf = pygame.transform.scale(flash_surf, (scale_up, scale_up))
                        offset = (scale_up - cell_size) // 2
                        self.screen.blit(flash_surf, (cx - offset, cy - offset))
                    else:
                        self.screen.blit(creeper_img, (cx, cy))
                else:
                    self.screen.blit(creeper_img, (cx, cy))
            else:
                color = GREEN if creep['state'] == 'PATROL' else WHITE
                pygame.draw.rect(self.screen, color, (cx+2, cy+2, cell_size-4, cell_size-4))

        if state.mode != "hell":
            for r, c in state.path_taken:
                pygame.draw.rect(self.screen, YELLOW, 
                    (margin_x + c * cell_size + cell_size // 4, 
                     margin_y + r * cell_size + cell_size // 4, 
                     cell_size // 2, cell_size // 2))

        piglin = self.get_scaled_asset('piglin', cell_size, cell_size)
        for bot in state.bots:
            ax, ay = bot['pos']
            screen_x = margin_x + ay * cell_size
            screen_y = margin_y + ax * cell_size
            if piglin:
                self.screen.blit(piglin, (screen_x, screen_y))
            else:
                color = HELL_RED if state.mode == "hell" else RED
                pygame.draw.rect(self.screen, color, (screen_x+2, screen_y+2, cell_size-4, cell_size-4))

        if state.enderman:
            enderman_img = self.get_scaled_asset('enderman', cell_size, cell_size)
            er, ec = state.enderman['pos']
            ex = margin_x + ec * cell_size
            ey = margin_y + er * cell_size
            pygame.draw.rect(self.screen, ENDERMAN_PURPLE, (ex, ey, cell_size, cell_size), 2)
            if enderman_img:
                self.screen.blit(enderman_img, (ex, ey))
            else:
                pygame.draw.rect(self.screen, ENDERMAN_PURPLE, (ex+2, ey+2, cell_size-4, cell_size-4))
        
        ghast_size = int(cell_size * 3.5) 
        ghast_img = self.get_scaled_asset('ghast', ghast_size, ghast_size)
        for g in state.ghasts:
            gr, gc = g['pos']
            shadow_x = margin_x + gc * cell_size + cell_size//2
            shadow_y = margin_y + gr * cell_size + UI_HEIGHT + cell_size 
            pygame.draw.circle(self.screen, GHAST_SHADOW, (int(shadow_x), int(shadow_y)), cell_size//2)
            
            screen_gx = margin_x + gc * cell_size - ghast_size//2 
            screen_gy = margin_y + gr * cell_size - ghast_size//2
            if ghast_img:
                self.screen.blit(ghast_img, (screen_gx, screen_gy))
            else:
                pygame.draw.rect(self.screen, WHITE, (screen_gx, screen_gy, ghast_size, ghast_size))

        # Fire Charges
        fire_img = self.get_scaled_asset('fire_charge', cell_size, cell_size)
        for fc in state.fire_charges:
            fr, fc_col = fc['pos']
            fx = margin_x + fc_col * cell_size
            fy = margin_y + fr * cell_size
            if fire_img:
                self.screen.blit(fire_img, (fx, fy))
            else:
                pygame.draw.circle(self.screen, ORANGE, (int(fx+cell_size//2), int(fy+cell_size//2)), cell_size//3)

        px, py = state.player_pos
        steve = self.get_scaled_asset('steve', cell_size, cell_size)
        p_x = margin_x + py * cell_size
        p_y = margin_y + px * cell_size
        if steve:
             self.screen.blit(steve, (p_x, p_y))
        else:
            pygame.draw.rect(self.screen, CYAN, (p_x+3, p_y+3, cell_size-6, cell_size-6))

        gx, gy = state.goal_pos
        portal = self.get_scaled_asset('portal', cell_size, cell_size)
        g_x = margin_x + gy * cell_size
        g_y = margin_y + gx * cell_size
        if portal:
            self.screen.blit(portal, (g_x, g_y))
        else:
            pygame.draw.rect(self.screen, GREEN, (g_x, g_y, cell_size, cell_size))
        
        if state.mode == "vs_ai" and not state.has_key:
             pygame.draw.rect(self.screen, WHITE, (g_x, g_y, cell_size, cell_size), 3)

        if state.mode == "solo" and state.game_won:
             if state.ai_draw_index > 1:
                points = []
                for i in range(int(state.ai_draw_index)):
                    r, c = state.ai_path_display[i]
                    points.append((margin_x + c * cell_size + cell_size // 2, 
                                   margin_y + r * cell_size + cell_size // 2))
                if len(points) > 1: pygame.draw.lines(self.screen, RED, False, points, 3)

        pygame.draw.rect(self.screen, (0,0,0), (0,0, SCREEN_WIDTH, UI_HEIGHT))
        pygame.draw.line(self.screen, WHITE, (0, UI_HEIGHT), (SCREEN_WIDTH, UI_HEIGHT), 2)
        
        status = ""
        if state.mode == "solo": status = f"Steps: {len(state.path_taken)} | 'P' to Pause"
        elif state.mode == "vs_ai": status = f"YOU: {state.user_score} | AI: {state.bots[0]['score'] if state.bots else 0}"
        elif state.mode == "hell": status = f"Score: {state.user_score} | Bots: {len(state.bots)}"
        
        txt = self.font_small.render(status, True, WHITE)
        self.screen.blit(txt, (20, (UI_HEIGHT - txt.get_height())//2))
        
        if state.mode == "vs_ai":
            icon_x = 400
            if state.has_key:
                k_icon = self.get_scaled_asset('key', 30, 30)
                if k_icon: self.screen.blit(k_icon, (icon_x, (UI_HEIGHT-30)//2))
                icon_x += 40
            
            if state.has_shield:
                h_icon = self.get_scaled_asset('heart', 30, 30)
                if h_icon: self.screen.blit(h_icon, (icon_x, (UI_HEIGHT-30)//2))

        if state.is_warming_up:
            rem = (state.warmup_duration - (pygame.time.get_ticks() - state.start_ticks)) // 1000 + 1
            txt = "GO!" if rem <= 0 else str(int(rem))
            surf = self.font_huge.render(txt, True, COUNTDOWN_COLOR)
            self.screen.blit(surf, (SCREEN_WIDTH//2 - surf.get_width()//2, SCREEN_HEIGHT//2 - surf.get_height()//2))
        elif state.paused:
            self.draw_overlay("PAUSED", "Press 'P' to Resume | 'R' to Menu")
        elif not state.game_active and not state.game_won:
             self.draw_overlay(state.game_over_text, "Press 'R' to Return to Menu", False, state.death_type)
        elif state.mode == "solo" and state.game_won and state.ai_draw_index >= len(state.ai_path_display):
             self.draw_overlay(state.game_over_text, "Press 'R' to Return to Menu")
        elif (state.mode != "solo" and state.game_won and not state.game_active):
             use_win_gif = (state.mode in ["vs_ai", "hell"])
             self.draw_overlay(state.game_over_text, "Press 'R' to Return to Menu", use_win_gif, state.death_type)

    def draw_overlay(self, title_text, sub_text, show_win_gif=False, death_type=None):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_BG)
        self.screen.blit(overlay, (0,0))
        cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
        
        asset_to_show = None
        is_static = False
        
        if show_win_gif is True:
             asset_to_show = 'win'
        elif death_type == "explosion":
             if "TNT" in title_text:
                 asset_to_show = 'tnt'
                 is_static = True
             elif "CREEPER" in title_text:
                 asset_to_show = 'creeper_death'
                 is_static = True
             elif "ENDERMAN" in title_text:
                 asset_to_show = 'enderman'
                 is_static = True
             elif "GHAST" in title_text: # Handle Ghast death
                 asset_to_show = 'ghast'
                 is_static = True
            
        if asset_to_show and self.assets.get(asset_to_show):
            asset_data = self.assets[asset_to_show]
            img = None
            
            if isinstance(asset_data, list) and len(asset_data) > 0:
                frame_delay = 50 if asset_to_show == 'explosion' else 100
                frame_idx = (pygame.time.get_ticks() // frame_delay) % len(asset_data)
                img = asset_data[frame_idx]
            
            elif isinstance(asset_data, pygame.Surface):
                img = asset_data

            if img:
                target_height = SCREEN_HEIGHT // 4
                w, h = img.get_size()
                
                scale_factor = target_height / h
                new_w, new_h = int(w * scale_factor), int(h * scale_factor)
                
                scaled_img = pygame.transform.scale(img, (new_w, new_h))
                
                img_rect = scaled_img.get_rect(center=(cx, cy - 100))
                self.screen.blit(scaled_img, img_rect)
                
                text_y_start = img_rect.bottom + 20
            else:
                 text_y_start = cy - 50
        else:
             text_y_start = cy - 50
        
        t_surf = self.font_large.render(title_text, True, YELLOW)
        s_surf = self.font_small.render(sub_text, True, WHITE)
        self.screen.blit(t_surf, (cx - t_surf.get_width()//2, text_y_start))
        self.screen.blit(s_surf, (cx - s_surf.get_width()//2, text_y_start + 70))

    def draw_menu(self):
        self.screen.fill((0,0,0))
        title = self.font_large.render("Mabrook's Maze Challenge", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        options = [
            ("1. Easy", BLUE_MENU),
            ("2. Normal", BLUE_MENU),
            ("3. Hard", BLUE_MENU),
            ("4. VS AI", (0, 200, 0)),
            ("5. HELL MODE", HELL_RED)
        ]
        y = 200
        for txt, col in options:
            surf = self.font_small.render(txt, True, col)
            self.screen.blit(surf, (SCREEN_WIDTH//2 - surf.get_width()//2, y))
            y += 60
        info = self.font_small.render("Controls: Arrows to Move | P to Pause | R for Menu | ESC to Quit", True, (150,150,150))
        self.screen.blit(info, (SCREEN_WIDTH//2 - info.get_width()//2, SCREEN_HEIGHT - 100))

# --- MAIN LOOP ---
if __name__ == "__main__":
    renderer = GameRenderer(screen)
    game = None 
    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game: game = None 
                    else: pygame.quit(); sys.exit() # Quit from menu
                if game is None:
                    # UPDATED ROW COUNTS FOR BIGGER SPRITES
                    if event.key == pygame.K_1: game = GameState(12, "solo") 
                    elif event.key == pygame.K_2: game = GameState(18, "solo") 
                    elif event.key == pygame.K_3: game = GameState(25, "solo") 
                    elif event.key == pygame.K_4: game = GameState(25, "vs_ai")
                    elif event.key == pygame.K_5: game = GameState(25, "hell") 
                else:
                    if event.key == pygame.K_p:
                        game.paused = not game.paused
                    elif event.key == pygame.K_r:
                        if game.paused or not game.game_active or game.game_won:
                            game = None
        
        # CONTINUOUS MOVEMENT HANDLING
        if game and not game.paused and game.game_active:
            keys = pygame.key.get_pressed()
            if game.move_timer > 0:
                game.move_timer -= 1
            else:
                dx, dy = 0, 0
                if keys[pygame.K_LEFT]: dx = -1
                elif keys[pygame.K_RIGHT]: dx = 1
                elif keys[pygame.K_UP]: dy = -1
                elif keys[pygame.K_DOWN]: dy = 1
                
                if dx != 0 or dy != 0:
                    game.move_player(dx, dy)
                    game.move_timer = game.move_delay

        if game:
            game.update()
            renderer.draw_game(game)
        else:
            renderer.draw_menu()
        pygame.display.flip()