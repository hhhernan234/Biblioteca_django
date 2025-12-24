from django.test import TestCase
from gestion.models import Autor, Libro, Prestamo, Editorial
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from gestion.models import UsuarioBiblioteca, validar_cedula_ecuatoriana

class EditorialModelTest(TestCase):
    def setUp(self):
        self.editorial = Editorial.objects.create(
            nombre="Penguin Random House",
            pais="Estados Unidos",
            ciudad="Nueva York"
        )

    def test_editorial_str(self):
        self.assertEqual(str(self.editorial), "Penguin Random House")

    def test_editorial_campos(self):
        self.assertEqual(self.editorial.pais, "Estados Unidos")
        self.assertEqual(self.editorial.ciudad, "Nueva York")

class LibroModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        editorial = Editorial.objects.create(nombre="Editorial Prueba")
        autor = Autor.objects.create(nombre="Isaac", apellido="Asimov", bibliografia="Escritor de ciencia ficción")
        Libro.objects.create(titulo="Fundacion", 
            autor= autor, 
            editorial=editorial,
            isbn="9780553293357",
            paginas=255,
            costo=25.50,
            ejemplares=3,
            disponible=True
        )

    def test_str_devuelve_titulo(self):
        libro = Libro.objects.get(id=1)
        self.assertEqual(str(libro), 'Fundacion')

    def test_libro_tiene_isbn(self):
        libro = Libro.objects.get(id=1)
        self.assertEqual(libro.isbn, "9780553293357")

    def test_libro_tiene_costo(self):
        libro = Libro.objects.get(id=1)
        self.assertEqual(float(libro.costo), 25.50)

    def test_ejemplares_disponibles_sin_prestamos(self):
        libro = Libro.objects.get(id=1)
        self.assertEqual(libro.ejemplares_disponibles, 3)

    def test_ejemplares_disponibles_con_prestamo(self):
        libro = Libro.objects.get(id=1)
        usuario = User.objects.create(username='juan', password='#123Uyqwe')
        Prestamo.objects.create(
            libro=libro,
            usuario=usuario,
            fecha_max=timezone.now().date() + timezone.timedelta(days=2),
            estado='p'  # Prestado
        )
        # Refrescar para obtener el cálculo actualizado
        libro = Libro.objects.get(id=1)
        self.assertEqual(libro.ejemplares_disponibles, 2)

class PrestamoModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        editorial = Editorial.objects.create(nombre="Editorial Test")
        autor = Autor.objects.create(nombre="Isaac", apellido="Asimov", bibliografia="Cualquier dato")
        usuario= User.objects.create(username='juan', password='#123Uyqwe')
        libro= Libro.objects.create(titulo="I Robot", autor_id= 1, disponible=False)
        cls.prestamo= Prestamo.objects.create(
            libro=libro,
            usuario=usuario,
            fecha_max=timezone.now().date() - timezone.timedelta(days=8),
            estado='p'
        )

    def test_libro_no_disponible(self):
        self.prestamo.refresh_from_db()
        self.assertFalse(self.prestamo.libro.disponible)

    def test_dias_retraso(self):
        self.assertEqual(self.prestamo.dias_retraso, 8)

    def test_multa_retraso(self):
        if self.prestamo.dias_retraso > 0:
            self.assertGreater(self.prestamo.multa_retraso, 0)

    def test_estado_prestamo(self):
        self.assertEqual(self.prestamo.estado, 'p')

class PrestamoUsuarioViewTest(TestCase):
    def setUp(self):
        self.user1 =User.objects.create_user('u1', password = 'test12345')
        self.user2 =User.objects.create_user('u2', password = 'test12345')

    def test_redirige_no_login(self):
        resp= self.client.get(reverse('crear_autor'))
        self.assertEqual(resp.status_code, 302)

    def test_carga_login(self):
        resp=self.client.login(username="u1", password ="test12345")
        #self.assertEqual(resp.status_code, 200)
        respl = self.client.get(reverse('crear_autor'))
        self.assertEqual(respl.status_code, 200)

class ValidadorCedulaTest(TestCase):
    def test_cedula_valida(self):
        try:
            validar_cedula_ecuatoriana('1714567890')
        except ValidationError:
            self.fail("Cédula válida fue rechazada")
    
    def test_cedula_invalida(self):
        with self.assertRaises(ValidationError):
            validar_cedula_ecuatoriana('123456789')  # 9 dígitos
        
        with self.assertRaises(ValidationError):
            validar_cedula_ecuatoriana('171456789A')  # Con letra

class UsuarioBibliotecaTest(TestCase):
    def test_crear_usuario(self):
        usuario = UsuarioBiblioteca.objects.create(
            nombre="Juan Pérez",
            cedula="1714567890",
            email="juan@test.com",
            tipo="estudiante"
        )
        self.assertEqual(str(usuario), "Juan Pérez (1714567890)")


        