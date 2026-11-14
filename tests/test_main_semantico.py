# -*- coding: utf-8 -*-
"""Pruebas del ejecutor y del log del analizador semántico (Avance 3)."""
import os
import sys
import tempfile
import unittest
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import main_semantico  # noqa: E402


# INICIO aporte: César Balladares
class PruebasLogSemantico(unittest.TestCase):
    """Nombre y contenido del log semantico-usuarioGit-DDMMAAAA-HHhMM.txt."""

    def ejecutar(self, ruta, usuario='gabytv1'):
        with tempfile.TemporaryDirectory() as carpeta:
            resultado = main_semantico.ejecutar(os.path.join(RAIZ, ruta), usuario, carpeta)
            with open(resultado[0], encoding='utf-8') as f:
                return resultado, f.read(), os.path.basename(resultado[0])

    def test_nombre_del_log(self):
        ahora = datetime(2026, 11, 20, 23, 32)
        self.assertEqual(main_semantico.nombre_log('rasaraguro', ahora),
                         'semantico-rasaraguro-20112026-23h32.txt')

    def test_el_log_se_crea_con_el_formato_del_proyecto(self):
        _, _, nombre = self.ejecutar('algoritmos/algoritmo1.go')
        self.assertRegex(nombre, r'^semantico-gabytv1-\d{8}-\d{2}h\d{2}\.txt$')

    def test_log_con_errores_semanticos(self):
        (_, errores, sint, lex, ejecutado, _), log, _ = self.ejecutar('errores/semantico_fatima.go')
        self.assertTrue(ejecutado)
        self.assertEqual((len(errores), len(sint), len(lex)), (2, 0, 0))
        for texto in ('ANÁLISIS SEMÁNTICO', 'Usuario Git   : gabytv1',
                      'errores/semantico_fatima.go', '[S2] Error semántico [línea 9]',
                      '[S1] Error semántico [línea 10]', 'Errores semánticos  : 2',
                      'Resultado           : CON ERRORES SEMÁNTICOS'):
            self.assertIn(texto, log)

    def test_log_sin_errores_incluye_la_tabla_de_simbolos(self):
        (_, errores, _, _, ejecutado, simbolos), log, _ = self.ejecutar('algoritmos/algoritmo2.go')
        self.assertTrue(ejecutado)
        self.assertEqual(errores, [])
        self.assertGreater(len(simbolos), 0)
        for texto in ('(ninguno)', 'TABLA DE SÍMBOLOS', 'factorial',
                      'Resultado           : SEMÁNTICA CORRECTA'):
            self.assertIn(texto, log)

    def test_no_se_ejecuta_con_errores_sintacticos_o_lexicos(self):
        (_, errores, sint, lex, ejecutado, _), log, _ = self.ejecutar('errores/error_elkin.go')
        self.assertFalse(ejecutado)
        self.assertEqual(errores, [])
        self.assertTrue(sint or lex)
        for texto in ('NO se ejecutó', '(no evaluados)', 'NO EJECUTADO'):
            self.assertIn(texto, log)
# FIN aporte: César Balladares


if __name__ == '__main__':
    unittest.main()
