import pygame
import os
import random
import math
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class SoundManager:
    """THE DJ: Handles all music and sound effects logic."""
    def __init__(self):
        self.sounds = {}
        self.music_tracks = []
        self.current_music = None
        self.load_sounds()
        self.load_music_tracks()

    def load_sounds(self):
        # Using relative paths. Ensure 'assets' folder is in the same directory as this script.
        # Format: (Key, Path)
        sfx_data = {
            'walk': 'assets/Music/walk/walk.mp3',
            'pearl': 'assets/Music/Drink_Pearl/Pearl.mp3',
            'drink': 'assets/Music/Drink_Pearl/Drinking.mp3',
            'creeper': 'assets/Music/Creeper/Creeper.mp3',
            'enderman': 'assets/Music/Enderman/Enderman.mp3',
            'ghast_1': 'assets/Music/Ghast/Cry1.mp3',
            'ghast_2': 'assets/Music/Ghast/Cry2.mp3',
            'ghast_3': 'assets/Music/Ghast/Cry3.mp3',
            'ghast_4': 'assets/Music/Ghast/Cry4.mp3',
            'piglin_1': 'assets/Music/Piglin/Piglin1.mp3',
            'piglin_2': 'assets/Music/Piglin/Piglin2.mp3',
        }

        print("--- Loading Sounds ---")
        for key, rel_path in sfx_data.items():
            # Use resource_path to find the file inside the .exe structure
            abs_path = resource_path(rel_path)
            try:
                if not os.path.exists(abs_path):
                    print(f"FAILED: File not found: {abs_path}")
                    self.sounds[key] = None
                    continue
                
                # Using 'with open' is more robust for loading binary audio data on Windows
                with open(abs_path, 'rb') as f:
                    sound = pygame.mixer.Sound(f)
                
                self.sounds[key] = sound
                print(f"SUCCESS: Loaded {key}")
            except Exception as e:
                print(f"ERROR: Could not load {key} from {abs_path}. Reason: {e}")
                self.sounds[key] = None

    def load_music_tracks(self):
        # Use resource_path to find the background music folder
        bg_folder = resource_path('assets/Music/Background/')
        try:
            if os.path.exists(bg_folder):
                for f in os.listdir(bg_folder):
                    if f.lower().endswith('.mp3'):
                        self.music_tracks.append(os.path.join(bg_folder, f))
            else:
                print(f"Warning: Music folder not found at {bg_folder}")
        except Exception as e:
            print(f"Warning: Could not scan music directory. {e}")

    def play_bgm(self, context):
        """
        Context: 'menu', 'hell', 'normal'.
        Logic: 
        - Hell: Must play Pigstep.
        - Menu/Normal: Play any non-Pigstep track.
          CRITICAL: If already playing a non-Pigstep track, DO NOT restart/change it.
        """
        try:
            # 1. Identify what kind of track we need
            need_pigstep = (context == 'hell')
            
            # 2. Check what is currently playing
            is_playing_pigstep = (self.current_music is not None and 'Pigstep' in self.current_music)
            
            # 3. Decide if we need to switch
            if need_pigstep:
                if not is_playing_pigstep:
                    # Switch TO Pigstep
                    target = next((t for t in self.music_tracks if 'Pigstep' in t), None)
                    if target: self._start_track(target, volume=0.1) # 10% Volume for Pigstep
            else:
                # We need Standard Music
                if is_playing_pigstep or self.current_music is None:
                    # We are coming from Hell (or startup). Switch to random standard track.
                    choices = [t for t in self.music_tracks if 'Pigstep' not in t]
                    if choices:
                        target = random.choice(choices)
                        self._start_track(target, volume=0.3) # 30% Volume for others
                # ELSE: We are already playing standard music. Continue uninterrupted.

        except Exception as e:
            print(f"Error playing music: {e}")

    def _start_track(self, track_path, volume=0.3):
        """Internal helper to load and play a track"""
        pygame.mixer.music.load(track_path)
        pygame.mixer.music.play(-1) # Loop forever
        pygame.mixer.music.set_volume(volume)
        self.current_music = track_path

    def play_sfx(self, key, player_pos=None, source_pos=None):
        # We disabled SFX for now as per your request, but the method stays to prevent crashes
        pass