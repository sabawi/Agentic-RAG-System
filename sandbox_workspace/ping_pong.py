import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Set up display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Ping Pong Game')

# Colors
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
yellow = (255, 255, 0)

# Ball settings
ball_size = 20
ball_x = width // 2
ball_y = height // 2
ball_x_speed = random.choice([-5, 5])
ball_y_speed = random.choice([-5, 5])

# Paddle settings
paddle_width = 10
paddle_height = 100
paddle_speed = 10
left_paddle_y = height // 2 - paddle_height // 2
right_paddle_y = height // 2 - paddle_height // 2

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] and left_paddle_y > 0:
        left_paddle_y -= paddle_speed
    if keys[pygame.K_s] and left_paddle_y < height - paddle_height:
        left_paddle_y += paddle_speed
    if keys[pygame.K_UP] and right_paddle_y > 0:
        right_paddle_y -= paddle_speed
    if keys[pygame.K_DOWN] and right_paddle_y < height - paddle_height:
        right_paddle_y += paddle_speed

    # Move the ball
    ball_x += ball_x_speed
    ball_y += ball_y_speed

    # Ball collision with top and bottom
    if ball_y <= 0 or ball_y >= height - ball_size:
        ball_y_speed = -ball_y_speed
        # pygame.mixer.Sound.play(pygame.mixer.Sound('sound_effect.wav'))  # Funny sound effect

    # Ball collision with paddles
    if (ball_x <= paddle_width and left_paddle_y < ball_y < left_paddle_y + paddle_height) or (ball_x >= width - paddle_width - ball_size and right_paddle_y < ball_y < right_paddle_y + paddle_height):
        ball_x_speed = -ball_x_speed
        pygame.mixer.Sound.play(pygame.mixer.Sound('sound_effect.wav'))  # Funny sound effect

    # Reset ball if it goes out of bounds
    if ball_x < 0 or ball_x > width:
        ball_x = width // 2
        ball_y = height // 2
        ball_x_speed = random.choice([-5, 5])
        ball_y_speed = random.choice([-5, 5])

    # Fill the screen with a bright color
    screen.fill(random.choice([red, green, blue, yellow]))

    # Draw paddles and ball
    pygame.draw.rect(screen, white, (0, left_paddle_y, paddle_width, paddle_height))
    pygame.draw.rect(screen, white, (width - paddle_width, right_paddle_y, paddle_width, paddle_height))
    pygame.draw.ellipse(screen, white, (ball_x, ball_y, ball_size, ball_size))

    # Update display
    pygame.display.flip()
    pygame.time.delay(30)