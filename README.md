# Asistente Educativo de Errores para Principiantes en Go

Proyecto de Lenguajes de Programación – PAO II 2026.
Asistente para principiantes que analiza un subconjunto de Go (análisis léxico, sintáctico y semántico) con PLY y una interfaz en Python.

**Avance 1:** analizador léxico con `ply.lex`.

| Integrante | Usuario Git |
|---|---|
| Fátima Torres | gabytv1 |
| César Balladares | CBalla-05 |
| Elkin Salazar | sElkinEspol |

## Estructura

```
lexico.py                  analizador léxico (ply.lex), organizado por tipo de token
main.py                    ejecuta el análisis sobre un archivo .go y genera el log
verificar_algoritmos.py    revisa los algoritmos: cobertura de tokens y compilación con Go
algoritmos/                algoritmo1.go, algoritmo2.go, algoritmo3.go (uno por integrante)
errores/                   archivos con errores léxicos a propósito (L1 a L7)
logs/                      logs lexico-NombreApellido-DD-MM-AAAA-HHhMM.txt
tests/                     pruebas unittest (tokens, log y prueba integral)
```

## Uso

```bash
pip install -r requirements.txt
python main.py algoritmos/algoritmo1.go "Nombre Apellido"
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
