from django.urls import path
from .views import *
urlpatterns = [
    path("",index, name= "index"),

    #libros
    path('libros/', lista_libros, name="lista_libros"),
    path('libros/nuevo/', crear_libro, name="crear_libro"),

    #Autores
    path('autores/', lista_autores, name="lista_autores"),
    path('autores/nuevo/', crear_autor, name="crear_autor"),

    #prestamos
    path('prestamos/', lista_prestamos, name="lista_prestamos"),
    path('prestamos/nuevo/', crear_prestamo, name="crear_prestamo"),
    path('prestamos/<int:id>', detalle_prestamo, name="detalle_prestamo"),

    #multas
    path('multas/', lista_multas, name="lista_multas"),
    path('multas/nuevo/<int:id>', crear_multa, name="crear_multa"),

]