package main

import "fmt"

// Algoritmo 2 - César Balladares
// Factorial, division con dos retornos y estadistica basica de un slice.

/* Combina enteros, flotantes y cadenas.
   Usa funciones con uno y dos valores de retorno. */

const PI = 3.14159
const SALUDO = "Calculadora basica"

var llamadas int = 0
var precision float64 = 0.01
var modo string = "completo"
var verbose bool = false

func factorial(n int) int {
	if n <= 1 {
		return 1
	}
	return n * factorial(n-1)
}

func dividir(a int, b int) (int, int) {
	return a / b, a % b
}

func promedio(valores []float64) float64 {
	var suma float64 = 0.0
	for i := 0; i < 4; i++ {
		suma += valores[i]
	}
	return suma / 4.0
}

func mostrar(texto string) {
	llamadas++
	fmt.Println(texto)
}

func main() {
	mostrar(SALUDO)
	f := factorial(5)
	c, m := dividir(17, 5)
	fmt.Println("Factorial:", f, "Cociente:", c, "Residuo:", m)

	edades := []float64{18.0, 21.5, 25.0, 30.5}
	prom := promedio(edades)
	area := PI * 2.0 * 2.0
	fmt.Println("Promedio:", prom, "Area:", area, modo)

	nombres := []string{"Ana", "Luis", "Maria"}
	var etiqueta string = "Grupo: "
	etiqueta = etiqueta + nombres[0]
	fmt.Println(etiqueta)

	var contador int = 10
	for contador > 0 {
		contador -= 3
		llamadas++
		if contador < 4 && !verbose {
			break
		}
	}

	pares := map[string]int{"pares": 0, "impares": 0}
	for i := 1; i <= 6; i++ {
		if i%2 == 0 {
			pares["pares"]++
			continue
		}
		pares["impares"]++
	}
	fmt.Println(pares["pares"], pares["impares"], llamadas, contador)

	switch c {
	case 3:
		fmt.Println("Cociente tres")
	default:
		fmt.Println("Otro cociente")
	}

	if precision >= 0.001 || verbose == true {
		fmt.Println("Precision aceptable")
	} else {
		fmt.Println("Precision baja")
	}
	var leido int
	if llamadas != 0 {
		fmt.Println("Hubo llamadas:", llamadas)
	}
	fmt.Scanln(&leido)
	leido--
	fmt.Println(leido)
}
