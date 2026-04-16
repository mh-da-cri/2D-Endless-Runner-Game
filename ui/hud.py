"""
HUD - Heads-Up Display
Hiển thị điểm số, highscore, và các thông tin trạng thái trong lúc chơi.
"""

import pygame
import settings
from utils.asset_loader import load_font


class HUD:
    """Hiển thị thông tin game trên màn hình."""
    
    def __init__(self):
        """Khởi tạo HUD với font và vị trí."""
        self.font = load_font(settings.HUD_FONT_SIZE)
        self.small_font = load_font(settings.HUD_FONT_SIZE - 6)
    
    def draw(self, screen, score, highscore, game_speed=None):
        """
        Vẽ HUD lên màn hình.
        
        Args:
            screen: pygame.Surface
            score: Điểm hiện tại (float, sẽ được làm tròn)
            highscore: Điểm cao nhất
            game_speed: Tốc độ game hiện tại (tùy chọn, để hiển thị)
        """
        display_score = int(score)
        display_high = int(highscore)
        
        # === Điểm hiện tại (góc trên phải) ===
        score_text = self.font.render(
            f"Score: {display_score}", True, settings.COLOR_SCORE
        )
        score_rect = score_text.get_rect()
        score_rect.topright = (settings.SCREEN_WIDTH - 20, 15)
        
        # Nền bán trong suốt cho score
        bg_surface = pygame.Surface(
            (score_rect.width + 20, score_rect.height + 10), pygame.SRCALPHA
        )
        bg_surface.fill((0, 0, 0, 100))
        screen.blit(bg_surface, (score_rect.x - 10, score_rect.y - 5))
        screen.blit(score_text, score_rect)
        
        # === Highscore (bên dưới score) ===
        high_text = self.small_font.render(
            f"Best: {display_high}", True, settings.COLOR_TEXT
        )
        high_rect = high_text.get_rect()
        high_rect.topright = (settings.SCREEN_WIDTH - 20, score_rect.bottom + 8)
        screen.blit(high_text, high_rect)
        
        # === Hướng dẫn điều khiển (góc dưới trái, nhỏ) ===
        controls = [
            "SPACE: Jump / Double Jump",
            "DOWN: Duck",
            "SHIFT: Dash",
        ]
        for i, text in enumerate(controls):
            ctrl_text = self.small_font.render(text, True, (*settings.COLOR_TEXT[:3],))
            ctrl_surface = pygame.Surface(
                (ctrl_text.get_width() + 8, ctrl_text.get_height() + 4), pygame.SRCALPHA
            )
            ctrl_surface.fill((0, 0, 0, 60))
            screen.blit(ctrl_surface, (8, settings.GROUND_Y + 10 + i * 25))
            screen.blit(ctrl_text, (12, settings.GROUND_Y + 12 + i * 25))
