# Función que pega imágenes (pelota, canastas) sobre el video 
# de la cámara sin mostrar fondos blancos, usando máscaras para integración visual profesional.
import cv2
import numpy as np

class Utils:
    @staticmethod
    def overlay_with_mask(bg, fg, mask, x, y):
        """Superponer imagen con máscara sobre fondo"""
        h, w = fg.shape[:2]
        H, W = bg.shape[:2]
        
        if x < 0:
            w += x
            fg = fg[:, -x:]
            mask = mask[:, -x:]
            x = 0
        if y < 0:
            h += y
            fg = fg[-y:, :]
            mask = mask[-y:, :]
            y = 0
        if x + w > W:
            w = W - x
            fg = fg[:, :w]
            mask = mask[:, :w]
        if y + h > H:
            h = H - y
            fg = fg[:h]
            mask = mask[:h]
            
        if w <= 0 or h <= 0:
            return bg
            
        try:
            roi = bg[y:y+h, x:x+w]
            mask_norm = mask.astype(float) / 255
            
            if len(fg.shape) == 3:
                mask_3d = np.stack([mask_norm] * 3, axis=2)
            else:
                mask_3d = mask_norm
                
            blended = roi * (1 - mask_3d) + fg * mask_3d
            bg[y:y+h, x:x+w] = blended.astype(np.uint8)
        except Exception as e:
            print(f"Error en overlay: {e}")
            bg[y:y+h, x:x+w] = fg
            
        return bg