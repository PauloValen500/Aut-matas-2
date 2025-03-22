import re
import sys
import pandas as pd
from tabla_de_tokens import obtener_config, analizar_archivo

########################################
# GENERACIÓN DE LA TABLA DE SÍMBOLOS
########################################
def generar_tabla_simbolos(tokens):
    """
    Genera la tabla de símbolos a partir de la lista de tokens.

    Cada entrada contiene:
      - Tipo: (Entero, Real, Identificador o Error)
      - Id_Token: Para literales numéricos es igual al valor numérico;
                  para variables se asigna un valor incremental (inicia en 500)
      - Repeticiones: Número de apariciones del token
      - Lineas: Lista de líneas donde aparece el token
      - Valor: Valor literal (para números) o la cadena de la expresión asignada;
               para variables sin asignación se usa 0
      - Asignado: Indica si la variable recibió asignación
      - Errores: Lista de mensajes de error asociados (incluyendo la línea)
      - EsVariable: True si es variable, False si es literal numérico

    Se realizan las siguientes comprobaciones:
      1. Se omite el token que aparece inmediatamente después de "Iniciar" si ese token no es una palabra reservada.
      2. Para cada asignación/expresión aritmética se recogen los tipos de los operandos numéricos
         y se verifica que sean iguales. Si no lo son se marca un error semántico (indicando la línea)
         y se termina el análisis.
    """
    tabla_simbolos = {}
    id_contador = 500  # Para variables, el Id_Token inicia en 500

    config = obtener_config()
    palabras_reservadas = {p.upper() for p in config["PALABRAS_RESERVADAS"]}
    reservadas_omitir = {"Leer", "Mostrar", "Finalizar"}

    def agregar(token, tipo, num_linea, valor=None, error_msg=None, es_variable=True):
        nonlocal id_contador
        if not es_variable:
            if valor == 0:
                return
            nuevo_id = valor  # Para literales, el id es su valor numérico
        else:
            nuevo_id = id_contador

        if token in tabla_simbolos:
            tabla_simbolos[token]["Repeticiones"] += 1
            tabla_simbolos[token]["Lineas"].append(num_linea)
            if error_msg:
                tabla_simbolos[token]["Errores"].append(f"Línea {num_linea}: {error_msg}")
        else:
            tabla_simbolos[token] = {
                "Tipo": tipo,
                "Id_Token": nuevo_id,
                "Repeticiones": 1,
                "Lineas": [num_linea],
                "Valor": valor if valor is not None else 0,
                "Asignado": False,
                "Errores": [],
                "EsVariable": es_variable
            }
            if error_msg:
                tabla_simbolos[token]["Errores"].append(f"Línea {num_linea}: {error_msg}")
            if es_variable:
                id_contador += 1

    last_declared_type = None
    i = 0
    while i < len(tokens):
        if i > 0 and tokens[i-1][0].upper() == "INICIAR" and tokens[i][0].upper() not in palabras_reservadas:
            i += 1
            continue

        token, tipo_token, num_linea = tokens[i]
        if token.upper() in {"PROGRAMA", "INICIAR"}:
            i += 1
            continue
        if token in {",", ";"}:
            if token == ";":
                last_declared_type = None
            i += 1
            continue
        if token in {"Int", "Real", "float"}:
            last_declared_type = "Entero" if token == "Int" else "Real"
            i += 1
            continue
        if token in reservadas_omitir:
            i += 1
            continue

        if tipo_token == "Asignacion":
            if i - 1 >= 0:
                id_token, id_tipo, id_line = tokens[i - 1]
            else:
                i += 1
                continue

            j = i + 1
            expr_tokens = []
            while j < len(tokens) and tokens[j][0] != ";":
                expr_tokens.append(tokens[j])
                j += 1

            operand_types = []
            for tok_expr, tipo_expr, linea_expr in expr_tokens:
                if tipo_expr in ["Numero entero", "Numero flotante"]:
                    operand_types.append("Entero" if tipo_expr == "Numero entero" else "Real")
            if operand_types and len(set(operand_types)) > 1:
                agregar(id_token,
                        tabla_simbolos[id_token]["Tipo"] if id_token in tabla_simbolos else "Error",
                        num_linea,
                        error_msg="Error semántico: Operandos de la expresión tienen tipos incompatibles")
                return tabla_simbolos

            for tok_expr, tipo_expr, linea_expr in expr_tokens:
                if tipo_expr in ["Numero entero", "Numero flotante"]:
                    valor_literal = float(tok_expr) if tipo_expr == "Numero flotante" else int(tok_expr)
                    if valor_literal != 0:
                        if tok_expr not in tabla_simbolos:
                            agregar(tok_expr,
                                    "Real" if tipo_expr=="Numero flotante" else "Entero",
                                    linea_expr, valor_literal, es_variable=False)
                        else:
                            agregar(tok_expr,
                                    tabla_simbolos[tok_expr]["Tipo"],
                                    linea_expr, tabla_simbolos[tok_expr]["Valor"], es_variable=False)

            if not expr_tokens:
                if id_token in tabla_simbolos:
                    agregar(id_token, tabla_simbolos[id_token]["Tipo"], num_linea,
                            error_msg="Error sintáctico: Falta valor en la asignación")
                else:
                    agregar(id_token, "Error", num_linea,
                            error_msg="Error sintáctico: Falta valor en la asignación")
                i = j
                continue

            if len(expr_tokens) == 1 and expr_tokens[0][1] in ["Numero entero", "Numero flotante"]:
                literal_token, literal_tipo, lit_line = expr_tokens[0]
                valor = float(literal_token) if literal_tipo=="Numero flotante" else int(literal_token)
                valor_tipo = "Real" if literal_tipo=="Numero flotante" else "Entero"
                if id_token in tabla_simbolos:
                    decl_tipo = tabla_simbolos[id_token]["Tipo"]
                    if decl_tipo != valor_tipo:
                        agregar(id_token, decl_tipo, num_linea, valor,
                                error_msg=f"Error semántico (línea {num_linea}): Variable '{id_token}' declarada como {decl_tipo} no puede recibir un valor {valor_tipo}")
                    else:
                        tabla_simbolos[id_token]["Valor"] = valor
                        tabla_simbolos[id_token]["Asignado"] = True
                else:
                    agregar(id_token, "Error", num_linea,
                            error_msg=f"Error semántico (línea {num_linea}): Variable '{id_token}' usada sin declaración")
            else:
                expr_str = " ".join(tok for tok, t, nl in expr_tokens)
                expr_type = operand_types[0] if operand_types else "Entero"
                if id_token in tabla_simbolos:
                    decl_tipo = tabla_simbolos[id_token]["Tipo"]
                    if decl_tipo != expr_type:
                        agregar(id_token, decl_tipo, num_linea, valor=expr_str,
                                error_msg=f"Error semántico (línea {num_linea}): Variable '{id_token}' declarada como {decl_tipo} no puede recibir un valor {expr_type}")
                    else:
                        tabla_simbolos[id_token]["Valor"] = expr_str
                        tabla_simbolos[id_token]["Asignado"] = True
                else:
                    agregar(id_token, "Error", num_linea,
                            error_msg=f"Error semántico (línea {num_linea}): Variable '{id_token}' usada sin declaración")
            i = j
            continue

        if tipo_token in ["Numero entero", "Numero flotante"]:
            valor = float(token) if tipo_token=="Numero flotante" else int(token)
            num_tipo = "Real" if tipo_token=="Numero flotante" else "Entero"
            if valor != 0:
                agregar(token, num_tipo, num_linea, valor, es_variable=False)
            last_declared_type = None
            i += 1
            continue

        if tipo_token == "Identificador":
            if last_declared_type is not None:
                agregar(token, last_declared_type, num_linea)
            else:
                if token not in tabla_simbolos:
                    agregar(token, "Error", num_linea,
                            error_msg=f"Error semántico (línea {num_linea}): Variable '{token}' usada sin declaración")
                else:
                    agregar(token, tabla_simbolos[token]["Tipo"], num_linea)
            if i+1 < len(tokens):
                siguiente_token, _, _ = tokens[i+1]
                if siguiente_token != ",":
                    last_declared_type = None
            else:
                last_declared_type = None
            i += 1
            continue

        last_declared_type = None
        i += 1

    for var, info in tabla_simbolos.items():
        if info["EsVariable"] and info["Tipo"] in ["Entero", "Real"] and not info["Asignado"]:
            info["Errores"].append(f"Línea {info['Lineas'][0]}: Variable '{var}' declarada pero no asignada")
    return tabla_simbolos

########################################
# DEFINICIÓN DEL AST Y DEL PARSER CON LINE NUMBERS
########################################
class ASTNode:
    def __init__(self, node_type, value=None, children=None, line=None):
        self.node_type = node_type  # Ejemplo: "Program", "Declaration", "Assignment", "BinaryOp", etc.
        self.value = value          # Valor asociado (identificador, operador, etc.)
        self.children = children if children is not None else []
        self.line = line            # Línea en la que aparece (si se conoce)

    def pretty_print(self, prefix="", is_last=True):
        connector = "└── " if is_last else "├── "
        # Mostrar el tipo de nodo y, si se conoce, la línea
        line_info = f" (línea {self.line})" if self.line is not None else ""
        result = prefix + connector + f"{self.node_type}{line_info}: {self.value}\n"
        prefix_child = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(self.children):
            is_last_child = (i == len(self.children)-1)
            result += child.pretty_print(prefix_child, is_last_child)
        return result

    def __str__(self):
        return self.pretty_print()

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens      # Lista de tokens: (token, tipo, línea)
        self.pos = 0
        self.current = tokens[0] if tokens else None

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current = self.tokens[self.pos]
        else:
            self.current = None

    def parse_program(self):
        # Si existe "INICIAR", usar su línea
        prog_line = self.current[2] if self.current and self.current[0].upper() == "INICIAR" else None
        if self.current and self.current[0].upper() == "INICIAR":
            self.advance()
        prog_name = None
        if self.current and self.current[1] == "Identificador":
            prog_name = self.current[0]
            prog_line = self.current[2]
            self.advance()
        declarations = self.parse_declarations()
        statements = self.parse_statements()
        if self.current and self.current[0].upper() == "FINALIZAR":
            self.advance()
        else:
            raise Exception("Se esperaba 'Finalizar' al final del programa")
        return ASTNode("Program", prog_name, [declarations, statements], line=prog_line)

    def parse_declarations(self):
        decl_nodes = []
        while self.current and self.current[0] in {"Int", "Real", "float"}:
            decl_nodes.append(self.parse_declaration())
        return ASTNode("Declarations", children=decl_nodes)

    def parse_declaration(self):
        type_token = self.current[0]
        decl_line = self.current[2]
        declared_type = "Entero" if type_token == "Int" else "Real"
        self.advance()
        identifiers = []
        while self.current and self.current[1] == "Identificador":
            identifiers.append((self.current[0], self.current[2]))
            self.advance()
            if self.current and self.current[0] == ",":
                self.advance()
            else:
                break
        if self.current and self.current[0] == ";":
            self.advance()
        else:
            raise Exception("Se esperaba ';' al final de la declaración")
        children = [ASTNode("Identifier", id, line=line) for id, line in identifiers]
        return ASTNode("Declaration", declared_type, children, line=decl_line)

    def parse_statements(self):
        stmt_nodes = []
        while self.current and self.current[0].upper() not in {"FINALIZAR"}:
            stmt_nodes.append(self.parse_statement())
        return ASTNode("Statements", children=stmt_nodes)

    def parse_statement(self):
        if self.current and self.current[0].upper() == "LEER":
            stmt_line = self.current[2]
            self.advance()
            if self.current and self.current[1] == "Identificador":
                var = self.current[0]
                self.advance()
                if self.current and self.current[0] == ";":
                    self.advance()
                return ASTNode("Input", var, line=stmt_line)
            else:
                raise Exception("Se esperaba un identificador tras 'Leer'")
        if self.current and self.current[0].upper() == "MOSTRAR":
            stmt_line = self.current[2]
            self.advance()
            if self.current and self.current[1] == "Identificador":
                var = self.current[0]
                self.advance()
                if self.current and self.current[0] == ";":
                    self.advance()
                return ASTNode("Output", var, line=stmt_line)
            else:
                raise Exception("Se esperaba un identificador tras 'Mostrar'")
        if self.current and self.current[1] == "Identificador":
            stmt_line = self.current[2]
            var = self.current[0]
            self.advance()
            if self.current and self.current[0] == "=":
                assign_line = self.current[2]
                self.advance()
                expr = self.parse_expression()
                if self.current and self.current[0] == ";":
                    self.advance()
                else:
                    raise Exception("Se esperaba ';' al final de la asignación")
                return ASTNode("Assignment", var, [expr], line=assign_line)
            else:
                expr = self.parse_expression()
                if self.current and self.current[0] == ";":
                    self.advance()
                return ASTNode("Expression", None, [expr], line=stmt_line)
        expr = self.parse_expression()
        if self.current and self.current[0] == ";":
            self.advance()
        return ASTNode("Expression", None, [expr])

    def parse_expression(self):
        node = self.parse_term()
        while self.current and self.current[0] in {"+", "-"}:
            op_token = self.current
            op = op_token[0]
            op_line = op_token[2]
            self.advance()
            right = self.parse_term()
            node = ASTNode("BinaryOp", op, [node, right], line=op_line)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.current and self.current[0] in {"*", "/"}:
            op_token = self.current
            op = op_token[0]
            op_line = op_token[2]
            self.advance()
            right = self.parse_factor()
            node = ASTNode("BinaryOp", op, [node, right], line=op_line)
        return node

    def parse_factor(self):
        if self.current is None:
            raise Exception("Fin inesperado de la entrada")
        if self.current[0] == "(":
            self.advance()
            node = self.parse_expression()
            if self.current and self.current[0] == ")":
                self.advance()
                return node
            else:
                raise Exception("Se esperaba ')'")
        if self.current[1] in {"Numero entero", "Numero flotante"}:
            val = self.current[0]
            line_num = self.current[2]
            self.advance()
            return ASTNode("Number", val, line=line_num)
        if self.current[1] == "Identificador":
            id_val = self.current[0]
            line_num = self.current[2]
            self.advance()
            return ASTNode("Identifier", id_val, line=line_num)
        raise Exception(f"Token inesperado: {self.current[0]}")

def generate_ast(tokens):
    parser = Parser(tokens)
    return parser.parse_program()

########################################
# PASADA DE COMPROBACIÓN DE TIPOS EN EL AST
########################################
def type_check_ast(node, symbol_table):
    """
    Recorre recursivamente el AST y determina el tipo de cada expresión.
    Si se detecta que los operandos de una operación aritmética o asignación son incompatibles,
    lanza una Exception que indica el error semántico y la línea donde ocurre.
    """
    if node.node_type == "Number":
        return "Real" if "." in node.value else "Entero"
    elif node.node_type == "Identifier":
        if node.value in symbol_table:
            return symbol_table[node.value]["Tipo"]
        else:
            raise Exception(f"Error semántico (línea {node.line}): Identificador '{node.value}' no declarado")
    elif node.node_type == "BinaryOp":
        left_type = type_check_ast(node.children[0], symbol_table)
        right_type = type_check_ast(node.children[1], symbol_table)
        if left_type != right_type:
            raise Exception(f"Error semántico (línea {node.line}): Operador '{node.value}' tiene operandos de tipos incompatibles ({left_type} vs {right_type})")
        return left_type
    elif node.node_type == "Assignment":
        var = node.value
        if var not in symbol_table:
            raise Exception(f"Error semántico (línea {node.line}): Variable '{var}' usada sin declaración")
        var_type = symbol_table[var]["Tipo"]
        expr_type = type_check_ast(node.children[0], symbol_table)
        if var_type != expr_type:
            raise Exception(f"Error semántico (línea {node.line}): Variable '{var}' declarada como {var_type} no puede recibir un valor {expr_type}")
        return var_type
    elif node.node_type in {"Expression", "Input", "Output"}:
        if node.children:
            return type_check_ast(node.children[0], symbol_table)
        return None
    elif node.node_type in {"Declaration", "Declarations", "Statements", "Program"}:
        for child in node.children:
            type_check_ast(child, symbol_table)
        return None
    else:
        return None

########################################
# FUNCIÓN PRINCIPAL
########################################
if __name__ == '__main__':
    # 1. Obtener tokens y generar la tabla de símbolos
    config = obtener_config()
    archivo = config["ARCHIVO_FUENTE"]
    tokens = analizar_archivo(archivo)
    
    # Imprimir la tabla de tokens en consola
    df_tokens = pd.DataFrame(tokens, columns=["Token", "Tipo", "Linea"])
    print("Tabla de Tokens:")
    print(df_tokens.to_string(index=False))
    print("\n" + "="*50 + "\n")
    
    # Generar e imprimir la tabla de símbolos en consola
    tabla_simbolos = generar_tabla_simbolos(tokens)
    columnas = ["Tipo", "Id_Token", "Repeticiones", "Lineas", "Valor"]
    df_simbolos = pd.DataFrame.from_dict(tabla_simbolos, orient='index', columns=columnas)
    print("Tabla de Símbolos:")
    print(df_simbolos.to_string())
    print("\n" + "="*50 + "\n")
    
    # Imprimir errores detectados (indicando la línea) o mostrar que no se detectaron errores
    errores = []
    for info in tabla_simbolos.values():
        if info["Errores"]:
            errores.extend(info["Errores"])
    if errores:
        print("Errores detectados:")
        for err in errores:
            print(err)
    else:
        print("No se detectaron errores semánticos en la tabla de símbolos.")
    
    # 2. Generar el AST (sin imprimirlo en consola) y escribirlo en 'ast.txt'
    try:
        ast_root = generate_ast(tokens)
        # Realizar la comprobación de tipos en el AST
        type_check_ast(ast_root, tabla_simbolos)
    except Exception as e:
        print("\nSe ha detenido el análisis por error semántico:")
        print(e)
        sys.exit(1)
    
    ast_text = ast_root.pretty_print()
    with open("ast.txt", "w", encoding="utf-8") as f:
        f.write(ast_text)
    
    print("\nEl AST se ha generado y guardado en 'ast.txt'")
