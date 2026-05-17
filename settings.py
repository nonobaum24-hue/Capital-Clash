import os

class settings:
    def __init__(self):
        # Window settings
        self.width = 1250                   # window width in pixels
        self.height = 720                   # window height in pixels
        self.__title = "Capital Crush"        # window title
        
        # Game settings
        self.__fps = 60                       # frames per second
        self.__round_duration = 60            # main round duration in seconds
        self.__round_ticks = 3600             # main round in ticks (60 seconds * 60 fps)
        self.__end_tick_buffer = 7            # seconds to wait before boss fight after round ends

        # Player settings
        self.__player_health = 100            # starting health
        self.__player_scale = 0.25            # sprite scale factor
        self.__player_speed = 5               # pixels per frame during movement
        self.__player_attack_damage = 30      # damage per hit
        self.__player_attack_cooldown = 30    # frames between attacks
        self.__player_exception_radius = 150  # safe spawn distance around player

        # Audio settings
        self.master_volume = 50              # master volume (0.0 to 1.0)
        self.music_volume = 50             # music volume (0.0 to 1.0)
        self.sfx_volume = 50                 # sound effects volume (0.0 to 1.0)
        
        # Display settings
        self.__skin = "default"               # character skin (e.g., "default", "red", "blue")
        self.__background_color = (30, 30, 30)  # menu background fill color
        self.__background_opacity = 100       # menu background opacity (0-255)
        self.settings_file = os.path.join(os.path.dirname(__file__), "user_settings.py")
        self.load_settings()
    
    def get_settings(self):
        return {
            "width": self.width,
            "height": self.height,
            "title": self.__title,
            "fps": self.__fps,
            "round_duration": self.__round_duration,
            "round_ticks": self.__round_ticks,
            "end_tick_buffer": self.__end_tick_buffer,
            "player_health": self.__player_health,
            "player_scale": self.__player_scale,
            "player_speed": self.__player_speed,
            "player_attack_damage": self.__player_attack_damage,
            "player_attack_cooldown": self.__player_attack_cooldown,
            "player_exception_radius": self.__player_exception_radius,
            "master_volume": self.master_volume,
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "skin": self.__skin,
            "background_color": self.__background_color,
            "background_opacity": self.__background_opacity
        }
    
    def save_settings(self):
        content = f"""# Auto-generated user settings
width = {self.width}
height = {self.height}
master_volume = {self.master_volume}
music_volume = {self.music_volume}
sfx_volume = {self.sfx_volume}
"""
        with open(self.settings_file, 'w') as f:
            f.write(content)
    
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                namespace = {}
                with open(self.settings_file, 'r') as f:
                    exec(f.read(), namespace)
                self.width = namespace.get("width", 1250)
                self.height = namespace.get("height", 720)
                self.master_volume = namespace.get("master_volume", 50)
                self.music_volume = namespace.get("music_volume", 50)
                self.sfx_volume = namespace.get("sfx_volume", 50)
            except:
                pass

    def window_settings(self, width, height):
        self.height = height
        self.width = width

    def volume_settings(self, master_volume, music_volume, sfx_volume):
        self.master_volume = master_volume
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume
