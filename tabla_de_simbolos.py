import re
import pandas as pd

def generar_tabla_simbolos(tokens):
    tabla_simbolos = {}
    id_contador = 500  # ID inicial para identificadores
    palabras_reservadas = {"Iniciar", "Int", "Leer", "Mostrar", "Finalizar", "real", "entero", "Inicio", "Fin", "Escribir"}

    def agregar_a_tabla_simbolos(token, tipo, num_linea, valor=None):
        nonlocal id_contador
        if token not in tabla_simbolos:
            tabla_simbolos[token] = {
                "Tipo": tipo,
                "Id_Token": id_contador,
                "Repeticiones": 1,
                "Lineas": [num_linea],
                "Valor": valor if valor is not None else 0
            }
            id_contador += 1
        else:
            tabla_simbolos[token]["Repeticiones"] += 1
            tabla_simbolos[token]["Lineas"].append(num_linea)
            if valor is not None:
                tabla_simbolos[token]["Valor"] = valor
    
    for token, tipo, num_linea in tokens:
        if token in palabras_reservadas:
            continue  # Ignorar palabras reservadas
        if tipo in ["Numero entero", "Numero flotante"]:
            valor = float(token) if tipo == "Numero flotante" else int(token)
            agregar_a_tabla_simbolos(token, "Real" if tipo == "Numero flotante" else "Entero", num_linea, valor)
        elif tipo == "Identificador":
            agregar_a_tabla_simbolos(token, "Identificador", num_linea)
    
    return tabla_simbolos

# Archivo de prueba
archivo_txt = "codigo.txt"  # Asegúrate de que el archivo existe en la misma carpeta
from tabla_de_tokens import analizar_archivo  # Importamos la función de la tabla de tokens

tokens = analizar_archivo(archivo_txt)
tabla_simbolos = generar_tabla_simbolos(tokens)

# Convertir la tabla de símbolos en un DataFrame
df = pd.DataFrame.from_dict(tabla_simbolos, orient='index', columns=["Tipo", "Id_Token", "Repeticiones", "Lineas", "Valor"])
print(df.to_string())
