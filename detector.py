# detector.py
# Este archivo se encarga de inicializar el detector de manos usando cvzone,
# que por dentro utiliza MediaPipe (modelo de manos ya embebido).

from cvzone.HandTrackingModule import HandDetector

class HandTracker:
    def __init__(self, maxHands=1, detectionCon=0.8):
        """
        maxHands: número máximo de manos a detectar por cámara.
        detectionCon: confianza mínima para considerar detección.
        """
        self.detector = HandDetector(maxHands=maxHands, detectionCon=detectionCon)

    def findHands(self, img):
        """
        Detecta las manos en un frame de OpenCV.
        Devuelve: imagen anotada, lista de manos detectadas.
        """
        hands, img = self.detector.findHands(img)  # detecta manos y dibuja landmarks
        return img, hands
