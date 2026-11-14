# -*- coding: utf-8 -*-
"""
Ejecuta el análisis léxico, sintáctico y semántico sobre un archivo Go y
genera un log de los errores semánticos en logs/.

Uso:
    python main_semantico.py algoritmos/algoritmo1.go gabytv1
    python main_semantico.py algoritmos/algoritmo1.go gabytv1 --simbolos   (imprime la tabla de símbolos)

El log se llama:  semantico-usuarioGit-DDMMAAAA-HHhMM.txt
Ejemplo:          semantico-rasaraguro-20112026-23h32.txt

El análisis semántico solo se ejecuta si el código no tiene errores léxicos ni
sintácticos (el AST no es confiable en ese caso); si los tiene, el log los
lista y explica que primero deben corregirse.
"""
import os
import sys
from datetime import datetime

from semantico import AnalizadorSemantico, CATEGORIAS
from sintactico import AnalizadorSintactico

CARPETA_LOGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')


def nombre_log(usuario_git, ahora):
    """semantico-rasaraguro-20112026-23h32.txt"""
    return 'semantico-%s-%s.txt' % (usuario_git, ahora.strftime('%d%m%Y-%Hh%M'))


def construir_log(usuario_git, ruta_archivo, ahora, ejecutado, errores,
                  errores_sint, errores_lex, simbolos):
    lineas = []
    sep = '=' * 78
    lineas.append(sep)
    lineas.append('ANÁLISIS SEMÁNTICO - Asistente Educativo de Errores para Go')
    lineas.append(sep)
    lineas.append('Usuario Git   : %s' % usuario_git)
    lineas.append('Archivo       : %s' % ruta_archivo)
    lineas.append('Fecha y hora  : %s' % ahora.strftime('%d-%m-%Y %H:%M'))
    lineas.append(sep)
    lineas.append('')
    lineas.append('ESTADO DE LOS ANÁLISIS PREVIOS')
    lineas.append('-' * 78)
    lineas.append('Análisis léxico     : %s' % (
        'sin errores' if not errores_lex else '%d error(es)' % len(errores_lex)))
    lineas.append('Análisis sintáctico : %s' % (
        'sin errores' if not errores_sint else '%d error(es)' % len(errores_sint)))
    if not ejecutado:
        lineas.append('')
        lineas.append('El análisis semántico NO se ejecutó: corrige primero los '
                      'errores léxicos y sintácticos.')
        for e in errores_lex + errores_sint:
            lineas.append('[%s] %s' % (e['codigo'], e['mensaje']))
    lineas.append('')
    lineas.append('ERRORES SEMÁNTICOS')
    lineas.append('-' * 78)
    if not ejecutado:
        lineas.append('(no evaluados)')
    elif errores:
        for e in errores:
            lineas.append('[%s] %s' % (e['codigo'], e['mensaje']))
    else:
        lineas.append('(ninguno)')
    if ejecutado:
        lineas.append('')
        lineas.append('TABLA DE SÍMBOLOS (nombre, tipo, constante, ámbito, línea)')
        lineas.append('-' * 78)
        for s in simbolos:
            lineas.append('  %-14s %-36s %-10s %-24s %d' % (
                s.nombre, s.descripcion_tipo(),
                'sí' if s.es_const else 'no', s.ambito, s.linea))
    lineas.append('')
    lineas.append('RESUMEN')
    lineas.append('-' * 78)
    lineas.append('Errores léxicos     : %d' % len(errores_lex))
    lineas.append('Errores sintácticos : %d' % len(errores_sint))
    lineas.append('Errores semánticos  : %d' % len(errores))
    if ejecutado:
        for codigo, categoria in CATEGORIAS.items():
            cuantos = sum(1 for e in errores if e['codigo'] == codigo)
            if cuantos:
                lineas.append('  %s %-26s %d' % (codigo, categoria, cuantos))
    if not ejecutado:
        resultado = 'NO EJECUTADO (hay errores léxicos o sintácticos)'
    elif errores:
        resultado = 'CON ERRORES SEMÁNTICOS'
    else:
        resultado = 'SEMÁNTICA CORRECTA'
    lineas.append('Resultado           : %s' % resultado)
    return '\n'.join(lineas) + '\n'


def ejecutar(ruta_archivo, usuario_git, carpeta_logs=CARPETA_LOGS):
    """Devuelve (ruta_log, errores_sem, errores_sint, errores_lex, ejecutado, simbolos)."""
    with open(ruta_archivo, encoding='utf-8') as f:
        codigo = f.read()
    arbol, errores_sint, errores_lex = AnalizadorSintactico().analizar(codigo)
    ejecutado = arbol is not None and not errores_lex and not errores_sint
    analizador = AnalizadorSemantico()
    errores = analizador.analizar(arbol) if ejecutado else []
    simbolos = analizador.simbolos if ejecutado else []
    ahora = datetime.now()
    os.makedirs(carpeta_logs, exist_ok=True)
    ruta_log = os.path.join(carpeta_logs, nombre_log(usuario_git, ahora))
    with open(ruta_log, 'w', encoding='utf-8') as f:
        f.write(construir_log(usuario_git, ruta_archivo, ahora, ejecutado,
                              errores, errores_sint, errores_lex, simbolos))
    return ruta_log, errores, errores_sint, errores_lex, ejecutado, simbolos


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        sys.exit(1)
    ruta = args[0]
    usuario = args[1] if len(args) > 1 else input('Usuario Git: ').strip()
    ruta_log, errores, errores_sint, errores_lex, ejecutado, simbolos = \
        ejecutar(ruta, usuario)
    print('Errores léxicos: %d | Errores sintácticos: %d | Errores semánticos: %d'
          % (len(errores_lex), len(errores_sint), len(errores)))
    if not ejecutado:
        print('  El análisis semántico no se ejecutó: corrige primero los '
              'errores léxicos y sintácticos.')
        for e in errores_lex + errores_sint:
            print('  ' + e['mensaje'])
    for e in errores:
        print('  ' + e['mensaje'])
    if '--simbolos' in sys.argv and ejecutado:
        for s in simbolos:
            print('  %-14s %-36s %-5s %-24s %d' % (
                s.nombre, s.descripcion_tipo(), 'const' if s.es_const else '',
                s.ambito, s.linea))
    print('Log generado: %s' % ruta_log)


if __name__ == '__main__':
    main()
