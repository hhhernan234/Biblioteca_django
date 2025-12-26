from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
# Create your models here.

class Editorial(models.Model):
    nombre = models.CharField(max_length=100)
    pais = models.CharField(max_length=50, blank=True, null=True)
    ciudad = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Editoriales"

    def __str__(self):
        return self.nombre

class Autor(models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    bibliografia= models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Autores"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Libro(models.Model):
    titulo = models.CharField(max_length=20)
    autor = models.ForeignKey(Autor, related_name = "libros", on_delete=models.PROTECT)
    editorial = models.ForeignKey(Editorial, related_name="libros", on_delete=models.SET_NULL, null=True, blank=True)
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True)
    paginas = models.PositiveIntegerField(blank=True, null=True)
    fecha_publicacion = models.DateField(blank=True, null=True)
    costo = models.DecimalField(max_digits=6, decimal_places=2, default=20.00)
    ejemplares = models.PositiveIntegerField(default=1)
    disponible = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Libros"

    def __str__(self):
        return f"{self.titulo}"
    
    @property
    def ejemplares_disponibles(self):
        #Calcula ejemplares disponibles basándose en préstamos activos
        prestamos_activos = self.prestamos.filter(
            estado__in=['p', 'm']  # Prestado o Multado
        ).count()
        return self.ejemplares - prestamos_activos
    
class Prestamo(models.Model):
    ESTADOS = [
        ('b', 'Borrador'),
        ('p', 'Prestado'),
        ('m', 'Multado'),
        ('d', 'Devuelto'),
    ]

    ESTADOS_LIBRO = [  # ← AGREGAR ESTO
        ('bueno', 'Buen Estado'),
        ('danado', 'Dañado'),
        ('perdido', 'Perdido'),
    ]

    libro = models.ForeignKey(Libro, related_name ="prestamos", on_delete=models.PROTECT)
    usuario_biblioteca = models.ForeignKey('UsuarioBiblioteca', related_name='prestamos', 
                                       on_delete=models.PROTECT, null=True, blank=True)
    fecha_prestamos = models.DateField(default=timezone.now)
    fecha_max = models.DateField(null=True, blank=True)
    fecha_devolucion= models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=1, choices=ESTADOS, default='b') 
    estado_libro = models.CharField(max_length=10, choices=ESTADOS_LIBRO, default='bueno', blank=True) 

    class Meta:
        permissions = (
            ("Ver_prestamos", "Puede ver prestaamos"),
            ("gestionar_prestamos", "Puede gestionar_prestamos"),
        )
        verbose_name_plural = "Préstamos"
    
    def __str__(self):
        usuario_nombre = self.usuario_biblioteca.nombre if self.usuario_biblioteca else "Sin usuario"
        return f"{self.libro.titulo} - {usuario_nombre}"
    
    @property
    def dias_retraso(self):
        hoy= timezone.now().date()
        fecha_ref = self.fecha_devolucion or hoy
        if fecha_ref > self.fecha_max:
            return(fecha_ref - self.fecha_max).days
        else:
            return 0
    
    @property
    def multa_retraso(self):
        tarifa =0.50
        return self.dias_retraso * tarifa
    
    def save(self, *args, **kwargs):
        #Sobrescribe save para mantener compatibilidad
        super().save(*args, **kwargs)
    
    def generar_prestamo(self):
        #Activa el préstamo después de validaciones
        from datetime import timedelta
        
        # Validación 1: Verificar que haya ejemplares disponibles
        if self.libro.ejemplares_disponibles <= 0:
            raise ValidationError(
                f'No hay ejemplares disponibles de "{self.libro.titulo}". '
                f'Todos están prestados.'
            )
        
        # Validación 2: Solo se puede generar desde estado Borrador
        if self.estado != 'b':
            raise ValidationError('Solo se pueden generar préstamos en estado Borrador')
        
        # Validación 3: Debe tener usuario asignado
        if not self.usuario_biblioteca:
            raise ValidationError('Debe asignar un usuario de biblioteca antes de generar el préstamo')
        
        # Calcular fecha máxima (2 días desde hoy)
        if not self.fecha_max:
            self.fecha_max = timezone.now().date() + timedelta(days=2)
        
        # Cambiar estado a Prestado
        self.estado = 'p'
        
        # Actualizar disponibilidad del libro si es el último ejemplar
        if self.libro.ejemplares_disponibles == 1:
            self.libro.disponible = False
            self.libro.save()
        
        self.save()
        return True
    
    def devolver_libro(self):
        #Procesa la devolución del libro con generación automática de multas
        from datetime import timedelta
        
        # Validación: Solo se pueden devolver préstamos Prestados o Multados
        if self.estado not in ['p', 'm']:
            raise ValidationError('Solo se pueden devolver préstamos en estado Prestado o Multado')
        
        fecha_actual = timezone.now().date()
        self.fecha_devolucion = fecha_actual
        
        # 1. MULTA POR PÉRDIDA (tiene prioridad, cancela otras multas)
        if self.estado_libro == 'perdido':
            # Eliminar multas anteriores
            self.multas.all().delete()
            
            # Crear multa por pérdida (200% del costo)
            costo_perdida = float(self.libro.costo) * 2
            Multa.objects.create(
                prestamo=self,
                tipo='p',
                monto=costo_perdida,
                fecha=fecha_actual
            )
            
            self.estado = 'd'
            self.save()
            return f'Libro perdido registrado. Multa: ${costo_perdida:.2f}'
        
        # 2. MULTA POR DAÑO
        if self.estado_libro == 'danado':
            # Verificar si ya existe multa por daño
            multa_dano = self.multas.filter(tipo='d').first()
            if not multa_dano:
                costo_dano = float(self.libro.costo) * 0.5
                Multa.objects.create(
                    prestamo=self,
                    tipo='d',
                    monto=costo_dano,
                    fecha=fecha_actual
                )
        
        # 3. MULTA POR RETRASO
        if fecha_actual > self.fecha_max:
            dias_retraso = (fecha_actual - self.fecha_max).days
            
            # Verificar si ya existe multa por retraso
            multa_retraso = self.multas.filter(tipo='r').first()
            if multa_retraso:
                # Actualizar el monto
                multa_retraso.monto = dias_retraso * 1.0
                multa_retraso.save()
            else:
                # Crear nueva multa
                Multa.objects.create(
                    prestamo=self,
                    tipo='r',
                    monto=dias_retraso * 1.0,
                    fecha=fecha_actual
                )
        
        # Actualizar estado del préstamo
        self.estado = 'd'
        
        # Restaurar disponibilidad del libro
        self.libro.disponible = True
        self.libro.save()
        
        self.save()
        
        # Calcular total de multas
        total_multas = sum(float(m.monto) for m in self.multas.all())
        
        if total_multas > 0:
            return f'Libro devuelto. Total multas: ${total_multas:.2f}'
        else:
            return 'Libro devuelto sin multas'
    
class Multa(models.Model):
    TIPOS = [
        ('r', 'Retraso'),
        ('p', 'Pérdida'),
        ('d', 'Deterioro'),
    ]

    prestamo = models.ForeignKey(Prestamo, related_name="multas", on_delete=models.PROTECT)
    tipo = models.CharField(max_length=1, choices=TIPOS)
    monto = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    pagada = models.BooleanField(default=False)
    fecha = models.DateField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Multas"

    def __str__(self):
        return f"Multa {self.get_tipo_display()} - ${self.monto} - {self.prestamo}"

    # ==================== VALIDADOR DE CÉDULA ====================
def validar_cedula_ecuatoriana(cedula):
    cedula = str(cedula).strip()
    
    if not cedula.isdigit() or len(cedula) != 10:
        raise ValidationError('Cédula inválida: debe tener 10 dígitos')
    
    provincia = int(cedula[0:2])
    if provincia < 1 or provincia > 24:
        raise ValidationError('Código de provincia inválido')
    
    # Algoritmo del dígito verificador
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0
    for i in range(9):
        producto = int(cedula[i]) * coeficientes[i]
        suma += producto - 9 if producto >= 10 else producto
    
    digito = 0 if suma % 10 == 0 else 10 - (suma % 10)
    
    if digito != int(cedula[9]):
        raise ValidationError('Cédula inválida')
    
    return True


# ==================== USUARIO BIBLIOTECA ====================
class UsuarioBiblioteca(models.Model):
    TIPOS = [('estudiante', 'Estudiante'), ('profesor', 'Profesor'), ('externo', 'Externo')]
    
    nombre = models.CharField(max_length=100)
    cedula = models.CharField(max_length=10, unique=True, validators=[validar_cedula_ecuatoriana])
    email = models.EmailField()
    tipo = models.CharField(max_length=20, choices=TIPOS, default='externo')
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.cedula})"