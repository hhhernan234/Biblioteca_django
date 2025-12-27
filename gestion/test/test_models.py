from django.test import TestCase
from gestion.models import Autor, Libro, Prestamo, Editorial
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from gestion.models import UsuarioBiblioteca, validar_cedula_ecuatoriana
from django.core.exceptions import ValidationError
from django.core.management import call_command
from io import StringIO


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
        usuario_bib = UsuarioBiblioteca.objects.create(
            nombre="Juan Pérez",
            cedula="1714567890",
            email="juan@test.com"
        )
        Prestamo.objects.create(
            libro=libro,
            usuario_biblioteca=usuario_bib,  # ← CAMBIO AQUÍ
            fecha_max=timezone.now().date() + timezone.timedelta(days=2),
            estado='p'
        )
        libro = Libro.objects.get(id=1)
        self.assertEqual(libro.ejemplares_disponibles, 2)


class PrestamoModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        editorial = Editorial.objects.create(nombre="Editorial Test")
        autor = Autor.objects.create(nombre="Isaac", apellido="Asimov", bibliografia="Cualquier dato")
        usuario_bib = UsuarioBiblioteca.objects.create(
            nombre="Juan Pérez",
            cedula="0926687856",
            email="juan@test.com"
        )
        libro = Libro.objects.create(titulo="I Robot", autor=autor, editorial=editorial, disponible=False)
        
        cls.prestamo = Prestamo.objects.create(
            libro=libro,
            usuario_biblioteca=usuario_bib,  # ← CAMBIO AQUÍ        
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
            validar_cedula_ecuatoriana('0926687856')  # ← CÉDULA VÁLIDA
            validar_cedula_ecuatoriana('1710034065')
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
            cedula="0926687856",
            email="juan@test.com",
            tipo="estudiante"
        )
        self.assertEqual(str(usuario), "Juan Pérez (0926687856)")

class GenerarPrestamoTest(TestCase):
    def setUp(self):
        self.editorial = Editorial.objects.create(nombre="Test Editorial")
        self.autor = Autor.objects.create(nombre="Test", apellido="Autor")
        self.libro = Libro.objects.create(
            titulo="Libro Test",
            autor=self.autor,
            editorial=self.editorial,
            ejemplares=2,
            disponible=True
        )
        self.usuario_bib = UsuarioBiblioteca.objects.create(
            nombre="Test User",
            cedula="1714567890",
            email="test@test.com"
        )
    
    def test_generar_prestamo_exitoso(self):
        """Generar préstamo con datos válidos debe funcionar"""
        prestamo = Prestamo.objects.create(
            libro=self.libro,
            usuario_biblioteca=self.usuario_bib
        )
        
        # Estado inicial debe ser Borrador
        self.assertEqual(prestamo.estado, 'b')
        
        # Generar préstamo
        prestamo.generar_prestamo()
        
        # Verificar cambios
        self.assertEqual(prestamo.estado, 'p')  # Cambió a Prestado
        self.assertIsNotNone(prestamo.fecha_max)  # Se generó fecha máxima
        
        # Verificar que fecha_max es 2 días después
        from datetime import timedelta
        fecha_esperada = timezone.now().date() + timedelta(days=2)
        self.assertEqual(prestamo.fecha_max, fecha_esperada)
    
    def test_generar_prestamo_sin_ejemplares(self):
        #No debe permitir generar préstamo sin ejemplares disponibles
        # Crear préstamo que agota los ejemplares
        prestamo1 = Prestamo.objects.create(
            libro=self.libro,
            usuario_biblioteca=self.usuario_bib
        )
        prestamo1.generar_prestamo()
        
        usuario_bib2 = UsuarioBiblioteca.objects.create(
            nombre="User 2",
            cedula="0926687856",
            email="test2@test.com"
        )
        
        prestamo2 = Prestamo.objects.create(
            libro=self.libro,
            usuario_biblioteca=usuario_bib2
        )
        prestamo2.generar_prestamo()
        
        # Tercer préstamo debe fallar (ya no hay ejemplares)
        usuario_bib3 = UsuarioBiblioteca.objects.create(
            nombre="User 3",
            cedula="1710034065",
            email="test3@test.com"
        )
        
        prestamo3 = Prestamo.objects.create(
            libro=self.libro,
            usuario_biblioteca=usuario_bib3
        )
        
        with self.assertRaises(ValidationError):
            prestamo3.generar_prestamo()
    
    def test_actualizar_disponibilidad_libro(self):
        """Libro debe marcarse como no disponible al prestar último ejemplar"""
        # Libro con 1 solo ejemplar
        libro_unico = Libro.objects.create(
            titulo="Libro Único",
            autor=self.autor,
            ejemplares=1,
            disponible=True
        )
        
        prestamo = Prestamo.objects.create(
            libro=libro_unico,
            usuario_biblioteca=self.usuario_bib
        )
        
        # Antes de generar, está disponible
        self.assertTrue(libro_unico.disponible)
        
        # Generar préstamo
        prestamo.generar_prestamo()
        
        # Después de generar, NO está disponible
        libro_unico.refresh_from_db()
        self.assertFalse(libro_unico.disponible)

class DevolucionPrestamoTest(TestCase):
    def setUp(self):
        self.editorial = Editorial.objects.create(nombre="Test Editorial")
        self.autor = Autor.objects.create(nombre="Test", apellido="Autor")
        self.libro = Libro.objects.create(
            titulo="Libro Test",
            autor=self.autor,
            editorial=self.editorial,
            ejemplares=1,
            costo=20.00,
            disponible=True
        )
        self.usuario_bib = UsuarioBiblioteca.objects.create(
            nombre="Test User",
            cedula="1714567890",
            email="test@test.com"
        )
        self.prestamo = Prestamo.objects.create(
            libro=self.libro,
            usuario_biblioteca=self.usuario_bib,
            estado_libro='bueno'
        )
        self.prestamo.generar_prestamo()
    
    def test_devolucion_sin_multas(self):
        #Devolución en tiempo y buen estado no genera multas
        self.prestamo.estado_libro = 'bueno'
        resultado = self.prestamo.devolver_libro()
        
        self.assertEqual(self.prestamo.estado, 'd')
        self.assertEqual(self.prestamo.multas.count(), 0)
        self.assertIn('sin multas', resultado)
    
    def test_devolucion_con_retraso(self):
        #Devolución con retraso genera multa por día
        from datetime import timedelta
        # Simular retraso de 5 días
        self.prestamo.fecha_max = timezone.now().date() - timedelta(days=5)
        self.prestamo.save()
        
        self.prestamo.devolver_libro()
        
        multa = self.prestamo.multas.filter(tipo='r').first()
        self.assertIsNotNone(multa)
        self.assertEqual(float(multa.monto), 5.0)  # $1 por día x 5 días
    
    def test_devolucion_libro_danado(self):
        #Devolución con libro dañado genera multa del 50%
        self.prestamo.estado_libro = 'danado'
        self.prestamo.devolver_libro()
        
        multa = self.prestamo.multas.filter(tipo='d').first()
        self.assertIsNotNone(multa)
        self.assertEqual(float(multa.monto), 10.0)  # 50% de $20
    
    def test_devolucion_libro_perdido(self):
        #Devolución con libro perdido genera multa del 200%
        self.prestamo.estado_libro = 'perdido'
        self.prestamo.devolver_libro()
        
        multa = self.prestamo.multas.filter(tipo='p').first()
        self.assertIsNotNone(multa)
        self.assertEqual(float(multa.monto), 40.0)  # 200% de $20
    
    def test_restaurar_disponibilidad(self):
        #Libro debe volver a estar disponible después de devolución
        self.libro.disponible = False
        self.libro.save()
        
        self.prestamo.devolver_libro()
        
        self.libro.refresh_from_db()
        self.assertTrue(self.libro.disponible)

class ComandoVerificarPrestamosTest(TestCase):
    def setUp(self):
        self.editorial = Editorial.objects.create(nombre="Test Editorial")
        self.autor = Autor.objects.create(nombre="Test", apellido="Autor")
        self.libro = Libro.objects.create(
            titulo="Libro Test",
            autor=self.autor,
            editorial=self.editorial,
            ejemplares=1,
            costo=20.00
        )
        self.usuario_bib = UsuarioBiblioteca.objects.create(
            nombre="Test User",
            cedula="1714567890",
            email="test@test.com"
        )
    
    def test_comando_crea_multas_para_prestamos_vencidos(self):
        """El comando debe crear multas para préstamos vencidos"""
        from datetime import timedelta
        
        # Crear préstamo vencido
        prestamo = Prestamo.objects.create(
            libro=self.libro,
            usuario_biblioteca=self.usuario_bib,
            fecha_max=timezone.now().date() - timedelta(days=3),
            estado='p'
        )
        
        # Verificar que no tiene multas
        self.assertEqual(prestamo.multas.count(), 0)
        
        # Ejecutar comando
        out = StringIO()
        call_command('verificar_prestamos_vencidos', stdout=out)
        
        # Verificar que se creó la multa
        prestamo.refresh_from_db()
        self.assertEqual(prestamo.multas.count(), 1)
        self.assertEqual(prestamo.estado, 'm')  # Cambió a Multado
        
        # Verificar monto de la multa
        multa = prestamo.multas.first()
        self.assertEqual(float(multa.monto), 3.0)  # 3 días x $1
    
    def test_comando_actualiza_multas_existentes(self):
        """El comando debe actualizar multas existentes"""
        from datetime import timedelta
        from gestion.models import Multa
        
        # Crear préstamo vencido con multa existente
        prestamo = Prestamo.objects.create(
            libro=self.libro,
            usuario_biblioteca=self.usuario_bib,
            fecha_max=timezone.now().date() - timedelta(days=5),
            estado='p'
        )
        
        # Crear multa con monto antiguo
        multa = Multa.objects.create(
            prestamo=prestamo,
            tipo='r',
            monto=3.0
        )
        
        # Ejecutar comando
        call_command('verificar_prestamos_vencidos')
        
        # Verificar que se actualizó el monto
        multa.refresh_from_db()
        self.assertEqual(float(multa.monto), 5.0)  # 5 días x $1