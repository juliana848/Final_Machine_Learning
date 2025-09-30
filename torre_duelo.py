import cv2
import mediapipe as mp
import time

# --- Configuración cámara ---
WIDTH, HEIGHT = 1280, 720

# --- Mediapipe Pose ---
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

jump_threshold = 60
GAME_TIME = 180  # 3 minutos

def detect_jump(y, player):
    jump = False
    if player["last_y"] is not None and player["cooldown"] == 0:
        if player["last_y"] - y > jump_threshold:
            jump = True
            player["cooldown"] = 15
    player["last_y"] = y
    if player["cooldown"] > 0:
        player["cooldown"] -= 1
    return jump

def process_jump(player):
    bx = int(player["block"]["x"])
    by = int(player["block"]["y"])
    bw = int(player["block"]["w"])
    bh = int(player["block"]["h"])

    if player["tower"]:
        last_x, last_y, last_w, last_h = player["tower"][-1]
        overlap_start = max(bx, last_x)
        overlap_end = min(bx+bw, last_x+last_w)
        overlap = overlap_end - overlap_start
        if overlap > 0:
            bx = overlap_start
            bw = overlap
            by = last_y - bh
            player["tower"].append((bx, by, bw, bh))
            player["score"] += 1
        else:
            player["alive"] = False
    else:
        player["tower"].append((bx, by, bw, bh))
        player["score"] += 1

    player["block"] = {
        "x": int(player["side"][0] + 20),
        "y": int(HEIGHT - 100),
        "w": max(20, bw),
        "h": 40,
        "dir": 1
    }

def show_countdown(cap):
    # Contador 3..2..1..YA!
    for i in ["3", "2", "1", "¡YA!"]:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        cv2.putText(frame, i, (WIDTH//2-100, HEIGHT//2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 5, (0,0,255), 10)
        cv2.imshow("Stack Jump 2P", frame)
        cv2.waitKey(1000)  # 1 segundo
    cv2.waitKey(500)

def run_game():
    cap = cv2.VideoCapture(0)
    cap.set(3, WIDTH)
    cap.set(4, HEIGHT)

    cv2.namedWindow("Stack Jump 2P", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Stack Jump 2P", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    players = [
        {"tower": [], "block": {"x": 0, "y": HEIGHT-100, "w": 200, "h": 40, "dir": 1},
         "speed": 10, "score": 0, "last_y": None, "cooldown": 0, "alive": True, "side": (0, WIDTH//2)},
        {"tower": [], "block": {"x": WIDTH//2, "y": HEIGHT-100, "w": 200, "h": 40, "dir": 1},
         "speed": 10, "score": 0, "last_y": None, "cooldown": 0, "alive": True, "side": (WIDTH//2, WIDTH)}
    ]

    # --- Mostrar contador antes de iniciar ---
    show_countdown(cap)

    start_time = time.time()
    winner_text = ""

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        # --- Dibujar línea central ---
        cv2.line(frame, (WIDTH//2, 0), (WIDTH//2, HEIGHT), (255, 255, 255), 2)

        # --- Temporizador ---
        elapsed = time.time() - start_time
        remaining = max(0, GAME_TIME - int(elapsed))
        minutes, seconds = divmod(remaining, 60)

        # --- Subir dificultad cada 30s ---
        for p in players:
            p["speed"] = 10 + int(elapsed // 30) * 2

        # --- Detectar jugadores ---
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            landmarks = results.pose_landmarks.landmark
            x_hip = int((landmarks[mp_pose.PoseLandmark.LEFT_HIP].x +
                         landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x)/2 * WIDTH)
            y_hip = int((landmarks[mp_pose.PoseLandmark.LEFT_HIP].y +
                         landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y)/2 * HEIGHT)

            if x_hip < WIDTH//2 and players[0]["alive"]:
                if detect_jump(y_hip, players[0]):
                    process_jump(players[0])
            elif x_hip >= WIDTH//2 and players[1]["alive"]:
                if detect_jump(y_hip, players[1]):
                    process_jump(players[1])

        alive_count = sum(1 for p in players if p["alive"])

        # --- Dibujar bloques ---
        for idx, p in enumerate(players):
            if not p["alive"]:
                x_text = (p["side"][0] + p["side"][1]) // 2 - 150
                cv2.putText(frame, "GAME OVER", (x_text, HEIGHT//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 5)
                continue

            p["block"]["x"] = int(p["block"]["x"] + p["speed"] * p["block"]["dir"])
            if p["block"]["x"] <= p["side"][0] or p["block"]["x"]+p["block"]["w"] >= p["side"][1]:
                p["block"]["dir"] *= -1

            for (x, y, w, h) in p["tower"]:
                cv2.rectangle(frame, (int(x), int(y)), (int(x+w), int(y+h)), (0, 255, 0), -1)

            bx, by, bw, bh = p["block"]["x"], p["block"]["y"], p["block"]["w"], p["block"]["h"]
            cv2.rectangle(frame, (int(bx), int(by)), (int(bx+bw), int(by+bh)), (255, 0, 0), -1)

            if idx == 0:
                cv2.putText(frame, f"P1: {p['score']}", (30, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 3)
            else:
                cv2.putText(frame, f"P2: {p['score']}", (WIDTH-200, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 3)

        # --- Temporizador ---
        cv2.putText(frame, f"{minutes}:{seconds:02}", (WIDTH//2-60, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,255,255), 4)

        # --- Fin del juego ---
        if remaining == 0 or alive_count == 0:
            p1, p2 = players[0]["score"], players[1]["score"]
            if p1 > p2: winner_text = "Ganador: Jugador 1 🏆"
            elif p2 > p1: winner_text = "Ganador: Jugador 2 🏆"
            else: winner_text = "Empate 🎉"

            overlay = frame.copy()
            cv2.rectangle(overlay, (200, 200), (WIDTH-200, HEIGHT-200), (0,0,0), -1)
            alpha = 0.6
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

            cv2.putText(frame, "GAME OVER", (WIDTH//2-250, HEIGHT//2-50),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 6)
            cv2.putText(frame, winner_text, (WIDTH//2-300, HEIGHT//2+50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,0), 4)
            cv2.putText(frame, "Presiona R para Repetir | Q para Salir",
                        (WIDTH//2-350, HEIGHT//2+150),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 3)

            cv2.imshow("Stack Jump 2P", frame)
            key = cv2.waitKey(0) & 0xFF
            if key == ord("r"):
                return True
            else:
                return False

        cv2.imshow("Stack Jump 2P", frame)
        if cv2.waitKey(20) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    return False

# --- Loop principal ---
while True:
    repetir = run_game()
    if not repetir:
        break
