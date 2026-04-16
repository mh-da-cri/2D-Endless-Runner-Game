"""
Background - Parallax Scrolling Background
Nhiều lớp nền cuộn với tốc độ khác nhau tạo cảm giác chiều sâu.
Theme: High Fantasy (bầu trời tối, núi, rừng, lâu đài xa xa).
"""

import pygame
import random
import settings


class Background:
    """Parallax scrolling background với nhiều lớp."""
    
    def __init__(self):
        """Khởi tạo các lớp nền."""
        self.layers = []
        self._create_layers()
    
    def _create_layers(self):
        """Tạo các lớp nền parallax."""
        width = settings.SCREEN_WIDTH
        ground_y = settings.GROUND_Y
        
        # Layer 0: Bầu trời gradient (không cuộn)
        sky = self._create_sky_layer(width, ground_y)
        self.layers.append({
            "surface": sky,
            "x1": 0, "x2": width,
            "speed_ratio": 0,  # Không cuộn
        })
        
        # Layer 1: Núi xa (cuộn rất chậm)
        mountains_far = self._create_mountain_layer(
            width, ground_y, 
            color=(50, 50, 75), 
            height_range=(100, 200),
            num_peaks=6
        )
        self.layers.append({
            "surface": mountains_far,
            "x1": 0, "x2": width,
            "speed_ratio": settings.BG_LAYER_SPEEDS[0],
        })
        
        # Layer 2: Núi gần hơn (cuộn vừa)
        mountains_near = self._create_mountain_layer(
            width, ground_y,
            color=(55, 55, 65),
            height_range=(80, 160),
            num_peaks=8
        )
        self.layers.append({
            "surface": mountains_near,
            "x1": 0, "x2": width,
            "speed_ratio": settings.BG_LAYER_SPEEDS[1],
        })
        
        # Layer 3: Rừng cây tối (cuộn nhanh hơn)
        forest = self._create_forest_layer(width, ground_y)
        self.layers.append({
            "surface": forest,
            "x1": 0, "x2": width,
            "speed_ratio": settings.BG_LAYER_SPEEDS[2],
        })
    
    def _create_sky_layer(self, width, height):
        """
        Tạo lớp bầu trời gradient.
        
        Returns:
            pygame.Surface: Gradient từ tối (trên) đến sáng hơn (dưới)
        """
        surface = pygame.Surface((width, height))
        
        # Gradient dọc
        for y in range(height):
            ratio = y / height
            r = int(settings.COLOR_SKY[0] + (settings.COLOR_SKY_GRADIENT[0] - settings.COLOR_SKY[0]) * ratio)
            g = int(settings.COLOR_SKY[1] + (settings.COLOR_SKY_GRADIENT[1] - settings.COLOR_SKY[1]) * ratio)
            b = int(settings.COLOR_SKY[2] + (settings.COLOR_SKY_GRADIENT[2] - settings.COLOR_SKY[2]) * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
        
        # Thêm sao nhỏ
        random.seed(123)
        for _ in range(50):
            star_x = random.randint(0, width)
            star_y = random.randint(0, height // 2)
            star_size = random.randint(1, 2)
            star_brightness = random.randint(150, 255)
            pygame.draw.circle(
                surface, (star_brightness, star_brightness, star_brightness - 20),
                (star_x, star_y), star_size
            )
        
        # Mặt trăng
        moon_x = width - 200
        moon_y = 80
        pygame.draw.circle(surface, (220, 215, 190), (moon_x, moon_y), 35)
        pygame.draw.circle(surface, (200, 195, 170), (moon_x + 8, moon_y - 5), 30)  # Crescent effect
        
        return surface
    
    def _create_mountain_layer(self, width, ground_y, color, height_range, num_peaks):
        """
        Tạo lớp núi.
        
        Args:
            color: Màu núi
            height_range: (min_height, max_height) của đỉnh núi
            num_peaks: Số đỉnh núi
        
        Returns:
            pygame.Surface
        """
        surface = pygame.Surface((width, ground_y), pygame.SRCALPHA)
        
        random.seed(hash(color))  # Seed theo màu → mỗi lớp khác nhau
        
        peak_width = width // num_peaks + 50
        
        for i in range(num_peaks + 1):
            peak_x = i * (width // num_peaks) - 25
            peak_height = random.randint(height_range[0], height_range[1])
            peak_y = ground_y - peak_height
            
            # Tam giác núi
            points = [
                (peak_x - peak_width // 2, ground_y),
                (peak_x + random.randint(-20, 20), peak_y),
                (peak_x + peak_width // 2, ground_y),
            ]
            pygame.draw.polygon(surface, color, points)
        
        return surface
    
    def _create_forest_layer(self, width, ground_y):
        """
        Tạo lớp rừng cây phía trước.
        
        Returns:
            pygame.Surface
        """
        surface = pygame.Surface((width, ground_y), pygame.SRCALPHA)
        
        tree_color = (35, 55, 35)
        trunk_color = (45, 30, 20)
        
        random.seed(789)
        num_trees = 15
        
        for i in range(num_trees):
            tree_x = i * (width // num_trees) + random.randint(-20, 20)
            tree_height = random.randint(60, 130)
            tree_y = ground_y - tree_height
            trunk_width = random.randint(6, 12)
            canopy_width = random.randint(25, 50)
            
            # Thân cây
            trunk_rect = pygame.Rect(
                tree_x - trunk_width // 2, 
                ground_y - tree_height // 2,
                trunk_width, 
                tree_height // 2
            )
            pygame.draw.rect(surface, trunk_color, trunk_rect)
            
            # Tán cây (tam giác)
            pygame.draw.polygon(surface, tree_color, [
                (tree_x - canopy_width // 2, ground_y - tree_height // 2 + 10),
                (tree_x, tree_y),
                (tree_x + canopy_width // 2, ground_y - tree_height // 2 + 10),
            ])
        
        return surface
    
    def update(self, game_speed):
        """
        Cuộn các lớp nền (trừ bầu trời).
        
        Args:
            game_speed: Tốc độ game hiện tại
        """
        for layer in self.layers:
            if layer["speed_ratio"] == 0:
                continue  # Bầu trời không cuộn
            
            scroll_speed = game_speed * layer["speed_ratio"]
            layer["x1"] -= scroll_speed
            layer["x2"] -= scroll_speed
            
            width = settings.SCREEN_WIDTH
            
            # Reset tile khi ra khỏi màn hình
            if layer["x1"] + width <= 0:
                layer["x1"] = layer["x2"] + width
            if layer["x2"] + width <= 0:
                layer["x2"] = layer["x1"] + width
    
    def draw(self, screen):
        """
        Vẽ tất cả lớp nền theo thứ tự (xa → gần).
        
        Args:
            screen: pygame.Surface
        """
        for layer in self.layers:
            if layer["speed_ratio"] == 0:
                # Bầu trời: vẽ 1 lần, không cuộn
                screen.blit(layer["surface"], (0, 0))
            else:
                # Các lớp cuộn: vẽ 2 tile
                screen.blit(layer["surface"], (layer["x1"], 0))
                screen.blit(layer["surface"], (layer["x2"], 0))
    
    def reset(self):
        """Reset vị trí các lớp nền."""
        for layer in self.layers:
            layer["x1"] = 0
            layer["x2"] = settings.SCREEN_WIDTH
