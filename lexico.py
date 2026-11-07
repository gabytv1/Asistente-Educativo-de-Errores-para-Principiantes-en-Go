# -*- coding: utf-8 -*-
"""
Analizador léxico para un subconjunto del lenguaje Go (PLY - ply.lex).

Proyecto de Lenguajes de Programación - PAO II 2026
Asistente Educativo de Errores para Principiantes en Go
Integrantes: Fátima Torres, César Balladares, Elkin Salazar

Notas de PLY:
  * Las reglas definidas como FUNCIONES se prueban en el orden en que aparecen
    en este archivo (de arriba hacia abajo).
  * Las reglas definidas como CADENAS se prueban después de las funciones,
    ordenadas de la expresión regular más larga a la más corta. Por eso ':='
    se reconoce antes que ':' y '==' antes que '='.
"""
import sys

import ply.lex as lex


# ===========================================================================
# 1. UTILIDADES COMPARTIDAS
# ===========================================================================
def columna(lexdata, pos):
    """Columna (empieza en 1) de la posición `pos` dentro del texto."""
    inicio_linea = lexdata.rfind('\n', 0, pos)
    return pos - inicio_linea  # si no hay '\n' previo, inicio_linea = -1


def registrar_error(t, codigo, mensaje, pos=None):
    """Guarda un error léxico con su línea y columna en el analizador."""
    pos = t.lexpos if pos is None else pos
    linea = t.lexer.lineno
    col = columna(t.lexer.lexdata, pos)
    texto = "Error léxico [línea %d, col. %d]: %s" % (linea, col, mensaje)
    t.lexer.errores.append({
        'codigo': codigo, 'linea': linea, 'columna': col, 'mensaje': texto,
    })


# Palabras que parecen identificadores pero son tokens propios. Cada sección
# agrega las suyas con reservadas.update({...}); t_ID las consulta.
reservadas = {}

# Espacios, tabulaciones y retornos de carro se ignoran.
t_ignore = ' \t\r'


# ===========================================================================
# 2. COMENTARIOS Y SALTO DE LÍNEA
# ===========================================================================
# INICIO aporte: Fátima Torres
tokens_comentarios = ['NEWLINE']


def t_COMENTARIO_MULTILINEA(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')      # se cuentan sus saltos de línea


def t_COMENTARIO_SIN_CERRAR(t):                # Error L4
    r'/\*(.|\n)*'
    registrar_error(
        t, 'L4',
        "el comentario iniciado con /* no se cierra. "
        "Sugerencia: agrega */ al final del comentario.")
    t.lexer.lineno += t.value.count('\n')


def t_COMENTARIO_LINEA(t):
    r'//[^\n]*'
    # se descarta; el salto de línea lo procesa t_NEWLINE


def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    # Se emite siempre; AnalizadorLexico lo conserva únicamente si el último
    # token de la línea permite la inserción automática (ver más abajo).
    return t
# FIN aporte: Fátima Torres


# ===========================================================================
# 3. PALABRAS RESERVADAS
# ===========================================================================
# INICIO aporte: Fátima Torres
reservadas_basicas = {
    'package': 'PACKAGE',
    'import': 'IMPORT',
    'func': 'FUNC',
    'var': 'VAR',
    'const': 'CONST',
    'if': 'IF',
    'else': 'ELSE',
    'for': 'FOR',
    'switch': 'SWITCH',
    'case': 'CASE',
    'default': 'DEFAULT',
    'break': 'BREAK',
    'continue': 'CONTINUE',
    'return': 'RETURN',
}
reservadas.update(reservadas_basicas)

# Paquete fmt: la propuesta (sección 5) reconoce solo estas dos funciones, y el
# nombre del paquete. Se distinguen de los identificadores igual que las
# palabras reservadas, para que el analizador sintáctico y el semántico no las
# traten como variables o funciones sin declarar.
reservadas_fmt = {
    'fmt': 'FMT',
    'Println': 'PRINTLN',
    'Scanln': 'SCANLN',
}
reservadas.update(reservadas_fmt)

tokens_reservadas = list(reservadas_basicas.values()) + list(reservadas_fmt.values())
# FIN aporte: Fátima Torres


# ===========================================================================
# 4. DELIMITADORES
# ===========================================================================
# INICIO aporte: Fátima Torres
tokens_delimitadores = [
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
    'COMMA', 'SEMICOLON', 'COLON', 'DOT',
]

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_COMMA = r','
t_SEMICOLON = r';'
t_COLON = r':'
t_DOT = r'\.'
# FIN aporte: Fátima Torres


# ===========================================================================
# 5. IDENTIFICADORES, LITERALES Y TIPOS
# ===========================================================================
# INICIO aporte: César Balladares
reservadas_tipos = {
    'true': 'TRUE',
    'false': 'FALSE',
    'int': 'TYPE_INT',
    'float64': 'TYPE_FLOAT64',
    'string': 'TYPE_STRING',
    'bool': 'TYPE_BOOL',
}
reservadas.update(reservadas_tipos)

tokens_literales = [
    'ID', 'INTEGER_VALUE', 'FLOAT_VALUE', 'STRING_VALUE',
] + list(reservadas_tipos.values())


# --- Números ---------------------------------------------------------------
def t_NUMERO_MAL_FORMADO(t):                   # Error L3
    r'[0-9]+(?:\.[0-9]+){2,}[\w.]*|[0-9]+(?:\.[0-9]+)?[^\W\d][\w.]*'
    registrar_error(
        t, 'L3',
        "el literal '%s' no es válido. Sugerencia: revisa que el número no "
        "contenga letras ni más de un punto decimal." % t.value)
    

def t_FLOAT_VALUE(t):
    r'[0-9]+\.[0-9]+'
    t.value = float(t.value)
    return t


def t_INTEGER_VALUE(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t


# --- Cadenas ---------------------------------------------------------------
def t_STRING_VALUE(t):
    r'"(?:[^"\\\n]|\\.)*"'
    return t


def t_CADENA_SIN_CERRAR(t):                    # Error L2
    r'"(?:[^"\\\n]|\\.)*\\?'
    registrar_error(
        t, 'L2',
        "la cadena de texto no tiene comilla de cierre. "
        "Sugerencia: agrega \" al final de la cadena.")


def t_COMILLA_SIMPLE(t):                       # Error L6
    r"'(?:[^'\\\n]|\\.)*\\?'?"
    # En Go las cadenas llevan comillas dobles; las simples son para un solo
    # carácter (rune), que este subconjunto no incluye. Se admite \ dentro
    # (por ejemplo '\n' o '\'') para consumir el texto completo y no generar
    # errores en cascada.
    cerrada = len(t.value) > 1 and t.value.endswith("'")
    contenido = t.value[1:-1] if cerrada else t.value[1:]
    registrar_error(
        t, 'L6',
        "el texto %s usa comillas simples, pero las cadenas de texto se escriben "
        "con comillas dobles. Sugerencia: reemplázalo por \"%s\"."
        % (t.value, contenido))


# --- Identificadores y palabras reservadas -------------------------------
def t_ID(t):
    r'[^\W\d]\w*'
    # Letra (incluye tildes y ñ: año, número) o _ seguida de letras, dígitos o _.
    # Las palabras reservadas se reconocen antes que los identificadores.
    t.type = reservadas.get(t.value, 'ID')
    return t


# --- Error L1: carácter ilegal -------------------------------------------
def t_error(t):
    registrar_error(
        t, 'L1',
        "el carácter '%s' no pertenece al subconjunto definido. "
        "Sugerencia: elimínalo o reemplázalo por un operador válido."
        % t.value[0])
    t.lexer.skip(1)
# FIN aporte: César Balladares


# ===========================================================================
# 6. OPERADORES
# ===========================================================================
# INICIO aporte: Elkin Salazar
reservadas.update({'map': 'MAP'})

tokens_operadores = [
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'INC', 'DEC',
    'ASSIGN', 'DECLARE', 'PLUS_ASSIGN', 'MINUS_ASSIGN',
    'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
    'AND', 'OR', 'NOT',
    'ADDR',
    'MAP',
]


# --- Error L5: '|' solo es válido como '||' ------------------------------
def t_OPERADOR_INCOMPLETO(t):
    r'\|(?!\|)'
    registrar_error(
        t, 'L5',
        "el símbolo '|' solo es válido como '||'. "
        "Sugerencia: usa || para la disyunción lógica.")


# --- Operadores de dos caracteres (PLY los prueba antes que los de uno) ---
t_INC = r'\+\+'
t_DEC = r'--'
t_DECLARE = r':='
t_PLUS_ASSIGN = r'\+='
t_MINUS_ASSIGN = r'-='
t_EQ = r'=='
t_NE = r'!='
t_LE = r'<='
t_GE = r'>='
t_AND = r'&&'
t_OR = r'\|\|'

# --- Operadores de un carácter --------------------------------------------
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'
t_ASSIGN = r'='
t_LT = r'<'
t_GT = r'>'
t_NOT = r'!'
t_ADDR = r'&'
# FIN aporte: Elkin Salazar


# ===========================================================================
# 7. UNIÓN DE LAS SECCIONES Y CLASE DEL ANALIZADOR
# ===========================================================================
tokens = tuple(tokens_comentarios + tokens_reservadas + tokens_delimitadores
               + tokens_literales + tokens_operadores)

# El salto de línea solo termina una sentencia si el último token de la línea
# es uno de estos (regla de inserción automática de Go, ver sección 3).
TOKENS_QUE_CIERRAN_SENTENCIA = {
    'ID', 'FMT', 'PRINTLN', 'SCANLN',
    'TYPE_INT', 'TYPE_FLOAT64', 'TYPE_STRING', 'TYPE_BOOL',
    'TRUE', 'FALSE', 'INTEGER_VALUE', 'FLOAT_VALUE', 'STRING_VALUE',
    'BREAK', 'CONTINUE', 'RETURN',
    'INC', 'DEC', 'RPAREN', 'RBRACKET', 'RBRACE',
}


class AnalizadorLexico:
    """Envuelve el lexer de PLY: aplica la regla de NEWLINE y guarda errores.

    Tiene los métodos input() y token(), por lo que también puede usarse como
    lexer de ply.yacc en los siguientes avances.
    """

    def __init__(self):
        self.lexer = lex.lex(module=sys.modules[__name__])
        self.reiniciar()

    def reiniciar(self):
        self.lexer.lineno = 1
        self.lexer.errores = []
        self._anterior = None

    def input(self, codigo):
        self.reiniciar()
        self.codigo = codigo
        self.lexer.input(codigo)

    def token(self):
        while True:
            tok = self.lexer.token()
            if tok is None:
                return None
            if tok.type == 'NEWLINE':
                if self._anterior not in TOKENS_QUE_CIERRAN_SENTENCIA:
                    continue                      # no termina la sentencia
                tok.value = '\\n'                  # se muestra como \n
            self._anterior = tok.type
            tok.columna = columna(self.codigo, tok.lexpos)
            return tok

    @property
    def errores(self):
        return self.lexer.errores

    def analizar(self, codigo):
        """Devuelve (tokens, errores) del texto recibido."""
        self.input(codigo)
        lista = []
        while True:
            tok = self.token()
            if tok is None:
                break
            lista.append(tok)
        return lista, list(self.errores)
