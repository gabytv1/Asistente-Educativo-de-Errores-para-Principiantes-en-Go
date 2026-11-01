package main

import "fmt"

// Algoritmo 1 - Fátima Torres
// Clasifica las notas de un estudiante a partir de un arreglo.

/* El programa recorre las notas, calcula el promedio
   y muestra una clasificacion segun el resultado. */

const MINIMO = 60.0
const MATERIA = "Lenguajes de Programacion"

var aprobadas int = 0
var activo bool = true
var ajuste float64

func clasificar(promedio float64) string {
	if promedio >= 90.0 {
		return "Excelente"
	} else {
		if promedio >= MINIMO && !(promedio > 100.0) {
			return "Aprobado"
		}
	}
	return "Reprobado"
}

func main() {
	notas := [5]float64{85.5, 92.0, 70.0, 55.5, 99.0}
	var suma float64 = 0.0
	var contador int
	var intentos int = 3; var mensaje string = "Fin del analisis"

	for i := 0; i < 5; i++ {
		if notas[i] < MINIMO {
			continue
		}
		suma += notas[i]
		contador++
		aprobadas++
	}

	promedio := suma / 5.0
	estado := clasificar(promedio)
	fmt.Println(MATERIA, estado, aprobadas, contador)

	nivel := 2
	switch nivel {
	case 1:
		fmt.Println("Nivel basico")
	case 2:
		fmt.Println("Nivel intermedio")
	default:
		fmt.Println("Nivel avanzado")
	}

	pesos := map[string]int{"parcial": 40, "final": 60}
	if activo != false || pesos["final"] == 60 {
		fmt.Println("Pesos validos")
	} else {
		fmt.Println("Revisar pesos")
	}

	for intentos > 0 {
		intentos -= 1
		if intentos == 1 {
			break
		}
	}
	for contador > 1 {
		contador--
	}
	ajuste = promedio - 2.5 * 1.0 + 0.5
	resto := aprobadas % 2
	if resto <= 1 && ajuste > 0.0 {
		fmt.Println(mensaje, resto, ajuste, intentos)
	}
	var libre int
	fmt.Scanln(&libre)
	fmt.Println(libre, intentos)
}
