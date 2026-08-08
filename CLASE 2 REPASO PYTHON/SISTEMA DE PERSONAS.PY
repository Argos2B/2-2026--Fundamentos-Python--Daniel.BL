class Persona:
    def __init__(self, nombre, identificacion, edad, oficio):
        self.nombre = nombre
        self.identificacion = identificacion
        self.edad = edad
        self.oficio = oficio

    def obtener_detalles(self):
        return (
            f"Nombre: {self.nombre}\n"
            f"Identificación: {self.identificacion}\n"
            f"Edad: {self.edad} años\n"
            f"Oficio: {self.oficio}"
        )


class Estudiante(Persona):
    def __init__(self, nombre, identificacion, edad, carrera):
        super().__init__(nombre, identificacion, edad, "Estudiante")
        self.carrera = carrera

    def obtener_detalles(self):
        return f"{super().obtener_detalles()}\nCarrera: {self.carrera}"


class Profesor(Persona):
    def __init__(self, nombre, identificacion, edad, departamento):
        super().__init__(nombre, identificacion, edad, "Profesor")
        self.departamento = departamento

    def obtener_detalles(self):
        return f"{super().obtener_detalles()}\nDepartamento: {self.departamento}"


def imprimir_detalles(persona):
    print(persona.obtener_detalles())


def obtener_tipo(persona):
    return "Estudiante" if isinstance(persona, Estudiante) else "Profesor"


def mostrar_personas(personas, titulo):
    print(f"\n--- {titulo} ---")
    if not personas:
        print("No hay personas registradas.")
        return

    for i, persona in enumerate(personas, 1):
        tipo = obtener_tipo(persona)
        print(f"\n[{i}] ({tipo})")
        imprimir_detalles(persona)


# Programa principal
if __name__ == "__main__":
    estudiante1 = Estudiante("Daniel Borge", "2026-IS0471", 18, "Ingeniería en Sistemas")
    estudiante2 = Estudiante("Carlos Ruiz", "2026-IS0523", 20, "Ingeniería en Sistemas")

    profesor1 = Profesor("Dr. María García", "P-2024-001", 45, "Ciencias de la Computación")
    profesor2 = Profesor("Dr. Juan Martínez", "P-2024-002", 50, "Matemáticas")

    personas = [estudiante1, estudiante2, profesor1, profesor2]

    while True:
        print("\n" + "=" * 50)
        print("       SISTEMA DE GESTIÓN DE PERSONAS")
        print("=" * 50)
        print("\n1. Ver todos los registros")
        print("2. Buscar por nombre")
        print("3. Ver solo estudiantes")
        print("4. Ver solo profesores")
        print("5. Salir")
        print("-" * 50)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            mostrar_personas(personas, "TODOS LOS REGISTROS")

        elif opcion == "2":
            nombre_buscar = input("Ingrese el nombre a buscar: ").strip()
            if not nombre_buscar:
                print("Debe escribir un nombre.")
                continue

            resultados = [
                persona for persona in personas
                if nombre_buscar.lower() in persona.nombre.lower()
            ]

            if resultados:
                mostrar_personas(resultados, f"RESULTADOS PARA: {nombre_buscar}")
            else:
                print("No se encontró ninguna persona con ese nombre.")

        elif opcion == "3":
            estudiantes = [persona for persona in personas if isinstance(persona, Estudiante)]
            mostrar_personas(estudiantes, "ESTUDIANTES")

        elif opcion == "4":
            profesores = [persona for persona in personas if isinstance(persona, Profesor)]
            mostrar_personas(profesores, "PROFESORES")

        elif opcion == "5":
            print("\n¡Hasta luego, Daniel! 👋")
            break

        else:
            print("Opción no válida. Intente de nuevo.")