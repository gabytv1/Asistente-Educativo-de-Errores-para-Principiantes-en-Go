# -*- coding: utf-8 -*-
"""Pruebas del resaltado de sintaxis del editor (resaltado.py), sin Tkinter."""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from resaltado import COLORES, resaltar  # noqa: E402


def etiquetas(codigo):
    """{texto: etiqueta} de cada tramo (si un texto se repite, queda el último)."""
    return {codigo[a:b]: t for t, a, b in resaltar(codigo)}


class PruebasResaltado(unittest.TestCase):
    def test_palabras_reservadas_tipos_y_constantes(self):
        e = etiquetas('package main\nimport "fmt"\nfunc f() {\n\tvar x int = 5\n\tif true {\n\t}\n}')
        self.assertEqual(e['package'], 'declaracion')
        self.assertEqual(e['func'], 'declaracion')
        self.assertEqual(e['var'], 'declaracion')
        self.assertEqual(e['import'], 'control')
        self.assertEqual(e['if'], 'control')
        self.assertEqual(e['int'], 'tipo')
        self.assertEqual(e['true'], 'constante')
        self.assertEqual(e['5'], 'numero')

    def test_paquete_y_funciones(self):
        e = etiquetas('package main\nfunc suma(a int) int {\n\tfmt.Println(suma(1))\n}')
        self.assertEqual(e['main'], 'paquete')
        self.assertEqual(e['fmt'], 'paquete')
        self.assertEqual(e['suma'], 'funcion')
        self.assertEqual(e['Println'], 'funcion')
        self.assertNotIn('a', e)                 # una variable no se pinta

    def test_cadena_con_escape(self):
        codigo = 'x := "Hola\\n"'
        self.assertEqual([(t, codigo[a:b]) for t, a, b in resaltar(codigo)
                          if t in ('cadena', 'escape')],
                         [('cadena', '"Hola\\n"'), ('escape', '\\n')])

    def test_las_palabras_dentro_de_cadenas_y_comentarios_no_son_codigo(self):
        codigo = 'x := "for if"\n// func var\n/* return */'
        self.assertEqual({t for t, _, _ in resaltar(codigo)},
                         {'cadena', 'comentario'})

    def test_codigo_con_errores_no_falla(self):
        for codigo in ('x := "sin cerrar\ny := 1', '/* sin cerrar\nfor', "'hola'", ''):
            resaltar(codigo)                      # no debe lanzar excepciones
        self.assertEqual(resaltar('/* sin cerrar')[0][0], 'comentario')

    def test_todas_las_etiquetas_tienen_color(self):
        usadas = {t for t, _, _ in resaltar(
            'package main\nimport "fmt"\n// c\nfunc f() { var x float64 = 1.5\n'
            'fmt.Println("a\\n", true) }')}
        self.assertTrue(usadas <= set(COLORES))


if __name__ == '__main__':
    unittest.main()
