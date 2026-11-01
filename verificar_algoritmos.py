# -*- coding: utf-8 -*-
"""Verifica los algoritmos de prueba.

Para cada archivo de algoritmos/ muestra cuántos tokens reconoce el analizador,
cuántos tipos de token distintos cubre (de los definidos) y cuáles faltan, y si
compila con el compilador oficial de Go (si `go` está instalado)

Uso:  python verificar_algoritmos.py
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

from lexico import AnalizadorLexico, tokens

RAIZ = os.path.dirname(os.path.abspath(__file__))


def compila_con_go(ruta):
    if shutil.which('go') is None:
        return 'go no instalado (omitido)'
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(ruta, os.path.join(tmp, 'main.go'))
        r = subprocess.run(['go', 'build', '-o', os.path.join(tmp, 'salida'), 'main.go'],
                           cwd=tmp, capture_output=True, text=True)
        return 'compila' if r.returncode == 0 else 'NO compila: ' + r.stderr.strip()


def main():
    todos = set(tokens)
    ok = True
    for ruta in sorted(glob.glob(os.path.join(RAIZ, 'algoritmos', '*.go'))):
        with open(ruta, encoding='utf-8') as f:
            toks, errs = AnalizadorLexico().analizar(f.read())
        usados = {t.type for t in toks}
        faltan = sorted(todos - usados)
        print('%s' % os.path.relpath(ruta, RAIZ))
        print('  tokens: %d | tipos distintos: %d de %d | errores léxicos: %d'
              % (len(toks), len(usados), len(todos), len(errs)))
        print('  faltan: %s' % (', '.join(faltan) if faltan else '(ninguno)'))
        estado = compila_con_go(ruta)
        print('  Go: %s' % estado)
        ok = ok and not errs and not estado.startswith('NO')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
