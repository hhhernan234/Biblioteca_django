from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from .models import Autor, Libro, Prestamo, Multa

def index(request):
    title = settings.TITLE
    return render(request, 'gestion/templates/home.html', {'titulo': title})

def lista_libros(request):
    libros = Libro.objects.all()
    return render(request,'gestion/templates/libros.html', {'libros': libros} )

def crear_libro(request):
    autores = Autor.objects.all()
    if request.method == 'POST':
        titulo=request.POST.get('titulo')
        autor_id=request.POST.get('autor')
        if titulo and autor_id:
            autor = get_object_or_404(Autor, id=autor_id)
            Libro.objects.create(titulo=titulo, autor=autor)
            return redirect('lista_libros')
    return render(request, 'gestion/templates/crear_libro.html', {'autores': autores})
 
def lista_autores(request):
    autores = Autor.objects.all()
    return render(request,'gestion/templates/autores.html', {'autores': autores} )
    
def crear_autor(request, id=None):
    if id == None:
        autor= None
        modo = 'crear'
    else:
        autor= get_object_or_404(Autor, id=id)
        modo = 'editar'

    if request.method == 'POST':
        nombre=request.POST.get('nombre')
        apellido=request.POST.get('apellido')
        bibliografia=request.POST.get('bibliografia')
        if autor == None:
            Autor.objects.create(nombre=nombre, apellido=apellido, bibliografia=bibliografia)
        else:
            autor.apellido= apellido
            autor.nombre= nombre
            autor.bibliografia= bibliografia
            autor.save()
        return redirect('lista_autores')
    context = {'autor': autor,
               'titulo': 'Editar Autor' if modo == 'editar' else 'Crear Autor',
               'texto_boton': 'Guardar cambios' if modo == 'editar' else 'Crear'}
    return render(request, 'gestion/templates/crear_autores.html', context)

def lista_prestamos(request):
    prestamos = Prestamo.objects.all()
    return render(request,'gestion/templates/prestamos.html', {'prestamos': prestamos} )

def crear_prestamo(request):
    libro = Libro.objects.filter(disponible=True)
    usuario = User.objects.all()
    if request.method == 'POST':
        libro_id= request.method.POST.get('libro')
        usuario_id = request.method.POST.get('usuario')
        fecha_prestamo = request.method.POST.get('fecha_maxima')
        if libro_id and usuario_id and fecha_prestamo:
            libro = get_object_or_404(Libro, id= libro_id)
            usuario = get_object_or_404(User, id= usuario_id)
            prestamo = Prestamo.objects.create(libro= libro,
                                               usuario= usuario,
                                               fecha_prestamo= fecha_prestamo)
            libro.disponible = False
            libro.save()
            return redirect('detalle_prestamo', id= prestamo.id)
    fecha = (timezone.now().date()).isoformat()
    return render (request, 'gestion/templates/crear_prestamo.html', {'libros':libro,
                                                                     'usuario':usuario,
                                                                     'fecha': fecha})
        

def detalle_prestamo(request):
    pass

def lista_multas(request):
    multas = Multa.objects.all()
    return render(request,'gestion/templates/multas.html', {'multas': multas} )

def crear_multa(request):
    pass




# Create your views here.
def crear_editar_autor(request, id=None):
    autor = get_object_or_404(Autor, id=id) if id else None
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        bibliografia = request.POST.get('bibliografia')
        
        if nombre and apellido:
            if autor:  # Editar
                autor.nombre = nombre
                autor.apellido = apellido
                autor.bibliografia = bibliografia
                autor.save()
            else:  # Crear
                Autor.objects.create(nombre=nombre, apellido=apellido, bibliografia=bibliografia)
            return redirect('lista_autores')
    
    template = 'gestion/templates/editar_autores.html' if autor else 'gestion/templates/crear_autores.html'
    return render(request, template, {'autor': autor})