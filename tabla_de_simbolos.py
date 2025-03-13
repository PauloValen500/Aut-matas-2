import re
import pandas as pd
from tabla_de_tokens import analizar_archivo

def generar_tabla_simbolos(tokens):
    """
    Genera la tabla de símbolos a partir de la lista de tokens.
    Cada entrada tiene:
      - Tipo: (Entero, Real, Identificador o Error)
      - Id_Token: identificador numérico único (inicia en 500)
      - Repeticiones: cantidad de apariciones
      - Lineas: lista de líneas donde aparece
      - Valor: valor literal en caso de números o el string de la expresión para asignaciones complejas; 0 para variables sin asignar
      - Asignado: indica si la variable recibió una asignación
      - Errores: lista de mensajes de error asociados al token
      - EsVariable: True si el token corresponde a una variable, False si es un literal numérico
    """
    tabla_simbolos = {}
    id_contador = 500  # ID inicial

    # Palabras reservadas a omitir (excepto las que declaran el tipo)
    # Se consideran válidas las declaraciones con "Int", "real" y "float"
    reservadas_omitir = {"Iniciar", "Leer", "Mostrar", "Finalizar"}
    
    def agregar(token, tipo, num_linea, valor=None, error_msg=None, es_variable=True):
        nonlocal id_contador
        if token in tabla_simbolos:
            tabla_simbolos[token]["Repeticiones"] += 1
            tabla_simbolos[token]["Lineas"].append(num_linea)
            if error_msg:
                tabla_simbolos[token]["Errores"].append(f"Línea {num_linea}: {error_msg}")
        else:
            tabla_simbolos[token] = {
                "Tipo": tipo,
                "Id_Token": id_contador,
                "Repeticiones": 1,
                "Lineas": [num_linea],
                "Valor": valor if valor is not None else 0,
                "Asignado": False,    # Indica si la variable recibió asignación
                "Errores": [],        # Lista de errores asociados
                "EsVariable": es_variable
            }
            if error_msg:
                tabla_simbolos[token]["Errores"].append(f"Línea {num_linea}: {error_msg}")
            id_contador += 1

    last_declared_type = None  # Guarda el tipo en la declaración actual

    i = 0
    while i < len(tokens):
        token, tipo_token, num_linea = tokens[i]

        # Omitir "PROGRAMA"
        if token.upper() == "PROGRAMA":
            i += 1
            continue

        # Delimitadores: coma y punto y coma
        if token in {",", ";"}:
            if token == ";":
                last_declared_type = None  # Fin de declaración
            i += 1
            continue

        # Declaración de tipo válida: "Int", "real" o "float"
        if token in {"Int", "eal", "float"}:
            if token == "Int":
                last_declared_type = "Entero"
            else:
                last_declared_type = "Real"
            i += 1
            continue

        # Omitir otras palabras reservadas
        if token in reservadas_omitir:
            i += 1
            continue

        # Procesamiento de asignación: detecta el token "="
        if tipo_token == "Asignacion":
            # Se espera que el token anterior sea el identificador
            if i - 1 >= 0:
                id_token, id_tipo, id_line = tokens[i - 1]
            else:
                i += 1
                continue

            # Ahora se reúne la expresión completa desde el token siguiente hasta el ";".
            j = i + 1
            expr_tokens = []
            while j < len(tokens) and tokens[j][0] != ";":
                expr_tokens.append(tokens[j])
                j += 1
            # Si no se encontraron tokens en la expresión, se marca error (aunque ahora se permite expresiones complejas)
            if not expr_tokens:
                if id_token in tabla_simbolos:
                    agregar(id_token, tabla_simbolos[id_token]["Tipo"], num_linea,
                            error_msg="Error sintáctico: Falta valor en la asignación")
                else:
                    agregar(id_token, "Error", num_linea,
                            error_msg="Error sintáctico: Falta valor en la asignación")
                i = j
                continue

            # Si la expresión consta de un único token que es numérico, se procede como antes.
            if len(expr_tokens) == 1 and expr_tokens[0][1] in ["Numero entero", "Numero flotante"]:
                literal_token, literal_tipo, lit_line = expr_tokens[0]
                if literal_tipo == "Numero flotante":
                    valor = float(literal_token)
                    valor_tipo = "Real"
                else:
                    valor = int(literal_token)
                    valor_tipo = "Entero"
                # Verificar coherencia semántica
                if id_token in tabla_simbolos:
                    decl_tipo = tabla_simbolos[id_token]["Tipo"]
                    if decl_tipo == "Entero" and valor_tipo == "Real":
                        agregar(id_token, decl_tipo, num_linea, valor,
                                error_msg=f"Error semántico: Variable '{id_token}' declarada como Entero no puede recibir un valor Real")
                    else:
                        tabla_simbolos[id_token]["Valor"] = valor
                        tabla_simbolos[id_token]["Asignado"] = True
                else:
                    agregar(id_token, "Error", num_linea,
                            error_msg=f"Error semántico: Variable '{id_token}' usada sin declaración")
            else:
                # La expresión es compleja. Se reconstruye como string.
                expr_str = " ".join(tok for tok, t, nl in expr_tokens)
                # Heurística simple: si algún token tiene un punto, se considera Real.
                expr_type = "Entero"
                for tok, t, nl in expr_tokens:
                    if t == "Numero flotante" or "." in tok:
                        expr_type = "Real"
                        break
                # Verificar coherencia con la declaración
                if id_token in tabla_simbolos:
                    decl_tipo = tabla_simbolos[id_token]["Tipo"]
                    if decl_tipo == "Entero" and expr_type == "Real":
                        agregar(id_token, decl_tipo, num_linea, valor=expr_str,
                                error_msg=f"Error semántico: Variable '{id_token}' declarada como Entero no puede recibir un valor Real")
                    else:
                        tabla_simbolos[id_token]["Valor"] = expr_str
                        tabla_simbolos[id_token]["Asignado"] = True
                else:
                    agregar(id_token, "Error", num_linea,
                            error_msg=f"Error semántico: Variable '{id_token}' usada sin declaración")
            i = j  # Continuar desde el delimitador
            continue

        # Procesamiento de literales numéricos (no parte de asignaciones)
        if tipo_token in ["Numero entero", "Numero flotante"]:
            if tipo_token == "Numero flotante":
                valor = float(token)
                num_tipo = "Real"
            else:
                valor = int(token)
                num_tipo = "Entero"
            # Los literales se marcan como no variables.
            agregar(token, num_tipo, num_linea, valor, es_variable=False)
            last_declared_type = None
            i += 1
            continue

        # Procesamiento de identificadores
        if tipo_token == "Identificador":
            if last_declared_type is not None:
                agregar(token, last_declared_type, num_linea)
            else:
                if token not in tabla_simbolos:
                    agregar(token, "Error", num_linea,
                            error_msg=f"Error semántico: Variable '{token}' usada sin declaración")
                else:
                    agregar(token, tabla_simbolos[token]["Tipo"], num_linea)
            if i + 1 < len(tokens):
                siguiente_token, _, _ = tokens[i + 1]
                if siguiente_token != ",":
                    last_declared_type = None
            else:
                last_declared_type = None
            i += 1
            continue

        # Para cualquier otro token, reiniciar el estado de declaración.
        last_declared_type = None
        i += 1

    # Verificar variables (solo las declaradas como variables) que nunca recibieron asignación.
    for var, info in tabla_simbolos.items():
        if info["EsVariable"] and info["Tipo"] in ["Entero", "Real"] and not info["Asignado"]:
            info["Errores"].append(f"Línea {info['Lineas'][0]}: Variable '{var}' declarada pero no asignada")

    return tabla_simbolos

if __name__ == '__main__':
    # Ruta al archivo fuente (ajustar según corresponda)
    archivo_txt = "./codigo.txt"
    
    # Obtener la lista de tokens
    tokens = analizar_archivo(archivo_txt)
    
    # Generar la tabla de símbolos a partir de los tokens
    tabla_simbolos = generar_tabla_simbolos(tokens)
    
    # Crear un DataFrame para la tabla de símbolos sin la columna de errores
    columnas_tabla = ["Tipo", "Id_Token", "Repeticiones", "Lineas", "Valor"]
    df = pd.DataFrame.from_dict(tabla_simbolos, orient='index', columns=columnas_tabla)
    print("\n")
    print(df.to_string())
    
    # Recopilar e imprimir los errores detectados (cada error en una línea)
    print("\nErrores detectados:")
    errores_totales = []
    for info in tabla_simbolos.values():
        if info["Errores"]:
            errores_totales.extend(info["Errores"])
    if errores_totales:
        for error in errores_totales:
            print(error)
    else:
        print("No se detectaron errores.")
