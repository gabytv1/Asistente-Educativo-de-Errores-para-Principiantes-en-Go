# Asistente Educativo de Errores para Principiantes en Go

Proyecto de Lenguajes de Programación – PAO II 2026.
Asistente para principiantes que analiza un subconjunto de Go (análisis léxico, sintáctico y semántico) con PLY y una interfaz en Python.

**Avance 1:** analizador léxico con `ply.lex`.  
**Avance 2:** analizador sintáctico con `ply.yacc`.

| Integrante | Usuario Git |
|---|---|
| Fátima Torres | gabytv1 |
| César Balladares | CBalla-05 |
| Elkin Salazar | sElkinEspol |

## Estructura

```
lexico.py                  analizador léxico (ply.lex), organizado por tipo de token
main.py                    ejecuta el análisis léxico sobre un archivo .go y genera el log
sintactico.py              analizador sintáctico (ply.yacc): gramática, AST y errores Y1 a Y6
main_sintactico.py         ejecuta el análisis sintáctico y genera el log
verificar_algoritmos.py    revisa los algoritmos: cobertura de tokens y compilación con Go
algoritmos/                algoritmo1.go, algoritmo2.go, algoritmo3.go (uno por integrante)
errores/                   errores léxicos a propósito (error_*.go) y sintácticos (sintactico_*.go)
logs/                      lexico-NombreApellido-DD-MM-AAAA-HHhMM.txt y sintactico-usuarioGit-DDMMAAAA-HHhMM.txt
tests/                     pruebas unittest (tokens, parser, logs y pruebas integrales)
```

## Uso

```bash
pip install -r requirements.txt
python main.py algoritmos/algoritmo1.go "Nombre Apellido"            # léxico
python main_sintactico.py algoritmos/algoritmo1.go usuarioGit          # sintáctico
python -m unittest discover -s tests -v
```

## Reparto del Avance 1

| | Fátima Torres | César Balladares | Elkin Salazar |
|---|---|---|---|
| **Tokens** | Palabras reservadas (excepto `map`), `fmt`, `Println` y `Scanln`, delimitadores, NEWLINE, comentarios, errores L4 y L7 | ID (admite tildes y ñ), INTEGER_VALUE, FLOAT_VALUE, STRING_VALUE (admite escapes), TRUE, FALSE, tipos, errores L1, L2, L3 y L6 | Operadores, `map`, error L5 |
| **Infraestructura** | Repositorio y README; utilidades compartidas y clase del analizador (regla de NEWLINE) | `main.py`: generación de logs con el nombre y formato pedidos | Prueba integral con el programa de la propuesta (69 tokens) y verificación de los algoritmos con `go build` |
| **unittest** | Pruebas de sus tokens | Pruebas de sus tokens | Pruebas de sus tokens |
| **Algoritmo y errores** | `algoritmo1.go`, `error_fatima.go` | `algoritmo2.go`, `error_cesar.go` | `algoritmo3.go`, `error_elkin.go` |
| **Log propio** | Sí | Sí | Sí |

## Checklist del Avance 1

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
| **Estructuras de control** | `if`, `if-else` | `for` con condición y `for` clásico | `switch` con `case`/`default`, `break`, `continue` |
| **Estructuras de datos** | Arreglo (declaración, literal, acceso por índice) | Slice | Mapa (declaración, literal, acceso por clave) |
| **Funciones** | Un valor de retorno | Dos valores de retorno y llamada | Sin retorno; estructura del programa (`package`, `import`, funciones) |
| **Errores** | Y1 (falta `{`), Y5 (`else` mal ubicado) | Y2 (paréntesis sin cerrar), Y4 (declaración incompleta) | Y3 (llave sin cerrar), Y6 (token inesperado) |
| **Infraestructura** | Nodo del AST, reglas compartidas, `p_error` y recuperación | Pruebas de sus reglas (`PruebasCesar`) | `main_sintactico.py` y pruebas de integración (`PruebasIntegral`) |
| **Algoritmo y errores** | `algoritmo1.go`, `sintactico_fatima.go` | `algoritmo2.go`, `sintactico_cesar.go` | `algoritmo3.go`, `sintactico_elkin.go` |
| **Log propio** | Sí | Sí | Sí |

Notas de diseño:

- El parser recibe los tokens del léxico (con la regla de NEWLINE del Avance 1) y construye un AST con objetos `Nodo`, listo para el analizador semántico.
- Si hay errores, intenta recuperarse (insertando el `{`, el `)` o el tipo que faltan, o descartando la línea) para informar varios errores en una misma ejecución sin generar cascadas.
- Las funciones `error_yN` de `sintactico.py` son los manejadores de cada error; `p_error` las prueba en orden.
- Además de la propuesta, se acepta `else if` y las sentencias separadas por `;` en una misma línea.
- Los errores léxicos se informan aparte: conviene corregirlos primero, porque pueden provocar errores sintácticos.
- `python -m unittest discover -s tests -v` ejecuta las pruebas del léxico y del sintáctico (96 en total).

## Checklist del Avance 2

- [x] Fátima: reglas de `var`, booleanas, `if`/`else if`, arreglo y función con un retorno; Y1 y Y5; nodo del AST y recuperación de errores
- [x] César: reglas de `:=`, asignación, aritmética, `for`, slice y función con dos retornos; Y2 y Y4; `PruebasCesar`
- [x] Elkin: estructura del programa, `const`, `switch`, mapa, impresión y lectura; Y3 y Y6; `main_sintactico.py` y `PruebasIntegral`
- [x] Logs sintácticos de los tres en `logs/` (`sintactico-usuarioGit-DDMMAAAA-HHhMM.txt`)
- [x] Documento actualizado (sección 8, resultados y sección 9) con el link del repositorio
