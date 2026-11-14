import asyncio
import math
import random

import pygame


WIDTH, HEIGHT = 900, 680
FPS = 60
TABLE = pygame.Rect(90, 92, 720, 510)
PLAY_LEFT = TABLE.left + 18
PLAY_RIGHT = TABLE.right - 18
PLAY_TOP = TABLE.top + 18
PLAY_BOTTOM = TABLE.bottom - 18

RACKET_W, RACKET_H = 112, 70
RACKET_Y = PLAY_BOTTOM - 44
BALL_RADIUS = 10
START_SPEED = 270.0
MAX_SPEED = 440.0

BACKGROUND = (14, 21, 31)
TABLE_GREEN = (35, 122, 91)
TABLE_DARK = (22, 87, 67)
TABLE_EDGE = (226, 232, 214)
WHITE = (247, 248, 236)
MUTED = (171, 190, 185)
GOLD = (255, 211, 96)
RED = (190, 42, 48)
RUBBER = (229, 55, 59)
WOOD = (177, 108, 48)
WOOD_LIGHT = (224, 159, 78)
SPOTLIGHT_RADIUS = 210
SPOTLIGHT_DARKNESS = 244
SPIKE_SCORE_TRIGGER = 5
SPIKE_WARNING_DURATION = 3.0
SPIKE_ACTIVE_DURATION = 10.0
SPIKE_COUNT = 4
SPIKE_RADIUS = 15
CONTROL_SWAP_SCORE = 30


def new_ball():
    angle = random.uniform(-0.20, 0.20)
    return [float(TABLE.centerx), float(RACKET_Y - 36),
            math.sin(angle) * START_SPEED, -math.cos(angle) * START_SPEED]


def ellipse_contains(x, y, center_x, center_y, radius_x, radius_y):
    dx = (x - center_x) / radius_x
    dy = (y - center_y) / radius_y
    return dx * dx + dy * dy <= 1.0


def draw_racket(surface, center_x):
    blade = pygame.Rect(round(center_x - RACKET_W / 2), RACKET_Y,
                        RACKET_W, RACKET_H)
    handle = pygame.Rect(round(center_x - 13), RACKET_Y + RACKET_H - 3, 26, 48)
    pygame.draw.rect(surface, (73, 42, 25), handle, border_radius=10)
    pygame.draw.rect(surface, WOOD_LIGHT, handle.inflate(-5, -4), border_radius=8)
    pygame.draw.ellipse(surface, (75, 43, 24), blade.inflate(8, 8))
    pygame.draw.ellipse(surface, WOOD, blade)
    pygame.draw.ellipse(surface, RUBBER, blade.inflate(-12, -12))
    pygame.draw.arc(surface, (255, 117, 93), blade.inflate(-12, -12),
                    math.pi * 0.1, math.pi * 0.9, 2)
    pygame.draw.ellipse(surface, (255, 105, 88), blade.inflate(-30, -30), 2)


def draw_table(surface):
    surface.fill(BACKGROUND)
    shadow = TABLE.move(0, 12).inflate(24, 18)
    pygame.draw.rect(surface, (7, 11, 17), shadow, border_radius=12)
    pygame.draw.rect(surface, TABLE_EDGE, TABLE.inflate(8, 8), border_radius=8)
    pygame.draw.rect(surface, TABLE_GREEN, TABLE, border_radius=4)
    pygame.draw.rect(surface, (177, 218, 180), TABLE, 3, border_radius=4)
    pygame.draw.line(surface, (184, 221, 185),
                     (TABLE.left, TABLE.centery), (TABLE.right, TABLE.centery), 2)
    pygame.draw.line(surface, (184, 221, 185),
                     (TABLE.centerx, TABLE.top), (TABLE.centerx, TABLE.bottom), 2)
    pygame.draw.line(surface, TABLE_DARK,
                     (TABLE.left, TABLE.centery + 5),
                     (TABLE.right, TABLE.centery + 5), 5)
    pygame.draw.line(surface, (238, 242, 226),
                     (TABLE.left, TABLE.centery), (TABLE.right, TABLE.centery), 2)
    pygame.draw.line(surface, (243, 244, 224),
                     (TABLE.left - 2, TABLE.centery - 9),
                     (TABLE.right + 2, TABLE.centery - 9), 3)
    pygame.draw.line(surface, (125, 163, 145),
                     (TABLE.left - 2, TABLE.centery - 6),
                     (TABLE.right + 2, TABLE.centery - 6), 1)


def draw_text_center(surface, font, text, y, color):
    image = font.render(text, True, color)
    surface.blit(image, (WIDTH // 2 - image.get_width() // 2, y))


def draw_spotlight(surface, spotlight_x, spotlight_y):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, SPOTLIGHT_DARKNESS))
    for radius in range(SPOTLIGHT_RADIUS, 0, -4):
        alpha = int(SPOTLIGHT_DARKNESS * (radius / SPOTLIGHT_RADIUS) ** 2)
        pygame.draw.circle(
            overlay,
            (0, 0, 0, alpha),
            (round(spotlight_x), round(spotlight_y)),
            radius,
        )
    surface.blit(overlay, (0, 0))


def make_spikes():
    spikes = []
    attempts = 0
    while len(spikes) < SPIKE_COUNT and attempts < 100:
        attempts += 1
        candidate = (
            random.randint(PLAY_LEFT + 24, PLAY_RIGHT - 24),
            random.randint(PLAY_TOP + 30, RACKET_Y - 70),
        )
        if all(math.hypot(candidate[0] - x, candidate[1] - y) > 65
               for x, y in spikes):
            spikes.append(candidate)
    return spikes


def draw_spikes(surface, spikes):
    for x, y in spikes:
        points = [(x, y - SPIKE_RADIUS), (x - 13, y + 10), (x + 13, y + 10)]
        pygame.draw.polygon(surface, (78, 20, 25), points)
        pygame.draw.polygon(surface, (239, 74, 62),
                            [(x, y - SPIKE_RADIUS + 4),
                             (x - 9, y + 7), (x + 9, y + 7)])
        pygame.draw.line(surface, (255, 170, 111),
                         (x, y - SPIKE_RADIUS + 4), (x - 2, y + 3), 2)


async def main():
    pygame.init()
    pygame.display.set_caption("RE:TURN")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("segoeui", 38, bold=True)
    heading_font = pygame.font.SysFont("segoeui", 26, bold=True)
    font = pygame.font.SysFont("segoeui", 21)
    small_font = pygame.font.SysFont("segoeui", 17)

    racket_x = float(TABLE.centerx)
    ball = new_ball()
    score = 0
    best = 0
    state = "ready"
    spotlight_x, spotlight_y = WIDTH / 2, HEIGHT / 2
    spike_event_started = False
    spike_event_time = 0.0
    spikes = []
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 1 / 30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    ball = new_ball()
                    score = 0
                    spike_event_started = False
                    spike_event_time = 0.0
                    spikes = []
                    state = "playing"

        keys = pygame.key.get_pressed()
        controls_swapped = score >= CONTROL_SWAP_SCORE
        if (not controls_swapped and keys[pygame.K_LEFT]) or (
                controls_swapped and keys[pygame.K_a]):
            racket_x -= 430 * dt
        if (not controls_swapped and keys[pygame.K_RIGHT]) or (
                controls_swapped and keys[pygame.K_d]):
            racket_x += 430 * dt
        racket_x = max(PLAY_LEFT + RACKET_W / 2,
                       min(PLAY_RIGHT - RACKET_W / 2, racket_x))

        spotlight_speed = 540 * dt
        if (not controls_swapped and keys[pygame.K_a]) or (
                controls_swapped and keys[pygame.K_LEFT]):
            spotlight_x -= spotlight_speed
        if (not controls_swapped and keys[pygame.K_d]) or (
                controls_swapped and keys[pygame.K_RIGHT]):
            spotlight_x += spotlight_speed
        if (not controls_swapped and keys[pygame.K_w]) or (
                controls_swapped and keys[pygame.K_UP]):
            spotlight_y -= spotlight_speed
        if (not controls_swapped and keys[pygame.K_s]) or (
                controls_swapped and keys[pygame.K_DOWN]):
            spotlight_y += spotlight_speed
        spotlight_x = max(0, min(WIDTH, spotlight_x))
        spotlight_y = max(0, min(HEIGHT, spotlight_y))

        if state == "playing":
            if score >= SPIKE_SCORE_TRIGGER and not spike_event_started:
                spike_event_started = True
            if spike_event_started:
                spike_event_time += dt
            old_y = ball[1]
            ball[0] += ball[2] * dt
            ball[1] += ball[3] * dt

            if ball[0] - BALL_RADIUS <= PLAY_LEFT:
                ball[0] = PLAY_LEFT + BALL_RADIUS
                ball[2] = abs(ball[2])
            elif ball[0] + BALL_RADIUS >= PLAY_RIGHT:
                ball[0] = PLAY_RIGHT - BALL_RADIUS
                ball[2] = -abs(ball[2])

            if ball[1] - BALL_RADIUS <= PLAY_TOP and ball[3] < 0:
                ball[1] = PLAY_TOP + BALL_RADIUS
                ball[3] = abs(ball[3])

            blade_top = RACKET_Y + 7
            crossed_blade = old_y + BALL_RADIUS <= blade_top <= ball[1] + BALL_RADIUS
            inside_blade = ellipse_contains(
                ball[0], blade_top + RACKET_H * 0.34,
                racket_x, RACKET_Y + RACKET_H / 2,
                RACKET_W / 2 + BALL_RADIUS, RACKET_H / 2 + BALL_RADIUS,
            )
            if ball[3] > 0 and crossed_blade and inside_blade:
                ball[1] = RACKET_Y - BALL_RADIUS - 1
                offset = (ball[0] - racket_x) / (RACKET_W / 2)
                offset = max(-1.0, min(1.0, offset))
                post_thirty_boost = max(0, score - 29) * 0.75
                speed = min(
                    MAX_SPEED,
                    math.hypot(ball[2], ball[3]) + 5 + post_thirty_boost,
                )
                ball[2] = offset * speed * 0.82
                ball[3] = -math.sqrt(max(1.0, speed * speed - ball[2] * ball[2]))
                score += 1
                best = max(best, score)

            if ball[1] - BALL_RADIUS > PLAY_BOTTOM:
                state = "game_over"

            spike_phase_active = (
                spike_event_started
                and SPIKE_WARNING_DURATION <= spike_event_time
                < SPIKE_WARNING_DURATION + SPIKE_ACTIVE_DURATION
            )
            if spike_phase_active:
                if not spikes:
                    spikes = make_spikes()
                if any(math.hypot(ball[0] - x, ball[1] - y)
                       <= SPIKE_RADIUS + BALL_RADIUS for x, y in spikes):
                    state = "game_over"

        draw_table(screen)
        spike_phase_active = (
            spike_event_started
            and SPIKE_WARNING_DURATION <= spike_event_time
            < SPIKE_WARNING_DURATION + SPIKE_ACTIVE_DURATION
        )
        if spike_phase_active:
            draw_spikes(screen, spikes)
        draw_racket(screen, racket_x)
        pygame.draw.ellipse(screen, (19, 57, 48),
                            (round(ball[0] - 13), round(ball[1] + 8), 26, 8))
        pygame.draw.circle(screen, (255, 246, 202),
                           (round(ball[0]), round(ball[1])), BALL_RADIUS)
        pygame.draw.circle(screen, (255, 255, 244),
                           (round(ball[0] - 3), round(ball[1] - 3)), 3)
        draw_spotlight(screen, spotlight_x, spotlight_y)

        heading = title_font.render("RE:TURN", True, WHITE)
        screen.blit(heading, (42, 26))
        score_label = small_font.render("RALLY", True, MUTED)
        score_image = heading_font.render(str(score), True, GOLD)
        best_label = small_font.render("BEST", True, MUTED)
        best_image = heading_font.render(str(best), True, WHITE)
        screen.blit(score_label, (625, 29))
        screen.blit(score_image, (625, 47))
        screen.blit(best_label, (720, 29))
        screen.blit(best_image, (720, 47))

        if state == "ready":
            draw_text_center(screen, heading_font, "KEEP THE RALLY GOING", 250, WHITE)
            draw_text_center(screen, font, "Move the light with  W A S D", 295, MUTED)
            draw_text_center(screen, font, "Press SPACE to serve", 330, GOLD)
        elif state == "game_over":
            draw_text_center(screen, heading_font, "RALLY OVER", 250, WHITE)
            draw_text_center(screen, font, f"You hit the ball {score} times", 295, MUTED)
            draw_text_center(screen, font, "Press SPACE to try again", 330, GOLD)

        if (state == "playing" and spike_event_started
                and 0 <= spike_event_time < SPIKE_WARNING_DURATION):
            countdown = max(1, math.ceil(SPIKE_WARNING_DURATION - spike_event_time))
            panel = pygame.Surface((430, 112), pygame.SRCALPHA)
            panel.fill((18, 12, 19, 225))
            pygame.draw.rect(panel, (244, 82, 72, 210), panel.get_rect(), 2)
            screen.blit(panel, (WIDTH // 2 - 215, 205))
            draw_text_center(screen, heading_font, "SPIKES INCOMING", 218, (255, 126, 91))
            draw_text_center(screen, font, f"DON'T BOUNCE INTO THEM   {countdown}", 260, WHITE)
        elif state == "playing" and spike_phase_active:
            draw_text_center(screen, small_font, "AVOID THE SPIKES!", 112, (255, 126, 91))

        pygame.draw.line(screen, (68, 87, 86), (42, 635), (858, 635), 1)
        if controls_swapped:
            control_text = (
                "ARROWS  spotlight     A / D  racket     "
                "SPACE  restart     ESC  quit"
            )
        else:
            control_text = (
                "W A S D  spotlight     LEFT / RIGHT  racket     "
                "SPACE  restart     ESC  quit"
            )
        instructions = small_font.render(control_text, True, MUTED)
        screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, 647))
        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
