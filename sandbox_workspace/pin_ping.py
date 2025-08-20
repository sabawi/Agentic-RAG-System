import pygame
import random

# Initialize Pygame
pygame.init()

# Set up the display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Pin-Ping Game')

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Game variables
ball_pos = [width // 2, height // 2]
ball_radius = 20
ball_speed = [random.choice([-4, 4]), random.choice([-4, 4])]

# Load sounds
bounce_sound = pygame.mixer.Sound(pygame.mixer.Sound('path/to/sound.wav'))

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Move the ball
    ball_pos[0] += ball_speed[0]
    ball_pos[1] += ball_speed[1]

    # Bounce the ball off the walls
    if ball_pos[0] <= ball_radius or ball_pos[0] >= width - ball_radius:
        ball_speed[0] = -ball_speed[0]
        bounce_sound.play()
    if ball_pos[1] <= ball_radius or ball_pos[1] >= height - ball_radius:
        ball_speed[1] = -ball_speed[1]
        bounce_sound.play()

    # Fill the screen with a bright color
    screen.fill(WHITE)

    # Draw the ball
    pygame.draw.circle(screen, random.choice([RED, GREEN, BLUE, YELLOW]), ball_pos, ball_radius)

    # Update the display
    pygame.display.flip()
    pygame.time.delay(30)

pygame.quit()