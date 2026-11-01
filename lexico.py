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
tokens_reservadas = list(reservadas_basicas.values())
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
tokens_literales = []


def t_error(t):
    t.lexer.skip(1)



# ===========================================================================
# 6. OPERADORES
# ===========================================================================

tokens_operadores = []


# ===========================================================================
# 7. UNIÓN DE LAS SECCIONES Y CLASE DEL ANALIZADOR
# ===========================================================================
tokens = tuple(tokens_comentarios + tokens_reservadas + tokens_delimitadores
               + tokens_literales + tokens_operadores)

# El salto de línea solo termina una sentencia si el último token de la línea
# es uno de estos (regla de inserción automática de Go, ver sección 3).
TOKENS_QUE_CIERRAN_SENTENCIA = {
    'ID', 'TYPE_INT', 'TYPE_FLOAT64', 'TYPE_STRING', 'TYPE_BOOL',
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
