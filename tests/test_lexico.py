# -*- coding: utf-8 -*-
"""Pruebas automáticas del analizador léxico (unittest).

Ejecutar desde la raíz del repositorio:  python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lexico  # noqa: E402
from lexico import AnalizadorLexico  # noqa: E402


def analizar(codigo):
    toks, errs = AnalizadorLexico().analizar(codigo)
    return [t.type for t in toks], errs


# ---------------------------------------------------------------------------
# INICIO aporte: Fátima Torres
# ---------------------------------------------------------------------------
class PruebasFatima(unittest.TestCase):

    def test_delimitadores(self):
        tipos, errs = analizar('( ) { } [ ] , ; : .')
        self.assertEqual(tipos, ['LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET',
                                 'RBRACKET', 'COMMA', 'SEMICOLON', 'COLON', 'DOT'])
        self.assertEqual(errs, [])

    def test_comentarios_se_descartan_y_cuentan_lineas(self):
        toks, errs = AnalizadorLexico().analizar('// hola\n/* a\nb */ )')
        self.assertEqual([t.type for t in toks], ['RPAREN'])
        self.assertEqual(toks[0].lineno, 3)
        self.assertEqual(errs, [])

    def test_newline_solo_si_cierra_sentencia(self):
        # tras '(' no hay NEWLINE; tras ')' y tras '}' sí
        tipos, _ = analizar('(\n)\n{\n}\n')
        self.assertEqual(tipos.count('NEWLINE'), 2)

    def test_error_L4_comentario_sin_cerrar(self):
        _, errs = analizar(')\n/* nota\n')
        self.assertEqual([e['codigo'] for e in errs], ['L4'])
        self.assertEqual((errs[0]['linea'], errs[0]['columna']), (2, 1))
        self.assertIn('no se cierra', errs[0]['mensaje'])

    @unittest.skipUnless('ID' in lexico.tokens, 'Pendiente: t_ID de César')
    def test_palabras_reservadas_no_son_id(self):
        tipos, errs = analizar('package import func var const if else for '
                               'switch case default break continue return')
        self.assertEqual(tipos, ['PACKAGE', 'IMPORT', 'FUNC', 'VAR', 'CONST', 'IF',
                                 'ELSE', 'FOR', 'SWITCH', 'CASE', 'DEFAULT',
                                 'BREAK', 'CONTINUE', 'RETURN'])
        self.assertEqual(errs, [])
# FIN aporte: Fátima Torres


if __name__ == '__main__':
    unittest.main()
