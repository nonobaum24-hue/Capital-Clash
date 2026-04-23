from setuptools import setup

# Define the application
APP = ['game.py']

# Data files that need to be included in the bundle
DATA_FILES = [
    # Images for the game UI and sprites
    'marx.png',
    'marx1.png',
    'marx2.png',
    'floor.png',
    'projectile.png',
    'aoe.png',
    'heal.png',
    'revive.png',
    
    # Opponent sprites
    'normal_opp1.png',
    'normal_opp2.png',
    'mini_opp1.png',
    'mini_opp2.png',
    'super_opp1.png',
    'super_opp2.png',
    
    # Boss sprites
    'marx1.png',
    'marx2.png',
    
    # Olaf sprites and animations (from olaf folder)
    ('olaf', ['olaf/origin.png.zip', 'olaf/spritesheet.png.zip']),
    ('olaf/idle_olaf', ['olaf/idle_olaf/idle_olaf.png']),
    ('olaf/walk_olaf', ['olaf/walk_olaf/walk_olaf.png']),
    ('olaf/punch_olaf', [
        'olaf/punch_olaf/punch_olaf_1.png',
        'olaf/punch_olaf/punch_olaf_2.png',
        'olaf/punch_olaf/punch_olaf_3.png'
    ]),
    ('olaf/cast_olaf', [
        'olaf/cast_olaf/cast_olaf_1.png',
        'olaf/cast_olaf/cast_olaf_2.png'
    ]),
    
    # Music and audio
    ('music', ['music/Arbeiterfront_8-Bit.mp3', 'music/the_red_army_is_the_strongest.mp3']),
]

# Options for py2app
OPTIONS = {
    'py2app': {
        'argv_emulation': True,  # Allows command-line arguments
        'includes': [
            'pygame',
            'mainloop',
            'startmenu',
            'boss_fight',
            'boss_classes',
            'game_classes',
            'opp_classes',
            'collectible_classes',
            'resource_path',
        ],
        'resources': DATA_FILES,
        'iconfile': None,  # You can add an icon file here later if you want
        'plist': {
            'NSPrincipalClass': 'NSApplication',
            'CFBundleIdentifier': 'org.capitalclash.game',
        },
    }
}

setup(
    name='Capital Clash',
    version='1.0',
    app=APP,
    data_files=DATA_FILES,
    options=OPTIONS,
    setup_requires=['py2app'],
)
