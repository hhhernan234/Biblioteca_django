from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.

class Autor(models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    bibliografia= models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Libro(models.Model):
    titulo = models.CharField(max_length=20)
    autor = models.ForeignKey(Autor, related_name = "libros", on_delete=models.PROTECT)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo

class Prestamo(models.Model):
    libro = models.ForeignKey(Libro, related_name ="prestamos", on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name= "prestamos", on_delete=models.PROTECT)
    fecha_prestamos = models.DateField(default=timezone.now)
    fecha_max = models.DateField()
    fecha_devolucion= models.DateField(blank=True, null=True)

    class Meta:
        permissions = (
            ("Ver_prestamos", "Puede ver prestaamos"),
            ("gestionar_prestamos", "Puede gestionar_prestamos"),
        )
    
    def __str__(self):
        return f"prestamo de{self.libro} {self.usuario}"
    
    @property
    def dias_retraso(self):
        hoy= timezone.now().date()
        fecha_ref = self.fecha_devolucion or hoy
        if fecha_ref > self.fecha_max:
            return(fecha_ref - self.fecha_max).days
        return 0
    
    @property
    def multa_retraso(self):
        tarifa =0.50
        return self.dias_retraso * tarifa
    
class Multa(models.Model):
    prestamo= models.ForeignKey(Prestamo, related_name="multas", on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices= (('r', 'retraso'), ('p', 'perdida'), ('d', 'deterioro')))
    monto= models. DecimalField(max_digits=3, decimal_places=2, default=0)
    pagada= models.BooleanField(default= False)
    fecha = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Multa{self.tipo} - {self.monto} - {self.prestamo}"
    

    def save(self, *args, **kwargs):
        if self.tipo == 'r' and self.monto == 0:
            self.monto = monto =self.prestamo.multa_retraso
        super().save(*args, **kwargs)

    

