from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views
urlpatterns = [
    path("",index, name= "index"),

    # Devolución
    path('prestamos/<int:id>/devolver/', devolver_prestamo, name="devolver_prestamo"),

    #Class View
    path('libros_view/', LibroListView.as_view(), name= "libro_list"),

    #Gestion Usuarios
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name="logout"),

    #Cambio de contraseña
    path('password/change', auth_views.PasswordChangeView.as_view(), name="password_change"),
    path('password/change/done', auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    #Registro
    path('registro/', registro, name="registro"),
    #libros
    path('libros/', lista_libros, name="lista_libros"),
    path('libros/nuevo/', crear_libro, name="crear_libro"),

    #Autores
    path('autores/', lista_autores, name="lista_autores"),
    path('autores/nuevo/', crear_autor, name="crear_autor"),
    path('autores/<int:id>/editar/', crear_autor, name="editar_autor"),

    #prestamos
    path('prestamos/', lista_prestamos, name="lista_prestamos"),
    path('prestamos/nuevo/', crear_prestamo, name="crear_prestamo"),
    path('prestamos/<int:id>', detalle_prestamo, name="detalle_prestamo"),

    #multas
    path('multas/', lista_multas, name="lista_multas"),
    path('multas/nuevo/<int:id>', crear_multa, name="crear_multa"),

    #usuarios
    path('usuarios-biblioteca/', lista_usuarios_biblioteca, name="lista_usuarios_biblioteca"),
    path('usuarios-biblioteca/nuevo/', crear_usuario_biblioteca, name="crear_usuario_biblioteca"),

]