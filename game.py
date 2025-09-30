# Clase principal del juego
import cv2
import numpy as np
import time
import math
from collections import deque

from assets import AssetsManager
from detector import HandTracker
from effects import EffectsManager
from ui import UIManager
from utils import Utils

class BasketballGamePro:
    def __init__(self):
        # Configuración cvzone HandDetector
        self.hand_tracker = HandTracker(maxHands=2, detectionCon=0.7)
        
        # Timer del juego - 3 minutos
        self.game_duration = 180
        self.start_time = time.time()
        self.game_over = False
        
        # División de pantalla
        self.split_screen = True
        self.screen_width = 1280
        self.screen_height = 720
        self.split_line_x = self.screen_width // 2
        
        # Managers
        self.assets_manager = AssetsManager()
        self.assets = self.assets_manager.load_assets()
        
        self.effects_manager = EffectsManager(self.assets_manager.colors)
        
        self.ui_manager = UIManager(self.assets_manager.colors)
        
        # Tracking para canastas
        self.ball_positions = {'left': deque(maxlen=15), 'right': deque(maxlen=15)}
        self.basket_cooldown = 1.5
        self.last_basket_time = 0
        
        # Puntajes
        self.player1_score = 0
        self.player2_score = 0
        self.combo_count = 0
        self.last_score_time = 0
        
        # Sistema de salida
        self.thumbs_up_count = 0
        self.thumbs_up_threshold = 30
        self.exit_animation_frames = 120
        self.exiting = False
        self.exit_frame_count = 0
        self.show_final_modal = False
        
        # Canastas móviles
        self.moving_baskets = False
        self.basket_move_speed = 3
        self.super_speed_activated = False
        self.left_basket_pos = [100, 80]
        self.right_basket_pos = [960, 80]
        self.basket_direction = {'left': [1, 1], 'right': [-1, 1]}
        
        # Límites ajustados para cada mitad de pantalla
        self.basket_bounds = {
            'left': {'min_x': 50, 'max_x': 590, 'min_y': 60, 'max_y': 350},
            'right': {'min_x': 690, 'max_x': 1230, 'min_y': 60, 'max_y': 350}
        }
        
        # Cámara
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def get_remaining_time(self):
        elapsed = time.time() - self.start_time
        remaining = max(0, self.game_duration - elapsed)
        return remaining

    def update_moving_baskets(self):
        if not self.moving_baskets:
            return
        
        current_speed = self.basket_move_speed
        
        # Mover canasta izquierda (dentro de su zona)
        self.left_basket_pos[0] += self.basket_direction['left'][0] * current_speed
        self.left_basket_pos[1] += self.basket_direction['left'][1] * current_speed
        
        # Rebotes para canasta izquierda (solo en su mitad)
        if self.left_basket_pos[0] <= self.basket_bounds['left']['min_x'] or \
           self.left_basket_pos[0] >= self.basket_bounds['left']['max_x'] - 220:
            self.basket_direction['left'][0] *= -1
            
        if self.left_basket_pos[1] <= self.basket_bounds['left']['min_y'] or \
           self.left_basket_pos[1] >= self.basket_bounds['left']['max_y']:
            self.basket_direction['left'][1] *= -1
        
        # Mover canasta derecha (dentro de su zona)
        self.right_basket_pos[0] += self.basket_direction['right'][0] * current_speed
        self.right_basket_pos[1] += self.basket_direction['right'][1] * current_speed
        
        # Rebotes para canasta derecha (solo en su mitad)
        if self.right_basket_pos[0] <= self.basket_bounds['right']['min_x'] or \
           self.right_basket_pos[0] >= self.basket_bounds['right']['max_x'] - 220:
            self.basket_direction['right'][0] *= -1
            
        if self.right_basket_pos[1] <= self.basket_bounds['right']['min_y'] or \
           self.right_basket_pos[1] >= self.basket_bounds['right']['max_y']:
            self.basket_direction['right'][1] *= -1

    def handle_basket_score(self, player_id):
        current_time = time.time()
        points = 2
        
        if current_time - self.last_score_time < 3:
            self.combo_count += 1
            points += self.combo_count
            print(f"COMBO x{self.combo_count + 1} - Total: {points}")
        else:
            self.combo_count = 0
        
        if player_id == 1:
            old_score = self.player1_score
            self.player1_score += points
            print(f"JUGADOR 1: {old_score} -> {self.player1_score}")
            color = self.assets_manager.colors['neon_blue']
        else:
            old_score = self.player2_score
            self.player2_score += points
            print(f"JUGADOR 2: {old_score} -> {self.player2_score}")
            color = self.assets_manager.colors['neon_green']
        
        # Activar modos especiales
        max_score = max(self.player1_score, self.player2_score)
        
        if max_score >= 20 and not self.super_speed_activated:
            self.super_speed_activated = True
            self.basket_move_speed = 7
            print("MODO SUPER VELOCIDAD ACTIVADO! (20+ puntos)")
        elif max_score >= 8 and not self.moving_baskets:
            self.moving_baskets = True
            print("MODO DIFICIL ACTIVADO! (8+ puntos)")
        
        self.last_score_time = current_time
        print(f"MARCADOR - J1: {self.player1_score} | J2: {self.player2_score}")
        
        return points, color

    def reset_game(self):
        self.player1_score = 0
        self.player2_score = 0
        self.moving_baskets = False
        self.super_speed_activated = False
        self.basket_move_speed = 3
        self.combo_count = 0
        self.left_basket_pos = [100, 80]
        self.right_basket_pos = [960, 80]
        self.effects_manager.clear_particles()
        self.effects_manager.clear_confetti()
        self.start_time = time.time()
        self.game_over = False
        self.show_final_modal = False
        self.thumbs_up_count = 0
        print("Juego reiniciado! Nueva partida de 3 minutos")

    def detect_thumbs_up(self, hand):
        """Detectar gesto de pulgar arriba con cvzone"""
        if hand and 'lmList' in hand:
            lmList = hand['lmList']
            if len(lmList) >= 21:
                # Puntos clave de la mano
                thumb_tip = lmList[4]
                thumb_ip = lmList[3]
                thumb_mcp = lmList[2]
                
                index_tip = lmList[8]
                index_pip = lmList[6]
                middle_tip = lmList[12]
                middle_pip = lmList[10]
                ring_tip = lmList[16]
                ring_pip = lmList[14]
                pinky_tip = lmList[20]
                pinky_pip = lmList[18]
                
                # Verificar si el pulgar está extendido
                thumb_extended = thumb_tip[1] < thumb_ip[1] < thumb_mcp[1]
                
                # Verificar si otros dedos están doblados
                fingers_folded = (
                    index_tip[1] > index_pip[1] and
                    middle_tip[1] > middle_pip[1] and
                    ring_tip[1] > ring_pip[1] and
                    pinky_tip[1] > pinky_pip[1]
                )
                
                return thumb_extended and fingers_folded
        return False

    def detect_basket(self, hand_pos, left_basket_pos, right_basket_pos, split_line_x):
        """Detectar si la mano está cerca de una canasta"""
        x, y = hand_pos
        current_time = time.time()
        
        # Determinar en qué lado está la mano
        if x < split_line_x:
            player_side = 'left'
            player_id = 1
            aro_x = left_basket_pos[0] + 110
            aro_y = left_basket_pos[1] + 85
        else:
            player_side = 'right'
            player_id = 2
            aro_x = right_basket_pos[0] + 110
            aro_y = right_basket_pos[1] + 85
        
        # Verificar distancia al aro
        distance = math.sqrt((x - aro_x)**2 + (y - aro_y)**2)
        
        if distance <= 50 and current_time - self.last_basket_time > self.basket_cooldown:
            self.ball_positions[player_side].append((x, y, current_time))
            
            if len(self.ball_positions[player_side]) >= 3:
                positions = list(self.ball_positions[player_side])
                
                if self.is_basket_pattern(positions):
                    self.last_basket_time = current_time
                    self.ball_positions[player_side].clear()
                    return True, player_id
        
        return False, 0

    def is_basket_pattern(self, positions):
        """Verificar si el patrón de movimiento indica una canasta"""
        if len(positions) < 3:
            return False
            
        recent_positions = positions[-3:]
        y_positions = [pos[1] for pos in recent_positions]
        
        descent_count = 0
        for i in range(1, len(y_positions)):
            if y_positions[i] > y_positions[i-1]:
                descent_count += 1
        
        total_fall = y_positions[-1] - y_positions[0]
        
        is_valid = descent_count >= 1 and total_fall > 15
        return is_valid

    def run(self):
        # CAMBIADO: Modo ventana normal en lugar de pantalla completa
        cv2.namedWindow("Basketball Pro Championship", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Basketball Pro Championship", self.screen_width, self.screen_height)
        
        print("BASKETBALL PRO CHAMPIONSHIP INICIADO!")
        print("=" * 60)
        print("CONTROLES:")
        print("   Pulgar arriba 2 segundos: Salir")
        print("   R: Reiniciar puntajes")
        print("   ESC: Salida de emergencia")
        print("DURACION DEL JUEGO: 3 MINUTOS")
        print("REGLAS:")
        print("   PANTALLA DIVIDIDA - Cada jugador en su zona")
        print("   Jugador 1: Mitad IZQUIERDA (AZUL)")
        print("   Jugador 2: Mitad DERECHA (VERDE)")
        print("   Solo puedes anotar en tu lado de la pantalla")
        print("   8+ puntos: Canastas moviles activadas!")
        print("   20+ puntos: SUPER VELOCIDAD activada!")
        print("   Combos: Puntos extra por tiros consecutivos")
        print("=" * 60)
        
        while True:
            success, img = self.cap.read()
            if not success:
                break
                
            img = cv2.flip(img, 1)
            remaining_time = self.get_remaining_time()
            
            # Verificar fin de juego por tiempo
            if remaining_time <= 0 and not self.game_over:
                self.game_over = True
                self.show_final_modal = True
                self.effects_manager.create_confetti(60)
                self.thumbs_up_count = 0
                print("TIEMPO AGOTADO! Mostrando estadisticas finales...")
            
            # Actualizar canastas móviles
            if not self.game_over:
                self.update_moving_baskets()
            
            # Superponer assets
            img = Utils.overlay_with_mask(img, self.assets['hoop_left'], 
                                        self.assets['hoop_left_mask'], 
                                        self.left_basket_pos[0], self.left_basket_pos[1])
            img = Utils.overlay_with_mask(img, self.assets['hoop_right'], 
                                        self.assets['hoop_right_mask'], 
                                        self.right_basket_pos[0], self.right_basket_pos[1])
            
            # Procesar detección de manos con cvzone
            img, hands = self.hand_tracker.findHands(img)
            
            thumbs_detected = False
            
            if hands:
                for hand in hands:
                    # Detectar thumbs up
                    if self.detect_thumbs_up(hand):
                        thumbs_detected = True
                        if 'lmList' in hand and len(hand['lmList']) > 4:
                            cx = int(hand['lmList'][4][0])
                            cy = int(hand['lmList'][4][1])
                            cv2.circle(img, (cx, cy), 35, self.assets_manager.colors['success'], 4)
                            cv2.putText(img, "OK", (cx-20, cy+8), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 1.2, 
                                      self.assets_manager.colors['success'], 3)
                    
                    # Detectar canastas
                    if not self.game_over and 'lmList' in hand and len(hand['lmList']) > 9:
                        cx = int(hand['lmList'][9][0])  # Usar punto central de la mano
                        cy = int(hand['lmList'][9][1])
                        
                        basket_made, player_id = self.detect_basket(
                            (cx, cy), self.left_basket_pos, self.right_basket_pos, self.split_line_x)
                        
                        if basket_made:
                            points, color = self.handle_basket_score(player_id)
                            
                            # Efectos visuales
                            cv2.circle(img, (cx, cy), 70, self.assets_manager.colors['gold'], 5)
                            cv2.circle(img, (cx, cy), 50, self.assets_manager.colors['light'], 3)
                            
                            self.ui_manager.draw_text_with_shadow(img, f"+{points} PTS!", cx, cy-80, 
                                                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, 
                                                            self.assets_manager.colors['gold'], 4, center=True)
                            
                            if points > 2:
                                self.ui_manager.draw_text_with_shadow(img, "COMBO!", cx, cy+100, 
                                                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, 
                                                                self.assets_manager.colors['purple'], 3, center=True)
                            
                            self.effects_manager.create_particle_explosion(cx, cy, color, 30)
                        
                        # Dibujar pelota en la posición de la mano
                        ball_x, ball_y = cx - 27, cy - 27
                        if (0 <= ball_x < img.shape[1]-55 and 0 <= ball_y < img.shape[0]-55):
                            img = Utils.overlay_with_mask(img, self.assets['ball'], 
                                                        self.assets['ball_mask'], ball_x, ball_y)
            
            # Manejo del sistema de salida
            if thumbs_detected:
                self.thumbs_up_count += 1
            else:
                self.thumbs_up_count = max(0, self.thumbs_up_count - 2)
            
            if self.thumbs_up_count >= self.thumbs_up_threshold and not self.exiting:
                if self.show_final_modal:
                    self.show_final_modal = False
                    self.exiting = True
                    print("Saliendo del juego...")
                elif not self.game_over:
                    self.exiting = True
                    print("Iniciando secuencia de despedida...")
            
            # Actualizar efectos
            self.effects_manager.update_particles()
            self.effects_manager.draw_particles(img)
            
            if self.game_over or self.show_final_modal:
                self.effects_manager.update_confetti()
                self.effects_manager.draw_confetti(img)
            
            # Dibujar UI
            if self.exiting:
                img = self.ui_manager.draw_exit_animation(img, self.exit_frame_count, 
                                                        self.exit_animation_frames)
                self.exit_frame_count += 1
                if self.exit_frame_count >= self.exit_animation_frames:
                    break
            elif self.show_final_modal:
                img = self.ui_manager.draw_final_statistics_modal(
                    img, self.player1_score, self.player2_score,
                    self.super_speed_activated, self.moving_baskets,
                    self.thumbs_up_count, self.thumbs_up_threshold)
            else:
                img = self.ui_manager.draw_professional_ui(
                    img, self.player1_score, self.player2_score, remaining_time,
                    self.combo_count, self.thumbs_up_count, self.thumbs_up_threshold,
                    self.super_speed_activated, self.moving_baskets, self.split_line_x,
                    self.left_basket_pos, self.right_basket_pos)
            
            cv2.imshow("Basketball Pro Championship", img)
            
            # Manejo de teclas
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('r') or key == ord('R'):
                if not self.exiting:
                    self.reset_game()
        
        self.cleanup()

    def cleanup(self):
        self.cap.release()
        cv2.destroyAllWindows()
        
        print("\n" + "="*60)
        print("ESTADISTICAS FINALES:")
        print(f"   Jugador 1: {self.player1_score} puntos")
        print(f"   Jugador 2: {self.player2_score} puntos")
        
        if self.player1_score > self.player2_score:
            print("   GANADOR: JUGADOR 1!")
        elif self.player2_score > self.player1_score:
            print("   GANADOR: JUGADOR 2!")
        else:
            print("   EMPATE PERFECTO!")
            
        # Estadísticas de logros
        if self.super_speed_activated:
            print("   Lograron activar el modo SUPER VELOCIDAD!")
        elif self.moving_baskets:
            print("   Lograron activar el modo dificil!")
            
        total_points = self.player1_score + self.player2_score
        if total_points >= 40:
            print("   PARTIDA LEGENDARIA! Mas de 40 puntos en 3 minutos")
        elif total_points >= 25:
            print("   GRAN PARTIDA! Excelente competencia")
            
        print("   Gracias por jugar Basketball Pro Championship!")
        print("="*60)