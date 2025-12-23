from django.db import models
from django.conf import settings
from django.utils import timezone

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

    libro = models.ForeignKey(Libro, related_name ="prestamos", on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name= "prestamos", on_delete=models.PROTECT)
    fecha_prestamos = models.DateField(default=timezone.now)
    fecha_max = models.DateField()
    fecha_devolucion= models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=1, choices=ESTADOS, default='b') 

    class Meta:
        permissions = (
            ("Ver_prestamos", "Puede ver prestaamos"),
            ("gestionar_prestamos", "Puede gestionar_prestamos"),
        )
        verbose_name_plural = "Préstamos"
    
    def __str__(self):
        return f"prestamo de{self.libro} {self.usuario}"
    
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
    
class Multa(models.Model):
    TIPOS = [
        ('r', 'Retraso'),
        ('p', 'Pérdida'),
        ('d', 'Deterioro'),
    ]

    prestamo= models.ForeignKey(Prestamo, related_name="multas", on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices= (('r', 'retraso'), ('p', 'perdida'), ('d', 'deterioro')))
    monto= models. DecimalField(max_digits=3, decimal_places=2, default=0)
    pagada= models.BooleanField(default= False)
    fecha = models.DateField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Multas"

    def __str__(self):
        return f"Multa{self.tipo} - {self.monto} - {self.prestamo}"
    

    def save(self, *args, **kwargs):
        if self.tipo == 'r' and self.monto == 0:
            self.monto = monto =self.prestamo.multa_retraso
        super().save(*args, **kwargs)

    

