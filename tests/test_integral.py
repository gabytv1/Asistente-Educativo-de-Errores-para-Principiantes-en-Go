# -*- coding: utf-8 -*-
"""Prueba integral con el programa de ejemplo de la propuesta.

Es el mismo programa del prototipo (Figura 1 de la sección 7): debe dar 69 tokens.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexico import AnalizadorLexico  # noqa: E402

PROGRAMA = '''package main

import "fmt"

func suma(a int, b int) int {
	return a + b
}

func main() {
	var total int = suma(4, 5)
	for i := 0; i < 3; i++ {
		total += i
	}
	fmt.Println("Total:", total)
}
'''


class PruebaIntegral(unittest.TestCase):

    def test_programa_de_la_propuesta_tiene_69_tokens(self):
        toks, errs = AnalizadorLexico().analizar(PROGRAMA)
        self.assertEqual(len(toks), 69)
        self.assertEqual(errs, [])

    def test_primeros_tokens_con_linea_y_columna(self):
        toks, _ = AnalizadorLexico().analizar(PROGRAMA)
        esperados = [('PACKAGE', 1, 1), ('ID', 1, 9), ('NEWLINE', 1, 13),
                     ('IMPORT', 3, 1), ('STRING_VALUE', 3, 8)]
        self.assertEqual([(t.type, t.lineno, t.columna) for t in toks[:5]], esperados)

    def test_fmt_y_sus_funciones_son_tokens_propios(self):
        # línea 14: fmt.Println("Total:", total)
        toks, _ = AnalizadorLexico().analizar(PROGRAMA)
        linea14 = [t.type for t in toks if t.lineno == 14]
        self.assertEqual(linea14[:3], ['FMT', 'DOT', 'PRINTLN'])
        self.assertNotIn('Println', [t.value for t in toks if t.type == 'ID'])

    def test_funciona_con_saltos_de_linea_de_windows(self):
        toks, errs = AnalizadorLexico().analizar(PROGRAMA.replace('\n', '\r\n'))
        self.assertEqual(len(toks), 69)
        self.assertEqual(errs, [])


if __name__ == '__main__':
    unittest.main()
