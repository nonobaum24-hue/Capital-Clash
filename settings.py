class settings:
    def __init__(self):
        # Window settings
        self.width = 1250                   # window width in pixels
        self.height = 720                   # window height in pixels
        self.title = "Capital Crush"        # window title
        
        # Game settings
        self.fps = 60                       # frames per second
        self.round_duration = 60            # main round duration in seconds
        self.round_ticks = 3600             # main round in ticks (60 seconds * 60 fps)
        self.end_tick_buffer = 7            # seconds to wait before boss fight after round ends
        
        # Player settings
        self.player_health = 100            # starting health
        self.player_scale = 0.25            # sprite scale factor
        self.player_speed = 5               # pixels per frame during movement
        self.player_attack_damage = 30      # damage per hit
        self.player_attack_cooldown = 30    # frames between attacks
        self.player_exception_radius = 150  # safe spawn distance around player
        
        # Audio settings
        self.master_volume = 1              # master volume (0.0 to 1.0)
        self.music_volume = 1             # music volume (0.0 to 1.0)
        self.sfx_volume = 1                 # sound effects volume (0.0 to 1.0)
        
        # Display settings
        self.skin = "default"               # character skin (e.g., "default", "red", "blue")
        self.background_color = (30, 30, 30)  # menu background fill color
        self.background_opacity = 100       # menu background opacity (0-255)

