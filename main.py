# -*- coding: utf-8 -*-
"""
Ejecuta el analizador léxico sobre un archivo Go y genera un log en logs/.

Uso:
    python main.py algoritmos/algoritmo1.go "César Balladares"

El log se llama:  lexico-NombreApellido-DD-MM-AAAA-HHhMM.txt
Ejemplo:          lexico-CesarBalladares-01-11-2026-01h20.txt
"""
import os
import sys
import unicodedata
from collections import Counter
from datetime import datetime

from lexico import AnalizadorLexico

CARPETA_LOGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')


def nombre_para_archivo(nombre):
    """'César Balladares' -> 'CesarBalladares' (sin tildes, espacios ni símbolos)."""
    sin_tildes = unicodedata.normalize('NFKD', nombre)
    sin_tildes = ''.join(c for c in sin_tildes if not unicodedata.combining(c))
    partes = [''.join(c for c in p if c.isalnum()) for p in sin_tildes.split()]
    return ''.join(p[:1].upper() + p[1:] for p in partes if p)


def construir_log(desarrollador, ruta_archivo, ahora, tokens, errores):
    lineas = []
    sep = '=' * 78
    lineas.append(sep)
    lineas.append('ANÁLISIS LÉXICO - Asistente Educativo de Errores para Go')
    lineas.append(sep)
    lineas.append('Desarrollador : %s' % desarrollador)
    lineas.append('Archivo       : %s' % ruta_archivo)
    lineas.append('Fecha y hora  : %s' % ahora.strftime('%d-%m-%Y %H:%M'))
    lineas.append(sep)
    lineas.append('')
    lineas.append('TOKENS RECONOCIDOS')
    lineas.append('%-6s %-5s %-15s %s' % ('LÍNEA', 'COL.', 'TOKEN', 'LEXEMA'))
    lineas.append('-' * 78)
    for t in tokens:
        lineas.append('%-6d %-5d %-15s %s' % (t.lineno, t.columna, t.type, t.value))
    lineas.append('')
    lineas.append('ERRORES LÉXICOS')
    lineas.append('-' * 78)
    if errores:
        for e in errores:
            lineas.append('[%s] %s' % (e['codigo'], e['mensaje']))
    else:
        lineas.append('(ninguno)')
    lineas.append('')
    lineas.append('RESUMEN')
    lineas.append('-' * 78)
    lineas.append('Total de tokens reconocidos : %d' % len(tokens))
    lineas.append('Tipos de token distintos    : %d' % len({t.type for t in tokens}))
    lineas.append('Errores léxicos             : %d' % len(errores))
    lineas.append('Resultado                   : %s' % (
        'CON ERRORES' if errores else 'SIN ERRORES'))
    lineas.append('')
    lineas.append('Frecuencia por tipo de token:')
    for tipo, n in sorted(Counter(t.type for t in tokens).items()):
        lineas.append('  %-15s %d' % (tipo, n))
    return '\n'.join(lineas) + '\n'


def ejecutar(ruta_archivo, desarrollador, carpeta_logs=CARPETA_LOGS):
    with open(ruta_archivo, encoding='utf-8') as f:
        codigo = f.read()
    analizador = AnalizadorLexico()
    tokens, errores = analizador.analizar(codigo)
    ahora = datetime.now()
    os.makedirs(carpeta_logs, exist_ok=True)
    nombre_log = 'lexico-%s-%s.txt' % (
        nombre_para_archivo(desarrollador), ahora.strftime('%d-%m-%Y-%Hh%M'))
    ruta_log = os.path.join(carpeta_logs, nombre_log)
    with open(ruta_log, 'w', encoding='utf-8') as f:
        f.write(construir_log(desarrollador, ruta_archivo, ahora, tokens, errores))
    return ruta_log, tokens, errores


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    ruta = sys.argv[1]
    desarrollador = sys.argv[2] if len(sys.argv) > 2 else input('Nombre del desarrollador: ').strip()
    ruta_log, tokens, errores = ejecutar(ruta, desarrollador)
    print('Tokens reconocidos: %d | Errores léxicos: %d' % (len(tokens), len(errores)))
    for e in errores:
        print('  ' + e['mensaje'])
    print('Log generado: %s' % ruta_log)


if __name__ == '__main__':
    main()
