from django.contrib import admin
from .models import Autor
from .models import Libro
from .models import Multa
from .models import Prestamo
from .models import Editorial
from .models import UsuarioBiblioteca

# Register your models here.

@admin.register(UsuarioBiblioteca)
class UsuarioBibliotecaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cedula', 'tipo', 'email', 'activo']
    search_fields = ['nombre', 'cedula']
    list_filter = ['tipo', 'activo']

@admin.register(Editorial)
class EditorialAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'pais', 'ciudad']
    search_fields = ['nombre', 'pais']

@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido']
    search_fields = ['nombre', 'apellido']

@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'autor', 'editorial', 'isbn', 'ejemplares', 'costo']
    search_fields = ['titulo', 'isbn']
    list_filter = ['editorial', 'autor']

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ['libro', 'usuario_biblioteca', 'fecha_prestamos', 'fecha_max', 'estado']
    list_filter = ['estado', 'fecha_prestamos']

@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = ['prestamo', 'tipo', 'monto', 'pagada', 'fecha']
    list_filter = ['tipo', 'pagada']