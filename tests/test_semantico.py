# -*- coding: utf-8 -*-
"""Pruebas del analizador semántico (Avance 3). Cada clase es de un integrante."""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from semantico import AnalizadorSemantico  # noqa: E402
from sintactico import AnalizadorSintactico  # noqa: E402

PARSER = AnalizadorSintactico()


def programa(cuerpo, extra=''):
    """Envuelve las sentencias de `cuerpo` dentro de main(). La primera
    sentencia del cuerpo queda en la línea 6 si `extra` está vacío."""
    lineas = ''.join('\t%s\n' % l for l in cuerpo.strip('\n').split('\n'))
    return 'package main\n\nimport "fmt"\n\n%sfunc main() {\n%s}\n' % (extra, lineas)


def semantica(codigo):
    """Lista de errores semánticos; el código debe ser léxica y sintácticamente válido."""
    arbol, errs, errs_lex = PARSER.analizar(codigo)
    assert not errs and not errs_lex, (errs, errs_lex)
    return AnalizadorSemantico().analizar(arbol)


def codigos(codigo):
    return [e['codigo'] for e in semantica(codigo)]


def mensajes(codigo):
    return [e['mensaje'] for e in semantica(codigo)]


def leer(ruta):
    with open(os.path.join(RAIZ, ruta), encoding='utf-8') as f:
        return f.read()


# Funciones auxiliares que usan varias pruebas (van antes de main).
F_SUMA = 'func suma(a int, b int) int {\n\treturn a + b\n}\n'
F_DIVIDIR = 'func dividir(a int, b int) (int, int) {\n\treturn a / b, a % b\n}\n'
F_SALUDAR = 'func saludar(nombre string) {\n\tfmt.Println(nombre)\n}\n'


# INICIO aporte: Fátima Torres
class PruebasFatima(unittest.TestCase):
    """S1 (identificadores declarados) y S2 (constantes)."""

    # --- S1 ---
    def test_s1_variable_no_declarada(self):
        self.assertEqual(codigos(programa('resultado := total + 1\nfmt.Println(resultado)')), ['S1'])

    def test_s1_mensaje_de_la_propuesta(self):
        self.assertEqual(
            mensajes(programa('resultado := total + 1\nfmt.Println(resultado)')),
            ["Error semántico [línea 6]: la variable 'total' no ha sido declarada. "
             "Sugerencia: declárala con var o :=."])

    def test_s1_variable_del_bloque_padre_es_visible(self):
        self.assertEqual(codigos(programa('var x int = 1\nif x > 0 {\n\tx++\n}')), [])

    def test_s1_variable_de_bloque_no_es_visible_fuera(self):
        self.assertEqual(codigos(programa(
            'if true {\n\ty := 1\n\tfmt.Println(y)\n}\nfmt.Println(y)')), ['S1'])

    def test_s1_parametro_visible_en_la_funcion(self):
        self.assertEqual(codigos(programa('fmt.Println(suma(1, 2))', F_SUMA)), [])

    def test_s1_funcion_no_declarada(self):
        errs = mensajes(programa('x := triple(2)\nfmt.Println(x)'))
        self.assertEqual(len(errs), 1)
        self.assertIn("la función 'triple' no ha sido declarada", errs[0])
        self.assertIn('Sugerencia: defínela con func', errs[0])

    def test_s1_funcion_definida_despues_se_puede_llamar(self):
        codigo = ('package main\n\nimport "fmt"\n\nfunc main() {\n'
                  '\tfmt.Println(doble(4))\n}\n\n'
                  'func doble(n int) int {\n\treturn n * 2\n}\n')
        self.assertEqual(codigos(codigo), [])

    def test_s1_global_visible_dentro_de_funciones(self):
        extra = 'var g int = 3\nfunc leer() int {\n\treturn g\n}\n'
        self.assertEqual(codigos(programa('fmt.Println(leer())', extra)), [])

    def test_s1_uso_antes_de_declarar(self):
        errs = semantica(programa('x := y\ny := 1\nfmt.Println(x)'))
        self.assertEqual([(e['codigo'], e['linea']) for e in errs], [('S1', 6)])

    def test_s1_variable_del_for_clasico_no_vive_despues(self):
        self.assertEqual(codigos(programa(
            'for i := 0; i < 3; i++ {\n}\nfmt.Println(i)')), ['S1'])

    def test_s1_variable_sombreada_en_un_bloque(self):
        self.assertEqual(codigos(programa(
            'x := 1\nif true {\n\tx := "a"\n\tfmt.Println(x)\n}\nfmt.Println(x)')), [])

    def test_s1_en_lectura_asignacion_e_indice(self):
        cuerpo = 'fmt.Scanln(&n)\nz = 5\nfmt.Println(a[0])'
        self.assertEqual(codigos(programa(cuerpo)), ['S1', 'S1', 'S1'])

    # --- S2 ---
    def test_s2_reasignar_constante(self):
        errs = mensajes(programa('const PI = 3.14\nPI = 3'))
        self.assertEqual(errs, [
            "Error semántico [línea 7]: no se puede modificar la constante 'PI'. "
            "Sugerencia: usa una variable si el valor debe cambiar."])

    def test_s2_con_operador_compuesto(self):
        self.assertEqual(codigos(programa('const N = 1\nN += 2\nN -= 1')), ['S2', 'S2'])

    def test_s2_con_incremento_y_decremento(self):
        self.assertEqual(codigos(programa('const N = 1\nN++\nN--')), ['S2', 'S2'])

    def test_s2_con_scanln(self):
        self.assertEqual(codigos(programa('const N = 1\nfmt.Scanln(&N)')), ['S2'])

    def test_s2_constante_global_modificada_en_funcion(self):
        extra = 'const LIM = 5\nfunc cambiar() {\n\tLIM = 6\n}\n'
        self.assertEqual(codigos(programa('cambiar()', extra)), ['S2'])

    def test_s2_variable_se_puede_modificar_y_constante_leer(self):
        cuerpo = 'var x int = 1\nx = 2\nx += 1\nx++\nconst A = 2\nb := A * 3\nfmt.Println(b)'
        self.assertEqual(codigos(programa(cuerpo)), [])
    # --- S1: declaración repetida ---
    def test_s1_variable_repetida_en_el_mismo_ambito(self):
        cuerpo = 'var x int = 1\nvar x int = 2\nfmt.Println(x)'
        self.assertEqual(mensajes(programa(cuerpo)), [
            "Error semántico [línea 7]: el nombre 'x' ya fue declarado en este ámbito "
            "(línea 6). Sugerencia: usa otro nombre, o asigna con = si solo quieres "
            "cambiar su valor."])

    def test_s1_declaracion_corta_sin_variables_nuevas(self):
        cuerpo = 'a := 1\na := 2\nfmt.Println(a)'
        self.assertEqual(mensajes(programa(cuerpo)), [
            "Error semántico [línea 7]: no hay variables nuevas a la izquierda de :=. "
            "Sugerencia: usa = para asignar a variables que ya existen."])

    def test_s1_declaracion_corta_con_una_variable_nueva_es_valida(self):
        cuerpo = 'a := 1\na, b := 2, 3\nfmt.Println(a, b)'
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s1_mismo_nombre_en_otro_ambito_es_valido(self):
        cuerpo = 'x := 1\nif x > 0 {\n\tx := 2\n\tfmt.Println(x)\n}\nfmt.Println(x)'
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s1_funcion_repetida(self):
        extra = 'func f() {\n}\nfunc f() {\n}\n'
        self.assertEqual(codigos(programa('f()', extra)), ['S1'])

    def test_s1_variable_con_el_nombre_de_un_parametro(self):
        extra = 'func g(a int) {\n\tvar a int = 1\n\tfmt.Println(a)\n}\n'
        self.assertEqual(codigos(programa('g(1)', extra)), ['S1'])
# FIN aporte: Fátima Torres


if __name__ == '__main__':
    unittest.main()
