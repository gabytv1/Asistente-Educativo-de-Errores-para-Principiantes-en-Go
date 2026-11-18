# -*- coding: utf-8 -*-
"""Pruebas de la lógica de la interfaz gráfica (logica_gui.py), sin Tkinter."""
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import logica_gui as lg  # noqa: E402


def leer(ruta):
    with open(os.path.join(RAIZ, ruta), encoding='utf-8') as f:
        return f.read()


class PruebasLogicaGui(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.logs = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def analizar(self, tipo, ruta, dev=0):
        return lg.analizar(tipo, leer(ruta), dev, ruta, self.logs)

    # --- los tres analizadores sobre un algoritmo correcto
    def test_algoritmos_correctos_no_dan_errores(self):
        for n in (1, 2, 3):
            for tipo in (lg.LEXICO, lg.SINTACTICO, lg.SEMANTICO):
                res = self.analizar(tipo, 'algoritmos/algoritmo%d.go' % n)
                self.assertTrue(res.ok, (n, tipo, res.errores))
                self.assertEqual(res.lineas_error, [])

    def test_lexico_lista_tokens_con_linea_y_columna(self):
        res = self.analizar(lg.LEXICO, 'algoritmos/algoritmo1.go')
        self.assertEqual([c[1] for c in res.columnas],
                         ['Línea', 'Col.', 'Tipo de token', 'Lexema'])
        linea, col, tipo, lexema = res.filas[0][0]
        self.assertEqual((linea, col, tipo, lexema), (1, 1, 'PACKAGE', 'package'))

    # --- errores con su número de línea
    def test_error_lexico_trae_linea_columna_y_sugerencia(self):
        res = self.analizar(lg.LEXICO, 'errores/error_fatima.go')
        self.assertEqual(res.lineas_error, [10, 14])
        e = res.errores[0]
        self.assertEqual((e.codigo, e.linea, e.columna, e.tipo), ('L7', 10, 11, 'Léxico'))
        self.assertNotIn('Error léxico', e.texto)        # sin el prefijo repetido
        self.assertTrue(e.sugerencia)
        self.assertEqual(res.filas[0][1], 'error')       # los errores van primero y en rojo

    def test_error_sintactico_incluye_los_lexicos(self):
        res = self.analizar(lg.SINTACTICO, 'errores/error_fatima.go')
        self.assertEqual({e.tipo for e in res.errores}, {'Léxico', 'Sintáctico'})
        self.assertEqual(res.lineas_error, [9, 10, 13, 14])
        self.assertEqual([e.linea for e in res.errores],
                         sorted(e.linea for e in res.errores))

    def test_sintaxis_correcta_muestra_las_construcciones(self):
        res = self.analizar(lg.SINTACTICO, 'algoritmos/algoritmo1.go')
        self.assertEqual(res.titulo_panel, 'Construcciones reconocidas')
        self.assertTrue(res.filas)

    def test_error_semantico_trae_regla_y_categoria(self):
        res = self.analizar(lg.SEMANTICO, 'errores/semantico_fatima.go')
        self.assertTrue(res.ejecutado)
        self.assertEqual([(e.codigo, e.linea) for e in res.errores],
                         [('S2', 9), ('S1', 10)])
        self.assertEqual(res.filas[0][0][:3], (9, 'S2', 'Constantes'))

    def test_semantico_con_errores_previos_no_se_ejecuta(self):
        res = self.analizar(lg.SEMANTICO, 'errores/sintactico_cesar.go')
        self.assertFalse(res.ejecutado)
        self.assertFalse(res.ok)
        self.assertEqual(res.lineas_error, [8, 9])
        self.assertIn('no se ejecutó', res.resumen)
        log = open(res.ruta_log, encoding='utf-8').read()
        self.assertIn('NO se ejecutó', log)

    def test_tabla_de_simbolos(self):
        res = self.analizar(lg.SEMANTICO, 'algoritmos/algoritmo2.go')
        nombres = {fila[0] for fila in res.simbolos}
        self.assertIn('factorial', nombres)
        self.assertEqual(len(res.simbolos[0]), len(lg.COLUMNAS_SIMBOLOS))

    # --- logs: mismo nombre y formato que los ejecutables por consola
    def test_nombres_de_log_segun_desarrollador(self):
        esperado = [('FatimaTorres', 'gabytv1'), ('CesarBalladares', 'CBalla-05'),
                    ('ElkinSalazar', 'sElkinEspol')]
        for i, (lexico, git) in enumerate(esperado):
            l = self.analizar(lg.LEXICO, 'algoritmos/algoritmo1.go', i).nombre_log
            s = self.analizar(lg.SINTACTICO, 'algoritmos/algoritmo1.go', i).nombre_log
            m = self.analizar(lg.SEMANTICO, 'algoritmos/algoritmo1.go', i).nombre_log
            self.assertRegex(l, r'^lexico-%s-\d{2}-\d{2}-\d{4}-\d{2}h\d{2}\.txt$' % lexico)
            self.assertRegex(s, r'^sintactico-%s-\d{8}-\d{2}h\d{2}\.txt$' % git)
            self.assertRegex(m, r'^semantico-%s-\d{8}-\d{2}h\d{2}\.txt$' % git)

    def test_el_log_existe_y_menciona_la_ruta_recibida(self):
        res = self.analizar(lg.SEMANTICO, 'errores/semantico_elkin.go', 2)
        self.assertTrue(os.path.isfile(res.ruta_log))
        texto = open(res.ruta_log, encoding='utf-8').read()
        self.assertIn('errores/semantico_elkin.go', texto)
        self.assertIn('sElkinEspol', texto)
        self.assertIn('[S5]', texto)

    def test_analiza_el_texto_del_editor_y_no_el_archivo(self):
        codigo = 'package main\nfunc main() {\n\tx := 1 +\n}\n'
        res = lg.analizar(lg.SINTACTICO, codigo, 0, '(editor, sin guardar)', self.logs)
        self.assertFalse(res.ok)
        self.assertEqual(res.lineas_error, [3])

    def test_analisis_desconocido(self):
        with self.assertRaises(ValueError):
            lg.analizar('otro', 'x', 0, 'a.go', self.logs)

    def test_ruta_para_log(self):
        self.assertEqual(lg.ruta_para_log(None), '(editor, sin guardar)')
        self.assertEqual(lg.ruta_para_log(os.path.join(RAIZ, 'algoritmos', 'a.go')),
                         'algoritmos/a.go')

    def test_desarrolladores_coinciden_con_los_usuarios_git_del_equipo(self):
        self.assertEqual([g for _, g in lg.DESARROLLADORES],
                         ['gabytv1', 'CBalla-05', 'sElkinEspol'])


if __name__ == '__main__':
    unittest.main()
