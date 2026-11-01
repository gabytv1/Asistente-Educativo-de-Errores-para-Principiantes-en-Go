package main

import "fmt"

// Prueba de errores - Elkin Salazar (L5: operador incompleto)

func main() {
	a := true
	b := false
	if a | b {
		fmt.Println("uno de los dos es verdadero")
	}
	if a || b {
		fmt.Println("esta linea si es valida")
	}
}
