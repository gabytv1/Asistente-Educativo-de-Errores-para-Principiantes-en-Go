package main

import "fmt"

// Prueba de errores - Fátima Torres (L4: comentario sin cerrar, L7: palabra reservada no soportada)

func main() {
	var edad int = 20
	var notas = []int{8, 9, 10}
	for i := range notas {
		fmt.Println(i)
	}
	fmt.Println(edad)
	/* este comentario nunca se cierra
	edad++
	fmt.Println("no se analiza")
}
