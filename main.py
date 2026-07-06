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
    roi_cinza = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)

    # Borra para minimizar texturas e extraí as bordas
    roi_blur = cv2.GaussianBlur(roi_cinza, (5, 5), 0)
    bordas = cv2.Canny(roi_blur, 50, 150)

    # Usa um filtro de dilatação para conectar bordas próximas desconexas
    kernel = np.ones((3, 3), np.uint8)
    bordas_fechadas = cv2.dilate(bordas, kernel, iterations=1)

    # Transforma as bordas em contornos, pega o maior contorno (em comprimento) e preenche ele com branco
    contornos, _ = cv2.findContours(bordas_fechadas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mascara_roi = np.zeros(roi_cinza.shape, dtype=np.uint8)
    if contornos:
        maior_contorno = max(contornos, key=cv2.contourArea)
        forma_fechada = cv2.convexHull(maior_contorno)
        
        cv2.drawContours(mascara_roi, [forma_fechada], -1, 255, thickness=-1)

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
    cap = cv2.VideoCapture(1)
    
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
    media_cor, desvio_cor = calibracao()
    cap = cv2.VideoCapture(1)
    ret, frame = cap.read()
    if ret:
        altura, largura = frame.shape[:2]
        print(f"Resolução da câmera: {largura}x{altura}")
    camera_painter = CameraPainter(canvas_size = (largura, altura))

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # Chama a detecção
        cx, cy = camera_painter.detect_object(frame, media_cor, desvio_cor, 1)
        
        # Verifica se o objeto foi detectado antes de tentar desenhar
        if cx is not None and cy is not None:
            # Linha vertical
            cv2.line(frame, (cx, 0), (cx, frame.shape[0]), (255, 0, 0), 1)
            # Linha horizontal
            cv2.line(frame, (0, cy), (frame.shape[1], cy), (255, 0, 0), 1)
            # Círculo
            cv2.circle(frame, (cx, cy), 10, (0, 0, 255), -1)
        
        # Exibe o frame com o círculo pintado
        cv2.imshow("Detecao em Tempo Real", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
    