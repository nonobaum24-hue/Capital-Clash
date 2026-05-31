import pygame
import os
from settings import settings
from ui_components import Dropdown, Slider, Button


def settings_loop(settings_obj, screen):
    """
    Display and handle the settings menu.
    
    Allows the player to adjust resolution, master volume, music volume,
    and SFX volume. Changes are saved to user_settings.py immediately.
    If resolution changes, the screen is resized before returning.
    
    Parameters
    ----------
    settings_obj : settings
        The game settings object to modify and save
    screen : pygame.Surface
        The existing game screen surface to reuse
    """
    game_screen = screen  # Use the existing screen surface passed from the start menu
    game_screen.fill((0, 0, 0))  # Clear the screen with black
    script_dir = os.path.dirname(os.path.abspath(__file__))

    font_large = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 24)

    # Available resolution options
    resolutions = ["1280x720", "1920x1080", "2560x1440"]
    current_res_index = 0
    if f"{settings_obj.width}x{settings_obj.height}" in resolutions:
        current_res_index = resolutions.index(f"{settings_obj.width}x{settings_obj.height}")

    # UI-Komponenten erstellen
    res_dropdown = Dropdown(200, 100, 300, 40, resolutions, current_res_index)
    master_slider = Slider(200, 200, 300, 20, 0, 100, settings_obj.master_volume)
    music_slider = Slider(200, 280, 300, 20, 0, 100, settings_obj.music_volume)
    sfx_slider = Slider(200, 360, 300, 20, 0, 100, settings_obj.sfx_volume)
    save_button = Button(200, 450, 150, 50, "Speichern")
    back_button = Button(370, 450, 130, 50, "Zurück")

    clock = pygame.time.Clock()
    running = True

    while running:
        clock.tick(60)  # 60 FPS
        game_screen.fill((20, 20, 20))
        mouse_pos = pygame.mouse.get_pos()

        # Display title
        title = font_large.render("Einstellungen", True, (255, 255, 255))
        game_screen.blit(title, (50, 30))

        # Display labels for settings
        res_label = font_small.render("Auflösung:", True, (255, 255, 255))
        game_screen.blit(res_label, (50, 100))

        # UI aktualisieren
        res_dropdown.update(mouse_pos)
        master_slider.update(mouse_pos)
        music_slider.update(mouse_pos)
        sfx_slider.update(mouse_pos)
        save_button.update(mouse_pos)
        back_button.update(mouse_pos)

        # UI zeichnen
        res_dropdown.draw(game_screen, font_small)
        master_slider.draw(game_screen, font_small, "Master Lautstärke")
        music_slider.draw(game_screen, font_small, "Musik Lautstärke")
        sfx_slider.draw(game_screen, font_small, "SFX Lautstärke")
        save_button.draw(game_screen, font_small)
        back_button.draw(game_screen, font_small)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return False  # Exit without saving

            res_dropdown.handle_click(event, mouse_pos)
            master_slider.handle_event(event, mouse_pos)
            music_slider.handle_event(event, mouse_pos)
            sfx_slider.handle_event(event, mouse_pos)

            if save_button.is_clicked(event):
                # Parse and save resolution
                res_str = res_dropdown.get_selected()
                width, height = map(int, res_str.split('x'))
                settings_obj.width = width
                settings_obj.height = height

                # Save volume settings
                settings_obj.master_volume = int(master_slider.value)
                settings_obj.music_volume = int(music_slider.value)
                settings_obj.sfx_volume = int(sfx_slider.value)

                # Persist settings to file
                settings_obj.save_settings()
                
                # Resize the window to new resolution
                game_screen = pygame.display.set_mode((width, height))
                
                running = False
                return True  # Settings saved successfully

            if back_button.is_clicked(event):
                running = False
                return False  # Discard changes without saving

        pygame.display.flip()

    return False
