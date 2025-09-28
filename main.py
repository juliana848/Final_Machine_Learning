# Punto de entrada
from game import BasketballGamePro

if __name__ == "__main__":
    try:
        game = BasketballGamePro()
        game.run()
    except KeyboardInterrupt:
        print("\nJuego interrumpido! Hasta la proxima!")
    except Exception as e:
        print(f"Error en el juego: {e}")
        print("Verifica tu camara y las librerias instaladas")

