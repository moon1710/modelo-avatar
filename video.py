import tkinter as tk
from tkvideo import tkvideo

# Crear la ventana principal
root = tk.Tk()
root.title("Video Idle")

# Crear un Label para mostrar el video
video_label = tk.Label(root)
video_label.pack()

# Configurar el reproductor de video
# "idle_video.mp4" debe estar en la misma carpeta que este script o especificar la ruta completa
player = tkvideo("./assets/idle_video.mp4", video_label, loop=1, size=(300, 300))
player.play()

# Ejecutar el loop principal de Tkinter
root.mainloop()
