"""
Obstacle - Chướng ngại vật (quái vật)
Gồm 2 loại: mặt đất (goblin/orc - cần nhảy qua) và bay (cần cúi né).
"""

import random
import pygame
import settings


class Obstacle:
    """Chướng ngại vật - Quái vật High Fantasy."""
    
    # Loại obstacle
    TYPE_GROUND = "ground"   # Quái mặt đất (goblin, orc) → nhảy qua
    TYPE_FLYING = "flying"   # Quái bay (bat, harpy) → cúi né
    
    def __init__(self, obstacle_type=None, game_speed=None):
        """
        Khởi tạo obstacle mới ở bên phải màn hình.
        
        Args:
            obstacle_type: "ground" hoặc "flying", None = random
            game_speed: Tốc độ game hiện tại, None = dùng INITIAL_GAME_SPEED
        """
        # Random loại nếu không chỉ định
        if obstacle_type is None:
            # Điều chỉnh cân bằng: 40% quái mặt đất, 60% quái bay 
            # (Đảm bảo mỗi loại bay Tím, Xanh, Đỏ chiếm 20% tổng số quái)
            self.type = self.TYPE_GROUND if random.random() < 0.4 else self.TYPE_FLYING
        else:
            self.type = obstacle_type
        
        self.speed = game_speed if game_speed else settings.INITIAL_GAME_SPEED
        
        # Khởi tạo kích thước và vị trí theo loại
        if self.type == self.TYPE_GROUND:
            self._init_ground_obstacle()
        else:
            self._init_flying_obstacle()
        
        # Hitbox
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # Đã bị vượt qua chưa (để tính điểm)
        self.passed = False
    
    def _init_ground_obstacle(self):
        """Khởi tạo quái mặt đất."""
        self.width = random.randint(
            settings.OBSTACLE_MIN_WIDTH,
            settings.OBSTACLE_MAX_WIDTH
        )
        self.height = random.randint(
            settings.OBSTACLE_MIN_HEIGHT,
            settings.OBSTACLE_MAX_HEIGHT
        )
        self.x = settings.SCREEN_WIDTH + random.randint(0, 100)
        self.y = settings.GROUND_Y - self.height  # Đặt trên mặt đất
        self.color = settings.COLOR_OBSTACLE_GROUND
    
    def _init_flying_obstacle(self):
        """Khởi tạo quái bay với 3 mức độ cao khác nhau (giữ nguyên kích thước nhỏ)."""
        self.width = settings.FLYING_OBSTACLE_WIDTH
        self.height = settings.FLYING_OBSTACLE_HEIGHT  # Cố định kích thước
        
        # Chọn ngẫu nhiên loại quái bay một cách cân bằng (tỷ lệ bằng nhau 1:1:1)
        subtype = random.choice(["jump", "duck", "double_jump"])
        
        if subtype == "jump":
            # Quái bay khinh công sát đất -> Cúi hay đứng đều trúng. Bắt buộc nhảy.
            self.y = 560
            self.color = settings.COLOR_OBSTACLE_FLYING  # Tím tối
        elif subtype == "duck":
            # Quái bay ngang đầu (Bottom=550). Đứng trúng đầu. Bắt buộc rũ đầu cúi qua.
            self.y = 510
            self.color = settings.COLOR_OBSTACLE_FLYING  # Tím tối
        else: # "double_jump"
            # Quái bay rất cao (Đỉnh 450, Đáy 490). Nếu người chơi đã phóng lên không trung bằng Nhảy 1 lần (đỉnh=480) sẽ bị va phải. 
            # Bắt buộc phải Double Jump (đỉnh=375) để vọt qua. Dĩ nhiên nếu tinh ý có thể chạy bộ/cúi thẳng dưới háng quái mà không cần nhảy.
            self.y = 450
            self.color = settings.COLOR_OBSTACLE_FLYING  # Tím tối
            
        self.x = settings.SCREEN_WIDTH + random.randint(0, 100)
    
    def update(self, game_speed=None):
        """
        Di chuyển obstacle từ phải sang trái.
        
        Args:
            game_speed: Tốc độ game hiện tại (tăng dần theo thời gian)
        """
        speed = game_speed if game_speed else self.speed
        self.x -= speed
        self.rect.x = self.x
    
    def draw(self, screen):
        """
        Vẽ obstacle lên màn hình.
        Dùng hình học placeholder, sau thay bằng sprite.
        
        Args:
            screen: pygame.Surface
        """
        if self.type == self.TYPE_GROUND:
            self._draw_ground_monster(screen)
        else:
            self._draw_flying_monster(screen)
    
    def _draw_ground_monster(self, screen):
        """Vẽ quái mặt đất (goblin/orc style)."""
        # Thân chính
        pygame.draw.rect(screen, self.color, self.rect, border_radius=6)
        
        # Outline
        pygame.draw.rect(screen, settings.COLOR_BLACK, self.rect, 2, border_radius=6)
        
        # Mắt đỏ (2 chấm)
        eye_y = self.y + 12
        eye_x1 = self.x + self.width // 3
        eye_x2 = self.x + self.width * 2 // 3
        pygame.draw.circle(screen, (220, 50, 50), (eye_x1, eye_y), 4)
        pygame.draw.circle(screen, (220, 50, 50), (eye_x2, eye_y), 4)
        
        # "Sừng" nhỏ trên đầu
        horn_x = self.x + self.width // 2
        pygame.draw.polygon(screen, (80, 40, 35), [
            (horn_x - 5, self.y),
            (horn_x, self.y - 10),
            (horn_x + 5, self.y)
        ])
    
    def _draw_flying_monster(self, screen):
        """Vẽ quái bay (bat/harpy style)."""
        # Thân chính
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        # Thân (ellipse)
        pygame.draw.ellipse(screen, self.color, self.rect)
        pygame.draw.ellipse(screen, settings.COLOR_BLACK, self.rect, 2)
        
        # Cánh trái
        wing_points_left = [
            (self.x, center_y),
            (self.x - 15, self.y - 5),
            (self.x + 10, self.y + 5)
        ]
        pygame.draw.polygon(screen, self.color, wing_points_left)
        pygame.draw.polygon(screen, settings.COLOR_BLACK, wing_points_left, 2)
        
        # Cánh phải
        wing_points_right = [
            (self.x + self.width, center_y),
            (self.x + self.width + 15, self.y - 5),
            (self.x + self.width - 10, self.y + 5)
        ]
        pygame.draw.polygon(screen, self.color, wing_points_right)
        pygame.draw.polygon(screen, settings.COLOR_BLACK, wing_points_right, 2)
        
        # Mắt đỏ
        pygame.draw.circle(screen, (255, 80, 80), (center_x - 6, center_y - 3), 3)
        pygame.draw.circle(screen, (255, 80, 80), (center_x + 6, center_y - 3), 3)
    
    def is_off_screen(self):
        """
        Kiểm tra obstacle đã ra khỏi màn hình bên trái chưa.
        
        Returns:
            bool: True nếu đã ra khỏi màn hình
        """
        return self.x + self.width < 0
    
    def get_rect(self):
        """
        Trả về hitbox cho collision detection.
        Thu nhỏ hitbox một chút so với visual để collision "dễ chịu" hơn.
        
        Returns:
            pygame.Rect
        """
        shrink = 4
        return pygame.Rect(
            self.rect.x + shrink,
            self.rect.y + shrink,
            self.rect.width - shrink * 2,
            self.rect.height - shrink * 2
        )
