"""Script que implementa a classe CameraPainter, que é responsável por criar um sistema de
desenho na tela usando a webcam.
"""

import cv2
import numpy as np


class CameraPainter:
    """Classe que implementa um sistema de desenho na tela usando a webcam."""

    def __init__(self, canvas_size):
        """Inicializa o sistema de desenho. canvas_size define o tamanho do canvas onde o desenho
        será armazenado. Idealmente, o canvas deve ter o mesmo tamanho dos quadros capturados pela 
        webcam.
        """

        # Imagem no qual o desenho é armazenado
        self.canvas = np.zeros((canvas_size[0], canvas_size[1], 3), dtype=np.uint8)
        self.prev_p = None

    def process_frame(self, frame):

        coords = self.detect_object(frame)
        if self.prev_p is None:
            # Primeira detecção, apenas armazena as coordenadas
            self.prev_p = coords
        else:
            # Desenha uma linha entre a posição anterior e a nova posição do objeto
            self.draw_line_on_canvas(self.canvas, self.prev_p, coords)

        self.prev_p = coords
        display_img = self.overlay_canvas(frame, self.canvas)

        return display_img

    def detect_object(self, frame, media, desvio, fator):
        # 1. Converte o frame para HSV antes de comparar
        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        lower = np.clip(media - (fator * desvio), 0, 255)
        upper = np.clip(media + (fator * desvio), 0, 255)
        
        # 2. Aplica a limiarização
        mask_bool = (frame_hsv >= lower) & (frame_hsv <= upper)
        mascara = np.all(mask_bool, axis=2).astype(np.uint8) * 255
        
        # --- DEBUG: PLOTAR MÁSCARA ---
        # Resize apenas para exibir maior, se precisar (opcional)
        cv2.imshow("Debug Mascara", mascara)
        cv2.waitKey(1) 
        # -----------------------------
        
        indices_linhas, indices_colunas = np.where(mascara == 255)

        # 3. Proteção contra o objeto sumir da tela
        if indices_colunas.size > 50 and indices_linhas.size > 50:
            # A média de TODAS as posições x e y ativas resulta no centro de massa real
            cx = int(np.mean(indices_colunas))
            cy = int(np.mean(indices_linhas))
            return cx, cy
        else:
            return None, None

    def draw_line_on_canvas(self, canvas, p1, p2, color=(0, 255, 0), thickness=2):
        """Desenha uma linha entre os pontos p1 e p2 no canvas."""
        cv2.line(canvas, p1, p2, color, thickness)

    def overlay_canvas(self, base_img, canvas):
        """Sobrepõe o canvas sobre a imagem base."""

        # Cria uma máscara onde o canvas tem pixels diferentes de preto (0, 0, 0)
        mask = np.any(canvas != [0, 0, 0], axis=-1, keepdims=True)
        
        # Usa a máscara para combinar o canvas e a imagem base. Onde a máscara é True, usamos o 
        # pixel do canvas. Caso contrário, usamos o pixel da imagem base.
        result = np.where(mask, canvas, base_img)
        
        return result