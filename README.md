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
lexico.py            analizador léxico (ply.lex), organizado por tipo de token
main.py              ejecuta el análisis sobre un archivo .go y genera el log
algoritmos/          algoritmo1.go, algoritmo2.go, algoritmo3.go (uno por integrante)
errores/             archivos con errores léxicos a propósito (L1 a L5)
logs/                logs lexico-NombreApellido-DD-MM-AAAA-HHhMM.txt
tests/               pruebas unittest
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
| **Tokens** | Palabras reservadas (excepto `map`), delimitadores, NEWLINE, comentarios, error L4 | ID, INTEGER_VALUE, FLOAT_VALUE, STRING_VALUE, TRUE, FALSE, tipos, errores L1, L2, L3 | Operadores, `map`, error L5 |
| **Infraestructura** | Repositorio y README; utilidades compartidas y clase del analizador (regla de NEWLINE) | `main.py`: generación de logs con el nombre y formato pedidos | Prueba integral con el programa de la propuesta (69 tokens) y verificación de los algoritmos con `go build` |
| **unittest** | Pruebas de sus tokens | Pruebas de sus tokens | Pruebas de sus tokens |
| **Algoritmo y errores** | `algoritmo1.go`, `error_fatima.go` | `algoritmo2.go`, `error_cesar.go` | `algoritmo3.go`, `error_elkin.go` |
| **Documento** | Sección 8: Casos de Prueba y link del repositorio | Sección 8: Resultados (logs y errores) | Sección 9: Uso de IA; corregir el nombre del log en la sección 7 |
| **Log propio** | Sí | Sí | Sí |

