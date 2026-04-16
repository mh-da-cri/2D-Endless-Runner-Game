"""
Game Manager - Quản lý State Machine
Điều phối luồng game: Menu → Play → Game Over → ...
Chịu trách nhiệm chuyển đổi giữa các state.
"""

import pygame


class GameManager:
    """
    Quản lý trạng thái game (State Machine).
    
    Mỗi state phải có 3 phương thức:
    - handle_events(events): Xử lý input
    - update(): Cập nhật logic
    - draw(): Vẽ lên màn hình
    """
    
    def __init__(self, screen):
        """
        Khởi tạo GameManager.
        
        Args:
            screen: pygame.Surface - màn hình game chính
        """
        self.screen = screen
        self.current_state = None
        
        # Khởi tạo với MenuState
        from states.menu_state import MenuState
        self.current_state = MenuState(self)
    
    def change_state(self, new_state):
        """
        Chuyển sang state mới.
        
        Args:
            new_state: Instance của state mới (MenuState, PlayState, GameOverState)
        """
        self.current_state = new_state
    
    def handle_events(self, events):
        """
        Chuyển tiếp events cho state hiện tại.
        
        Args:
            events: List các pygame event
        """
        if self.current_state:
            self.current_state.handle_events(events)
    
    def update(self):
        """Chuyển tiếp update cho state hiện tại."""
        if self.current_state:
            self.current_state.update()
    
    def draw(self):
        """Chuyển tiếp draw cho state hiện tại."""
        if self.current_state:
            self.current_state.draw()
