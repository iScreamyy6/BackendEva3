from django.db import models
from django.contrib.auth.models import User
from organizacion.models import Funcionario, Delegacion, Territorio, Hito


class Vecino(models.Model):
    id_vecino = models.AutoField(primary_key=True)
    rut = models.CharField(max_length=20, unique=True, verbose_name='RUT')
    nombres = models.CharField(max_length=120, blank=True, default='', verbose_name='Nombres')
    apellidos = models.CharField(max_length=120, blank=True, default='', verbose_name='Apellidos')
    nombre = models.CharField(max_length=200, verbose_name='Nombre Completo')
    telefono = models.CharField(max_length=30, blank=True, null=True, verbose_name='Teléfono')
    correo = models.EmailField(blank=True, null=True, verbose_name='Correo Electrónico')
    direccion = models.CharField(max_length=250, blank=True, null=True, verbose_name='Dirección / Sector')
    territorio_rel = models.ForeignKey(
        Territorio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vecinos_sector',
        verbose_name='Territorio Asociado'
    )
    territorio = models.CharField(max_length=200, blank=True, null=True, verbose_name='Territorio / Sector')
    estado = models.CharField(
        max_length=20,
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')],
        default='Activo',
        verbose_name='Estado'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')

    class Meta:
        db_table = 'vecinos'
        verbose_name = 'Vecino / Solicitante'
        verbose_name_plural = 'Vecinos / Solicitantes'
        ordering = ['nombre']

    @property
    def id(self):
        return self.pk

    def save(self, *args, **kwargs):
        if (self.nombres or self.apellidos) and not self.nombre:
            full = f"{self.nombres.strip()} {self.apellidos.strip()}".strip()
            if full:
                self.nombre = full
        elif self.nombre and not self.nombres:
            partes = self.nombre.strip().split(' ', 1)
            self.nombres = partes[0]
            self.apellidos = partes[1] if len(partes) > 1 else ''
        if self.territorio_rel and not self.territorio:
            self.territorio = self.territorio_rel.nombre
        elif self.territorio and not self.territorio_rel:
            t_match = Territorio.objects.filter(nombre__iexact=self.territorio.strip()).first()
            if t_match:
                self.territorio_rel = t_match
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.rut} - {self.nombre}"



class Actividad(models.Model):
    ORIGENES = [
        ('Requerimiento Vecinal', 'Requerimiento Vecinal / Atención'),
        ('Terreno', 'Despliegue en Terreno'),
        ('Pauta Interna', 'Pauta Interna / Operativo'),
        ('Tubo de Trabajo', 'Derivación / Tubo de Trabajo'),
        ('Coordinación Territorial', 'Coordinación Territorial'),
    ]

    id_actividad = models.AutoField(primary_key=True)
    id_gestion_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column='id_gestion_padre',
        related_name='subgestiones',
        verbose_name='Gestión Principal / Padre'
    )
    codigo = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Código de Gestión'
    )
    usuario_creador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades_creadas',
        verbose_name='Usuario Creador'
    )
    id_funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.RESTRICT,
        db_column='id_funcionario',
        related_name='actividades',
        verbose_name='Funcionario Registrador'
    )
    responsable_funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades_responsable',
        verbose_name='Funcionario Responsable'
    )
    id_delegacion = models.ForeignKey(
        Delegacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_delegacion',
        related_name='actividades_delegacion',
        verbose_name='Delegación'
    )
    territorio_rel = models.ForeignKey(
        Territorio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades_territorio',
        verbose_name='Territorio Asociado'
    )
    fecha = models.DateField(verbose_name='Fecha de Actividad')
    origen = models.CharField(
        max_length=50,
        choices=ORIGENES,
        default='Requerimiento Vecinal',
        verbose_name='Origen de la Actividad'
    )

    # Solicitante / Vecino (unificado)
    id_vecino = models.ForeignKey(
        'Vecino',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_vecino',
        related_name='actividades',
        verbose_name='Vecino / Solicitante'
    )
    solicitante = models.CharField(max_length=200, blank=True, null=True, verbose_name='Solicitante / Vecino')
    rut_solicitante = models.CharField(max_length=20, blank=True, null=True, verbose_name='RUT')
    telefono = models.CharField(max_length=30, blank=True, null=True, verbose_name='Teléfono')
    correo = models.EmailField(blank=True, null=True, verbose_name='Correo Electrónico')
    direccion = models.CharField(max_length=250, blank=True, null=True, verbose_name='Dirección / Sector')
    territorio = models.CharField(max_length=200, blank=True, null=True, verbose_name='Territorio / Sector')
    contacto = models.CharField(max_length=200, blank=True, null=True)

    # Clasificación en catálogo
    id_tipo = models.ForeignKey(
        'TipoAtencion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_tipo',
        related_name='actividades_clasificadas',
        verbose_name='Tipo de Atención'
    )
    id_subatencion = models.ForeignKey(
        'SubAtencion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_subatencion',
        related_name='actividades_clasificadas',
        verbose_name='Subtipo de Atención'
    )

    # Asociación con Asignación de Meta e Hito
    asignacion_meta = models.ForeignKey(
        'resultados.MetaFuncionario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades_asociadas',
        verbose_name='Asignación de Meta Asociada'
    )
    hito = models.ForeignKey(
        Hito,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades_hito',
        verbose_name='Hito Territorial (Opcional)'
    )

    # Requerimiento y acción
    solicitud = models.TextField(verbose_name='Solicitud / Problema / Requerimiento')
    accion = models.CharField(max_length=300, verbose_name='Acción Realizada')
    responsable = models.CharField(max_length=200, verbose_name='Responsable')
    item_evaluacion = models.CharField(max_length=200, verbose_name='Ítem de Evaluación')
    avance = models.IntegerField(default=100, verbose_name='Porcentaje de Avance (%)')
    resultado = models.CharField(max_length=255, blank=True, default='Gestión ejecutada satisfactoriamente', verbose_name='Resultado Obtenido')

    # Derivación a Tubo de Trabajo y Enlaces
    ingreso_tubo = models.BooleanField(default=False, verbose_name='¿Derivado a Tubo de Trabajo?')
    id_compromiso = models.ForeignKey(
        'agenda.Compromiso',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_compromiso',
        related_name='gestion_origen',
        verbose_name='Compromiso en Tubo'
    )
    id_atencion = models.ForeignKey(
        'AtencionCiudadana',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_atencion',
        related_name='actividades_vinculadas',
        verbose_name='Atención Ciudadana de Origen'
    )
    id_gestion_social = models.ForeignKey(
        'GestionSocial',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_gestion_social',
        related_name='actividades_vinculadas',
        verbose_name='Gestión Social de Origen'
    )
    fecha_limite_tubo = models.DateField(null=True, blank=True, verbose_name='Fecha Compromiso / Límite Tubo')
    area_apoyo_tubo = models.CharField(max_length=200, blank=True, null=True, verbose_name='Área de Apoyo Tubo')

    # Especialización para Gestor Social
    es_gestion_social = models.BooleanField(default=False, verbose_name='¿Es Gestión Social?')
    requiere_visita = models.BooleanField(default=False, verbose_name='¿Requiere Visita en Terreno?')
    fecha_programada_visita = models.DateField(blank=True, null=True, verbose_name='Fecha Programada Visita')
    observaciones_sociales = models.TextField(blank=True, null=True, verbose_name='Observaciones / Diagnóstico Social')
    primera_gestion = models.CharField(max_length=200, blank=True, null=True, verbose_name='1ª Gestión Social')
    segunda_gestion = models.CharField(max_length=200, blank=True, null=True, verbose_name='2ª Gestión Social')
    fecha_visita = models.DateField(blank=True, null=True, verbose_name='Fecha Visita Realizada')
    fecha_entrega_informe = models.DateField(blank=True, null=True, verbose_name='Fecha Entrega Informe')
    tercera_gestion = models.CharField(max_length=200, blank=True, null=True, verbose_name='3ª Gestión Social')
    fecha_entrega_beneficio = models.DateField(blank=True, null=True, verbose_name='Fecha Entrega Beneficio')

    # Estado y verificación
    estado = models.CharField(
        max_length=30,
        choices=[
            ('Pendiente', 'Pendiente'),
            ('En Proceso', 'En Proceso'),
            ('Realizado', 'Realizado'),
            ('Inactivo', 'Inactivo'),
        ],
        default='Pendiente'
    )
    codigo_evidencia = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Código de Evidencia'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'actividades'
        verbose_name = 'Actividad / Gestión'
        verbose_name_plural = 'Actividades y Gestiones'
        ordering = ['-fecha', '-id_actividad']

    def save(self, *args, **kwargs):
        if self.id_vecino and not self.solicitante:
            self.solicitante = self.id_vecino.nombre
            self.rut_solicitante = self.id_vecino.rut
        if not self.contacto and self.solicitante:
            self.contacto = self.solicitante
        elif not self.solicitante and self.contacto:
            self.solicitante = self.contacto
        if self.territorio_rel and not self.territorio:
            self.territorio = self.territorio_rel.nombre
        if self.responsable_funcionario and not self.responsable:
            self.responsable = self.responsable_funcionario.nombre
        elif not self.responsable and self.id_funcionario_id:
            self.responsable = self.id_funcionario.nombre
        if self.asignacion_meta and not self.item_evaluacion:
            self.item_evaluacion = self.asignacion_meta.item

        if not self.codigo or not self.codigo_evidencia:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            updates = []
            if not self.codigo:
                if self.id_gestion_padre:
                    padre_cod = self.id_gestion_padre.codigo or f"GES-{self.id_gestion_padre.pk:05d}"
                    num_sub = self.id_gestion_padre.subgestiones.exclude(pk=self.pk).count() + 1
                    cod = f"{padre_cod}-S{num_sub:02d}"
                else:
                    prefijo = "SOC" if self.es_gestion_social else "GES"
                    cod = f"{prefijo}-{self.pk:05d}"
                counter = self.pk
                while Actividad.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                    counter += 1
                    cod = f"GES-{counter:05d}"
                self.codigo = cod
                updates.append('codigo')
            if not self.codigo_evidencia:
                if isinstance(self.fecha, str):
                    fecha_str = self.fecha.replace('-', '')
                elif hasattr(self.fecha, 'strftime'):
                    fecha_str = self.fecha.strftime('%Y%m%d')
                else:
                    fecha_str = '2026'
                cod_ev = f"EVI-{fecha_str}-{self.pk:04d}"
                counter = self.pk
                while Actividad.objects.filter(codigo_evidencia=cod_ev).exclude(pk=self.pk).exists():
                    counter += 1
                    cod_ev = f"EVI-{fecha_str}-{counter:04d}"
                self.codigo_evidencia = cod_ev
                updates.append('codigo_evidencia')
            if updates:
                super().save(update_fields=updates)
            return
        return super().save(*args, **kwargs)

    def __str__(self):
        cod = f"[{self.codigo}] " if self.codigo else ""
        return f"{cod}{self.fecha} - {self.solicitud[:50]}"

    @property
    def id(self):
        return self.pk

    @property
    def es_subgestion(self):
        return bool(self.id_gestion_padre_id)

    @property
    def cantidad_subgestiones(self):
        return self.subgestiones.count()

    # Alias para templates
    @property
    def funcionario(self):
        return self.id_funcionario


class Evidencia(models.Model):
    TIPOS_ARCHIVO = [
        ('Fotografía JPG/PNG', 'Fotografía Georreferenciada (JPG/PNG)'),
        ('Acta PDF', 'Acta de Reunión / Compromiso (PDF)'),
        ('Informe Social PDF', 'Informe Social Técnico (PDF)'),
        ('Planilla de Asistencia', 'Listado / Planilla de Asistencia'),
        ('Comprobante de Entrega', 'Comprobante de Entrega de Beneficio'),
    ]

    id_evidencia = models.AutoField(primary_key=True)
    id_actividad = models.ForeignKey(
        Actividad,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column='id_actividad',
        related_name='evidencias',
        verbose_name='Actividad de Origen'
    )
    id_gestion_social = models.ForeignKey(
        'GestionSocial',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='evidencias_sociales',
        verbose_name='Gestión Social de Origen'
    )
    id_funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_funcionario',
        related_name='evidencias_subidas',
        verbose_name='Cargado por (Funcionario)'
    )
    verificador = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evidencias_verificadas',
        verbose_name='Verificador (Funcionario)'
    )
    codigo = models.CharField(max_length=50, unique=True, blank=True, verbose_name='Código de Evidencia')
    archivo_ruta = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nombre / Referencia de Archivo')
    tipo_archivo = models.CharField(
        max_length=60,
        choices=TIPOS_ARCHIVO,
        default='Fotografía JPG/PNG',
        verbose_name='Tipo de Archivo / Medio'
    )
    fecha_evidencia = models.DateField(null=True, blank=True, verbose_name='Fecha de la Evidencia')
    imagen = models.ImageField(
        upload_to='evidencias/',
        null=True,
        blank=True,
        verbose_name='Imagen de Evidencia (Opcional)'
    )
    imagen_verificada = models.BooleanField(default=False)
    verificador_valido = models.BooleanField(default=False)
    resultado = models.IntegerField(default=0)
    estado_validacion = models.CharField(
        max_length=20,
        choices=[
            ('Pendiente', 'Pendiente'),
            ('Aprobada', 'Aprobada'),
            ('Rechazada', 'Rechazada'),
            ('Corregir', 'Requiere Correción'),
            ('Inactiva', 'Inactiva'),
        ],
        default='Pendiente',
        verbose_name='Estado de Validación'
    )
    observacion = models.TextField(blank=True, null=True, verbose_name='Descripción / Observación')
    fecha_carga = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'evidencias'
        verbose_name = 'Evidencia'
        verbose_name_plural = 'Evidencias'
        ordering = ['-fecha_carga']

    def save(self, *args, **kwargs):
        if not self.fecha_evidencia:
            if self.id_actividad and self.id_actividad.fecha:
                self.fecha_evidencia = self.id_actividad.fecha
            elif self.id_gestion_social and self.id_gestion_social.fecha_ingreso:
                self.fecha_evidencia = self.id_gestion_social.fecha_ingreso
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"EVI-DOC-{self.pk:04d}"
            counter = self.pk
            while Evidencia.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"EVI-DOC-{counter:04d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Evidencia {self.codigo}"

    @property
    def id(self):
        return self.pk

    # Alias para compatibilidad con templates
    @property
    def actividad(self):
        return self.id_actividad

    @property
    def actividad_solicitud(self):
        if self.id_actividad:
            return self.id_actividad.solicitud
        if self.id_gestion_social:
            return self.id_gestion_social.observaciones
        return ''

    @property
    def actividad_resumen(self):
        if self.id_actividad:
            return self.id_actividad.accion
        if self.id_gestion_social:
            return self.id_gestion_social.primera_gestion
        return ''

    @property
    def fecha(self):
        if self.fecha_evidencia and hasattr(self.fecha_evidencia, 'strftime'):
            return self.fecha_evidencia.strftime('%d/%m/%Y')
        if self.id_actividad and self.id_actividad.fecha:
            return self.id_actividad.fecha.strftime('%d/%m/%Y')
        if self.id_gestion_social and self.id_gestion_social.fecha_ingreso:
            return self.id_gestion_social.fecha_ingreso.strftime('%d/%m/%Y')
        return ''

    @property
    def archivo_nombre(self):
        return self.archivo_ruta or 'Sin archivo adjunto'

    @property
    def responsable(self):
        if self.id_funcionario:
            return self.id_funcionario.nombre
        if self.id_actividad and self.id_actividad.responsable:
            return self.id_actividad.responsable
        if self.id_gestion_social and self.id_gestion_social.id_funcionario:
            return self.id_gestion_social.id_funcionario.nombre
        return 'No asignado'

    @property
    def accion(self):
        if self.id_actividad:
            return self.id_actividad.accion
        if self.id_gestion_social:
            return self.id_gestion_social.primera_gestion
        return '—'

    @property
    def item_evaluacion(self):
        if self.id_actividad:
            return self.id_actividad.item_evaluacion
        if self.id_gestion_social:
            return 'INFORMES SOCIALES'
        return 'General'

    @property
    def contacto(self):
        if self.id_actividad:
            return self.id_actividad.contacto or self.id_actividad.solicitante
        if self.id_gestion_social:
            return self.id_gestion_social.usuario
        return ''

    @property
    def telefono(self):
        if self.id_actividad:
            return self.id_actividad.telefono
        if self.id_gestion_social:
            return self.id_gestion_social.telefono
        return ''

    @property
    def estado(self):
        return self.estado_validacion

    @property
    def observaciones(self):
        return self.observacion or ''


class TipoAtencion(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Código')
    nombre = models.CharField(max_length=150, unique=True, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    estado = models.CharField(
        max_length=20,
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')],
        default='Activo'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tipos_atencion'
        verbose_name = 'Tipo de Atención'
        verbose_name_plural = 'Tipos de Atención'
        ordering = ['nombre']

    @property
    def id(self):
        return self.pk

    def save(self, *args, **kwargs):
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"TIP-{self.pk:02d}"
            counter = self.pk
            while TipoAtencion.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"TIP-{counter:02d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.codigo}] {self.nombre}"


class SubAtencion(models.Model):
    id_subatencion = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Código')
    id_tipo = models.ForeignKey(
        TipoAtencion,
        on_delete=models.RESTRICT,
        db_column='id_tipo',
        related_name='subatenciones',
        verbose_name='Tipo de Atención'
    )
    nombre = models.CharField(max_length=150, verbose_name='Nombre')
    estado = models.CharField(
        max_length=20,
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')],
        default='Activo'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sub_atenciones'
        verbose_name = 'Sub Atención'
        verbose_name_plural = 'Sub Atenciones'
        ordering = ['id_tipo__nombre', 'nombre']
        unique_together = ('id_tipo', 'nombre')

    @property
    def id(self):
        return self.pk

    @property
    def tipo(self):
        return self.id_tipo

    def save(self, *args, **kwargs):
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"SUB-{self.pk:02d}"
            counter = self.pk
            while SubAtencion.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"SUB-{counter:02d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.codigo}] {self.nombre} ({self.id_tipo.nombre})"


class AtencionCiudadana(models.Model):
    id_atencion = models.AutoField(primary_key=True)
    folio = models.CharField(max_length=30, unique=True, verbose_name='Folio')
    id_vecino = models.ForeignKey(
        Vecino,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_vecino',
        related_name='atenciones',
        verbose_name='Vecino'
    )
    solicitante = models.CharField(max_length=200, verbose_name='Solicitante')
    rut_solicitante = models.CharField(max_length=20, blank=True, null=True, verbose_name='RUT')
    telefono = models.CharField(max_length=30, blank=True, null=True, verbose_name='Teléfono')
    correo = models.EmailField(blank=True, null=True, verbose_name='Correo')
    direccion = models.CharField(max_length=250, blank=True, null=True, verbose_name='Dirección')
    id_tipo = models.ForeignKey(
        TipoAtencion,
        on_delete=models.RESTRICT,
        db_column='id_tipo',
        related_name='atenciones',
        verbose_name='Tipo de Atención'
    )
    id_subatencion = models.ForeignKey(
        SubAtencion,
        on_delete=models.RESTRICT,
        db_column='id_subatencion',
        related_name='atenciones',
        verbose_name='Sub Atención'
    )
    descripcion = models.TextField(verbose_name='Descripción del Requerimiento')
    id_delegacion = models.ForeignKey(
        Delegacion,
        on_delete=models.RESTRICT,
        db_column='id_delegacion',
        related_name='atenciones_ciudadanas',
        verbose_name='Delegación'
    )
    id_usuario_responsable = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        db_column='id_usuario',
        related_name='atenciones_ingresadas',
        verbose_name='Usuario Responsable'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    estado = models.CharField(
        max_length=30,
        choices=[
            ('Ingresada', 'Ingresada'),
            ('En Tramite', 'En Trámite'),
            ('Derivada', 'Derivada'),
            ('Resuelta', 'Resuelta'),
            ('Cerrada', 'Cerrada'),
        ],
        default='Ingresada'
    )

    class Meta:
        db_table = 'atenciones_ciudadanas'
        verbose_name = 'Atención Ciudadana'
        verbose_name_plural = 'Atenciones Ciudadanas'
        ordering = ['-fecha_registro']

    @property
    def id(self):
        return self.pk

    @property
    def tipo(self):
        return self.id_tipo

    @property
    def subatencion(self):
        return self.id_subatencion

    @property
    def delegacion(self):
        return self.id_delegacion

    @property
    def usuario_responsable(self):
        return self.id_usuario_responsable

    def save(self, *args, **kwargs):
        if not self.folio:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            self.folio = f"ATC-{self.pk:05d}"
            return super().save(update_fields=['folio'])
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.folio or f'ATC-{self.pk}'} - {self.solicitante}"


class GestionSocial(models.Model):
    id_gestion_social = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=30, unique=True, blank=True, null=True, verbose_name='Código Social')
    fecha_ingreso = models.DateField(verbose_name='Fecha de Ingreso')
    fecha_atencion = models.DateField(null=True, blank=True, verbose_name='Fecha de Atención')

    id_tipo = models.ForeignKey(
        TipoAtencion,
        on_delete=models.RESTRICT,
        db_column='id_tipo',
        related_name='gestiones_sociales',
        verbose_name='Tipo de Atención Social'
    )
    id_subatencion = models.ForeignKey(
        SubAtencion,
        on_delete=models.RESTRICT,
        db_column='id_subatencion',
        related_name='gestiones_sociales',
        verbose_name='Subtipo de Atención Social'
    )

    beneficiario_vecino = models.ForeignKey(
        Vecino,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gestiones_sociales_vecino',
        verbose_name='Beneficiario / Vecino Asociado'
    )
    usuario = models.CharField(max_length=200, verbose_name='Nombre del Usuario / Beneficiario')
    rut = models.CharField(max_length=20, blank=True, null=True, verbose_name='RUT')
    telefono = models.CharField(max_length=30, blank=True, null=True, verbose_name='Teléfono')
    direccion = models.CharField(max_length=250, blank=True, null=True, verbose_name='Dirección / Sector')

    derivacion = models.CharField(
        max_length=200,
        blank=True,
        default='Atención Directa Delegación',
        verbose_name='Derivación / Origen Social'
    )
    requiere_visita = models.BooleanField(default=False, verbose_name='¿Requiere Visita en Terreno?')
    fecha_programada_visita = models.DateField(blank=True, null=True, verbose_name='Fecha Programada Visita')
    ingreso_tubo = models.BooleanField(default=False, verbose_name='¿Ingreso al Tubo de Trabajo?')
    observaciones = models.TextField(verbose_name='Observaciones del Caso / Situación Social')
    informe_detalle = models.TextField(blank=True, default='', verbose_name='Detalle de Informe Social')
    beneficio_entregado = models.CharField(max_length=200, blank=True, default='', verbose_name='Beneficio o Ayuda Entregada')

    # Flujo multi-etapa de gestiones del Gestor Social
    primera_gestion = models.CharField(
        max_length=200,
        default='ATENCIÓN SOCIAL A USUARIO PRESENCIAL',
        verbose_name='Primera Gestión'
    )
    segunda_gestion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Segunda Gestión'
    )
    fecha_visita = models.DateField(blank=True, null=True, verbose_name='Fecha de Visita Realizada')
    fecha_entrega_informe = models.DateField(blank=True, null=True, verbose_name='Fecha Entrega Informe')

    tercera_gestion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Tercera Gestión'
    )
    fecha_entrega_beneficio = models.DateField(blank=True, null=True, verbose_name='Fecha Entrega Beneficio')

    id_funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.RESTRICT,
        db_column='id_funcionario',
        related_name='gestiones_sociales',
        verbose_name='Gestor Social Responsable'
    )
    id_delegacion = models.ForeignKey(
        Delegacion,
        on_delete=models.RESTRICT,
        db_column='id_delegacion',
        related_name='gestiones_sociales',
        verbose_name='Delegación'
    )
    asignacion_meta = models.ForeignKey(
        'resultados.MetaFuncionario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gestiones_sociales_asociadas',
        verbose_name='Asignación de Meta Asociada'
    )

    estado = models.CharField(
        max_length=30,
        choices=[
            ('Ingresada', 'Ingresada'),
            ('En Proceso', 'En Proceso'),
            ('Visita Pendiente', 'Visita Pendiente'),
            ('Informe Entregado', 'Informe Entregado'),
            ('Resuelta', 'Resuelta'),
            ('Cerrada', 'Cerrada'),
            ('Inactiva', 'Inactiva'),
        ],
        default='Ingresada'
    )
    imagen_verificada = models.BooleanField(default=False, verbose_name='Imagen Verificada')
    verificador_valido = models.IntegerField(default=1, verbose_name='Verificador Válido')
    resultado = models.IntegerField(default=1, verbose_name='Resultado Numérico')
    resultado_texto = models.CharField(
        max_length=255,
        blank=True,
        default='Atención social registrada y verificada',
        verbose_name='Resultado del Caso'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gestiones_sociales'
        verbose_name = 'Gestión Social'
        verbose_name_plural = 'Gestiones Sociales'
        ordering = ['-fecha_ingreso', '-id_gestion_social']

    @property
    def id(self):
        return self.pk

    @property
    def tipo(self):
        return self.id_tipo

    @property
    def subatencion(self):
        return self.id_subatencion

    @property
    def delegacion(self):
        return self.id_delegacion

    @property
    def funcionario(self):
        return self.id_funcionario

    def save(self, *args, **kwargs):
        if not self.fecha_atencion and self.fecha_ingreso:
            self.fecha_atencion = self.fecha_ingreso
        if self.beneficiario_vecino and not self.usuario:
            self.usuario = self.beneficiario_vecino.nombre
            self.rut = self.beneficiario_vecino.rut
        if self.tercera_gestion and not self.beneficio_entregado:
            self.beneficio_entregado = self.tercera_gestion
        elif self.beneficio_entregado and not self.tercera_gestion:
            self.tercera_gestion = self.beneficio_entregado
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"SOC-{self.pk:05d}"
            counter = self.pk
            while GestionSocial.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"SOC-{counter:05d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        cod = f"[{self.codigo}] " if self.codigo else ""
        return f"{cod}{self.usuario} - {self.primera_gestion}"
