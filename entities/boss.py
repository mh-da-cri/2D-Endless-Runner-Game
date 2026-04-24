import math
import random

import pygame

import settings
from entities.boss_bullet import BossBullet
from utils.asset_loader import load_image
from utils.spritesheet import SpriteSheet

MONSTER_SPRITESHEET = "monsters_cp.png"
MONSTER_SHEET_COLORKEY = (158, 165, 127)
SHADOW_BOSS_FRAMES = (
    (8, 1012, 91, 99),
    (124, 1012, 91, 99),
    (241, 1011, 91, 99),
)
SHADOW_BOSS_ANIMATION_FRAMES = 12
SHADOW_BOSS_VISUAL_SCALE = 1.35
SHADOW_BOSS_DRAW_OFFSET_Y = 10


class Boss:
    """Boss enemy using the Shadow Boss row from monsters_cp.png."""

    STATE_ENTERING = "entering"
    STATE_FIGHTING = "fighting"
    STATE_DYING = "dying"

    _frames = None

    @classmethod
    def _load_frames(cls):
        if cls._frames is not None:
            return cls._frames

        try:
            sprite_sheet = SpriteSheet(load_image(MONSTER_SPRITESHEET, convert_alpha=True))
            cls._frames = [
                sprite_sheet.get_image_at(x, y, w, h, 1, colorkey=MONSTER_SHEET_COLORKEY)
                for x, y, w, h in SHADOW_BOSS_FRAMES
            ]
        except pygame.error:
            cls._frames = []

        return cls._frames

    def __init__(self):
        self.width = settings.BOSS_WIDTH
        self.height = settings.BOSS_HEIGHT

        self.x = settings.SCREEN_WIDTH + 100
        self.y = settings.BOSS_Y_CENTER - self.height // 2
        self.base_y = self.y

        self.max_hp = settings.BOSS_HP
        self.hp = self.max_hp
        self.state = self.STATE_ENTERING

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.time = 0
        self._flash_timer = 0

        self.frames = self._load_frames()
        self.animation_frame = 0
        self.animation_timer = 0

        self.pattern_timer = settings.BOSS_PATTERN_INTERVAL
        self.current_pattern_index = 0
        self.patterns = [
            self._pattern_duck_line,
            self._pattern_jump_line,
            self._pattern_dash_wall,
            self._pattern_rain,
        ]

    def _advance_animation(self):
        if not self.frames:
            return

        self.animation_timer += 1
        if self.animation_timer >= SHADOW_BOSS_ANIMATION_FRAMES:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % len(self.frames)

    def update(self):
        if self.state == self.STATE_ENTERING:
            self.x -= settings.BOSS_ENTER_SPEED
            if self.x <= settings.BOSS_X:
                self.x = settings.BOSS_X
                self.state = self.STATE_FIGHTING
        elif self.state == self.STATE_FIGHTING:
            self.time += 0.05
            self.y = self.base_y + math.sin(self.time) * 30
        elif self.state == self.STATE_DYING:
            self.y += 2

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self._advance_animation()

    def take_damage(self, amount):
        if self.state == self.STATE_FIGHTING:
            self.hp -= amount
            self._flash_timer = 5
            if self.hp <= 0:
                self.hp = 0
                self.state = self.STATE_DYING
                return True
        return False

    def get_next_pattern(self):
        if self.state != self.STATE_FIGHTING:
            return []

        choices = [
            i for i in range(len(self.patterns))
            if i != getattr(self, "current_pattern_index", -1)
        ]
        if not choices:
            choices = list(range(len(self.patterns)))

        self.current_pattern_index = random.choice(choices)
        pattern_func = self.patterns[self.current_pattern_index]
        return pattern_func()

    def _pattern_duck_line(self):
        bullets = []
        y_pos = settings.GROUND_Y - 90
        for i in range(4):
            bullets.append(
                BossBullet(self.x + i * 45, y_pos, -settings.BOSS_BULLET_SPEED, 0)
            )
        return bullets

    def _pattern_jump_line(self):
        bullets = []
        y_pos = settings.GROUND_Y - 30
        for i in range(4):
            bullets.append(
                BossBullet(self.x + i * 45, y_pos, -settings.BOSS_BULLET_SPEED, 0)
            )
        return bullets

    def _pattern_dash_wall(self):
        bullets = []
        start_y = settings.GROUND_Y - 30
        gap = 35
        for i in range(6):
            bullets.append(
                BossBullet(
                    self.x,
                    start_y - i * gap,
                    -settings.BOSS_BULLET_SPEED * 1.5,
                    0,
                    requires_dash=True,
                )
            )
        return bullets

    def _pattern_rain(self):
        bullets = []
        base_x = settings.PLAYER_START_X - 35
        for i in range(5):
            bullets.append(
                BossBullet(
                    base_x + i * 35,
                    -50,
                    0,
                    settings.BOSS_BULLET_SPEED * 1.2,
                    requires_dash=True,
                )
            )
        return bullets

    def draw(self, screen):
        if self.frames:
            self._draw_sprite(screen)
        else:
            self._draw_placeholder(screen)

    def _draw_sprite(self, screen):
        frame = self.frames[self.animation_frame]
        target_height = max(1, int(self.height * SHADOW_BOSS_VISUAL_SCALE))
        target_width = max(1, int(frame.get_width() * target_height / frame.get_height()))
        sprite = pygame.transform.scale(frame, (target_width, target_height))
        sprite.set_colorkey(MONSTER_SHEET_COLORKEY)
        draw_rect = sprite.get_rect(
            midbottom=(self.rect.centerx, self.rect.bottom + SHADOW_BOSS_DRAW_OFFSET_Y)
        )

        shadow = pygame.Surface((target_width, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        screen.blit(shadow, shadow.get_rect(center=(self.rect.centerx, self.rect.bottom + 8)))

        if self._flash_timer > 0:
            flash = pygame.Surface((draw_rect.width + 24, draw_rect.height + 24), pygame.SRCALPHA)
            pygame.draw.ellipse(flash, (255, 255, 255, 85), flash.get_rect())
            screen.blit(flash, flash.get_rect(center=draw_rect.center))
            self._flash_timer -= 1

        screen.blit(sprite, draw_rect)

    def _draw_placeholder(self, screen):
        color = settings.COLOR_BOSS_BODY
        if self._flash_timer > 0:
            color = settings.COLOR_WHITE
            self._flash_timer -= 1

        pygame.draw.rect(screen, color, self.rect, border_radius=15)

        eye_y = self.y + 40
        pygame.draw.circle(screen, settings.COLOR_BOSS_EYE, (int(self.x + 30), int(eye_y)), 10)
        pygame.draw.circle(
            screen,
            settings.COLOR_BOSS_EYE,
            (int(self.x + self.width - 30), int(eye_y)),
            10,
        )

        pygame.draw.polygon(
            screen,
            settings.COLOR_BOSS_ACCENT,
            [(self.x + 15, self.y), (self.x + 35, self.y - 40), (self.x + 45, self.y)],
        )
        pygame.draw.polygon(
            screen,
            settings.COLOR_BOSS_ACCENT,
            [
                (self.x + self.width - 15, self.y),
                (self.x + self.width - 35, self.y - 40),
                (self.x + self.width - 45, self.y),
            ],
        )

        mouth_y = self.y + 100
        for i in range(4):
            pygame.draw.polygon(
                screen,
                settings.COLOR_WHITE,
                [
                    (self.x + 30 + i * 20, mouth_y),
                    (self.x + 40 + i * 20, mouth_y + 15),
                    (self.x + 50 + i * 20, mouth_y),
                ],
            )

        pygame.draw.rect(screen, settings.COLOR_BLACK, self.rect, 3, border_radius=15)

    def get_rect(self):
        return self.rect
