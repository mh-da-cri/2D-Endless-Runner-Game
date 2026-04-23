"""
Main entry point for the endless runner game.

Run this file with: python main.py
"""

import sys

import pygame

import settings
from game_manager import GameManager
from utils.music_manager import stop_music


def main():
    """Initialize pygame and run the main game loop."""

    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode(
        (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
    )
    pygame.display.set_caption(settings.TITLE)

    clock = pygame.time.Clock()
    game_manager = GameManager(screen)

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        game_manager.handle_events(events)
        game_manager.update()
        game_manager.draw()

        pygame.display.flip()
        clock.tick(settings.FPS)

    stop_music()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
