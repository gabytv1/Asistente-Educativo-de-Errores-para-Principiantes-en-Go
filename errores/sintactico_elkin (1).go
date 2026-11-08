package main

import "fmt"

// Prueba de errores sintácticos - Elkin Salazar (Y6: token inesperado, Y3: llave sin cerrar)

func main() {
	total := := 5
	fmt.Println(total)
	switch total {
	case 5:
		fmt.Println("cinco")
