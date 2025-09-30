#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MENÚ ARCADE CON CARDS ESTILO GALAXY
Diseño moderno con cards estilo Bootstrap
"""

import cv2
import numpy as np
import subprocess
import sys
import os
import random
import math

# Los 4 juegos
JUEGOS = [
    {
        'nombre': 'BASKETBALL PRO',
        'archivo': 'main.py',
        'color': (255, 140, 0),
        'icono': '🏀',
        'descripcion': 'Lanza y anota'
    },
    {
        'nombre': 'FRUIT NINJA',
        'archivo': 'fruit_ninja.py',
        'color': (255, 20, 147),
        'icono': '🍉',
        'descripcion': 'Corta las frutas'
    },
    {
        'nombre': 'ESQUIVAR BLOQUES',
        'archivo': 'juego_saltar.py',
        'color': (138, 43, 226),
        'icono': '⚡',
        'descripcion': 'Salta y esquiva'
    },
    {
        'nombre': 'TORRE DUELO',
        'archivo': 'torre_duelo.py',
        'color': (0, 255, 255),
        'icono': '🗼',
        'descripcion': 'Batalla épica'
    }
]

class Estrella:
    def __init__(self, w, h):
        self.x = random.randint(0, w)
        self.y = random.randint(0, h)
        self.size = random.randint(1, 3)
        self.brillo = random.randint(150, 255)
        self.velocidad = random.uniform(0.1, 0.5)
        
    def actualizar(self):
        self.brillo += random.randint(-10, 10)
        self.brillo = max(100, min(255, self.brillo))

class Galaxia:
    def __init__(self, w, h):
        self.x = random.randint(100, w-100)
        self.y = random.randint(100, h-100)
        self.radio = random.randint(30, 60)
        self.rotacion = random.uniform(0, 360)
        self.velocidad_rot = random.uniform(0.2, 0.5)
        self.color = random.choice([
            (200, 100, 255),  # Morado
            (255, 100, 200),  # Rosa
            (100, 150, 255)   # Azul
        ])
    
    def actualizar(self):
        self.rotacion += self.velocidad_rot
        if self.rotacion >= 360:
            self.rotacion = 0

def verificar_juegos():
    """Verificar qué juegos existen"""
    print("\n" + "="*50)
    print("VERIFICANDO JUEGOS DISPONIBLES")
    print("="*50)
    
    disponibles = []
    for juego in JUEGOS:
        if os.path.exists(juego['archivo']):
            print(f"✓ {juego['nombre']} - {juego['archivo']}")
            disponibles.append(juego)
        else:
            print(f"✗ {juego['nombre']} - NO ENCONTRADO")
    
    print("="*50 + "\n")
    return disponibles

def crear_fondo_galaxia(w, h, estrellas, galaxias):
    """Crear fondo espacial con estrellas y galaxias"""
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Fondo negro con ligero gradiente
    for y in range(h):
        ratio = y / h
        val = int(5 + ratio * 15)
        frame[y, :] = [val, val, val]
    
    # Dibujar galaxias
    for galaxia in galaxias:
        # Efecto de galaxia espiral
        overlay = frame.copy()
        for i in range(3):
            radio = galaxia.radio - i * 15
            angulo = galaxia.rotacion + i * 45
            alpha = 0.3 - i * 0.1
            
            for j in range(8):
                ang_rad = math.radians(angulo + j * 45)
                x_end = int(galaxia.x + math.cos(ang_rad) * radio)
                y_end = int(galaxia.y + math.sin(ang_rad) * radio)
                
                cv2.ellipse(overlay, (galaxia.x, galaxia.y), 
                          (radio, radio//2), angulo + j * 45, 
                          0, 180, galaxia.color, -1)
        
        cv2.addWeighted(frame, 1, overlay, 0.15, 0, frame)
        
        galaxia.actualizar()
    
    # Dibujar estrellas
    for estrella in estrellas:
        color = (estrella.brillo, estrella.brillo, estrella.brillo)
        cv2.circle(frame, (estrella.x, estrella.y), estrella.size, color, -1)
        
        # Algunas estrellas brillan más
        if estrella.size >= 2 and random.random() > 0.95:
            cv2.circle(frame, (estrella.x, estrella.y), 
                      estrella.size + 2, color, 1)
        
        estrella.actualizar()
    
    return frame

def cargar_logo(nombre_archivo, h_deseada=None):
    """Intentar cargar logo PNG con transparencia"""
    if os.path.exists(nombre_archivo):
        img = cv2.imread(nombre_archivo, cv2.IMREAD_UNCHANGED)
        if img is not None:
            if h_deseada:
                ratio = h_deseada / img.shape[0]
                w_nueva = int(img.shape[1] * ratio)
                img = cv2.resize(img, (w_nueva, h_deseada))
            return img
    return None

def overlay_png(fondo, png, x, y):
    """Superponer PNG con transparencia"""
    if png is None:
        return
    
    h, w = png.shape[:2]
    
    # Ajustar coordenadas si se sale del frame
    if x < 0: x = 0
    if y < 0: y = 0
    if x + w > fondo.shape[1]: w = fondo.shape[1] - x
    if y + h > fondo.shape[0]: h = fondo.shape[0] - y
    
    if w <= 0 or h <= 0:
        return
    
    png_crop = png[:h, :w]
    
    # Si tiene canal alpha
    if png_crop.shape[2] == 4:
        alpha = png_crop[:, :, 3] / 255.0
        for c in range(3):
            fondo[y:y+h, x:x+w, c] = (
                alpha * png_crop[:, :, c] + 
                (1 - alpha) * fondo[y:y+h, x:x+w, c]
            )
    else:
        fondo[y:y+h, x:x+w] = png_crop[:, :, :3]

def dibujar_card(frame, juego, x, y, w, h, hover=False, pulse=0):
    """Dibujar una card estilo Bootstrap para un juego"""
    overlay = frame.copy()
    
    # Colores del tema
    if hover:
        # Degradado brillante cuando está seleccionado
        for i in range(h):
            ratio = i / h
            r = int(120 + ratio * 80)  # Morado a rosa
            g = int(50 + ratio * 100)
            b = int(220 - ratio * 60)
            color = (b, g, r)
            cv2.rectangle(overlay, (x, y+i), (x+w, y+i+1), color, -1)
        
        # Brillo de pulso
        brillo_extra = int(20 * math.sin(pulse))
        cv2.rectangle(overlay, (x, y), (x+w, y+h), 
                     (255, 255, 255), 3)
    else:
        # Card normal con degradado sutil
        for i in range(h):
            ratio = i / h
            val = int(30 + ratio * 25)
            color = (val, val, val + 15)
            cv2.rectangle(overlay, (x, y+i), (x+w, y+i+1), color, -1)
    
    # Mezclar con transparencia
    alpha = 0.85 if hover else 0.75
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    # Borde de la card
    border_color = (200, 150, 255) if hover else (100, 80, 150)
    cv2.rectangle(frame, (x, y), (x+w, y+h), border_color, 2)
    
    # Área superior de color (header de la card)
    header_h = 80
    overlay2 = frame.copy()
    cv2.rectangle(overlay2, (x+2, y+2), (x+w-2, y+header_h), juego['color'], -1)
    cv2.addWeighted(overlay2, 0.3, frame, 0.7, 0, frame)
    
    # Línea divisoria
    cv2.line(frame, (x+2, y+header_h), (x+w-2, y+header_h), 
             border_color, 2)
    
    # Icono del juego (emoji simulado con forma)
    icono_y = y + 35
    icono_size = 30
    
    # Dibujar forma según el juego
    if '🏀' in juego['icono']:  # Basketball
        cv2.circle(frame, (x+w//2, icono_y), icono_size, (0, 165, 255), -1)
        cv2.circle(frame, (x+w//2, icono_y), icono_size, (255, 255, 255), 2)
    elif '🍉' in juego['icono']:  # Fruit
        pts = np.array([[x+w//2, icono_y-icono_size],
                       [x+w//2-icono_size, icono_y+icono_size//2],
                       [x+w//2+icono_size, icono_y+icono_size//2]], np.int32)
        cv2.fillPoly(frame, [pts], (50, 255, 50))
    elif '⚡' in juego['icono']:  # Rayo
        pts = np.array([[x+w//2, icono_y-icono_size],
                       [x+w//2-icono_size//2, icono_y],
                       [x+w//2+icono_size//2, icono_y],
                       [x+w//2, icono_y+icono_size]], np.int32)
        cv2.fillPoly(frame, [pts], (0, 255, 255))
    else:  # Torre
        cv2.rectangle(frame, (x+w//2-icono_size//2, icono_y-icono_size),
                     (x+w//2+icono_size//2, icono_y+icono_size), (255, 255, 0), -1)
    
    # Título del juego
    titulo_y = y + header_h + 40
    # Ajustar tamaño de fuente según largo del título
    font_scale = 0.7 if len(juego['nombre']) > 12 else 0.85
    
    # Texto con sombra
    cv2.putText(frame, juego['nombre'], (x+w//2-80, titulo_y+2), 
               cv2.FONT_HERSHEY_DUPLEX, font_scale, (0, 0, 0), 3)
    cv2.putText(frame, juego['nombre'], (x+w//2-80, titulo_y), 
               cv2.FONT_HERSHEY_DUPLEX, font_scale, (255, 255, 255), 2)
    
    # Descripción
    desc_y = titulo_y + 35
    cv2.putText(frame, juego['descripcion'], (x+w//2-70, desc_y), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 200), 1)
    
    # Botón "JUGAR"
    btn_y = y + h - 50
    btn_w = 120
    btn_h = 35
    btn_x = x + (w - btn_w) // 2
    
    if hover:
        btn_color = (255, 200, 255)
        texto_color = (80, 20, 120)
    else:
        btn_color = (150, 100, 200)
        texto_color = (255, 255, 255)
    
    cv2.rectangle(frame, (btn_x, btn_y), (btn_x+btn_w, btn_y+btn_h), 
                 btn_color, -1)
    cv2.rectangle(frame, (btn_x, btn_y), (btn_x+btn_w, btn_y+btn_h), 
                 (200, 150, 255), 2)
    
    cv2.putText(frame, "JUGAR", (btn_x+25, btn_y+24), 
               cv2.FONT_HERSHEY_DUPLEX, 0.7, texto_color, 2)

def dibujar_menu(seleccionado, juegos_disponibles, estrellas, galaxias, pulse, logo_text, logo_soft):
    """Dibujar menú completo con cards"""
    w, h = 1400, 900
    frame = crear_fondo_galaxia(w, h, estrellas, galaxias)
    
    # Logo superior (text-soft.png)
    if logo_text is not None:
        logo_h = logo_text.shape[0]
        logo_w = logo_text.shape[1]
        overlay_png(frame, logo_text, (w - logo_w) // 2, 30)
        titulo_y = 30 + logo_h + 20
    else:
        # Título alternativo si no hay logo
        titulo = "OSEASOFT ARCADE"
        titulo_w = cv2.getTextSize(titulo, cv2.FONT_HERSHEY_DUPLEX, 2.2, 5)[0][0]
        titulo_x = (w - titulo_w) // 2
        
        # Texto con efecto neón
        cv2.putText(frame, titulo, (titulo_x+3, 83), 
                   cv2.FONT_HERSHEY_DUPLEX, 2.2, (150, 50, 200), 8)
        cv2.putText(frame, titulo, (titulo_x, 80), 
                   cv2.FONT_HERSHEY_DUPLEX, 2.2, (255, 150, 255), 5)
        titulo_y = 120
    
    # Calcular posiciones de las cards (2x2)
    card_w = 280
    card_h = 320
    gap = 40
    inicio_x = (w - (2 * card_w + gap)) // 2
    inicio_y = titulo_y + 40
    
    # Dibujar las 4 cards
    for i, juego in enumerate(juegos_disponibles[:4]):
        fila = i // 2
        col = i % 2
        
        x = inicio_x + col * (card_w + gap)
        y = inicio_y + fila * (card_h + gap)
        
        hover = (i == seleccionado)
        dibujar_card(frame, juego, x, y, card_w, card_h, hover, pulse)
    
    # Logo inferior (logo-soft.png)
    if logo_soft is not None:
        logo_h = logo_soft.shape[0]
        logo_w = logo_soft.shape[1]
        overlay_png(frame, logo_soft, 20, h - logo_h - 20)
    
    # Instrucciones en la parte inferior
    instrucciones = [
        "W/A/S/D o Flechas: Navegar",
        "ENTER o ESPACIO: Jugar",
        "1-4: Acceso directo",
        "ESC: Salir"
    ]
    
    inst_y = h - 60
    inst_x = w - 350
    for i, inst in enumerate(instrucciones):
        y = inst_y + i * 20
        cv2.putText(frame, inst, (inst_x, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 180), 1)
    
    return frame

def abrir_juego(juego):
    """Abrir juego en nueva ventana"""
    print(f"\n{'='*50}")
    print(f"ABRIENDO: {juego['nombre']}")
    print(f"Archivo: {juego['archivo']}")
    print(f"{'='*50}")
    
    try:
        resultado = subprocess.run([sys.executable, juego['archivo']])
        
        print(f"\n{'='*50}")
        print(f"Juego cerrado - Código: {resultado.returncode}")
        print(f"{'='*50}\n")
        
    except Exception as e:
        print(f"\nERROR al abrir {juego['nombre']}: {e}\n")

def menu_principal():
    """Loop principal del menú"""
    juegos_disponibles = verificar_juegos()
    
    if not juegos_disponibles:
        print("ERROR: No se encontró ningún juego")
        input("\nPresiona Enter para salir...")
        return
    
    # Cargar logos
    logo_text = cargar_logo('text-soft.png', h_deseada=80)
    logo_soft = cargar_logo('logo-soft.png', h_deseada=100)
    
    if logo_text is None:
        print("⚠ Advertencia: No se encontró 'text-soft.png'")
    if logo_soft is None:
        print("⚠ Advertencia: No se encontró 'logo-soft.png'")
    
    print("Iniciando menú...\n")
    
    # Crear estrellas y galaxias
    w, h = 1400, 900
    estrellas = [Estrella(w, h) for _ in range(200)]
    galaxias = [Galaxia(w, h) for _ in range(5)]
    
    cv2.namedWindow("Oseasoft Arcade", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Oseasoft Arcade", w, h)
    
    seleccionado = 0
    pulse = 0
    
    while True:
        pulse += 0.1
        
        frame = dibujar_menu(seleccionado, juegos_disponibles, estrellas, 
                            galaxias, pulse, logo_text, logo_soft)
        cv2.imshow("Oseasoft Arcade", frame)
        
        key = cv2.waitKey(30) & 0xFF
        
        if key == 27:  # ESC
            break
        
        # Navegación
        elif key in [ord('w'), ord('W'), 82]:  # W o Flecha arriba
            if seleccionado >= 2:
                seleccionado -= 2
        elif key in [ord('s'), ord('S'), 84]:  # S o Flecha abajo
            if seleccionado < len(juegos_disponibles) - 2:
                seleccionado += 2
        elif key in [ord('a'), ord('A'), 81]:  # A o Flecha izquierda
            if seleccionado % 2 == 1:
                seleccionado -= 1
        elif key in [ord('d'), ord('D'), 83]:  # D o Flecha derecha
            if seleccionado % 2 == 0 and seleccionado < len(juegos_disponibles) - 1:
                seleccionado += 1
        
        # Ejecutar juego
        elif key in [13, 32]:  # ENTER o ESPACIO
            cv2.destroyWindow("Oseasoft Arcade")
            abrir_juego(juegos_disponibles[seleccionado])
            cv2.namedWindow("Oseasoft Arcade", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Oseasoft Arcade", w, h)
        
        # Acceso directo 1-4
        elif key >= ord('1') and key <= ord('4'):
            indice = key - ord('1')
            if indice < len(juegos_disponibles):
                cv2.destroyWindow("Oseasoft Arcade")
                abrir_juego(juegos_disponibles[indice])
                cv2.namedWindow("Oseasoft Arcade", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Oseasoft Arcade", w, h)
    
    cv2.destroyAllWindows()
    print("\n¡Hasta luego!\n")

if __name__ == "__main__":
    try:
        print("\n" + "="*50)
        print("     OSEASOFT ARCADE - MENÚ GALAXY")
        print("="*50)
        menu_principal()
    except KeyboardInterrupt:
        print("\n\nInterrumpido por el usuario")
    except Exception as e:
        print(f"\nError: {e}")
        input("Presiona Enter para salir...")