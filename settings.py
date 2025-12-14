import pygame

# --- INITIALIZE PYGAME FOR SCREEN DIMENSIONS ---
# Pre-init mixer with LOWER BUFFER (1024) - Safe low latency
pygame.mixer.pre_init(44100, -16, 2, 1024)
pygame.init()

# Get the current resolution of the monitor
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# --- CONFIGURATION ---
UI_HEIGHT = 80
FPS = 30 

# --- COLORS ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
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
CREEPER_AURA = (0, 0, 0, 100)
EXPLOSION_MARK = (10, 0, 0, 180)
ENDERMAN_PURPLE = (148, 0, 211)
GHAST_SHADOW = (0, 0, 0, 100)
INVINCIBLE_GOLD = (255, 215, 0)
BUTTON_COLOR = (50, 50, 50)
BUTTON_BORDER = (20, 20, 20)
BUTTON_HOVER_BORDER = (255, 255, 255)

# Reward Colors 
PURPLE = (128, 0, 128)  
ORANGE = (255, 165, 0)  
PINK = (255, 105, 180) 
CYAN_POTION = (0, 255, 255)
BROWN_POTION = (139, 69, 19)
RED_HEART = (255, 0, 0)
GOLD_KEY = (255, 215, 0)
PEARL_COLOR = (0, 255, 200)