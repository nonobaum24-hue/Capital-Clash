import pygame

class Button:
    """
    Generic button component with hover detection and click handling.
    
    The button brightens when hovered and fires is_clicked() when clicked.
    """
    def __init__(self, x, y, width, height, text, color=(100, 100, 100), text_color=(255, 255, 255)):
        """
        Parameters
        ----------
        x, y           – top-left position
        width, height  – button dimensions
        text           – button label
        color          – RGB fill colour (default: grey)
        text_color     – RGB text colour (default: white)
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hovered = False
    
    def draw(self, surface, font):
        """
        Draw the button. Brightens by 30 per RGB channel if hovered.
        Includes a light grey border (2 px) and centred text.
        """
        # Brighten the button if hovered, otherwise use the base colour
        color = tuple(min(c + 30, 255) for c in self.color) if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2)  # border
        
        # Render and centre the text
        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def update(self, mouse_pos):
        """Update hover state based on current mouse position."""
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, event):
        """Return True if the button was clicked this frame."""
        return event.type == pygame.MOUSEBUTTONDOWN and self.hovered


class Dropdown:
    """
    Dropdown menu component for selecting one option from a list.
    
    Clicking toggles the menu open/closed. Selecting an option closes the menu
    and updates selected_index.
    """
    def __init__(self, x, y, width, height, options, default_index=0):
        """
        Parameters
        ----------
        x, y           – top-left position
        width, height  – button dimensions
        options        – list of strings to choose from
        default_index  – initially selected index (default: 0)
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = default_index
        self.open = False  # True if the dropdown menu is visible
        self.hovered = False
    
    def draw(self, surface, font):
        """
        Draw the dropdown button and (if open) all option rows below it.
        
        Button is lighter when hovered. Each option row is drawn below the button,
        with a subtle border.
        """
        # Draw the main button (lighter if hovered)
        color = (120, 120, 120) if self.hovered else (100, 100, 100)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2)
        
        # Draw the currently selected option on the button
        text_surf = font.render(self.options[self.selected_index], True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(self.rect.x + self.rect.width // 2, self.rect.y + self.rect.height // 2))
        surface.blit(text_surf, text_rect)
        
        # Draw all options if the dropdown is open
        if self.open:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height * (i + 1), self.rect.width, self.rect.height)
                pygame.draw.rect(surface, (80, 80, 80), option_rect)
                pygame.draw.rect(surface, (150, 150, 150), option_rect, 1)  # subtle border
                opt_surf = font.render(option, True, (255, 255, 255))
                opt_rect = opt_surf.get_rect(center=option_rect.center)
                surface.blit(opt_surf, opt_rect)
    
    def update(self, mouse_pos):
        """Update hover state based on current mouse position."""
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def handle_click(self, event, mouse_pos):
        """
        Handle click events: toggle open on button click, or select option if menu is open.
        
        Returns True if an option was selected, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Click on the button: toggle the dropdown open/closed
            if self.rect.collidepoint(mouse_pos):
                self.open = not self.open
            # Click on an option (if menu is open): select it and close the menu
            elif self.open:
                for i, option in enumerate(self.options):
                    option_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height * (i + 1), self.rect.width, self.rect.height)
                    if option_rect.collidepoint(mouse_pos):
                        self.selected_index = i
                        self.open = False
                        return True
        return False
    
    def get_selected(self):
        """Return the currently selected option string."""
        return self.options[self.selected_index]


class Slider:
    """
    Horizontal slider component for selecting a numeric value in a range.
    
    Click and drag the handle to adjust the value. The slider displays the
    current value as text above it.
    """
    def __init__(self, x, y, width, height, min_val=0, max_val=100, initial_val=50):
        """
        Parameters
        ----------
        x, y           – top-left position
        width, height  – slider dimensions
        min_val        – minimum selectable value (default: 0)
        max_val        – maximum selectable value (default: 100)
        initial_val    – starting value (default: 50)
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.dragging = False  # True while the handle is being dragged
    
    def draw(self, surface, font, label=""):
        """
        Draw the slider track, handle, and value label.
        
        Parameters
        ----------
        surface – pygame surface to draw on
        font    – font for rendering the value label
        label   – optional text prefix (e.g., "Master Volume")
        """
        # Draw the track (dark background)
        pygame.draw.rect(surface, (60, 60, 60), self.rect)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2)  # border
        
        # Calculate handle position based on current value
        handle_x = self.rect.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        handle_rect = pygame.Rect(handle_x - 5, self.rect.y - 5, 10, self.rect.height + 10)
        pygame.draw.rect(surface, (200, 200, 200), handle_rect)
        
        # Draw the value label above the slider
        value_text = font.render(f"{label}: {int(self.value)}", True, (255, 255, 255))
        surface.blit(value_text, (self.rect.x, self.rect.y - 25))
    
    def update(self, mouse_pos):
        """
        Update the slider value based on dragging.
        
        If currently dragging, move the value to match the mouse x-position
        (clamped to the valid range).
        """
        if self.dragging:
            # Map mouse x-position to value in [min_val, max_val]
            self.value = max(self.min_val, min(self.max_val, 
                            self.min_val + (mouse_pos[0] - self.rect.x) / self.rect.width * (self.max_val - self.min_val)))
    
    def handle_event(self, event, mouse_pos):
        """
        Handle mouse down and mouse up events to start/stop dragging.
        
        The handle is considered clickable if the mouse is within 15 px horizontally
        and within the slider's vertical bounds.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Calculate current handle position
            handle_x = self.rect.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
            # Start dragging if the mouse clicked on the handle (±15 px)
            if abs(mouse_pos[0] - handle_x) < 15 and self.rect.y - 5 <= mouse_pos[1] <= self.rect.y + self.rect.height + 5:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            # Stop dragging on mouse release
            self.dragging = False


class StartButton:
    """
    Start Game Button for the main menu.
    
    Uses a semi-transparent white background with black text.
    """
    def __init__(self, x, y, width, height, text="Start Game"):
        """
        Parameters
        ----------
        x, y           – top-left position
        width, height  – button dimensions
        text           – button label (default: "Start Game")
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = (255, 255, 255, 160)  # RGBA: white, 63 % opaque
        self.hovered = False

    def draw(self, screen, font):
        """Draw the button with semi-transparent white background and black text."""
        # Use SRCALPHA surface so the semi-transparent fill works correctly
        but_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        but_surf.fill(self.color)
        screen.blit(but_surf, self.rect)
        
        # Render and centre the text in black
        text_surf = font.render(self.text, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def update(self, mouse_pos):
        """Update hover state based on current mouse position."""
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        """Return True if the button was clicked this frame."""
        return event.type == pygame.MOUSEBUTTONDOWN and self.hovered


class SettingsButton:
    """
    Settings Button for the main menu.
    
    Opens the settings menu when clicked.
    Uses a semi-transparent white background with black text.
    """
    def __init__(self, x, y, width, height, settings_obj, screen, text="Settings"):
        """
        Parameters
        ----------
        x, y             – top-left position
        width, height    – button dimensions
        settings_obj     – the settings object to pass to settings_loop()
        screen           – the pygame screen surface to pass to settings_loop()
        text             – button label (default: "Settings")
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = (255, 255, 255, 160)  # RGBA: white, 63 % opaque
        self.hovered = False
        self.settings_obj = settings_obj
        self.screen = screen

    def draw(self, screen, font):
        """Draw the button with semi-transparent white background and black text."""
        # Use SRCALPHA surface so the semi-transparent fill works correctly
        but_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        but_surf.fill(self.color)
        screen.blit(but_surf, self.rect)
        
        # Render and centre the text in black
        text_surf = font.render(self.text, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def update(self, mouse_pos):
        """Update hover state based on current mouse position."""
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        """Return True if the button was clicked this frame."""
        return event.type == pygame.MOUSEBUTTONDOWN and self.hovered
