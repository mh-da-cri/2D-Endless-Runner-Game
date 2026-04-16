"""
Ground - Mặt đất cuộn liên tục
Sử dụng 2 tile nối tiếp nhau để tạo hiệu ứng cuộn vô tận.
"""

import pygame
import settings


class Ground:
    """Mặt đất cuộn liên tục."""
    
    def __init__(self):
        """Khởi tạo 2 tile mặt đất."""
        self.width = settings.SCREEN_WIDTH
        self.height = settings.GROUND_HEIGHT
        self.y = settings.GROUND_Y
        
        # 2 tile nối tiếp: khi tile 1 ra khỏi màn hình → đặt lại sau tile 2
        self.tile1_x = 0
        self.tile2_x = self.width
        
        # Tạo surface cho mặt đất (vẽ 1 lần, dùng lại)
        self.surface = self._create_ground_surface()
    
    def _create_ground_surface(self):
        """
        Tạo surface mặt đất với chi tiết.
        Sau này thay bằng sprite tileset.
        
        Returns:
            pygame.Surface
        """
        surface = pygame.Surface((self.width, self.height))
        
        # Phần đất chính
        surface.fill(settings.COLOR_GROUND)
        
        # Viền cỏ trên cùng
        grass_height = 8
        pygame.draw.rect(
            surface, settings.COLOR_GRASS,
            (0, 0, self.width, grass_height)
        )
        
        # Lớp đất sáng hơn bên dưới cỏ
        top_layer_height = 15
        pygame.draw.rect(
            surface, settings.COLOR_GROUND_TOP,
            (0, grass_height, self.width, top_layer_height)
        )
        
        # Thêm chi tiết đá/sỏi nhỏ (dots)
        import random
        random.seed(42)  # Seed cố định → pattern giống nhau mỗi lần
        for _ in range(40):
            dot_x = random.randint(0, self.width)
            dot_y = random.randint(top_layer_height + grass_height, self.height - 5)
            dot_size = random.randint(2, 5)
            dot_color = (
                settings.COLOR_GROUND[0] + random.randint(-10, 10),
                settings.COLOR_GROUND[1] + random.randint(-10, 10),
                settings.COLOR_GROUND[2] + random.randint(-10, 10),
            )
            pygame.draw.circle(surface, dot_color, (dot_x, dot_y), dot_size)
        
        return surface
    
    def update(self, game_speed):
        """
        Cuộn mặt đất sang trái.
        
        Args:
            game_speed: Tốc độ cuộn hiện tại
        """
        self.tile1_x -= game_speed
        self.tile2_x -= game_speed
        
        # Khi tile ra khỏi màn hình bên trái → đặt lại sau tile kia
        if self.tile1_x + self.width <= 0:
            self.tile1_x = self.tile2_x + self.width
        
        if self.tile2_x + self.width <= 0:
            self.tile2_x = self.tile1_x + self.width
    
    def draw(self, screen):
        """
        Vẽ mặt đất lên màn hình.
        
        Args:
            screen: pygame.Surface
        """
        screen.blit(self.surface, (self.tile1_x, self.y))
        screen.blit(self.surface, (self.tile2_x, self.y))
    
    def reset(self):
        """Reset vị trí mặt đất (khi chơi lại)."""
        self.tile1_x = 0
        self.tile2_x = self.width
