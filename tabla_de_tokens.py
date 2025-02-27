import re
import pandas as pd

def analizar_archivo(archivo):
    # Definir las categorías de tokens
    palabras_reservadas = {"Iniciar", "Int", "Leer", "Mostrar", "Finalizar"}
    simbolos_especiales = {"(", ")", "{", "}", ";", ","}
    operadores_aritmeticos = {"+", "-", "*", "/"}
    simbolo_asignacion = {"="}
    
    # Expresiones regulares para los tokens
    patron_identificador = re.compile(r'^[a-zA-Z_]\w*$')
    patron_flotante = re.compile(r'^\d+\.\d+$')  # Asegura al menos un número antes y después del punto
    patron_entero = re.compile(r'^\d+$')

    resultados = []
    
    with open(archivo, 'r') as f:
        for num_linea, linea in enumerate(f, start=1):
            # Modificación en la expresión regular para reconocer números decimales correctamente
            tokens = re.findall(r'\d+\.\d+|\w+|[+\-*/=<>!(){};,]', linea)  

            for token in tokens:
                if token in palabras_reservadas:
                    tipo = "Palabra reservada"
                elif token in simbolos_especiales:
                    tipo = "Simbolo especial"
                elif token in operadores_aritmeticos:
                    tipo = "Operador aritmetico"
                elif token in simbolo_asignacion:
                    tipo = "Asignacion"
                elif patron_flotante.match(token):
                    tipo = "Numero flotante"
                elif patron_entero.match(token):
                    tipo = "Numero entero"
                elif patron_identificador.match(token):
                    tipo = "Identificador"
                else:
                    tipo = "Desconocido"
                
                resultados.append((token, tipo, num_linea))
    
    return resultados

# Archivo de prueba
archivo_txt = "codigo.txt"  # Asegúrate de que el archivo existe en la misma carpeta
resultados = analizar_archivo(archivo_txt)

# Mostrar en forma de tabla
df = pd.DataFrame(resultados, columns=["Token", "Tipo", "Linea"])
print(df.to_string(index=False))
