def startmenu():
    import os
    import pygame

    width  = 1250   # Fensterbreite in Pixeln
    height = 720    # Fensterhöhe in Pixeln

    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Capital Crush")

    running = True

    while running:
        #hier gibt es ein Startmenu wo man vielleicht Einstellungen oder Skins anpassen oder einfach nur starten kann
        running = False

    return screen