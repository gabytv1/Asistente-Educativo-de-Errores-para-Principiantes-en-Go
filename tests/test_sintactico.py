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


# INICIO aporte: Elkin Salazar
class PruebasElkin(unittest.TestCase):

    def test_estructura_del_programa(self):
        arbol = sin_errores(self, 'package main\n\nimport "fmt"\n\nfunc main() {\n}\n')
        self.assertEqual(arbol.hijos[0:2], ['main', '"fmt"'])
        sin_errores(self, 'package main\n\nfunc main() {\n}\n')          # import opcional

    def test_const_global_y_local(self):
        arbol = sin_errores(self, programa('const MAX = 5', 'const PI = 3.14159\n\n'))
        self.assertEqual(contar_construcciones(arbol)['const'], 2)

    def test_switch_con_case_y_default(self):
        arbol = sin_errores(self, programa(
            'switch dia {\ncase 1:\n\tfmt.Println("Lunes")\ncase 2, 3:\n\tx++\ndefault:\n\tfmt.Println("Otro")\n}'))
        sw = sentencias_main(arbol)[0]
        self.assertEqual([c.tipo for c in sw.hijos[1]], ['case', 'case', 'default'])

    def test_break_y_continue(self):
        arbol = sin_errores(self, programa(
            'for i := 0; i < 5; i++ {\n\tif i == 3 {\n\t\tbreak\n\t}\n\tcontinue\n}'))
        cuenta = contar_construcciones(arbol)
        self.assertEqual((cuenta['break'], cuenta['continue']), (1, 1))

    def test_mapa_declaracion_y_acceso_por_clave(self):
        arbol = sin_errores(self, programa(
            'edades := map[string]int{"Ana": 20, "Luis": 22}\nvar m map[string]int = map[string]int{}\n'
            'e := edades["Ana"]\nedades["Ana"] += 1'))
        cuenta = contar_construcciones(arbol)
        self.assertEqual((cuenta['mapa'], cuenta['par'], cuenta['indice']), (2, 2, 2))

    def test_funcion_sin_retorno(self):
        arbol = sin_errores(self, programa(
            'saludar("Ana")', 'func saludar(nombre string) {\n\tfmt.Println(nombre)\n\treturn\n}\n\n'))
        self.assertEqual(arbol.hijos[2][0].hijos[2], [])

    def test_impresion_con_varios_argumentos_y_vacia(self):
        arbol = sin_errores(self, programa('fmt.Println("Total:", total, a + 1)\nfmt.Println()'))
        impresiones = [s for s in sentencias_main(arbol) if s.tipo == 'impresion']
        self.assertEqual([len(i.hijos[0]) for i in impresiones], [3, 0])

    def test_lectura_por_teclado(self):
        arbol = sin_errores(self, programa('var edad int\nfmt.Scanln(&edad)'))
        self.assertEqual(contar_construcciones(arbol)['lectura'], 1)

    def test_Scanln_exige_ampersand(self):
        self.assertEqual(errores(programa('fmt.Scanln(edad)')), ['Y6'])

    def test_Y3_llave_sin_cerrar_al_final_del_archivo(self):
        codigo = 'package main\n\nfunc main() {\n\ttotal := 0\n'
        arbol, errs, _ = analizar(codigo)
        self.assertEqual([e['codigo'] for e in errs], ['Y3'])
        self.assertIn("falta '}'", errs[0]['mensaje'])
        self.assertIn('[línea 4]', errs[0]['mensaje'])

    def test_Y3_funcion_nueva_antes_de_cerrar_la_anterior(self):
        codigo = 'package main\n\nfunc a() {\n\tx := 1\n\nfunc main() {\n}\n'
        self.assertEqual(errores(codigo), ['Y3'])

    def test_Y6_token_inesperado(self):
        arbol, errs, _ = analizar(programa('total := := 5\nx := 1'))
        self.assertEqual([e['codigo'] for e in errs], ['Y6'])
        self.assertIn("token inesperado ':='", errs[0]['mensaje'])

    def test_Y6_llave_o_parentesis_de_sobra(self):
        self.assertEqual(errores(programa('x := 1') + '}\n'), ['Y6'])
        self.assertIn("token inesperado ')'", analizar(programa('x := (1 + 2))'))[1][0]['mensaje'])

    def test_Y6_sentencia_incompleta_se_reporta_en_su_linea(self):
        arbol, errs, _ = analizar(programa('fmt.Println("a",\n)\nx := 1'))
        self.assertEqual([e['codigo'] for e in errs], ['Y6'])
        self.assertIn('[línea 6]', errs[0]['mensaje'])
        self.assertIn("termina en ','", errs[0]['mensaje'])


# FIN aporte: Elkin Salazar


# INICIO aporte: Elkin Salazar (
class PruebasIntegral(unittest.TestCase):
    """Los tres algoritmos, los archivos de error y el log del Avance 2."""

    def test_los_tres_algoritmos_no_tienen_errores_sintacticos(self):
        for n in (1, 2, 3):
            arbol, errs, lex = analizar(leer('algoritmos/algoritmo%d.go' % n))
            self.assertEqual(errs, [], 'algoritmo%d.go' % n)
            self.assertEqual(lex, [])
            self.assertEqual(arbol.tipo, 'programa')

    def test_los_algoritmos_cubren_las_reglas_minimas(self):
        cuenta = {}
        for n in (1, 2, 3):
            for k, v in contar_construcciones(analizar(leer('algoritmos/algoritmo%d.go' % n))[0]).items():
                cuenta[k] = cuenta.get(k, 0) + v
        for tipo in ('impresion', 'lectura', 'aritmetica', 'logica', 'comparacion', 'var',
                     'declare', 'const', 'asignacion', 'arreglo', 'slice', 'mapa', 'indice',
                     'if', 'for_condicion', 'for_clasico', 'switch', 'func', 'llamada'):
            self.assertGreater(cuenta.get(tipo, 0), 0, tipo)

    def test_programa_de_la_propuesta(self):
        codigo = ('package main\n\nimport "fmt"\n\nfunc suma(a int, b int) int {\n\treturn a + b\n}\n\n'
                  'func main() {\n\tvar total int = suma(4, 5)\n\tfor i := 0; i < 3; i++ {\n'
                  '\t\ttotal += i\n\t}\n\tfmt.Println("Total:", total)\n}\n')
        sin_errores(self, codigo)

    def test_archivos_de_error_producen_sus_codigos(self):
        esperado = {
            'errores/sintactico_fatima.go': ['Y1', 'Y5'],
            'errores/sintactico_cesar.go': ['Y4', 'Y2'],
            'errores/sintactico_elkin.go': ['Y6', 'Y3'],
        }
        for ruta, codigos in esperado.items():
            arbol, errs, _ = analizar(leer(ruta))
            self.assertEqual([e['codigo'] for e in errs], codigos, ruta)
            self.assertIsNone(arbol)

    def test_varios_errores_en_un_mismo_archivo(self):
        src = programa('var edad\ntotal := := 5\nfmt.Println("a"\nfor i := 0; i < 3; i++\n{\n}')
        self.assertEqual(errores(src), ['Y4', 'Y6', 'Y2', 'Y1'])

    def test_los_errores_vienen_con_la_linea_correcta(self):
        arbol, errs, _ = analizar(programa('x := 1\ntotal := := 5'))
        self.assertEqual(errs[0]['linea'], 7)

    def test_archivo_sin_salto_de_linea_final_y_con_saltos_de_windows(self):
        sin_errores(self, 'package main\nfunc main() {\n}')
        sin_errores(self, programa('x := 1\nif x > 0 {\n\tx++\n}').replace('\n', '\r\n'))

    def test_comentarios_y_lineas_en_blanco_no_afectan(self):
        sin_errores(self, 'package main\n\n// c1\n\n/* c2\n   c3 */\nfunc main() {\n\n\t// c4\n\tx := 1\n\n}\n')

    def test_los_errores_lexicos_se_informan_aparte(self):
        arbol, errs, lex = analizar(programa('x := 5 @ 3'))
        self.assertEqual([e['codigo'] for e in lex], ['L1'])

    def test_no_falla_ni_se_cuelga_con_codigo_truncado_o_roto(self):
        base = leer('algoritmos/algoritmo3.go')
        for corte in range(0, len(base), 97):
            analizar(base[:corte])                    # no debe lanzar excepciones
        for basura in ('', '\n\n', '}', '{', 'func', 'package', 'x := ', ')))', 'else'):
            analizar(basura)

    def test_nombre_y_contenido_del_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta, arbol, errs, lex = main_sintactico.ejecutar(
                os.path.join(RAIZ, 'errores/sintactico_fatima.go'), 'gabytv1', tmp)
            self.assertRegex(os.path.basename(ruta),
                             r'^sintactico-gabytv1-\d{8}-\d{2}h\d{2}\.txt$')
            with open(ruta, encoding='utf-8') as f:
                texto = f.read()
            for esperado in ('ANÁLISIS SINTÁCTICO', 'Usuario Git   : gabytv1',
                             'ERRORES SINTÁCTICOS', '[Y1]', '[Y5]', 'CON ERRORES'):
                self.assertIn(esperado, texto)

    def test_log_de_programa_correcto_lista_las_construcciones(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta, arbol, errs, lex = main_sintactico.ejecutar(
                os.path.join(RAIZ, 'algoritmos/algoritmo2.go'), 'CBalla-05', tmp)
            with open(ruta, encoding='utf-8') as f:
                texto = f.read()
            self.assertIn('SINTAXIS CORRECTA', texto)
            self.assertIn('CONSTRUCCIONES RECONOCIDAS', texto)
            self.assertIn('Ingreso por teclado (fmt.Scanln)', texto)

# FIN aporte: Elkin Salazar 


if __name__ == '__main__':
    unittest.main()
