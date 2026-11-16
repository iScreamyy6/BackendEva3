from django.db import models
from organizacion.models import Funcionario, Delegacion


class ItemMeta(models.Model):
    id_item = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, unique=True, verbose_name='Nombre del Ítem')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    tipo_meta = models.CharField(
        max_length=50,
        choices=[
            ('Cuantitativa', 'Cuantitativa (Numérica / Volumen)'),
            ('Cualitativa', 'Cualitativa (Hito / Cumplimiento)'),
        ],
        default='Cuantitativa',
        verbose_name='Tipo de Meta'
    )
    unidad_medida = models.CharField(
        max_length=120,
        default='Gestiones Verificadas',
        verbose_name='Unidad de Medida'
    )
    requisito_evidencia = models.CharField(
        max_length=200,
        default='Fotografía georreferenciada o Acta firmada',
        verbose_name='Requisito de Evidencia'
    )
    estado = models.CharField(
        max_length=20,
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')],
        default='Activo'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'items_metas'
        verbose_name = 'Ítem y Meta'
        verbose_name_plural = 'Ítems y Metas'
        ordering = ['codigo']

    @property
    def id(self):
        return self.pk

    def save(self, *args, **kwargs):
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"ITM-{self.pk:02d}"
            counter = self.pk
            while ItemMeta.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"ITM-{counter:02d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.codigo}] {self.nombre}"


class PeriodoEvaluacion(models.Model):
    id_periodo = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Código Trimestre')
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Trimestre')
    anio = models.IntegerField(default=2026, verbose_name='Año')
    numero = models.IntegerField(default=1, verbose_name='Número de Trimestre (1 a 4)')
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_cierre = models.DateField(verbose_name='Fecha de Término / Cierre')
    dias_totales = models.IntegerField(default=90)
    dias_transcurridos = models.IntegerField(default=89)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('Activo', 'Activo'),
            ('Cerrado', 'Cerrado'),
            ('Inactivo', 'Inactivo'),
        ],
        default='Activo',
        verbose_name='Estado'
    )
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'periodos_evaluacion'
        verbose_name = 'Trimestre / Período de Evaluación'
        verbose_name_plural = 'Trimestres / Períodos de Evaluación'
        ordering = ['-anio', '-numero', '-fecha_inicio']

    @property
    def id(self):
        return self.pk

    def save(self, *args, **kwargs):
        if self.estado in ('Cerrado', 'Inactivo'):
            self.activo = False
        elif self.estado == 'Activo':
            self.activo = True
        if self.fecha_inicio and self.fecha_cierre and hasattr(self.fecha_cierre, 'toordinal') and hasattr(self.fecha_inicio, 'toordinal'):
            diff = (self.fecha_cierre - self.fecha_inicio).days + 1
            if diff > 0:
                self.dias_totales = diff
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"TRI-{self.anio}-T{self.numero}-{self.pk:02d}"
            counter = self.pk
            while PeriodoEvaluacion.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"TRI-{self.anio}-T{self.numero}-{counter:02d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        cod = f"[{self.codigo}] " if self.codigo else ""
        return f"{cod}{self.nombre} ({self.estado})"


class MetaFuncionario(models.Model):
    id_meta = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=30, unique=True, blank=True, null=True, verbose_name='Código Asignación')
    id_item_meta = models.ForeignKey(
        ItemMeta,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name='asignaciones',
        verbose_name='Meta Asociada (Catálogo)'
    )
    id_funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        db_column='id_funcionario',
        related_name='metas',
        verbose_name='Funcionario Responsable'
    )
    id_periodo = models.ForeignKey(
        PeriodoEvaluacion,
        on_delete=models.RESTRICT,
        db_column='id_periodo',
        related_name='metas',
        null=True,
        blank=True,
        verbose_name='Trimestre / Período'
    )
    item = models.CharField(max_length=200, verbose_name='Ítem de Evaluación')
    ponderador = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Porcentaje de ponderación (ej: 25.00 para 25%)',
        verbose_name='Ponderación (%)'
    )
    meta_periodo = models.IntegerField(verbose_name='Cantidad Objetivo (Meta)')
    avance_actual = models.IntegerField(default=0, verbose_name='Avance Actual')
    porcentaje_cumplimiento = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    cumplimiento_ponderado = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    felicitaciones = models.IntegerField(default=0)
    reclamos = models.IntegerField(default=0)
    fecha_asignacion = models.DateField(null=True, blank=True, verbose_name='Fecha de Asignación')
    observacion = models.TextField(blank=True, default='', verbose_name='Observación')
    estado = models.CharField(
        max_length=20,
        choices=[('Activa', 'Activa'), ('Inactiva', 'Inactiva')],
        default='Activa',
        verbose_name='Estado'
    )

    class Meta:
        db_table = 'metas_funcionario'
        verbose_name = 'Asignación de Meta a Funcionario'
        verbose_name_plural = 'Asignaciones de Metas a Funcionarios'
        ordering = ['id_funcionario', 'item']

    @property
    def id(self):
        return self.pk

    # Alias para templates
    @property
    def funcionario(self):
        return self.id_funcionario

    @property
    def periodo(self):
        return self.id_periodo

    @property
    def item_meta(self):
        return self.id_item_meta

    def save(self, *args, **kwargs):
        if self.id_item_meta and not self.item:
            self.item = self.id_item_meta.nombre
        elif self.item and not self.id_item_meta:
            match = ItemMeta.objects.filter(nombre__iexact=self.item.strip()).first()
            if match:
                self.id_item_meta = match
        if self.meta_periodo and self.meta_periodo > 0:
            pct = (float(self.avance_actual or 0) / float(self.meta_periodo)) * 100.0
            self.porcentaje_cumplimiento = round(pct, 2)
            self.cumplimiento_ponderado = round((min(pct, 100.0) * float(self.ponderador or 0)) / 100.0, 2)
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"ASG-{self.pk:03d}"
            counter = self.pk
            while MetaFuncionario.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"ASG-{counter:03d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        cod = f"[{self.codigo}] " if self.codigo else ""
        return f"{cod}{self.id_funcionario.nombre} - {self.item}"


class IndicadorDelegacion(models.Model):
    id_indicador = models.AutoField(primary_key=True)
    id_delegacion = models.ForeignKey(
        Delegacion,
        on_delete=models.CASCADE,
        db_column='id_delegacion',
        related_name='indicadores'
    )
    id_periodo = models.ForeignKey(
        PeriodoEvaluacion,
        on_delete=models.RESTRICT,
        db_column='id_periodo',
        related_name='indicadores',
        null=True,
        blank=True
    )
    area = models.CharField(max_length=150)
    responsable = models.CharField(max_length=200)
    avance_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    estado_semaforo = models.CharField(
        max_length=10,
        choices=[
            ('verde', 'Verde (Óptimo ≥ 98.9%)'),
            ('amarillo', 'Amarillo (Alerta ≥ 60%)'),
            ('rojo', 'Rojo (Crítico < 60%)'),
        ],
        default='verde'
    )
    licencias = models.IntegerField(default=0)
    vacaciones = models.IntegerField(default=0)
    emergencias = models.IntegerField(default=0)
    compensatorios = models.IntegerField(default=0)

    class Meta:
        db_table = 'indicadores_delegacion'
        verbose_name = 'Indicador de Delegación'
        verbose_name_plural = 'Indicadores de Delegaciones'

    def __str__(self):
        return f"{self.area} - {self.responsable} ({self.estado_semaforo})"

    @property
    def id(self):
        return self.pk

    # Alias para templates
    @property
    def delegacion(self):
        return self.id_delegacion

    @property
    def avance(self):
        return float(self.avance_porcentaje)
