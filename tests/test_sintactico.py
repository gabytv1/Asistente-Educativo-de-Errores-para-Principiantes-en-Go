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


# INICIO aporte: César Balladares
class PruebasCesar(unittest.TestCase):

    def test_declaracion_corta_simple_y_multiple(self):
        arbol = sin_errores(self, programa('total := 100\na, b := 1, 2\nc, m := dividir(17, 5)',
                                           'func dividir(a int, b int) (int, int) {\n\treturn a / b, a % b\n}\n\n'))
        decl = [s for s in sentencias_main(arbol) if s.tipo == 'declare']
        self.assertEqual([d.hijos[0] for d in decl], [['total'], ['a', 'b'], ['c', 'm']])

    def test_asignacion_y_operadores_compuestos(self):
        arbol = sin_errores(self, programa('x = 1\nx += 2\nx -= 3\nx++\nx--\nv[0] += 1\nm["a"]++'))
        cuenta = contar_construcciones(arbol)
        self.assertEqual((cuenta['asignacion'], cuenta['incdec']), (4, 3))

    def test_aritmetica_precedencia_menos_unario_y_parentesis(self):
        arbol = sin_errores(self, programa('r := (a + b) * 2 - c / 4 % 3\nn := -x + 1'))
        r = sentencias_main(arbol)[0].hijos[1][0]
        self.assertEqual((r.tipo, r.hijos[0]), ('aritmetica', '-'))
        suma = sentencias_main(arbol)[0].hijos[1][0].hijos[1]
        self.assertEqual(suma.hijos[0], '*')
        self.assertEqual(contar_construcciones(arbol)['menos_unario'], 1)

    def test_aritmetica_asocia_a_la_izquierda(self):
        arbol = sin_errores(self, programa('r := 10 - 3 - 2'))
        r = sentencias_main(arbol)[0].hijos[1][0]
        self.assertEqual(r.hijos[1].tipo, 'aritmetica')      # (10 - 3) - 2
        self.assertEqual(r.hijos[2].tipo, 'literal')

    def test_for_con_condicion_y_for_clasico(self):
        arbol = sin_errores(self, programa(
            'for t < 100 {\n\tt += 10\n}\nfor i := 0; i < 5; i++ {\n\ts += i\n}'))
        cuenta = contar_construcciones(arbol)
        self.assertEqual((cuenta['for_condicion'], cuenta['for_clasico']), (1, 1))

    def test_for_clasico_con_declaracion_y_decremento(self):
        sin_errores(self, programa('for r := 5; r > 0; r-- {\n\tfmt.Println(r)\n}'))

    def test_slice_declaracion_literal_y_parametro(self):
        sin_errores(self, programa(
            'nombres := []string{"Ana", "Luis"}\nvar v []float64 = []float64{1.5, 2.0}\np := prom(v)',
            'func prom(v []float64) float64 {\n\treturn v[0]\n}\n\n'))

    def test_funcion_con_dos_retornos(self):
        arbol = sin_errores(self, programa(
            'c, m := dividir(17, 5)',
            'func dividir(a int, b int) (int, int) {\n\treturn a / b, a % b\n}\n\n'))
        self.assertEqual(arbol.hijos[2][0].hijos[2], ['int', 'int'])

    def test_llamada_como_sentencia_y_como_expresion(self):
        arbol = sin_errores(self, programa(
            'saludar("Ana")\nr := f(g(1), 2)',
            'func saludar(n string) {\n\tfmt.Println(n)\n}\n\n'))
        self.assertEqual(contar_construcciones(arbol)['llamada'], 3)

    def test_Y2_parentesis_sin_cerrar(self):
        arbol, errs, _ = analizar(programa('fmt.Println("Hola"\nx := 1'))
        self.assertEqual([e['codigo'] for e in errs], ['Y2'])
        self.assertIn("se esperaba ')'", errs[0]['mensaje'])
        self.assertIn('[línea 6]', errs[0]['mensaje'])

    def test_Y2_en_condicion_con_llave(self):
        self.assertEqual(errores(programa('if suma(1, 2 {\n\tx++\n}')), ['Y2'])

    def test_Y4_falta_el_tipo(self):
        arbol, errs, _ = analizar(programa('var edad\nx := 1'))
        self.assertEqual([e['codigo'] for e in errs], ['Y4'])
        self.assertIn("falta el tipo en la declaración de 'edad'", errs[0]['mensaje'])
        self.assertIn('var edad int', errs[0]['mensaje'])

    def test_Y4_falta_el_tipo_con_valor(self):
        self.assertEqual(errores(programa('var edad = 5')), ['Y4'])

    def test_Y4_falta_el_valor(self):
        for src in ('var edad int =', 'total :=', 'const MAX ='):
            arbol, errs, _ = analizar(programa(src + '\nx := 1'))
            self.assertEqual([e['codigo'] for e in errs], ['Y4'], src)
            self.assertIn('[línea 6]', errs[0]['mensaje'], src)


# FIN aporte: César Balladares






if __name__ == '__main__':
    unittest.main()
