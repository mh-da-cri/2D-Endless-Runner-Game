import random
import pygame
import math
import settings
from entities.boss_bullet import BossBullet

class Boss:
    """Quái vật Boss."""
    
    STATE_ENTERING = 'entering'
    STATE_FIGHTING = 'fighting'
    STATE_DYING = 'dying'
    
    def __init__(self):
        """Khởi tạo Boss."""
        self.width = settings.BOSS_WIDTH
        self.height = settings.BOSS_HEIGHT
        
        # Bắt đầu từ bên ngoài màn hình dọc bên phải
        self.x = settings.SCREEN_WIDTH + 100
        self.y = settings.BOSS_Y_CENTER - self.height // 2
        self.base_y = self.y
        
        self.max_hp = settings.BOSS_HP
        self.hp = self.max_hp
        
        self.state = self.STATE_ENTERING
        
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # Float effect
        self.time = 0
        
        # Pattern system
        self.pattern_timer = settings.BOSS_PATTERN_INTERVAL
        self.current_pattern_index = 0
        self.patterns = [
            self._pattern_duck_line,
            self._pattern_jump_line,
            self._pattern_dash_wall,
            self._pattern_rain
        ]
        
    def update(self):
        """Cập nhật Boss."""
        if self.state == self.STATE_ENTERING:
            # Bay vào màn hình
            self.x -= settings.BOSS_ENTER_SPEED
            if self.x <= settings.BOSS_X:
                self.x = settings.BOSS_X
                self.state = self.STATE_FIGHTING
        elif self.state == self.STATE_FIGHTING:
            # Lơ lửng
            self.time += 0.05
            self.y = self.base_y + math.sin(self.time) * 30
            
            # Giảm hp giả lập? Không, chờ va chạm
            
        elif self.state == self.STATE_DYING:
            self.y += 2 # Rơi xuống
            
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
    def take_damage(self, amount):
        """
        Nhận sát thương từ counter shield.
        Returns:
            bool: True nếu boss chết do nhát đánh này
        """
        if self.state == self.STATE_FIGHTING:
            self.hp -= amount
            self._flash_timer = 5
            if self.hp <= 0:
                self.hp = 0
                self.state = self.STATE_DYING
                return True
        return False
        
    def get_next_pattern(self):
        """Lấy danh sách đạn cần spawn cho pattern tiếp theo ngẫu nhiên."""
        if self.state != self.STATE_FIGHTING:
            return []
            
        choices = [i for i in range(len(self.patterns)) if i != getattr(self, 'current_pattern_index', -1)]
        if not choices:
            choices = list(range(len(self.patterns)))
            
        self.current_pattern_index = random.choice(choices)
        pattern_func = self.patterns[self.current_pattern_index]
        bullets = pattern_func()
        
        return bullets
        
    def _pattern_duck_line(self):
        """Đạn bay cao, yêu cầu CÚI XUỐNG để né."""
        bullets = []
        y_pos = settings.GROUND_Y - 90
        for i in range(4):
            bullets.append(BossBullet(self.x + i * 45, y_pos, -settings.BOSS_BULLET_SPEED, 0))
        return bullets
        
    def _pattern_jump_line(self):
        """Đạn bay sát đất, yêu cầu NHẢY để né."""
        bullets = []
        y_pos = settings.GROUND_Y - 30
        for i in range(4):
            bullets.append(BossBullet(self.x + i * 45, y_pos, -settings.BOSS_BULLET_SPEED, 0))
        return bullets
        

        
    def _pattern_dash_wall(self):
        """Tường đạn dày, bắt buộc phải dash qua."""
        bullets = []
        # Tường dài bắt đầu từ sát mặt đất lên cao
        start_y = settings.GROUND_Y - 30
        gap = 35
        for i in range(6):  # 6 viên là đủ cao không qua được bằng double jump (6*35 = 210)
            bullets.append(BossBullet(self.x, start_y - i * gap, -settings.BOSS_BULLET_SPEED * 1.5, 0, requires_dash=True))
        return bullets
        
    def _pattern_rain(self):
        """Đạn rơi thẳng từ trên xuống dính sát vào nhau ngay đầu người chơi, yêu cầu dash qua."""
        bullets = []
        base_x = settings.PLAYER_START_X - 35
        for i in range(5):
            bullets.append(BossBullet(base_x + i * 35, -50, 0, settings.BOSS_BULLET_SPEED * 1.2, requires_dash=True))
        return bullets

    def draw(self, screen):
        """Vẽ boss."""
        # Chỉ chớp đỏ khi mất máu hoặc bình thường
        color = settings.COLOR_BOSS_BODY
        if getattr(self, '_flash_timer', 0) > 0:
             color = settings.COLOR_WHITE
             self._flash_timer -= 1
             
        # Body chính
        pygame.draw.rect(screen, color, self.rect, border_radius=15)
        
        # Mắt
        eye_y = self.y + 40
        pygame.draw.circle(screen, settings.COLOR_BOSS_EYE, (int(self.x + 30), int(eye_y)), 10)
        pygame.draw.circle(screen, settings.COLOR_BOSS_EYE, (int(self.x + self.width - 30), int(eye_y)), 10)
        
        # Sừng
        pygame.draw.polygon(screen, settings.COLOR_BOSS_ACCENT, [
            (self.x + 15, self.y), (self.x + 35, self.y - 40), (self.x + 45, self.y)
        ])
        pygame.draw.polygon(screen, settings.COLOR_BOSS_ACCENT, [
            (self.x + self.width - 15, self.y), (self.x + self.width - 35, self.y - 40), (self.x + self.width - 45, self.y)
        ])
        
        # Răng/Miệng
        mouth_y = self.y + 100
        for i in range(4):
            pygame.draw.polygon(screen, settings.COLOR_WHITE, [
                (self.x + 30 + i*20, mouth_y), 
                (self.x + 40 + i*20, mouth_y + 15), 
                (self.x + 50 + i*20, mouth_y)
            ])
            
        # Viền
        pygame.draw.rect(screen, settings.COLOR_BLACK, self.rect, 3, border_radius=15)

    def get_rect(self):
        return self.rect
