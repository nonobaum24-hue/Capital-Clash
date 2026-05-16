import pygame
import os
from settings import settings


def settings_loop(settings, screen):
    game_screen = screen  # Use the existing screen surface passed from the start menu
    game_screen.fill((0, 0, 0))  # Clear the screen with black
    game_settings = settings  # Load settings from file or use defaults
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    scrn_surf = pygame.Surface((game_settings.width, game_settings.height), pygame.SRCALPHA)  # surface for drawing the menu

    running = True

    while running:
        game_screen.fill((0, 0, 0))  # Clear the screen with black
        setting_variables = game_settings.get_settings()  # Display settings menu and update settings object

        

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False  # Exit the settings loop if the window is closed

        game_screen.flip()  # Update the display to show the settings menu
