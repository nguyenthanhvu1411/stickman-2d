"""Stickman Rooftops, a keyboard-controlled Pygame platformer."""

import asyncio
import math

import pygame

WIDTH, HEIGHT = 900, 500
GROUND = 404
SPAWN = (72, GROUND - 54)
ROOFS = (
    pygame.Rect(0, GROUND, 235, 96),
    pygame.Rect(290, GROUND - 35, 155, 131),
    pygame.Rect(500, GROUND - 74, 155, 170),
    pygame.Rect(716, GROUND - 42, 184, 138),
)
COINS = ((165, 364), (360, 325), (575, 284), (818, 308))
EXIT = pygame.Rect(827, 286, 36, 76)
INK = "#17253c"
MINT = "#63f7bc"


class Game:
    def __init__(self):
        self.best = 0
        self.reset()

    def reset(self):
        self.x, self.y = SPAWN
        self.velocity = 0.0
        self.grounded = True
        self.facing = 1
        self.walk_time = 0.0
        self.coins = set(COINS)
        self.state = "playing"

    def update(self, dt, direction, jump):
        if self.state != "playing":
            return
        if direction:
            self.facing = direction
            self.walk_time += dt
        else:
            self.walk_time = 0.0
        self.x = max(0, min(WIDTH - 32, self.x + direction * 290 * dt))
        if jump and self.grounded:
            self.velocity = -490

        previous_bottom = self.y + 54
        self.velocity += 1260 * dt
        self.y += self.velocity * dt
        self.grounded = False
        if self.velocity >= 0:
            for roof in ROOFS:
                if self.x + 32 > roof.left and self.x < roof.right:
                    if previous_bottom <= roof.top <= self.y + 54:
                        self.y = roof.top - 54
                        self.velocity = 0
                        self.grounded = True
                        break

        player = pygame.Rect(round(self.x), round(self.y), 32, 54)
        self.coins = {coin for coin in self.coins if not player.inflate(16, 16).collidepoint(coin)}
        self.best = max(self.best, len(COINS) - len(self.coins))
        if self.y > HEIGHT + 50:
            self.state = "fell"
        elif not self.coins and player.colliderect(EXIT):
            self.state = "won"


def label(surface, font, text, position, color):
    surface.blit(font.render(text, True, color), position)


def draw(screen, game, small, large):
    screen.fill("#172944")
    pygame.draw.circle(screen, "#fbd596", (740, 124), 44)
    for index in range(15):
        left = index * 67
        height = 62 + (index * 73) % 170
        top = HEIGHT - height
        pygame.draw.rect(screen, "#253e5a", (left, top, 58, height))
        for row in range(top + 18, HEIGHT - 12, 24):
            pygame.draw.rect(screen, "#3a5570", (left + 10, row, 7, 9))
    for roof in ROOFS:
        pygame.draw.rect(screen, INK, roof)
        pygame.draw.rect(screen, "#82a3c3", (roof.x, roof.y, roof.w, 5))
    pygame.draw.rect(screen, MINT if not game.coins else "#8095a7", EXIT, 3, border_radius=4)
    label(screen, small, "EXIT", (EXIT.x - 3, EXIT.y - 24), "#eef3fa")
    for x, y in game.coins:
        pygame.draw.circle(screen, "#ffc85f", (x, y), 11)
        pygame.draw.circle(screen, "#8b561e", (x, y), 6, 2)

    x, y = round(game.x) + 16, round(game.y)
    stride = round(9 * math.sin(game.walk_time * 17))
    pygame.draw.circle(screen, "#eef3fa", (x, y + 10), 9, 3)
    pygame.draw.line(screen, "#eef3fa", (x, y + 20), (x, y + 38), 4)
    pygame.draw.line(screen, "#eef3fa", (x, y + 24), (x - 14, y + 31 + stride // 2), 3)
    pygame.draw.line(screen, "#eef3fa", (x, y + 24), (x + 14, y + 31 - stride // 2), 3)
    pygame.draw.line(screen, "#eef3fa", (x, y + 37), (x - 10 - stride, y + 53), 3)
    pygame.draw.line(screen, "#eef3fa", (x, y + 37), (x + 10 + stride, y + 53), 3)
    pygame.draw.line(screen, MINT, (x - 6 * game.facing, y + 20), (x - 18 * game.facing, y + 16), 4)

    label(screen, large, "Stickman Rooftops", (26, 22), "#eef3fa")
    label(screen, small, "A / D or arrows: Move     Space: Jump     R: Restart", (27, 65), "#b8cbe0")
    label(screen, small, f"Coins  {len(COINS) - len(game.coins)} / {len(COINS)}",
          (27, 101), "#ffc85f")
    if game.state != "playing":
        card = pygame.Rect(234, 170, 432, 150)
        pygame.draw.rect(screen, INK, card, border_radius=14)
        pygame.draw.rect(screen, MINT, card, 2, border_radius=14)
        title = "Rooftop cleared!" if game.state == "won" else "You missed the rooftop"
        label(screen, large, title, (255, 195), "#eef3fa")
        label(screen, small, f"Best: {game.best} / {len(COINS)}    Press R to try again",
              (255, 258), MINT)


async def main():
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Stickman Rooftops")
    small = pygame.font.Font(None, 25)
    large = pygame.font.Font(None, 44)
    clock = pygame.time.Clock()
    game = Game()

    while True:
        dt = min(clock.tick(60) / 1000, 1 / 30)
        jump = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()
                if event.key == pygame.K_SPACE:
                    jump = True
        keys = pygame.key.get_pressed()
        direction = int(keys[pygame.K_d] or keys[pygame.K_RIGHT])
        direction -= int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        game.update(dt, direction, jump)
        draw(screen, game, small, large)
        pygame.display.flip()
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
