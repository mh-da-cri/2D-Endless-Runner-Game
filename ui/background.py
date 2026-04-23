"""Parallax background for the game.

The primary background uses the Forest Pass asset pack from
assets/Forest Pass/PNG. If those files are unavailable, the class falls
back to the generated fantasy background that the project used before.
"""

import os
import random

import pygame

import settings


class Background:
    """Parallax scrolling background with multiple depth layers."""

    FOREST_PASS_LAYERS = (
        ("bgcolor.png", 0),
        ("Tlayer1.png", 0.08),
        ("Tlayer2.png", 0.16),
        ("Tlayer3.png", 0.28),
    )

    def __init__(self):
        self.layers = []
        self._create_layers()

    def _create_layers(self):
        if not self._create_forest_pass_layers():
            self._create_generated_layers()

    def _create_forest_pass_layers(self):
        base_path = os.path.join("assets", "Forest Pass", "PNG")
        loaded_layers = []

        try:
            for filename, speed_ratio in self.FOREST_PASS_LAYERS:
                image = pygame.image.load(os.path.join(base_path, filename)).convert_alpha()
                surface = self._scale_forest_pass_layer(image)
                width = surface.get_width()
                loaded_layers.append({
                    "surface": surface,
                    "x1": 0,
                    "x2": width,
                    "speed_ratio": speed_ratio,
                    "width": width,
                    "y": 0,
                })
        except (pygame.error, FileNotFoundError):
            return False

        self.layers = loaded_layers
        return True

    def _scale_forest_pass_layer(self, image):
        scale = settings.GROUND_Y / image.get_height()
        target_width = int(image.get_width() * scale)
        target_height = settings.GROUND_Y
        return pygame.transform.scale(image, (target_width, target_height))

    def _scale_to_screen_height(self, image):
        target_height = settings.SCREEN_HEIGHT
        scale = target_height / image.get_height()
        target_width = int(image.get_width() * scale)
        return pygame.transform.scale(image, (target_width, target_height))

    def _create_generated_layers(self):
        width = settings.SCREEN_WIDTH
        ground_y = settings.GROUND_Y

        sky = self._create_sky_layer(width, ground_y)
        self.layers.append(self._make_layer(sky, 0))

        mountains_far = self._create_mountain_layer(
            width,
            ground_y,
            color=(50, 50, 75),
            height_range=(100, 200),
            num_peaks=6,
        )
        self.layers.append(self._make_layer(mountains_far, settings.BG_LAYER_SPEEDS[0]))

        mountains_near = self._create_mountain_layer(
            width,
            ground_y,
            color=(55, 55, 65),
            height_range=(80, 160),
            num_peaks=8,
        )
        self.layers.append(self._make_layer(mountains_near, settings.BG_LAYER_SPEEDS[1]))

        forest = self._create_forest_layer(width, ground_y)
        self.layers.append(self._make_layer(forest, settings.BG_LAYER_SPEEDS[2]))

    def _make_layer(self, surface, speed_ratio):
        width = surface.get_width()
        return {
            "surface": surface,
            "x1": 0,
            "x2": width,
            "speed_ratio": speed_ratio,
            "width": width,
            "y": 0,
        }

    def _create_sky_layer(self, width, height):
        surface = pygame.Surface((width, height))

        for y in range(height):
            ratio = y / height
            r = int(settings.COLOR_SKY[0] + (settings.COLOR_SKY_GRADIENT[0] - settings.COLOR_SKY[0]) * ratio)
            g = int(settings.COLOR_SKY[1] + (settings.COLOR_SKY_GRADIENT[1] - settings.COLOR_SKY[1]) * ratio)
            b = int(settings.COLOR_SKY[2] + (settings.COLOR_SKY_GRADIENT[2] - settings.COLOR_SKY[2]) * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

        random.seed(123)
        for _ in range(50):
            star_x = random.randint(0, width)
            star_y = random.randint(0, height // 2)
            star_size = random.randint(1, 2)
            star_brightness = random.randint(150, 255)
            pygame.draw.circle(
                surface,
                (star_brightness, star_brightness, star_brightness - 20),
                (star_x, star_y),
                star_size,
            )

        moon_x = width - 200
        moon_y = 80
        pygame.draw.circle(surface, (220, 215, 190), (moon_x, moon_y), 35)
        pygame.draw.circle(surface, (200, 195, 170), (moon_x + 8, moon_y - 5), 30)

        return surface

    def _create_mountain_layer(self, width, ground_y, color, height_range, num_peaks):
        surface = pygame.Surface((width, ground_y), pygame.SRCALPHA)
        random.seed(hash(color))
        peak_width = width // num_peaks + 50

        for i in range(num_peaks + 1):
            peak_x = i * (width // num_peaks) - 25
            peak_height = random.randint(height_range[0], height_range[1])
            peak_y = ground_y - peak_height
            points = [
                (peak_x - peak_width // 2, ground_y),
                (peak_x + random.randint(-20, 20), peak_y),
                (peak_x + peak_width // 2, ground_y),
            ]
            pygame.draw.polygon(surface, color, points)

        return surface

    def _create_forest_layer(self, width, ground_y):
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

            trunk_rect = pygame.Rect(
                tree_x - trunk_width // 2,
                ground_y - tree_height // 2,
                trunk_width,
                tree_height // 2,
            )
            pygame.draw.rect(surface, trunk_color, trunk_rect)
            pygame.draw.polygon(surface, tree_color, [
                (tree_x - canopy_width // 2, ground_y - tree_height // 2 + 10),
                (tree_x, tree_y),
                (tree_x + canopy_width // 2, ground_y - tree_height // 2 + 10),
            ])

        return surface

    def update(self, game_speed):
        for layer in self.layers:
            if layer["speed_ratio"] == 0:
                continue

            scroll_speed = game_speed * layer["speed_ratio"]
            layer["x1"] -= scroll_speed
            layer["x2"] -= scroll_speed
            width = layer["width"]

            if layer["x1"] + width <= 0:
                layer["x1"] = layer["x2"] + width
            if layer["x2"] + width <= 0:
                layer["x2"] = layer["x1"] + width

    def draw(self, screen):
        for layer in self.layers:
            if layer["speed_ratio"] == 0:
                x = 0
                while x < settings.SCREEN_WIDTH:
                    screen.blit(layer["surface"], (x, layer.get("y", 0)))
                    x += layer["width"]
            else:
                x = layer["x1"] % layer["width"] - layer["width"]
                while x < settings.SCREEN_WIDTH:
                    screen.blit(layer["surface"], (int(x), layer.get("y", 0)))
                    x += layer["width"]

    def reset(self):
        for layer in self.layers:
            layer["x1"] = 0
            layer["x2"] = layer["width"]
