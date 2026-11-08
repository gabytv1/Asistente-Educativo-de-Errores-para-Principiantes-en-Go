package main

import "fmt"

// Prueba de errores sintácticos - Fátima Torres (Y1: falta '{', Y5: else mal ubicado)

func main() {
	var edad int = 20
	if edad >= 18
		fmt.Println("Mayor")
	}
	if edad < 18 {
		fmt.Println("Menor")
	}
	else {
		fmt.Println("No aplica")
	}
}
