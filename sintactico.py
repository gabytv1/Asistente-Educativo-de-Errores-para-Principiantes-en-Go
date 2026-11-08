# -*- coding: utf-8 -*-
"""
Analizador sintáctico para un subconjunto del lenguaje Go (PLY - ply.yacc).

Proyecto de Lenguajes de Programación - PAO II 2026
Asistente Educativo de Errores para Principiantes en Go
Integrantes: Fátima Torres (gabytv1), César Balladares (CBalla-05),
             Elkin Salazar (sElkinEspol)

Cómo está organizado
  * Los tokens vienen del analizador léxico (lexico.py, Avance 1).
  * Cada regla gramatical es una función p_xxx cuyo docstring es la regla
    (así lo exige PLY). Las reglas están agrupadas por integrante entre los
    comentarios  INICIO aporte / FIN aporte.
  * Los errores se guardan con los códigos Y1 a Y6 de la propuesta (Tabla 16)
    y el analizador intenta recuperarse para seguir buscando más errores.

Regla de NEWLINE (heredada del Avance 1): el salto de línea solo llega al
parser cuando termina una sentencia. Por eso:
    * después de '{', de ',' o de un operador NO hay NEWLINE;
    * después de ')', ']', '}', un identificador, un literal, break, continue,
      return, ++ y -- SÍ lo hay.
"""
import sys
from collections import Counter

import ply.lex as lex
import ply.yacc as yacc

from lexico import AnalizadorLexico, tokens  # noqa: F401  (PLY lee `tokens`)


# ===========================================================================
# 0. INFRAESTRUCTURA COMPARTIDA
# ===========================================================================
# INICIO aporte: Fátima Torres
class Nodo:
    """Nodo del AST: tipo, línea de origen e hijos (Nodo, str, lista, etc.)."""
    __slots__ = ('tipo', 'linea', 'hijos')

    def __init__(self, tipo, linea, *hijos):
        self.tipo = tipo
        self.linea = linea
        self.hijos = list(hijos)

    def __repr__(self):
        return 'Nodo(%s, línea %s, %r)' % (self.tipo, self.linea, self.hijos)


def _linea(p, i=1):
    """Línea del símbolo i de la regla (token, Nodo o lista de Nodos)."""
    x = p[i]
    if isinstance(x, Nodo):
        return x.linea
    if isinstance(x, list):
        return _linea_lista(x)
    return p.lineno(i)


def _linea_lista(lista):
    for x in lista:
        if isinstance(x, Nodo):
            return x.linea
    return 0


# Precedencia (de menor a mayor). Las reglas de expresiones están en las
# secciones de Fátima (booleanas) y César (aritméticas).
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NE', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'UMINUS', 'NOT'),
)

start = 'programa'


def p_empty(p):
    'empty :'
    p[0] = None


def p_fin(p):
    '''fin : NEWLINE
           | SEMICOLON'''
    p[0] = p[1]


def p_bloque(p):
    'bloque : LBRACE sentencias RBRACE'
    p[0] = Nodo('bloque', p.lineno(1), p[2])


def p_sentencias(p):
    '''sentencias : sentencias sentencia
                  | empty'''
    if len(p) == 3:
        p[0] = p[1] + ([p[2]] if p[2] is not None else [])
    else:
        p[0] = []


def p_sentencia(p):
    '''sentencia : sent_simple fin
                 | decl_var fin
                 | decl_const fin
                 | sent_if
                 | sent_for
                 | sent_switch
                 | sent_break fin
                 | sent_continue fin
                 | sent_return fin
                 | bloque NEWLINE'''
    p[0] = p[1]


def p_sentencia_error(p):
    'sentencia : error NEWLINE'
    # Recuperación de errores: se descartan los tokens hasta el fin de línea.
    _ctx['parser'].errok()
    p[0] = None


def p_tipo_simple(p):
    '''tipo_simple : TYPE_INT
                   | TYPE_FLOAT64
                   | TYPE_STRING
                   | TYPE_BOOL'''
    p[0] = p[1]


def p_tipo_dato(p):
    '''tipo_dato : tipo_simple
                 | tipo_arreglo
                 | tipo_slice
                 | tipo_mapa'''
    p[0] = p[1]


def p_lista_expr(p):
    '''lista_expr : expr
                  | lista_expr COMMA expr'''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]


def p_lista_expr_opt(p):
    '''lista_expr_opt : lista_expr
                      | empty'''
    p[0] = p[1] if p[1] is not None else []


def p_parametros(p):
    '''parametros : lista_param
                  | empty'''
    p[0] = p[1] if p[1] is not None else []


def p_lista_param(p):
    '''lista_param : param
                   | lista_param COMMA param'''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]


def p_param(p):
    'param : ID tipo_dato'
    p[0] = Nodo('param', p.lineno(1), p[1], p[2])
# FIN aporte: Fátima Torres (infraestructura)


# ===========================================================================
# 1. FÁTIMA TORRES
#    var (con tipo / con tipo y valor), expresiones booleanas, if e if-else,
#    arreglo (declaración, inicialización y acceso), función con un retorno.
#    Mensajes Y1 (falta '{') y Y5 (else mal ubicado) -> ver p_error.
# ===========================================================================
# INICIO aporte: Fátima Torres
# --- Declaración con var ---------------------------------------------------
def p_decl_var(p):
    '''decl_var : VAR ID tipo_dato
                | VAR ID tipo_dato ASSIGN expr'''
    valor = p[5] if len(p) == 6 else None
    p[0] = Nodo('var', p.lineno(1), p[2], p[3], valor)


# --- Expresiones booleanas (||, &&, comparaciones, !) ----------------------
def p_expr_logica(p):
    '''expr : expr OR expr
            | expr AND expr'''
    p[0] = Nodo('logica', _linea(p), p[2], p[1], p[3])


def p_expr_comparacion(p):
    '''expr : expr EQ expr
            | expr NE expr
            | expr LT expr
            | expr LE expr
            | expr GT expr
            | expr GE expr'''
    p[0] = Nodo('comparacion', _linea(p), p[2], p[1], p[3])


def p_expr_not(p):
    'expr : NOT expr'
    p[0] = Nodo('not', p.lineno(1), p[2])


# --- if e if-else ----------------------------------------------------------
def p_sent_if(p):
    '''sent_if : IF expr bloque NEWLINE
               | IF expr bloque ELSE bloque NEWLINE
               | IF expr bloque ELSE sent_if'''
    if len(p) == 5:
        p[0] = Nodo('if', p.lineno(1), p[2], p[3], None)
    elif len(p) == 7:
        p[0] = Nodo('if', p.lineno(1), p[2], p[3], p[5])
    else:                                          # else if ...
        p[0] = Nodo('if', p.lineno(1), p[2], p[3], p[5])


# --- Arreglo: tipo, literal y (en la sección compartida) acceso por índice --
def p_tipo_arreglo(p):
    'tipo_arreglo : LBRACKET INTEGER_VALUE RBRACKET tipo_simple'
    p[0] = '[%s]%s' % (p[2], p[4])


def p_literal_arreglo(p):
    'literal : LBRACKET INTEGER_VALUE RBRACKET tipo_simple LBRACE lista_expr_opt RBRACE'
    p[0] = Nodo('arreglo', p.lineno(1), int(p[2]), p[4], p[6])


# --- Función con un valor de retorno ---------------------------------------
def p_func_un_retorno(p):
    'decl_func : FUNC ID LPAREN parametros RPAREN tipo_dato bloque NEWLINE'
    p[0] = Nodo('func', p.lineno(1), p[2], p[4], [p[6]], p[7])


def p_sent_return_valor(p):
    'sent_return : RETURN expr'
    p[0] = Nodo('return', p.lineno(1), [p[2]])


# --- Errores Y1 (falta '{') y Y5 (else mal ubicado) ---------------------------
def error_y1(c):
    """Y1: la línea del encabezado (if, for, switch, func, else) terminó sin '{'."""
    if not (c.es_nl and c.pila and c.pila[-1] in _CIERRAN_ENCABEZADO):
        return NO_APLICA
    for i in range(len(c.pila) - 1, -1, -1):
        if c.pila[i] == 'LBRACE':
            break
        if c.pila[i] in _ENCABEZADOS:
            kw = c.pila[i]
            _registrar('Y1', c.linea,
                       "token inesperado NEWLINE al final de %s. "
                       "Sugerencia: abre el bloque con '{' en la misma "
                       "línea %s." % (_ENCABEZADOS[kw], _MISMA_LINEA[kw]))
            sig = c.fuente.token()                     # '{' en la línea siguiente
            if sig is not None and sig.type != 'LBRACE':
                c.fuente.devolver(sig, delante=True)
            return c.seguir_con(_sintetico('LBRACE', '{', c.tok))  # reemplaza al NEWLINE
    return NO_APLICA


def error_y5(c):
    """Y5: 'else' al comienzo de una línea (debe ir después de la llave '}')."""
    if c.tok.type == 'ELSE' and c.fuente.previo == 'NEWLINE':
        _registrar('Y5', c.linea,
                   "'else' debe ir en la misma línea que la llave de cierre "
                   "del if. Sugerencia: escribe } else {.")
        c.parser.errok()
        return c.fuente.token()                        # se descarta el 'else'
    return NO_APLICA
# FIN aporte: Fátima Torres


# ===========================================================================
# 2. CÉSAR BALLADARES
#    := (simple y múltiple), asignación y operadores compuestos (=, +=, -=,
#    ++, --), expresiones aritméticas con precedencia, for (con condición y
#    clásico), slice, función con dos retornos, llamada a función.
#    Mensajes Y2 (paréntesis sin cerrar) y Y4 (declaración incompleta).
# ===========================================================================
# INICIO aporte: César Balladares
# --- Declaración corta ------------------------------------------------------
def p_sent_declare(p):
    '''sent_simple : ID DECLARE expr
                   | lista_id DECLARE lista_expr'''
    if isinstance(p[1], list):
        p[0] = Nodo('declare', _linea(p), p[1], p[3])
    else:
        p[0] = Nodo('declare', p.lineno(1), [p[1]], [p[3]])


def p_lista_id(p):
    '''lista_id : ID COMMA ID
                | lista_id COMMA ID'''
    p[0] = [p[1], p[3]] if len(p) == 4 and not isinstance(p[1], list) else p[1] + [p[3]]


# --- Asignación y operadores compuestos -----------------------------------
def p_lvalue(p):
    '''lvalue : ID
              | ID LBRACKET expr RBRACKET'''
    if len(p) == 2:
        p[0] = Nodo('id', p.lineno(1), p[1])
    else:
        p[0] = Nodo('indice', p.lineno(1), p[1], p[3])


def p_sent_asignacion(p):
    '''sent_simple : lvalue ASSIGN expr
                   | lvalue PLUS_ASSIGN expr
                   | lvalue MINUS_ASSIGN expr'''
    p[0] = Nodo('asignacion', _linea(p), p[2], p[1], p[3])


def p_sent_incremento(p):
    '''sent_simple : lvalue INC
                   | lvalue DEC'''
    p[0] = Nodo('incdec', _linea(p), p[2], p[1])


# --- Expresiones aritméticas ------------------------------------------------
def p_expr_aritmetica(p):
    '''expr : expr PLUS expr
            | expr MINUS expr
            | expr TIMES expr
            | expr DIVIDE expr
            | expr MOD expr'''
    p[0] = Nodo('aritmetica', _linea(p), p[2], p[1], p[3])


def p_expr_menos_unario(p):
    'expr : MINUS expr %prec UMINUS'
    p[0] = Nodo('menos_unario', p.lineno(1), p[2])


def p_expr_parentesis(p):
    'expr : LPAREN expr RPAREN'
    p[0] = p[2]


# --- for con condición y for clásico ----------------------------------------
def p_sent_for_condicion(p):
    'sent_for : FOR expr bloque NEWLINE'
    p[0] = Nodo('for_condicion', p.lineno(1), p[2], p[3])


def p_sent_for_clasico(p):
    'sent_for : FOR sent_simple SEMICOLON expr SEMICOLON sent_simple bloque NEWLINE'
    p[0] = Nodo('for_clasico', p.lineno(1), p[2], p[4], p[6], p[7])


# --- Slice ------------------------------------------------------------------
def p_tipo_slice(p):
    'tipo_slice : LBRACKET RBRACKET tipo_simple'
    p[0] = '[]%s' % p[3]


def p_literal_slice(p):
    'literal : LBRACKET RBRACKET tipo_simple LBRACE lista_expr_opt RBRACE'
    p[0] = Nodo('slice', p.lineno(1), p[3], p[5])


# --- Función con dos valores de retorno -------------------------------------
def p_func_dos_retornos(p):
    'decl_func : FUNC ID LPAREN parametros RPAREN LPAREN tipo_dato COMMA tipo_dato RPAREN bloque NEWLINE'
    p[0] = Nodo('func', p.lineno(1), p[2], p[4], [p[7], p[9]], p[11])


def p_sent_return_doble(p):
    'sent_return : RETURN expr COMMA expr'
    p[0] = Nodo('return', p.lineno(1), [p[2], p[4]])


# --- Llamada a función (como expresión y como sentencia) --------------------
def p_llamada(p):
    'llamada : ID LPAREN lista_expr_opt RPAREN'
    p[0] = Nodo('llamada', p.lineno(1), p[1], p[3])


def p_sent_llamada(p):
    'sent_simple : llamada'
    p[0] = p[1]


# --- Errores Y2 (paréntesis sin cerrar) y Y4 (declaración incompleta) -------------
def error_y2(c):
    """Y2: falta ')' (la línea terminó, o llegó '{' o ';', con un '(' abierto)."""
    if c.parens > 0 and (c.es_nl or c.tok.type in ('LBRACE', 'SEMICOLON')):
        _registrar('Y2', c.linea,
                   "se esperaba ')' antes del fin de línea. Sugerencia: cierra "
                   "la llamada con ')'.")
        c.fuente.devolver(c.tok)
        return c.seguir_con(_sintetico('RPAREN', ')', c.tok))
    return NO_APLICA


def error_y4(c):
    """Y4: declaración incompleta (falta el tipo o el valor)."""
    pila, valores, tok = c.pila, c.valores, c.tok
    # var edad            /  var edad = 5   -> falta el tipo
    if pila[-2:] == ['VAR', 'ID'] and (c.es_nl or tok.type in ('ASSIGN', 'SEMICOLON')):
        nombre = valores[-1]
        _registrar('Y4', c.linea,
                   "falta el tipo en la declaración de '%s'. Sugerencia: "
                   "escribe el tipo, por ejemplo var %s int." % (nombre, nombre))
        c.fuente.devolver(tok)
        return c.seguir_con(_sintetico('TYPE_INT', 'int', tok))
    # total :=   /   var edad int =   /   const MAX =   -> falta el valor
    falta_valor = None
    if pila[-2:] == ['ID', 'DECLARE']:
        falta_valor = ("falta el valor en la declaración de '%s'. Sugerencia: "
                       "escribe una expresión después de ':='." % valores[-2])
    elif pila[-1:] == ['ASSIGN'] and len(pila) >= 4 and pila[-4] == 'VAR':
        falta_valor = ("falta el valor en la declaración de '%s'. Sugerencia: "
                       "escribe una expresión después de '='." % valores[-3])
    elif pila[-3:] == ['CONST', 'ID', 'ASSIGN']:
        falta_valor = ("falta el valor en la declaración de la constante '%s'. "
                       "Sugerencia: escribe una expresión después de '='." % valores[-2])
    if falta_valor and (c.es_nl or c.corte):
        _registrar('Y4', c.linea_prev, falta_valor)
        _cerrar_linea(c.fuente, tok)
        return c.seguir_con(_sintetico('INTEGER_VALUE', '0', tok))
    if c.es_nl and pila[-2:] == ['CONST', 'ID']:
        _registrar('Y4', c.linea,
                   "falta el valor en la declaración de la constante '%s'. "
                   "Sugerencia: escribe const %s = <valor>." % (valores[-1], valores[-1]))
        return None
    return NO_APLICA


def error_incompleto_oculto(c):
    """Sentencia incompleta cuya línea siguiente 'se pegó' a ella.

    Ej.: 'total :=' y debajo 'x := 1': el parser lee 'total := x' y falla en el
    segundo ':='. Se reporta la línea que quedó incompleta (Y4 o Y6).
    """
    h = c.hist
    if not (not c.es_nl and len(h) >= 3 and h[-3].type in _TERMINAN_INCOMPLETO
            and c.previo.lineno > h[-3].lineno and c.tok.lineno == c.previo.lineno):
        return NO_APLICA
    corte, pila, valores = h[-3], c.pila, c.valores
    if corte.type == 'DECLARE' and len(h) >= 4 and h[-4].type == 'ID':
        _registrar('Y4', corte.lineno,
                   "falta el valor en la declaración de '%s'. Sugerencia: "
                   "escribe una expresión después de ':='." % h[-4].value)
    elif (corte.type == 'ASSIGN' and len(pila) >= 5
          and pila[-5:-3] == ['VAR', 'ID'] and pila[-2] == 'ASSIGN'):
        _registrar('Y4', corte.lineno,
                   "falta el valor en la declaración de '%s'. Sugerencia: "
                   "escribe una expresión después de '='." % valores[-4])
    elif (corte.type == 'ASSIGN' and len(pila) >= 4
          and pila[-4:-2] == ['CONST', 'ID'] and pila[-2] == 'ASSIGN'):
        _registrar('Y4', corte.lineno,
                   "falta el valor en la declaración de la constante '%s'. "
                   "Sugerencia: escribe una expresión después de '='." % valores[-3])
    else:
        _registrar('Y6', corte.lineno,
                   "la sentencia está incompleta: termina en '%s'. Sugerencia: "
                   "escribe lo que falta después de ese símbolo." % _texto_token(corte))
    return None
# FIN aporte: César Balladares


# ===========================================================================
# 3. ELKIN SALAZAR
#    Estructura del programa (package, import, funciones), const, switch con
#    case y default, break y continue, mapa (declaración y acceso por clave),
#    función sin retorno, impresión fmt.Println y lectura fmt.Scanln.
#    Mensajes Y3 (llave sin cerrar) y Y6 (token inesperado) -> ver p_error.
# ===========================================================================


# ===========================================================================
# 4. REGLAS COMPARTIDAS POR LOS TRES (operandos de las expresiones)
#    Acceso por índice o clave (Tabla 13), llamada, literales y variables.
# ===========================================================================
def p_expr_primaria(p):
    '''expr : llamada
            | literal
            | acceso
            | ID
            | INTEGER_VALUE
            | FLOAT_VALUE
            | STRING_VALUE
            | TRUE
            | FALSE'''
    t = p.slice[1].type
    if t == 'ID':
        p[0] = Nodo('id', p.lineno(1), p[1])
    elif t in ('INTEGER_VALUE', 'FLOAT_VALUE', 'STRING_VALUE', 'TRUE', 'FALSE'):
        p[0] = Nodo('literal', p.lineno(1), t, p[1])
    else:
        p[0] = p[1]


def p_acceso(p):
    'acceso : ID LBRACKET expr RBRACKET'
    p[0] = Nodo('indice', p.lineno(1), p[1], p[3])


# ===========================================================================
# 5. ERRORES SINTÁCTICOS Y RECUPERACIÓN (infraestructura: Fátima Torres)
#    p_error arma el contexto del error y prueba, en orden, los manejadores
#    error_yN de cada integrante (definidos en sus secciones). El primero que
#    reconoce la situación registra el error y decide cómo continuar:
#      * devolver un token  -> el parser sigue con ese token (recuperación);
#      * devolver None      -> se descartan tokens hasta el fin de línea.
# ===========================================================================
# INICIO aporte: Fátima Torres (infraestructura de errores)
# Estado de la ejecución actual (lo reinicia AnalizadorSintactico.analizar).
_ctx = {'parser': None, 'fuente': None, 'errores': [], 'repeticiones': {}}

NO_APLICA = object()      # un manejador devuelve esto si el error no es suyo

_ENCABEZADOS = {
    'IF': 'la condición del if',
    'FOR': 'la condición del for',
    'SWITCH': 'la expresión del switch',
    'FUNC': 'la firma de la función',
    'ELSE': 'el else',
}
_CIERRAN_ENCABEZADO = {'expr', 'sent_simple', 'RPAREN', 'tipo_simple',
                       'tipo_dato', 'tipo_arreglo', 'tipo_slice', 'tipo_mapa',
                       'ELSE'}
# Tokens tras los cuales el léxico no emite NEWLINE y la sentencia sigue abierta.
_TERMINAN_INCOMPLETO = {
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 'ASSIGN', 'DECLARE',
    'PLUS_ASSIGN', 'MINUS_ASSIGN', 'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
    'AND', 'OR', 'NOT', 'ADDR', 'COMMA', 'LPAREN', 'LBRACKET', 'DOT',
}
_MISMA_LINEA = {
    'IF': 'del if', 'FOR': 'del for', 'SWITCH': 'del switch',
    'FUNC': 'de la declaración de la función', 'ELSE': 'del else',
}


def _texto_token(tok):
    if tok.type == 'NEWLINE':
        return 'NEWLINE'
    return tok.value if isinstance(tok.value, str) else str(tok.value)


def _registrar(codigo, linea, texto):
    errores = _ctx['errores']
    if errores and errores[-1]['linea'] == linea:
        return                                   # evita errores en cascada
    errores.append({
        'codigo': codigo, 'linea': linea,
        'mensaje': 'Error sintáctico [línea %d]: %s' % (linea, texto),
    })


def _sintetico(tipo, valor, base):
    """Token inventado para continuar el análisis tras un error."""
    t = lex.LexToken()
    t.type, t.value = tipo, valor
    t.lineno, t.lexpos = base.lineno, getattr(base, 'lexpos', 0)
    t.columna = getattr(base, 'columna', 1)
    t.sintetico = True
    return t


def _cerrar_linea(fuente, tok):
    """Devuelve `tok` al flujo precedido de un NEWLINE inventado (si hacía falta)."""
    fuente.devolver(tok)
    if tok.type != 'NEWLINE':
        fuente.devolver(_sintetico('NEWLINE', '\\n', tok), delante=True)


class ContextoError:
    """Lo que saben los manejadores sobre el error que acaba de ocurrir."""

    def __init__(self, tok, parser, fuente):
        self.tok, self.parser, self.fuente = tok, parser, fuente
        self.pila = [s.type for s in parser.symstack[1:]]
        self.valores = [getattr(s, 'value', None) for s in parser.symstack[1:]]
        self.parens = self.pila.count('LPAREN') - self.pila.count('RPAREN')
        self.llaves = self.pila.count('LBRACE') - self.pila.count('RBRACE')
        self.linea = tok.lineno
        self.es_nl = tok.type == 'NEWLINE'
        h = fuente.hist
        self.hist = h if (h and h[-1] is tok) else []
        self.previo = self.hist[-2] if len(self.hist) >= 2 else None
        # El léxico no emite NEWLINE después de un operador, una coma, '=' o
        # ':='. Si el token que falla está en otra línea, la sentencia anterior
        # quedó incompleta y el error se reporta en la línea de esa sentencia.
        self.corte = (not self.es_nl and self.previo is not None
                      and self.previo.lineno < self.linea
                      and self.previo.type in _TERMINAN_INCOMPLETO)
        self.linea_prev = self.previo.lineno if self.previo is not None else self.linea

    def seguir_con(self, token):
        """Continuar el análisis con `token` como siguiente lookahead."""
        self.parser.errok()
        return token


def p_error(tok):
    parser, fuente = _ctx['parser'], _ctx['fuente']

    # --- Fin de archivo ----------------------------------------------------
    if tok is None:
        ctx = ContextoError(_sintetico('NEWLINE', '', _fin_de_archivo(fuente)), parser, fuente)
        error_fin_de_archivo(ctx)
        return None

    # Seguro contra bucles: si el mismo token falla muchas veces seguidas, se
    # descarta y se sigue con el siguiente.
    clave = (tok.type, tok.lexpos, getattr(tok, 'sintetico', False))
    _ctx['repeticiones'][clave] = _ctx['repeticiones'].get(clave, 0) + 1
    if _ctx['repeticiones'][clave] > 3:
        parser.errok()
        return fuente.token()

    # Un token inventado por la recuperación que vuelve a fallar: no se
    # reporta de nuevo, solo se descarta la línea.
    if getattr(tok, 'sintetico', False):
        return None

    ctx = ContextoError(tok, parser, fuente)
    for manejador in (error_incompleto_oculto,   # César  (Y4 / Y6)
                      error_y5,                  # Fátima (Y5)
                      error_y4,                  # César  (Y4)
                      error_y2,                  # César  (Y2)
                      error_y1,                  # Fátima (Y1)
                      error_y3_funcion,          # Elkin  (Y3)
                      error_incompleto,          # Elkin  (Y6)
                      error_y6):                 # Elkin  (Y6, caso general)
        resultado = manejador(ctx)
        if resultado is not NO_APLICA:
            return resultado
    return None


def _fin_de_archivo(fuente):
    """Token de referencia (línea de la última sentencia) para el fin de archivo."""
    t = lex.LexToken()
    t.type, t.value, t.lexpos, t.columna = 'NEWLINE', '', 0, 1
    t.lineno = fuente.ultima_linea
    return t
# FIN aporte: Fátima Torres (infraestructura de errores)


# ===========================================================================
# 6. CLASE DEL ANALIZADOR
# ===========================================================================
class _FuenteTokens:
    """Entrega al parser los tokens del léxico; permite devolver un token."""

    def __init__(self, lexico):
        self.lexico = lexico
        self.cola = []
        self.previo = None            # tipo del token entregado antes del actual
        self.ultimo = None            # tipo del último token entregado
        self.hist = []                # últimos tokens reales entregados
        self.ultima_linea = 1

    def input(self, codigo):
        self.lexico.input(codigo)

    def devolver(self, tok, delante=False):
        """Vuelve a poner `tok` en el flujo. Con delante=True va antes de los
        que ya estaban devueltos."""
        if delante:
            self.cola.insert(0, tok)
        else:
            self.cola.append(tok)

    def token(self):
        tok = self.cola.pop(0) if self.cola else self.lexico.token()
        self.previo = self.ultimo
        if tok is None:
            return None
        if not getattr(tok, 'sintetico', False) and (not self.hist or tok is not self.hist[-1]):
            self.hist = (self.hist + [tok])[-5:]
        self.ultimo = tok.type
        if not getattr(tok, 'sintetico', False):
            self.ultima_linea = tok.lineno
        return tok


class AnalizadorSintactico:
    """Analizador sintáctico: tokens (AnalizadorLexico) -> AST + errores Yn."""

    def __init__(self):
        self.lexico = AnalizadorLexico()
        self.parser = yacc.yacc(module=sys.modules[__name__], debug=False,
                                write_tables=False, errorlog=yacc.NullLogger())

    def analizar(self, codigo):
        """Devuelve (ast, errores_sintacticos, errores_lexicos).

        `ast` es None si hubo errores sintácticos.
        """
        if not codigo.endswith('\n'):
            codigo += '\n'                     # la última sentencia debe cerrar
        fuente = _FuenteTokens(self.lexico)
        _ctx.update(parser=self.parser, fuente=fuente, errores=[], repeticiones={})
        arbol = self.parser.parse(codigo, lexer=fuente)
        errores = list(_ctx['errores'])
        if errores:
            arbol = None
        return arbol, errores, list(self.lexico.errores)


# ---------------------------------------------------------------------------
# Utilidades para el log
# ---------------------------------------------------------------------------
NOMBRES_CONSTRUCCIONES = [
    ('impresion', 'Impresión (fmt.Println)'),
    ('lectura', 'Ingreso por teclado (fmt.Scanln)'),
    ('aritmetica', 'Expresiones aritméticas (operadores + - * / %)'),
    ('menos_unario', 'Menos unario'),
    ('comparacion', 'Comparaciones (== != < <= > >=)'),
    ('logica', 'Conectores lógicos (&& ||)'),
    ('not', 'Negación (!)'),
    ('var', 'Declaración con var'),
    ('declare', 'Declaración corta (:=)'),
    ('const', 'Constantes (const)'),
    ('asignacion', 'Asignaciones (=, +=, -=)'),
    ('incdec', 'Incremento/decremento (++, --)'),
    ('arreglo', 'Literales de arreglo'),
    ('slice', 'Literales de slice'),
    ('mapa', 'Literales de mapa'),
    ('indice', 'Accesos por índice o clave'),
    ('if', 'Estructuras if / if-else'),
    ('for_condicion', 'Estructuras for con condición'),
    ('for_clasico', 'Estructuras for clásico'),
    ('switch', 'Estructuras switch'),
    ('break', 'break'),
    ('continue', 'continue'),
    ('func', 'Definiciones de función'),
    ('llamada', 'Llamadas a función'),
    ('return', 'return'),
]


def contar_construcciones(arbol):
    """Cuenta cuántos nodos de cada tipo hay en el AST."""
    cuenta = Counter()

    def visitar(x):
        if isinstance(x, Nodo):
            cuenta[x.tipo] += 1
            for h in x.hijos:
                visitar(h)
        elif isinstance(x, list):
            for h in x:
                visitar(h)

    visitar(arbol)
    return cuenta


def formatear_ast(x, nivel=0):
    """Texto con sangría del AST (para depurar)."""
    sang = '  ' * nivel
    if isinstance(x, Nodo):
        simples = [h for h in x.hijos if not isinstance(h, (Nodo, list))]
        cab = '%s%s (línea %s)%s' % (
            sang, x.tipo, x.linea, ' ' + ' '.join(map(str, simples)) if simples else '')
        partes = [cab]
        for h in x.hijos:
            if isinstance(h, (Nodo, list)):
                partes.append(formatear_ast(h, nivel + 1))
        return '\n'.join(partes)
    if isinstance(x, list):
        return '\n'.join(formatear_ast(h, nivel) for h in x)
    return '%s%s' % (sang, x)
