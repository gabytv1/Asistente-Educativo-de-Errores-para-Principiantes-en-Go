# -*- coding: utf-8 -*-
"""
Lógica de la interfaz gráfica (sin Tkinter).

gui.py solo dibuja; todo lo que decide qué mostrar vive aquí, así se puede
probar sin abrir ventanas. Cada función analizar_* llama a las mismas
funciones ejecutar() de main.py, main_sintactico.py y main_semantico.py, por lo
que el log que genera la interfaz es idéntico al de la línea de comandos.
"""
import os
import re
from dataclasses import dataclass, field
from typing import List, Tuple

import main as _lexico_main
import main_sintactico as _sint_main
import main_semantico as _sem_main
from semantico import CATEGORIAS
from sintactico import NOMBRES_CONSTRUCCIONES, contar_construcciones

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_LOGS = os.path.join(BASE, 'logs')

# (nombre para el log léxico, usuario Git para los logs sintáctico y semántico)
DESARROLLADORES = [
    ('Fátima Torres', 'gabytv1'),
    ('César Balladares', 'CBalla-05'),
    ('Elkin Salazar', 'sElkinEspol'),
]

LEXICO, SINTACTICO, SEMANTICO = 'lexico', 'sintactico', 'semantico'
NOMBRE_ANALISIS = {LEXICO: 'léxico', SINTACTICO: 'sintáctico',
                   SEMANTICO: 'semántico'}


@dataclass
class ErrorVista:
    """Un error listo para mostrar: línea, columna (si existe) y texto."""
    codigo: str
    linea: int
    columna: int
    tipo: str          # 'Léxico', 'Sintáctico' o 'Semántico'
    texto: str         # mensaje sin el prefijo "Error ... [línea N]:"
    sugerencia: str


@dataclass
class Resultado:
    analisis: str
    titulo_panel: str
    columnas: List[Tuple[str, str, int]]       # (id, encabezado, ancho)
    filas: List[Tuple[tuple, str]]             # (valores, etiqueta 'error'|'')
    errores: List[ErrorVista] = field(default_factory=list)
    ejecutado: bool = True                     # False: el semántico no corrió
    resumen: str = ''
    ruta_log: str = ''
    simbolos: List[tuple] = field(default_factory=list)
    aviso: str = ''

    @property
    def ok(self):
        return self.ejecutado and not self.errores

    @property
    def lineas_error(self):
        return sorted({e.linea for e in self.errores if e.linea})

    @property
    def nombre_log(self):
        return os.path.basename(self.ruta_log)


_PREFIJO = re.compile(r'^Error \w+ \[[^\]]*\]:\s*')


def a_error_vista(error, tipo):
    """Convierte un dict de error (lexico/sintactico/semantico) en ErrorVista."""
    texto = _PREFIJO.sub('', error['mensaje'])
    sugerencia = ''
    if 'Sugerencia:' in texto:
        texto, sugerencia = texto.split('Sugerencia:', 1)
    return ErrorVista(error['codigo'], error.get('linea', 0),
                      error.get('columna', 0), tipo,
                      texto.strip(), sugerencia.strip())


COLS_ERRORES = [('linea', 'Línea', 60), ('codigo', 'Código', 70),
                ('tipo', 'Tipo', 100), ('mensaje', 'Mensaje', 520)]


def _fila_error(e):
    return ((e.linea, e.codigo, e.tipo, e.texto), 'error')


def analizar_lexico(codigo, desarrollador, ruta_mostrada, carpeta_logs=CARPETA_LOGS):
    ruta_log, tokens, errores = _lexico_main.ejecutar(
        ruta_mostrada, desarrollador, carpeta_logs, codigo=codigo)
    ev = [a_error_vista(e, 'Léxico') for e in errores]
    filas = [((e.linea, e.columna, 'ERROR LÉXICO', '[%s] %s' % (e.codigo, e.texto)),
              'error') for e in ev]
    for t in tokens:
        filas.append(((t.lineno, t.columna, t.type, t.value), ''))
    if ev:
        resumen = ('Análisis léxico completado: %d tokens válidos, %d error(es) léxico(s).'
                   % (len(tokens), len(ev)))
    else:
        resumen = ('Análisis léxico completado: %d tokens válidos, 0 errores léxicos.'
                   % len(tokens))
    return Resultado(
        LEXICO, 'Tokens reconocidos (%d)' % len(tokens),
        [('linea', 'Línea', 60), ('col', 'Col.', 60),
         ('tipo', 'Tipo de token', 190), ('lexema', 'Lexema', 380)],
        filas, ev, True, resumen, ruta_log)


def analizar_sintactico(codigo, usuario_git, ruta_mostrada, carpeta_logs=CARPETA_LOGS):
    ruta_log, arbol, errores, errores_lex = _sint_main.ejecutar(
        ruta_mostrada, usuario_git, carpeta_logs, codigo=codigo)
    ev = ([a_error_vista(e, 'Léxico') for e in errores_lex]
          + [a_error_vista(e, 'Sintáctico') for e in errores])
    ev.sort(key=lambda e: e.linea)
    if ev:
        filas = [_fila_error(e) for e in ev]
        titulo = 'Errores (%d)' % len(ev)
        resumen = ('Análisis sintáctico completado: %d error(es) sintáctico(s)'
                   ' y %d léxico(s).' % (len(errores), len(errores_lex)))
        columnas = COLS_ERRORES
    else:
        cuenta = contar_construcciones(arbol)
        filas = [((nombre, cuenta[tipo]), '')
                 for tipo, nombre in NOMBRES_CONSTRUCCIONES if cuenta[tipo]]
        titulo = 'Construcciones reconocidas'
        resumen = 'Análisis sintáctico completado: la sintaxis es correcta (0 errores).'
        columnas = [('construccion', 'Construcción', 420), ('cantidad', 'Cantidad', 100)]
    return Resultado(SINTACTICO, titulo, columnas, filas, ev, True, resumen, ruta_log)


def analizar_semantico(codigo, usuario_git, ruta_mostrada, carpeta_logs=CARPETA_LOGS):
    """Encadena léxico → sintáctico → semántico (el semántico solo corre si
    no hay errores previos, porque el AST no es confiable en ese caso)."""
    ruta_log, errores, errores_sint, errores_lex, ejecutado, simbolos = \
        _sem_main.ejecutar(ruta_mostrada, usuario_git, carpeta_logs, codigo=codigo)
    tabla = [(s.nombre, s.descripcion_tipo(), 'sí' if s.es_const else 'no',
              s.ambito, s.linea) for s in simbolos]
    if not ejecutado:
        ev = ([a_error_vista(e, 'Léxico') for e in errores_lex]
              + [a_error_vista(e, 'Sintáctico') for e in errores_sint])
        ev.sort(key=lambda e: e.linea)
        return Resultado(
            SEMANTICO, 'Errores previos (%d)' % len(ev), COLS_ERRORES,
            [_fila_error(e) for e in ev], ev, False,
            'El análisis semántico no se ejecutó: corrige primero los errores '
            'léxicos y sintácticos.', ruta_log, tabla,
            'Se detectaron %d error(es) léxico(s) y %d sintáctico(s).'
            % (len(errores_lex), len(errores_sint)))
    ev = [a_error_vista(e, 'Semántico') for e in errores]
    cols = [('linea', 'Línea', 60), ('regla', 'Regla', 60),
            ('categoria', 'Categoría', 200), ('mensaje', 'Mensaje', 440)]
    filas = [((e.linea, e.codigo, CATEGORIAS.get(e.codigo, ''), e.texto), 'error')
             for e in ev]
    if ev:
        resumen = ('Análisis semántico completado: %d error(es) semántico(s).' % len(ev))
    else:
        resumen = 'Análisis semántico completado: la semántica es correcta (0 errores).'
    return Resultado(SEMANTICO, 'Errores semánticos (%d)' % len(ev), cols, filas,
                     ev, True, resumen, ruta_log, tabla)


COLUMNAS_SIMBOLOS = [('nombre', 'Nombre', 130), ('tipo', 'Tipo', 230),
                     ('const', 'Constante', 100), ('ambito', 'Ámbito', 170),
                     ('linea', 'Línea', 60)]


def analizar(tipo, codigo, indice_dev, ruta_mostrada, carpeta_logs=CARPETA_LOGS):
    """Punto de entrada de la GUI. indice_dev elige a la persona de DESARROLLADORES."""
    nombre, usuario = DESARROLLADORES[indice_dev]
    if tipo == LEXICO:
        return analizar_lexico(codigo, nombre, ruta_mostrada, carpeta_logs)
    if tipo == SINTACTICO:
        return analizar_sintactico(codigo, usuario, ruta_mostrada, carpeta_logs)
    if tipo == SEMANTICO:
        return analizar_semantico(codigo, usuario, ruta_mostrada, carpeta_logs)
    raise ValueError('análisis desconocido: %r' % (tipo,))


def ruta_para_log(ruta):
    """Ruta que se escribe en el log: relativa al proyecto si está dentro de él."""
    if not ruta:
        return '(editor, sin guardar)'
    try:
        rel = os.path.relpath(ruta, BASE)
    except ValueError:             # otra unidad en Windows
        return ruta
    return ruta if rel.startswith('..') else rel.replace('\\', '/')
