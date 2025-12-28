from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from .models import Autor, Libro, Prestamo, Multa, UsuarioBiblioteca, Editorial
import requests
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User, Permission
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views.generic import ListView, CreateView, UpdateView,DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


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
    return render(request, 'gestion/templates/crear_libros.html', {'autores': autores})
 
def lista_autores(request):
    autores = Autor.objects.all()
    return render(request,'gestion/templates/autores.html', {'autores': autores} )

@login_required    
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
    prestamos = Prestamo.objects.select_related('libro', 'usuario_biblioteca').all()
    return render(request,'gestion/templates/prestamos.html', {'prestamos': prestamos})

def crear_prestamo(request):
    if not request.user.has_perm('gestion.gestionar_prestamos'):
        return HttpResponseForbidden()
    
    libros = Libro.objects.all()  # Mostrar todos, luego validamos disponibilidad
    usuarios_biblioteca = UsuarioBiblioteca.objects.filter(activo=True)
    
    if request.method == 'POST':
        libro_id = request.POST.get('libro')
        usuario_biblioteca_id = request.POST.get('usuario_biblioteca')
        
        if libro_id and usuario_biblioteca_id:
            libro = get_object_or_404(Libro, id=libro_id)
            usuario_bib = get_object_or_404(UsuarioBiblioteca, id=usuario_biblioteca_id)
            
            try:
                # Crear préstamo en estado Borrador
                prestamo = Prestamo.objects.create(
                    libro=libro,
                    usuario_biblioteca=usuario_bib
                )
                
                # Intentar generar el préstamo (activa validaciones)
                prestamo.generar_prestamo()
                
                messages.success(request, f'Préstamo generado exitosamente. Devolver antes del {prestamo.fecha_max.strftime("%d/%m/%Y")}')
                return redirect('detalle_prestamo', id=prestamo.id)
                
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error al crear préstamo: {str(e)}')
    
    return render(request, 'crear_prestamo.html', {
        'libros': libros,
        'usuarios_biblioteca': usuarios_biblioteca
    })
        

def detalle_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, id=id)
    return render(request, 'gestion/templates/detalle_prestamo.html', {'prestamo': prestamo})

def lista_multas(request):
    multas = Multa.objects.select_related(
        'prestamo__libro',
        'prestamo__usuario_biblioteca'
    ).all()
    return render(request,'gestion/templates/multas.html', {'multas': multas})

def crear_multa(request):
    pass

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            try:
                permiso = Permission.objects.get(codename='gestionar_prestamos')
                usuario.user_permissions.add(permiso)
            except Permission.DoesNotExist:
                pass  # El permiso no existe
            login(request, usuario)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render (request, 'gestion/templates/registration/registro.html', {'form': form})



class LibroListView(LoginRequiredMixin, ListView):
    model = Libro
    template_name = 'gestion/templates/libros_view.html'
    context_object_name = 'libros'
    paginate_by = 1

class LibroDetalleView(LoginRequiredMixin, ListView):
    model = Libro
    template = 'gestion/templates/detalle_libros.html'
    context_object_name = 'libro'

class LibroCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Libro
    fields = ['titulo', 'autor', 'disponible']
    template_name = 'gestion/templates/crear_libros.html'
    success_url = reverse_lazy('libro_list')
    permission_required = 'gestion.add_libro'

class LibroUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Libro
    fields = ['titulo', 'autor']
    template_name = 'gestion/templates/editar_libros.html'
    success_url = reverse_lazy('libro_list')
    permission_required = 'gestion.change_libro'

class LibroDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Libro
    template_name = 'gestion/templates/delete_libros.html'
    success_url = reverse_lazy('libro_list')
    permission_required = 'gestion.delete_libro'

# Agregar al final de views.py

def lista_usuarios_biblioteca(request):
    usuarios = UsuarioBiblioteca.objects.filter(activo=True)
    return render(request, 'gestion/templates/usuarios_biblioteca.html', {'usuarios': usuarios})


@login_required
def crear_usuario_biblioteca(request):
    if request.method == 'POST':
        try:
            UsuarioBiblioteca.objects.create(
                nombre=request.POST.get('nombre'),
                cedula=request.POST.get('cedula'),
                email=request.POST.get('email'),
                tipo=request.POST.get('tipo', 'externo')
            )
            messages.success(request, 'Usuario creado exitosamente')
            return redirect('lista_usuarios_biblioteca')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'gestion/templates/crear_usuario_biblioteca.html')

@login_required
def devolver_prestamo(request, id):
    #Vista para procesar la devolución de un préstamo
    prestamo = get_object_or_404(Prestamo, id=id)
    
    if request.method == 'POST':
        estado_libro = request.POST.get('estado_libro', 'bueno')
        
        try:
            # Actualizar estado del libro
            prestamo.estado_libro = estado_libro
            
            # Procesar devolución
            mensaje = prestamo.devolver_libro()
            
            messages.success(request, mensaje)
            return redirect('detalle_prestamo', id=prestamo.id)
            
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al devolver: {str(e)}')
    
    return render(request, 'devolver_prestamo.html', {'prestamo': prestamo})

@login_required
def enviar_correo_multa(request, id):
    #Envía correo de notificación de multa al usuario
    prestamo = get_object_or_404(Prestamo, id=id)
    
    if not prestamo.usuario_biblioteca or not prestamo.usuario_biblioteca.email:
        messages.error(request, 'El usuario no tiene email registrado')
        return redirect('detalle_prestamo', id=prestamo.id)
    
    if not prestamo.multas.exists():
        messages.error(request, 'Este préstamo no tiene multas')
        return redirect('detalle_prestamo', id=prestamo.id)
    
    try:
        # Calcular total de multas
        total_multas = sum(float(m.monto) for m in prestamo.multas.all())
        
        # Preparar contexto para el template
        context = {
            'prestamo': prestamo,
            'total_multas': total_multas,
            'usuario': prestamo.usuario_biblioteca,
            'libro': prestamo.libro,
        }
        
        # Renderizar el mensaje
        mensaje_html = render_to_string('email_multa.html', context)
        mensaje_texto = f"""
        Estimado/a {prestamo.usuario_biblioteca.nombre},
        
        Le informamos que tiene una multa pendiente por el préstamo del libro:
        "{prestamo.libro.titulo}"
        
        Detalles:
        - Fecha de préstamo: {prestamo.fecha_prestamos.strftime('%d/%m/%Y')}
        - Fecha máxima de devolución: {prestamo.fecha_max.strftime('%d/%m/%Y')}
        
        Total de multas: ${total_multas:.2f}
        
        Por favor, devuelva el libro y pague la multa a la brevedad posible.
        
        Saludos,
        Sistema de Biblioteca
        """
        
        # Enviar correo
        send_mail(
            subject=f'Multa pendiente - Préstamo #{prestamo.id}',
            message=mensaje_texto,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'biblioteca@example.com',
            recipient_list=[prestamo.usuario_biblioteca.email],
            html_message=mensaje_html,
            fail_silently=False,
        )
        
        messages.success(request, f'Correo enviado exitosamente a {prestamo.usuario_biblioteca.email}')
        
    except Exception as e:
        messages.error(request, f'Error al enviar correo: {str(e)}')
    
    return redirect('detalle_prestamo', id=prestamo.id)

import requests

@login_required
def importar_libros(request):
    """Vista para buscar e importar libros desde OpenLibrary"""
    resultados = []
    busqueda_realizada = False
    
    if request.method == 'POST':
        buscar_por = request.POST.get('buscar_por', 'titulo')
        texto = request.POST.get('texto_busqueda', '').strip()
        
        if texto:
            try:
                # Construir URL según tipo de búsqueda
                if buscar_por == 'titulo':
                    url = f"https://openlibrary.org/search.json?title={texto}&limit=10"
                else:
                    url = f"https://openlibrary.org/search.json?author={texto}&limit=10"
                
                # Hacer petición
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if data.get('docs'):
                    resultados = data['docs'][:10]
                    busqueda_realizada = True
                else:
                    messages.warning(request, 'No se encontraron resultados')
                    
            except Exception as e:
                messages.error(request, f'Error al buscar: {str(e)}')
    
    return render(request, 'importar_libros.html', {
        'resultados': resultados,
        'busqueda_realizada': busqueda_realizada
    })


@login_required
def importar_libro_seleccionado(request, isbn):
    """Importa un libro específico desde OpenLibrary"""
    try:
        # Verificar si ya existe
        if Libro.objects.filter(isbn=isbn).exists():
            messages.warning(request, f'El libro con ISBN {isbn} ya existe en la biblioteca')
            return redirect('importar_libros')
        
        # Buscar información del libro
        url = f"https://openlibrary.org/search.json?isbn={isbn}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data.get('docs'):
            messages.error(request, 'No se encontró información del libro')
            return redirect('importar_libros')
        
        doc = data['docs'][0]
        
        # Crear o buscar autor
        autor = None
        if doc.get('author_name'):
            nombre_completo = doc['author_name'][0]
            nombres = nombre_completo.split()
            firstname = nombres[0]
            lastname = ' '.join(nombres[1:]) if len(nombres) > 1 else ''
            
            autor, created = Autor.objects.get_or_create(
                nombre=firstname,
                apellido=lastname
            )
        
        # Crear o buscar editorial
        editorial = None
        if doc.get('publisher'):
            nombre_editorial = doc['publisher'][0]
            editorial, created = Editorial.objects.get_or_create(
                nombre=nombre_editorial
            )
        
        # Crear el libro
        libro = Libro.objects.create(
            titulo=doc.get('title', 'Sin título')[:200],
            autor=autor if autor else Autor.objects.first(),
            editorial=editorial,
            isbn=isbn,
            paginas=doc.get('number_of_pages_median'),
            fecha_publicacion=f"{doc['first_publish_year']}-01-01" if doc.get('first_publish_year') else None,
            ejemplares=1,
            costo=20.00,
            disponible=True  # ← MUY IMPORTANTE
        )
        
        messages.success(request, f'Libro "{libro.titulo}" importado exitosamente')
        
    except Exception as e:
        messages.error(request, f'Error al importar: {str(e)}')
    
    return redirect('importar_libros')

@login_required
def importar_libro_sin_isbn(request):
    """Importa un libro sin ISBN, usando el título como identificador"""
    if request.method == 'POST':
        try:
            titulo = request.POST.get('titulo', 'Sin título')[:200]
            autor_nombre = request.POST.get('autor', '')
            isbn = request.POST.get('isbn', '') or None
            editorial_nombre = request.POST.get('editorial', '')
            anio = request.POST.get('anio', '')
            paginas = request.POST.get('paginas', '')
            
            # Verificar si ya existe (por ISBN si tiene, sino por título)
            if isbn:
                if Libro.objects.filter(isbn=isbn).exists():
                    messages.warning(request, f'El libro con ISBN {isbn} ya existe')
                    return redirect('importar_libros')
            else:
                # Si no tiene ISBN, verificar por título exacto
                if Libro.objects.filter(titulo__iexact=titulo).exists():
                    messages.warning(request, f'El libro "{titulo}" ya existe en la biblioteca')
                    return redirect('importar_libros')
            
            # Crear o buscar autor
            autor = None
            if autor_nombre:
                nombres = autor_nombre.split()
                firstname = nombres[0]
                lastname = ' '.join(nombres[1:]) if len(nombres) > 1 else ''
                
                autor, created = Autor.objects.get_or_create(
                    nombre=firstname,
                    apellido=lastname
                )
            
            # Crear o buscar editorial
            editorial = None
            if editorial_nombre:
                editorial, created = Editorial.objects.get_or_create(
                    nombre=editorial_nombre
                )
            
            # Preparar fecha de publicación
            fecha_pub = None
            if anio:
                try:
                    fecha_pub = f"{anio}-01-01"
                except:
                    pass
            
            # Crear el libro
            libro = Libro.objects.create(
                titulo=titulo,
                autor=autor if autor else Autor.objects.first(),
                editorial=editorial,
                isbn=isbn,
                paginas=int(paginas) if paginas else None,
                fecha_publicacion=fecha_pub,
                ejemplares=1,
                costo=20.00,
                disponible=True
            )
            
            messages.success(request, f'Libro "{libro.titulo}" importado exitosamente')
            
        except Exception as e:
            messages.error(request, f'Error al importar: {str(e)}')
    
    return redirect('importar_libros')
 
@login_required
def generar_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, id=id)
    
    try:
        # El método generar_prestamo() YA cambia el estado y guarda
        prestamo.generar_prestamo()
        
        messages.success(request, f"✅ Préstamo {prestamo.codigo} generado exitosamente.")
    except ValidationError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
    
    return redirect('detalle_prestamo', id=id)