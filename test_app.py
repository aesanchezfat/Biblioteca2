import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

import app as biblioteca_app


class BibliotecaTests(unittest.TestCase):
    def setUp(self):
        self.app = biblioteca_app.app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            biblioteca_app.db.drop_all()
            biblioteca_app.db.create_all()

            libro = biblioteca_app.Libro(
                titulo="Test",
                autor="Autor",
                isbn="123",
                disponibles=1,
                prestados=0,
            )
            biblioteca_app.db.session.add(libro)
            biblioteca_app.db.session.commit()

    def test_devolver_sin_prestar_no_cambia_disponibilidad(self):
        with self.app.app_context():
            libro = biblioteca_app.Libro.query.first()
            self.assertEqual(libro.disponibles, 1)
            self.assertEqual(libro.prestados, 0)

            self.client.get(f"/devolver/{libro.id}")

            libro = biblioteca_app.Libro.query.get(libro.id)
            self.assertEqual(libro.disponibles, 1)
            self.assertEqual(libro.prestados, 0)

    def test_prestar_y_devolver_actualiza_los_contadores(self):
        with self.app.app_context():
            libro = biblioteca_app.Libro.query.first()

            self.client.get(f"/prestar/{libro.id}")
            libro = biblioteca_app.Libro.query.get(libro.id)
            self.assertEqual(libro.disponibles, 0)
            self.assertEqual(libro.prestados, 1)

            self.client.get(f"/devolver/{libro.id}")
            libro = biblioteca_app.Libro.query.get(libro.id)
            self.assertEqual(libro.disponibles, 1)
            self.assertEqual(libro.prestados, 0)


if __name__ == "__main__":
    unittest.main()
