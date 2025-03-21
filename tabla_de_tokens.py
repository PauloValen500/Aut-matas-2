import re
import pandas as pd

def obtener_config():
    """
    Devuelve un diccionario con la configuración utilizada en el análisis léxico.
    """
    config = {
        "ARCHIVO_FUENTE": "/Users/aldomoreno/Desktop/Proyectos Automatas II/Aut-matas-2/codigo2.txt",
        "PALABRAS_RESERVADAS": {"Iniciar", "Int", "Real", "Leer", "Mostrar", "Finalizar"},
        "SIMBOLOS_ESPECIALES": {"(", ")", "{", "}", ";", ","},
        "OPERADORES_ARITMETICOS": {"+", "-", "*", "/"},
        "SIMBOLO_ASIGNACION": {"="}
    }
    return config

def analizar_archivo(archivo):
    """
    Analiza el archivo fuente y devuelve una lista de tokens.
    Cada token se representa como una tupla: (token, tipo, línea)
    """
    # Definir expresiones regulares para identificar tokens
    patron_identificador = re.compile(r'^[a-zA-Z_]\w*$')
    patron_flotante = re.compile(r'^\d+\.\d+$')   # Al menos un dígito antes y después del punto
    patron_entero = re.compile(r'^\d+$')
    
    # Obtener la configuración necesaria
    config = obtener_config()
    palabras_reservadas = config["PALABRAS_RESERVADAS"]
    simbolos_especiales = config["SIMBOLOS_ESPECIALES"]
    operadores_aritmeticos = config["OPERADORES_ARITMETICOS"]
    simbolo_asignacion = config["SIMBOLO_ASIGNACION"]
    
    resultados = []
    with open(archivo, 'r') as f:
        for num_linea, linea in enumerate(f, start=1):
            # Buscar números decimales, palabras y símbolos especiales
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

if __name__ == '__main__':
    config = obtener_config()
    archivo = config["ARCHIVO_FUENTE"]
    tokens = analizar_archivo(archivo)
    
    # Imprimir la tabla de tokens usando pandas
    df_tokens = pd.DataFrame(tokens, columns=["Token", "Tipo", "Linea"])
    print("Tabla de Tokens:")
    print(df_tokens.to_string(index=False))
