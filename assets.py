#Gestión de imágenes y gráficos
import cv2
import numpy as np
import math

class AssetsManager:
    def __init__(self):
        self.colors = {
            'primary': (255, 140, 0),
            'accent': (255, 215, 0),
            'success': (50, 205, 50),
            'danger': (255, 69, 0),
            'dark': (25, 25, 25),
            'light': (255, 255, 255),
            'neon_green': (0, 255, 127),
            'neon_blue': (0, 191, 255),
            'purple': (147, 0, 211),
            'gold': (255, 215, 0),
            'silver': (192, 192, 192)
        }

    def remove_background_advanced(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        mask_white = cv2.inRange(hsv, lower_white, upper_white)
        
        lower_gray = np.array([0, 0, 180])
        upper_gray = np.array([180, 50, 220])
        mask_gray = cv2.inRange(hsv, lower_gray, upper_gray)
        
        background_mask = cv2.bitwise_or(mask_white, mask_gray)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        background_mask = cv2.morphologyEx(background_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        background_mask = cv2.morphologyEx(background_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        object_mask = cv2.bitwise_not(background_mask)
        object_mask = cv2.GaussianBlur(object_mask, (3, 3), 0)
        
        return object_mask

    def load_assets(self):
        assets = {}
        
        try:
            hoop_left_orig = cv2.imread('assets/hoop_left.jpg')
            hoop_right_orig = cv2.imread('assets/hoop_right.jpg')
            ball_orig = cv2.imread('assets/ball.jpg')
            
            if hoop_left_orig is not None and hoop_right_orig is not None and ball_orig is not None:
                assets['hoop_left'] = cv2.resize(hoop_left_orig, (220, 170))
                assets['hoop_right'] = cv2.resize(hoop_right_orig, (220, 170))
                assets['ball'] = cv2.resize(ball_orig, (55, 55))
                
                assets['hoop_left_mask'] = self.remove_background_advanced(assets['hoop_left'])
                assets['hoop_right_mask'] = self.remove_background_advanced(assets['hoop_right'])
                assets['ball_mask'] = self.remove_background_advanced(assets['ball'])
                
                print("Assets cargados con fondo transparente")
            else:
                raise FileNotFoundError("Imagenes no encontradas")
            
        except Exception as e:
            print(f"Creando assets profesionales: {e}")
            assets = self.create_professional_assets()
            
        return assets

    def create_professional_assets(self):
        assets = {}
        
        # Canasta izquierda
        hoop_left = np.zeros((170, 220, 3), dtype=np.uint8)
        
        # Tablero
        tablero_color = (180, 100, 50)
        cv2.rectangle(hoop_left, (60, 30), (160, 100), tablero_color, -1)
        cv2.rectangle(hoop_left, (60, 30), (160, 100), self.colors['dark'], 3)
        cv2.rectangle(hoop_left, (90, 50), (130, 80), self.colors['light'], 2)
        
        # Aro principal
        center_x, center_y = 110, 85
        aro_radius = 35
        
        cv2.circle(hoop_left, (center_x, center_y), aro_radius + 3, self.colors['danger'], 8)
        cv2.circle(hoop_left, (center_x, center_y), aro_radius, self.colors['accent'], 6)
        cv2.circle(hoop_left, (center_x, center_y), aro_radius - 3, self.colors['light'], 4)
        
        # Red del aro
        red_lines = 16
        for i in range(red_lines):
            angle = i * (360 / red_lines)
            x1 = int(center_x + (aro_radius - 2) * math.cos(math.radians(angle)))
            y1 = int(center_y + (aro_radius - 2) * math.sin(math.radians(angle)))
            
            red_length = 25 + np.random.randint(-5, 5)
            x2 = x1 + np.random.randint(-3, 3)
            y2 = y1 + red_length
            
            cv2.line(hoop_left, (x1, y1), (x2, y2), self.colors['light'], 3)
            
            if i % 2 == 0 and i < red_lines - 2:
                next_angle = (i + 2) * (360 / red_lines)
                x3 = int(center_x + (aro_radius - 2) * math.cos(math.radians(next_angle)))
                y3 = int(center_y + (aro_radius - 2) * math.sin(math.radians(next_angle)))
                
                mid_x = (x1 + x3) // 2
                mid_y = (y1 + y3) // 2 + 8
                cv2.line(hoop_left, (x1, y1 + 8), (mid_x, mid_y), self.colors['light'], 2)
                cv2.line(hoop_left, (mid_x, mid_y), (x3, y3 + 8), self.colors['light'], 2)
        
        # Soporte
        cv2.rectangle(hoop_left, (center_x - 5, center_y + aro_radius + 3), 
                     (center_x + 5, center_y + aro_radius + 20), self.colors['dark'], -1)
        cv2.rectangle(hoop_left, (center_x - 15, center_y + aro_radius + 20), 
                     (center_x + 15, center_y + aro_radius + 25), self.colors['dark'], -1)
        
        # Canasta derecha
        hoop_right = cv2.flip(hoop_left, 1)
        
        # Pelota
        ball = np.zeros((55, 55, 3), dtype=np.uint8)
        center = (27, 27)
        radius = 25
        
        cv2.circle(ball, center, radius, (0, 165, 255), -1)
        cv2.circle(ball, center, radius, self.colors['dark'], 3)
        
        cv2.line(ball, (2, 27), (52, 27), self.colors['dark'], 4)
        cv2.line(ball, (27, 2), (27, 52), self.colors['dark'], 4)
        
        cv2.ellipse(ball, center, (20, 10), 0, 0, 180, self.colors['dark'], 4)
        cv2.ellipse(ball, center, (20, 10), 0, 180, 360, self.colors['dark'], 4)
        cv2.ellipse(ball, center, (10, 20), 90, 0, 180, self.colors['dark'], 4)
        cv2.ellipse(ball, center, (10, 20), 90, 180, 360, self.colors['dark'], 4)
        
        assets['hoop_left'] = hoop_left
        assets['hoop_right'] = hoop_right
        assets['ball'] = ball
        
        # Máscaras
        hoop_left_gray = cv2.cvtColor(hoop_left, cv2.COLOR_BGR2GRAY)
        hoop_right_gray = cv2.cvtColor(hoop_right, cv2.COLOR_BGR2GRAY)
        ball_gray = cv2.cvtColor(ball, cv2.COLOR_BGR2GRAY)
        
        assets['hoop_left_mask'] = cv2.threshold(hoop_left_gray, 10, 255, cv2.THRESH_BINARY)[1]
        assets['hoop_right_mask'] = cv2.threshold(hoop_right_gray, 10, 255, cv2.THRESH_BINARY)[1]
        assets['ball_mask'] = cv2.threshold(ball_gray, 10, 255, cv2.THRESH_BINARY)[1]
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        assets['hoop_left_mask'] = cv2.morphologyEx(assets['hoop_left_mask'], cv2.MORPH_CLOSE, kernel)
        assets['hoop_right_mask'] = cv2.morphologyEx(assets['hoop_right_mask'], cv2.MORPH_CLOSE, kernel)
        assets['ball_mask'] = cv2.morphologyEx(assets['ball_mask'], cv2.MORPH_CLOSE, kernel)
        
        return assets