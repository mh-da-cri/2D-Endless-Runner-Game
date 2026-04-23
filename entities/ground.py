"""
Ground - scrolling Forest Pass road.

Uses the Forest Pass texture sheet as separate pieces:
- grass strip along the road edge
- random pine trees growing from that grass strip
Uses assets/images/ground.png for the playable floor.
"""

import os
import random

import pygame

import settings


class Ground:
    """Continuously scrolling ground."""

    GROUND_IMAGE = os.path.join("assets", "images", "ground.png")
    GROUND_IMAGE_RECT = pygame.Rect(0, 536, 1464, 538)
    FOREST_TEXTURES = os.path.join("assets", "Forest Pass", "PNG", "Textures&trees.png")
    GRASS_RECT = pygame.Rect(16, 73, 240, 23)
    TREE_RECTS = (
        pygame.Rect(53, 4, 22, 60),
        pygame.Rect(86, 4, 20, 60),
        pygame.Rect(119, 4, 19, 60),
        pygame.Rect(149, 2, 21, 62),
        pygame.Rect(182, 4, 20, 60),
    )

    def __init__(self):
        self.visual_overhang = 560
        self.visual_raise = 20
        self.road_top_offset = self.visual_overhang - 16 - self.visual_raise
        self.width = settings.SCREEN_WIDTH
        self.height = settings.GROUND_HEIGHT + self.visual_overhang
        self.y = settings.GROUND_Y - self.visual_overhang
        self.tile1_x = 0
        self.tile2_x = self.width
        self.surface = self._create_ground_surface()

    def _create_ground_surface(self):
        forest_ground = self._create_forest_pass_ground()
        if forest_ground:
            return forest_ground

        surface = pygame.Surface((self.width, self.height))
        surface.fill(settings.COLOR_GROUND)
        pygame.draw.rect(surface, settings.COLOR_GRASS, (0, self.road_top_offset, self.width, 8))
        pygame.draw.rect(surface, settings.COLOR_GROUND_TOP, (0, self.road_top_offset + 8, self.width, 15))
        return surface

    def _create_forest_pass_ground(self):
        try:
            ground_source = pygame.image.load(self.GROUND_IMAGE).convert()
            forest_source = pygame.image.load(self.FOREST_TEXTURES).convert_alpha()
        except (pygame.error, FileNotFoundError):
            return None

        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))

        scale = self.width / 240
        self._draw_ground_image(surface, ground_source)
        self._draw_grass(surface, forest_source, scale)
        self._draw_random_trees(surface, forest_source, scale)
        return surface

    def _draw_ground_image(self, surface, source):
        source_crop = pygame.Surface(self.GROUND_IMAGE_RECT.size).convert()
        source_crop.blit(source, (0, 0), self.GROUND_IMAGE_RECT)

        ground_height = self.height - self.road_top_offset
        scale = ground_height / self.GROUND_IMAGE_RECT.height
        ground_width = max(1, int(self.GROUND_IMAGE_RECT.width * scale))
        ground_block = pygame.transform.scale(source_crop, (ground_width, ground_height))

        x = 0
        while x < self.width:
            surface.blit(ground_block, (x, self.road_top_offset))
            x += ground_width

    def _draw_grass(self, surface, source, scale):
        grass = self._crop(source, self.GRASS_RECT)
        grass_width = int(self.GRASS_RECT.width * scale)
        grass_height = int(self.GRASS_RECT.height * scale)
        grass = pygame.transform.scale(grass, (grass_width, grass_height))

        x = 0
        grass_y = self.road_top_offset - grass_height + 26
        while x < self.width:
            surface.blit(grass, (x, grass_y))
            x += grass_width

    def _draw_random_trees(self, surface, source, scale):
        rng = random.Random(2026)
        tree_count = 9
        edge_padding = 80

        for i in range(tree_count):
            rect = rng.choice(self.TREE_RECTS)
            tree = self._crop(source, rect)
            tree_scale = scale * rng.uniform(1.22, 1.65)
            tree_width = int(rect.width * tree_scale)
            tree_height = int(rect.height * tree_scale)
            tree = pygame.transform.scale(tree, (tree_width, tree_height))

            slot_width = self.width / tree_count
            x = int(i * slot_width + rng.randint(-34, 42))
            x = max(edge_padding, min(self.width - tree_width - edge_padding, x))
            y = int(self.road_top_offset - 30 - tree_height + rng.randint(-18, 10))
            surface.blit(tree, (x, y))

    def _crop(self, source, rect):
        image = pygame.Surface(rect.size, pygame.SRCALPHA)
        image.blit(source, (0, 0), rect)
        return image

    def update(self, game_speed):
        self.tile1_x -= game_speed
        self.tile2_x -= game_speed

        if self.tile1_x + self.width <= 0:
            self.tile1_x = self.tile2_x + self.width
        if self.tile2_x + self.width <= 0:
            self.tile2_x = self.tile1_x + self.width

    def draw(self, screen):
        screen.blit(self.surface, (self.tile1_x, self.y))
        screen.blit(self.surface, (self.tile2_x, self.y))

    def reset(self):
        self.tile1_x = 0
        self.tile2_x = self.width
