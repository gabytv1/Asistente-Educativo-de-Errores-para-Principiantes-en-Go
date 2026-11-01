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



# ---------------------------------------------------------------------------
# INICIO aporte: César Balladares
# ---------------------------------------------------------------------------
class PruebasCesar(unittest.TestCase):

    def test_identificadores_y_literales(self):
        tipos, errs = analizar('edad total_1 _aux 42 3.14 "Hola" true false')
        self.assertEqual(tipos, ['ID', 'ID', 'ID', 'INTEGER_VALUE', 'FLOAT_VALUE',
                                 'STRING_VALUE', 'TRUE', 'FALSE'])
        self.assertEqual(errs, [])

    def test_valores_numericos_se_convierten(self):
        toks, _ = AnalizadorLexico().analizar('42 3.14')
        self.assertEqual([t.value for t in toks], [42, 3.14])

    def test_cadena_con_espacios_y_acentos(self):
        tipos, errs = analizar('"Hola mundo, qué tal"')
        self.assertEqual(tipos, ['STRING_VALUE'])
        self.assertEqual(errs, [])

    def test_nombres_de_tipo(self):
        tipos, _ = analizar('int float64 string bool')
        self.assertEqual(tipos, ['TYPE_INT', 'TYPE_FLOAT64', 'TYPE_STRING', 'TYPE_BOOL'])

    def test_identificador_distingue_mayusculas(self):
        tipos, _ = analizar('Edad edad For')
        self.assertEqual(tipos, ['ID', 'ID', 'ID'])      # For no es la palabra for

    def test_newline_despues_de_literal_o_id(self):
        tipos, _ = analizar('42\nx\n"a"\n')
        self.assertEqual(tipos, ['INTEGER_VALUE', 'NEWLINE', 'ID', 'NEWLINE',
                                 'STRING_VALUE', 'NEWLINE'])

    def test_error_L1_caracter_ilegal(self):
        tipos, errs = analizar('x @ 3')
        self.assertEqual([e['codigo'] for e in errs], ['L1'])
        self.assertEqual((errs[0]['linea'], errs[0]['columna']), (1, 3))
        self.assertIn("'@'", errs[0]['mensaje'])
        self.assertEqual(tipos, ['ID', 'INTEGER_VALUE'])  # el análisis continúa

    def test_error_L2_cadena_sin_cerrar(self):
        tipos, errs = analizar('"Hola')
        self.assertEqual([e['codigo'] for e in errs], ['L2'])
        self.assertEqual((errs[0]['linea'], errs[0]['columna']), (1, 1))
        self.assertEqual(tipos, [])

    def test_error_L3_numero_mal_formado(self):
        _, errs = analizar('12abc\n3.14.15')
        self.assertEqual([e['codigo'] for e in errs], ['L3', 'L3'])
        self.assertIn("'12abc'", errs[0]['mensaje'])
        self.assertIn("'3.14.15'", errs[1]['mensaje'])
        self.assertEqual((errs[1]['linea'], errs[1]['columna']), (2, 1))

    def test_varios_errores_en_un_archivo(self):
        _, errs = analizar('@\n"abc\n7x')
        self.assertEqual([e['codigo'] for e in errs], ['L1', 'L2', 'L3'])
# FIN aporte: César Balladares


# ---------------------------------------------------------------------------
# INICIO aporte: Elkin Salazar
# ---------------------------------------------------------------------------
class PruebasElkin(unittest.TestCase):

    def test_operadores_de_dos_caracteres(self):
        tipos, errs = analizar(':= == != <= >= && || ++ -- += -=')
        self.assertEqual(tipos, ['DECLARE', 'EQ', 'NE', 'LE', 'GE', 'AND', 'OR',
                                 'INC', 'DEC', 'PLUS_ASSIGN', 'MINUS_ASSIGN'])
        self.assertEqual(errs, [])

    def test_operadores_de_un_caracter(self):
        tipos, errs = analizar('+ - * / % = < > ! &')
        self.assertEqual(tipos, ['PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 'ASSIGN',
                                 'LT', 'GT', 'NOT', 'ADDR'])
        self.assertEqual(errs, [])

    def test_dos_caracteres_no_se_separan(self):
        tipos, _ = analizar('a:=b==c!=d<=e>=f')
        self.assertEqual(tipos, ['ID', 'DECLARE', 'ID', 'EQ', 'ID', 'NE', 'ID',
                                 'LE', 'ID', 'GE', 'ID'])

    def test_division_no_se_confunde_con_comentario(self):
        tipos, _ = analizar('a / b // resto es comentario')
        self.assertEqual(tipos, ['ID', 'DIVIDE', 'ID'])

    def test_map_es_palabra_reservada(self):
        tipos, _ = analizar('map[string]int')
        self.assertEqual(tipos, ['MAP', 'LBRACKET', 'TYPE_STRING', 'RBRACKET', 'TYPE_INT'])

    def test_incremento_y_asignacion_compuesta(self):
        tipos, _ = analizar('i++\ntotal += 5\nx -= 1\ny--')
        self.assertEqual(tipos, ['ID', 'INC', 'NEWLINE', 'ID', 'PLUS_ASSIGN',
                                 'INTEGER_VALUE', 'NEWLINE', 'ID', 'MINUS_ASSIGN',
                                 'INTEGER_VALUE', 'NEWLINE', 'ID', 'DEC'])

    def test_direccion_en_scanln(self):
        tipos, _ = analizar('fmt.Scanln(&edad)')
        self.assertEqual(tipos, ['ID', 'DOT', 'ID', 'LPAREN', 'ADDR', 'ID', 'RPAREN'])

    def test_error_L5_operador_incompleto(self):
        tipos, errs = analizar('if a | b {')
        self.assertEqual([e['codigo'] for e in errs], ['L5'])
        self.assertEqual((errs[0]['linea'], errs[0]['columna']), (1, 6))
        self.assertIn("'||'", errs[0]['mensaje'])
        self.assertNotIn('OR', tipos)

    def test_or_valido_no_genera_error(self):
        tipos, errs = analizar('a || b')
        self.assertEqual(tipos, ['ID', 'OR', 'ID'])
        self.assertEqual(errs, [])

    def test_algoritmo3_usa_todos_mis_tokens(self):
        ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'algoritmos', 'algoritmo3.go')
        with open(ruta, encoding='utf-8') as f:
            toks, errs = AnalizadorLexico().analizar(f.read())
        self.assertEqual(errs, [])
        usados = {t.type for t in toks}
        self.assertEqual(set(lexico.tokens_operadores) - usados, set())
# FIN aporte: Elkin Salazar


if __name__ == '__main__':
    unittest.main()
