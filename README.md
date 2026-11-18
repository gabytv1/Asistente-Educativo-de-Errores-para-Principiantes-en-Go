# Asistente Educativo de Errores para Principiantes en Go

Proyecto de Lenguajes de Programación – PAO II 2026.
Asistente para principiantes que analiza un subconjunto de Go (análisis léxico, sintáctico y semántico) con PLY y una interfaz en Python.

**Avance 1:** analizador léxico con `ply.lex`.  
**Avance 2:** analizador sintáctico con `ply.yacc` (gramática LALR sin conflictos y AST).  
**Avance 3:** analizador semántico (tabla de símbolos por ámbitos y seis reglas, S1 a S6).  
**Entrega final:** interfaz gráfica (`gui.py`) que ejecuta los tres análisis y muestra los errores con su línea.

| Integrante | Usuario Git |
|---|---|
| Fátima Torres | gabytv1 |
| César Balladares | CBalla-05 |
| Elkin Salazar | sElkinEspol |

## Estructura

```
lexico.py                  analizador léxico (ply.lex), organizado por tipo de token
sintactico.py              analizador sintáctico (ply.yacc): gramática, AST y errores Y1 a Y6
semantico.py               analizador semántico: tabla de símbolos y reglas S1 a S6
main.py                    análisis léxico de un archivo .go y generación del log
main_sintactico.py         análisis sintáctico y generación del log
main_semantico.py          análisis completo (léxico + sintáctico + semántico) y log semántico
gui.py                     interfaz gráfica (CustomTkinter): editor, resultados y consola
logica_gui.py              lógica de la interfaz, sin Tkinter (se prueba por separado)
resaltado.py               colores de sintaxis del editor (sin Tkinter, se prueba por separado)
verificar_algoritmos.py    revisa los algoritmos: cobertura de tokens y compilación con Go
algoritmos/                algoritmo1.go, algoritmo2.go, algoritmo3.go (uno por integrante)
errores/                   archivos con errores a propósito: error_*.go (L1-L7),
                           sintactico_*.go (Y1-Y6) y semantico_*.go (S1-S6)
logs/                      lexico-..., sintactico-... y semantico-usuarioGit-DDMMAAAA-HHhMM.txt
tests/                     pruebas unittest de los tres analizadores, la interfaz y el resaltado
```

## Uso

**Requisitos:** Python 3.10 o superior y las librerías de `requirements.txt`
(`ply` y `customtkinter`). Tkinter viene con Python en Windows y macOS; en Linux
hay que instalarlo aparte (`sudo apt install python3-tk`).

```bash
pip install -r requirements.txt
python gui.py                                                      # interfaz gráfica
python main.py algoritmos/algoritmo1.go "Nombre Apellido"          # léxico
python main_sintactico.py algoritmos/algoritmo1.go gabytv1         # sintáctico
python main_semantico.py algoritmos/algoritmo1.go gabytv1          # semántico
python main_semantico.py algoritmos/algoritmo1.go gabytv1 --simbolos   # y muestra la tabla de símbolos
python -m unittest discover -s tests -v
```

El análisis semántico solo se ejecuta si el archivo no tiene errores léxicos ni
sintácticos; si los tiene, el log los lista y pide corregirlos primero.

Las pruebas de la ventana (`tests/test_gui.py`) se omiten solas si el equipo no tiene
pantalla o Tkinter; las demás se ejecutan siempre.

## Reparto del Avance 1

| | Fátima Torres | César Balladares | Elkin Salazar |
|---|---|---|---|
| **Tokens** | Palabras reservadas (excepto `map`), `fmt`, `Println` y `Scanln`, delimitadores, NEWLINE, comentarios, errores L4 y L7 | ID (admite tildes y ñ), INTEGER_VALUE, FLOAT_VALUE, STRING_VALUE (admite escapes), TRUE, FALSE, tipos, errores L1, L2, L3 y L6 | Operadores, `map`, error L5 |
| **Infraestructura** | Repositorio y README; utilidades compartidas y clase del analizador (regla de NEWLINE) | `main.py`: generación de logs con el nombre y formato pedidos | Prueba integral con el programa de la propuesta (69 tokens) y verificación de los algoritmos con `go build` |
| **unittest** | Pruebas de sus tokens | Pruebas de sus tokens | Pruebas de sus tokens |
| **Algoritmo y errores** | `algoritmo1.go`, `error_fatima.go` | `algoritmo2.go`, `error_cesar.go` | `algoritmo3.go`, `error_elkin.go` |
| **Log propio** | Sí | Sí | Sí |

### Checklist del Avance 1

- [x] Fátima: tokens, clase del analizador, tests, algoritmo1.go, error_fatima.go
- [x] César: tokens, main.py, tests, algoritmo2.go, error_cesar.go
- [x] Elkin: tokens, tests, prueba integral, algoritmo3.go, error_elkin.go
- [x] Logs de los tres en `logs/`
- [x] Documento actualizado (secciones 8 y 9) con el link del repositorio

## Correcciones tras la revisión del docente

- `fmt`, `Println` y `Scanln` ahora son tokens propios (`FMT`, `PRINTLN`, `SCANLN`); antes se reconocían como `ID`. Otras funciones (`Printf`, etc.) siguen siendo `ID` porque la propuesta solo admite estas dos.
- Nuevo error **L6**: comillas simples (`'hola'`). Se reporta un solo error con sugerencia de usar comillas dobles, sin errores en cascada. Un apóstrofe dentro de una cadena o de un comentario no es error.
- Las cadenas admiten secuencias de escape (`\"`, `\n`, `\t`, `\\`): `"dijo \"hola\""` es una sola cadena.
- Los identificadores admiten letras con tilde y la ñ (`año`, `número`).
- 48 pruebas unittest; los tres algoritmos cubren los 60 tipos de token y compilan con `go build`.
- Nuevo error **L7**: las 10 palabras reservadas de Go que están fuera del subconjunto (`range`, `type`, `struct`, `interface`, `chan`, `select`, `go`, `defer`, `goto`, `fallthrough`) se reportan con una sugerencia en lugar de pasar como `ID`.

## Avance 2: analizador sintáctico

Reglas mínimas: impresión, ingreso por teclado, expresiones aritméticas y booleanas, asignación y declaración de variables, estructuras de datos, estructuras de control y definición de funciones. Cada integrante tiene al menos una estructura de datos, una de control y un tipo de función. Su código está entre los comentarios `INICIO aporte` / `FIN aporte` de `sintactico.py`.

| | Fátima Torres (gabytv1) | César Balladares (CBalla-05) | Elkin Salazar (sElkinEspol) |
|---|---|---|---|
| **Declaraciones y asignación** | `var` (con tipo, con tipo y valor) | `:=` simple y múltiple; `=`, `+=`, `-=`, `++`, `--` | `const` |
| **Expresiones** | Booleanas (`\|\|`, `&&`, comparaciones, `!`) | Aritméticas con precedencia, `-` unario, paréntesis | Impresión `fmt.Println` y lectura `fmt.Scanln` |
| **Estructuras de control** | `if`, `if-else`, `else if` | `for` con condición y `for` clásico | `switch` con `case`/`default`, `break`, `continue` |
| **Estructuras de datos** | Arreglo (declaración, literal, acceso por índice) | Slice | Mapa (declaración, literal, acceso por clave) |
| **Funciones** | Un valor de retorno | Dos valores de retorno y llamada | Sin retorno; estructura del programa (`package`, `import`, funciones) |
| **Errores** | Y1 (falta `{`), Y5 (`else` mal ubicado) | Y2 (paréntesis sin cerrar), Y4 (declaración incompleta) | Y3 (llave sin cerrar), Y6 (token inesperado) |
| **Infraestructura** | Nodo del AST, reglas compartidas, `p_error` y recuperación | Pruebas de sus reglas (`PruebasCesar`) | `main_sintactico.py` y pruebas de integración (`PruebasIntegral`) |
| **Algoritmo y errores** | `algoritmo1.go`, `sintactico_fatima.go` | `algoritmo2.go`, `sintactico_cesar.go` | `algoritmo3.go`, `sintactico_elkin.go` |
| **Log propio** | Sí | Sí | Sí |

Notas de diseño:

- La gramática es LALR y no tiene conflictos shift/reduce ni reduce/reduce.
- El parser recibe los tokens del léxico (con la regla de NEWLINE del Avance 1) y construye un AST con objetos `Nodo`, listo para el analizador semántico.
- Si hay errores, intenta recuperarse (insertando el `{`, el `)` o el tipo que faltan, o descartando la línea) para informar varios errores en una misma ejecución sin generar cascadas; informa un error por línea como máximo.
- Las funciones `error_yN` de `sintactico.py` son los manejadores de cada error; `p_error` las prueba en orden.
- Además de la propuesta, se acepta `else if` y las sentencias separadas por `;` en una misma línea.
- Los errores léxicos se informan aparte: conviene corregirlos primero, porque pueden provocar errores sintácticos.
- Las pruebas del léxico y del sintáctico son 108 en total (48 y 60); con las del semántico (105), la interfaz (27) y el resaltado (6), el conjunto completo es de 246 (`python -m unittest discover -s tests -v`).
- Los mensajes se adaptan al contexto del error. Por ejemplo, Y1 nombra la construcción afectada (condición del `if`, `for` o `switch`, o la firma de la función) y Y6 tiene mensajes propios para un `for` con paréntesis alrededor de sus tres partes, `:=` o `=` dentro de la condición de un `if`, un `if` sin condición o con la condición incompleta, un `case` sin `:`, `fmt.Printf` u otra función de `fmt` no admitida, `fmt.Scanln(x)` sin `&`, un `)` o `}` sobrante y una sentencia fuera de una función. Y2 cubre también el paréntesis sin cerrar de un `for`; Y3, una función que empieza sin cerrar la anterior; Y4, `const N =` y `var x int =` sin valor; Y5, un `else` sin `if`.

### Checklist del Avance 2

- [x] Fátima: reglas de `var`, booleanas, `if`/`else if`, arreglo y función con un retorno; Y1 y Y5; nodo del AST y recuperación de errores
- [x] César: reglas de `:=`, asignación, aritmética, `for`, slice y función con dos retornos; Y2 y Y4; `PruebasCesar`
- [x] Elkin: estructura del programa, `const`, `switch`, mapa, impresión y lectura; Y3 y Y6; `main_sintactico.py` y `PruebasIntegral`
- [x] Logs sintácticos de los tres en `logs/` (`sintactico-usuarioGit-DDMMAAAA-HHhMM.txt`)
- [x] Documento actualizado (sección 8, resultados y sección 9) con el link del repositorio

## Avance 3: analizador semántico

`semantico.py` recorre el AST con una tabla de símbolos organizada por ámbitos (global,
función y bloque). Cada símbolo guarda nombre, tipo, si es constante, ámbito y línea de
declaración. Los errores se informan con categoría, línea, mensaje y sugerencia, y el análisis
continúa para mostrar varios errores en una ejecución. Cada aporte está delimitado con
`INICIO aporte` / `FIN aporte`.

| Cód. | Categoría | Regla | Responsable |
|---|---|---|---|
| S1 | Identificadores | Toda variable o función se declara antes de usarse, en el ámbito actual o en uno que lo contenga, y una sola vez en cada ámbito (`var`, `const`, `func`, parámetros y `:=` sin variables nuevas) | Fátima Torres |
| S2 | Constantes | Una constante declarada con `const` no puede reasignarse ni modificarse (`=`, `+=`, `-=`, `++`, `--`, `&` en `Scanln`) | Fátima Torres |
| S3 | Asignación de tipo | El tipo del valor asignado coincide con el de la variable (declarado o deducido con `:=`; un literal entero o una constante sin tipo puede asignarse a `float64`); incluye argumentos de llamadas (y su cantidad), elementos de arreglos, slices y mapas, y la cantidad de nombres y valores de `:=` | César Balladares |
| S4 | Retorno de funciones | El tipo y la cantidad de valores de `return` coinciden con la firma; una función con retorno debe terminar en `return` | César Balladares |
| S5 | Operaciones permitidas | Aritméticos solo entre números del mismo tipo (`+` también entre cadenas), `%` solo con enteros, `&&` `\|\|` `!` solo con `bool`, comparaciones entre el mismo tipo, índices y claves del tipo correcto, división entre cero literal con enteros | Elkin Salazar |
| S6 | Estructuras de control | `break` y `continue` solo dentro de un `for` (y `break` también dentro de un `switch`) | Elkin Salazar |

Constantes sin tipo, como en Go: un literal entero (`5`) o una constante `const N = 10` se adapta a `float64` (`var x float64 = 5`, `x * 2` y `x > 1` son válidos), pero una variable tiene un tipo fijo: mezclar una variable `int` con una `float64`, o asignar una a la otra, es error. El subconjunto no tiene conversiones (`float64(n)`), por eso la sugerencia es usar el mismo tipo en ambas variables.

| | Fátima Torres | César Balladares | Elkin Salazar |
|---|---|---|---|
| **Reglas** | S1 y S2; tabla de símbolos y recorrido del AST | S3 y S4 | S5 y S6; tipo de cada expresión |
| **Infraestructura** | `Simbolo`, `TablaSimbolos`, `AnalizadorSemantico` | `main_semantico.py` (log `semantico-usuarioGit-fecha-hora.txt`) | prueba integral y verificación de los algoritmos |
| **Archivo de errores** | `errores/semantico_fatima.go` (S2, S1) | `errores/semantico_cesar.go` (S4, S3) | `errores/semantico_elkin.go` (S5, S6) |
| **unittest** | `PruebasFatima` | `PruebasCesar`, `PruebasLogSemantico` | `PruebasElkin`, `PruebasIntegral` |

### Checklist del Avance 3

- [x] Fátima: tabla de símbolos, recorrido, S1 y S2, `semantico_fatima.go`, tests, log propio
- [x] Elkin: S5 y S6, `semantico_elkin.go`, tests, pruebas integrales, log propio
- [x] César: S3 y S4, `main_semantico.py`, `semantico_cesar.go`, tests, log propio
- [x] Logs semánticos de los tres en `logs/`
- [x] Documento actualizado

## Entrega final: interfaz gráfica

```bash
python gui.py
```

La ventana sigue el diseño de la propuesta (Figuras 1 y 2):

1. **Barra de herramientas:** *Abrir archivo*, *Guardar*, *Análisis léxico*, *Análisis sintáctico*,
   *Análisis semántico*, *Limpiar* y el selector de **desarrollador** (Fátima Torres, César Balladares o
   Elkin Salazar).
2. **Editor** (izquierda) con numeración de líneas y colores de sintaxis al estilo de VS Code (palabras reservadas, tipos, funciones, cadenas, números y comentarios; los colores están en `resaltado.py`). Las líneas con error se pintan en rojo.
3. **Resultados** (derecha): tabla de tokens (línea, columna, tipo, lexema) para el léxico, tabla de
   errores (línea, código, tipo, mensaje) para el sintáctico y el semántico, y la pestaña
   *Tabla de símbolos*. Con un clic en un error, el editor salta a su línea.
4. **Consola de resultados:** ✔ ÉXITO o ✘ ERRORES, con línea, mensaje y sugerencia de cada error
   (también se puede hacer clic en ellos).
5. **Barra de estado:** nombre del log generado, estado del análisis, archivo y desarrollador.

Cómo se comporta:

- Se analiza **el texto del editor**, esté o no guardado. Si se edita después de analizar, las marcas
  rojas se quitan y el estado pide volver a analizar.
- **Cada análisis genera su log** en `logs/` con el mismo formato que los ejecutables de consola. El
  léxico usa el nombre del desarrollador (`lexico-NombreApellido-DD-MM-AAAA-HHhMM.txt`) y el sintáctico y
  el semántico su usuario Git (`sintactico-` y `semantico-usuarioGit-DDMMAAAA-HHhMM.txt`). Dos análisis del
  mismo tipo y del mismo desarrollador en el mismo minuto escriben el mismo archivo.
- El análisis sintáctico muestra también los errores léxicos del código. El **semántico encadena los tres
  análisis**: si hay errores léxicos o sintácticos, los muestra y avisa que el semántico no se ejecutó.
- Si el semántico no tiene errores, se abre la pestaña *Tabla de símbolos*.

Archivos para la sustentación: `algoritmos/algoritmo1.go` (Fátima), `algoritmo2.go` (César) y
`algoritmo3.go` (Elkin); para mostrar errores, los archivos de `errores/`.

### Checklist de la entrega final

- [x] `gui.py` y `logica_gui.py`; `requirements.txt` con `ply` y `customtkinter`
- [x] Errores de los tres análisis con su número de línea en la tabla, la consola y el editor
- [x] Pruebas: `tests/test_gui_logica.py` (lógica), `tests/test_gui.py` (ventana) y `tests/test_resaltado.py` (colores)
- [x] Colores de sintaxis en el editor (`resaltado.py`)
- [x] Al menos un log de cada análisis por integrante en `logs/`
- [x] Informe final
