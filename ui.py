# Interfaz de usuario
import cv2
import numpy as np
import math
import time

class UIManager:
    def __init__(self, colors):
        self.colors = colors

    def draw_text_with_shadow(self, img, text, x, y, font, size, color, thickness, center=False):
        if center:
            text_size = cv2.getTextSize(text, font, size, thickness)[0]
            x = x - text_size[0] // 2
        
        cv2.putText(img, text, (x + 3, y + 3), font, size, (0, 0, 0), thickness + 1)
        cv2.putText(img, text, (x, y), font, size, color, thickness)

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def draw_crown(self, img, x, y, color, scale=1.0):
        size = int(30 * scale)
        pts = np.array([
            [x, y + size],
            [x + size*2, y + size],
            [x + size*2, y + size//2],
            [x + size*1.7, y + size//4],
            [x + size*1.3, y],
            [x + size, y + size//4],
            [x + size*0.7, y],
            [x + size*0.3, y + size//4],
            [x, y + size//2]
        ], np.int32)
        
        cv2.fillPoly(img, [pts], color)
        cv2.polylines(img, [pts], True, self.colors['accent'], 2)
        
        cv2.circle(img, (x + size, y + size//3), 4, self.colors['danger'], -1)
        cv2.circle(img, (x + size//2, y + size//2), 3, self.colors['neon_blue'], -1)
        cv2.circle(img, (x + size*3//2, y + size//2), 3, self.colors['neon_green'], -1)

    def draw_detection_zones(self, img, split_line_x, left_basket_pos, right_basket_pos):
        screen_height = img.shape[0]
        
        # Línea divisoria central
        cv2.line(img, (split_line_x, 140), (split_line_x, screen_height-50), 
                self.colors['light'], 2)
        
        # Etiquetas de zonas de jugadores
        self.draw_text_with_shadow(img, "JUGADOR 1", split_line_x//2, 170, 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, 
                                self.colors['neon_blue'], 3, center=True)
        self.draw_text_with_shadow(img, "JUGADOR 2", split_line_x + split_line_x//2, 170, 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, 
                                self.colors['neon_green'], 3, center=True)
        
        # Círculo alrededor del aro izquierdo (Jugador 1)
        aro_left_x = left_basket_pos[0] + 110
        aro_left_y = left_basket_pos[1] + 85
        cv2.circle(img, (aro_left_x, aro_left_y), 50, self.colors['neon_blue'], 3)
        cv2.putText(img, "ARO J1", (aro_left_x - 30, aro_left_y - 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.colors['neon_blue'], 2)
        
        # Círculo alrededor del aro derecho (Jugador 2)
        aro_right_x = right_basket_pos[0] + 110
        aro_right_y = right_basket_pos[1] + 85
        cv2.circle(img, (aro_right_x, aro_right_y), 50, self.colors['neon_green'], 3)
        cv2.putText(img, "ARO J2", (aro_right_x - 30, aro_right_y - 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.colors['neon_green'], 2)

    def draw_professional_ui(self, img, player1_score, player2_score, remaining_time, 
                           combo_count, thumbs_up_count, thumbs_up_threshold, 
                           super_speed_activated, moving_baskets, split_line_x, 
                           left_basket_pos, right_basket_pos):
        height, width = img.shape[:2]
        current_time = time.time()
        
        # Header con gradiente
        header_height = 140
        overlay = img.copy()
        
        for y in range(header_height):
            alpha = (header_height - y) / header_height * 0.85
            color = tuple(int(c * alpha) for c in [40, 40, 60])
            cv2.line(overlay, (0, y), (width, y), color, 1)
        
        img = cv2.addWeighted(img, 0.25, overlay, 0.75, 0)
        
        # Titulo
        title = "BASKETBALL PRO CHAMPIONSHIP"
        self.draw_text_with_shadow(img, title, width//2, 45, 
                                 cv2.FONT_HERSHEY_SIMPLEX, 1.4, 
                                 self.colors['accent'], 4, center=True)
        
        # Cronometro
        time_str = self.format_time(remaining_time)
        if remaining_time <= 30:
            time_color = self.colors['danger']
        elif remaining_time <= 60:
            time_color = self.colors['accent']
        else:
            time_color = self.colors['light']
            
        self.draw_text_with_shadow(img, f"TIEMPO: {time_str}", width//2, 80, 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.1, 
                                 time_color, 3, center=True)
        
        # Marcadores
        score_y = 110
        
        # Jugador 1
        p1_text = f"JUGADOR 1: {player1_score}"
        p1_bg = (60, 85, 260, 140)
        cv2.rectangle(img, p1_bg[:2], p1_bg[2:], self.colors['neon_blue'], 3)
        cv2.rectangle(img, (p1_bg[0]+3, p1_bg[1]+3), (p1_bg[2]-3, p1_bg[3]-3), (20, 20, 40), -1)
        self.draw_text_with_shadow(img, p1_text, 70, score_y, 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, 
                                self.colors['neon_blue'], 3)
        
        # Jugador 2
        p2_text = f"JUGADOR 2: {player2_score}"
        p2_bg = (width-260, 85, width-60, 140)
        cv2.rectangle(img, p2_bg[:2], p2_bg[2:], self.colors['neon_green'], 3)
        cv2.rectangle(img, (p2_bg[0]+3, p2_bg[1]+3), (p2_bg[2]-3, p2_bg[3]-3), (20, 40, 20), -1)
        self.draw_text_with_shadow(img, p2_text, width-250, score_y, 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, 
                                self.colors['neon_green'], 3)
        
        # Combo
        if combo_count > 0:
            combo_text = f"COMBO x{combo_count + 1}!"
            pulse = abs(math.sin(current_time * 8)) * 0.4 + 0.6
            combo_color = tuple(int(c * pulse) for c in self.colors['gold'])
            self.draw_text_with_shadow(img, combo_text, width//2, 125, 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, 
                                    combo_color, 3, center=True)
        
        # Zonas de deteccion
        self.draw_detection_zones(img, split_line_x, left_basket_pos, right_basket_pos)
        
        # Estado del juego
        status_y = height - 80
        max_score = max(player1_score, player2_score)
        
        if super_speed_activated:
            status_text = "MODO SUPER VELOCIDAD! - CANASTAS A MAXIMA VELOCIDAD!"
            status_color = self.colors['danger']
            # Efecto de parpadeo para el modo súper velocidad
            pulse = abs(math.sin(current_time * 10)) * 0.5 + 0.5
            status_color = tuple(int(c * pulse) for c in status_color)
        elif moving_baskets:
            status_text = "MODO DIFICIL ACTIVADO - CANASTAS EN MOVIMIENTO!"
            status_color = self.colors['accent']
        else:
            status_text = f"8 puntos: Modo Dificil | 20 puntos: Super Velocidad"
            status_color = self.colors['light']
            
        self.draw_text_with_shadow(img, status_text, width//2, status_y, 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                                status_color, 2, center=True)
        
        # Controles
        if thumbs_up_count > 0:
            progress = min(thumbs_up_count / thumbs_up_threshold, 1.0)
            exit_text = f"SALIENDO... {int(progress * 100)}%"
            
            bar_width = 250
            bar_height = 20
            bar_x = (width - bar_width) // 2
            bar_y = height - 50
            
            cv2.rectangle(img, (bar_x-2, bar_y-2), (bar_x+bar_width+2, bar_y+bar_height+2), 
                        self.colors['light'], 2)
            cv2.rectangle(img, (bar_x, bar_y), (bar_x+bar_width, bar_y+bar_height), 
                        (60, 60, 60), -1)
            
            progress_width = int(bar_width * progress)
            cv2.rectangle(img, (bar_x, bar_y), (bar_x+progress_width, bar_y+bar_height), 
                        self.colors['danger'], -1)
            
            self.draw_text_with_shadow(img, exit_text, width//2, bar_y-10, 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, 
                                    self.colors['danger'], 2, center=True)
        else:
            controls_text = "Manten pulgar arriba 2s para salir | R: Reiniciar"
            self.draw_text_with_shadow(img, controls_text, width//2, height-25, 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                                    self.colors['light'], 1, center=True)
        
        return img

    def draw_final_statistics_modal(self, img, player1_score, player2_score, 
                                  super_speed_activated, moving_baskets, 
                                  thumbs_up_count, thumbs_up_threshold):
        height, width = img.shape[:2]
        
        # Overlay oscuro
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 0), -1)
        img = cv2.addWeighted(img, 0.3, overlay, 0.7, 0)
        
        # Modal
        modal_width = 800
        modal_height = 600
        modal_x = (width - modal_width) // 2
        modal_y = (height - modal_height) // 2
        
        # Fondo del modal
        modal_bg = np.zeros((modal_height, modal_width, 3), dtype=np.uint8)
        for y in range(modal_height):
            progress = y / modal_height
            r = int(30 + progress * 20)
            g = int(30 + progress * 20)
            b = int(50 + progress * 30)
            modal_bg[y, :] = [b, g, r]
        
        img[modal_y:modal_y+modal_height, modal_x:modal_x+modal_width] = modal_bg
        
        # Borde
        cv2.rectangle(img, (modal_x-5, modal_y-5), 
                     (modal_x+modal_width+5, modal_y+modal_height+5), 
                     self.colors['accent'], 8)
        cv2.rectangle(img, (modal_x, modal_y), 
                     (modal_x+modal_width, modal_y+modal_height), 
                     self.colors['light'], 3)
        
        # Título
        title_y = modal_y + 80
        self.draw_text_with_shadow(img, "ESTADISTICAS FINALES", 
                                 modal_x + modal_width//2, title_y, 
                                 cv2.FONT_HERSHEY_SIMPLEX, 1.8, 
                                 self.colors['accent'], 4, center=True)
        
        # Separador
        cv2.line(img, (modal_x + 100, title_y + 30), 
                (modal_x + modal_width - 100, title_y + 30), 
                self.colors['accent'], 4)
        
        # Puntajes
        score_y = title_y + 120
        self.draw_text_with_shadow(img, f"Jugador 1: {player1_score} puntos", 
                                 modal_x + modal_width//2, score_y, 
                                 cv2.FONT_HERSHEY_SIMPLEX, 1.3, 
                                 self.colors['neon_blue'], 3, center=True)
        
        self.draw_text_with_shadow(img, f"Jugador 2: {player2_score} puntos", 
                                 modal_x + modal_width//2, score_y + 60, 
                                 cv2.FONT_HERSHEY_SIMPLEX, 1.3, 
                                 self.colors['neon_green'], 3, center=True)
        
        # Ganador
        winner_y = score_y + 150
        if player1_score > player2_score:
            winner_text = "GANADOR: JUGADOR 1!"
            winner_color = self.colors['gold']
            self.draw_crown(img, modal_x + modal_width//2 - 40, winner_y - 50, 
                          self.colors['gold'], 1.5)
        elif player2_score > player1_score:
            winner_text = "GANADOR: JUGADOR 2!"
            winner_color = self.colors['gold']
            self.draw_crown(img, modal_x + modal_width//2 - 40, winner_y - 50, 
                          self.colors['gold'], 1.5)
        else:
            winner_text = "EMPATE PERFECTO!"
            winner_color = self.colors['silver']
            self.draw_crown(img, modal_x + modal_width//2 - 70, winner_y - 50, 
                          self.colors['silver'], 1.0)
            self.draw_crown(img, modal_x + modal_width//2 + 10, winner_y - 50, 
                          self.colors['silver'], 1.0)
        
        self.draw_text_with_shadow(img, winner_text, 
                                 modal_x + modal_width//2, winner_y, 
                                 cv2.FONT_HERSHEY_SIMPLEX, 1.5, 
                                 winner_color, 4, center=True)
        
        # Logros
        achievement_y = winner_y + 80
        if super_speed_activated:
            self.draw_text_with_shadow(img, "Lograron activar el modo SUPER VELOCIDAD!", 
                                     modal_x + modal_width//2, achievement_y, 
                                     cv2.FONT_HERSHEY_SIMPLEX, 1.0, 
                                     self.colors['danger'], 3, center=True)
            achievement_y += 40
        elif moving_baskets:
            self.draw_text_with_shadow(img, "Lograron activar el modo dificil!", 
                                     modal_x + modal_width//2, achievement_y, 
                                     cv2.FONT_HERSHEY_SIMPLEX, 1.0, 
                                     self.colors['accent'], 3, center=True)
            achievement_y += 40
        
        # Mensaje final
        self.draw_text_with_shadow(img, "Gracias por jugar Basketball Pro Championship!", 
                                 modal_x + modal_width//2, achievement_y + 30, 
                                 cv2.FONT_HERSHEY_SIMPLEX, 0.9, 
                                 self.colors['light'], 2, center=True)
        
        # Instrucción de salida
        if thumbs_up_count > 0:
            progress = min(thumbs_up_count / thumbs_up_threshold, 1.0)
            exit_text = f"SALIENDO... {int(progress * 100)}%"
            
            bar_width = 300
            bar_height = 25
            bar_x = modal_x + (modal_width - bar_width) // 2
            bar_y = modal_y + modal_height - 80
            
            cv2.rectangle(img, (bar_x-2, bar_y-2), (bar_x+bar_width+2, bar_y+bar_height+2), 
                        self.colors['light'], 2)
            cv2.rectangle(img, (bar_x, bar_y), (bar_x+bar_width, bar_y+bar_height), 
                        (60, 60, 60), -1)
            
            progress_width = int(bar_width * progress)
            cv2.rectangle(img, (bar_x, bar_y), (bar_x+progress_width, bar_y+bar_height), 
                        self.colors['danger'], -1)
            
            self.draw_text_with_shadow(img, exit_text, modal_x + modal_width//2, bar_y-15, 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, 
                                    self.colors['danger'], 2, center=True)
        else:
            self.draw_text_with_shadow(img, "Manten el pulgar arriba para salir", 
                                     modal_x + modal_width//2, modal_y + modal_height - 50, 
                                     cv2.FONT_HERSHEY_SIMPLEX, 0.8, 
                                     self.colors['accent'], 2, center=True)
        
        return img

    def draw_exit_animation(self, img, exit_frame_count, exit_animation_frames):
        height, width = img.shape[:2]
        progress = exit_frame_count / exit_animation_frames
        
        overlay = np.zeros_like(img)
        alpha = progress * 0.9
        img = cv2.addWeighted(img, 1 - alpha, overlay, alpha, 0)
        
        farewell_texts = [
            "Gracias por jugar!",
            "Hasta la proxima!",
            "Sigue practicando!",
            "Basketball Pro Championship!"
        ]
        
        text_index = min(int(progress * len(farewell_texts)), len(farewell_texts) - 1)
        text = farewell_texts[text_index]
        
        scale = 0.8 + math.sin(progress * math.pi) * 0.7
        font_size = 2.2 * scale
        
        color_progress = (progress * 2) % 1
        if color_progress < 0.5:
            color = self.colors['accent']
        else:
            color = self.colors['gold']
        
        self.draw_text_with_shadow(img, text, width//2, height//2, 
                                cv2.FONT_HERSHEY_SIMPLEX, font_size, 
                                 color, int(4 * scale), center=True)
        
        return img