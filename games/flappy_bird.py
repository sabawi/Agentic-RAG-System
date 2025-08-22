import pygame
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 400, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
FPS = 60

# Game Variables
score = 0

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Flappy Bird')

# Load images
bird_img = pygame.Surface((30, 30))
bird_img.fill(BLUE)

# Bird class
class Bird:
    def __init__(self):
        self.x = 50
        self.y = HEIGHT // 2
        self.gravity = 0

    def flap(self):
        self.gravity = -10

    def update(self):
        self.gravity += 0.5
        self.y += self.gravity
        if self.y > HEIGHT:
            self.y = HEIGHT
        if self.y < 0:
            self.y = 0

    def draw(self):
        screen.blit(bird_img, (self.x, self.y))

# Main game loop
bird = Bird()
clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                bird.flap()

    screen.fill(WHITE)
    bird.update()
    bird.draw()

    # Display score
    font = pygame.font.SysFont(None, 36)
    score_text = font.render(f'Score: {score}', True, BLACK)
    screen.blit(score_text, (10, 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()