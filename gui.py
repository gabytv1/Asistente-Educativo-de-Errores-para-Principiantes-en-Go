# -*- coding: utf-8 -*-
"""
Interfaz gráfica del Asistente Educativo de Errores para Go.

Uso:
    python gui.py

Flujo: escribe u abre un archivo .go, elige al desarrollador, pulsa uno de los
tres análisis y revisa el resultado en la misma pantalla. Cada análisis genera
su log en logs/ (mismo formato que main.py, main_sintactico.py y
main_semantico.py). Al hacer clic en un error se salta a su línea.
"""
import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

import logica_gui as lg
import resaltado

# Paleta (la misma de los prototipos de la propuesta, Figuras 1 y 2)
AZUL = '#1F2A4D'
FONDO = '#F1F2F8'
PANEL = '#FFFFFF'
CABECERA = '#E1E5F2'
BORDE = '#8E9BC8'
TEXTO = '#1B2038'
TENUE = '#5A6285'
ROJO = '#B42318'
ROJO_FONDO = '#FDECEC'
VERDE = '#0B6B34'
VERDE_FONDO = '#D1F0DC'
AMBAR = '#8A5A00'
AMBAR_FONDO = '#FFF1CC'
FOCO = '#FFF3B0'

TITULOS = {lg.LEXICO: 'Análisis léxico', lg.SINTACTICO: 'Análisis sintáctico',
           lg.SEMANTICO: 'Análisis semántico'}

CODIGO_DE_EJEMPLO = ('package main\n\nimport "fmt"\n\nfunc main() {\n'
                     '\tfmt.Println("Hola, Go")\n}\n')


def _fuente_mono():
    disponibles = set(tkfont.families())
    for nombre in ('Consolas', 'Menlo', 'DejaVu Sans Mono', 'Liberation Mono',
                   'Courier New'):
        if nombre in disponibles:
            return nombre
    return 'TkFixedFont'


class BarraAuto(ctk.CTkScrollbar):
    """Barra de desplazamiento que solo se ve cuando el contenido no cabe.

    No se quita del layout (eso hacía que la interfaz se reacomodara y
    parpadeara): sigue ocupando su espacio, pero cuando todo el contenido es
    visible su "pulgar" se pinta del color del fondo, de modo que no se ve y
    no da la falsa impresión de que se puede desplazar.
    """

    def __init__(self, master, fondo=PANEL, **kwargs):
        super().__init__(master, **kwargs)
        self._fondo = fondo
        self._color_boton = self.cget('button_color')
        self._color_hover = self.cget('button_hover_color')
        self._visible = None
        self._pintar(False)

    def _pintar(self, visible):
        if visible == self._visible:
            return
        self._visible = visible
        if visible:
            self.configure(button_color=self._color_boton,
                           button_hover_color=self._color_hover)
        else:
            self.configure(button_color=self._fondo,
                           button_hover_color=self._fondo)

    def set(self, inicio, fin):
        super().set(inicio, fin)
        self._pintar(float(inicio) > 0.000001 or float(fin) < 0.999999)


class App(ctk.CTk):
    def __init__(self, carpeta_logs=lg.CARPETA_LOGS):
        super().__init__()
        self.carpeta_logs = carpeta_logs
        ctk.set_appearance_mode('light')
        self.title('Asistente de errores para Go')
        ancho = min(1280, self.winfo_screenwidth() - 40)
        alto = min(820, self.winfo_screenheight() - 90)
        self.geometry('%dx%d+20+20' % (ancho, alto))
        self.minsize(min(1200, ancho), min(640, alto))
        self.configure(fg_color=FONDO)

        self.ruta = None               # archivo abierto/guardado (None = nuevo)
        self.modificado = False
        self.resultado = None          # último Resultado mostrado
        self.analisis_activo = None
        self.fuente_mono = (_fuente_mono(), 12)
        self._ids_foco = None

        self._estilo_tabla()
        self._encabezado()
        self._barra()
        self._estado()          # primero lo de abajo, para que el cuerpo
        self._consola()         # ocupe solo el espacio sobrante
        self._cuerpo()

        self.editor.insert('1.0', CODIGO_DE_EJEMPLO)
        self._al_modificar()
        self.editor.edit_reset()
        self.modificado = False
        self._actualizar_estado()

    # ------------------------------------------------------------------ UI
    def _estilo_tabla(self):
        st = ttk.Style(self)
        st.theme_use('clam')
        st.configure('Treeview', background=PANEL, fieldbackground=PANEL,
                     foreground=TEXTO, rowheight=26, borderwidth=0,
                     font=(self.fuente_mono[0], 11))
        st.configure('Treeview.Heading', background=CABECERA, foreground=TEXTO,
                     relief='flat', font=('Segoe UI', 11, 'bold'), padding=(6, 6))
        st.map('Treeview', background=[('selected', '#C7D0EE')],
               foreground=[('selected', TEXTO)])
        st.map('Treeview.Heading', background=[('active', CABECERA)])

    def _encabezado(self):
        barra = ctk.CTkFrame(self, fg_color=AZUL, corner_radius=0, height=52)
        barra.pack(fill='x')
        barra.pack_propagate(False)
        ctk.CTkLabel(barra, text='Asistente de errores para Go', text_color='white',
                     font=ctk.CTkFont(size=19, weight='bold')).pack(side='left', padx=24)
        ctk.CTkLabel(barra, text='Léxico · Sintáctico · Semántico',
                     text_color='#DDE2F5', font=ctk.CTkFont(size=12)
                     ).pack(side='right', padx=24)

    def _boton(self, padre, texto, comando):
        return ctk.CTkButton(padre, text=texto, command=comando, height=36,
                             corner_radius=18, fg_color='white', text_color=AZUL,
                             hover_color=CABECERA, border_width=2, border_color=AZUL,
                             font=ctk.CTkFont(size=13, weight='bold'))

    def _barra(self):
        fila = ctk.CTkFrame(self, fg_color='transparent')
        fila.pack(fill='x', padx=24, pady=(14, 10))
        self.botones = {}
        self._boton(fila, 'Abrir archivo', self.abrir).pack(side='left', padx=(0, 8))
        self._boton(fila, 'Guardar', self.guardar).pack(side='left', padx=(0, 12))
        for tipo in (lg.LEXICO, lg.SINTACTICO, lg.SEMANTICO):
            b = self._boton(fila, TITULOS[tipo], lambda t=tipo: self.analizar(t))
            b.pack(side='left', padx=(0, 8))
            self.botones[tipo] = b
        self._boton(fila, 'Limpiar', self.limpiar).pack(side='left', padx=(4, 16))
        ctk.CTkLabel(fila, text='Desarrollador:', text_color=TENUE,
                     font=ctk.CTkFont(size=13)).pack(side='left', padx=(0, 6))
        self.nombres_dev = [n for n, _ in lg.DESARROLLADORES]
        self.selector = ctk.CTkOptionMenu(
            fila, values=self.nombres_dev, height=36, corner_radius=18,
            fg_color='white', text_color=AZUL, button_color='white',
            button_hover_color=CABECERA, dropdown_fg_color='white',
            dropdown_text_color=AZUL, dropdown_hover_color=CABECERA,
            font=ctk.CTkFont(size=13, weight='bold'), dynamic_resizing=False,
            width=190, command=lambda _v: self._actualizar_estado())
        self.selector.pack(side='left')

    def _panel(self, padre, titulo):
        marco = ctk.CTkFrame(padre, fg_color=PANEL, border_width=1,
                             border_color=BORDE, corner_radius=8)
        cab = ctk.CTkFrame(marco, fg_color=CABECERA, corner_radius=8, height=38)
        cab.pack(fill='x', padx=1, pady=1)
        cab.pack_propagate(False)
        etiqueta = ctk.CTkLabel(cab, text=titulo, text_color=TEXTO,
                                font=ctk.CTkFont(size=14, weight='bold'))
        etiqueta.pack(side='left', padx=14)
        return marco, etiqueta

    def _cuerpo(self):
        cuerpo = ctk.CTkFrame(self, fg_color='transparent')
        cuerpo.pack(fill='both', expand=True, padx=24)
        cuerpo.grid_columnconfigure(0, weight=11, uniform='c')
        cuerpo.grid_columnconfigure(1, weight=10, uniform='c')
        cuerpo.grid_rowconfigure(0, weight=1)

        # ---- editor con numeración de líneas
        izq, self.titulo_editor = self._panel(cuerpo, 'Editor de código fuente (Go)')
        izq.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        zona = tk.Frame(izq, bg=PANEL)
        zona.pack(fill='both', expand=True, padx=2, pady=(0, 2))
        zona.grid_columnconfigure(1, weight=1)
        zona.grid_rowconfigure(0, weight=1)
        comunes = dict(font=self.fuente_mono, bd=0, highlightthickness=0,
                       wrap='none', padx=6, pady=8, spacing1=0, spacing3=0)
        self.numeros = tk.Text(zona, width=4, bg=PANEL, fg=TENUE, cursor='arrow',
                               takefocus=0, state='disabled', **comunes)
        self.numeros.grid(row=0, column=0, sticky='ns')
        self.numeros.tag_configure('der', justify='right')
        self.numeros.tag_configure('err', background=ROJO_FONDO, foreground=ROJO)
        for ev in ('<MouseWheel>', '<Button-4>', '<Button-5>', '<Button-1>',
                   '<B1-Motion>', '<Double-Button-1>'):
            self.numeros.bind(ev, lambda e: 'break')
        # Las barras solo aparecen si el código no cabe en el editor
        self.sb_y = BarraAuto(zona, command=self._scroll_y)
        self.sb_y.grid(row=0, column=2, sticky='ns')
        self.sb_x = BarraAuto(zona, orientation='horizontal')
        self.sb_x.grid(row=1, column=0, columnspan=3, sticky='ew')
        self.editor = tk.Text(zona, bg=PANEL, fg=TEXTO, insertbackground=TEXTO,
                              undo=True, tabs=self.fuente_mono[1] * 3,
                              selectbackground='#C7D0EE', selectforeground=TEXTO,
                              yscrollcommand=self._al_scroll,
                              xscrollcommand=self.sb_x.set, **comunes)
        self.editor.grid(row=0, column=1, sticky='nsew')
        self.sb_x.configure(command=self.editor.xview)
        self.editor.tag_configure('linea_error', background=ROJO_FONDO)
        self.editor.tag_configure('foco', background=FOCO)
        for etiqueta, color in resaltado.COLORES.items():   # colores de sintaxis
            self.editor.tag_configure(etiqueta, foreground=color)
        self.editor.tag_raise('sel')
        self.editor.bind('<<Modified>>', self._al_modificar)
        self.editor.bind('<Control-s>', lambda e: (self.guardar(), 'break')[1])

        # ---- resultados (tabla de la propuesta + tabla de símbolos)
        der, self.titulo_tabla = self._panel(cuerpo, 'Resultados')
        der.grid(row=0, column=1, sticky='nsew', padx=(8, 0))
        self.pestanas = ctk.CTkTabview(
            der, fg_color=PANEL, corner_radius=0, height=10,
            segmented_button_fg_color=CABECERA,
            segmented_button_selected_color='#B9C3E6',
            segmented_button_selected_hover_color='#B9C3E6',
            segmented_button_unselected_color=CABECERA,
            segmented_button_unselected_hover_color='#D3D9EE',
            text_color=TEXTO)
        self.pestanas.pack(fill='both', expand=True, padx=2, pady=(0, 2))
        self.pestanas.add('Resultados')
        self.pestanas.add('Tabla de símbolos')
        self.tabla = self._crear_tabla(self.pestanas.tab('Resultados'))
        self.tabla_simbolos = self._crear_tabla(self.pestanas.tab('Tabla de símbolos'))
        self.tabla.bind('<<TreeviewSelect>>', self._seleccion_tabla)
        self._configurar_tabla(self.tabla_simbolos, lg.COLUMNAS_SIMBOLOS)
        self._configurar_tabla(self.tabla, [('linea', 'Línea', 60),
                                            ('mensaje', 'Mensaje', 560)])

    def _crear_tabla(self, padre):
        marco = tk.Frame(padre, bg=PANEL)
        marco.pack(fill='both', expand=True)
        marco.grid_columnconfigure(0, weight=1)
        marco.grid_rowconfigure(0, weight=1)
        tabla = ttk.Treeview(marco, show='headings', selectmode='browse')
        sy = BarraAuto(marco, command=tabla.yview)
        sx = BarraAuto(marco, orientation='horizontal', command=tabla.xview)
        tabla.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        tabla.grid(row=0, column=0, sticky='nsew')
        sy.grid(row=0, column=1, sticky='ns')
        sx.grid(row=1, column=0, sticky='ew')
        tabla.tag_configure('error', background=ROJO_FONDO, foreground=ROJO)
        return tabla

    def _configurar_tabla(self, tabla, columnas):
        tabla.delete(*tabla.get_children())
        tabla['columns'] = [c[0] for c in columnas]
        for i, (cid, titulo, ancho) in enumerate(columnas):
            tabla.heading(cid, text=titulo, anchor='w')
            tabla.column(cid, width=ancho, minwidth=40, anchor='w',
                         stretch=(i == len(columnas) - 1))

    def _consola(self):
        marco, _ = self._panel(self, 'Consola de resultados')
        marco.pack(side='bottom', fill='x', padx=24, pady=(10, 4))
        zona = tk.Frame(marco, bg=PANEL)
        zona.pack(fill='both', expand=True, padx=2, pady=(0, 2))
        zona.grid_columnconfigure(0, weight=1)
        zona.grid_rowconfigure(0, weight=1)
        sb = BarraAuto(zona)
        sb.grid(row=0, column=1, sticky='ns')
        self.consola = tk.Text(zona, height=7, bg=PANEL, fg=TEXTO, bd=0,
                               highlightthickness=0, wrap='word', padx=12, pady=8,
                               font=('Segoe UI', 11), state='disabled',
                               yscrollcommand=sb.set)
        self.consola.grid(row=0, column=0, sticky='nsew')
        sb.configure(command=self.consola.yview)
        t = self.consola
        t.tag_configure('insignia_ok', background=VERDE_FONDO, foreground=VERDE,
                        font=('Segoe UI', 10, 'bold'))
        t.tag_configure('insignia_err', background=ROJO_FONDO, foreground=ROJO,
                        font=('Segoe UI', 10, 'bold'))
        t.tag_configure('insignia_aviso', background=AMBAR_FONDO, foreground=AMBAR,
                        font=('Segoe UI', 10, 'bold'))
        t.tag_configure('ok', foreground=VERDE)
        t.tag_configure('err', foreground=ROJO)
        t.tag_configure('aviso', foreground=AMBAR)
        t.tag_configure('sugerencia', foreground=TENUE, lmargin1=28, lmargin2=28)
        t.tag_configure('tenue', foreground=TENUE)
        self._escribir_consola([('Listo. Escribe o abre un archivo .go y elige un '
                                 'análisis.', 'tenue')])

    def _estado(self):
        fila = ctk.CTkFrame(self, fg_color='transparent')
        fila.pack(side='bottom', fill='x', padx=24, pady=(0, 8))
        self.lbl_log = ctk.CTkLabel(fila, text='', text_color=TENUE,
                                    font=ctk.CTkFont(size=12))
        self.lbl_log.pack(side='left')
        self.lbl_estado = ctk.CTkLabel(fila, text='', text_color=TENUE,
                                       font=ctk.CTkFont(size=12))
        self.lbl_estado.pack(side='left', padx=24)
        self.lbl_archivo = ctk.CTkLabel(fila, text='', text_color=TENUE,
                                        font=ctk.CTkFont(size=12))
        self.lbl_archivo.pack(side='right')

    # ----------------------------------------------------------- editor
    def _scroll_y(self, *args):
        self.editor.yview(*args)
        self.numeros.yview(*args)

    def _al_scroll(self, primero, ultimo):
        self.sb_y.set(primero, ultimo)
        self.numeros.yview_moveto(primero)

    def _colorear(self):
        """Pinta el código con los colores de resaltado.py."""
        for etiqueta in resaltado.COLORES:
            self.editor.tag_remove(etiqueta, '1.0', 'end')
        for etiqueta, a, b in resaltado.resaltar(self.editor.get('1.0', 'end-1c')):
            self.editor.tag_add(etiqueta, '1.0+%dc' % a, '1.0+%dc' % b)

    def _al_modificar(self, _evento=None):
        if not self.editor.edit_modified() and _evento is not None:
            return
        self.editor.edit_modified(False)
        n = int(self.editor.index('end-1c').split('.')[0])
        ancho = max(3, len(str(n)))
        self.numeros.configure(width=ancho + 1, state='normal')
        self.numeros.delete('1.0', 'end')
        self.numeros.insert('1.0', '\n'.join(str(i) for i in range(1, n + 1)), 'der')
        self.numeros.configure(state='disabled')
        self.numeros.yview_moveto(self.editor.yview()[0])
        self._colorear()
        if _evento is not None:
            self.modificado = True
            self._quitar_marcas()
            if self.resultado is not None:
                self._actualizar_estado(
                    'texto modificado: vuelve a ejecutar el análisis')
            else:
                self._actualizar_estado()

    def _quitar_marcas(self):
        self.editor.tag_remove('linea_error', '1.0', 'end')
        self.numeros.tag_remove('err', '1.0', 'end')

    def _marcar_lineas(self, lineas):
        self._quitar_marcas()
        ultima = int(self.editor.index('end-1c').split('.')[0])
        for n in lineas:
            if 1 <= n <= ultima:
                self.editor.tag_add('linea_error', '%d.0' % n, '%d.0' % (n + 1))
                self.numeros.tag_add('err', '%d.0' % n, '%d.0' % (n + 1))

    def ir_a_linea(self, n):
        """Lleva el cursor a la línea n y la resalta un momento."""
        ultima = int(self.editor.index('end-1c').split('.')[0])
        if not 1 <= n <= ultima:
            return
        self.editor.mark_set('insert', '%d.0' % n)
        self.editor.see('%d.0' % n)
        self.editor.tag_remove('foco', '1.0', 'end')
        self.editor.tag_add('foco', '%d.0' % n, '%d.0' % (n + 1))
        self.editor.focus_set()
        if self._ids_foco:
            self.after_cancel(self._ids_foco)
        self._ids_foco = self.after(1500, lambda: self.editor.tag_remove(
            'foco', '1.0', 'end'))

    def destroy(self):
        if self._ids_foco:                 # evita un temporizador huérfano
            try:
                self.after_cancel(self._ids_foco)
            except tk.TclError:
                pass
            self._ids_foco = None
        super().destroy()

    def texto(self):
        return self.editor.get('1.0', 'end-1c')

    def _poner_texto(self, texto):
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', texto)
        self.editor.edit_reset()
        self._al_modificar()        # numeración al día; no cuenta como edición

    # --------------------------------------------------------- acciones
    def abrir(self, ruta=None):
        if ruta is None:
            ruta = filedialog.askopenfilename(
                title='Abrir archivo Go', initialdir=self._carpeta_inicial(),
                filetypes=[('Archivos Go', '*.go'), ('Todos los archivos', '*.*')])
        if not ruta:
            return None
        try:
            with open(ruta, encoding='utf-8') as f:
                contenido = f.read()
        except (OSError, UnicodeDecodeError) as exc:
            messagebox.showerror('No se pudo abrir', str(exc))
            return None
        self._poner_texto(contenido)
        self.ruta = ruta
        self.modificado = False
        self._reiniciar_resultados()
        self._escribir_consola([('Archivo abierto: %s' % os.path.basename(ruta),
                                 'tenue')])
        self._actualizar_estado('archivo cargado')
        return ruta

    def guardar(self, ruta=None):
        if ruta is None:
            ruta = self.ruta
        if ruta is None:
            ruta = filedialog.asksaveasfilename(
                title='Guardar archivo Go', initialdir=self._carpeta_inicial(),
                defaultextension='.go', filetypes=[('Archivos Go', '*.go')])
        if not ruta:
            return None
        try:
            with open(ruta, 'w', encoding='utf-8', newline='\n') as f:
                f.write(self.texto())
        except OSError as exc:
            messagebox.showerror('No se pudo guardar', str(exc))
            return None
        self.ruta = ruta
        self.modificado = False
        self._actualizar_estado('archivo guardado')
        return ruta

    def limpiar(self, confirmar=True):
        if (confirmar and self.modificado and self.texto().strip()
                and not messagebox.askyesno(
                    'Limpiar', 'Hay cambios sin guardar. ¿Quieres limpiar de todos modos?')):
            return
        self._poner_texto('')
        self.ruta = None
        self.modificado = False
        self._reiniciar_resultados()
        self._escribir_consola([('Editor y resultados limpiados.', 'tenue')])
        self._actualizar_estado('listo')

    def _carpeta_inicial(self):
        if self.ruta:
            return os.path.dirname(self.ruta)
        algoritmos = os.path.join(lg.BASE, 'algoritmos')
        return algoritmos if os.path.isdir(algoritmos) else lg.BASE

    def analizar(self, tipo):
        codigo = self.texto()
        if not codigo.strip():
            self._reiniciar_resultados()
            self._escribir_consola([('⚠ ADVERTENCIA', 'insignia_aviso'),
                                    ('  El editor está vacío: escribe o abre un '
                                     'archivo antes de analizar.', 'aviso')])
            self._actualizar_estado('sin análisis')
            return None
        try:
            res = lg.analizar(tipo, codigo, self.nombres_dev.index(self.selector.get()),
                              lg.ruta_para_log(self.ruta), self.carpeta_logs)
        except Exception as exc:        # nunca dejar la ventana sin respuesta
            self._escribir_consola([('✘ ERROR INTERNO', 'insignia_err'),
                                    ('  %s: %s' % (type(exc).__name__, exc), 'err')])
            self._actualizar_estado('falló el análisis')
            return None
        self.resultado = res
        self.analisis_activo = tipo
        self._mostrar(res)
        return res

    # ------------------------------------------------------- resultados
    def _reiniciar_resultados(self):
        self.resultado = None
        self.analisis_activo = None
        self._quitar_marcas()
        self._configurar_tabla(self.tabla, [('linea', 'Línea', 60),
                                            ('mensaje', 'Mensaje', 560)])
        self._configurar_tabla(self.tabla_simbolos, lg.COLUMNAS_SIMBOLOS)
        self.titulo_tabla.configure(text='Resultados')
        self.lbl_log.configure(text='')
        self._resaltar_boton(None)

    def _resaltar_boton(self, activo):
        for tipo, b in self.botones.items():
            if tipo == activo:
                b.configure(fg_color=AZUL, text_color='white', hover_color=AZUL)
            else:
                b.configure(fg_color='white', text_color=AZUL, hover_color=CABECERA)

    def _mostrar(self, res):
        self._resaltar_boton(res.analisis)
        self.titulo_tabla.configure(text=res.titulo_panel)
        self._configurar_tabla(self.tabla, res.columnas)
        for valores, etiqueta in res.filas:
            self.tabla.insert('', 'end', values=valores,
                              tags=(etiqueta,) if etiqueta else ())
        self._configurar_tabla(self.tabla_simbolos, lg.COLUMNAS_SIMBOLOS)
        for fila in res.simbolos:
            self.tabla_simbolos.insert('', 'end', values=fila)
        # semántica correcta: no hay errores que listar, se muestra la tabla de símbolos
        self.pestanas.set('Tabla de símbolos' if res.analisis == lg.SEMANTICO
                          and res.ok else 'Resultados')
        self._marcar_lineas(res.lineas_error)
        self._consola_resultado(res)
        self.lbl_log.configure(text='Log generado: %s' % res.nombre_log)
        nombre = lg.NOMBRE_ANALISIS[res.analisis]
        if not res.ejecutado:
            estado = 'análisis %s no ejecutado' % nombre
        elif res.errores:
            estado = 'análisis %s finalizado con %d error(es)' % (nombre, len(res.errores))
        else:
            estado = 'análisis %s finalizado sin errores' % nombre
        self._actualizar_estado(estado)

    def _consola_resultado(self, res):
        partes = []
        if not res.ejecutado:
            partes += [('⚠ NO EJECUTADO', 'insignia_aviso'),
                       ('  ' + res.resumen + '\n', 'aviso')]
            if res.aviso:
                partes.append((res.aviso + '\n', 'tenue'))
        elif res.errores:
            partes += [('✘ ERRORES (%d)' % len(res.errores), 'insignia_err'),
                       ('  ' + res.resumen + '\n', 'err')]
        else:
            partes += [('✔ ÉXITO', 'insignia_ok'), ('  ' + res.resumen + '\n', 'ok')]
        for i, e in enumerate(res.errores):
            etiqueta = 'ir_%d' % i
            partes.append(('✘ Línea %d' % e.linea +
                           (', col. %d' % e.columna if e.columna else '') +
                           ' [%s] %s\n' % (e.codigo, e.texto), ('err', etiqueta)))
            if e.sugerencia:
                partes.append(('Sugerencia: %s\n' % e.sugerencia, 'sugerencia'))
        self._escribir_consola(partes)
        for i, e in enumerate(res.errores):
            etiqueta = 'ir_%d' % i
            self.consola.tag_bind(etiqueta, '<Button-1>',
                                  lambda _ev, n=e.linea: self.ir_a_linea(n))
            self.consola.tag_bind(etiqueta, '<Enter>',
                                  lambda _ev: self.consola.configure(cursor='hand2'))
            self.consola.tag_bind(etiqueta, '<Leave>',
                                  lambda _ev: self.consola.configure(cursor=''))

    def _escribir_consola(self, partes):
        t = self.consola
        t.configure(state='normal')
        t.delete('1.0', 'end')
        for texto, etiquetas in partes:
            t.insert('end', texto, etiquetas)
        t.configure(state='disabled')
        t.yview_moveto(0)

    def _seleccion_tabla(self, _evento=None):
        if self.resultado is None:
            return
        sel = self.tabla.selection()
        if not sel:
            return
        valor = self.tabla.item(sel[0], 'values')[0]
        if str(valor).isdigit():
            self.ir_a_linea(int(valor))

    def _actualizar_estado(self, estado=None):
        if estado is not None:
            self._estado_texto = estado
        self.lbl_estado.configure(
            text='Estado: %s' % getattr(self, '_estado_texto', 'listo'))
        nombre = os.path.basename(self.ruta) if self.ruta else 'sin título'
        self.lbl_archivo.configure(
            text='Archivo: %s%s   |   Desarrollador: %s' % (
                nombre, ' ●' if self.modificado else '', self.selector.get()))


def main():
    App().mainloop()


if __name__ == '__main__':
    main()
    