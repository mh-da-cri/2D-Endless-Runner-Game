"""
Game Over State - Màn hình kết thúc game
Hiển thị điểm số, highscore, và các nút chơi lại / về menu.
"""

import pygame
import sys
import settings
from utils.asset_loader import load_font
from utils.score_manager import save_highscore


class GameOverState:
    """Trạng thái Game Over."""
    
    def __init__(self, game_manager, final_score, previous_highscore):
        """
        Khởi tạo game over state.
        
        Args:
            game_manager: Reference đến GameManager
            final_score: Điểm số cuối cùng
            previous_highscore: Highscore trước khi game over
        """
        self.game_manager = game_manager
        self.screen = game_manager.screen
        
        self.final_score = int(final_score)
        self.previous_highscore = int(previous_highscore)
        
        # Kiểm tra và lưu kỷ lục mới
        self.is_new_record = save_highscore(self.final_score)
        self.highscore = max(self.final_score, self.previous_highscore)
        
        # Fonts
        self.title_font = load_font(settings.GAMEOVER_TITLE_SIZE)
        self.score_font = load_font(settings.GAMEOVER_SCORE_SIZE)
        self.hint_font = load_font(settings.GAMEOVER_HINT_SIZE)
        self.button_font = load_font(settings.BUTTON_FONT_SIZE)
        
        # Buttons (mouse click)
        center_x = settings.SCREEN_WIDTH // 2
        center_y = settings.SCREEN_HEIGHT // 2
        
        self.retry_button = pygame.Rect(
            center_x - settings.BUTTON_WIDTH // 2,
            center_y + 80,
            settings.BUTTON_WIDTH,
            settings.BUTTON_HEIGHT
        )
        
        self.menu_button = pygame.Rect(
            center_x - settings.BUTTON_WIDTH // 2,
            center_y + 80 + settings.BUTTON_HEIGHT + 15,
            settings.BUTTON_WIDTH,
            settings.BUTTON_HEIGHT
        )
        
        # Hover
        self.retry_hovered = False
        self.menu_hovered = False
        
        # Animation
        self.frame_count = 0
        self.fade_alpha = 0  # Fade in effect
    
    def handle_events(self, events):
        """
        Xử lý input.
        
        Args:
            events: List các pygame event
        """
        mouse_pos = pygame.mouse.get_pos()
        
        self.retry_hovered = self.retry_button.collidepoint(mouse_pos)
        self.menu_hovered = self.menu_button.collidepoint(mouse_pos)
        
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.retry_hovered:
                    # Chơi lại - quay về chọn nhân vật
                    from states.character_select_state import CharacterSelectState
                    self.game_manager.change_state(CharacterSelectState(self.game_manager))
                
                elif self.menu_hovered:
                    # Về menu
                    from states.menu_state import MenuState
                    self.game_manager.change_state(MenuState(self.game_manager))
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    from states.character_select_state import CharacterSelectState
                    self.game_manager.change_state(CharacterSelectState(self.game_manager))
                elif event.key == pygame.K_ESCAPE:
                    from states.menu_state import MenuState
                    self.game_manager.change_state(MenuState(self.game_manager))
    
    def update(self):
        """Cập nhật animation."""
        self.frame_count += 1
        
        # Fade in
        if self.fade_alpha < 180:
            self.fade_alpha = min(180, self.fade_alpha + 5)
    
    def draw(self):
        """Vẽ màn hình game over."""
        # Overlay tối bán trong suốt (không xóa nền, tạo hiệu ứng dim)
        overlay = pygame.Surface(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, self.fade_alpha))
        self.screen.blit(overlay, (0, 0))
        
        center_x = settings.SCREEN_WIDTH // 2
        
        # === GAME OVER Title ===
        title_text = self.title_font.render("GAME OVER", True, settings.COLOR_GAMEOVER)
        title_rect = title_text.get_rect(center=(center_x, settings.SCREEN_HEIGHT // 4))
        
        # Shadow
        shadow = self.title_font.render("GAME OVER", True, (50, 10, 10))
        shadow_rect = shadow.get_rect(center=(center_x + 3, settings.SCREEN_HEIGHT // 4 + 3))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title_text, title_rect)
        
        # === Score ===
        score_text = self.score_font.render(
            f"Score: {self.final_score}", True, settings.COLOR_SCORE
        )
        score_rect = score_text.get_rect(center=(center_x, title_rect.bottom + 50))
        self.screen.blit(score_text, score_rect)
        
        # === Highscore ===
        high_text = self.score_font.render(
            f"Best: {self.highscore}", True, settings.COLOR_TEXT
        )
        high_rect = high_text.get_rect(center=(center_x, score_rect.bottom + 35))
        self.screen.blit(high_text, high_rect)
        
        # === New Record! ===
        if self.is_new_record:
            import math
            # Nhấp nháy
            if math.sin(self.frame_count * 0.1) > 0:
                record_text = self.hint_font.render(
                    "★ NEW RECORD! ★", True, (255, 215, 0)
                )
                record_rect = record_text.get_rect(center=(center_x, high_rect.bottom + 30))
                self.screen.blit(record_text, record_rect)
        
        # === Buttons ===
        self._draw_button(self.retry_button, "Play Again", self.retry_hovered)
        self._draw_button(self.menu_button, "Main Menu", self.menu_hovered)
        
        # === Hint ===
        hint_text = self.hint_font.render(
            "SPACE to retry  |  ESC for menu", True, (120, 115, 100)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = center_x
        hint_rect.bottom = settings.SCREEN_HEIGHT - 20
        self.screen.blit(hint_text, hint_rect)
    
    def _draw_button(self, rect, text, is_hovered):
        """Vẽ nút bấm (giống MenuState)."""
        color = settings.COLOR_BUTTON_HOVER if is_hovered else settings.COLOR_BUTTON
        
        # Shadow
        shadow_rect = rect.copy()
        shadow_rect.y += 4
        pygame.draw.rect(
            self.screen, (20, 15, 30),
            shadow_rect, border_radius=settings.BUTTON_BORDER_RADIUS
        )
        
        # Nút
        pygame.draw.rect(
            self.screen, color,
            rect, border_radius=settings.BUTTON_BORDER_RADIUS
        )
        
        # Border
        border_color = settings.COLOR_TITLE if is_hovered else (90, 70, 120)
        pygame.draw.rect(
            self.screen, border_color,
            rect, 2, border_radius=settings.BUTTON_BORDER_RADIUS
        )
        
        # Text
        btn_text = self.button_font.render(text, True, settings.COLOR_BUTTON_TEXT)
        btn_rect = btn_text.get_rect(center=rect.center)
        self.screen.blit(btn_text, btn_rect)
        
        # Hover arrow
        if is_hovered:
            arrow_x = btn_rect.left - 20
            arrow_y = rect.centery
            pygame.draw.polygon(self.screen, settings.COLOR_TITLE, [
                (arrow_x, arrow_y - 6),
                (arrow_x + 10, arrow_y),
                (arrow_x, arrow_y + 6),
            ])
