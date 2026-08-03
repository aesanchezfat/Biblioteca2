# Sistema de Biblioteca - Corrección de Devoluciones y Carga de Imágenes

Implementar un control para que solo los usuarios que hayan pedido prestado un libro puedan devolverlo, y agregar soporte para subir imágenes (portadas) de los libros, codificado con un estilo básico de programación orientada a objetos (OOP) apto para un estudiante de programación.

## Proposed Changes

### Modelos y Configuración de Base de Datos
Actualizaremos los modelos de la base de datos en `app.py`:
- Añadir el atributo `prestados` a `Libro` para realizar el seguimiento del número total de libros prestados (de esta manera los tests existentes pasarán).
- Añadir el atributo `imagen` a `Libro` para almacenar el nombre de la imagen de portada.
- Crear la clase `Prestamo` como un nuevo modelo que registre qué `Usuario` (mediante `usuario_id`) ha pedido prestado qué `Libro` (mediante `libro_id`).

### Controladores y Rutas en Flask
- **`prestar`**: Modificarla para verificar la sesión, verificar si el usuario ya tiene prestado este libro, descontar de `disponibles`, aumentar `prestados` y crear el objeto `Prestamo`.
- **`devolver`**: Modificarla para verificar que el usuario tenga un préstamo activo de ese libro. De ser así, eliminar el `Prestamo`, incrementar `disponibles` y decrementar `prestados`.
- **`agregar`** y **`editar`**: Modificar las rutas para recibir archivos multimedia (imágenes) en el formulario, guardarlos en `Static/uploads` y asociar el nombre del archivo al libro.

---

### Archivos Modificados

#### [MODIFY] [app.py](file:///c:/Users/brian/Documents/biblioteca/app.py)
- Importar `os` y configurar el directorio de subida (`Static/uploads`).
- Definir la clase `Prestamo(db.Model)`.
- Añadir los atributos `prestados` e `imagen` a `Libro`.
- Actualizar las vistas `/prestar/<int:id>`, `/devolver/<int:id>`, `/agregar` y `/editar/<int:id>` con las validaciones de préstamos y la gestión de archivos de imagen.

#### [MODIFY] [inicio.html](file:///c:/Users/brian/Documents/biblioteca/Templates/inicio.html)
- Agregar una columna al catálogo para mostrar la imagen del libro (`<img>` con ruta a `/Static/uploads/`).
- Ocultar o deshabilitar el botón "Devolver" si el usuario no tiene prestado el libro (opcional, pero mejora la experiencia).

#### [MODIFY] [agregar.html](file:///c:/Users/brian/Documents/biblioteca/Templates/agregar.html)
- Añadir `enctype="multipart/form-data"` a la etiqueta `<form>`.
- Añadir un `<input type="file" name="imagen">` para subir la portada.

#### [MODIFY] [editar.html](file:///c:/Users/brian/Documents/biblioteca/Templates/editar.html)
- Añadir `enctype="multipart/form-data"` a la etiqueta `<form>`.
- Añadir un `<input type="file" name="imagen">` para actualizar la portada actual.

#### [MODIFY] [test_app.py](file:///c:/Users/brian/Documents/biblioteca/test_app.py)
- Ajustar el flujo de prueba para iniciar sesión (`self.client.post('/')`) antes de realizar acciones de préstamo/devolución.

---

## Verification Plan

### Automated Tests
Correr los tests con:
- `python test_app.py`

### Manual Verification
- Iniciar la aplicación (`python app.py`).
- Iniciar sesión como administrador (`admin` / `1234`).
- Registrar un libro con una imagen de portada y verificar que se suba correctamente a `Static/uploads` y se muestre en el catálogo.
- Iniciar sesión como usuario (`andre` / `1234`).
- Intentar devolver un libro no prestado mediante la URL directa (`/devolver/1`) y verificar que se deniegue la devolución.
- Prestar un libro y comprobar que disminuye la cantidad disponible y se permite su devolución.
