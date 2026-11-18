# -*- coding: utf-8 -*-
"""Pruebas de la ventana (gui.py). Se omiten si no hay Tkinter, customtkinter
o pantalla disponible (por ejemplo, en un servidor sin entorno gráfico)."""
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

try:
    import tkinter
    tkinter.Tk().destroy()          # falla si no hay pantalla
    import gui                      # falla si falta customtkinter
    DISPONIBLE = True
except Exception:       # sin Tk, sin customtkinter o sin display
    DISPONIBLE = False


def ruta(*partes):
    return os.path.join(RAIZ, *partes)


@unittest.skipUnless(DISPONIBLE, 'Tkinter/customtkinter o pantalla no disponibles')
class PruebasVentana(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui.App()           # una sola ventana para todas las pruebas
        cls.app.update()

    @classmethod
    def tearDownClass(cls):
        cls.app.update()
        cls.app.destroy()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.app.carpeta_logs = self._tmp.name
        self.app.limpiar(confirmar=False)
        self.app.selector.set('Fátima Torres')
        self.app.update()

    def lineas_marcadas(self):
        # Tk junta las líneas contiguas en un solo rango: se expanden una a una
        r = [str(x) for x in self.app.editor.tag_ranges('linea_error')]
        lineas = set()
        for ini, fin in zip(r[::2], r[1::2]):
            lineas.update(range(int(ini.split('.')[0]), int(fin.split('.')[0])))
        return sorted(lineas)

    def test_estructura_segun_la_propuesta(self):
        a = self.app
        self.assertEqual(set(a.botones), {'lexico', 'sintactico', 'semantico'})
        self.assertEqual(a.nombres_dev, ['Fátima Torres', 'César Balladares',
                                         'Elkin Salazar'])
        self.assertEqual(a.numeros.get('1.0', '1.end'), '1')

    def test_numeracion_de_lineas_sigue_al_editor(self):
        a = self.app
        a.abrir(ruta('algoritmos', 'algoritmo1.go'))
        n = int(a.editor.index('end-1c').split('.')[0])
        self.assertEqual(a.numeros.get('1.0', 'end-1c').split('\n')[-1], str(n))

    def test_analisis_con_errores_marca_lineas_tabla_y_consola(self):
        a = self.app
        a.abrir(ruta('errores', 'semantico_fatima.go'))
        res = a.analizar('semantico')
        self.assertEqual(self.lineas_marcadas(), [9, 10])
        self.assertEqual(len(a.tabla.get_children()), 2)
        consola = a.consola.get('1.0', 'end')
        self.assertIn('Línea 9', consola)
        self.assertIn('Línea 10', consola)
        self.assertIn('Sugerencia', consola)
        self.assertIn(res.nombre_log, a.lbl_log.cget('text'))
        self.assertTrue(os.path.isfile(res.ruta_log))

    def test_analisis_correcto_muestra_exito(self):
        a = self.app
        a.abrir(ruta('algoritmos', 'algoritmo3.go'))
        for tipo in ('lexico', 'sintactico', 'semantico'):
            res = a.analizar(tipo)
            self.assertTrue(res.ok)
            self.assertIn('ÉXITO', a.consola.get('1.0', 'end'))
            self.assertEqual(self.lineas_marcadas(), [])
        self.assertTrue(a.tabla_simbolos.get_children())

    def test_semantico_bloqueado_por_errores_previos(self):
        a = self.app
        a.abrir(ruta('errores', 'sintactico_cesar.go'))
        res = a.analizar('semantico')
        self.assertFalse(res.ejecutado)
        self.assertIn('NO EJECUTADO', a.consola.get('1.0', 'end'))
        self.assertEqual(self.lineas_marcadas(), [8, 9])

    def test_analiza_el_texto_del_editor(self):
        a = self.app
        a._poner_texto('package main\nfunc main() {\n\tx := 1 +\n}\n')
        res = a.analizar('sintactico')
        self.assertEqual(res.lineas_error, [3])
        with open(res.ruta_log, encoding='utf-8') as f:
            self.assertIn('(editor, sin guardar)', f.read())

    def test_selector_de_desarrollador_cambia_el_nombre_del_log(self):
        a = self.app
        a.abrir(ruta('algoritmos', 'algoritmo1.go'))
        a.selector.set('César Balladares')
        self.assertIn('CBalla-05', a.analizar('sintactico').nombre_log)
        self.assertIn('CesarBalladares', a.analizar('lexico').nombre_log)
        a.selector.set('Elkin Salazar')
        self.assertIn('sElkinEspol', a.analizar('semantico').nombre_log)

    def test_clic_en_error_salta_a_su_linea(self):
        a = self.app
        a.abrir(ruta('errores', 'semantico_fatima.go'))
        a.analizar('semantico')
        a.tabla.selection_set(a.tabla.get_children()[1])
        a.update()
        self.assertEqual(a.editor.index('insert').split('.')[0], '10')

    def test_editar_el_texto_quita_las_marcas_obsoletas(self):
        a = self.app
        a.abrir(ruta('errores', 'semantico_fatima.go'))
        a.analizar('semantico')
        self.assertTrue(self.lineas_marcadas())
        a.editor.insert('1.0', '// comentario\n')
        a.update()
        self.assertEqual(self.lineas_marcadas(), [])
        self.assertTrue(a.modificado)
        self.assertIn('modificado', a.lbl_estado.cget('text'))

    def test_editor_vacio_avisa_y_no_genera_log(self):
        a = self.app
        a.limpiar(confirmar=False)
        self.assertIsNone(a.analizar('lexico'))
        self.assertIn('vacío', a.consola.get('1.0', 'end'))
        self.assertEqual(os.listdir(self._tmp.name), [])

    def test_abrir_y_guardar_no_cuentan_como_modificacion(self):
        a = self.app
        a.abrir(ruta('algoritmos', 'algoritmo1.go'))
        a.update()
        self.assertFalse(a.modificado)
        destino = os.path.join(self._tmp.name, 'copia.go')
        a._poner_texto('package main\n')
        a.guardar(destino)
        a.update()
        self.assertFalse(a.modificado)
        with open(destino, encoding='utf-8') as f:
            self.assertEqual(f.read(), 'package main\n')

    def test_limpiar_reinicia_todo(self):
        a = self.app
        a.abrir(ruta('errores', 'semantico_fatima.go'))
        a.analizar('semantico')
        a.limpiar(confirmar=False)
        self.assertEqual(a.texto(), '')
        self.assertEqual(self.lineas_marcadas(), [])
        self.assertEqual(a.tabla.get_children(), ())
        self.assertIsNone(a.resultado)

    def test_el_editor_colorea_el_codigo(self):
        a = self.app
        a.abrir(ruta('algoritmos', 'algoritmo1.go'))
        a.update()
        r = [str(x) for x in a.editor.tag_ranges('declaracion')]
        self.assertTrue(r)                          # package, func, var...
        self.assertEqual(a.editor.get(r[0], r[1]), 'package')
        a.editor.insert('end', '// nota\n')        # al editar se vuelve a pintar
        a.update()
        self.assertTrue(a.editor.tag_ranges('comentario'))
        a.limpiar(confirmar=False)
        self.assertEqual(a.editor.tag_ranges('declaracion'), ())


if __name__ == '__main__':
    unittest.main()
