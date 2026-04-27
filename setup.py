from setuptools import setup

# Define the application
APP = ['game.py']

# Data files that need to be included in the bundle
DATA_FILES = [
    # Assets folder structure
    ('assets/characters', ['assets/characters/logo.png', 'assets/characters/marx.png', 'assets/characters/marx1.png', 'assets/characters/marx2.png']),
    ('assets/environment', ['assets/environment/floor.png']),
    ('assets/enemies/normal', ['assets/enemies/normal/normal_opp1.png', 'assets/enemies/normal/normal_opp2.png']),
    ('assets/enemies/super', ['assets/enemies/super/super_opp1.png', 'assets/enemies/super/super_opp2.png']),
    ('assets/enemies/mini', ['assets/enemies/mini/mini_opp1.png', 'assets/enemies/mini/mini_opp2.png']),
    ('assets/collectibles', ['assets/collectibles/heal.png', 'assets/collectibles/aoe.png', 'assets/collectibles/revive.png']),
    ('assets/effects', ['assets/effects/projectile.png']),
    ('assets/animations/olaf/idle_olaf', ['assets/animations/olaf/idle_olaf/idle_olaf.png']),
    ('assets/animations/olaf/walk_olaf', ['assets/animations/olaf/walk_olaf/walk_olaf.png']),
    ('assets/animations/olaf/punch_olaf', [
        'assets/animations/olaf/punch_olaf/punch_olaf_1.png',
        'assets/animations/olaf/punch_olaf/punch_olaf_2.png',
        'assets/animations/olaf/punch_olaf/punch_olaf_3.png'
    ]),
    ('assets/animations/olaf/cast_olaf', [
        'assets/animations/olaf/cast_olaf/cast_olaf_1.png',
        'assets/animations/olaf/cast_olaf/cast_olaf_2.png'
    ]),
    ('assets/music', ['assets/music/Arbeiterfront_8-Bit.mp3', 'assets/music/the_red_army_is_the_strongest.mp3']),
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
