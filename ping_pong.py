import pygame
import sys
import cv2
import mediapipe as mp
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 800
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)  # Red color for circles
BALL_COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
BACKGROUND_COLOR = (0, 0, 0)  # Dark grey
BALL_RADIUS = 20  # Reduced size of the ball
PADDLE_WIDTH, PADDLE_HEIGHT = 100, 10
INITIAL_BALL_SPEED_X, INITIAL_BALL_SPEED_Y = 5, 5
BALL_SPEED_INCREMENT = 0.2  # Speed increment after every ball touch
FONT_SIZE = 24
PADDLE_SPEED = 5
PADDLE_SMOOTHING = 0.1  # Smoothing factor for paddle movement

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vertical Ping Pong Game")

# Paddle and ball setup
bottom_paddle = pygame.Rect((WIDTH - PADDLE_WIDTH) // 2, HEIGHT - 30 - PADDLE_HEIGHT, PADDLE_WIDTH, PADDLE_HEIGHT)
ball = pygame.Rect(WIDTH // 2, HEIGHT // 2, BALL_RADIUS, BALL_RADIUS)
ball_color_index = 0

# NPC board setup
npc_board = pygame.Rect((WIDTH - PADDLE_WIDTH) // 2, 30, PADDLE_WIDTH, PADDLE_HEIGHT)

# Score and lives variables
player_score = 0
player_lives = 3
hit_count = 0

# Fonts setup
font = pygame.font.Font(None, FONT_SIZE)

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Initialize webcam
cap = cv2.VideoCapture(0)

# Ball speed variables
ball_speed_x, ball_speed_y = INITIAL_BALL_SPEED_X, INITIAL_BALL_SPEED_Y

# Gesture control toggle button
gesture_enabled = False
toggle_button_rect = pygame.Rect(WIDTH - 150, 20, 140, 40)  # Right side toggle button
toggle_button_color = WHITE
toggle_button_bg_color = (0, 0, 0, 100)  # Semi-transparent background color for the toggle button

# Game Over animation variables
game_over_font = pygame.font.Font(None, 36)
game_over_text = game_over_font.render("Game Over!", True, WHITE)
game_over_text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
game_over_visible = False
game_over_flash_interval = 500  # milliseconds
game_over_last_flash = pygame.time.get_ticks()

# Pause/Resume variables
game_paused = False
restart_button_rect = pygame.Rect(WIDTH // 2 - 70, HEIGHT // 2 + 40, 140, 40)
resume_button_rect = pygame.Rect(WIDTH // 2 - 70, HEIGHT // 2 + 100, 140, 40)

def detect_hand_position():
    ret, frame = cap.read()
    if not ret:
        return None

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    hand_center_x = None

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            index_finger_x = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * WIDTH
            hand_center_x = index_finger_x

            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    cv2.imshow('Hand Tracking', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        pygame.quit()
        sys.exit()

    return hand_center_x

def draw_toggle_button():
    global toggle_button_color, toggle_button_bg_color
    if gesture_enabled:
        toggle_button_bg_color = (0, 0, 0, 0)  # Fully transparent when gesture enabled
    pygame.draw.rect(screen, toggle_button_bg_color, toggle_button_rect)  # Draw semi-transparent background first
    toggle_text = font.render("on / off", True, toggle_button_color)
    text_rect = toggle_text.get_rect(center=toggle_button_rect.center)  # Centering the text
    screen.blit(toggle_text, text_rect)

def draw_lives():
    circle_radius = 10
    circle_gap = 30
    start_x = 30
    start_y = 30
    for i in range(player_lives):
        pygame.draw.circle(screen, RED, (start_x + i * (circle_gap), start_y), circle_radius)

def draw_score():
    player_score_text = font.render(f'Score: {player_score}', True, WHITE)
    screen.blit(player_score_text, (20, 20))  # Render score on the left side

def game_over_animation():
    global game_over_visible, game_over_last_flash

    current_time = pygame.time.get_ticks()
    if current_time - game_over_last_flash > game_over_flash_interval:
        game_over_visible = not game_over_visible
        game_over_last_flash = current_time

    if game_over_visible:
        screen.blit(game_over_text, game_over_text_rect)

def draw_buttons():
    pygame.draw.rect(screen, (0, 255, 0), restart_button_rect)  # Green for restart button
    restart_text = font.render("Restart", True, BLACK)
    restart_text_rect = restart_text.get_rect(center=restart_button_rect.center)
    screen.blit(restart_text, restart_text_rect)

    pygame.draw.rect(screen, (0, 0, 255), resume_button_rect)  # Blue for resume button
    resume_text = font.render("Resume", True, WHITE)
    resume_text_rect = resume_text.get_rect(center=resume_button_rect.center)
    screen.blit(resume_text, resume_text_rect)

def reset_game():
    global player_score, player_lives, ball_speed_x, ball_speed_y, hit_count, game_paused
    player_score = 0
    player_lives = 3
    ball_speed_x, ball_speed_y = INITIAL_BALL_SPEED_X, INITIAL_BALL_SPEED_Y
    hit_count = 0
    ball.x = WIDTH // 2
    ball.y = HEIGHT // 2
    game_paused = False

# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            cap.release()
            cv2.destroyAllWindows()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if toggle_button_rect.collidepoint(event.pos):
                gesture_enabled = not gesture_enabled
                toggle_button_color = WHITE if gesture_enabled else BLACK
                toggle_button_bg_color = (50, 50, 50, 100) if gesture_enabled else (50, 50, 50, 100)
            elif restart_button_rect.collidepoint(event.pos):
                reset_game()
            elif resume_button_rect.collidepoint(event.pos) and game_paused:
                game_paused = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_paused = True
            elif event.key == pygame.K_SPACE:
                game_paused = False

    if game_paused:
        screen.fill(BACKGROUND_COLOR)
        draw_buttons()
        pygame.display.flip()
        continue

    if gesture_enabled:
        hand_center_x = detect_hand_position()
    else:
        hand_center_x = None

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        bottom_paddle.centerx -= PADDLE_SPEED
    if keys[pygame.K_RIGHT]:
        bottom_paddle.centerx += PADDLE_SPEED

    if ball.centerx < npc_board.centerx:
        npc_board.centerx -= min(PADDLE_SPEED, npc_board.centerx - ball.centerx)
    elif ball.centerx > npc_board.centerx:
        npc_board.centerx += min(PADDLE_SPEED, ball.centerx - npc_board.centerx)

    if bottom_paddle.left < 0:
        bottom_paddle.left = 0
    elif bottom_paddle.right > WIDTH:
        bottom_paddle.right = WIDTH

    if npc_board.left < 0:
        npc_board.left = 0
    elif npc_board.right > WIDTH:
        npc_board.right = WIDTH

    if gesture_enabled and hand_center_x is not None:
        bottom_paddle.centerx = int(hand_center_x)
    elif keys[pygame.K_LEFT]:
        bottom_paddle.centerx -= PADDLE_SPEED
    elif keys[pygame.K_RIGHT]:
        bottom_paddle.centerx += PADDLE_SPEED

    ball.x += ball_speed_x
    ball.y += ball_speed_y

    if ball.left <= 0 or ball.right >= WIDTH:
        ball_speed_x = -ball_speed_x

    if ball.colliderect(bottom_paddle) or ball.colliderect(npc_board):
        ball_speed_y = -ball_speed_y
        ball_color_index = (ball_color_index + 1) % len(BALL_COLORS)
        hit_count += 1
        if hit_count % 1 == 0:
            if ball_speed_x > 0:
                ball_speed_x += BALL_SPEED_INCREMENT
            else:
                ball_speed_x -= BALL_SPEED_INCREMENT

            if ball_speed_y > 0:
                ball_speed_y += BALL_SPEED_INCREMENT
            else:
                ball_speed_y -= BALL_SPEED_INCREMENT

    if ball.top <= 0:
        player_score += 1
        ball.x = WIDTH // 2
        ball.y = HEIGHT // 2
        ball_speed_x = INITIAL_BALL_SPEED_X if random.randint(0, 1) == 0 else -INITIAL_BALL_SPEED_X
        ball_speed_y = INITIAL_BALL_SPEED_Y if ball_speed_y > 0 else -INITIAL_BALL_SPEED_Y
        hit_count = 0

    if ball.bottom >= HEIGHT:
        player_lives -= 1
        if player_lives == 0:
            ball.x = WIDTH // 2
            ball.y = HEIGHT // 2
            ball_speed_x = 0
            ball_speed_y = 0
        else:
            ball.x = WIDTH // 2
            ball.y = HEIGHT // 2
            ball_speed_x = INITIAL_BALL_SPEED_X if random.randint(0, 1) == 0 else -INITIAL_BALL_SPEED_X
            ball_speed_y = INITIAL_BALL_SPEED_Y if ball_speed_y > 0 else -INITIAL_BALL_SPEED_Y
        hit_count = 0

    screen.fill(BACKGROUND_COLOR)
    pygame.draw.rect(screen, WHITE, bottom_paddle)
    pygame.draw.rect(screen, WHITE, npc_board)
    pygame.draw.ellipse(screen, BALL_COLORS[ball_color_index], ball)
    pygame.draw.aaline(screen, WHITE, (0, HEIGHT // 2), (WIDTH, HEIGHT // 2))

    if gesture_enabled:
        draw_score()
    else:
        draw_lives()

    draw_toggle_button()

    if player_lives == 0:
        game_over_animation()
        draw_buttons()

    pygame.display.flip()
    pygame.time.Clock().tick(60)
