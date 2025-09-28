#Sistema de efectos y partículas
# Explosiones de partículas cuando se anota una canasta
# Confetti para celebraciones al final del juego
# Física realista con gravedad para ambos tipos de efectos
# Gestión de memoria eliminando partículas cuando expiran
# Funciones de limpieza para reiniciar efectos
import cv2
import numpy as np

class EffectsManager:
    def __init__(self, colors):
        self.colors = colors
        self.particle_systems = []
        self.confetti_particles = []

    def create_particle_explosion(self, x, y, color, count=20):
        """Crear explosión de partículas en una posición específica"""
        for _ in range(count):
            particle = {
                'x': x + np.random.randint(-15, 15),
                'y': y + np.random.randint(-15, 15),
                'vx': np.random.uniform(-10, 10),
                'vy': np.random.uniform(-15, -5),
                'life': 80,
                'max_life': 80,
                'color': color,
                'size': np.random.randint(4, 10)
            }
            self.particle_systems.append(particle)

    def create_confetti(self, count=50):
        """Crear confetti para celebraciones"""
        width = 1280
        colors = [self.colors['accent'], self.colors['success'], self.colors['neon_blue'],
                 self.colors['neon_green'], self.colors['purple']]

        for _ in range(count):
            particle = {
                'x': np.random.randint(0, width),
                'y': np.random.randint(-50, 0),
                'vx': np.random.uniform(-3, 3),
                'vy': np.random.uniform(2, 8),
                'life': np.random.randint(180, 300),
                'max_life': 300,
                'color': colors[np.random.randint(0, len(colors))],
                'size': np.random.randint(4, 12),
                'rotation': np.random.uniform(0, 360),
                'rotation_speed': np.random.uniform(-10, 10)
            }
            self.confetti_particles.append(particle)

    def update_particles(self):
        """Actualizar física de las partículas de explosión"""
        for particle in self.particle_systems[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.4  # Gravedad
            particle['life'] -= 1

            if particle['life'] <= 0:
                self.particle_systems.remove(particle)

    def update_confetti(self):
        """Actualizar física del confetti"""
        for particle in self.confetti_particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.2  # Gravedad más suave
            particle['rotation'] += particle['rotation_speed']
            particle['life'] -= 1

            if particle['life'] <= 0 or particle['y'] > 720:
                self.confetti_particles.remove(particle)

    def draw_particles(self, img):
        """Dibujar partículas de explosión"""
        for particle in self.particle_systems:
            alpha = particle['life'] / particle['max_life']
            size = int(particle['size'] * alpha)
            if size > 0:
                cv2.circle(img, (int(particle['x']), int(particle['y'])),
                          size, particle['color'], -1)

    def draw_confetti(self, img):
        """Dibujar confetti"""
        for particle in self.confetti_particles:
            alpha = particle['life'] / particle['max_life']
            size = int(particle['size'] * alpha)
            if size > 0:
                x, y = int(particle['x']), int(particle['y'])
                pts = np.array([
                    [x-size//2, y-size//4],
                    [x+size//2, y-size//4],
                    [x+size//2, y+size//4],
                    [x-size//2, y+size//4]
                ], np.int32)
                cv2.fillPoly(img, [pts], particle['color'])

    def clear_particles(self):
        """Limpiar todas las partículas de explosión"""
        self.particle_systems.clear()

    def clear_confetti(self):
        """Limpiar todo el confetti"""
        self.confetti_particles.clear()

    def clear_all_effects(self):
        """Limpiar todos los efectos"""
        self.clear_particles()
        self.clear_confetti()