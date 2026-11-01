package main

import "fmt"

// Algoritmo 3 - Elkin Salazar
// Mini tienda: calcula el total de una compra, aplica un descuento
// y actualiza el stock del producto vendido.

/* Se prueban los operadores del subconjunto: aritmeticos, comparacion,
   logicos, asignacion, direccion (&) y el tipo mapa (map). */

const TIENDA = "Mini Tienda"
const MINIMO = 5
const DESCUENTO = 10
const ENVIO = 5
const IVA = 0.12

func mostrarMenu(titulo string) {
	fmt.Println(titulo)
	fmt.Println("1 = manzana, 2 = pera")
}

func calcularTotal(precio int, cantidad int) int {
	total := precio * cantidad
	if cantidad >= MINIMO {
		total -= DESCUENTO
	}
	return total
}

func main() {
	mostrarMenu(TIENDA)

	precios := map[string]int{"manzana": 50, "pera": 75}
	stock := map[string]int{"manzana": 20, "pera": 8}

	var opcion int
	var cantidad int
	fmt.Scanln(&opcion)
	fmt.Scanln(&cantidad)

	if opcion < 1 || opcion > 2 {
		fmt.Println("Opcion fuera del menu")
	}

	var nombre string
	switch opcion {
	case 1:
		nombre = "manzana"
	case 2:
		nombre = "pera"
	default:
		nombre = "ninguno"
	}

	var promo bool = false
	if cantidad >= MINIMO {
		promo = true
	}

	valido := nombre != "ninguno" && cantidad > 0 && !(cantidad > stock[nombre])

	if valido {
		total := calcularTotal(precios[nombre], cantidad)
		totalFinal := total + ENVIO
		ahorro := precios[nombre]*cantidad - total
		stock[nombre] -= cantidad
		if stock[nombre] < MINIMO {
			stock[nombre] += 10
		}
		fmt.Println("Producto:", nombre)
		fmt.Println("Total con envio:", totalFinal)
		fmt.Println("Ahorro:", ahorro)
		fmt.Println("Hay promocion:", promo)
		fmt.Println("Stock actual:", stock[nombre])
	} else {
		fmt.Println("Opcion o cantidad no valida")
	}

	paquetes := cantidad / 3
	sueltos := cantidad % 3
	fmt.Println("Paquetes:", paquetes, "Sueltos:", sueltos)

	for restantes := paquetes; restantes > 0; restantes-- {
		fmt.Println("Paquete listo")
	}

	for i := 1; i <= 3; i++ {
		if i == 2 {
			continue
		}
		fmt.Println("Revisando estante", i)
	}

	pendientes := cantidad
	viajes := 0
	for pendientes > 0 {
		pendientes -= 3
		viajes++
		if viajes == 4 {
			break
		}
	}
	fmt.Println("Viajes:", viajes)

	var porcentajeIva float64 = IVA * 100.0
	fmt.Println("IVA (%):", porcentajeIva)
}
