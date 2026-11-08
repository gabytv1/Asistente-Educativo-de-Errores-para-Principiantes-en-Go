# -*- coding: utf-8 -*-
"""Pruebas del analizador sintáctico (Avance 2). Cada clase es de un integrante."""
import os
import re
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import main_sintactico  # noqa: E402
from sintactico import AnalizadorSintactico, Nodo, contar_construcciones  # noqa: E402

PARSER = AnalizadorSintactico()


def programa(cuerpo, extra=''):
    """Envuelve las sentencias de `cuerpo` dentro de main()."""
    lineas = ''.join('\t%s\n' % l for l in cuerpo.strip('\n').split('\n'))
    return 'package main\n\nimport "fmt"\n\n%sfunc main() {\n%s}\n' % (extra, lineas)


def analizar(codigo):
    return PARSER.analizar(codigo)


def errores(codigo):
    return [e['codigo'] for e in analizar(codigo)[1]]


def sin_errores(test, codigo):
    arbol, errs, _ = analizar(codigo)
    test.assertEqual([e['mensaje'] for e in errs], [])
    test.assertIsNotNone(arbol)
    return arbol


def sentencias_main(arbol):
    """Lista de sentencias del cuerpo de la última función (main)."""
    funcion = arbol.hijos[2][-1]
    return funcion.hijos[3].hijos[0]


def leer(ruta):
    with open(os.path.join(RAIZ, ruta), encoding='utf-8') as f:
        return f.read()


# INICIO aporte: Fátima Torres
class PruebasFatima(unittest.TestCase):

    def test_var_con_tipo_y_con_tipo_y_valor(self):
        sin_errores(self, programa('var edad int\nvar nombre string = "Ana"\nvar ok bool = true'))

    def test_arreglo_declaracion_inicializacion_y_acceso(self):
        arbol = sin_errores(self, programa(
            'var notas [3]int = [3]int{10, 8, 9}\nprimera := notas[0]\nnotas[1] = 7'))
        self.assertEqual(contar_construcciones(arbol)['arreglo'], 1)
        self.assertEqual(contar_construcciones(arbol)['indice'], 2)

    def test_expresion_booleana_respeta_precedencia(self):
        arbol = sin_errores(self, programa('r := a == 1 || b > 2 && !(c < 3)'))
        expr = sentencias_main(arbol)[0].hijos[1][0]
        self.assertEqual((expr.tipo, expr.hijos[0]), ('logica', '||'))   # || es la raíz
        self.assertEqual(expr.hijos[2].hijos[0], '&&')                    # && va debajo

    def test_if_if_else_y_else_if(self):
        arbol = sin_errores(self, programa(
            'if x > 0 {\n\tx++\n}\n'
            'if x > 0 {\n\tx++\n} else {\n\tx--\n}\n'
            'if x > 0 {\n\tx++\n} else if x < 0 {\n\tx--\n} else {\n\tx = 0\n}'))
        self.assertEqual(contar_construcciones(arbol)['if'], 4)

    def test_funcion_con_un_retorno(self):
        arbol = sin_errores(self, programa(
            'r := suma(1, 2)',
            'func suma(a int, b int) int {\n\treturn a + b\n}\n\n'))
        f = arbol.hijos[2][0]
        self.assertEqual((f.tipo, f.hijos[0], f.hijos[2]), ('func', 'suma', ['int']))

    def test_Y1_falta_llave_en_for_if_func_y_switch(self):
        casos = {
            'for': programa('for i := 0; i < 3; i++\n\tx++\n}'),
            'if': programa('if x > 0\n\tx++\n}'),
            'switch': programa('switch x\n\tcase 1:\n\t\tx++\n}'),
            'func': 'package main\n\nfunc f(a int) int\n\treturn a\n}\n',
        }
        for nombre, codigo in casos.items():
            arbol, errs, _ = analizar(codigo)
            self.assertEqual([e['codigo'] for e in errs], ['Y1'], nombre)
            self.assertIn('abre el bloque con', errs[0]['mensaje'])

    def test_Y1_se_recupera_y_no_genera_errores_en_cascada(self):
        self.assertEqual(errores(programa('if x > 0\n\tx++\n}\nx = 1')), ['Y1'])

    def test_Y5_else_en_otra_linea(self):
        arbol, errs, _ = analizar(programa('if x > 0 {\n\tx++\n}\nelse {\n\tx--\n}'))
        self.assertEqual([e['codigo'] for e in errs], ['Y5'])
        self.assertIn("'else' debe ir en la misma línea", errs[0]['mensaje'])
        self.assertIn('[línea 9]', errs[0]['mensaje'])


# FIN aporte: Fátima Torres








if __name__ == '__main__':
    unittest.main()
