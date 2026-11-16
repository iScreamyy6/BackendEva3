from django.db import models
from django.contrib.auth.models import User, Group


class Delegacion(models.Model):
    id_delegacion = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, unique=True)
    direccion = models.CharField(max_length=250, blank=True, default='', verbose_name='Dirección')
    comuna = models.CharField(max_length=100, default='La Serena', verbose_name='Comuna')
    ambito = models.CharField(max_length=150, default='Territorial y Comunitario')
    responsable = models.CharField(max_length=200, verbose_name='Delegado / Responsable')
    delegado = models.ForeignKey(
        'Funcionario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delegaciones_a_cargo',
        verbose_name='Funcionario Delegado'
    )
    foco_estrategico = models.TextField(blank=True, null=True)
    estado = models.CharField(
        max_length=20,
        choices=[('Activa', 'Activa'), ('Inactiva', 'Inactiva')],
        default='Activa'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'delegaciones'
        verbose_name = 'Delegación'
        verbose_name_plural = 'Delegaciones'
        ordering = ['nombre']

    @property
    def id(self):
        return self.pk

    def save(self, *args, **kwargs):
        if self.delegado and not self.responsable:
            self.responsable = self.delegado.nombre
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"D{self.pk:02d}"
            counter = self.pk
            while Delegacion.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"D{counter:02d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        cod = f"[{self.codigo}] " if self.codigo else ""
        return f"{cod}{self.nombre}"


class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Código')
    nombre = models.CharField(max_length=150, unique=True, verbose_name='Nombre del Cargo')
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripción / Funciones')
    estado = models.CharField(
        max_length=20,
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')],
        default='Activo',
        verbose_name='Estado'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cargos_funcionarios'
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering = ['nombre']

    @property
    def id(self):
        return self.pk

    def save(self, *args, **kwargs):
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"CAR-{self.pk:02d}"
            counter = self.pk
            while Cargo.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"CAR-{counter:02d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        cod = f"[{self.codigo}] " if self.codigo else ""
        return f"{cod}{self.nombre}"


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Código')
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre del Rol')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    alcance_autorizado = models.CharField(
        max_length=30,
        choices=[
            ('COMUNAL', 'Comunal (Todas las delegaciones)'),
            ('DELEGACION', 'Por Delegación Asignada'),
        ],
        default='DELEGACION',
        verbose_name='Alcance Autorizado'
    )
    permisos = models.CharField(
        max_length=255,
        default='Listar, Consultar, Crear, Editar',
        verbose_name='Permisos y Alcance'
    )
    grupo_django = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roles_sgr',
        verbose_name='Grupo de Permisos Django'
    )
    estado = models.CharField(
        max_length=20,
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')],
        default='Activo'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['nombre']

    @property
    def id(self):
        return self.pk

    def save(self, *args, **kwargs):
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"ROL-{self.pk:02d}"
            counter = self.pk
            while Rol.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"ROL-{counter:02d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.codigo}] {self.nombre} ({self.get_alcance_autorizado_display()})"


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rut = models.CharField(max_length=20, blank=True, null=True, verbose_name='RUT Ficticio')
    cargo = models.ForeignKey(
        Cargo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfiles',
        verbose_name='Cargo'
    )
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, null=True, blank=True, related_name='usuarios')
    roles = models.ManyToManyField(
        Rol,
        blank=True,
        related_name='perfiles_asignados',
        verbose_name='Roles Asignados'
    )
    delegacion_activa = models.ForeignKey(
        Delegacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_activa',
        verbose_name='Delegación Principal / Activa'
    )
    delegaciones_autorizadas = models.ManyToManyField(
        Delegacion,
        blank=True,
        related_name='usuarios_autorizados',
        verbose_name='Delegaciones Autorizadas'
    )
    telefono = models.CharField(max_length=30, blank=True, null=True, verbose_name='Teléfono')
    estado = models.CharField(
        max_length=20,
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')],
        default='Activo'
    )
    # Control de recuperación de contraseña de 6 dígitos
    codigo_recuperacion = models.CharField(max_length=6, blank=True, null=True)
    codigo_expiracion = models.DateTimeField(null=True, blank=True)
    intentos_fallidos = models.IntegerField(default=0)
    codigo_usado = models.BooleanField(default=False)
    ultimo_reenvio = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'perfiles_usuarios'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'
        ordering = ['user__username']

    @property
    def id(self):
        return self.pk

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.rol.nombre if self.rol else 'Sin Rol'}"

    def delegaciones_disponibles(self):
        if self.rol and self.rol.alcance_autorizado == 'COMUNAL':
            return Delegacion.objects.filter(estado='Activa')
        return self.delegaciones_autorizadas.filter(estado='Activa')


class Funcionario(models.Model):
    id_funcionario = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='funcionario',
        verbose_name='Cuenta de Usuario'
    )
    id_delegacion = models.ForeignKey(
        Delegacion,
        on_delete=models.RESTRICT,
        db_column='id_delegacion',
        related_name='funcionarios',
        verbose_name='Delegación Principal'
    )
    rut = models.CharField(max_length=20, blank=True, null=True, verbose_name='RUT Ficticio')
    nombres = models.CharField(max_length=120, blank=True, default='', verbose_name='Nombres')
    apellidos = models.CharField(max_length=120, blank=True, default='', verbose_name='Apellidos')
    nombre = models.CharField(max_length=200, verbose_name='Nombre Completo')
    correo = models.EmailField(blank=True, null=True, verbose_name='Correo Institucional')
    telefono = models.CharField(max_length=30, blank=True, null=True, verbose_name='Teléfono')
    cargo_rel = models.ForeignKey(
        Cargo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='funcionarios',
        verbose_name='Cargo Asociado'
    )
    cargo = models.CharField(max_length=150)
    estado = models.CharField(
        max_length=20,
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')],
        default='Activo',
        verbose_name='Estado'
    )
    activo = models.BooleanField(default=True)
    fecha_ingreso = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'funcionarios'
        verbose_name = 'Funcionario'
        verbose_name_plural = 'Funcionarios'
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        if (self.nombres or self.apellidos) and not self.nombre:
            full = f"{self.nombres.strip()} {self.apellidos.strip()}".strip()
            if full:
                self.nombre = full
        elif self.nombre and not self.nombres:
            partes = self.nombre.strip().split(' ', 1)
            self.nombres = partes[0]
            self.apellidos = partes[1] if len(partes) > 1 else ''
        if self.cargo_rel and not self.cargo:
            self.cargo = self.cargo_rel.nombre
        if self.estado == 'Inactivo':
            self.activo = False
        elif self.estado == 'Activo':
            self.activo = True
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.cargo})"

    @property
    def id(self):
        return self.pk

    # Alias para compatibilidad con templates que usen .delegacion
    @property
    def delegacion(self):
        return self.id_delegacion


class CargoTipoGestion(models.Model):
    id_cargo_tipo = models.AutoField(primary_key=True)
    cargo = models.CharField(max_length=150, verbose_name='Cargo de Funcionario')
    id_tipo = models.ForeignKey(
        'actividades.TipoAtencion',
        on_delete=models.CASCADE,
        related_name='cargos_autorizados',
        db_column='id_tipo',
        verbose_name='Tipo de Atención / Gestión'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cargos_tipos_gestion'
        verbose_name = 'Mapeo Cargo - Tipo de Gestión'
        verbose_name_plural = 'Mapeos Cargo - Tipo de Gestión'
        unique_together = ('cargo', 'id_tipo')

    def __str__(self):
        return f"{self.cargo} -> {self.id_tipo.nombre}"


class Territorio(models.Model):
    id_territorio = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Territorio')
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripción / Sector')
    delegacion = models.ForeignKey(
        Delegacion,
        on_delete=models.RESTRICT,
        related_name='territorios',
        verbose_name='Delegación Asignada'
    )
    estado = models.CharField(
        max_length=20,
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')],
        default='Activo'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'territorios'
        verbose_name = 'Territorio / Sector'
        verbose_name_plural = 'Territorios / Sectores'
        ordering = ['delegacion__nombre', 'nombre']

    @property
    def id(self):
        return self.pk

    def save(self, *args, **kwargs):
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"TER-{self.pk:02d}"
            counter = self.pk
            while Territorio.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"TER-{counter:02d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        cod = f"[{self.codigo}] " if self.codigo else ""
        return f"{cod}{self.nombre} ({self.delegacion.nombre})"


class JuntaVecinos(models.Model):
    id_junta = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Código')
    nombre = models.CharField(max_length=250, unique=True, verbose_name='Nombre de la Junta de Vecinos')
    direccion = models.CharField(max_length=250, blank=True, default='', verbose_name='Dirección de Sede / Punto de Encuentro')
    delegacion = models.ForeignKey(
        Delegacion,
        on_delete=models.RESTRICT,
        related_name='juntas_vecinos',
        verbose_name='Delegación'
    )
    territorio = models.ForeignKey(
        Territorio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='juntas_vecinos',
        verbose_name='Territorio / Sector'
    )
    fecha_constitucion = models.DateField(null=True, blank=True, verbose_name='Fecha de Constitución')
    estado = models.CharField(
        max_length=20,
        choices=[('Activa', 'Activa'), ('Inactiva', 'Inactiva')],
        default='Activa'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'juntas_vecinos'
        verbose_name = 'Junta de Vecinos'
        verbose_name_plural = 'Juntas de Vecinos'
        ordering = ['nombre']

    @property
    def id(self):
        return self.pk

    def save(self, *args, **kwargs):
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"JJVV-{self.pk:02d}"
            counter = self.pk
            while JuntaVecinos.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"JJVV-{counter:02d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        cod = f"[{self.codigo}] " if self.codigo else ""
        return f"{cod}{self.nombre}"


class ParticipacionJunta(models.Model):
    CARGOS_DIRIGENTE = [
        ('Presidente/a', 'Presidente/a'),
        ('Secretario/a', 'Secretario/a'),
        ('Tesorero/a', 'Tesorero/a'),
        ('Primer Director/a', 'Primer Director/a'),
        ('Segundo Director/a', 'Segundo Director/a'),
        ('Socio/a Activo/a', 'Socio/a Activo/a'),
    ]

    id_participacion = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Código')
    vecino = models.ForeignKey(
        'actividades.Vecino',
        on_delete=models.CASCADE,
        related_name='participaciones_junta',
        verbose_name='Vecino'
    )
    junta = models.ForeignKey(
        JuntaVecinos,
        on_delete=models.CASCADE,
        related_name='dirigentes_socios',
        verbose_name='Junta de Vecinos'
    )
    es_dirigente = models.BooleanField(default=False, verbose_name='¿Es Dirigente Vecinal?')
    cargo = models.CharField(
        max_length=100,
        choices=CARGOS_DIRIGENTE,
        default='Socio/a Activo/a',
        verbose_name='Cargo en la Junta'
    )
    fecha_incorporacion = models.DateField(null=True, blank=True, verbose_name='Fecha de Incorporación')
    estado = models.CharField(
        max_length=20,
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')],
        default='Activo'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'participaciones_juntas'
        verbose_name = 'Participación Vecinal en Junta'
        verbose_name_plural = 'Participaciones Vecinales en Juntas'
        unique_together = ('vecino', 'junta')
        ordering = ['-es_dirigente', 'cargo', 'vecino__nombre']

    @property
    def id(self):
        return self.pk

    def save(self, *args, **kwargs):
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"PAR-{self.pk:02d}"
            counter = self.pk
            while ParticipacionJunta.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"PAR-{counter:02d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        tipo = f"[{self.cargo}]" if self.es_dirigente else "[Socio/a]"
        return f"{self.vecino.nombre} -> {self.junta.nombre} {tipo}"


class Hito(models.Model):
    PERIODICIDADES = [
        ('Único', 'Único (Evento puntual)'),
        ('Mensual', 'Mensual'),
        ('Trimestral', 'Trimestral'),
        ('Semestral', 'Semestral'),
        ('Anual', 'Anual'),
    ]
    ESTADOS = [
        ('Programado', 'Programado'),
        ('En Ejecución', 'En Ejecución'),
        ('Cumplido', 'Cumplido'),
        ('Inactivo', 'Inactivo'),
    ]

    id_hito = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Hito')
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripción / Objetivo')
    periodicidad = models.CharField(
        max_length=30,
        choices=PERIODICIDADES,
        default='Trimestral',
        verbose_name='Periodicidad'
    )
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_termino = models.DateField(verbose_name='Fecha de Término')
    delegacion = models.ForeignKey(
        Delegacion,
        on_delete=models.RESTRICT,
        related_name='hitos',
        verbose_name='Delegación'
    )
    territorio = models.ForeignKey(
        Territorio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hitos',
        verbose_name='Territorio Asociado'
    )
    responsable = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hitos_responsable',
        verbose_name='Funcionario Responsable Principal'
    )
    responsables = models.ManyToManyField(
        Funcionario,
        blank=True,
        related_name='hitos_equipo',
        verbose_name='Equipo Responsable'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='Programado',
        verbose_name='Estado'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hitos_territoriales'
        verbose_name = 'Hito'
        verbose_name_plural = 'Hitos'
        ordering = ['-fecha_inicio', 'nombre']

    @property
    def id(self):
        return self.pk

    def save(self, *args, **kwargs):
        if not self.codigo:
            kwargs.pop('force_insert', None)
            super().save(*args, **kwargs)
            cod = f"HIT-{self.pk:02d}"
            counter = self.pk
            while Hito.objects.filter(codigo=cod).exclude(pk=self.pk).exists():
                counter += 1
                cod = f"HIT-{counter:02d}"
            self.codigo = cod
            return super().save(update_fields=['codigo'])
        return super().save(*args, **kwargs)

    def __str__(self):
        cod = f"[{self.codigo}] " if self.codigo else ""
        return f"{cod}{self.nombre} ({self.delegacion.nombre})"



