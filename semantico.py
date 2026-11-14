# -*- coding: utf-8 -*-
"""
Analizador semántico (Avance 3) del Asistente Educativo de Errores para Go.

Recorre el AST que construye sintactico.py y comprueba seis reglas:

    S1  Identificadores      toda variable o función se declara antes de usarse
                             (y una sola vez en cada ámbito)
    S2  Constantes           una constante no puede reasignarse ni modificarse
    S3  Asignación de tipo   el valor asignado coincide con el tipo de la variable
    S4  Retorno de funciones tipo y cantidad de valores de return
    S5  Operaciones          operandos compatibles con cada operador
    S6  Estructuras de control  break / continue solo dentro de for (o switch)

Uso:
    from sintactico import AnalizadorSintactico
    from semantico import AnalizadorSemantico
    arbol, errores_sint, errores_lex = AnalizadorSintactico().analizar(codigo)
    errores = AnalizadorSemantico().analizar(arbol)

Cada error es un dict {'codigo', 'categoria', 'linea', 'mensaje'}.
Los tipos se representan como cadenas: 'int', 'float64', 'string', 'bool',
'[3]int' (arreglo), '[]string' (slice) y 'map[string]int' (mapa). Una
expresión de tipo desconocido (por un error ya reportado) vale None; así no
se encadenan errores. Una llamada que no devuelve exactamente un valor vale
una tupla con sus tipos (vacía si no devuelve nada).

Reparto del trabajo (cada aporte está delimitado con INICIO / FIN aporte):
    Fátima Torres   : tabla de símbolos por ámbitos, recorrido del AST, S1 y S2
    Elkin Salazar   : tipo de cada expresión y S5, contador de bucles y S6
    César Balladares: S3 y S4 (tipos asignados y retornos de funciones)
"""
import re

TIPOS_NUMERICOS = ('int', 'float64')
TIPOS_SIMPLES = ('int', 'float64', 'string', 'bool')

CATEGORIAS = {
    'S1': 'Identificadores',
    'S2': 'Constantes',
    'S3': 'Asignación de tipo',
    'S4': 'Retorno de funciones',
    'S5': 'Operaciones permitidas',
    'S6': 'Estructuras de control',
}

class SinTipo(str):
    """Tipo 'int' de una constante sin tipo (literal entero o const).

    Como en Go, un literal entero escrito directamente (5, -1) se adapta a
    float64 cuando hace falta; una variable, en cambio, tiene un tipo fijo.
    Vale 'int' en todas las comparaciones y solo se distingue con isinstance.
    """
    __slots__ = ()


def con_tipo(tipo):
    """Al guardar el valor en una variable deja de ser una constante sin tipo."""
    return str(tipo) if isinstance(tipo, SinTipo) else tipo


def compatible(destino, valor):
    """¿Se puede asignar un valor de tipo 'valor' a algo de tipo 'destino'?"""
    return destino == valor or (destino == 'float64' and isinstance(valor, SinTipo))


def unificar(izq, der):
    """Operandos de una operación: una constante sin tipo toma el tipo del
    otro operando si este es numérico (2 * x con x float64 es float64)."""
    if isinstance(izq, SinTipo) != isinstance(der, SinTipo):
        con_tipo_, sin_tipo = (der, izq) if isinstance(izq, SinTipo) else (izq, der)
        if con_tipo_ in TIPOS_NUMERICOS:
            return con_tipo_, con_tipo_
    return izq, der


_TIPO_LITERAL = {
    'INTEGER_VALUE': SinTipo('int'),
    'FLOAT_VALUE': 'float64',
    'STRING_VALUE': 'string',
    'TRUE': 'bool',
    'FALSE': 'bool',
}

_RE_ARREGLO = re.compile(r'^\[(\d*)\](.+)$')
_RE_MAPA = re.compile(r'^map\[(int|float64|string|bool)\](.+)$')

_VALOR_SUGERIDO = {
    'int': 'un valor entero',
    'float64': 'un valor decimal (float64)',
    'string': 'una cadena entre comillas dobles',
    'bool': 'true o false',
}
_RETORNO_SUGERIDO = {
    'int': 'un entero',
    'float64': 'un decimal (float64)',
    'string': 'una cadena',
    'bool': 'true o false',
}


def elemento_de(tipo):
    """Tipo de los elementos de un arreglo o slice ('[3]int' -> 'int'), o None."""
    m = _RE_ARREGLO.match(tipo) if isinstance(tipo, str) else None
    return m.group(2) if m else None


def partes_mapa(tipo):
    """(tipo_clave, tipo_valor) de un mapa, o None."""
    m = _RE_MAPA.match(tipo) if isinstance(tipo, str) else None
    return (m.group(1), m.group(2)) if m else None


def _plural(n, singular, plural):
    return '%d %s' % (n, singular if n == 1 else plural)


def _lista_tipos(tipos):
    return ', '.join(str(t) for t in tipos)


# ===========================================================================
# FÁTIMA TORRES (infraestructura): símbolos y tabla de símbolos por ámbitos
# ===========================================================================
# INICIO aporte: Fátima Torres (infraestructura)
class Simbolo:
    """Entrada de la tabla de símbolos."""
    __slots__ = ('nombre', 'tipo', 'es_const', 'ambito', 'linea',
                 'es_funcion', 'params', 'retornos')

    def __init__(self, nombre, tipo, es_const, ambito, linea,
                 es_funcion=False, params=None, retornos=None):
        self.nombre = nombre
        self.tipo = tipo
        self.es_const = es_const
        self.ambito = ambito
        self.linea = linea
        self.es_funcion = es_funcion
        self.params = params or []          # [(nombre, tipo), ...]
        self.retornos = retornos or []      # [tipo, ...]

    def descripcion_tipo(self):
        if self.es_funcion:
            params = ', '.join('%s %s' % p for p in self.params)
            if not self.retornos:
                ret = ''
            elif len(self.retornos) == 1:
                ret = ' ' + self.retornos[0]
            else:
                ret = ' (%s)' % ', '.join(self.retornos)
            return 'func(%s)%s' % (params, ret)
        return str(self.tipo) if self.tipo is not None else '(desconocido)'


class TablaSimbolos:
    """Pila de ámbitos (global -> función -> bloque)."""

    def __init__(self):
        self._ambitos = []          # lista de (etiqueta, {nombre: Simbolo})
        self.historial = []         # todos los símbolos declarados, en orden

    @property
    def etiqueta(self):
        return self._ambitos[-1][0] if self._ambitos else 'global'

    def entrar(self, etiqueta):
        self._ambitos.append((etiqueta, {}))

    def salir(self):
        self._ambitos.pop()

    def declarar(self, simbolo):
        self._ambitos[-1][1][simbolo.nombre] = simbolo
        self.historial.append(simbolo)

    def buscar_local(self, nombre):
        return self._ambitos[-1][1].get(nombre)

    def buscar(self, nombre):
        """Busca desde el ámbito actual hacia los que lo contienen."""
        for _, simbolos in reversed(self._ambitos):
            if nombre in simbolos:
                return simbolos[nombre]
        return None
# FIN aporte: Fátima Torres (infraestructura)


# ===========================================================================
# 1. FÁTIMA TORRES
#    S1: toda variable o función debe estar declarada antes de usarse, en el
#        ámbito actual o en uno que lo contenga (bloque, función o global).
#    S2: una constante no puede reasignarse ni modificarse (=, +=, -=, ++, --).
# ===========================================================================
# INICIO aporte: Fátima Torres
class _ReglasFatima:
    def _registrar(self, codigo, linea, texto):
        """Guarda un error semántico (sin repetir el mismo en la misma línea)."""
        clave = (codigo, linea, texto)
        if clave in self._vistos:
            return
        self._vistos.add(clave)
        self.errores.append({
            'codigo': codigo,
            'categoria': CATEGORIAS[codigo],
            'linea': linea,
            'mensaje': 'Error semántico [línea %d]: %s' % (linea, texto),
        })

    # --- S1 ---------------------------------------------------------------
    def _resolver_id(self, nombre, linea):
        """Busca una variable en los ámbitos visibles; reporta S1 si no existe."""
        if nombre == '_':                        # identificador en blanco
            return None
        simbolo = self.tabla.buscar(nombre)
        if simbolo is None:
            self._registrar('S1', linea,
                            "la variable '%s' no ha sido declarada. "
                            "Sugerencia: declárala con var o :=." % nombre)
        return simbolo

    def _resolver_funcion(self, nombre, linea):
        """Busca una función; reporta S1 si no existe."""
        simbolo = self.tabla.buscar(nombre)
        if simbolo is None:
            self._registrar('S1', linea,
                            "la función '%s' no ha sido declarada. "
                            "Sugerencia: defínela con func antes de llamarla."
                            % nombre)
            return None
        return simbolo if simbolo.es_funcion else None

    def s1_redeclarada(self, nombre, linea):
        """S1: el nombre ya se declaró en este mismo ámbito (var, const, func,
        parámetro o :=). Devuelve True si hay error."""
        previo = self.tabla.buscar_local(nombre)
        if nombre == '_' or previo is None:
            return False
        self._registrar('S1', linea,
                        "el nombre '%s' ya fue declarado en este ámbito "
                        "(línea %d). Sugerencia: usa otro nombre, o asigna con "
                        "= si solo quieres cambiar su valor."
                        % (nombre, previo.linea))
        return True

    def s1_sin_nuevas(self, nombres, linea):
        """S1: un := debe declarar al menos una variable nueva."""
        propios = [n for n in nombres if n != '_']
        if propios and all(self.tabla.buscar_local(n) is not None
                           for n in propios):
            self._registrar('S1', linea,
                            "no hay variables nuevas a la izquierda de :=. "
                            "Sugerencia: usa = para asignar a variables que ya "
                            "existen.")

    # --- S2 ---------------------------------------------------------------
    def s2_modificar(self, simbolo, linea):
        """S2: se intenta cambiar el valor de 'simbolo' (=, +=, -=, ++, --, &)."""
        if simbolo is not None and simbolo.es_const:
            self._registrar('S2', linea,
                            "no se puede modificar la constante '%s'. "
                            "Sugerencia: usa una variable si el valor debe "
                            "cambiar." % simbolo.nombre)
# FIN aporte: Fátima Torres


# ===========================================================================
# 2. ELKIN SALAZAR
#    S5: determinar el tipo de cada expresión y verificar que los operandos
#        sean compatibles con el operador (aritméticos, % solo con enteros,
#        lógicos solo con bool, comparaciones del mismo tipo).
#    S6: mantener un contador de bucles y switch abiertos para validar
#        break y continue.
# ===========================================================================
# INICIO aporte: Elkin Salazar
class _ReglasElkin:
    def _iniciar_elkin(self):
        self._bucles = 0
        self._switches = 0

    # --- S6: break y continue -------------------------------------------
    def s6_reiniciar(self):
        self._bucles = 0
        self._switches = 0

    def s6_entrar_bucle(self):
        self._bucles += 1

    def s6_salir_bucle(self):
        self._bucles -= 1

    def s6_entrar_switch(self):
        self._switches += 1

    def s6_salir_switch(self):
        self._switches -= 1

    def s6_break(self, n):
        if self._bucles == 0 and self._switches == 0:
            self._registrar('S6', n.linea,
                            "'break' fuera de un bucle o switch. "
                            "Sugerencia: muévelo dentro de un for.")

    def s6_continue(self, n):
        if self._bucles == 0:
            self._registrar('S6', n.linea,
                            "'continue' fuera de un bucle. "
                            "Sugerencia: muévelo dentro de un for.")

    # --- S5: tipos de las expresiones y operaciones permitidas -----------
    def _s5_llamada_multiple(self, linea, texto_op, hijo, tipos):
        """Un operando es una llamada que no devuelve exactamente un valor."""
        if hijo is not None and hijo.tipo == 'llamada':
            quien = "la función '%s'" % hijo.hijos[0]
        else:
            quien = 'una llamada a función'
        cuantos = ('no devuelve ningún valor' if not tipos
                   else 'devuelve %d valores' % len(tipos))
        self._registrar('S5', linea,
                        "operación '%s' inválida: %s %s y aquí se necesita uno. "
                        "Sugerencia: guarda los resultados en variables con := "
                        "antes de usarlos en una operación."
                        % (texto_op, quien, cuantos))

    def _s5_aritmetica(self, linea, texto_op, op, tl, tr):
        """Valida + - * / % entre dos tipos conocidos; devuelve el tipo o None."""
        if op == '%':
            if tl == 'int' and tr == 'int':
                return 'int'
            self._registrar('S5', linea,
                            "el operador '%%' solo se aplica a enteros, pero "
                            "recibió %s y %s. Sugerencia: usa operandos de "
                            "tipo int." % (tl, tr))
            return None
        if tl != tr:
            self._registrar('S5', linea,
                            "operación '%s' inválida entre %s y %s. "
                            "Sugerencia: usa el mismo tipo en ambos lados."
                            % (texto_op, tl, tr))
            return None
        if tl in TIPOS_NUMERICOS:
            return tl
        if tl == 'string':
            if op == '+':
                return 'string'
            self._registrar('S5', linea,
                            "el operador '%s' no se puede aplicar a valores "
                            "string. Sugerencia: con cadenas solo se puede "
                            "usar + para concatenar." % texto_op)
            return None
        self._registrar('S5', linea,
                        "el operador '%s' solo se aplica a números (y + a "
                        "cadenas), pero recibió %s y %s. Sugerencia: usa "
                        "operandos int o float64." % (texto_op, tl, tr))
        return None

    def _s5_division_cero(self, n, op, tl, tr):
        """/ o % entre enteros con divisor 0 escrito directamente."""
        der = n.hijos[2]
        if (op in ('/', '%') and tl == 'int' and tr == 'int'
                and der.tipo == 'literal' and der.hijos[0] == 'INTEGER_VALUE'
                and int(der.hijos[1]) == 0):
            self._registrar('S5', n.linea,
                            "división entre cero con el operador '%s'. "
                            "Sugerencia: usa un divisor distinto de 0." % op)
            return True
        return False

    def s5_binaria(self, n, op, tl, tr):
        """Operadores aritméticos, lógicos y de comparación; devuelve el tipo."""
        es_bool = n.tipo in ('comparacion', 'logica')
        for hijo, t in ((n.hijos[1], tl), (n.hijos[2], tr)):
            if isinstance(t, tuple):
                self._s5_llamada_multiple(n.linea, op, hijo, t)
                return 'bool' if es_bool else None
        if tl is None or tr is None:
            return 'bool' if es_bool else None
        tl, tr = unificar(tl, tr)
        if n.tipo == 'aritmetica':
            if self._s5_division_cero(n, op, tl, tr):
                return None
            return self._s5_aritmetica(n.linea, op, op, tl, tr)
        if n.tipo == 'logica':
            if tl != 'bool' or tr != 'bool':
                self._registrar('S5', n.linea,
                                "el operador '%s' solo se aplica a valores "
                                "bool, pero recibió %s y %s. Sugerencia: usa "
                                "condiciones que den true o false, por "
                                "ejemplo x > 0." % (op, tl, tr))
            return 'bool'
        # comparación
        if tl != tr:
            self._registrar('S5', n.linea,
                            "operación '%s' inválida entre %s y %s. "
                            "Sugerencia: compara valores del mismo tipo."
                            % (op, tl, tr))
        elif tl not in TIPOS_SIMPLES:
            self._registrar('S5', n.linea,
                            "operación '%s' inválida entre valores de tipo %s. "
                            "Sugerencia: compara los elementos uno por uno, "
                            "por ejemplo a[0] == b[0]." % (op, tl))
        return 'bool'

    def s5_not(self, n, t):
        if isinstance(t, tuple):
            self._s5_llamada_multiple(n.linea, '!', n.hijos[0], t)
        elif t is not None and t != 'bool':
            self._registrar('S5', n.linea,
                            "el operador '!' solo se aplica a valores bool, "
                            "pero recibió %s. Sugerencia: usa una condición "
                            "que dé true o false, por ejemplo !(x > 0)." % t)
        return 'bool'

    def s5_menos(self, n, t):
        if isinstance(t, tuple):
            self._s5_llamada_multiple(n.linea, '-', n.hijos[0], t)
            return None
        if t is None:
            return None
        if t not in TIPOS_NUMERICOS:
            self._registrar('S5', n.linea,
                            "el signo '-' solo se aplica a números, pero "
                            "recibió %s. Sugerencia: usa un valor int o "
                            "float64." % t)
            return None
        return t

    def s5_incdec(self, n, t):
        """x++ y x-- solo con int o float64."""
        if t is None or isinstance(t, tuple):
            return
        if t not in TIPOS_NUMERICOS:
            self._registrar('S5', n.linea,
                            "el operador '%s' solo se aplica a números (int o "
                            "float64), pero la variable es %s. Sugerencia: usa "
                            "una variable numérica." % (n.hijos[0], t))

    def s5_compuesta(self, n, tl, tr):
        """x += y y x -= y: equivalen a x = x + y y x = x - y."""
        op = n.hijos[0]
        if isinstance(tr, tuple):
            self._s5_llamada_multiple(n.linea, op, n.hijos[2], tr)
            return
        if tl is None or tr is None:
            return
        tl, tr = unificar(tl, tr)
        self._s5_aritmetica(n.linea, op, op[0], tl, tr)

    def s5_indice(self, n, tbase, tindice):
        """Acceso nombre[expr]; devuelve el tipo del elemento."""
        nombre = n.hijos[0]
        if tbase is None:
            return None
        elemento = elemento_de(tbase)
        if elemento is not None:
            if tindice is not None and tindice != 'int':
                self._registrar('S5', n.linea,
                                "el índice de '%s' debe ser int, pero es %s. "
                                "Sugerencia: usa un entero como índice, por "
                                "ejemplo %s[0]." % (nombre, tindice, nombre))
            return elemento
        mapa = partes_mapa(tbase)
        if mapa is not None:
            clave, valor = mapa
            if tindice is not None and not compatible(clave, tindice):
                self._registrar('S5', n.linea,
                                "la clave de '%s' debe ser %s, pero es %s. "
                                "Sugerencia: usa una clave de tipo %s."
                                % (nombre, clave, tindice, clave))
            return valor
        self._registrar('S5', n.linea,
                        "no se puede indexar '%s' de tipo %s con []. "
                        "Sugerencia: solo los arreglos, slices y mapas se "
                        "indexan." % (nombre, tbase))
        return None

    def s5_case(self, caso, tswitch, tcase):
        """Cada case se compara con la expresión del switch (mismo tipo)."""
        if tswitch is None or tcase is None or isinstance(tcase, tuple):
            return
        tswitch, tcase = unificar(tswitch, tcase)
        if tswitch != tcase:
            self._registrar('S5', caso.linea,
                            "el case compara un valor %s con un switch de tipo "
                            "%s. Sugerencia: usa valores de tipo %s en los "
                            "case." % (tcase, tswitch, tswitch))
# FIN aporte: Elkin Salazar


# ===========================================================================
# 3. CÉSAR BALLADARES
#    S3: guardar en la tabla de símbolos el tipo declarado o deducido de cada
#        variable y compararlo con el tipo de cada valor asignado.
#    S4: comparar el tipo y la cantidad de valores de cada return con el
#        retorno declarado en la firma de la función.
# ===========================================================================
# INICIO aporte: César Balladares
class _ReglasCesar:
    def _iniciar_cesar(self):
        pass

    # --- S3: asignación de tipo -------------------------------------------
    def s3_asignar(self, linea, destino, tdest, tval):
        """Un valor de tipo 'tval' se asigna a 'destino' (de tipo 'tdest')."""
        if isinstance(tval, tuple):
            if not tval:
                self._registrar('S3', linea,
                                "no se puede asignar a %s el resultado de una "
                                "función que no devuelve ningún valor. "
                                "Sugerencia: usa una función que devuelva un "
                                "valor." % destino)
            else:
                self._registrar('S3', linea,
                                "no se pueden asignar %d valores a %s. "
                                "Sugerencia: usa una variable por cada valor, "
                                "por ejemplo a, b := f()." % (len(tval), destino))
            return
        if tdest is None or tval is None:
            return
        if not compatible(tdest, tval):
            self._registrar('S3', linea,
                            "no se puede asignar %s a %s. Sugerencia: usa %s."
                            % (tval, destino,
                               _VALOR_SUGERIDO.get(tdest,
                                                   'un valor de tipo %s' % tdest)))

    def s3_declare(self, n, nombres, exprs, vals):
        """Declaración corta: la cantidad de nombres debe igualar la de valores."""
        if len(exprs) == 1 and exprs[0].tipo == 'llamada':
            if len(vals) == 1 and vals[0] is None:       # llamada ya reportada
                return
            if len(vals) != len(nombres):
                nombre_f = exprs[0].hijos[0]
                if not vals:
                    self._registrar('S3', n.linea,
                                    "no se puede declarar %s con el resultado "
                                    "de la función '%s' porque no devuelve "
                                    "ningún valor. Sugerencia: llama a la "
                                    "función sin guardar su resultado."
                                    % (_plural(len(nombres), 'variable',
                                               'variables'), nombre_f))
                else:
                    self._registrar('S3', n.linea,
                                    "se declaran %s pero la función '%s' "
                                    "devuelve %s. Sugerencia: declara una "
                                    "variable por cada valor que devuelve."
                                    % (_plural(len(nombres), 'variable',
                                               'variables'), nombre_f,
                                       _plural(len(vals), 'valor', 'valores')))
            return
        for e, t in zip(exprs, vals):
            if isinstance(t, tuple):
                quien = (("la función '%s'" % e.hijos[0]) if e.tipo == 'llamada'
                         else 'una llamada a función')
                cuantos = ('no devuelve ningún valor' if not t
                           else 'devuelve %d valores' % len(t))
                self._registrar('S3', n.linea,
                                "no se puede usar %s como un solo valor porque "
                                "%s. Sugerencia: guarda sus resultados en "
                                "variables con :=." % (quien, cuantos))
        if len(exprs) != len(nombres):
            self._registrar('S3', n.linea,
                            "se declaran %s pero se reciben %s. Sugerencia: la "
                            "cantidad de nombres debe ser igual a la de valores."
                            % (_plural(len(nombres), 'variable', 'variables'),
                               _plural(len(exprs), 'valor', 'valores')))

    def s3_argumentos(self, n, simbolo, vals):
        """Los argumentos de una llamada se asignan a los parámetros."""
        if simbolo is None or not simbolo.es_funcion:
            return
        nombre = n.hijos[0]
        params = simbolo.params
        if len(vals) != len(params):
            firma = ', '.join('%s %s' % p for p in params)
            self._registrar('S3', n.linea,
                            "la función '%s' espera %s, pero recibe %d. "
                            "Sugerencia: llama a %s con (%s)."
                            % (nombre, _plural(len(params), 'argumento',
                                               'argumentos'), len(vals),
                               nombre, firma))
            return
        for (pnombre, ptipo), v in zip(params, vals):
            if v is None or isinstance(v, tuple):
                continue
            if not compatible(ptipo, v):
                self._registrar('S3', n.linea,
                                "no se puede pasar %s como argumento '%s' de "
                                "tipo %s a la función '%s'. Sugerencia: usa %s."
                                % (v, pnombre, ptipo, nombre,
                                   _VALOR_SUGERIDO.get(ptipo,
                                                       'un valor de tipo %s'
                                                       % ptipo)))

    def s3_elementos(self, n, tipo_elem, exprs, tipos):
        """Elementos de un literal de arreglo o slice."""
        clase = 'arreglo' if n.tipo == 'arreglo' else 'slice'
        for e, t in zip(exprs, tipos):
            if t is None or isinstance(t, tuple):
                continue
            if not compatible(tipo_elem, t):
                self._registrar('S3', e.linea,
                                "no se puede usar %s como elemento de un %s de "
                                "%s. Sugerencia: usa %s."
                                % (t, clase, tipo_elem,
                                   _VALOR_SUGERIDO.get(tipo_elem,
                                                       'un valor de tipo %s'
                                                       % tipo_elem)))

    def s3_pares(self, n, tclave, tvalor, pares, tipos):
        """Claves y valores de un literal de mapa."""
        for par, (tk, tv) in zip(pares, tipos):
            if tk is not None and not isinstance(tk, tuple) and not compatible(tclave, tk):
                self._registrar('S3', par.linea,
                                "no se puede usar %s como clave de un mapa con "
                                "claves %s. Sugerencia: usa %s como clave."
                                % (tk, tclave,
                                   _VALOR_SUGERIDO.get(tclave, tclave)))
            if tv is not None and not isinstance(tv, tuple) and not compatible(tvalor, tv):
                self._registrar('S3', par.linea,
                                "no se puede usar %s como valor de un mapa con "
                                "valores %s. Sugerencia: usa %s."
                                % (tv, tvalor,
                                   _VALOR_SUGERIDO.get(tvalor, tvalor)))

    # --- S4: retorno de funciones -----------------------------------------
    @staticmethod
    def _descripcion_retornos(tipos):
        if len(tipos) == 1:
            return tipos[0]
        return '%d valores (%s)' % (len(tipos), _lista_tipos(tipos))

    def s4_return(self, n, simbolo, vals):
        """El return debe coincidir en cantidad y tipos con la firma."""
        if simbolo is None:
            return
        esperados = simbolo.retornos
        quien = "la función '%s'" % simbolo.nombre
        if not esperados:
            if vals:
                self._registrar('S4', n.linea,
                                "%s no devuelve ningún valor, pero retorna %d. "
                                "Sugerencia: quita el valor del return o "
                                "declara el tipo de retorno en la firma."
                                % (quien, len(vals)))
            return
        exprs = n.hijos[0]
        if None in vals and len(exprs) == 1 and len(esperados) != 1:
            return                                     # llamada ya reportada
        if len(vals) != len(esperados):
            if not vals:
                self._registrar('S4', n.linea,
                                "%s debe retornar %s, pero el return no lleva "
                                "ningún valor. Sugerencia: devuelve %s."
                                % (quien, self._descripcion_retornos(esperados),
                                   _lista_tipos(esperados)))
            else:
                self._registrar('S4', n.linea,
                                "%s debe retornar %s, pero retorna %s. "
                                "Sugerencia: devuelve exactamente %s."
                                % (quien, self._descripcion_retornos(esperados),
                                   _plural(len(vals), 'valor', 'valores'),
                                   _lista_tipos(esperados)))
            return
        for i, (esperado, v) in enumerate(zip(esperados, vals)):
            if v is None or isinstance(v, tuple):
                continue
            if not compatible(esperado, v):
                posicion = ('' if len(esperados) == 1
                            else ' en la posición %d' % (i + 1))
                self._registrar('S4', n.linea,
                                "%s debe retornar %s%s, pero retorna %s. "
                                "Sugerencia: devuelve %s."
                                % (quien, esperado, posicion, v,
                                   _RETORNO_SUGERIDO.get(
                                       esperado, 'un valor de tipo %s' % esperado)))

    def s4_fin_funcion(self, f, simbolo, sentencias):
        """Una función con tipo de retorno debe terminar en un return."""
        if simbolo.retornos and not self._termina(sentencias):
            self._registrar('S4', f.linea,
                            "la función '%s' debe terminar con un return de %s. "
                            "Sugerencia: agrega return al final de la función."
                            % (simbolo.nombre, _lista_tipos(simbolo.retornos)))

    def _termina(self, sentencias):
        return bool(sentencias) and self._sentencia_termina(sentencias[-1])

    def _sentencia_termina(self, s):
        """¿La sentencia siempre termina en un return? (regla de Go simplificada)"""
        if s.tipo == 'return':
            return True
        if s.tipo == 'bloque':
            return self._termina(s.hijos[0])
        if s.tipo == 'if':
            _, bloque, otro = s.hijos
            if otro is None or not self._termina(bloque.hijos[0]):
                return False
            return self._sentencia_termina(otro)
        if s.tipo == 'switch':
            casos = s.hijos[1]
            if not any(c.tipo == 'default' for c in casos):
                return False
            for c in casos:
                sents = c.hijos[1] if c.tipo == 'case' else c.hijos[0]
                if not self._termina(sents) or self._tiene_break(sents):
                    return False
            return True
        return False

    def _tiene_break(self, sentencias):
        for s in sentencias:
            if s.tipo == 'break':
                return True
            if s.tipo == 'bloque' and self._tiene_break(s.hijos[0]):
                return True
            if s.tipo == 'if':
                _, bloque, otro = s.hijos
                if self._tiene_break(bloque.hijos[0]):
                    return True
                if otro is not None and self._tiene_break([otro]):
                    return True
        return False
# FIN aporte: César Balladares


# ===========================================================================
# FÁTIMA TORRES (infraestructura): recorrido del AST
# ===========================================================================
# INICIO aporte: Fátima Torres (recorrido)
class AnalizadorSemantico(_ReglasFatima, _ReglasElkin, _ReglasCesar):
    """Recorre el AST con una tabla de símbolos por ámbitos y aplica S1-S6."""

    def __init__(self):
        self._reiniciar()

    def _reiniciar(self):
        self.tabla = TablaSimbolos()
        self.errores = []
        self._vistos = set()
        self._funciones = {}
        self.funcion = None
        self._iniciar_elkin()
        self._iniciar_cesar()

    @property
    def simbolos(self):
        """Todos los símbolos declarados (para el log)."""
        return list(self.tabla.historial)

    def analizar(self, arbol):
        """Devuelve la lista de errores semánticos (ordenada por línea)."""
        self._reiniciar()
        if arbol is None:
            return []
        declaraciones = arbol.hijos[2]
        self.tabla.entrar('global')
        funciones = [d for d in declaraciones if d.tipo == 'func']
        for f in funciones:                    # las funciones se pueden llamar
            self._declarar_funcion(f)          # antes de su definición
        for d in declaraciones:
            if d.tipo in ('var', 'const'):
                self._sentencia(d)
        for f in funciones:
            self._funcion(f)
        self.tabla.salir()
        self.errores.sort(key=lambda e: e['linea'])
        return list(self.errores)

    # --- funciones --------------------------------------------------------
    def _declarar_funcion(self, f):
        nombre, params, retornos, _ = f.hijos
        simbolo = Simbolo(nombre, 'func', False, 'global', f.linea,
                          es_funcion=True,
                          params=[(p.hijos[0], p.hijos[1]) for p in params],
                          retornos=list(retornos))
        if not self.s1_redeclarada(nombre, f.linea):
            self.tabla.declarar(simbolo)
        self._funciones[id(f)] = simbolo

    def _funcion(self, f):
        nombre, params, _, cuerpo = f.hijos
        simbolo = self._funciones[id(f)]
        self.funcion = simbolo
        self.tabla.entrar('función %s' % nombre)
        for p in params:
            if not self.s1_redeclarada(p.hijos[0], p.linea):
                self.tabla.declarar(Simbolo(p.hijos[0], p.hijos[1], False,
                                            self.tabla.etiqueta, p.linea))
        self.s6_reiniciar()
        sentencias = cuerpo.hijos[0]
        for s in sentencias:
            self._sentencia(s)
        self.s4_fin_funcion(f, simbolo, sentencias)
        self.tabla.salir()
        self.funcion = None

    def _bloque(self, b, etiqueta=None):
        self.tabla.entrar(etiqueta or 'bloque (línea %d)' % b.linea)
        for s in b.hijos[0]:
            self._sentencia(s)
        self.tabla.salir()

    # --- sentencias -------------------------------------------------------
    def _sentencia(self, s):
        if s is None:
            return
        t = s.tipo
        if t == 'var':
            self._var(s)
        elif t == 'const':
            tv = self._expr(s.hijos[1])
            if not self.s1_redeclarada(s.hijos[0], s.linea):
                self.tabla.declarar(Simbolo(s.hijos[0],
                                            tv if isinstance(tv, str) else None,
                                            True, self.tabla.etiqueta, s.linea))
        elif t == 'declare':
            self._declare(s)
        elif t == 'asignacion':
            op, lv, expr = s.hijos
            tl, simbolo, destino = self._lvalue(lv)
            self.s2_modificar(simbolo, s.linea)
            tr = self._expr(expr)
            if simbolo is not None and simbolo.es_const:
                pass                       # ya es error S2: no se encadenan más
            elif op == '=':
                self.s3_asignar(s.linea, destino, tl, tr)
            else:
                self.s5_compuesta(s, tl, tr)
        elif t == 'incdec':
            tl, simbolo, _ = self._lvalue(s.hijos[1])
            self.s2_modificar(simbolo, s.linea)
            if simbolo is None or not simbolo.es_const:
                self.s5_incdec(s, tl)
        elif t == 'llamada':
            self._expr(s)
        elif t == 'impresion':
            for e in s.hijos[0]:
                self._expr(e)
        elif t == 'lectura':
            simbolo = self._resolver_id(s.hijos[0], s.linea)
            self.s2_modificar(simbolo, s.linea)
        elif t == 'if':
            self._if(s)
        elif t == 'for_condicion':
            self._expr(s.hijos[0])
            self.s6_entrar_bucle()
            self._bloque(s.hijos[1])
            self.s6_salir_bucle()
        elif t == 'for_clasico':
            inicio, cond, paso, cuerpo = s.hijos
            self.tabla.entrar('for (línea %d)' % s.linea)
            self._sentencia(inicio)
            self._expr(cond)
            self._sentencia(paso)
            self.s6_entrar_bucle()
            self._bloque(cuerpo)
            self.s6_salir_bucle()
            self.tabla.salir()
        elif t == 'switch':
            self._switch(s)
        elif t == 'return':
            self._return(s)
        elif t == 'break':
            self.s6_break(s)
        elif t == 'continue':
            self.s6_continue(s)
        elif t == 'bloque':
            self._bloque(s)

    def _var(self, s):
        nombre, tipo, valor = s.hijos
        if valor is not None:
            tv = self._expr(valor)
            self.s3_asignar(s.linea, "'%s' de tipo %s" % (nombre, tipo), tipo, tv)
        if not self.s1_redeclarada(nombre, s.linea):
            self.tabla.declarar(Simbolo(nombre, tipo, False,
                                        self.tabla.etiqueta, s.linea))

    def _declare(self, s):
        nombres, exprs = s.hijos
        tipos = [self._expr(e) for e in exprs]
        vals = self._expandir(exprs, tipos)
        self.s3_declare(s, nombres, exprs, vals)
        self.s1_sin_nuevas(nombres, s.linea)
        for i, nombre in enumerate(nombres):
            if nombre == '_':
                continue
            tval = None
            if len(vals) == len(nombres) and not isinstance(vals[i], tuple):
                tval = vals[i]
            local = self.tabla.buscar_local(nombre)
            if local is not None:          # ya existía en este ámbito
                self.s2_modificar(local, s.linea)
                if not local.es_const:
                    self.s3_asignar(s.linea,
                                    "'%s' de tipo %s" % (nombre, local.tipo),
                                    local.tipo, tval)
            else:
                self.tabla.declarar(Simbolo(nombre, con_tipo(tval), False,
                                            self.tabla.etiqueta, s.linea))

    def _if(self, s):
        cond, bloque, otro = s.hijos
        self._expr(cond)
        self._bloque(bloque)
        if otro is not None:
            if otro.tipo == 'if':
                self._if(otro)
            else:
                self._bloque(otro)

    def _switch(self, s):
        expr, casos = s.hijos
        tswitch = self._expr(expr)
        self.s6_entrar_switch()
        for c in casos:
            if c.tipo == 'case':
                valores, sentencias = c.hijos
                for v in valores:
                    self.s5_case(c, tswitch, self._expr(v))
            else:
                sentencias = c.hijos[0]
            self.tabla.entrar('%s (línea %d)' % (c.tipo, c.linea))
            for st in sentencias:
                self._sentencia(st)
            self.tabla.salir()
        self.s6_salir_switch()

    def _return(self, s):
        exprs = s.hijos[0]
        tipos = [self._expr(e) for e in exprs]
        self.s4_return(s, self.funcion, self._expandir(exprs, tipos))

    @staticmethod
    def _expandir(exprs, tipos):
        """Una sola llamada que devuelve varios valores cuenta como varios."""
        if len(exprs) == 1 and exprs[0].tipo == 'llamada' \
                and isinstance(tipos[0], tuple):
            return list(tipos[0])
        return list(tipos)

    def _lvalue(self, lv):
        """Destino de una asignación: (tipo, símbolo, descripción)."""
        if lv.tipo == 'id':
            nombre = lv.hijos[0]
            simbolo = self._resolver_id(nombre, lv.linea)
            if simbolo is None or simbolo.es_funcion:
                return None, None, "'%s'" % nombre
            return simbolo.tipo, simbolo, "'%s' de tipo %s" % (nombre, simbolo.tipo)
        tipo = self._expr(lv)                      # lv es un acceso por índice
        simbolo = self.tabla.buscar(lv.hijos[0])
        return tipo, simbolo, "un elemento de '%s' de tipo %s" % (lv.hijos[0], tipo)

    # --- expresiones: devuelven el tipo -------------------------------------
    def _expr(self, n):
        if n is None:
            return None
        t = n.tipo
        if t == 'literal':
            return _TIPO_LITERAL.get(n.hijos[0])
        if t == 'id':
            simbolo = self._resolver_id(n.hijos[0], n.linea)
            if simbolo is None or simbolo.es_funcion:
                return None
            return simbolo.tipo
        if t == 'indice':
            simbolo = self._resolver_id(n.hijos[0], n.linea)
            tindice = self._expr(n.hijos[1])
            tbase = simbolo.tipo if simbolo is not None else None
            return self.s5_indice(n, tbase, tindice)
        if t == 'llamada':
            simbolo = self._resolver_funcion(n.hijos[0], n.linea)
            args = n.hijos[1]
            tipos = [self._expr(a) for a in args]
            self.s3_argumentos(n, simbolo, self._expandir(args, tipos))
            if simbolo is None:
                return None
            if len(simbolo.retornos) == 1:
                return simbolo.retornos[0]
            return tuple(simbolo.retornos)
        if t == 'arreglo':
            tam, tipo_elem, exprs = n.hijos
            tipos = [self._expr(e) for e in exprs]
            self.s3_elementos(n, tipo_elem, exprs, tipos)
            return '[%d]%s' % (tam, tipo_elem)
        if t == 'slice':
            tipo_elem, exprs = n.hijos
            tipos = [self._expr(e) for e in exprs]
            self.s3_elementos(n, tipo_elem, exprs, tipos)
            return '[]%s' % tipo_elem
        if t == 'mapa':
            tclave, tvalor, pares = n.hijos
            tipos = [(self._expr(p.hijos[0]), self._expr(p.hijos[1]))
                     for p in pares]
            self.s3_pares(n, tclave, tvalor, pares, tipos)
            return 'map[%s]%s' % (tclave, tvalor)
        if t in ('aritmetica', 'comparacion', 'logica'):
            op, izq, der = n.hijos
            return self.s5_binaria(n, op, self._expr(izq), self._expr(der))
        if t == 'not':
            return self.s5_not(n, self._expr(n.hijos[0]))
        if t == 'menos_unario':
            return self.s5_menos(n, self._expr(n.hijos[0]))
        return None
# FIN aporte: Fátima Torres (recorrido)
