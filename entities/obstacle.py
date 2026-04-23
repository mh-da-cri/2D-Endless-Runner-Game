"""
Obstacle entity for the endless runner.

Ground obstacles use the Skeleton row from monsters_cp.png and flying
obstacles use the Bat row from the same sheet.
"""

import random
from math import sin as math_sin

import pygame

import settings
from utils.asset_loader import load_image
from utils.spritesheet import SpriteSheet

MONSTER_SPRITESHEET = "monsters_cp.png"
MONSTER_SHEET_COLORKEY = (158, 165, 127)
BAT_FRAMES = (
    (3, 80, 64, 38),
    (71, 80, 64, 38),
    (140, 80, 64, 38),
)
SKELETON_FRAMES = (
    (12, 447, 44, 69),
    (72, 447, 44, 69),
    (130, 447, 44, 69),
)
SPIDER_FRAMES = (
    (3, 547, 55, 38),
    (68, 547, 55, 38),
    (134, 547, 55, 38),
)
BAT_ANIMATION_FRAMES = 8
SKELETON_ANIMATION_FRAMES = 10
SPIDER_ANIMATION_FRAMES = 9
BAT_VISUAL_SCALE = 1.7
SKELETON_VISUAL_SCALE = 1.15
SPIDER_VISUAL_SCALE = 1.6
BAT_DRAW_OFFSET_Y = -2
SKELETON_DRAW_OFFSET_Y = 4
SPIDER_WEB_COLOR = (178, 196, 196)
BAT_VARIANTS = {
    "orange": {
        "frame_index": 0,
        "placeholder_color": (226, 146, 116),
    },
    "gray": {
        "frame_index": 1,
        "placeholder_color": (186, 186, 196),
    },
    "yellow": {
        "frame_index": 2,
        "placeholder_color": (242, 182, 72),
    },
}
SKELETON_VARIANTS = {
    "orange": {
        "frame_index": 0,
        "placeholder_color": (180, 102, 74),
    },
    "purple": {
        "frame_index": 1,
        "placeholder_color": (154, 90, 164),
    },
    "gray": {
        "frame_index": 2,
        "placeholder_color": (182, 182, 182),
    },
}
SPIDER_VARIANTS = {
    "gray": {
        "frame_index": 0,
        "damage": 1,
        "score_penalty": settings.SPIDER_SCORE_PENALTY,
        "slow_duration": 0,
    },
    "blue": {
        "frame_index": 1,
        "damage": 1,
        "score_penalty": 0,
        "slow_duration": settings.SPIDER_SLOW_DURATION,
    },
    "red": {
        "frame_index": 2,
        "damage": 2,
        "score_penalty": 0,
        "slow_duration": 0,
    },
}
OBSTACLE_DEATH_SOUNDS = {
    "ground": settings.OBSTACLE_SKELETON_DEATH_SOUND,
    "flying": settings.OBSTACLE_BAT_DEATH_SOUND,
    "spider": settings.OBSTACLE_SPIDER_DEATH_SOUND,
}


class Obstacle:
    """Obstacle entity with sprite-based visuals and stable gameplay hitboxes."""

    TYPE_GROUND = "ground"
    TYPE_FLYING = "flying"
    TYPE_SPIDER = "spider"

    _sprite_frames = None

    @classmethod
    def _load_sprite_frames(cls):
        if cls._sprite_frames is not None:
            return cls._sprite_frames

        try:
            sprite_sheet = SpriteSheet(load_image(MONSTER_SPRITESHEET, convert_alpha=True))
            cls._sprite_frames = {
                cls.TYPE_GROUND: [
                    sprite_sheet.get_image_at(x, y, w, h, 1, colorkey=MONSTER_SHEET_COLORKEY)
                    for x, y, w, h in SKELETON_FRAMES
                ],
                cls.TYPE_FLYING: [
                    sprite_sheet.get_image_at(x, y, w, h, 1, colorkey=MONSTER_SHEET_COLORKEY)
                    for x, y, w, h in BAT_FRAMES
                ],
                cls.TYPE_SPIDER: [
                    sprite_sheet.get_image_at(x, y, w, h, 1, colorkey=MONSTER_SHEET_COLORKEY)
                    for x, y, w, h in SPIDER_FRAMES
                ],
            }
        except pygame.error:
            cls._sprite_frames = {
                cls.TYPE_GROUND: [],
                cls.TYPE_FLYING: [],
                cls.TYPE_SPIDER: [],
            }

        return cls._sprite_frames

    def __init__(self, obstacle_type=None, game_speed=None):
        if obstacle_type is None:
            roll = random.random()
            if roll < settings.SPIDER_OBSTACLE_CHANCE:
                self.type = self.TYPE_SPIDER
            elif roll < settings.SPIDER_OBSTACLE_CHANCE + 0.57:
                self.type = self.TYPE_GROUND
            else:
                self.type = self.TYPE_FLYING
        else:
            self.type = obstacle_type

        self.speed = game_speed if game_speed else settings.INITIAL_GAME_SPEED
        self.variant = None
        self.damage = 1
        self.score_penalty = 0
        self.slow_duration = 0
        self.consume_on_hit = False
        self.time = random.random() * 10

        if self.type == self.TYPE_GROUND:
            self._init_ground_obstacle()
        elif self.type == self.TYPE_FLYING:
            self._init_flying_obstacle()
        else:
            self._init_spider_obstacle()

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.passed = False

        sprite_frames = self._load_sprite_frames()
        self.frames = sprite_frames.get(self.type, [])
        self.animation_frame = random.randrange(len(self.frames)) if self.frames else 0
        self.animation_timer = random.randint(0, self._animation_cooldown() - 1)

    def _init_ground_obstacle(self):
        self.width = random.randint(
            settings.OBSTACLE_MIN_WIDTH,
            settings.OBSTACLE_MAX_WIDTH,
        )
        self.height = random.randint(
            settings.OBSTACLE_MIN_HEIGHT,
            settings.OBSTACLE_MAX_HEIGHT,
        )
        self.x = settings.SCREEN_WIDTH + random.randint(0, 100)
        self.y = settings.GROUND_Y - self.height
        self._set_skeleton_variant(random.choice(tuple(SKELETON_VARIANTS.keys())))

    def _set_skeleton_variant(self, variant):
        self.variant = variant
        self.color = SKELETON_VARIANTS[self.variant]["placeholder_color"]

    def _init_flying_obstacle(self):
        self.width = settings.FLYING_OBSTACLE_WIDTH
        self.height = settings.FLYING_OBSTACLE_HEIGHT

        subtype = random.choice(["jump", "duck", "double_jump"])

        if subtype == "jump":
            self.y = 560
        elif subtype == "duck":
            self.y = 510
        else:
            self.y = 450

        self.x = settings.SCREEN_WIDTH + random.randint(0, 100)
        self._set_bat_variant(random.choice(tuple(BAT_VARIANTS.keys())))

    def _set_bat_variant(self, variant):
        self.variant = variant
        self.color = BAT_VARIANTS[self.variant]["placeholder_color"]

    def _init_spider_obstacle(self):
        self.width = settings.SPIDER_WIDTH
        self.height = settings.SPIDER_HEIGHT
        self.x = settings.SCREEN_WIDTH + random.randint(0, 100)
        self.base_y = random.randint(settings.SPIDER_Y_MIN, settings.SPIDER_Y_MAX)
        self.y = self.base_y
        self._set_spider_variant(random.choice(tuple(SPIDER_VARIANTS.keys())))
        self.consume_on_hit = True

    def _set_spider_variant(self, variant):
        self.variant = variant
        data = SPIDER_VARIANTS[self.variant]
        self.damage = data["damage"]
        self.score_penalty = data["score_penalty"]
        self.slow_duration = data["slow_duration"]
        # Thêm lại color cho placeholder đề phòng lỗi load sprite
        self.color = (190, 190, 185) if variant == "gray" else (90, 170, 255) if variant == "blue" else (240, 76, 64)

    def _animation_cooldown(self):
        if self.type == self.TYPE_GROUND:
            return SKELETON_ANIMATION_FRAMES
        if self.type == self.TYPE_SPIDER:
            return SPIDER_ANIMATION_FRAMES
        return BAT_ANIMATION_FRAMES

    def _advance_animation(self):
        if not self.frames:
            return

        self.animation_timer += 1
        if self.animation_timer >= self._animation_cooldown():
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % len(self.frames)

    def update(self, game_speed=None):
        speed = game_speed if game_speed else self.speed
        self.x -= speed
        self.time += 0.08
        if self.type == self.TYPE_SPIDER:
            self.y = self.base_y + math_sin(self.time) * 8
            self.rect.y = int(self.y)
        self.rect.x = int(self.x)
        self._advance_animation()

    def draw(self, screen):
        if self.frames:
            self._draw_sprite(screen)
            return

        if self.type == self.TYPE_GROUND:
            self._draw_ground_placeholder(screen)
        elif self.type == self.TYPE_FLYING:
            self._draw_flying_placeholder(screen)
        else:
            self._draw_spider_placeholder(screen)

    def _draw_sprite(self, screen):
        if self.type == self.TYPE_GROUND:
            variant_data = SKELETON_VARIANTS.get(self.variant, SKELETON_VARIANTS["orange"])
            frame = self.frames[variant_data["frame_index"]]
            target_height = max(1, int(self.height * SKELETON_VISUAL_SCALE))
            target_width = max(1, int(frame.get_width() * target_height / frame.get_height()))
            sprite = pygame.transform.scale(frame, (target_width, target_height))
            sprite.set_colorkey(MONSTER_SHEET_COLORKEY)
            draw_rect = sprite.get_rect(
                midbottom=(self.rect.centerx, self.rect.bottom + SKELETON_DRAW_OFFSET_Y)
            )
        elif self.type == self.TYPE_FLYING:
            variant_data = BAT_VARIANTS.get(self.variant, BAT_VARIANTS["orange"])
            frame = self.frames[variant_data["frame_index"]]
            target_width = max(1, int(self.width * BAT_VISUAL_SCALE))
            target_height = max(1, int(frame.get_height() * target_width / frame.get_width()))
            sprite = pygame.transform.scale(frame, (target_width, target_height))
            sprite.set_colorkey(MONSTER_SHEET_COLORKEY)
            draw_rect = sprite.get_rect(
                center=(self.rect.centerx, self.rect.centery + BAT_DRAW_OFFSET_Y)
            )
        else:
            # Spider: dùng frame theo variant (Xám, Xanh, Đỏ)
            variant_data = SPIDER_VARIANTS.get(self.variant, SPIDER_VARIANTS["gray"])
            frame_idx = variant_data["frame_index"]
            frame = self.frames[frame_idx]
            
            target_width = max(1, int(self.width * SPIDER_VISUAL_SCALE))
            target_height = max(1, int(frame.get_height() * target_width / frame.get_width()))
            sprite = pygame.transform.scale(frame, (target_width, target_height))
            sprite.set_colorkey(MONSTER_SHEET_COLORKEY)
            
            # Xóa sạch viền nếu cần (giống _clear_monster_key nhưng làm luôn ở đây)
            sprite = self._clear_monster_key(sprite)
            
            draw_rect = sprite.get_rect(center=self.rect.center)
            self._draw_spider_web(screen, draw_rect)

        screen.blit(sprite, draw_rect)

    def _draw_spider_web(self, screen, draw_rect):
        anchor_x = draw_rect.centerx + int(math_sin(self.time * 0.7) * 4)
        pygame.draw.line(screen, (72, 88, 88), (anchor_x + 1, 0), (draw_rect.centerx + 1, draw_rect.top + 5), 2)
        pygame.draw.line(screen, SPIDER_WEB_COLOR, (anchor_x, 0), (draw_rect.centerx, draw_rect.top + 5), 1)
        for y in range(22, max(22, draw_rect.top), 32):
            pygame.draw.circle(screen, (202, 218, 218), (anchor_x, y), 1)

    def _tint_spider(self, sprite):
        """Đã bị thay thế bởi việc dùng sprite màu sẵn từ sheet."""
        return sprite

    def _clear_monster_key(self, sprite):
        sprite = sprite.copy().convert_alpha()
        key_r, key_g, key_b = MONSTER_SHEET_COLORKEY
        for y in range(sprite.get_height()):
            for x in range(sprite.get_width()):
                r, g, b, a = sprite.get_at((x, y))
                if abs(r - key_r) <= 5 and abs(g - key_g) <= 5 and abs(b - key_b) <= 5:
                    sprite.set_at((x, y), (r, g, b, 0))
        return sprite

    def _draw_spider_placeholder(self, screen):
        web_bottom = self.y + self.height // 2
        pygame.draw.line(screen, SPIDER_WEB_COLOR, (self.rect.centerx, 0), (self.rect.centerx, web_bottom), 1)
        pygame.draw.ellipse(screen, self.color, self.rect)
        pygame.draw.ellipse(screen, settings.COLOR_BLACK, self.rect, 2)

        for side in (-1, 1):
            for i in range(4):
                leg_y = self.y + 8 + i * 7
                pygame.draw.line(
                    screen,
                    settings.COLOR_BLACK,
                    (self.rect.centerx + side * 8, leg_y),
                    (self.rect.centerx + side * (28 + i * 3), leg_y + side * 2),
                    2,
                )

    def _draw_ground_placeholder(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=6)
        pygame.draw.rect(screen, settings.COLOR_BLACK, self.rect, 2, border_radius=6)

        eye_y = self.y + 12
        eye_x1 = self.x + self.width // 3
        eye_x2 = self.x + self.width * 2 // 3
        pygame.draw.circle(screen, (220, 50, 50), (eye_x1, eye_y), 4)
        pygame.draw.circle(screen, (220, 50, 50), (eye_x2, eye_y), 4)

        horn_x = self.x + self.width // 2
        pygame.draw.polygon(
            screen,
            (80, 40, 35),
            [
                (horn_x - 5, self.y),
                (horn_x, self.y - 10),
                (horn_x + 5, self.y),
            ],
        )

    def _draw_flying_placeholder(self, screen):
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2

        pygame.draw.ellipse(screen, self.color, self.rect)
        pygame.draw.ellipse(screen, settings.COLOR_BLACK, self.rect, 2)

        wing_points_left = [
            (self.x, center_y),
            (self.x - 15, self.y - 5),
            (self.x + 10, self.y + 5),
        ]
        pygame.draw.polygon(screen, self.color, wing_points_left)
        pygame.draw.polygon(screen, settings.COLOR_BLACK, wing_points_left, 2)

        wing_points_right = [
            (self.x + self.width, center_y),
            (self.x + self.width + 15, self.y - 5),
            (self.x + self.width - 10, self.y + 5),
        ]
        pygame.draw.polygon(screen, self.color, wing_points_right)
        pygame.draw.polygon(screen, settings.COLOR_BLACK, wing_points_right, 2)

        pygame.draw.circle(screen, (255, 80, 80), (center_x - 6, center_y - 3), 3)
        pygame.draw.circle(screen, (255, 80, 80), (center_x + 6, center_y - 3), 3)

    def is_off_screen(self):
        return self.x + self.width < 0

    def get_rect(self):
        shrink = 4
        return pygame.Rect(
            self.rect.x + shrink,
            self.rect.y + shrink,
            self.rect.width - shrink * 2,
            self.rect.height - shrink * 2,
        )

    def get_defeat_sound_filename(self):
        return OBSTACLE_DEATH_SOUNDS.get(self.type)
