import cv2
import mediapipe as mp
import random
import time
import math
import numpy as np

# ---------------- Config ----------------
WIDTH, HEIGHT = 1280, 720
CAP_INDEX = 0

# Block types probabilities: 'normal' (70%), 'gold' (15%), 'blue' (15%)
BLOCK_TYPES = (['normal'] * 70 + ['gold'] * 15 + ['blue'] * 15)

# Timings mejorados
WARNING_SECONDS = 1.0
ACTIVE_LIFETIME = 1.2
SPAWN_INTERVAL_BASE_MIN = 2.0
SPAWN_INTERVAL_BASE_MAX = 3.5
ROUND_DURATION = 180  # 3 minutos por ronda

# Gold multiplier duration
GOLD_DURATION = 5.0

# ---------------- Setup ----------------
cap = cv2.VideoCapture(CAP_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Two pose detectors for 2-player mode
pose_left = mp_pose.Pose()
pose_right = mp_pose.Pose()

# CAMBIADO: Ventana normal en lugar de WINDOW_NORMAL que causa problemas
cv2.namedWindow("Esquivar Bloques", cv2.WINDOW_AUTOSIZE)

# Colores mejorados
COLORS = {
    'bg_primary': (139, 69, 19),
    'bg_secondary': (160, 82, 45),
    'text_primary': (255, 255, 255),
    'text_secondary': (255, 215, 0),
    'accent': (255, 140, 0),
    'success': (0, 255, 0),
    'danger': (0, 0, 255),
    'warning': (255, 255, 0),
}

# ---------------- Alert System ----------------
class Alert:
    def __init__(self, text, x, y, color, duration=2.0):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.start_time = time.time()
        self.duration = duration
        self.initial_y = y
        
    def update_and_draw(self, frame):
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            return False
        
        progress = elapsed / self.duration
        alpha = 1.0 - progress
        current_y = self.initial_y - int(progress * 60)
        scale = 1.5 - progress * 0.5
        
        if alpha > 0:
            cv2.putText(frame, self.text, (self.x+3, current_y+3), 
                       cv2.FONT_HERSHEY_DUPLEX, scale, (0,0,0), 4, cv2.LINE_AA)
            color = (int(self.color[0]*alpha), int(self.color[1]*alpha), int(self.color[2]*alpha))
            cv2.putText(frame, self.text, (self.x, current_y), 
                       cv2.FONT_HERSHEY_DUPLEX, scale, color, 3, cv2.LINE_AA)
        
        return True

class Block:
    def __init__(self, x, y, w, h, btype):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.type = btype
        self.spawn = time.time()
        self.state = "warning"
        self.active_since = None
        self.touched_by = set()

    def draw(self, frame):
        elapsed = time.time() - self.spawn
        if self.state == "warning":
            if elapsed >= WARNING_SECONDS:
                self.state = "active"
                self.active_since = time.time()
            else:
                # Efecto de pulso para advertencia
                pulse = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(elapsed * 10))
                overlay = frame.copy()
                
                # Borde brillante
                cv2.rectangle(frame, (self.x-5, self.y-5),
                            (self.x + self.w + 5, self.y + self.h + 5), 
                            (255, 255, 255), 3)
                
                color = (0, 100, 255)
                cv2.rectangle(overlay, (self.x, self.y),
                            (self.x + self.w, self.y + self.h), color, -1)
                cv2.addWeighted(overlay, pulse, frame, 1 - pulse, 0, frame)
                
        elif self.state == "active":
            # RESTAURADO: Sombra para profundidad
            cv2.rectangle(frame, (self.x+5, self.y+5),
                        (self.x + self.w + 5, self.y + self.h + 5), 
                        (0, 0, 0), -1)
            
            if self.type == "normal":
                # Bloque rojo con gradiente
                cv2.rectangle(frame, (self.x, self.y),
                            (self.x + self.w, self.y + self.h), (0, 0, 200), -1)
                cv2.rectangle(frame, (self.x+10, self.y+10),
                            (self.x + self.w-10, self.y + self.h-10), (0, 0, 255), -1)
                # Borde para definición
                cv2.rectangle(frame, (self.x, self.y),
                            (self.x + self.w, self.y + self.h), (255, 255, 255), 2)
                
            elif self.type == "gold":
                # Bloque dorado con brillo
                cv2.rectangle(frame, (self.x, self.y),
                            (self.x + self.w, self.y + self.h), (0, 165, 255), -1)
                cv2.rectangle(frame, (self.x+10, self.y+10),
                            (self.x + self.w-10, self.y + self.h-10), (0, 215, 255), -1)
                
                # Efecto de brillo animado
                shine = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(time.time() * 3))
                overlay = frame.copy()
                cv2.rectangle(overlay, (self.x, self.y),
                            (self.x + self.w, self.y + self.h), (255, 255, 255), -1)
                cv2.addWeighted(overlay, shine * 0.3, frame, 1 - shine * 0.3, 0, frame)
                
                # Borde brillante
                cv2.rectangle(frame, (self.x, self.y),
                            (self.x + self.w, self.y + self.h), (255, 255, 255), 3)
                
            elif self.type == "blue":
                # Bloque azul con efecto
                cv2.rectangle(frame, (self.x, self.y),
                            (self.x + self.w, self.y + self.h), (255, 100, 0), -1)
                cv2.rectangle(frame, (self.x+10, self.y+10),
                            (self.x + self.w-10, self.y + self.h-10), (255, 150, 0), -1)
                # Borde para definición
                cv2.rectangle(frame, (self.x, self.y),
                            (self.x + self.w, self.y + self.h), (255, 255, 255), 2)

    def expired(self):
        if self.state == "active":
            return (time.time() - self.active_since) >= ACTIVE_LIFETIME
        return False

    def check_collision_with_landmarks(self, landmarks, full_width, full_height):
        if self.state != "active":
            return False
        for (lx, ly) in landmarks:
            if self.x <= lx <= self.x + self.w and self.y <= ly <= self.y + self.h:
                return True
        return False

# ---------------- Utilities draw ----------------
def draw_fancy_text(frame, text, pos, scale=1.0, color=(255,255,255), thickness=2, font_type=0):
    x, y = pos
    # Sombra
    cv2.putText(frame, text, (x+3, y+3), font_type, scale, (0,0,0), thickness+2, cv2.LINE_AA)
    # Borde
    cv2.putText(frame, text, (x-1, y-1), font_type, scale, (255,255,255), thickness+1, cv2.LINE_AA)
    cv2.putText(frame, text, (x+1, y+1), font_type, scale, (255,255,255), thickness+1, cv2.LINE_AA)
    # Texto principal
    cv2.putText(frame, text, (x, y), font_type, scale, color, thickness, cv2.LINE_AA)

def draw_background(frame):
    # Fondo de otoño inspirado
    # Gradiente de cielo
    for i in range(HEIGHT//3):
        color_ratio = i / (HEIGHT//3)
        b = int(200 * (1 - color_ratio) + 139 * color_ratio)
        g = int(230 * (1 - color_ratio) + 160 * color_ratio)
        r = int(255 * (1 - color_ratio) + 200 * color_ratio)
        cv2.line(frame, (0, i), (WIDTH, i), (b, g, r), 1)
    
    # Suelo
    cv2.rectangle(frame, (0, HEIGHT//3), (WIDTH, HEIGHT), (101, 67, 33), -1)
    
    # Elementos decorativos (árboles simples)
    tree_positions = [150, 400, 650, 900, 1150]
    for pos in tree_positions:
        # Tronco
        cv2.rectangle(frame, (pos-15, HEIGHT//3-100), (pos+15, HEIGHT//3), (101, 67, 33), -1)
        # Copa
        cv2.circle(frame, (pos, HEIGHT//3-120), 40, (255, 140, 0), -1)
        cv2.circle(frame, (pos-20, HEIGHT//3-110), 25, (255, 165, 0), -1)
        cv2.circle(frame, (pos+20, HEIGHT//3-110), 25, (255, 165, 0), -1)

def draw_score_panel(frame, score_p1, score_p2, mode, gold_end_p1, gold_end_p2, time_left):
    # Panel superior decorativo
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (WIDTH, 80), (139, 69, 19), -1)
    cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
    
    # Borde decorativo
    cv2.rectangle(frame, (0, 0), (WIDTH, 80), (255, 215, 0), 3)
    cv2.line(frame, (0, 76), (WIDTH, 76), (255, 140, 0), 4)
    
    # Tiempo restante (centro)
    minutes = int(time_left // 60)
    seconds = int(time_left % 60)
    time_text = f"{minutes:02d}:{seconds:02d}"
    draw_fancy_text(frame, time_text, (WIDTH//2 - 60, 45), 1.5, COLORS['text_secondary'], 3, cv2.FONT_HERSHEY_DUPLEX)
    
    # Score P1
    draw_fancy_text(frame, f"P1: {score_p1}", (30, 45), 1.2, COLORS['success'], 2, cv2.FONT_HERSHEY_DUPLEX)
    
    if mode == 2:
        # Score P2
        draw_fancy_text(frame, f"P2: {score_p2}", (WIDTH-150, 45), 1.2, COLORS['success'], 2, cv2.FONT_HERSHEY_DUPLEX)
    
    # Estados dorados
    if time.time() < gold_end_p1:
        rem = int(gold_end_p1 - time.time())
        draw_fancy_text(frame, f"2X: {rem}s", (200, 45), 0.8, (0, 215, 255), 2, cv2.FONT_HERSHEY_DUPLEX)
    
    if mode == 2 and time.time() < gold_end_p2:
        rem = int(gold_end_p2 - time.time())
        draw_fancy_text(frame, f"2X: {rem}s", (WIDTH-280, 45), 0.8, (0, 215, 255), 2, cv2.FONT_HERSHEY_DUPLEX)

def get_landmarks_in_full_coords(results, crop_offset_x, crop_width, full_width, full_height):
    pts = []
    if not results or not results.pose_landmarks:
        return pts
    h = full_height
    w = crop_width
    for lm in results.pose_landmarks.landmark:
        px = int(lm.x * w) + crop_offset_x
        py = int(lm.y * h)
        pts.append((px, py))
    return pts

def countdown():
    """Contador de 3-2-1 antes de comenzar con cámara visible"""
    for count in [3, 2, 1]:
        start_time = time.time()
        while time.time() - start_time < 1.0:
            ret, frame = cap.read()
            if not ret:
                return False
            frame = cv2.flip(frame, 1)
            
            # Mostrar la cámara de fondo (sin efectos decorativos para ver mejor)
            # No usar draw_background() aquí para que se vea la cámara real
            
            # Efecto de zoom para el número
            progress = (time.time() - start_time)
            scale = 6.0 - 4.0 * progress
            alpha = 1.0 - progress
            
            # Número grande en el centro con fondo semi-transparente
            text = str(count)
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, scale, int(scale*2))[0]
            x = WIDTH // 2 - text_size[0] // 2
            y = HEIGHT // 2 + text_size[1] // 2
            
            # Círculo de fondo para el número
            # Círculo de fondo para el número
            radius = max(0, int(150 * alpha))
            if radius > 0:
                cv2.circle(frame, (WIDTH//2, HEIGHT//2), radius, (0, 0, 0), -1)
                cv2.circle(frame, (WIDTH//2, HEIGHT//2), radius, (255, 215, 0), 5)

            
            # Texto del contador
            draw_fancy_text(frame, text, (x, y), scale, (255, 215, 0), int(scale*2), cv2.FONT_HERSHEY_DUPLEX)
            
            cv2.imshow("Esquivar Bloques", frame)
            cv2.setWindowProperty("Esquivar Bloques", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            if cv2.waitKey(30) == 27:  # ESC para salir
                return False
    return True

# ---------------- Menu Inicial ----------------
def menu():
    sel = 1
    while True:
        ret, frame = cap.read()
        if not ret:
            return 0
        frame = cv2.flip(frame, 1)
        
        # Fondo animado
        draw_background(frame)
        
        # Título con efecto
        title_y = 150
        draw_fancy_text(frame, "ESQUIVAR", (WIDTH//2-200, title_y), 3.0, COLORS['text_secondary'], 4, cv2.FONT_HERSHEY_DUPLEX)
        draw_fancy_text(frame, "BLOQUES", (WIDTH//2-180, title_y + 80), 3.0, COLORS['accent'], 4, cv2.FONT_HERSHEY_DUPLEX)
        
        # Opciones
        color1 = COLORS['success'] if sel == 1 else COLORS['text_primary']
        color2 = COLORS['success'] if sel == 2 else COLORS['text_primary']
        
        draw_fancy_text(frame, "1 JUGADOR", (WIDTH//2 - 120, 350), 1.5, color1, 3, cv2.FONT_HERSHEY_DUPLEX)
        draw_fancy_text(frame, "2 JUGADORES", (WIDTH//2 - 140, 420), 1.5, color2, 3, cv2.FONT_HERSHEY_DUPLEX)
        
        # Instrucciones
        draw_fancy_text(frame, "Evita los bloques ROJOS - Toca los DORADOS para puntos x2", (WIDTH//2 - 350, 520), 0.8, COLORS['text_primary'], 2)
        draw_fancy_text(frame, "Toca los AZULES para robar puntos del oponente", (WIDTH//2 - 280, 550), 0.8, COLORS['text_primary'], 2)
        draw_fancy_text(frame, "ESC - Salir", (50, HEIGHT-50), 1.0, COLORS['text_secondary'], 2)
        
        cv2.imshow("Esquivar Bloques", frame)
        cv2.setWindowProperty("Esquivar Bloques", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        k = cv2.waitKey(30) & 0xFF
        if k == ord('1'):
            return 1
        if k == ord('2'):
            return 2
        if k == 27:
            return 0

# ---------------- Game Loop ----------------
def game_loop(mode):
    blocks = []
    last_spawn = time.time()
    spawn_interval = SPAWN_INTERVAL_BASE_MAX
    score_p1 = 0
    score_p2 = 0
    gold_end_p1 = 0.0
    gold_end_p2 = 0.0
    game_over = False
    loser = None
    
    # Contador inicial con cámara visible
    if not countdown():
        return False
    
    # Inicio de la ronda
    round_start = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        
        # NO usar draw_background() aquí - queremos ver la cámara real
        # Solo agregamos una overlay sutil para el HUD si es necesario
        
        # Tiempo restante
        elapsed = time.time() - round_start
        time_left = max(0, ROUND_DURATION - elapsed)
        
        # Dificultad progresiva
        difficulty_factor = elapsed / ROUND_DURATION
        spawn_interval_min = max(0.5, SPAWN_INTERVAL_BASE_MIN - difficulty_factor * 1.0)
        spawn_interval_max = max(1.0, SPAWN_INTERVAL_BASE_MAX - difficulty_factor * 2.0)
        
        # Fin de ronda por tiempo
        if time_left <= 0 and not game_over:
            game_over = True
            loser = "time_up"
        
        # Detección de pose (sin divisor visual)
        if mode == 2:
            left_crop = frame[:, :WIDTH//2].copy()
            right_crop = frame[:, WIDTH//2:].copy()
            rgb_left = cv2.cvtColor(left_crop, cv2.COLOR_BGR2RGB)
            rgb_right = cv2.cvtColor(right_crop, cv2.COLOR_BGR2RGB)

            res_left = pose_left.process(rgb_left)
            res_right = pose_right.process(rgb_right)

            lm_p1 = get_landmarks_in_full_coords(res_left, 0, WIDTH//2, WIDTH, HEIGHT)
            lm_p2 = get_landmarks_in_full_coords(res_right, WIDTH//2, WIDTH//2, WIDTH, HEIGHT)
            
            # Dibujar landmarks directamente en el frame original
            if res_left.pose_landmarks:
                # Convertir landmarks para dibujar en frame completo
                for connection in mp_pose.POSE_CONNECTIONS:
                    start_idx, end_idx = connection
                    start_lm = res_left.pose_landmarks.landmark[start_idx]
                    end_lm = res_left.pose_landmarks.landmark[end_idx]
                    
                    start_x = int(start_lm.x * (WIDTH//2))
                    start_y = int(start_lm.y * HEIGHT)
                    end_x = int(end_lm.x * (WIDTH//2))
                    end_y = int(end_lm.y * HEIGHT)
                    
                    cv2.line(frame, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
                    
            if res_right.pose_landmarks:
                for connection in mp_pose.POSE_CONNECTIONS:
                    start_idx, end_idx = connection
                    start_lm = res_right.pose_landmarks.landmark[start_idx]
                    end_lm = res_right.pose_landmarks.landmark[end_idx]
                    
                    start_x = int(start_lm.x * (WIDTH//2)) + WIDTH//2
                    start_y = int(start_lm.y * HEIGHT)
                    end_x = int(end_lm.x * (WIDTH//2)) + WIDTH//2
                    end_y = int(end_lm.y * HEIGHT)
                    
                    cv2.line(frame, (start_x, start_y), (end_x, end_y), (0, 255, 255), 2)
                    
        else:
            # Un jugador - usar frame completo
            rgb_full = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res_full = pose_left.process(rgb_full)
            lm_p1 = get_landmarks_in_full_coords(res_full, 0, WIDTH, WIDTH, HEIGHT)
            lm_p2 = []
            
            # Dibujar landmarks
            if res_full.pose_landmarks:
                mp_drawing.draw_landmarks(frame, res_full.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Spawn de bloques con dificultad progresiva
        if not game_over and (time.time() - last_spawn) > spawn_interval:
            # Ahora spawnea entre 2 y 5 bloques desde el inicio
            spawn_count = random.randint(2, 5)
            
            for _ in range(spawn_count):
                bw, bh = 100, 100
                bx = random.randint(40, WIDTH - bw - 40)
                by = random.randint(100, HEIGHT - bh - 100)
                btype = random.choice(BLOCK_TYPES)
                blocks.append(Block(bx, by, bw, bh, btype))
            
            last_spawn = time.time()
            spawn_interval = random.uniform(spawn_interval_min, spawn_interval_max)

        # Update blocks - DIBUJAR LOS BLOQUES SOBRE LA CÁMARA
        for b in blocks[:]:
            b.draw(frame)

            touched_p1 = b.check_collision_with_landmarks(lm_p1, WIDTH, HEIGHT) if lm_p1 else False
            touched_p2 = b.check_collision_with_landmarks(lm_p2, WIDTH, HEIGHT) if lm_p2 else False

            if touched_p1:
                b.touched_by.add('p1')
            if touched_p2:
                b.touched_by.add('p2')

            if b.state == "active":
                # Normal blocks kill
                if 'p1' in b.touched_by and b.type == 'normal':
                    game_over = True
                    loser = 'p1'
                if 'p2' in b.touched_by and b.type == 'normal' and not game_over:
                    game_over = True
                    loser = 'p2'

                # Gold gives multiplier
                if 'p1' in b.touched_by and b.type == 'gold':
                    gold_end_p1 = max(gold_end_p1, time.time() + GOLD_DURATION)
                    blocks.remove(b)
                    continue
                if 'p2' in b.touched_by and b.type == 'gold':
                    gold_end_p2 = max(gold_end_p2, time.time() + GOLD_DURATION)
                    blocks.remove(b)
                    continue

                # Blue steals points
                if 'p1' in b.touched_by and b.type == 'blue':
                    steal = score_p2 // 2
                    score_p1 += steal
                    score_p2 -= steal
                    blocks.remove(b)
                    continue
                if 'p2' in b.touched_by and b.type == 'blue':
                    steal = score_p1 // 2
                    score_p2 += steal
                    score_p1 -= steal
                    blocks.remove(b)
                    continue

            # Award points for avoiding
            if b.expired():
                if 'p1' not in b.touched_by and mode >= 1:
                    add = 1
                    if time.time() < gold_end_p1:
                        add *= 2
                    score_p1 += add
                if 'p2' not in b.touched_by and mode == 2:
                    add = 1
                    if time.time() < gold_end_p2:
                        add *= 2
                    score_p2 += add
                blocks.remove(b)

        # Draw HUD SOBRE LA CÁMARA
        draw_score_panel(frame, score_p1, score_p2, mode, gold_end_p1, gold_end_p2, time_left)

        # Game over screen
        if game_over:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (WIDTH, HEIGHT), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            
            if loser == "time_up":
                draw_fancy_text(frame, "TIEMPO AGOTADO!", (WIDTH//2 - 200, HEIGHT//2 - 60), 2.0, COLORS['text_secondary'], 4, cv2.FONT_HERSHEY_DUPLEX)
                winner_text = f"GANADOR: P1 ({score_p1})" if score_p1 > score_p2 else f"GANADOR: P2 ({score_p2})" if mode == 2 else f"PUNTAJE FINAL: {score_p1}"
                if mode == 2 and score_p1 == score_p2:
                    winner_text = "EMPATE!"
                draw_fancy_text(frame, winner_text, (WIDTH//2 - 150, HEIGHT//2), 1.2, COLORS['success'], 3, cv2.FONT_HERSHEY_DUPLEX)
            else:
                draw_fancy_text(frame, "GAME OVER", (WIDTH//2 - 180, HEIGHT//2 - 60), 2.2, COLORS['danger'], 4, cv2.FONT_HERSHEY_DUPLEX)
                if loser == 'p1':
                    draw_fancy_text(frame, "JUGADOR 1 TOCO UN BLOQUE ROJO", (WIDTH//2 - 300, HEIGHT//2), 1.0, (255, 200, 200), 2, cv2.FONT_HERSHEY_DUPLEX)
                elif loser == 'p2':
                    draw_fancy_text(frame, "JUGADOR 2 TOCO UN BLOQUE ROJO", (WIDTH//2 - 300, HEIGHT//2), 1.0, (255, 200, 200), 2, cv2.FONT_HERSHEY_DUPLEX)
            
            draw_fancy_text(frame, "SPACE - REINICIAR    ESC - MENU", (WIDTH//2 - 250, HEIGHT//2 + 100), 1.0, COLORS['text_primary'], 2, cv2.FONT_HERSHEY_DUPLEX)

        cv2.imshow("Esquivar Bloques", frame)
        cv2.setWindowProperty("Esquivar Bloques", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        k = cv2.waitKey(20) & 0xFF
        if k == 27:
            return False
        if game_over and k == 32:
            return True

    return False

# ---------------- Main ----------------
if __name__ == "__main__":
    while True:
        mode = menu()
        if mode == 0:
            break
        restart = game_loop(mode)
        if not restart:
            break

    cap.release()
    cv2.destroyAllWindows()