package main

import "fmt"

// Prueba de errores sintácticos - César Balladares (Y2: paréntesis sin cerrar, Y4: declaración incompleta)

func main() {
	var total
	fmt.Println("Hola"
	for i := 0; i < 3; i++ {
		total += i
	}
}
