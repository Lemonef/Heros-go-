import pygame
import os
import time

class Animation:
    def __init__(self, frames, interval=0.1, loop=True):
        self.frames = frames
        self.interval = interval
        self.index = 0
        self.last_time = time.time()
        self.loop = loop
        self.finished = False

    def update(self):
        if self.finished:
            return
        if time.time() - self.last_time >= self.interval:
            self.index += 1
            if self.index >= len(self.frames):
                if self.loop:
                    self.index = 0
                else:
                    self.index = len(self.frames) - 1
                    self.finished = True
            self.last_time = time.time()

    def get_frame(self):
        return self.frames[self.index]

class AnimationManager:
    @staticmethod
    def load_sprite_strip(path):
        sheet = pygame.image.load(path).convert_alpha()
        frame_height = sheet.get_height()
        frame_width = frame_height
        cols = sheet.get_width() // frame_width
        return [sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)) for i in range(cols)]

    @staticmethod
    def load_animations_from_folder(folder):
        animations = {}
        for file in os.listdir(folder):
            if file.endswith(".png"):
                key = file.replace(".png", "").lower()
                animations[key] = AnimationManager.load_sprite_strip(os.path.join(folder, file))
        return animations
