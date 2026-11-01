# -*- coding: utf-8 -*-
"""Pruebas de main.py: nombre y contenido del log (aporte de César Balladares)."""
import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main  # noqa: E402


class PruebasLog(unittest.TestCase):

    def test_nombre_para_archivo(self):
        self.assertEqual(main.nombre_para_archivo('Fátima Torres'), 'FatimaTorres')
        self.assertEqual(main.nombre_para_archivo('césar  balladares'), 'CesarBalladares')
        self.assertEqual(main.nombre_para_archivo('Elkin Salazar'), 'ElkinSalazar')

    def test_log_tiene_el_nombre_y_contenido_pedidos(self):
        with tempfile.TemporaryDirectory() as tmp:
            fuente = os.path.join(tmp, 'prueba.go')
            with open(fuente, 'w', encoding='utf-8') as f:
                f.write('package main\n)\n@\n')
            ruta, tokens, errores = main.ejecutar(fuente, 'César Balladares', tmp)
            nombre = os.path.basename(ruta)
            self.assertRegex(nombre, r'^lexico-CesarBalladares-\d{2}-\d{2}-\d{4}-\d{2}h\d{2}\.txt$')
            with open(ruta, encoding='utf-8') as f:
                texto = f.read()
            self.assertIn('Desarrollador : César Balladares', texto)
            self.assertIn('TOKENS RECONOCIDOS', texto)
            self.assertIn('ERRORES LÉXICOS', texto)
            self.assertIn('[L1]', texto)
            self.assertEqual(len(errores), 1)


if __name__ == '__main__':
    unittest.main()
