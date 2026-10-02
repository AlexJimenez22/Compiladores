import sys
import json

# --- ESTRUCTURA DEL OBJETO INSTRUCCIÓN ---
class ObjetoInstruccion:
    def __init__(self, operacion, registros=None, direccion=None):
        self.operacion = operacion
        self.registros = registros if registros is not None else []
        self.direccion = direccion

    def to_dict(self):
        return {
            "operacion": self.operacion,
            "registros": self.registros,
            "direccion": self.direccion
        }

# --- ETAPA 1: VALIDACIÓN E IDENTIFICACIÓN MEDIANTE AFD ---
def analizar_instruccion(entrada):
    # Definición de tokens válidos por tipo
    mnemonicos = {"MOV", "ADD", "STO", "END"}
    registros_validos = {"AL", "BL"}

    # Tokenización primaria (preservando comas y espacios)
    cadena_limpia = entrada.strip()
    if not cadena_limpia:
        return False, [], "Instrucción vacía."

    # AFD carácter por carácter
    tokens = []
    buffer = ""
    i = 0
    n = len(cadena_limpia)

    while i < n:
        c = cadena_limpia[i]

        if c.isspace():
            if buffer:
                tokens.append(buffer)
                buffer = ""
            i += 1
        elif c == ',':
            if buffer:
                tokens.append(buffer)
                buffer = ""
            tokens.append(",")
            i += 1
        else:
            buffer += c
            i += 1

    if buffer:
        tokens.append(buffer)

    # Clasificación de Tokens (Lexema -> Token)
    tokens_clasificados = []
    for t in tokens:
        if t in mnemonicos:
            tokens_clasificados.append((t, t))
        elif t in registros_validos:
            tokens_clasificados.append(("REGISTRO", t))
        elif t == ",":
            tokens_clasificados.append(("COMA", t))
        elif t.isdigit():
            tokens_clasificados.append(("NUMERO", t))
        else:
            tokens_clasificados.append(("UNKNOWN", t))

    # Validar sintaxis estricta mediante Estados
    # MOV R, d
    # ADD AL, BL
    # STO d
    # END
    
    if not tokens_clasificados:
        return False, [], "Entrada inválida."

    op_token, op_lex = tokens_clasificados[0]

    if op_lex not in mnemonicos:
        return False, [], f"Error Sintáctico/Léxico: Mnemónico '{op_lex}' no reconocido."

    # Validación por regla exacta según el mnemónico
    if op_lex == "MOV":
        # Formato esperado: MOV REGISTRO COMA NUMERO (4 tokens)
        if len(tokens_clasificados) != 4:
            return False, [], "Error Sintáctico: MOV requiere el formato 'MOV R, d'."
        if tokens_clasificados[1][0] != "REGISTRO":
            return False, [], f"Error Sintáctico: Registro no permitido '{tokens_clasificados[1][1]}'."
        if tokens_clasificados[2][0] != "COMA":
            return False, [], "Error Sintáctico: Se esperaba una coma ',' entre operandos."
        if tokens_clasificados[3][0] != "NUMERO":
            return False, [], "Error Sintáctico: La dirección debe ser un número decimal no negativo."

    elif op_lex == "ADD":
        # Formato esperado: ADD REGISTRO(AL) COMA REGISTRO(BL) (4 tokens)
        if len(tokens_clasificados) != 4:
            return False, [], "Error Sintáctico: ADD requiere el formato 'ADD AL, BL'."
        if tokens_clasificados[1][1] != "AL":
            return False, [], "Error Sintáctico: El primer operando de ADD debe ser AL."
        if tokens_clasificados[2][0] != "COMA":
            return False, [], "Error Sintáctico: Se esperaba una coma ',' entre operandos."
        if tokens_clasificados[3][1] != "BL":
            return False, [], "Error Sintáctico: El segundo operando de ADD debe ser BL."

    elif op_lex == "STO":
        # Formato esperado: STO NUMERO (2 tokens)
        if len(tokens_clasificados) != 2:
            return False, [], "Error Sintáctico: STO requiere el formato 'STO d'."
        if tokens_clasificados[1][0] != "NUMERO":
            return False, [], "Error Sintáctico: La dirección debe ser un número decimal no negativo."

    elif op_lex == "END":
        # Formato esperado: END (1 token)
        if len(tokens_clasificados) != 1:
            return False, [], "Error Sintáctico: END no acepta operandos adicionales."

    return True, tokens_clasificados, "Instrucción válida."


# --- ETAPA 2: CONSTRUCCIÓN DEL OBJETO INSTRUCCIÓN ---
def construir_objeto(tokens_clasificados):
    op = tokens_clasificados[0][1]

    if op == "MOV":
        reg = tokens_clasificados[1][1]
        direccion = int(tokens_clasificados[3][1])
        return ObjetoInstruccion(operacion="MOV", registros=[reg], direccion=direccion)

    elif op == "ADD":
        return ObjetoInstruccion(operacion="ADD", registros=["AL", "BL"], direccion=None)

    elif op == "STO":
        direccion = int(tokens_clasificados[1][1])
        return ObjetoInstruccion(operacion="STO", registros=[], direccion=direccion)

    elif op == "END":
        return ObjetoInstruccion(operacion="END", registros=[], direccion=None)


# --- ETAPA 3: MÁQUINA DE MOORE (GENERACIÓN DE MICROOPERACIONES) ---
def maquina_de_moore(objeto_inst):
    op = objeto_inst.operacion
    d = objeto_inst.direccion
    microops = []

    if op == "MOV":
        reg = objeto_inst.registros[0]
        microops.append(f"MAR <- {d}")
        microops.append("MBR <- M[MAR]")
        microops.append(f"{reg} <- MBR")

    elif op == "ADD":
        microops.append("ACC <- AL + BL")

    elif op == "STO":
        microops.append(f"MAR <- {d}")
        microops.append("MBR <- ACC")
        microops.append("M[MAR] <- MBR")

    elif op == "END":
        microops.append("HALT <- 1")

    return microops


# --- PROGRAMA PRINCIPAL ---
def main():
    print("=" * 50)
    print("ANALIZADOR LÉXICO/SINTÁCTICO Y MÁQUINA DE MOORE")
    print("=" * 50)
    
    instruccion_entrada = input("Ingrese la instrucción ISA: ")
    print("\n1. VALIDACIÓN MEDIANTE AFD")
    
    es_valida, tokens, mensaje = analizar_instruccion(instruccion_entrada)
    
    if not es_valida:
        print(f"Resultado: {mensaje}")
        print("Procesamiento detenido.")
        sys.exit(0)

    print(f"Resultado: {mensaje}")

    print("\n2. TOKENS RECONOCIDOS")
    for tok, lex in tokens:
        print(f"  {tok} (\"{lex}\")")

    print("\n3. COMPONENTES IDENTIFICADOS")
    obj = construir_objeto(tokens)
    print(f"  Mnemónico: {obj.operacion}")
    if obj.registros:
        print(f"  Registro(s): {', '.join(obj.registros)}")
    if obj.direccion is not None:
        print(f"  Dirección de memoria: {obj.direccion}")
        print("  Direccionamiento: directo")

    print("\n4. OBJETO INSTRUCCIÓN")
    print(json.dumps(obj.to_dict(), indent=4))

    print("\n5. MICROOPERACIONES GENERADAS POR MOORE")
    microoperaciones = maquina_de_moore(obj)
    for i, uop in enumerate(microoperaciones, 1):
        print(f"  Paso {i}: {uop}")
    print("  Fin de la generación.")

if __name__ == "__main__":
    main()