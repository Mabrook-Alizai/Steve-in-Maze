import pygame
import sys
from settings import *
from sound_manager import SoundManager
from game_engine import GameState, MenuState
from renderer import GameRenderer

def main():
    # --- INITIALIZATION ---
    # settings.py already initializes pygame and mixer, so we just get the clock here
    clock = pygame.time.Clock()
    
    # We must set the screen mode here (or in settings, but usually main controls the window)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Steve In Maze")

    # --- LOAD MODULES ---
    try:
        sound_manager = SoundManager()
        renderer = GameRenderer(screen)
        # Pass sound_manager to menu so it can play the start music
        menu = MenuState(sound_manager)
    except Exception as e:
        print(f"CRITICAL ERROR Initializing Modules: {e}")
        return

    game = None 
    
    # --- MAIN LOOP ---
    while True:
        clock.tick(FPS)
        
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if game:
                # --- GAME INPUT ---
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Return to Menu
                        game = None
                        menu = MenuState(sound_manager) # Reset menu to fade in again
                        
                    elif event.key == pygame.K_p: 
                        game.paused = not game.paused
                        
                    elif event.key == pygame.K_r:
                        # Restart / Return to Menu depending on state
                        if game.paused or not game.game_active or game.game_won: 
                            game = None 
                            menu = MenuState(sound_manager)
                            
                    # Hell Mode Items
                    elif event.key == pygame.K_1 and game.mode == "hell": 
                        game.use_pearl()
                    elif event.key == pygame.K_2 and game.mode == "hell": 
                        game.use_energy_drink()
            else:
                # --- MENU INPUT ---
                if event.type == pygame.KEYDOWN:
                    choice = menu.handle_input(event)
                    if choice is not None:
                        # Start Game based on choice
                        # 0=Easy, 1=Normal, 2=Hard, 3=VS, 4=Hell, 5=Quit
                        if choice == 0: game = GameState(12, "solo", sound_manager)
                        elif choice == 1: game = GameState(18, "solo", sound_manager)
                        elif choice == 2: game = GameState(25, "solo", sound_manager)
                        elif choice == 3: game = GameState(25, "vs_ai", sound_manager)
                        elif choice == 4: game = GameState(25, "hell", sound_manager)
                        elif choice == 5: 
                            pygame.quit(); sys.exit()
                        
                        if game: 
                            # Pre-render level for performance (optimization fix #2)
                            renderer.init_level(game)

        # --- UPDATES & DRAWING ---
        if game:
            # Continuous Movement Logic
            if not game.paused and game.game_active:
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
            
            # Update Game Logic
            game.update()
            # Draw Game
            renderer.draw_game(game)
        
        else:
            # Update & Draw Menu
            menu.update()
            renderer.draw_menu_new(menu)
            
        pygame.display.flip()

if __name__ == "__main__":
    main()