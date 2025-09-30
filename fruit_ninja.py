import cv2
import mediapipe as mp
import pygame
import random
import sys
import numpy as np
import math
import time
from typing import List, Dict, Tuple

# --- Inicializar pygame ---
pygame.init()
pygame.mixer.init()

# --- CONFIGURACIÓN DE PANTALLA FIJA (Ventana) ---
WIDTH, HEIGHT = 800, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🥷 RETRO FRUIT NINJA ⚔️✨")

# === COLORES RETRO NEON ===
BLACK = (0, 0, 0)
NEON_CYAN = (0, 255, 255)
NEON_PINK = (255, 20, 147)
NEON_GREEN = (57, 255, 20)
NEON_ORANGE = (255, 165, 0)
NEON_PURPLE = (138, 43, 226)
NEON_YELLOW = (255, 255, 0)
DARK_BLUE = (25, 25, 112)
ELECTRIC_BLUE = (0, 191, 255)
HOT_PINK = (255, 105, 180)
LIME_GREEN = (50, 205, 50)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)

# === CONFIGURACIÓN DEL JUEGO ===
GAME_DURATION = 3 * 60 * 1000
LEVEL_UP_TIME = 30 * 1000
BASE_SPEED_MIN = 5
BASE_SPEED_MAX = 10
CALIBRATION_TIME_MS = 4000

# === VARIABLES DE ESTADO ===
game_state = "MENU"
num_players = 1
calibration_start_time = 0

player_states = {
    1: {"score": 0, "alive": True, "death_time": 0, "combo": 0, "last_hit_time": 0},
    2: {"score": 0, "alive": True, "death_time": 0, "combo": 0, "last_hit_time": 0}
}

objects = []
splashes = []
particles = []
sword_trails = []
background_particles = []
screen_effects = []
combo_texts = []
start_time = pygame.time.get_ticks()
current_level = 0
frame_count = 0
menu_time = 0

# === CONFIGURACIÓN CÁMARA ===
cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils
clock = pygame.time.Clock()

# === CLASES PARA EFECTOS ===

class Particle:
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], size: int = 3):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-8, -2)
        self.color = color
        self.size = size
        self.life = 255
        self.gravity = 0.3
        self.fade_speed = random.uniform(3, 8)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= self.fade_speed
        self.size = max(1, self.size - 0.05)

    def draw(self, surface):
        if self.life > 0:
            alpha = max(0, int(self.life))
            color_with_alpha = (*self.color, alpha)
            temp_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, color_with_alpha, (self.size, self.size), int(self.size))
            surface.blit(temp_surf, (int(self.x - self.size), int(self.y - self.size)))

class BackgroundParticle:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.5, 2)
        self.size = random.randint(1, 3)
        self.color = random.choice([NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_PURPLE])
        self.alpha = random.randint(50, 150)
        self.direction = random.uniform(0, 360)

    def update(self):
        self.x += math.cos(math.radians(self.direction)) * self.speed
        self.y += math.sin(math.radians(self.direction)) * self.speed
        
        if self.x < 0: self.x = WIDTH
        if self.x > WIDTH: self.x = 0
        if self.y < 0: self.y = HEIGHT
        if self.y > HEIGHT: self.y = 0

    def draw(self, surface):
        temp_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color, self.alpha)
        pygame.draw.circle(temp_surf, color_with_alpha, (self.size, self.size), self.size)
        surface.blit(temp_surf, (int(self.x - self.size), int(self.y - self.size)))

class SwordTrail:
    def __init__(self, points: List[Tuple[int, int]], color: Tuple[int, int, int]):
        self.points = points.copy()
        self.color = color
        self.alpha = 255
        self.width = 8

    def update(self):
        self.alpha -= 15
        self.width = max(1, self.width - 0.3)

    def draw(self, surface):
        if len(self.points) > 1 and self.alpha > 0:
            for i in range(len(self.points) - 1):
                start_pos = self.points[i]
                end_pos = self.points[i + 1]
                
                temp_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                color_with_alpha = (*self.color, max(0, int(self.alpha)))
                pygame.draw.line(temp_surf, color_with_alpha, start_pos, end_pos, int(self.width))
                surface.blit(temp_surf, (0, 0))

class ScreenShake:
    def __init__(self, intensity: int, duration: int):
        self.intensity = intensity
        self.duration = duration
        self.timer = 0

    def update(self):
        self.timer += 1
        return self.timer < self.duration

    def get_offset(self):
        if self.timer < self.duration:
            return (
                random.randint(-self.intensity, self.intensity),
                random.randint(-self.intensity, self.intensity)
            )
        return (0, 0)

class ComboText:
    def __init__(self, x: int, y: int, combo: int):
        self.x = x
        self.y = y
        self.combo = combo
        self.timer = 0
        self.max_time = 60
        self.size = 40 + combo * 5

    def update(self):
        self.timer += 1
        self.y -= 2
        return self.timer < self.max_time

    def draw(self, surface):
        alpha = int(255 * (1 - self.timer / self.max_time))
        font = pygame.font.SysFont(None, int(self.size))
        
        if self.combo >= 5:
            color = NEON_PINK
            text = f"COMBO x{self.combo}! INSANE!"
        elif self.combo >= 3:
            color = NEON_ORANGE
            text = f"COMBO x{self.combo}!"
        else:
            color = NEON_YELLOW
            text = f"x{self.combo}"
        
        temp_surf = pygame.Surface((300, 60), pygame.SRCALPHA)
        text_surf = font.render(text, True, (*color, alpha))
        temp_surf.blit(text_surf, (0, 0))
        surface.blit(temp_surf, (self.x - 150, self.y - 30))

# === INICIALIZACIÓN DE PARTÍCULAS DE FONDO ===
for _ in range(50):
    background_particles.append(BackgroundParticle())

# === FUNCIONES DE CARGA ===

def load_fruit_images():
    fruit_data = [
        ("cereza", "frutas/cereza.png", NEON_PINK),
        ("manzana", "frutas/manzana.png", NEON_GREEN),
        ("sandia", "frutas/sandia.png", HOT_PINK),
        ("mora", "frutas/mora.png", NEON_PURPLE),
        ("naranja", "frutas/naranja.png", NEON_ORANGE)
    ]
    
    loaded_fruits = []
    for name, path, neon_color in fruit_data:
        try:
            image = pygame.image.load(path).convert_alpha()
            # 🥝 CAMBIO CLAVE: Escalar la imagen a un tamaño razonable
            image = pygame.transform.scale(image, (40, 40)) 
            # Aplicar efecto de brillo
            glow_image = create_glow_effect(image, neon_color)
            loaded_fruits.append({
                "name": name, 
                "image": image,
                "glow_image": glow_image,
                "color": neon_color
            })
        except pygame.error:
            # Crear frutas sintéticas si no existen las imágenes
            synthetic_image = create_synthetic_fruit(name, neon_color)
            glow_image = create_glow_effect(synthetic_image, neon_color)
            loaded_fruits.append({
                "name": name,
                "image": synthetic_image,
                "glow_image": glow_image,
                "color": neon_color
            })
    return loaded_fruits

def create_synthetic_fruit(name: str, color: Tuple[int, int, int]) -> pygame.Surface:
    """Crea una fruta sintética si no existe la imagen"""
    # 🥝 CAMBIO CLAVE: Reducir el tamaño de la superficie base a 20x20
    surf = pygame.Surface((20, 20), pygame.SRCALPHA)
    center = (10, 10) # <-- Ajustar el centro
    
    # Gradiente circular más pequeño
    for r in range(9, 0, -1): # <-- Ajustar el radio máximo
        alpha = int(255 * (r / 15))
        temp_color = (*color, alpha)
        pygame.draw.circle(surf, temp_color, center, r)
    
    # Brillo central más pequeño
    pygame.draw.circle(surf, (255, 255, 255, 180), (8, 8), 3) # <-- Ajustar posición y radio
    
    # 🥝 CAMBIO CLAVE: Escalar la imagen sintética a 40x40 para que coincida con las cargadas
    final_surf = pygame.transform.scale(surf, (40, 40))
    return final_surf

def create_glow_effect(image: pygame.Surface, glow_color: Tuple[int, int, int]) -> pygame.Surface:
    """Crea un efecto de brillo alrededor de la imagen"""
    size = image.get_size()
    glow_surf = pygame.Surface((size[0] + 20, size[1] + 20), pygame.SRCALPHA)
    
    # Múltiples capas de brillo
    for i in range(5):
        temp_surf = pygame.Surface((size[0] + i*4, size[1] + i*4), pygame.SRCALPHA)
        # Usar la imagen de entrada que ya está escalada
        scaled_img = pygame.transform.scale(image, (size[0] + i*4, size[1] + i*4))
        temp_surf.blit(scaled_img, (0, 0))
        
        # Aplicar color de brillo
        temp_surf.fill((*glow_color, 50 - i*8), special_flags=pygame.BLEND_RGBA_MULT)
        glow_surf.blit(temp_surf, (10 - i*2, 10 - i*2))
    
    # Imagen original encima
    glow_surf.blit(image, (10, 10))
    return glow_surf

try:
    fruit_images = load_fruit_images()
except:
    # Crear frutas sintéticas como respaldo
    fruit_images = []
    colors = [NEON_PINK, NEON_GREEN, HOT_PINK, NEON_PURPLE, NEON_ORANGE]
    names = ["cereza", "manzana", "sandia", "mora", "naranja"]
    
    for name, color in zip(names, colors):
        synthetic_image = create_synthetic_fruit(name, color)
        glow_image = create_glow_effect(synthetic_image, color)
        fruit_images.append({
            "name": name,
            "image": synthetic_image,
            "glow_image": glow_image,
            "color": color
        })

# === FUNCIONES DE EFECTOS VISUALES ===

def draw_glitch_text(surface, text: str, pos: Tuple[int, int], font, color: Tuple[int, int, int]):
    """Efecto de texto glitcheado"""
    offsets = [(0, 0), (2, 0), (-2, 0), (0, 2), (0, -2)]
    colors = [color, NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_PURPLE]
    
    for offset, glitch_color in zip(offsets, colors):
        glitch_pos = (pos[0] + offset[0], pos[1] + offset[1])
        text_surf = font.render(text, True, glitch_color)
        surface.blit(text_surf, text_surf.get_rect(center=glitch_pos))

def draw_pulsing_text(surface, text: str, pos: Tuple[int, int], base_size: int, color: Tuple[int, int, int], time_factor: float):
    """Texto que pulsa"""
    pulse = math.sin(time_factor / 200) * 10
    font_size = int(base_size + pulse)
    font = pygame.font.SysFont(None, font_size)
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, text_surf.get_rect(center=pos))

def draw_retro_border(surface, rect: pygame.Rect, color: Tuple[int, int, int], width: int = 3):
    """Borde retro con esquinas"""
    # Líneas principales
    pygame.draw.rect(surface, color, rect, width)
    
    # Esquinas decorativas
    corner_size = 15
    corners = [
        rect.topleft,
        (rect.topright[0] - corner_size, rect.topright[1]),
        (rect.bottomleft[0], rect.bottomleft[1] - corner_size),
        (rect.bottomright[0] - corner_size, rect.bottomright[1] - corner_size)
    ]
    
    for corner in corners:
        pygame.draw.line(surface, color, corner, (corner[0] + corner_size, corner[1]), width + 2)
        pygame.draw.line(surface, color, corner, (corner[0], corner[1] + corner_size), width + 2)

def create_explosion_particles(x: int, y: int, color: Tuple[int, int, int], count: int = 15):
    """Crea partículas de explosión"""
    global particles
    for _ in range(count):
        particles.append(Particle(x, y, color, random.randint(3, 8)))

# === FUNCIONES DE JUEGO ===

def spawn_object(level: int, player_zone: int = 0):
    """Genera objetos con efectos visuales mejorados"""
    speed_min = BASE_SPEED_MIN + level * 1.5
    speed_max = BASE_SPEED_MAX + level * 2.5
    bomb_prob = min(0.5, 0.2 + level * 0.1)
    
    speed = random.randint(int(speed_min), int(speed_max))
    y = -50
    
    if player_zone == 1:
        x_min, x_max = 50, WIDTH // 2 - 50
    elif player_zone == 2:
        x_min, x_max = WIDTH // 2 + 50, WIDTH - 50
    else:
        x_min, x_max = 50, WIDTH - 50
        
    x = random.randint(x_min, x_max)

    # El tamaño del rectángulo de colisión debe ser similar al de la imagen escalada (40x40)
    rect_size = 40 

    if random.random() < bomb_prob:
        return {
            "rect": pygame.Rect(x, y, rect_size, rect_size),
            "speed": speed,
            "kind": "bomb",
            "zone": player_zone,
            "rotation": 0,
            "pulse_time": 0
        }
    else:
        fruit_item = random.choice(fruit_images)
        return {
            "rect": pygame.Rect(x, y, rect_size, rect_size),
            "speed": speed,
            "image": fruit_item["glow_image"],
            "kind": "fruit",
            "zone": player_zone,
            "color": fruit_item["color"],
            "rotation": 0,
            "spin_speed": random.uniform(-10, 10)
        }

def draw_neon_sword(surface, center_pos: Tuple[int, int], angle: float = 0, color: Tuple[int, int, int] = SILVER, player_id: int = 1):
    """Dibuja espada con efectos neón"""
    cx, cy = center_pos

    cos_a = math.cos(math.radians(angle))
    sin_a = math.sin(math.radians(angle))

    def rotate_point(x: int, y: int) -> Tuple[int, int]:
        rx = x * cos_a - y * sin_a + cx
        ry = x * sin_a + y * cos_a + cy
        return int(rx), int(ry)

    blade_length = 90
    blade_width = 10
    
    # Efecto de brillo de la hoja
    for i in range(5):
        glow_color = (*color, 100 - i * 15)
        blade_points = [
            rotate_point(-blade_width // 2 - i, 0),
            rotate_point(blade_width // 2 + i, 0),
            rotate_point(blade_width // 2 + i, blade_length + i * 2),
            rotate_point(-blade_width // 2 - i, blade_length + i * 2)
        ]
        
        temp_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(temp_surf, glow_color, blade_points)
        surface.blit(temp_surf, (0, 0))
    
    # Hoja principal
    blade_points = [
        rotate_point(-blade_width // 2, 0),
        rotate_point(blade_width // 2, 0),
        rotate_point(blade_width // 2, blade_length),
        rotate_point(-blade_width // 2, blade_length)
    ]
    pygame.draw.polygon(surface, color, blade_points)
    
    # Empuñadura con brillo
    handle_color = NEON_CYAN if player_id == 1 else NEON_PINK
    guard_points = [
        rotate_point(-15, -3), rotate_point(15, -3),
        rotate_point(15, 3), rotate_point(-15, 3)
    ]
    pygame.draw.polygon(surface, handle_color, guard_points)
    
    # Cristal en la empuñadura
    crystal_pos = rotate_point(0, -15)
    pygame.draw.circle(surface, (255, 255, 255), crystal_pos, 5)
    pygame.draw.circle(surface, handle_color, crystal_pos, 3)

def cv2_to_pygame(cv_img):
    """Convierte imagen de OpenCV a Pygame con efectos"""
    cv_img = cv2.resize(cv_img, (WIDTH, HEIGHT))
    cv_img = cv2.flip(cv_img, 1)
    cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    cv_img = np.rot90(cv_img)
    cv_img = np.flipud(cv_img)
    return pygame.surfarray.make_surface(cv_img)

def reset_game(players: int):
    """Reinicia el juego"""
    global objects, game_state, start_time, current_level, num_players, player_states
    global frame_count, splashes, calibration_start_time, particles, sword_trails
    global combo_texts, screen_effects
    
    num_players = players
    objects.clear()
    splashes.clear()
    particles.clear()
    sword_trails.clear()
    combo_texts.clear()
    screen_effects.clear()
    
    game_state = "STARTING"
    calibration_start_time = pygame.time.get_ticks()
    start_time = 0
    current_level = 0
    frame_count = 0
    
    player_states = {
        1: {"score": 0, "alive": True, "death_time": 0, "combo": 0, "last_hit_time": 0},
        2: {"score": 0, "alive": True, "death_time": 0, "combo": 0, "last_hit_time": 0}
    }

def draw_retro_menu():
    """Menú principal con estilo retro"""
    global menu_time
    menu_time += 1
    
    # Fondo con partículas
    window.fill(BLACK)
    
    # Actualizar y dibujar partículas de fondo
    for particle in background_particles:
        particle.update()
        particle.draw(window)
    
    # Grid retro de fondo
    grid_size = 50
    for x in range(0, WIDTH, grid_size):
        alpha = int(30 + 20 * math.sin(menu_time / 100))
        pygame.draw.line(window, (*NEON_CYAN, alpha), (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, grid_size):
        alpha = int(30 + 20 * math.sin(menu_time / 100))
        pygame.draw.line(window, (*NEON_CYAN, alpha), (0, y), (WIDTH, y), 1)
    
    # Título principal con efecto glitch
    font_title = pygame.font.SysFont(None, 80)
    draw_glitch_text(window, "RETRO FRUIT NINJA", (WIDTH // 2, HEIGHT // 4), font_title, NEON_PINK)
    
    # Subtítulo pulsante
    font_sub = pygame.font.SysFont(None, 30)
    draw_pulsing_text(window, "⚡ NEON EDITION ⚡", (WIDTH // 2, HEIGHT // 4 + 60), 30, NEON_YELLOW, menu_time)
    
    # Opciones del menú
    font_option = pygame.font.SysFont(None, 50)
    
    # Opción 1 jugador
    option1_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 50, 400, 60)
    draw_retro_border(window, option1_rect, NEON_GREEN)
    draw_pulsing_text(window, "1 JUGADOR - Presiona 1", (WIDTH // 2, HEIGHT // 2 - 20), 40, NEON_GREEN, menu_time)
    
    # Opción 2 jugadores
    option2_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 + 50, 400, 60)
    draw_retro_border(window, option2_rect, NEON_ORANGE)
    draw_pulsing_text(window, "2 JUGADORES - Presiona 2", (WIDTH // 2, HEIGHT // 2 + 80), 40, NEON_ORANGE, menu_time)
    
    # Efectos de partículas alrededor del menú
    if random.random() < 0.1:
        particles.append(Particle(
            random.randint(0, WIDTH),
            random.randint(0, HEIGHT),
            random.choice([NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_PURPLE]),
            random.randint(2, 5)
        ))

# === BUCLE PRINCIPAL ===

sword_positions = {1: [], 2: []}  # Para el trail de la espada
screen_shake = None

while True:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            cap.release()
            cv2.destroyAllWindows()
            pygame.quit()
            sys.exit()

        if game_state == "MENU":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    reset_game(1)
                elif event.key == pygame.K_2:
                    reset_game(2)
        
        elif game_state == "GAME_OVER":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game_state = "MENU"
                    menu_time = 0
                if event.key == pygame.K_ESCAPE:
                    cap.release()
                    cv2.destroyAllWindows()
                    pygame.quit()
                    sys.exit()

    if game_state == "MENU":
        draw_retro_menu()
        
        # Actualizar partículas del menú
        for particle in particles[:]:
            particle.update()
            if particle.life <= 0:
                particles.remove(particle)
            else:
                particle.draw(window)
        
        pygame.display.flip()
        clock.tick(60)
        continue

    # === LÓGICA DE CÁMARA Y DETECCIÓN ===
    ret, frame = cap.read()
    if not ret:
        print("Error: No se pudo leer la cámara.")
        break

    frame_flipped = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame_flipped, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    # Aplicar shake de pantalla si existe
    shake_offset = (0, 0)
    if screen_shake:
        if not screen_shake.update():
            screen_shake = None
        else:
            shake_offset = screen_shake.get_offset()

    camera_surface = cv2_to_pygame(frame)
    window.blit(camera_surface, shake_offset)

    # Overlay oscuro con estilo retro
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 50, 150))  # Azul oscuro semi-transparente
    window.blit(overlay, (0, 0))
    
    # Actualizar partículas de fondo
    for particle in background_particles:
        particle.update()
        particle.draw(window)

    # Línea divisoria neón en modo 2 jugadores
    if num_players == 2:
        for i in range(5):
            alpha = int(255 - i * 40)
            color = (*NEON_CYAN, alpha)
            temp_surf = pygame.Surface((5, HEIGHT), pygame.SRCALPHA)
            temp_surf.fill(color)
            window.blit(temp_surf, (WIDTH // 2 - 2 + i, 0))

    sword_data = {}
    
    # === DETECCIÓN DE MANOS ===
    if results.multi_hand_landmarks:
        for i, handLms in enumerate(results.multi_hand_landmarks):
            palm_center = handLms.landmark[9]
            norm_x = palm_center.x
            player_id = 0
            
            if num_players == 1:
                player_id = 1
            elif num_players == 2:
                if norm_x < 0.5:
                    player_id = 1
                elif norm_x >= 0.5:
                    player_id = 2

            if player_id in player_states and player_states[player_id]["alive"]:
                wrist = handLms.landmark[0]
                cx = int(palm_center.x * WIDTH)
                cy = int(palm_center.y * HEIGHT)
                dx = palm_center.x - wrist.x
                dy = palm_center.y - wrist.y

                sword_angle = math.degrees(math.atan2(dy, dx)) - 90
                
                sword_data[player_id] = {
                    "pos": (cx, cy),
                    "angle": sword_angle
                }
                
                # Agregar posición al trail
                sword_positions[player_id].append((cx, cy))
                if len(sword_positions[player_id]) > 10:
                    sword_positions[player_id].pop(0)

    # === ESTADO STARTING ===
    if game_state == "STARTING":
        elapsed_calib_time = current_time - calibration_start_time
        remaining_calib_seconds = math.ceil((CALIBRATION_TIME_MS - elapsed_calib_time) / 1000)

        if elapsed_calib_time >= CALIBRATION_TIME_MS:
            game_state = "PLAYING"
            start_time = pygame.time.get_ticks()
        
        # Mensaje de calibración con efectos
        font_calib = pygame.font.SysFont(None, 60)
        
        draw_pulsing_text(window, "PREPARANDO CÁMARA...", (WIDTH // 2, HEIGHT // 2 - 50), 60, NEON_YELLOW, current_time)
        draw_pulsing_text(window, f"INICIANDO EN {max(0, remaining_calib_seconds)}", (WIDTH // 2, HEIGHT // 2 + 50), 60, NEON_CYAN, current_time)
        
        # Dibujar espadas durante calibración
        for player_id in sword_data.keys():
            sword = sword_data[player_id]
            color = NEON_CYAN if player_id == 1 else NEON_PINK
            draw_neon_sword(window, sword["pos"], sword["angle"], color=color, player_id=player_id)

    # === ESTADO PLAYING ===
    elif game_state == "PLAYING":
        elapsed_time_ms = pygame.time.get_ticks() - start_time
        remaining_time_ms = max(0, GAME_DURATION - elapsed_time_ms)
        
        # Lógica de fin de partida
        if remaining_time_ms == 0:
            game_state = "GAME_OVER"
        
        if num_players == 2:
            all_dead = all(not state["alive"] for state in player_states.values())
            if all_dead:
                game_state = "GAME_OVER"
        else:
            if not player_states[1]["alive"]:
                game_state = "GAME_OVER"
        
        # === SPAWN DE OBJETOS ===
        current_level = elapsed_time_ms // LEVEL_UP_TIME
        spawn_frame_interval = 12
        
        frame_count += 1
        if frame_count >= spawn_frame_interval:
            if num_players == 1:
                if player_states[1]["alive"]:
                    objects.append(spawn_object(current_level))
            else:
                zone_to_spawn = random.choice([1, 2])
                if player_states[zone_to_spawn]["alive"]:
                    objects.append(spawn_object(current_level, player_zone=zone_to_spawn))
            frame_count = 0

        # === ANIMACIÓN DE OBJETOS ===
        for obj in objects:
            obj["rect"].y += obj["speed"]
            obj["rotation"] += obj.get("spin_speed", 0)
            
            if obj["kind"] == "bomb":
                obj["pulse_time"] += 1

        # === DETECCIÓN DE COLISIONES ===
        for obj in objects[:]:
            # Si el objeto sale de la pantalla, se elimina
            if obj["rect"].y > HEIGHT:
                # Pérdida de vida si es fruta y se va
                if obj["kind"] == "fruit" and num_players == 1 and player_states[1]["alive"]:
                    # En este modo, no hay vidas explícitas, el juego solo termina por bomba o tiempo.
                    # Podrías implementar un sistema de 'fallos' si lo deseas.
                    pass
                objects.remove(obj)
                continue

            collided = False
            for player_id, sword in sword_data.items():
                if player_states[player_id]["alive"]:
                    sword_pos = sword["pos"]
                    # Ajustar el hitbox de la espada para que coincida con el dedo/mano
                    sword_hitbox = pygame.Rect(sword_pos[0] - 25, sword_pos[1] - 25, 50, 50)
                    
                    if obj["rect"].colliderect(sword_hitbox):
                        if obj["kind"] == "fruit":
                            # Sistema de combos
                            time_diff = current_time - player_states[player_id]["last_hit_time"]
                            if time_diff < 1500:  # 1.5 segundos para mantener combo
                                player_states[player_id]["combo"] += 1
                            else:
                                player_states[player_id]["combo"] = 1
                            
                            player_states[player_id]["last_hit_time"] = current_time
                            
                            # Puntuación con multiplicador de combo
                            combo_multiplier = min(player_states[player_id]["combo"], 10)
                            score_gain = combo_multiplier
                            player_states[player_id]["score"] += score_gain
                            
                            # Efectos visuales
                            create_explosion_particles(obj["rect"].centerx, obj["rect"].centery, obj["color"], 20)
                            screen_shake = ScreenShake(5, 10)
                            
                            # Texto de combo
                            if player_states[player_id]["combo"] > 1:
                                combo_texts.append(ComboText(obj["rect"].centerx, obj["rect"].centery, player_states[player_id]["combo"]))
                            
                            # Trail de espada más intenso
                            if len(sword_positions[player_id]) > 1:
                                trail_color = NEON_CYAN if player_id == 1 else NEON_PINK
                                sword_trails.append(SwordTrail(sword_positions[player_id], trail_color))
                        else:
                            # Explosión de bomba
                            create_explosion_particles(obj["rect"].centerx, obj["rect"].centery, (255, 0, 0), 30)
                            player_states[player_id]["alive"] = False
                            player_states[player_id]["death_time"] = current_time
                            player_states[player_id]["combo"] = 0
                            screen_shake = ScreenShake(15, 30)
                            
                        objects.remove(obj)
                        collided = True
                        break
            
            if collided:
                continue

        # === ACTUALIZAR EFECTOS ===
        
        # Actualizar partículas
        for particle in particles[:]:
            particle.update()
            if particle.life <= 0:
                particles.remove(particle)
        
        # Actualizar trails de espada
        for trail in sword_trails[:]:
            trail.update()
            if trail.alpha <= 0:
                sword_trails.remove(trail)
        
        # Actualizar textos de combo
        for combo_text in combo_texts[:]:
            if not combo_text.update():
                combo_texts.remove(combo_text)
        
        # === DIBUJAR OBJETOS ===
        blink_on = (current_time // 200) % 2 == 0
        
        for obj in objects:
            if obj["kind"] == "fruit":
                # Rotar fruta (imagen que ya incluye el glow)
                rotated_image = pygame.transform.rotate(obj["image"], obj["rotation"])
                new_rect = rotated_image.get_rect(center=obj["rect"].center)
                
                # Efecto de brillo pulsante
                # El tamaño del glow es ahora relativo al tamaño escalado de la imagen (40x40 + 20 de glow = 60x60)
                pulse = math.sin(current_time / 300) * 5 + 10 # Ajustar el pulso para el nuevo tamaño
                glow_surf = pygame.Surface((new_rect.width + pulse, new_rect.height + pulse), pygame.SRCALPHA)
                glow_color = (*obj["color"], 100)
                
                # Dibujar el glow como una elipse ligeramente más grande que la fruta
                pygame.draw.ellipse(glow_surf, glow_color, glow_surf.get_rect())
                
                glow_rect = glow_surf.get_rect(center=obj["rect"].center)
                window.blit(glow_surf, glow_rect)
                window.blit(rotated_image, new_rect)
            else:
                # Bomba con efecto de pulso
                pulse_intensity = math.sin(obj["pulse_time"] / 10) * 5 + 20 # Ajustar el pulso
                bomb_rect_base = pygame.Rect(obj["rect"].centerx - 10, obj["rect"].centery - 10, 20, 20)
                bomb_rect = bomb_rect_base.inflate(pulse_intensity, pulse_intensity)
                bomb_rect.center = obj["rect"].center # Asegurar que esté centrado en la posición del objeto
                
                if blink_on:
                    # Núcleo de la bomba
                    pygame.draw.ellipse(window, (50, 0, 0), bomb_rect)
                    pygame.draw.ellipse(window, (255, 0, 0), bomb_rect, 5)
                    
                    # Efecto de brillo
                    glow_surf = pygame.Surface((bomb_rect.width + 10, bomb_rect.height + 10), pygame.SRCALPHA)
                    pygame.draw.ellipse(glow_surf, (255, 0, 0, 100), glow_surf.get_rect())
                    glow_rect = glow_surf.get_rect(center=bomb_rect.center)
                    window.blit(glow_surf, glow_rect)
                    
                    # Chispas alrededor de la bomba
                    for i in range(5):
                        spark_angle = (current_time / 50 + i * 72) % 360
                        # Usar el ancho/alto del rectángulo de la bomba para la posición de las chispas
                        spark_x = bomb_rect.centerx + math.cos(math.radians(spark_angle)) * (bomb_rect.width // 2 + 5)
                        spark_y = bomb_rect.centery + math.sin(math.radians(spark_angle)) * (bomb_rect.height // 2 + 5)
                        pygame.draw.circle(window, NEON_YELLOW, (int(spark_x), int(spark_y)), 3)

        # === DIBUJAR EFECTOS ===
        
        # Dibujar partículas
        for particle in particles:
            particle.draw(window)
        
        # Dibujar trails de espada
        for trail in sword_trails:
            trail.draw(window)
        
        # Dibujar textos de combo
        for combo_text in combo_texts:
            combo_text.draw(window)

        # === DIBUJAR ESPADAS Y MÁSCARAS ===
        for player_id in range(1, num_players + 1):
            
            # Máscara de muerte con efectos
            if not player_states[player_id]["alive"]:
                mask = pygame.Surface((WIDTH // num_players, HEIGHT), pygame.SRCALPHA)
                
                # Efecto de interferencia
                interference_alpha = int(150 + 50 * math.sin(current_time / 100))
                mask.fill((*BLACK, interference_alpha))
                
                x_offset = (player_id - 1) * (WIDTH // num_players)
                window.blit(mask, (x_offset, 0))
                
                # Texto de muerte glitcheado
                death_pulse = int(abs(math.sin(current_time / 200) * 20))
                font_death = pygame.font.SysFont(None, 60 + death_pulse)
                
                death_center_x = x_offset + (WIDTH // (2 * num_players))
                draw_glitch_text(window, "ELIMINADO", (death_center_x, HEIGHT // 2), font_death, (255, 0, 0))
                
                # Efectos de chispas de muerte
                if random.random() < 0.3:
                    spark_x = random.randint(x_offset, x_offset + WIDTH // num_players)
                    spark_y = random.randint(0, HEIGHT)
                    particles.append(Particle(spark_x, spark_y, (255, 0, 0), 2))

            # Dibujar espada
            if player_id in sword_data and player_states[player_id]["alive"]:
                sword = sword_data[player_id]
                color = NEON_CYAN if player_id == 1 else NEON_PINK
                draw_neon_sword(window, sword["pos"], sword["angle"], color=color, player_id=player_id)
                
                # Trail de la espada
                if len(sword_positions[player_id]) > 2:
                    trail_points = sword_positions[player_id]
                    for i in range(len(trail_points) - 1):
                        start_alpha = int(255 * (i / len(trail_points)))
                        trail_color = (*color, start_alpha)
                        
                        temp_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                        pygame.draw.line(temp_surf, trail_color, trail_points[i], trail_points[i + 1], 3)
                        window.blit(temp_surf, (0, 0))

        # === HUD CON ESTILO RETRO ===
        
        # Panel de información superior
        hud_font = pygame.font.SysFont(None, 35)
        small_font = pygame.font.SysFont(None, 25)
        
        # Fondo del HUD
        hud_bg = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 180))
        window.blit(hud_bg, (0, 0))
        
        # Líneas decorativas del HUD
        for i in range(3):
            alpha = 255 - i * 60
            pygame.draw.line(window, (*NEON_CYAN, alpha), (0, 95 - i), (WIDTH, 95 - i), 1)
        
        if num_players == 1:
            # Puntuación con efecto brillante
            score_text = f"PUNTOS: {player_states[1]['score']}"
            draw_pulsing_text(window, score_text, (120, 25), 35, NEON_YELLOW, current_time)
            
            # Combo actual
            if player_states[1]["combo"] > 1:
                combo_color = NEON_PINK if player_states[1]["combo"] >= 5 else NEON_ORANGE
                combo_text = f"COMBO x{player_states[1]['combo']}"
                draw_pulsing_text(window, combo_text, (120, 60), 25, combo_color, current_time)
        else:
            # Puntuaciones duales
            p1_score = hud_font.render(f"P1: {player_states[1]['score']}", True, NEON_CYAN)
            p2_score = hud_font.render(f"P2: {player_states[2]['score']}", True, NEON_PINK)
            window.blit(p1_score, (20, 20))
            window.blit(p2_score, (WIDTH - p2_score.get_width() - 20, 20))
            
            # Combos
            if player_states[1]["combo"] > 1:
                combo1 = small_font.render(f"Combo x{player_states[1]['combo']}", True, NEON_CYAN)
                window.blit(combo1, (20, 50))
            if player_states[2]["combo"] > 1:
                combo2 = small_font.render(f"Combo x{player_states[2]['combo']}", True, NEON_PINK)
                window.blit(combo2, (WIDTH - combo2.get_width() - 20, 50))
        
        # Nivel con efecto de brillo
        level_text = f"NIVEL {current_level + 1}"
        draw_pulsing_text(window, level_text, (WIDTH // 2 - 100, 70), 30, NEON_GREEN, current_time)
        
        # Timer con efectos dramáticos
        remaining_seconds = remaining_time_ms // 1000
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        time_text = f"{minutes:02d}:{seconds:02d}"
        
        timer_color = (255, 0, 0) if remaining_seconds <= 10 else NEON_GREEN
        
        if remaining_seconds <= 10:
            # Efecto de urgencia
            draw_glitch_text(window, time_text, (WIDTH // 2, 25), hud_font, timer_color)
            
            # Partículas de alerta
            if random.random() < 0.5:
                particles.append(Particle(
                    WIDTH // 2 + random.randint(-50, 50),
                    25 + random.randint(-20, 20),
                    (255, 0, 0),
                    3
                ))
        else:
            draw_pulsing_text(window, time_text, (WIDTH // 2, 25), 35, timer_color, current_time)

    # === ESTADO GAME OVER ===
    elif game_state == "GAME_OVER":
        # Overlay con efectos
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        window.blit(overlay, (0, 0))
        
        # Efectos de fondo
        for particle in background_particles:
            particle.update()
            particle.draw(window)

        font = pygame.font.SysFont(None, 70)
        font2 = pygame.font.SysFont(None, 35)
        reason_font = pygame.font.SysFont(None, 40)
        
        p1_score = player_states[1]["score"]
        p2_score = player_states[2]["score"]
        
        if num_players == 1:
            # Game Over para 1 jugador
            draw_glitch_text(window, "💥 GAME OVER 💥", (WIDTH // 2, HEIGHT // 2 - 70), font, (255, 0, 0))
            
            score_text = f"PUNTUACIÓN FINAL: {p1_score}"
            draw_pulsing_text(window, score_text, (WIDTH // 2, HEIGHT // 2 + 30), 35, NEON_YELLOW, current_time)
            
            if not player_states[1]["alive"]:
                reason_text = "¡BOMBA CORTADA!"
                reason_color = (255, 0, 0)
            else:
                reason_text = "¡TIEMPO AGOTADO!"
                reason_color = NEON_YELLOW
            
            draw_pulsing_text(window, reason_text, (WIDTH // 2, HEIGHT // 2 - 20), 40, reason_color, current_time)
            
        else:
            # Game Over para 2 jugadores
            if p1_score == p2_score:
                winner_text = "¡EMPATE!"
                winner_color = NEON_YELLOW
                diff_text = f"P1: {p1_score} - P2: {p2_score}"
            else:
                winner_id = 1 if p1_score > p2_score else 2
                winner_color = NEON_CYAN if winner_id == 1 else NEON_PINK
                winner_text = f"¡GANADOR: JUGADOR {winner_id}!"
                difference = abs(p1_score - p2_score)
                diff_text = f"Por {difference} puntos (P1: {p1_score} vs P2: {p2_score})"
            
            draw_glitch_text(window, winner_text, (WIDTH // 2, HEIGHT // 2 - 70), font, winner_color)
            draw_pulsing_text(window, diff_text, (WIDTH // 2, HEIGHT // 2 + 30), 30, NEON_YELLOW, current_time)
            
            if remaining_time_ms <= 0:
                reason_text = "FIN POR TIEMPO AGOTADO"
                reason_color = NEON_GREEN
            else:
                reason_text = "AMBOS JUGADORES ELIMINADOS"
                reason_color = (255, 0, 0)
            
            draw_pulsing_text(window, reason_text, (WIDTH // 2, HEIGHT // 2 - 20), 30, reason_color, current_time)

        # Instrucciones con borde retro
        restart_rect = pygame.Rect(WIDTH // 2 - 300, HEIGHT // 2 + 80, 600, 50)
        draw_retro_border(window, restart_rect, NEON_CYAN)
        draw_pulsing_text(window, "ESPACIO: Menú | ESC: Salir", (WIDTH // 2, HEIGHT // 2 + 105), 25, NEON_CYAN, current_time)
        
        # Efectos de partículas finales
        if random.random() < 0.2:
            particles.append(Particle(
                random.randint(0, WIDTH),
                random.randint(0, HEIGHT),
                random.choice([NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_PURPLE]),
                random.randint(1, 4)
            ))
    
    # Actualizar y dibujar todas las partículas restantes
    for particle in particles[:]:
        particle.update()
        if particle.life <= 0:
            particles.remove(particle)
        else:
            particle.draw(window)

    pygame.display.flip()
    clock.tick(60)

# Limpieza final
cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()