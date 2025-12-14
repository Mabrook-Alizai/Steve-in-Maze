import pygame
import math
import random
import os
import sys
from settings import *

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class GameRenderer:
    """THE ARTIST: Handles drawing shapes, text, images and UI."""
    def __init__(self, screen):
        self.screen = screen
        self.assets = {}
        self.wall_textures = []
        self.background_surface = None
        self.cached_cell_size = 0
        self.cached_margin_x = 0
        self.cached_margin_y = 0
        self.menu_panorama = None
        self.load_assets()
        
        # Fonts - Main Menu Specific
        self.font_title = pygame.font.Font(resource_path('assets/fonts/Minecrafter.ttf'), 100) if self.assets.get('minecrafter') else pygame.font.SysFont("Arial", 100)
        self.font_option = pygame.font.Font(resource_path('assets/fonts/MinTen.ttf'), 40) if self.assets.get('minten') else pygame.font.SysFont("Arial", 40)
        self.font_tips = pygame.font.Font(resource_path('assets/fonts/Blocky.ttf'), 20) if self.assets.get('blocky') else pygame.font.SysFont("Arial", 20)
        self.font_splash = pygame.font.Font(resource_path('assets/fonts/MinTen.ttf'), 20) if self.assets.get('minten') else pygame.font.SysFont("Arial", 20)
        
        # Fonts - Gameplay & Overlay (Restored and Themed)
        self.font_ui = pygame.font.Font(resource_path('assets/fonts/MinTen.ttf'), 24) if self.assets.get('minten') else pygame.font.SysFont("Arial", 24)
        self.font_small = pygame.font.Font(resource_path('assets/fonts/Blocky.ttf'), 30) if self.assets.get('blocky') else pygame.font.SysFont("Arial", 30)
        self.font_large = pygame.font.Font(resource_path('assets/fonts/MinTen.ttf'), 60) if self.assets.get('minten') else pygame.font.SysFont("Arial", 60)
        self.font_huge = pygame.font.Font(resource_path('assets/fonts/Minecrafter.ttf'), 120) if self.assets.get('minecrafter') else pygame.font.SysFont("Arial", 120)
        self.font_desc = pygame.font.Font(resource_path('assets/fonts/Blocky.ttf'), 20) if self.assets.get('blocky') else pygame.font.SysFont("Arial", 20)

    def load_assets(self):
        # Fonts check
        font_files = {'minecrafter': 'assets/fonts/Minecrafter.ttf', 'minten': 'assets/fonts/MinTen.ttf', 'blocky': 'assets/fonts/Blocky.ttf'}
        for k, v in font_files.items():
            try: 
                open(resource_path(v), 'r')
                self.assets[k] = True 
            except: self.assets[k] = False

        # Menu Panorama - Updated to pick random scene
        try:
            scenes = ['Scene1.png', 'Scene2.png', 'Scene3.png']
            chosen_scene = random.choice(scenes)
            self.menu_panorama = pygame.image.load(resource_path(f'assets/Main Menu/{chosen_scene}'))
            # Scale to height
            ratio = self.menu_panorama.get_width() / self.menu_panorama.get_height()
            new_h = SCREEN_HEIGHT
            new_w = int(new_h * ratio)
            self.menu_panorama = pygame.transform.scale(self.menu_panorama, (new_w, new_h))
            print(f"Loaded Menu Background: {chosen_scene}")
        except:
            print(f"Failed to load menu background: assets/Main Menu/{chosen_scene}")
            self.menu_panorama = None

        # Game Assets
        files = {
            'steve': 'assets/steve.png', 'portal': 'assets/portal.jpg', 'piglin': 'assets/piglin.png',
            'vines': 'assets/vines.png', 'tnt': 'assets/tnt.png', 'win': 'assets/win.gif',
            'key': 'assets/key.png', 'swiftness': 'assets/swiftness.png', 'slowness': 'assets/slowness.png',
            'heart': 'assets/heart.png', 'creeper': 'assets/creeper.png', 'creeper_death': 'assets/creeper2.png',
            'explosion': 'assets/explosion.gif', 'enderman': 'assets/enderman.png', 'ghast': 'assets/ghast.png',
            'fire_charge': 'assets/fire_charge.png', 'pearl': 'assets/pearl.png' 
        }
        for key, filename in files.items():
            if key in ['win', 'explosion']: self.load_gif_frames(filename, key)
            else:
                try: self.assets[key] = pygame.image.load(resource_path(filename))
                except: self.assets[key] = None

        wall_files = ['assets/nether1.webp', 'assets/nether2.webp', 'assets/nether3.jpg']
        for wf in wall_files:
            try: self.wall_textures.append(pygame.image.load(resource_path(wf)))
            except: pass

    def load_gif_frames(self, filename, key):
        try:
            from PIL import Image, ImageSequence
            pil_image = Image.open(resource_path(filename))
            frames = []
            for frame in ImageSequence.Iterator(pil_image):
                frame = frame.convert('RGBA'); data = frame.tobytes(); size = frame.size; mode = frame.mode
                pygame_image = pygame.image.frombytes(data, size, mode); pygame_image.set_colorkey((0, 255, 0))
                frames.append(pygame_image)
            self.assets[key] = frames
        except: self.assets[key] = None

    def get_scaled_asset(self, key, w, h):
        img = self.assets.get(key)
        if img and not isinstance(img, list) and not isinstance(img, bool): return pygame.transform.scale(img, (w, h))
        return None

    def init_level(self, state):
        available_height = SCREEN_HEIGHT - UI_HEIGHT
        self.cached_cell_size = min(SCREEN_WIDTH // state.cols, available_height // state.rows)
        self.cached_margin_x = (SCREEN_WIDTH - (state.cols * self.cached_cell_size)) // 2
        self.cached_margin_y = UI_HEIGHT + (available_height - (state.rows * self.cached_cell_size)) // 2
        
        scaled_walls = []
        if self.wall_textures:
            for w_tex in self.wall_textures: scaled_walls.append(pygame.transform.scale(w_tex, (self.cached_cell_size + 1, self.cached_cell_size + 1)))

        self.background_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.background_surface.fill(WALL_COLOR)
        for r in range(state.rows):
            for c in range(state.cols):
                x = self.cached_margin_x + c * self.cached_cell_size
                y = self.cached_margin_y + r * self.cached_cell_size
                if state.grid[r][c] == 1:
                    if scaled_walls: self.background_surface.blit(scaled_walls[(r*7+c*13)%len(scaled_walls)], (x, y))
                    else: pygame.draw.rect(self.background_surface, WALL_COLOR, (x, y, self.cached_cell_size + 1, self.cached_cell_size + 1))
                else: pygame.draw.rect(self.background_surface, NETHER_FOG, (x, y, self.cached_cell_size + 1, self.cached_cell_size + 1))
        
        vine_img = self.assets.get('vines')
        if vine_img and not isinstance(vine_img, bool):
            if self.cached_margin_y > 0:
                scaled_h = pygame.transform.scale(vine_img, (SCREEN_WIDTH, self.cached_margin_y))
                self.background_surface.blit(scaled_h, (0, UI_HEIGHT)); self.background_surface.blit(scaled_h, (0, SCREEN_HEIGHT - self.cached_margin_y)) 
            if self.cached_margin_x > 0:
                scaled_v = pygame.transform.scale(vine_img, (self.cached_margin_x, SCREEN_HEIGHT))
                self.background_surface.blit(scaled_v, (0, 0)); self.background_surface.blit(scaled_v, (SCREEN_WIDTH - self.cached_margin_x, 0))

    def draw_game(self, state):
        if not self.background_surface: self.init_level(state)
        self.screen.blit(self.background_surface, (0,0))
        
        cell_size = self.cached_cell_size; margin_x = self.cached_margin_x; margin_y = self.cached_margin_y
        
        for ex in state.explosion_marks:
             cx = margin_x + ex[1] * cell_size + cell_size//2; cy = margin_y + ex[0] * cell_size + cell_size//2
             pygame.draw.circle(self.screen, EXPLOSION_MARK, (cx, cy), cell_size * 2)

        pulse = math.sin(pygame.time.get_ticks() * 0.01) * 2
        for rew in state.rewards:
            r, c = rew['pos']; cx = margin_x + c * cell_size + cell_size // 2; cy = margin_y + r * cell_size + cell_size // 2
            if rew['type'] == 'points':
                pygame.draw.circle(self.screen, WHITE, (cx, cy), int(cell_size//3 + 3 + pulse)); pygame.draw.circle(self.screen, rew['color'], (cx, cy), int(cell_size//3 + pulse))
            else:
                if rew['type'] == 'pearl': img_key = 'pearl'
                elif rew['type'] == 'energy_drink': img_key = 'swiftness'
                elif rew['type'] == 'swiftness': img_key = 'swiftness'
                elif rew['type'] == 'slowness': img_key = 'slowness'
                else: img_key = None
                img = self.get_scaled_asset(img_key, cell_size, cell_size) if img_key else None
                if img: self.screen.blit(img, (margin_x + c*cell_size, margin_y + r*cell_size))
                else: pygame.draw.circle(self.screen, rew['color'], (cx, cy), int(cell_size//3))

        if state.mode == "vs_ai":
            if state.key_spawned and not state.has_key:
                k_img = self.get_scaled_asset('key', cell_size, cell_size)
                if k_img: self.screen.blit(k_img, (margin_x + state.key_pos[1]*cell_size, margin_y + state.key_pos[0]*cell_size))
            
            # SAFE GUARD: Check if heart_pos exists before trying to access it
            if state.heart_spawned and not state.has_shield and state.heart_pos:
                h_img = self.get_scaled_asset('heart', cell_size, cell_size)
                if h_img: self.screen.blit(h_img, (margin_x + state.heart_pos[1]*cell_size, margin_y + state.heart_pos[0]*cell_size))

        tnt_img = self.get_scaled_asset('tnt', cell_size, cell_size)
        for b in state.bombs:
            bx = margin_x + b['pos'][1] * cell_size; by = margin_y + b['pos'][0] * cell_size
            if tnt_img: self.screen.blit(tnt_img, (bx, by))
            else: pygame.draw.circle(self.screen, BOMB_COLOR, (bx+cell_size//2, by+cell_size//2), cell_size//3)

        creeper_img = self.get_scaled_asset('creeper', cell_size, cell_size)
        for creep in state.creepers:
            cx = margin_x + creep['pos'][1] * cell_size; cy = margin_y + creep['pos'][0] * cell_size
            radius_px = creep['radius'] * cell_size * 2 + cell_size
            aura_surf = pygame.Surface((radius_px, radius_px), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, CREEPER_AURA, (radius_px//2, radius_px//2), radius_px//2)
            self.screen.blit(aura_surf, (cx + cell_size//2 - radius_px//2, cy + cell_size//2 - radius_px//2))
            if creeper_img:
                if creep['state'] == 'FUSE':
                    blink_speed = max(1, int(creep['fuse'] / 5)) 
                    if (creep.get('blink_timer', 0) // blink_speed) % 2 == 0:
                        flash_surf = creeper_img.copy(); flash_surf.fill((200, 200, 200), special_flags=pygame.BLEND_RGB_ADD)
                        self.screen.blit(flash_surf, (cx, cy))
                    else: self.screen.blit(creeper_img, (cx, cy))
                else: self.screen.blit(creeper_img, (cx, cy))
            else: pygame.draw.rect(self.screen, GREEN, (cx+2, cy+2, cell_size-4, cell_size-4))

        if state.mode == "solo": # ONLY DRAW TRAIL IN SOLO MODE
            for r, c in state.path_taken:
                pygame.draw.rect(self.screen, YELLOW, (margin_x + c * cell_size + cell_size // 4, margin_y + r * cell_size + cell_size // 4, cell_size // 2, cell_size // 2))

        piglin = self.get_scaled_asset('piglin', cell_size, cell_size)
        for bot in state.bots:
            screen_x = margin_x + bot['pos'][1] * cell_size; screen_y = margin_y + bot['pos'][0] * cell_size
            if piglin: self.screen.blit(piglin, (screen_x, screen_y))
            else: pygame.draw.rect(self.screen, HELL_RED, (screen_x+2, screen_y+2, cell_size-4, cell_size-4))

        if state.enderman:
            enderman_img = self.get_scaled_asset('enderman', cell_size, cell_size)
            ex = margin_x + state.enderman['pos'][1] * cell_size; ey = margin_y + state.enderman['pos'][0] * cell_size
            pygame.draw.rect(self.screen, ENDERMAN_PURPLE, (ex, ey, cell_size, cell_size), 2)
            if enderman_img: self.screen.blit(enderman_img, (ex, ey))

        ghast_size = int(cell_size * 3.5); ghast_img = self.get_scaled_asset('ghast', ghast_size, ghast_size)
        for g in state.ghasts:
            shadow_x = margin_x + g['pos'][1] * cell_size + cell_size//2; shadow_y = margin_y + g['pos'][0] * cell_size + UI_HEIGHT + cell_size 
            pygame.draw.circle(self.screen, GHAST_SHADOW, (int(shadow_x), int(shadow_y)), cell_size//2)
            screen_gx = margin_x + g['pos'][1] * cell_size - ghast_size//2; screen_gy = margin_y + g['pos'][0] * cell_size - ghast_size//2
            if ghast_img: self.screen.blit(ghast_img, (screen_gx, screen_gy))

        fire_img = self.get_scaled_asset('fire_charge', cell_size, cell_size)
        for fc in state.fire_charges:
            fx = margin_x + fc['pos'][1] * cell_size; fy = margin_y + fc['pos'][0] * cell_size
            if fire_img: self.screen.blit(fire_img, (fx, fy))
            else: pygame.draw.circle(self.screen, ORANGE, (int(fx+cell_size//2), int(fy+cell_size//2)), cell_size//3)

        px, py = state.player_pos; steve = self.get_scaled_asset('steve', cell_size, cell_size); p_x = margin_x + py * cell_size; p_y = margin_y + px * cell_size
        if state.invincible_timer > 0: pygame.draw.circle(self.screen, INVINCIBLE_GOLD, (p_x+cell_size//2, p_y+cell_size//2), cell_size, 3)
        if steve: self.screen.blit(steve, (p_x, p_y))
        else: pygame.draw.rect(self.screen, CYAN, (p_x+3, p_y+3, cell_size-6, cell_size-6))

        gx, gy = state.goal_pos; portal = self.get_scaled_asset('portal', cell_size, cell_size); g_x = margin_x + gy * cell_size; g_y = margin_y + gx * cell_size
        if portal: self.screen.blit(portal, (g_x, g_y))
        else: pygame.draw.rect(self.screen, GREEN, (g_x, g_y, cell_size, cell_size))
        
        if state.mode == "vs_ai" and not state.has_key: pygame.draw.rect(self.screen, WHITE, (g_x, g_y, cell_size, cell_size), 3)

        if state.mode == "solo" and state.game_won:
             if state.ai_draw_index > 1:
                points = []
                for i in range(int(state.ai_draw_index)):
                    r, c = state.ai_path_display[i]; points.append((margin_x + c * cell_size + cell_size // 2, margin_y + r * cell_size + cell_size // 2))
                if len(points) > 1: pygame.draw.lines(self.screen, RED, False, points, 3)

        pygame.draw.rect(self.screen, (0,0,0), (0,0, SCREEN_WIDTH, UI_HEIGHT)); pygame.draw.line(self.screen, WHITE, (0, UI_HEIGHT), (SCREEN_WIDTH, UI_HEIGHT), 2)
        
        status = ""
        if state.mode == "solo": status = f"Steps: {len(state.path_taken)} | 'P' to Pause"
        elif state.mode == "vs_ai": status = f"YOU: {state.user_score} | AI: {state.bots[0]['score'] if state.bots else 0}"
        elif state.mode == "hell": status = f"Score: {state.user_score} | Pearls(1): {state.pearl_count}/5 | Drink(2): {'Ready' if state.has_energy_drink else 'Empty'}"
        
        txt = self.font_ui.render(status, True, WHITE); self.screen.blit(txt, (20, (UI_HEIGHT - txt.get_height())//2))
        
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
            txt = "GO!" if rem <= 0 else str(int(rem)); surf = self.font_huge.render(txt, True, COUNTDOWN_COLOR)
            self.screen.blit(surf, (SCREEN_WIDTH//2 - surf.get_width()//2, SCREEN_HEIGHT//2 - surf.get_height()//2))
        elif state.paused: self.draw_overlay("PAUSED", "Press 'P' to Resume | 'R' to Menu")
        elif not state.game_active and not state.game_won: self.draw_overlay(state.game_over_text, "Press 'R' to Return to Menu", False, state.death_type)
        elif state.mode == "solo" and state.game_won and state.ai_draw_index >= len(state.ai_path_display): self.draw_overlay(state.game_over_text, "Press 'R' to Return to Menu")
        elif (state.mode != "solo" and state.game_won and not state.game_active):
             use_win_gif = (state.mode in ["vs_ai", "hell"])
             self.draw_overlay(state.game_over_text, "Press 'R' to Return to Menu", use_win_gif, state.death_type)

    def draw_overlay(self, title_text, sub_text, show_win_gif=False, death_type=None):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill(OVERLAY_BG); self.screen.blit(overlay, (0,0))
        cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
        asset_to_show = None; is_static = False
        if show_win_gif is True: asset_to_show = 'win'
        elif death_type == "explosion":
             if "TNT" in title_text: asset_to_show = 'tnt'; is_static = True
             elif "CREEPER" in title_text: asset_to_show = 'creeper_death'; is_static = True
             elif "ENDERMAN" in title_text: asset_to_show = 'enderman'; is_static = True
             elif "GHAST" in title_text: asset_to_show = 'ghast'; is_static = True
        
        text_y_start = cy - 50
        if asset_to_show and self.assets.get(asset_to_show):
            asset_data = self.assets[asset_to_show]; img = None
            if isinstance(asset_data, list) and len(asset_data) > 0:
                frame_delay = 50 if asset_to_show == 'explosion' else 100
                frame_idx = (pygame.time.get_ticks() // frame_delay) % len(asset_data)
                img = asset_data[frame_idx]
            elif isinstance(asset_data, pygame.Surface): img = asset_data

            if img:
                target_height = SCREEN_HEIGHT // 4; w, h = img.get_size(); scale_factor = target_height / h
                new_w, new_h = int(w * scale_factor), int(h * scale_factor)
                scaled_img = pygame.transform.scale(img, (new_w, new_h))
                img_rect = scaled_img.get_rect(center=(cx, cy - 100))
                self.screen.blit(scaled_img, img_rect); text_y_start = img_rect.bottom + 20
        
        t_surf = self.font_large.render(title_text, True, YELLOW); s_surf = self.font_small.render(sub_text, True, WHITE)
        self.screen.blit(t_surf, (cx - t_surf.get_width()//2, text_y_start)); self.screen.blit(s_surf, (cx - s_surf.get_width()//2, text_y_start + 70))

    def draw_menu_new(self, menu_state):
        # 1. Draw Background (Panorama)
        self.screen.fill(BLACK)
        if self.menu_panorama:
            # Simple scrolling logic
            # Draw twice to loop
            scroll = int(menu_state.scroll_x) % self.menu_panorama.get_width()
            self.screen.blit(self.menu_panorama, (-scroll, 0))
            self.screen.blit(self.menu_panorama, (-scroll + self.menu_panorama.get_width(), 0))
        
        # 2. Fade In Overlay logic
        time_elapsed = pygame.time.get_ticks() - menu_state.start_ticks
        
        # Calculate Opacities based on time sequence
        bg_fade = max(0, 255 - min(255, (time_elapsed) // 4)) # Fades out black overlay
        title_alpha = min(255, max(0, (time_elapsed - 1000) // 4)) if time_elapsed > 1000 else 0
        opt_alpha = min(255, max(0, (time_elapsed - 2000) // 4)) if time_elapsed > 2000 else 0
        tips_alpha = min(255, max(0, (time_elapsed - 3000) // 4)) if time_elapsed > 3000 else 0
        
        # Draw base black overlay if fading in
        if bg_fade > 0:
            fade_s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); fade_s.fill(BLACK); fade_s.set_alpha(bg_fade)
            self.screen.blit(fade_s, (0,0))

        # 3. Draw Title (Left Aligned)
        if title_alpha > 0:
            title_s = self.font_title.render("Steve In Maze", True, WHITE)
            title_s.set_alpha(title_alpha)
            # Drop shadow
            shadow_s = self.font_title.render("Steve In Maze", True, (50,50,50)); shadow_s.set_alpha(title_alpha)
            self.screen.blit(shadow_s, (54, 104))
            self.screen.blit(title_s, (50, 100))
            
            # Splash Text
            # Pulse/Rotate splash
            scale = 1.0 + math.sin(pygame.time.get_ticks() * 0.004) * 0.05
            angle = math.sin(pygame.time.get_ticks() * 0.008) * 5
            
            # Create surface for text with outline
            splash_base = self.font_splash.render(menu_state.splash_text, True, YELLOW)
            w, h = splash_base.get_size()
            outlined_surf = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
            
            # Draw outline (black)
            black_surf = self.font_splash.render(menu_state.splash_text, True, BLACK)
            for dx in [-2, 0, 2]:
                for dy in [-2, 0, 2]:
                    if dx != 0 or dy != 0:
                        outlined_surf.blit(black_surf, (dx + 2, dy + 2))
                        
            # Draw main text
            outlined_surf.blit(splash_base, (2, 2))
            
            # Apply alpha if needed
            if title_alpha < 255:
                outlined_surf.set_alpha(title_alpha)
                
            splash_rot = pygame.transform.rotozoom(outlined_surf, angle, scale)
            self.screen.blit(splash_rot, (50 + title_s.get_width() - 20, 100))

        # 4. Draw Options (Left Aligned)
        if opt_alpha > 0:
            start_y = 300
            for i, opt in enumerate(menu_state.options):
                # Button Rect
                btn_w, btn_h = 400, 60
                btn_x, btn_y = 100, start_y
                btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                
                # Check Selection
                is_selected = (i == menu_state.selected_index)
                
                # Colors
                bg_col = BUTTON_COLOR
                border_col = BUTTON_HOVER_BORDER if is_selected else BUTTON_BORDER
                text_col = YELLOW if is_selected else WHITE
                
                # Draw Button (Blocky Bevel Style)
                pygame.draw.rect(self.screen, BLACK, btn_rect) # Outer black border
                inner_rect = pygame.Rect(btn_x + 2, btn_y + 2, btn_w - 4, btn_h - 4)
                pygame.draw.rect(self.screen, bg_col, inner_rect) # Inner color
                
                # If selected, maybe add white corners or something?
                if is_selected:
                    # Draw white border inside
                    pygame.draw.rect(self.screen, WHITE, inner_rect, 2)
                    
                    # --- NEW: Draw Description Tooltip to the right ---
                    desc_text = menu_state.descriptions[i]
                    
                    # Render text first to get size
                    desc_s = self.font_desc.render(desc_text, True, WHITE) # Use Blocky font
                    desc_w = desc_s.get_width()
                    desc_h = desc_s.get_height()
                    
                    # Dynamic Box Size
                    tooltip_w = desc_w + 40 # Padding
                    tooltip_h = desc_h + 30 # Padding
                    
                    # Tooltip Position (Increased distance)
                    tooltip_x = btn_x + btn_w + 60 # Increased from 20
                    tooltip_rect = pygame.Rect(tooltip_x, btn_y + (btn_h - tooltip_h)//2, tooltip_w, tooltip_h) # Center vertically relative to button
                    
                    # Draw Tooltip Background
                    s = pygame.Surface((tooltip_w, tooltip_h), pygame.SRCALPHA)
                    s.fill((0, 0, 0, 180)) 
                    self.screen.blit(s, (tooltip_x, btn_y + (btn_h - tooltip_h)//2))
                    pygame.draw.rect(self.screen, (100, 100, 100), tooltip_rect, 2) 
                    
                    # Draw Description Text
                    desc_rect = desc_s.get_rect(center=tooltip_rect.center)
                    self.screen.blit(desc_s, desc_rect)
                
                # Draw Text
                txt_s = self.font_option.render(opt, True, text_col)
                txt_s.set_alpha(opt_alpha)
                
                # Center text in button
                txt_rect = txt_s.get_rect(center=btn_rect.center)
                self.screen.blit(txt_s, txt_rect)
                
                start_y += 80

        # 5. Draw Tips (Right Aligned Box)
        if tips_alpha > 0:
            box_w, box_h = 320, 150
            box_x = SCREEN_WIDTH - box_w - 50
            box_y = 300
            
            # Draw semi-transparent box
            box_s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            box_s.fill((0, 0, 0, 150))
            self.screen.blit(box_s, (box_x, box_y))
            
            # Draw Text wrapped
            # Use current tip and alpha from menu state
            tip_s = self.font_tips.render(menu_state.current_tip, True, WHITE)
            # Apply fade alpha
            final_alpha = min(tips_alpha, menu_state.tip_alpha)
            tip_s.set_alpha(final_alpha)
            
            # Simple wrapping for long tips
            words = menu_state.current_tip.split(' ')
            lines = []
            curr_line = ""
            for word in words:
                test_line = curr_line + word + " "
                if self.font_tips.size(test_line)[0] < box_w - 20:
                    curr_line = test_line
                else:
                    lines.append(curr_line)
                    curr_line = word + " "
            lines.append(curr_line)
            
            text_y = box_y + 20
            for line in lines:
                l_s = self.font_tips.render(line, True, WHITE)
                l_s.set_alpha(final_alpha)
                self.screen.blit(l_s, (box_x + 10, text_y))
                text_y += 30