"""
Main - Entry Point
Khởi tạo Pygame, tạo cửa sổ game, và chạy Game Loop chính.
Đây là file duy nhất cần chạy: python main.py
"""

import pygame
import sys
import settings
from game_manager import GameManager


def main():
    """Hàm chính - khởi tạo và chạy game."""
    
    # === Khởi tạo Pygame ===
    pygame.init()
    pygame.mixer.init()  # Khởi tạo hệ thống âm thanh (dùng khi có audio)
    
    # === Tạo cửa sổ game ===
    screen = pygame.display.set_mode(
        (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
    )
    pygame.display.set_caption(settings.TITLE)
    
    # === Clock để giữ FPS ổn định ===
    clock = pygame.time.Clock()
    
    # === Tạo Game Manager ===
    game_manager = GameManager(screen)
    
    # === Game Loop ===
    running = True
    while running:
        # 1. Bắt tất cả sự kiện
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        
        # 2. Xử lý events → State hiện tại
        game_manager.handle_events(events)
        
        # 3. Cập nhật logic
        game_manager.update()
        
        # 4. Vẽ mọi thứ
        game_manager.draw()
        
        # 5. Hiển thị lên màn hình
        pygame.display.flip()
        
        # 6. Giữ FPS ổn định
        clock.tick(settings.FPS)
    
    # === Dọn dẹp ===
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
