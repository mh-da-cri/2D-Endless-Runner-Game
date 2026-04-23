"""Small helper for switching looping background music by game state."""

import os

import pygame

_current_music = None


def play_music(filename, volume=0.35):
    """Play a looping music track if it is not already active."""
    global _current_music

    if not filename or _current_music == filename:
        return

    music_path = os.path.join("assets", "audio", filename)
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)
        _current_music = filename
    except (pygame.error, FileNotFoundError):
        _current_music = None
        print(f"[WARNING] Could not load background music: {music_path}")


def stop_music():
    """Stop the current background music and clear the tracked song."""
    global _current_music

    pygame.mixer.music.stop()
    _current_music = None
