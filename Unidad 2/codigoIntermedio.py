"""
Archivo: codigoIntermedio.py
Descripción: Convierte el código fuente a un código intermedio
El resultado se muestra en consola y se guarda en un archivo de texto.
"""

import os
from ejemplos import obtener_ejemplos

def convertir_linea_simple(line, temp_counter):
    """
    Convierte una línea simple de asignación en código intermedio.
    - Si la expresión involucra un operador aritmético, genera un temporal.
    - De lo contrario, sólo asigna directamente.
    Retorna:
      - lista de líneas de código intermedio,
      - el contador de temporales actualizado.
    """
    if "=" in line:
        var, expr = line.split("=", 1)
        var = var.strip()
        expr = expr.strip()
        # Si la expresión contiene operadores aritméticos se genera un temporal
        if any(op in expr for op in ["+", "-", "*", "/"]):
            temp = f"t{temp_counter}"
            temp_counter += 1
            code = [f"{temp} = {expr}", f"{var} = {temp}"]
            return code, temp_counter
        else:
            code = [f"{var} = {expr}"]
            return code, temp_counter
    else:
        # Si no hay '=', devolvemos la línea tal cual, pero en 3 direcciones normalmente
        return ([line], temp_counter)

def contar_indent(line):
    """
    Retorna la cantidad de espacios al inicio de la línea
    para determinar la indentación y saber qué bloque pertenece.
    """
    return len(line) - len(line.lstrip(" "))

def procesar_bloque(lines, start, current_indent, temp_counter, label_counter):
    """
    Procesa recursivamente un bloque de líneas cuya indentación es >= current_indent.
    Se soportan las estructuras:
        if ...:
        else:
        while ...:
    y las asignaciones simples.
    
    Retorna una tupla:
      (codigo_generado, indice_siguiente, temp_counter, label_counter)
    """
    codigo = []
    i = start
    while i < len(lines):
        # Salta líneas en blanco
        if not lines[i].strip():
            i += 1
            continue

        indent = contar_indent(lines[i])
        # Si la línea actual tiene indentación menor que current_indent,
        # entonces finaliza este bloque.
        if indent < current_indent:
            break

        stripped = lines[i].strip()

        # Copiar comentarios directamente
        if stripped.startswith("//"):
            codigo.append(stripped)
            i += 1
            continue

        # Detectar "if ...:" sin else en la misma línea
        if stripped.startswith("if ") and stripped.endswith(":"):
            bloque_if, i, temp_counter, label_counter = procesar_if_else(lines, i, current_indent, temp_counter, label_counter)
            codigo.extend(bloque_if)
            continue

        # Detectar "else:" (puede suceder cuando se está anidado)
        if stripped == "else:":
            # *Teóricamente* no se debería encontrar un else suelto sin un if anterior,
            # pero lo manejamos en procesar_if_else. Aquí, si aparece, lo ignoramos y
            # procesamos el bloque como un fallback:
            i += 1
            continue

        # Detectar "while ...:"
        if stripped.startswith("while ") and stripped.endswith(":"):
            bloque_while, i, temp_counter, label_counter = procesar_while(lines, i, current_indent, temp_counter, label_counter)
            codigo.extend(bloque_while)
            continue

        # Si no es if/else/while, tratamos como asignación o instrucción simple
        line_code, temp_counter = convertir_linea_simple(stripped, temp_counter)
        codigo.extend(line_code)
        i += 1

    return codigo, i, temp_counter, label_counter

def procesar_if_else(lines, index, current_indent, temp_counter, label_counter):
    """
    Procesa una estructura if-else, transformándola a un código intermedio de la forma:
       if not (cond) goto L_FALSE
       [rama verdadera]
       goto L_END
       L_FALSE:
       [rama falsa]
       L_END:
    Considera que la parte else: es opcional.
    """
    codigo = []
    stripped = lines[index].strip()
    # Extraer la condición (sin "if" ni ":")
    condition = stripped[3:].rstrip(":").strip()
    # Reemplazar "= =" por "==" (espacios)
    condition = condition.replace("= =", "==")
    index += 1

    # Definir etiquetas
    L_false = f"L{label_counter}"
    label_counter += 1
    L_end = f"L{label_counter}"
    label_counter += 1

    # if not (cond) goto L_false
    codigo.append(f"if not ({condition}) goto {L_false}")

    # Procesar rama verdadera (bloque indentado)
    true_block, index, temp_counter, label_counter = procesar_bloque(lines, index, current_indent + 4, temp_counter, label_counter)
    codigo.extend(true_block)

    # Salto al final
    codigo.append(f"goto {L_end}")

    # Verificar si la siguiente línea es un else:
    # (esto se detecta si la indentación del else es igual a current_indent
    #  y la línea empieza con "else:")
    if index < len(lines):
        # Revisar la indentación:
        if lines[index].strip().startswith("else:"):
            # Consumir la línea "else:"
            index += 1
            # Procesar bloque de la rama falsa
            codigo.append(f"{L_false}:")
            false_block, index, temp_counter, label_counter = procesar_bloque(lines, index, current_indent + 4, temp_counter, label_counter)
            codigo.extend(false_block)
        else:
            # No hay else:
            codigo.append(f"{L_false}:")
    else:
        # Se llegó al final sin else
        codigo.append(f"{L_false}:")

    # Etiqueta final
    codigo.append(f"{L_end}:")
    return codigo, index, temp_counter, label_counter

def procesar_while(lines, index, current_indent, temp_counter, label_counter):
    """
    Procesa una estructura while:
      while cond:
         ...
    => se traduce a:
       L_START:
         if not (cond) goto L_EXIT
         ...
         goto L_START
       L_EXIT:
    """
    codigo = []
    stripped = lines[index].strip()
    # Extraer condición (sin "while" ni ":")
    condition = stripped[6:].rstrip(":").strip()
    condition = condition.replace("= =", "==")
    index += 1

    L_start = f"L{label_counter}"
    label_counter += 1
    L_exit = f"L{label_counter}"
    label_counter += 1

    # Etiqueta de inicio
    codigo.append(f"{L_start}:")
    # if not (cond) goto L_exit
    codigo.append(f"if not ({condition}) goto {L_exit}")

    # Procesar el cuerpo del while
    body, index, temp_counter, label_counter = procesar_bloque(lines, index, current_indent + 4, temp_counter, label_counter)
    codigo.extend(body)

    # Saltar al inicio
    codigo.append(f"goto {L_start}")
    # Etiqueta de salida
    codigo.append(f"{L_exit}:")
    return codigo, index, temp_counter, label_counter

def convertir_a_intermedio(codigo_fuente):
    """
    Convierte el código fuente en estilo Python a código intermedio de tres direcciones,
    manejando if, else, while, asignaciones y comentarios.
    """
    lines = codigo_fuente.splitlines()
    codigo, _, temp_counter, label_counter = procesar_bloque(lines, 0, 0, 1, 1)
    return codigo

def procesar_ejemplos(ejemplos):
    """
    Convierte cada ejemplo de código fuente a su código intermedio.
    Devuelve un diccionario con 'codigo_fuente' y 'codigo_intermedio'.
    """
    resultado = {}
    for clave, contenido in ejemplos.items():
        fuente = contenido["codigo_fuente"]
        intermedio = convertir_a_intermedio(fuente)
        resultado[clave] = {
            "codigo_fuente": fuente,
            "codigo_intermedio": intermedio
        }
    return resultado

def mostrar_ejemplos(ejemplos):
    """
    Muestra por consola el código fuente y el código intermedio resultante.
    """
    for clave, contenido in ejemplos.items():
        print(f"--- {clave} ---")
        print("Código Fuente:")
        print(contenido["codigo_fuente"])
        print("Código Intermedio:")
        for linea in contenido["codigo_intermedio"]:
            print("   " + linea)
        print()

def guardar_codigo_intermedio(ejemplos, nombre_archivo="codigo_intermedio.txt"):
    """
    Guarda en un archivo de texto el código intermedio de cada ejemplo.
    """
    try:
        directorio = os.path.dirname(os.path.abspath(__file__))
        ruta_archivo = os.path.join(directorio, nombre_archivo)
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            for clave, contenido in ejemplos.items():
                f.write(f"--- {clave} ---\n")
                f.write("Código Intermedio:\n")
                for linea in contenido["codigo_intermedio"]:
                    f.write("   " + linea + "\n")
                f.write("\n")
        print(f"\nCódigo intermedio guardado en: {ruta_archivo}")
    except Exception as e:
        print("Error al guardar el archivo:", e)

def main():
    """
    Función principal:
      1. Obtiene los ejemplos (sólo con código fuente).
      2. Convierte cada uno a código intermedio.
      3. Lo muestra y guarda en un archivo de texto.
    """
    directorio_script = os.path.dirname(os.path.abspath(__file__))
    print("Directorio donde se guardará el archivo:", directorio_script)
    print("Iniciando la conversión a código intermedio...\n")

    # Cargar los ejemplos
    ejemplos = obtener_ejemplos()
    # Procesar los ejemplos
    ejemplos_procesados = procesar_ejemplos(ejemplos)
    # Mostrar en consola
    mostrar_ejemplos(ejemplos_procesados)
    # Guardar en un archivo de texto
    guardar_codigo_intermedio(ejemplos_procesados)

if __name__ == "__main__":
    main()
