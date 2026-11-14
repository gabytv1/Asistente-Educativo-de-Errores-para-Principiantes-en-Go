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


# INICIO aporte: Elkin Salazar
class PruebasElkin(unittest.TestCase):
    """S5 (operaciones permitidas) y S6 (break y continue)."""

    # --- S5 ---
    def test_s5_int_mas_float_mensaje_de_la_propuesta(self):
        cuerpo = 'var a int = 5\nvar b float64 = 2.5\nc := a + b\nfmt.Println(c)'
        self.assertEqual(mensajes(programa(cuerpo)), [
            "Error semántico [línea 8]: operación '+' inválida entre int y float64. "
            "Sugerencia: usa el mismo tipo en ambos lados."])

    def test_s5_literales_mezclados_se_adaptan(self):
        self.assertEqual(codigos(programa('x := 1 + 2.0\nfmt.Println(x)')), [])

    def test_s5_literal_entero_se_adapta_a_float64(self):
        cuerpo = 'x := 2.5\ny := x * 2\nz := 2 + x\nfmt.Println(y, z, x > 1, x == 2)'
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s5_variables_de_distinto_tipo_siguen_siendo_error(self):
        cuerpo = 'n := 2\nx := 2.5\nfmt.Println(n * x)'
        self.assertEqual(codigos(programa(cuerpo)), ['S5'])

    def test_s5_constante_sin_tipo_se_adapta(self):
        cuerpo = 'const N = 10\nx := 2.5\nfmt.Println(x * N)'
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s5_division_entre_cero_literal(self):
        self.assertEqual(mensajes(programa('a := 10\nfmt.Println(a / 0)')), [
            "Error semántico [línea 7]: división entre cero con el operador '/'. "
            "Sugerencia: usa un divisor distinto de 0."])
        self.assertEqual(codigos(programa('a := 10\nfmt.Println(a % 0)')), ['S5'])

    def test_s5_division_float_entre_cero_es_valida_en_go(self):
        self.assertEqual(codigos(programa('x := 2.5\nfmt.Println(x / 0)')), [])

    def test_s5_case_literal_con_switch_float64(self):
        cuerpo = 'x := 2.5\nswitch x {\ncase 1:\n\tfmt.Println(x)\n}'
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s5_mismo_tipo_y_concatenacion_son_validos(self):
        cuerpo = 's := "a" + "b"\nt := 1.5 * 2.0\nu := 8 / 2\nfmt.Println(s, t, u)'
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s5_resta_de_cadenas(self):
        self.assertEqual(codigos(programa('s := "a" - "b"\nfmt.Println(s)')), ['S5'])

    def test_s5_suma_de_bool(self):
        self.assertEqual(codigos(programa('x := true + false\nfmt.Println(x)')), ['S5'])

    def test_s5_residuo_solo_con_enteros(self):
        self.assertEqual(codigos(programa('x := 7.5 % 2.0\nfmt.Println(x)')), ['S5'])
        self.assertEqual(codigos(programa('x := 7 % 2\nfmt.Println(x)')), [])

    def test_s5_logicos_solo_con_bool(self):
        self.assertEqual(codigos(programa('ok := 1 && true\nfmt.Println(ok)')), ['S5'])
        self.assertEqual(codigos(programa('ok := true && 1 > 0\nfmt.Println(ok)')), [])

    def test_s5_negacion_solo_con_bool(self):
        self.assertEqual(codigos(programa('x := !5\nfmt.Println(x)')), ['S5'])
        self.assertEqual(codigos(programa('x := !true\nfmt.Println(x)')), [])

    def test_s5_menos_unario_solo_con_numeros(self):
        self.assertEqual(codigos(programa('x := -"a"\nfmt.Println(x)')), ['S5'])
        self.assertEqual(codigos(programa('x := -5\ny := -2.5\nfmt.Println(x, y)')), [])

    def test_s5_comparar_tipos_distintos(self):
        self.assertEqual(codigos(programa('ok := 1 == "a"\nfmt.Println(ok)')), ['S5'])

    def test_s5_comparar_mismo_tipo_es_valido_y_da_bool(self):
        cuerpo = 'var ok bool = 1 < 2\nvar t bool = "a" != "b"\nfmt.Println(ok, t)'
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s5_comparar_slices_no_es_valido(self):
        cuerpo = 'a := []int{1}\nb := []int{2}\nok := a == b\nfmt.Println(ok)'
        self.assertEqual(codigos(programa(cuerpo)), ['S5'])

    def test_s5_indice_de_arreglo_debe_ser_entero(self):
        cuerpo = 'v := [2]int{1, 2}\nx := v["a"]\nfmt.Println(x)'
        self.assertEqual(codigos(programa(cuerpo)), ['S5'])

    def test_s5_clave_de_mapa_del_tipo_correcto(self):
        cuerpo = 'm := map[string]int{"a": 1}\nx := m[1]\ny := m["a"]\nfmt.Println(x, y)'
        self.assertEqual(codigos(programa(cuerpo)), ['S5'])

    def test_s5_indexar_un_entero(self):
        self.assertEqual(codigos(programa('n := 5\nx := n[0]\nfmt.Println(x)')), ['S5'])

    def test_s5_incremento_solo_con_numeros(self):
        self.assertEqual(codigos(programa('s := "a"\ns++')), ['S5'])
        self.assertEqual(codigos(programa('x := 1.5\nx++\nx--')), [])

    def test_s5_operadores_compuestos(self):
        self.assertEqual(codigos(programa('s := "a"\ns += "b"')), [])
        self.assertEqual(codigos(programa('s := "a"\ns -= "b"')), ['S5'])
        self.assertEqual(codigos(programa('x := 1\nx += 2.5')), ['S5'])

    def test_s5_case_con_tipo_distinto_al_switch(self):
        cuerpo = 'x := 1\nswitch x {\ncase "a":\n\tfmt.Println(1)\n}'
        self.assertEqual(codigos(programa(cuerpo)), ['S5'])

    def test_s5_llamada_que_devuelve_dos_valores_en_una_operacion(self):
        cuerpo = 'x := dividir(4, 2) + 1\nfmt.Println(x)'
        errs = mensajes(programa(cuerpo, F_DIVIDIR))
        self.assertEqual(len(errs), 1)
        self.assertIn("la función 'dividir' devuelve 2 valores", errs[0])

    def test_s5_no_encadena_errores(self):
        cuerpo = 'var a int = 1\nvar b float64 = 2.0\nc := a + b\nd := c + 1\nfmt.Println(d)'
        self.assertEqual(codigos(programa(cuerpo)), ['S5'])

    # --- S6 ---
    def test_s6_break_fuera_de_bucle(self):
        self.assertEqual(mensajes(programa('break')), [
            "Error semántico [línea 6]: 'break' fuera de un bucle o switch. "
            "Sugerencia: muévelo dentro de un for."])

    def test_s6_continue_fuera_de_bucle(self):
        self.assertEqual(mensajes(programa('continue')), [
            "Error semántico [línea 6]: 'continue' fuera de un bucle. "
            "Sugerencia: muévelo dentro de un for."])

    def test_s6_dentro_de_for_es_valido(self):
        cuerpo = ('for i := 0; i < 5; i++ {\n\tif i == 3 {\n\t\tbreak\n\t}\n\tcontinue\n}\n'
                  'x := 3\nfor x > 0 {\n\tx--\n\tbreak\n}')
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s6_break_dentro_de_switch_es_valido(self):
        cuerpo = 'x := 1\nswitch x {\ncase 1:\n\tbreak\n}'
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s6_continue_en_switch_sin_for(self):
        cuerpo = 'x := 1\nswitch x {\ncase 1:\n\tcontinue\n}'
        self.assertEqual(codigos(programa(cuerpo)), ['S6'])

    def test_s6_continue_en_switch_dentro_de_for(self):
        cuerpo = ('for i := 0; i < 3; i++ {\n\tswitch i {\n\tcase 1:\n\t\tcontinue\n\t}\n}')
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s6_break_despues_de_cerrar_el_bucle(self):
        cuerpo = 'for i := 0; i < 3; i++ {\n}\nbreak'
        self.assertEqual(codigos(programa(cuerpo)), ['S6'])

    def test_s6_el_contador_se_reinicia_en_cada_funcion(self):
        extra = 'func f() {\n\tbreak\n}\n'
        cuerpo = 'for i := 0; i < 3; i++ {\n\tf()\n}'
        self.assertEqual(codigos(programa(cuerpo, extra)), ['S6'])
# FIN aporte: Elkin Salazar


# INICIO aporte: César Balladares
class PruebasCesar(unittest.TestCase):
    """S3 (tipo del valor asignado) y S4 (retorno de funciones)."""

    # --- S3 ---
    def test_s3_mensaje_de_la_propuesta(self):
        cuerpo = 'var edad int = "veinte"\nfmt.Println(edad)'
        self.assertEqual(mensajes(programa(cuerpo)), [
            "Error semántico [línea 6]: no se puede asignar string a 'edad' de tipo int. "
            "Sugerencia: usa un valor entero."])

    def test_s3_literal_entero_en_variable_float64(self):
        cuerpo = 'var x float64 = 3\nx = 4\nfmt.Println(x)'
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s3_variable_entera_en_variable_float64_es_error(self):
        cuerpo = 'n := 3\nvar x float64 = n\nfmt.Println(x)'
        self.assertEqual(mensajes(programa(cuerpo)), [
            "Error semántico [línea 7]: no se puede asignar int a 'x' de tipo float64. "
            "Sugerencia: usa un valor decimal (float64)."])

    def test_s3_texto_no_se_adapta_a_un_numero(self):
        self.assertEqual(codigos(programa('var s string = 5\nfmt.Println(s)')), ['S3'])

    def test_s3_argumento_literal_entero_a_parametro_float64(self):
        extra = 'func mitad(a float64) float64 {\n\treturn a / 2\n}\n'
        self.assertEqual(codigos(programa('fmt.Println(mitad(3))', extra)), [])

    def test_s3_argumento_variable_entera_a_parametro_float64(self):
        extra = 'func mitad(a float64) float64 {\n\treturn a / 2\n}\n'
        self.assertEqual(codigos(programa('n := 3\nfmt.Println(mitad(n))', extra)), ['S3'])

    def test_s3_elementos_literales_en_slice_y_mapa_float64(self):
        cuerpo = 'v := []float64{1, 2.5, 3}\nm := map[string]float64{"a": 1}\nfmt.Println(v, m)'
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s4_return_literal_entero_en_funcion_float64(self):
        extra = 'func uno() float64 {\n\treturn 1\n}\n'
        self.assertEqual(codigos(programa('fmt.Println(uno())', extra)), [])

    def test_s4_return_variable_entera_en_funcion_float64(self):
        extra = 'func conv(n int) float64 {\n\treturn n\n}\n'
        self.assertEqual(codigos(programa('fmt.Println(conv(1))', extra)), ['S4'])

    def test_s3_declaraciones_correctas(self):
        cuerpo = ('var a int = 1\nvar b float64 = 1.5\nvar c string = "x"\n'
                  'var d bool = true\nvar e [2]int = [2]int{1, 2}\nfmt.Println(a, b, c, d, e)')
        self.assertEqual(codigos(programa(cuerpo)), [])

    def test_s3_tipo_deducido_con_declaracion_corta(self):
        cuerpo = 'x := 5\nx = "hola"\nfmt.Println(x)'
        self.assertEqual(mensajes(programa(cuerpo)), [
            "Error semántico [línea 7]: no se puede asignar string a 'x' de tipo int. "
            "Sugerencia: usa un valor entero."])

    def test_s3_asignacion_correcta(self):
        self.assertEqual(codigos(programa('x := 5\nx = 7\ns := "a"\ns = "b"')), [])

    def test_s3_elemento_de_literal_slice_y_arreglo(self):
        self.assertEqual(codigos(programa('v := []int{1, "a"}\nfmt.Println(v)')), ['S3'])
        self.assertEqual(codigos(programa('v := [2]string{"a", 1}\nfmt.Println(v)')), ['S3'])

    def test_s3_clave_y_valor_de_literal_mapa(self):
        self.assertEqual(codigos(programa('m := map[string]int{"a": "b"}\nfmt.Println(m)')), ['S3'])
        self.assertEqual(codigos(programa('m := map[string]int{1: 2}\nfmt.Println(m)')), ['S3'])

    def test_s3_asignar_a_un_elemento(self):
        cuerpo = 'v := []int{1}\nv[0] = "a"\nfmt.Println(v)'
        errs = mensajes(programa(cuerpo))
        self.assertEqual(len(errs), 1)
        self.assertIn("a un elemento de 'v' de tipo int", errs[0])

    def test_s3_argumento_de_tipo_incorrecto(self):
        errs = mensajes(programa('x := suma("a", 2)\nfmt.Println(x)', F_SUMA))
        self.assertEqual(len(errs), 1)
        self.assertIn("no se puede pasar string como argumento 'a' de tipo int "
                      "a la función 'suma'", errs[0])

    def test_s3_cantidad_de_argumentos(self):
        errs = mensajes(programa('x := suma(1)\nfmt.Println(x)', F_SUMA))
        self.assertEqual(len(errs), 1)
        self.assertIn("la función 'suma' espera 2 argumentos, pero recibe 1", errs[0])

    def test_s3_declaracion_multiple_cantidad(self):
        self.assertEqual(codigos(programa('a, b := 1\nfmt.Println(a, b)')), ['S3'])
        self.assertEqual(codigos(programa('a, b := 1, 2\nfmt.Println(a, b)')), [])

    def test_s3_declaracion_con_llamada_de_dos_retornos(self):
        self.assertEqual(codigos(programa('c, m := dividir(17, 5)\nfmt.Println(c, m)',
                                          F_DIVIDIR)), [])
        errs = mensajes(programa('x := dividir(1, 2)\nfmt.Println(x)', F_DIVIDIR))
        self.assertEqual(len(errs), 1)
        self.assertIn("la función 'dividir' devuelve 2 valores", errs[0])
        self.assertEqual(codigos(programa('a, b := suma(1, 2)\nfmt.Println(a, b)', F_SUMA)),
                         ['S3'])

    def test_s3_asignar_resultado_de_funcion_sin_retorno(self):
        errs = mensajes(programa('x := saludar("a")\nfmt.Println(x)', F_SALUDAR))
        self.assertEqual(len(errs), 1)
        self.assertIn("la función 'saludar' porque no devuelve ningún valor", errs[0])
        self.assertEqual(codigos(programa('var y int = saludar("a")\nfmt.Println(y)',
                                          F_SALUDAR)), ['S3'])

    def test_s3_no_se_encadena_con_s1(self):
        self.assertEqual(codigos(programa('var x int = y + 1\nfmt.Println(x)')), ['S1'])

    # --- S4 ---
    def test_s4_mensaje_de_la_propuesta(self):
        extra = 'func suma(a int, b int) int {\n\treturn "ok"\n}\n'
        self.assertEqual(mensajes(programa('fmt.Println(suma(1, 2))', extra)), [
            "Error semántico [línea 6]: la función 'suma' debe retornar int, pero "
            "retorna string. Sugerencia: devuelve un entero."])

    def test_s4_return_correcto(self):
        self.assertEqual(codigos(programa('fmt.Println(suma(1, 2))', F_SUMA)), [])

    def test_s4_menos_valores_de_los_declarados(self):
        extra = 'func d(a int) (int, int) {\n\treturn a\n}\n'
        errs = mensajes(programa('x, y := d(1)\nfmt.Println(x, y)', extra))
        self.assertEqual(len(errs), 1)
        self.assertIn("debe retornar 2 valores (int, int), pero retorna 1 valor", errs[0])

    def test_s4_mas_valores_de_los_declarados(self):
        extra = 'func d(a int) int {\n\treturn a, a\n}\n'
        self.assertEqual(codigos(programa('fmt.Println(d(1))', extra)), ['S4'])

    def test_s4_valor_en_funcion_sin_retorno(self):
        extra = 'func f() {\n\treturn 1\n}\n'
        errs = mensajes(programa('f()', extra))
        self.assertEqual(len(errs), 1)
        self.assertIn("la función 'f' no devuelve ningún valor, pero retorna 1", errs[0])

    def test_s4_return_vacio_en_funcion_con_retorno(self):
        extra = 'func f() int {\n\treturn\n}\n'
        self.assertEqual(codigos(programa('fmt.Println(f())', extra)), ['S4'])

    def test_s4_tipo_incorrecto_en_la_segunda_posicion(self):
        extra = 'func d(a int) (int, int) {\n\treturn 1, "x"\n}\n'
        errs = mensajes(programa('x, y := d(1)\nfmt.Println(x, y)', extra))
        self.assertEqual(len(errs), 1)
        self.assertIn("debe retornar int en la posición 2, pero retorna string", errs[0])

    def test_s4_return_de_una_llamada_con_dos_valores(self):
        extra = F_DIVIDIR + 'func g() (int, int) {\n\treturn dividir(4, 2)\n}\n'
        self.assertEqual(codigos(programa('a, b := g()\nfmt.Println(a, b)', extra)), [])

    def test_s4_falta_el_return_final(self):
        extra = 'func n(a int) int {\n\tif a > 0 {\n\t\treturn 1\n\t}\n}\n'
        errs = semantica(programa('fmt.Println(n(1))', extra))
        self.assertEqual([(e['codigo'], e['linea']) for e in errs], [('S4', 5)])
        self.assertIn("debe terminar con un return de int", errs[0]['mensaje'])

    def test_s4_if_else_que_retorna_en_ambas_ramas(self):
        extra = ('func signo(a int) int {\n\tif a >= 0 {\n\t\treturn 1\n\t} else {\n'
                 '\t\treturn -1\n\t}\n}\n')
        self.assertEqual(codigos(programa('fmt.Println(signo(3))', extra)), [])

    def test_s4_switch_con_default_que_retorna_en_todos_los_casos(self):
        extra = ('func nombre(d int) string {\n\tswitch d {\n\tcase 1:\n\t\treturn "uno"\n'
                 '\tdefault:\n\t\treturn "otro"\n\t}\n}\n')
        self.assertEqual(codigos(programa('fmt.Println(nombre(1))', extra)), [])

    def test_s4_switch_sin_default_no_termina(self):
        extra = ('func nombre(d int) string {\n\tswitch d {\n\tcase 1:\n\t\treturn "uno"\n\t}\n}\n')
        self.assertEqual(codigos(programa('fmt.Println(nombre(1))', extra)), ['S4'])
# FIN aporte: César Balladares


# INICIO aporte: Elkin Salazar
class PruebasIntegral(unittest.TestCase):
    """Los algoritmos, los archivos de error y el conjunto de las seis reglas."""

    def test_los_tres_algoritmos_no_tienen_errores_semanticos(self):
        for n in (1, 2, 3):
            with self.subTest(algoritmo=n):
                self.assertEqual(mensajes(leer('algoritmos/algoritmo%d.go' % n)), [])

    def test_archivos_de_error_producen_sus_reglas_en_la_linea_esperada(self):
        esperado = {
            'fatima': [('S2', 9), ('S1', 10)],
            'cesar': [('S4', 6), ('S3', 10)],
            'elkin': [('S5', 8), ('S6', 10)],
        }
        for quien, reglas in esperado.items():
            with self.subTest(archivo=quien):
                errs = semantica(leer('errores/semantico_%s.go' % quien))
                self.assertEqual([(e['codigo'], e['linea']) for e in errs], reglas)

    def test_varios_errores_en_un_archivo_salen_ordenados_por_linea(self):
        cuerpo = ('const PI = 3.14\nPI = 3\nvar edad int = "veinte"\n'
                  'c := edad + 1.5\nbreak\nfmt.Println(total)')
        errs = semantica(programa(cuerpo))
        self.assertEqual([e['codigo'] for e in errs], ['S2', 'S3', 'S5', 'S6', 'S1'])
        self.assertEqual([e['linea'] for e in errs], sorted(e['linea'] for e in errs))

    def test_cada_error_trae_su_categoria(self):
        categorias = {'S1': 'Identificadores', 'S2': 'Constantes',
                      'S3': 'Asignación de tipo', 'S4': 'Retorno de funciones',
                      'S5': 'Operaciones permitidas', 'S6': 'Estructuras de control'}
        for quien in ('fatima', 'cesar', 'elkin'):
            for e in semantica(leer('errores/semantico_%s.go' % quien)):
                self.assertEqual(e['categoria'], categorias[e['codigo']])
                self.assertTrue(e['mensaje'].startswith('Error semántico [línea %d]:' % e['linea']))
                self.assertIn('Sugerencia:', e['mensaje'])

    def test_tabla_de_simbolos_por_ambitos(self):
        arbol, _, _ = PARSER.analizar(leer('algoritmos/algoritmo3.go'))
        analizador = AnalizadorSemantico()
        analizador.analizar(arbol)
        tabla = {(s.nombre, s.ambito): s for s in analizador.simbolos}
        self.assertTrue(tabla[('MINIMO', 'global')].es_const)
        self.assertEqual(tabla[('MINIMO', 'global')].tipo, 'int')
        self.assertEqual(tabla[('precio', 'función calcularTotal')].tipo, 'int')
        self.assertEqual(tabla[('precios', 'función main')].tipo, 'map[string]int')
        self.assertTrue(tabla[('calcularTotal', 'global')].es_funcion)
        self.assertGreater(tabla[('calcularTotal', 'global')].linea, 0)

    def test_arbol_nulo_no_produce_errores(self):
        self.assertEqual(AnalizadorSemantico().analizar(None), [])

    def test_el_analizador_se_puede_reutilizar(self):
        analizador = AnalizadorSemantico()
        arbol, _, _ = PARSER.analizar(leer('errores/semantico_fatima.go'))
        self.assertEqual(len(analizador.analizar(arbol)), 2)
        self.assertEqual(len(analizador.analizar(arbol)), 2)

    def test_programa_valido_en_go_con_literales_enteros_y_float64(self):
        cuerpo = ('const N = 10\ntotal := 0.0\nfor i := 0; i < N; i++ {\n\ttotal += 1\n}\n'
                  'var prom float64 = 0\nprom = total / 2\nfmt.Println(total, prom)')
        self.assertEqual(codigos(programa(cuerpo)), [])
# FIN aporte: Elkin Salazar


if __name__ == '__main__':
    unittest.main()
