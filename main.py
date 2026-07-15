import cv2
import numpy as np
import matplotlib.pyplot as plt
from camera_painter import CameraPainter

def mascaramento(frame, coordenadas_roi):
    # Desempacotamento da tupla
    pt_inicial, pt_final = coordenadas_roi
    x_min, y_min = pt_inicial
    x_max, y_max = pt_final

    # Extração do ROI do frame original
    roi_bgr = frame[y_min:y_max, x_min:x_max]
    roi_hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)

    # Borra para minimizar texturas antes do flood fill
    roi_hsv_blur = cv2.GaussianBlur(roi_hsv, (5, 5), 0)

    # Faz um flood fill a partir do ponto central do ROI, expandindo enquanto a cor for parecida
    h, w = roi_bgr.shape[:2]
    semente = (w // 2, h // 2)
    mascara_flood = np.zeros((h + 2, w + 2), dtype=np.uint8)
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8)
    cv2.floodFill(roi_hsv_blur.copy(), mascara_flood, semente, 0, (10, 40, 40), (10, 40, 40), flags)

    # Remove a borda extra de 1px exigida pelo floodFill
    mascara_roi = mascara_flood[1:-1, 1:-1].copy()

    print("O objeto está bem destacado? Aperte 's' para Sim ou 'n' para Não.")
    while True:
        # Exibe o ROI original colorido e a máscara preta e branca
        cv2.imshow("ROI Original", roi_bgr)
        cv2.imshow("Mascara Gerada", mascara_roi)

        # O código trava aqui esperando uma tecla ('0' significa esperar indefinidamente)
        tecla = cv2.waitKey(0) & 0xFF

        if tecla == ord('s'):
            # Destrói apenas as janelinhas de debug
            cv2.destroyWindow("ROI Original")
            cv2.destroyWindow("Mascara Gerada")
            # 4. Retorna os dois para extrairmos a cor no passo seguinte
            return roi_hsv, mascara_roi
            
        elif tecla == ord('n'):
            cv2.destroyWindow("ROI Original")
            cv2.destroyWindow("Mascara Gerada")
            # Retorna None para avisar a função principal que a imagem foi descartada
            return None, None


def calibracao():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Erro ao abrir a câmera.")
        return None, None
    
    print("Câmera aberta. Aperte 'c' para capturar ou 'q' para sair.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Falha ao capturar imagem.")
            break
            
        # Pega a altura e largura do frame para calcular o centro
        h, w = frame.shape[:2]
        
        # Define o tamanho do quadrado
        tamanho_quadrado = 250
        metade = tamanho_quadrado // 2
        
        # Calcula as coordenadas do quadrado centralizado
        ponto_inicial = (w//2 - metade, h//2 - metade) # (X_min, Y_min)
        ponto_final = (w//2 + metade, h//2 + metade)   # (X_max, Y_max)
        
        # Faz uma cópia do frame para desenhar por cima
        frame_exibicao = frame.copy()
        
        # Desenha o quadrado verde: imagem, pt1, pt2, cor(B,G,R), espessura
        cv2.rectangle(frame_exibicao, ponto_inicial, ponto_final, (0, 255, 0), 2)
        
        # Desenha o ponto central, como referência de onde posicionar o objeto
        cv2.circle(frame_exibicao, (w // 2, h // 2), 6, (0, 255, 0), -1)
        
        # Coloca um texto de instrução na tela
        cv2.putText(frame_exibicao, "Posicione o objeto e aperte 'c' para capturar", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Mostra a imagem na janela
        cv2.imshow('Calibracao', frame_exibicao)

        # Espera 1 milissegundo por uma tecla
        tecla = cv2.waitKey(1) & 0xFF
        
        if tecla == ord('c'):
            # Se apertou 'c', fecha a janela e retorna o frame sem o quadrado verde
            # e as coordenadas do ROI
            roi_hsv, mask = mascaramento(frame, (ponto_inicial, ponto_final))

            if roi_hsv is not None:
                cap.release()
                cv2.destroyAllWindows()
                pixels_uteis = roi_hsv[mask == 255]
                media_cor = np.mean(pixels_uteis, axis=0)
                desvio_cor = np.std(pixels_uteis, axis=0)

                print(media_cor)
                print(desvio_cor)

                return media_cor, desvio_cor
            else:
                # O usuário apertou 'n'. Apenas avisa e o laço while da câmera continua rodando normalmente.
                print("Captura descartada. Posicione novamente e aperte 'c'.")
            
        elif tecla == ord('q'):
            # Cancela tudo
            break

    # Libera a câmera se algo der errado ou apertar q
    cap.release()
    cv2.destroyAllWindows()
    return None, None

# Testando a função:
if __name__ == "__main__":
    print("Calibrando o objeto 1 (linha vermelha).")
    media_1, desvio_1 = calibracao()
    print("Calibrando o objeto 2 (linha azul).")
    media_2, desvio_2 = calibracao()

    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        altura, largura = frame.shape[:2]
        print(f"Resolução da câmera: {largura}x{altura}")

    # Um CameraPainter para cada objeto, cada um com seu próprio canvas
    painter_1 = CameraPainter(canvas_size=(altura, largura))
    painter_2 = CameraPainter(canvas_size=(altura, largura))

    while True:
        ret, frame = cap.read()
        if not ret: break
        
    # Fator de suavização (0.0 a 1.0). Quanto menor, mais suave e com mais atraso.
        alpha = 0.3 

        # --- OBJETO 1 ---
        cx1, cy1 = painter_1.detect_object(frame, media_1, desvio_1, 1)
        if cx1 is not None and cy1 is not None:
            if painter_1.prev_p is not None:
                prev_cx, prev_cy = painter_1.prev_p
                
                # Cálculo do EMA
                cx1_suave = int(alpha * cx1 + (1 - alpha) * prev_cx)
                cy1_suave = int(alpha * cy1 + (1 - alpha) * prev_cy)
                ponto_1_suave = (cx1_suave, cy1_suave)
                
                painter_1.draw_line_on_canvas(painter_1.canvas, painter_1.prev_p, ponto_1_suave, color=(0, 0, 255))
                # Atualiza com o ponto suavizado para o próximo cálculo
                painter_1.prev_p = ponto_1_suave
            else:
                # Primeiro frame, não há histórico para suavizar
                painter_1.prev_p = (cx1, cy1)
        else:
            painter_1.prev_p = None

        # --- OBJETO 2 ---
        cx2, cy2 = painter_2.detect_object(frame, media_2, desvio_2, 1)
        if cx2 is not None and cy2 is not None:
            if painter_2.prev_p is not None:
                prev_cx, prev_cy = painter_2.prev_p
                
                # Cálculo do EMA
                cx2_suave = int(alpha * cx2 + (1 - alpha) * prev_cx)
                cy2_suave = int(alpha * cy2 + (1 - alpha) * prev_cy)
                ponto_2_suave = (cx2_suave, cy2_suave)
                
                painter_2.draw_line_on_canvas(painter_2.canvas, painter_2.prev_p, ponto_2_suave, color=(255, 0, 0))
                # Atualiza com o ponto suavizado para o próximo cálculo
                painter_2.prev_p = ponto_2_suave
            else:
                # Primeiro frame, não há histórico para suavizar
                painter_2.prev_p = (cx2, cy2)
        else:
            painter_2.prev_p = None
        
        # Sobrepõe os dois canvas no frame
        frame_com_desenho_1 = painter_1.overlay_canvas(frame, painter_1.canvas)
        display_img = painter_2.overlay_canvas(frame_com_desenho_1, painter_2.canvas)
        
        # Exibe o frame com as linhas pintadas
        cv2.imshow("Detecao em Tempo Real", display_img)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break