import pygame

class Button:
    def __init__(self, x, y, width, height, text, color=(100, 100, 100), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hovered = False
    
    def draw(self, surface, font):
        color = tuple(min(c + 30, 255) for c in self.color) if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2)
        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.hovered

class Dropdown:
    def __init__(self, x, y, width, height, options, default_index=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = default_index
        self.open = False
        self.hovered = False
    
    def draw(self, surface, font):
        color = (120, 120, 120) if self.hovered else (100, 100, 100)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2)
        
        text_surf = font.render(self.options[self.selected_index], True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(self.rect.x + self.rect.width // 2, self.rect.y + self.rect.height // 2))
        surface.blit(text_surf, text_rect)
        
        if self.open:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height * (i + 1), self.rect.width, self.rect.height)
                pygame.draw.rect(surface, (80, 80, 80), option_rect)
                pygame.draw.rect(surface, (150, 150, 150), option_rect, 1)
                opt_surf = font.render(option, True, (255, 255, 255))
                opt_rect = opt_surf.get_rect(center=option_rect.center)
                surface.blit(opt_surf, opt_rect)
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def handle_click(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mouse_pos):
                self.open = not self.open
            elif self.open:
                for i, option in enumerate(self.options):
                    option_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height * (i + 1), self.rect.width, self.rect.height)
                    if option_rect.collidepoint(mouse_pos):
                        self.selected_index = i
                        self.open = False
                        return True
        return False
    
    def get_selected(self):
        return self.options[self.selected_index]

class Slider:
    def __init__(self, x, y, width, height, min_val=0, max_val=100, initial_val=50):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.dragging = False
    
    def draw(self, surface, font, label=""):
        pygame.draw.rect(surface, (60, 60, 60), self.rect)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2)
        
        handle_x = self.rect.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        handle_rect = pygame.Rect(handle_x - 5, self.rect.y - 5, 10, self.rect.height + 10)
        pygame.draw.rect(surface, (200, 200, 200), handle_rect)
        
        value_text = font.render(f"{label}: {int(self.value)}", True, (255, 255, 255))
        surface.blit(value_text, (self.rect.x, self.rect.y - 25))
    
    def update(self, mouse_pos):
        if self.dragging:
            self.value = max(self.min_val, min(self.max_val, 
                            self.min_val + (mouse_pos[0] - self.rect.x) / self.rect.width * (self.max_val - self.min_val)))
    
    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            handle_x = self.rect.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
            if abs(mouse_pos[0] - handle_x) < 15 and self.rect.y - 5 <= mouse_pos[1] <= self.rect.y + self.rect.height + 5:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
