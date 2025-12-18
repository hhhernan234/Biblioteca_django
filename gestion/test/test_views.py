from django.urls import reverse
from django.test import TestCase
from gestion.models import Libro, Autor

class ListaLibroViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        autor = Autor.objects.create(nombre = "autor", apellido="libro", bibliografia="BBBBBB")
        for i in range(3):
            Libro.objects.create(titulo=f"I Robot{i}", autor=autor, disponible=True)

    def test_url_existencias(self):
        resp = self.client.get(reverse('lista_libros'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'gestion/templates/libros.html')
        self.assertEqual(len(resp.context['libros']), 3)