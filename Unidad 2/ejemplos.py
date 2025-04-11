"""
Archivo: ejemplos.py
Descripción: Define los ejemplos de código fuente para procesarlos y generar su correspondiente código intermedio.
"""

def obtener_ejemplos():
    ejemplos = {
        "Ejemplo 1": {
            "codigo_fuente": "a = b + c"
        },
        "Ejemplo 2": {
            "codigo_fuente": "a = (b + c) * d"
        },
        "Ejemplo 3": {
            "codigo_fuente": """if a > b:
    a = a - b
else:
    b = b - a"""
        },
        "Ejemplo 4": {
            "codigo_fuente": """while a < 10:
    a = a + 1"""
        },
        "Ejemplo 5": {
            "codigo_fuente": """sum = 0
i = 0
while i < 10:
    if i % 2 == 0:
        sum = sum + i
    else:
        sum = sum - i
    i = i + 1"""
        }
    }
    return ejemplos
