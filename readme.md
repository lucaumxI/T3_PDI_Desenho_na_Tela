# O QUE PRECISA FAZER

Basicamente mexer no `camera_painter.py` e criar um `main.py`:
- `__init__()`: a priori não precisa mexer nisso mas talvez conforme implementa precise;
- `process_frame()`: precisa modificar para desenhar linhas com cores diferentes;
- `detect_object()`: aqui passamos o frame da webcam e ele precisa fazer limiarização de cores (usando HUE ao inves de RGB) para isolar os objetos. Após isolar é só pegar o centro do objeto e retornar as coordenadas (acho que o jeito mais simples é inscrever o objeto em um retângulo e pegar o centro do retângulo mas da para pegar o centro de massa, por exemplo. Ainda daria para usar funções do próprio oOpenCV mas não sei se pode, lembrar de perguntar);
- `draw_line_on_canvas()`: alteração semelhante a do `process_frame()`, as linhas precisam ser desenhadas em duas cores;
- `overlay_canvas()`: mesmo caso do `__init__()`;
- `main.py`: Na main a gente precisa inicializar os dois processos passando as cores dos objetos (cada processo fica responsável por UM objeto), capturar um frame da webcam e passar para ambos processos. Os processos vão fazer a limiarização, calcular o centro dos objetos, traçar uma linha entre o centro do frame $n$ e o frame $n+1$ e retornar um canvas (uma máscara) mostrando onde deve ficar a linha. Por fim a main vai pegar os dois canvas das linhas e sobrepor eles aos frames da webcam traçando a linha com as cores respectivas. Outra coisa a talvez considerar é ao inves de hardcodar o hexa das cores, criar uma etapa de calibração onde pede pro usuário por o objeto no centro da camera e confirmar se o objeto detectado será o usado para desenhar, aí tem como extrair daí as cores direto ao ínves de manualmente passar e também dessa forma da para usar diversos objetos.

## RECOMENDAÇÕES:
Ao ínves de modificar TUDO para lidar com dois objetos e duas cores, cria DOIS processos um para cada objeto e cada um com uma cor. E usa o HUE ao ínves de RGB para não ter trabalho com iluminação.

## Ideias/Implementação feita:

### main.py
Vou fazer uma função de calibração para definir as cores que serão usadas para limiarizar. Basicamente captura e exibe a webcam desenhando um quadrado centralizado, o usuário deixa o objeto centralizado e confirma. A função então captura esse frame após a confirmação e usa esse frame para:
1. Separar o fundo do objeto
2. Extrair a cor do objeto (aqui da pra usar a média dos pixeis do objeto e até usar o desvio padrão daqui mesmo como parametros da limiarização final)


### camera_painter.py