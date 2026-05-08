import pygame
import os

# =============================================================================
# start_classes.py  –  Classes for Capital Clash
# =============================================================================
# This file contains the class definitions for the game, including Player, Enemy, and Projectile.
# Each class has attributes and methods relevant to its role in the game, such as movement, health, and interactions with other objects.
# =============================================================================

class button:
    def __init__(self):
        self.color = (255, 255, 255, 160)  # white color for the button

    def draw(self, screen,):
        but_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)  # surface for the button
        but_surf.fill(self.color)
        screen.blit(but_surf, (self.x, self.y))  # draw the button surface onto the main screen
        font = pygame.font.SysFont(None, 36)  # default font, size 36
        text_surf = font.render(self.text, True, (0, 0, 0))  # render the button text in black
        text_rect = text_surf.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))  # center the text on the button
        screen.blit(text_surf, text_rect)

        if self.check_click():
            print("Start button clicked!")  # Placeholder for actual start game logic
            return True
        return False

    def is_clicked(self, pos):
        return (self.x <= pos[0] <= self.x + self.width) and (self.y <= pos[1] <= self.y + self.height)
    
class start_button(button):
    def __init__(self):
        super().__init__()  # call the base class constructor
        self.width = 200
        self.height = 80
        self.x = 1250 // 2 - self.width // 2  # center horizontally
        self.y = 720 // 2 - self.height // 2  # center vertically
        self.text = "Start Game"

    def check_click(self):
        if pygame.mouse.get_pressed()[0] and self.is_clicked(pygame.mouse.get_pos()):
            return True
        return False