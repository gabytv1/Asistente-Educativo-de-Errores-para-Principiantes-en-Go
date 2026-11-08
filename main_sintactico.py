# -*- coding: utf-8 -*-
"""
Ejecuta el analizador sintáctico sobre un archivo Go y genera un log en logs/.

Uso:
    python main_sintactico.py algoritmos/algoritmo1.go gabytv1
    python main_sintactico.py algoritmos/algoritmo1.go gabytv1 --ast   (imprime el AST)

El log se llama:  sintactico-usuarioGit-DDMMAAAA-HHhMM.txt
Ejemplo:          sintactico-gabytv1-07112026-20h45.txt
"""
import os
import sys
from datetime import datetime

from sintactico import (AnalizadorSintactico, NOMBRES_CONSTRUCCIONES,
                        contar_construcciones, formatear_ast)

CARPETA_LOGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')


def nombre_log(usuario_git, ahora):
    """sintactico-gabytv1-07112026-20h45.txt"""
    return 'sintactico-%s-%s.txt' % (usuario_git, ahora.strftime('%d%m%Y-%Hh%M'))


def construir_log(usuario_git, ruta_archivo, ahora, arbol, errores, errores_lex):
    lineas = []
    sep = '=' * 78
    lineas.append(sep)
    lineas.append('ANÁLISIS SINTÁCTICO - Asistente Educativo de Errores para Go')
    lineas.append(sep)
    lineas.append('Usuario Git   : %s' % usuario_git)
    lineas.append('Archivo       : %s' % ruta_archivo)
    lineas.append('Fecha y hora  : %s' % ahora.strftime('%d-%m-%Y %H:%M'))
    lineas.append(sep)
    lineas.append('')
    lineas.append('ERRORES SINTÁCTICOS')
    lineas.append('-' * 78)
    if errores:
        for e in errores:
            lineas.append('[%s] %s' % (e['codigo'], e['mensaje']))
    else:
        lineas.append('(ninguno)')
    if errores_lex:
        lineas.append('')
        lineas.append('ERRORES LÉXICOS (corrígelos primero: pueden causar errores sintácticos)')
        lineas.append('-' * 78)
        for e in errores_lex:
            lineas.append('[%s] %s' % (e['codigo'], e['mensaje']))
    if arbol is not None:
        cuenta = contar_construcciones(arbol)
        lineas.append('')
        lineas.append('CONSTRUCCIONES RECONOCIDAS')
        lineas.append('-' * 78)
        for tipo, nombre in NOMBRES_CONSTRUCCIONES:
            if cuenta[tipo]:
                lineas.append('  %-52s %d' % (nombre, cuenta[tipo]))
    lineas.append('')
    lineas.append('RESUMEN')
    lineas.append('-' * 78)
    lineas.append('Errores sintácticos : %d' % len(errores))
    lineas.append('Errores léxicos     : %d' % len(errores_lex))
    lineas.append('Resultado           : %s' % (
        'CON ERRORES' if errores else 'SINTAXIS CORRECTA'))
    return '\n'.join(lineas) + '\n'


def ejecutar(ruta_archivo, usuario_git, carpeta_logs=CARPETA_LOGS):
    with open(ruta_archivo, encoding='utf-8') as f:
        codigo = f.read()
    arbol, errores, errores_lex = AnalizadorSintactico().analizar(codigo)
    ahora = datetime.now()
    os.makedirs(carpeta_logs, exist_ok=True)
    ruta_log = os.path.join(carpeta_logs, nombre_log(usuario_git, ahora))
    with open(ruta_log, 'w', encoding='utf-8') as f:
        f.write(construir_log(usuario_git, ruta_archivo, ahora, arbol,
                              errores, errores_lex))
    return ruta_log, arbol, errores, errores_lex


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        sys.exit(1)
    ruta = args[0]
    usuario = args[1] if len(args) > 1 else input('Usuario Git: ').strip()
    ruta_log, arbol, errores, errores_lex = ejecutar(ruta, usuario)
    print('Errores sintácticos: %d | Errores léxicos: %d' % (len(errores), len(errores_lex)))
    for e in errores:
        print('  ' + e['mensaje'])
    for e in errores_lex:
        print('  ' + e['mensaje'])
    if arbol is not None and '--ast' in sys.argv:
        print(formatear_ast(arbol))
    print('Log generado: %s' % ruta_log)


if __name__ == '__main__':
    main()
