#!/usr/bin/env python3
"""Quiet animated robot-room night light for an original Raspberry Pi Zero W."""

from __future__ import annotations

import math
import os
import random
from datetime import datetime
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

WIDTH, HEIGHT, FPS = 800, 480, 12
ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"


class Drop:
    def __init__(self) -> None:
        self.reset(True)

    def reset(self, random_y: bool = False) -> None:
        self.x = random.randint(480, 785)
        self.y = random.randint(18, 195) if random_y else random.randint(8, 45)
        self.speed = random.uniform(22, 48)
        self.length = random.randint(3, 8)
        self.alpha = random.randint(35, 90)

    def update(self, dt: float) -> None:
        self.y += self.speed * dt
        # Stop at the sloping lower edge of the window glass. The sill and room
        # beneath it must remain completely dry.
        glass_bottom = 205 + (self.x - 470) * (30 / 330)
        if self.y > glass_bottom:
            self.reset()


class RobotNightlight:
    def __init__(self) -> None:
        pygame.init()
        self.fullscreen = True
        self.screen = self.make_screen()
        pygame.display.set_caption("Robot Window Nightlight")
        self.clock = pygame.time.Clock()
        self.normal_room = pygame.image.load(str(ASSETS / "room.png")).convert()
        self.halloween_room = pygame.image.load(str(ASSETS / "room-halloween.png")).convert()
        preview_flag = ROOT / "halloween-preview.flag"
        self.halloween_manual = True if preview_flag.exists() else None
        self.calendar_month = datetime.now().month
        show_halloween = self.halloween_manual is True or self.calendar_month == 10
        self.room = self.halloween_room if show_halloween else self.normal_room
        source = pygame.image.load(str(ASSETS / "robot-source.png")).convert_alpha()
        self.robot_right = pygame.transform.scale(source, (132, 132))
        self.robot_left = pygame.transform.flip(self.robot_right, True, False)
        self.pet_right = pygame.image.load(str(ASSETS / "pet-rover-right.png")).convert_alpha()
        self.pet_left = pygame.image.load(str(ASSETS / "pet-rover-left.png")).convert_alpha()
        self.x, self.y = 300.0, 371.0
        self.stops = [
            (300.0, 371.0, (4.0, 9.0)),   # rug / room center
            (388.0, 329.0, (5.0, 10.0)),  # visit the workbench
            (557.0, 344.0, (8.0, 16.0)),  # watch the city
            (650.0, 356.0, (3.0, 7.0)),   # patrol the window cabinets
            (438.0, 408.0, (4.0, 9.0)),   # cross the near edge of the rug
        ]
        self.stop_index = 2
        self.target_x = self.stops[self.stop_index][0]
        self.facing_right = True
        self.pause = 3.0
        self.pet_x, self.pet_y = 455.0, 417.0
        self.pet_stops = [
            (250.0, 405.0, (8.0, 18.0)),   # near the plant
            (350.0, 365.0, (4.0, 9.0)),    # rug
            (462.0, 416.0, (12.0, 28.0)),  # favorite nap spot
            (548.0, 379.0, (5.0, 12.0)),   # below the window
            (653.0, 392.0, (5.0, 10.0)),   # far cabinet patrol
        ]
        self.pet_stop_index = 1
        self.pet_pause = 6.0
        self.pet_facing_right = False
        self.running = True
        self.drops = [Drop() for _ in range(54)]
        self.twinkles = [
            (random.randint(505, 770), random.randint(100, 245), random.random() * 6.28)
            for _ in range(22)
        ]
        self.next_lightning = random.uniform(35.0, 100.0)
        self.lightning = 0.0
        self.next_flyby = random.uniform(18.0, 45.0)
        self.flyby_x = -80.0
        self.flyby_active = False
        self.next_alien = random.uniform(90.0, 240.0)
        self.alien_timer = 0.0
        self.elapsed = 0.0

    def make_screen(self) -> pygame.Surface:
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        pygame.mouse.set_visible(not self.fullscreen)
        return screen

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False
                elif event.key == pygame.K_f:
                    self.fullscreen = not self.fullscreen
                    self.screen = self.make_screen()
                elif event.key == pygame.K_h:
                    self.halloween_manual = self.room is self.normal_room
                    self.room = self.halloween_room if self.halloween_manual else self.normal_room

    def update_robot(self, dt: float) -> None:
        if self.pause > 0:
            self.pause -= dt
            return
        target_x, target_y, _ = self.stops[self.stop_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)
        if distance < 2:
            self.x, self.y = target_x, target_y
            low, high = self.stops[self.stop_index][2]
            self.pause = random.uniform(low, high)
            choices = [i for i in range(len(self.stops)) if i != self.stop_index]
            self.stop_index = random.choice(choices)
            self.target_x = self.stops[self.stop_index][0]
            return
        if abs(dx) > 1:
            self.facing_right = dx > 0
        step = min(distance, 17 * dt)
        self.x += dx / distance * step
        self.y += dy / distance * step

    def update_pet(self, dt: float) -> None:
        if self.pet_pause > 0:
            self.pet_pause -= dt
            return
        target_x, target_y, pause_range = self.pet_stops[self.pet_stop_index]
        dx = target_x - self.pet_x
        dy = target_y - self.pet_y
        distance = math.hypot(dx, dy)
        if distance < 1.5:
            self.pet_x, self.pet_y = target_x, target_y
            self.pet_pause = random.uniform(*pause_range)
            # Usually wander independently; sometimes choose the stop nearest
            # the resident robot, creating an occasional follow behavior.
            if random.random() < 0.35:
                self.pet_stop_index = min(
                    range(len(self.pet_stops)),
                    key=lambda i: abs(self.pet_stops[i][0] - self.x),
                )
            else:
                choices = [i for i in range(len(self.pet_stops)) if i != self.pet_stop_index]
                self.pet_stop_index = random.choice(choices)
            return
        if abs(dx) > 1:
            self.pet_facing_right = dx > 0
        step = min(distance, 22 * dt)
        self.pet_x += dx / distance * step
        self.pet_y += dy / distance * step

    def update(self, dt: float) -> None:
        self.elapsed += dt
        month = datetime.now().month
        if month != self.calendar_month:
            self.calendar_month = month
            if self.halloween_manual is None:
                self.room = self.halloween_room if month == 10 else self.normal_room
        self.update_robot(dt)
        self.update_pet(dt)
        for drop in self.drops:
            drop.update(dt)
        if self.lightning > 0:
            self.lightning = max(0.0, self.lightning - dt)
        elif self.elapsed >= self.next_lightning:
            self.lightning = 0.18
            self.next_lightning = self.elapsed + random.uniform(45.0, 130.0)
        if self.flyby_active:
            self.flyby_x += 55 * dt
            if self.flyby_x > 840:
                self.flyby_active = False
                self.next_flyby = self.elapsed + random.uniform(30.0, 80.0)
        elif self.elapsed >= self.next_flyby:
            self.flyby_active = True
            self.flyby_x = 470.0
        if self.alien_timer > 0:
            self.alien_timer = max(0.0, self.alien_timer - dt)
        elif self.elapsed >= self.next_alien:
            self.alien_timer = 2.4
            self.next_alien = self.elapsed + random.uniform(150.0, 420.0)

    def draw_window_life(self, ticks: int) -> None:
        for x, y, phase in self.twinkles:
            glow = int(90 + 65 * ((math.sin(ticks * 0.0013 + phase) + 1) / 2))
            pygame.draw.circle(self.screen, (glow, max(0, glow - 18), 210), (x, y), 1)
        for drop in self.drops:
            glass_bottom = 205 + (drop.x - 470) * (30 / 330)
            pygame.draw.line(
                self.screen,
                (62, 88, 145),
                (int(drop.x), int(drop.y)),
                (int(drop.x - 1), int(min(drop.y + drop.length, glass_bottom))),
                1,
            )
        if self.flyby_active:
            x = int(self.flyby_x)
            y = int(126 + 7 * math.sin(self.elapsed * 1.8))
            pygame.draw.line(self.screen, (91, 73, 166), (x - 26, y), (x - 8, y), 1)
            pygame.draw.polygon(
                self.screen,
                (72, 103, 151),
                [(x - 7, y - 2), (x + 7, y - 1), (x + 12, y + 2), (x - 5, y + 3)],
            )
            pygame.draw.circle(self.screen, (222, 121, 255), (x - 5, y + 1), 1)
        if self.lightning > 0:
            strength = int(22 * min(1.0, self.lightning / 0.12))
            flash = pygame.Surface((330, 245), pygame.SRCALPHA)
            flash.fill((145, 165, 255, strength))
            self.screen.blit(flash, (470, 0))

    def draw_room_activity(self, ticks: int) -> None:
        """Small opaque accents: cheap to render and readable from across a room."""
        slow = (ticks // 700) % 4
        colors = [(77, 135, 221), (107, 95, 207), (74, 181, 202), (172, 112, 221)]
        pygame.draw.circle(self.screen, colors[slow], (134, 129), 2)
        pygame.draw.circle(self.screen, colors[(slow + 2) % 4], (177, 137), 2)
        pygame.draw.rect(self.screen, colors[(slow + 1) % 4], (335, 188, 3, 2))
        pygame.draw.rect(self.screen, colors[(slow + 3) % 4], (541, 282, 4, 2))
        # Rare visitor: just eyes peeking from the dark lower-left machinery.
        if self.alien_timer > 0:
            blink = self.alien_timer < 0.22
            if not blink:
                pygame.draw.circle(self.screen, (89, 225, 176), (62, 408), 2)
                pygame.draw.circle(self.screen, (89, 225, 176), (69, 408), 2)

    def draw_robot(self, ticks: int) -> None:
        robot = self.robot_right if self.facing_right else self.robot_left
        left = int(self.x - 66)
        top = int(self.y - 132)
        self.screen.blit(robot, (left, top))

        pulse = (math.sin(ticks * 0.0022) + 1) / 2
        antenna_x = left + (51 if self.facing_right else 81)
        antenna = int(145 + pulse * 100)
        pygame.draw.circle(self.screen, (antenna, 95, 255), (antenna_x, top + 19), 3)
        chest_x = left + (71 if self.facing_right else 61)
        chest = int(175 + pulse * 65)
        pygame.draw.circle(self.screen, (255, chest, 72), (chest_x, top + 73), 2)

    def draw_pet(self, ticks: int) -> None:
        pet = self.pet_right if self.pet_facing_right else self.pet_left
        left = int(self.pet_x - pet.get_width() / 2)
        top = int(self.pet_y - pet.get_height())
        self.screen.blit(pet, (left, top))
        # A tiny status-light breath is visible up close without turning the
        # pet into a blinking distraction across the room.
        pulse = (math.sin(ticks * 0.0031 + 1.4) + 1) / 2
        light = int(135 + pulse * 100)
        light_x = left + (pet.get_width() * 61 // 100 if self.pet_facing_right else pet.get_width() * 39 // 100)
        pygame.draw.circle(self.screen, (light, 92, 245), (light_x, top + 19), 1)

    def run(self) -> None:
        while self.running:
            dt = min(0.1, self.clock.tick(FPS) / 1000.0)
            self.handle_events()
            self.update(dt)
            ticks = pygame.time.get_ticks()
            self.screen.blit(self.room, (0, 0))
            self.draw_window_life(ticks)
            self.draw_room_activity(ticks)
            self.draw_pet(ticks)
            self.draw_robot(ticks)
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    RobotNightlight().run()
