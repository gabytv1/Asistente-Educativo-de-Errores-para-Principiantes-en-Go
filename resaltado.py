# -*- coding: utf-8 -*-
"""
Resaltado de sintaxis del editor (colores al estilo de VS Code, tema claro).

Este módulo no usa Tkinter: recibe el texto y devuelve qué tramos llevan qué
etiqueta de color. gui.py aplica esas etiquetas al editor. No es un analizador
(no usa PLY): es una clasificación rápida por expresiones regulares que
tolera código con errores, como cadenas sin cerrar o comentarios sin cerrar.
"""
import re

# Etiqueta -> color de texto (tema claro de VS Code).
COLORES = {
    'declaracion': '#0000FF',   # package, func, var, const, map
    'control':     '#AF00DB',   # import, if, else, for, switch, case, return...
    'tipo':        '#267F99',   # int, float64, string, bool
    'paquete':     '#267F99',   # fmt y el nombre tras package
    'funcion':     '#795E26',   # nombres de funciones y Println, Scanln
    'cadena':      '#A31515',   # "texto"
    'escape':      '#EE0000',   # \n, \t, \" dentro de una cadena
    'numero':      '#098658',   # 42, 3.14
    'constante':   '#0000FF',   # true, false
    'comentario':  '#008000',   # // y /* */
}

DECLARACION = {'package', 'func', 'var', 'const', 'map'}
CONTROL = {'import', 'if', 'else', 'for', 'switch', 'case', 'default',
           'break', 'continue', 'return',
           # palabras de Go fuera del subconjunto (el léxico las reporta, L7)
           'range', 'type', 'struct', 'interface', 'chan', 'select', 'go',
           'defer', 'goto', 'fallthrough'}
TIPOS = {'int', 'float64', 'string', 'bool'}
CONSTANTES = {'true', 'false'}

_PATRON = re.compile(r'''
    (?P<comentario> //[^\n]* | /\*.*?(?:\*/|\Z) )
  | (?P<cadena>     "(?:[^"\\\n]|\\.)*(?:"|\\?(?=\n|\Z)) )
  | (?P<simple>     '(?:[^'\\\n]|\\.)*'? )
  | (?P<numero>     [0-9]+(?:\.[0-9]+)? )
  | (?P<ident>      [^\W\d]\w* )
''', re.VERBOSE | re.DOTALL)

_ESCAPE = re.compile(r'\\.')


def resaltar(texto):
    """Lista de (etiqueta, inicio, fin) con posiciones de carácter en `texto`."""
    tramos = []
    anterior = None            # última palabra o símbolo significativo
    for m in _PATRON.finditer(texto):
        tipo, a, b = m.lastgroup, m.start(), m.end()
        if tipo == 'comentario':
            tramos.append(('comentario', a, b))
        elif tipo in ('cadena', 'simple'):
            tramos.append(('cadena', a, b))
            for e in _ESCAPE.finditer(texto, a + 1, b):
                tramos.append(('escape', e.start(), e.end()))
        elif tipo == 'numero':
            tramos.append(('numero', a, b))
        else:
            palabra = m.group()
            siguiente = texto[b:b + 1] if b < len(texto) else ''
            if palabra in DECLARACION:
                etiqueta = 'declaracion'
            elif palabra in CONTROL:
                etiqueta = 'control'
            elif palabra in TIPOS:
                etiqueta = 'tipo'
            elif palabra in CONSTANTES:
                etiqueta = 'constante'
            elif palabra == 'fmt' or anterior == 'package':
                etiqueta = 'paquete'
            elif siguiente == '(' or anterior == 'func' or palabra in ('Println', 'Scanln'):
                etiqueta = 'funcion'
            else:
                etiqueta = None
            if etiqueta:
                tramos.append((etiqueta, a, b))
            anterior = palabra
    return tramos
