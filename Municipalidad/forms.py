import re
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from organizacion.models import (
    Delegacion, Territorio, Cargo, Rol, PerfilUsuario,
    JuntaVecinos, ParticipacionJunta, Hito
)
from actividades.models import (
    Vecino, Actividad, GestionSocial, TipoAtencion, SubAtencion, Evidencia
)
from resultados.models import (
    ItemMeta, MetaFuncionario, PeriodoEvaluacion
)


def validar_formato_rut(rut_valor):
    """Valida formato básico de RUT chileno ficticio (ej. 12.345.678-9 o 12345678-K)."""
    if not rut_valor:
        return rut_valor
    limpio = rut_valor.strip().upper()
    if len(limpio) < 3 or not re.match(r'^[0-9.\-]+[\-]?[0-9K]$', limpio):
        raise ValidationError('Ingrese un RUT válido (ej: 12.345.678-9).')
    return limpio


class DelegacionForm(forms.ModelForm):
    class Meta:
        model = Delegacion
        fields = [
            'codigo', 'nombre', 'direccion', 'comuna',
            'ambito', 'responsable', 'delegado', 'foco_estrategico', 'estado'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['responsable'].required = False
        self.fields['ambito'].required = False
        self.fields['comuna'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = Delegacion.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya está registrado en otra delegación.')
            return codigo
        return None

    def clean(self):
        cleaned = super().clean()
        nombre = (cleaned.get('nombre') or '').strip()
        if not nombre:
            self.add_error('nombre', 'El nombre de la delegación es obligatorio.')
        delegado = cleaned.get('delegado')
        responsable = (cleaned.get('responsable') or '').strip()
        if not delegado and not responsable:
            self.add_error('responsable', 'Debe indicar un funcionario delegado o el nombre del responsable.')
        elif delegado and not responsable:
            cleaned['responsable'] = delegado.nombre
        if not cleaned.get('ambito'):
            cleaned['ambito'] = 'Territorial y Comunitario'
        if not cleaned.get('comuna'):
            cleaned['comuna'] = 'La Serena'
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activa'
        return cleaned


class TerritorioForm(forms.ModelForm):
    class Meta:
        model = Territorio
        fields = ['codigo', 'nombre', 'descripcion', 'delegacion', 'estado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = Territorio.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya está asignado a otro territorio.')
            return codigo
        return None

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            raise ValidationError('El nombre del territorio es obligatorio.')
        return nombre

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activo'
        return cleaned


class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = ['codigo', 'nombre', 'descripcion', 'estado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = Cargo.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya pertenece a otro cargo.')
            return codigo
        return None

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            raise ValidationError('El nombre del cargo es obligatorio.')
        qs = Cargo.objects.filter(nombre__iexact=nombre)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f'Ya existe un cargo con el nombre "{nombre}".')
        return nombre

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activo'
        return cleaned


class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['codigo', 'nombre', 'descripcion', 'alcance_autorizado', 'permisos', 'estado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['alcance_autorizado'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = Rol.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya pertenece a otro rol.')
            return codigo
        return None

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            raise ValidationError('El nombre del rol es obligatorio.')
        qs = Rol.objects.filter(nombre__iexact=nombre)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f'Ya existe un rol con el nombre "{nombre}".')
        return nombre

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('alcance_autorizado'):
            cleaned['alcance_autorizado'] = 'DELEGACION'
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activo'
        return cleaned


class UsuarioFuncionarioForm(forms.ModelForm):
    """
    ModelForm sobre PerfilUsuario que gestiona de forma segura el Usuario Django
    y su Funcionario asociado, sin exponer is_superuser ni is_staff.
    """
    username = forms.CharField(max_length=150, required=True, label='Nombre de Usuario')
    first_name = forms.CharField(max_length=150, required=True, label='Nombres')
    last_name = forms.CharField(max_length=150, required=True, label='Apellidos')
    email = forms.EmailField(required=True, label='Correo Electrónico Institucional')
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        label='Contraseña'
    )
    cargo_texto = forms.CharField(max_length=150, required=False, label='Nombre del Cargo (Texto)')

    class Meta:
        model = PerfilUsuario
        fields = [
            'rut', 'cargo', 'rol', 'roles',
            'delegacion_activa', 'delegaciones_autorizadas',
            'telefono', 'estado'
        ]

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        self.fields['rol'].required = False
        self.fields['delegacion_activa'].required = False
        self.fields['estado'].required = False
        if self.user_instance and self.user_instance.pk:
            self.fields['username'].initial = self.user_instance.username
            self.fields['first_name'].initial = self.user_instance.first_name
            self.fields['last_name'].initial = self.user_instance.last_name
            self.fields['email'].initial = self.user_instance.email
        else:
            self.fields['password'].required = True

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise ValidationError('El nombre de usuario es obligatorio.')
        qs = User.objects.filter(username__iexact=username)
        if self.user_instance and self.user_instance.pk:
            qs = qs.exclude(pk=self.user_instance.pk)
        if qs.exists():
            raise ValidationError(f'El nombre de usuario "{username}" ya existe.')
        return username

    def clean_rut(self):
        rut = validar_formato_rut(self.cleaned_data.get('rut'))
        if rut:
            qs = PerfilUsuario.objects.filter(rut__iexact=rut)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El RUT "{rut}" ya está registrado en otro funcionario.')
        return rut

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activo'
        rol = cleaned.get('rol')
        # Evitar autoasignación de rol Administrador si el usuario actual no es superuser/Administrador
        if rol and 'admin' in rol.nombre.lower() and 'administrativo' not in rol.nombre.lower():
            if self.request_user and not self.request_user.is_superuser:
                perfil_req = getattr(self.request_user, 'perfil', None)
                rol_req = perfil_req.rol.nombre.lower() if (perfil_req and perfil_req.rol) else ''
                if 'administrador' not in rol_req:
                    self.add_error('rol', 'No tiene privilegios para asignar el rol de Administrador.')
        return cleaned


class VecinoForm(forms.ModelForm):
    class Meta:
        model = Vecino
        fields = [
            'rut', 'nombres', 'apellidos', 'nombre',
            'telefono', 'correo', 'direccion',
            'territorio_rel', 'territorio', 'estado'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = False
        self.fields['nombres'].required = False
        self.fields['apellidos'].required = False
        self.fields['estado'].required = False

    def clean_rut(self):
        rut = validar_formato_rut(self.cleaned_data.get('rut'))
        if not rut:
            raise ValidationError('El RUT del vecino es obligatorio.')
        qs = Vecino.objects.filter(rut__iexact=rut)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f'Ya existe un vecino registrado con el RUT "{rut}".')
        return rut

    def clean(self):
        cleaned = super().clean()
        nombres = (cleaned.get('nombres') or '').strip()
        apellidos = (cleaned.get('apellidos') or '').strip()
        nombre = (cleaned.get('nombre') or '').strip()
        if not nombre and not (nombres or apellidos):
            self.add_error('nombre', 'Debe ingresar el nombre completo o los nombres y apellidos del vecino.')
        elif (nombres or apellidos) and not str(self.data.get('nombre', '')).strip():
            cleaned['nombre'] = f"{nombres} {apellidos}".strip()
        elif nombre:
            if not str(self.data.get('nombres', '')).strip():
                partes = nombre.split(' ', 1)
                cleaned['nombres'] = partes[0]
                cleaned['apellidos'] = partes[1] if len(partes) > 1 else ''
            elif nombres or apellidos:
                cleaned['nombre'] = f"{nombres} {apellidos}".strip()
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activo'
        return cleaned


class JuntaVecinosForm(forms.ModelForm):
    class Meta:
        model = JuntaVecinos
        fields = [
            'codigo', 'nombre', 'direccion',
            'delegacion', 'territorio', 'fecha_constitucion', 'estado'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = JuntaVecinos.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya está asignado a otra junta de vecinos.')
            return codigo
        return None

    def clean(self):
        cleaned = super().clean()
        delegacion = cleaned.get('delegacion')
        territorio = cleaned.get('territorio')
        if delegacion and territorio and territorio.delegacion_id != delegacion.id_delegacion:
            self.add_error(
                'territorio',
                f'El territorio "{territorio.nombre}" no pertenece a la delegación "{delegacion.nombre}".'
            )
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activa'
        return cleaned


class ParticipacionJuntaForm(forms.ModelForm):
    class Meta:
        model = ParticipacionJunta
        fields = [
            'codigo', 'vecino', 'junta',
            'es_dirigente', 'cargo', 'fecha_incorporacion', 'estado'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['fecha_incorporacion'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = ParticipacionJunta.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya está asignado a otra participación.')
            return codigo
        return None

    def clean(self):
        cleaned = super().clean()
        vecino = cleaned.get('vecino')
        junta = cleaned.get('junta')
        if vecino and junta:
            qs = ParticipacionJunta.objects.filter(vecino=vecino, junta=junta)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('vecino', 'Este vecino ya registra participación en la junta seleccionada.')
        if str(self.data.get('es_dirigente', '')).upper() in ('NO', '0', 'FALSE', ''):
            if 'es_dirigente' in self.data and str(self.data.get('es_dirigente')).upper() in ('NO', '0', 'FALSE'):
                cleaned['es_dirigente'] = False
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activo'
        return cleaned


class HitoForm(forms.ModelForm):
    class Meta:
        model = Hito
        fields = [
            'codigo', 'nombre', 'descripcion', 'periodicidad',
            'fecha_inicio', 'fecha_termino',
            'delegacion', 'territorio', 'responsable', 'responsables', 'estado'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['periodicidad'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = Hito.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya pertenece a otro hito.')
            return codigo
        return None

    def clean(self):
        cleaned = super().clean()
        fecha_inicio = cleaned.get('fecha_inicio')
        fecha_termino = cleaned.get('fecha_termino')
        if fecha_inicio and fecha_termino and fecha_termino < fecha_inicio:
            self.add_error(
                'fecha_termino',
                'La fecha de término debe ser igual o posterior a la fecha de inicio del hito.'
            )
        delegacion = cleaned.get('delegacion')
        territorio = cleaned.get('territorio')
        if delegacion and territorio and territorio.delegacion_id != delegacion.id_delegacion:
            self.add_error(
                'territorio',
                f'El territorio "{territorio.nombre}" no pertenece a la delegación "{delegacion.nombre}".'
            )
        if not cleaned.get('periodicidad'):
            cleaned['periodicidad'] = 'Único'
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Programado'
        return cleaned


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = [
            'codigo', 'id_gestion_padre', 'id_funcionario', 'responsable_funcionario',
            'id_delegacion', 'territorio_rel', 'fecha', 'origen',
            'id_vecino', 'solicitante', 'rut_solicitante', 'telefono', 'correo', 'direccion', 'territorio',
            'id_tipo', 'id_subatencion', 'asignacion_meta', 'hito',
            'solicitud', 'accion', 'responsable', 'item_evaluacion', 'avance', 'resultado',
            'ingreso_tubo', 'fecha_limite_tubo', 'area_apoyo_tubo',
            'es_gestion_social', 'requiere_visita', 'fecha_programada_visita',
            'observaciones_sociales', 'primera_gestion', 'segunda_gestion',
            'fecha_visita', 'fecha_entrega_informe', 'tercera_gestion',
            'fecha_entrega_beneficio', 'estado'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['id_funcionario'].required = False
        self.fields['responsable'].required = False
        self.fields['item_evaluacion'].required = False
        self.fields['avance'].required = False
        self.fields['origen'].required = False
        self.fields['resultado'].required = False
        self.fields['fecha'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = Actividad.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya está registrado en otra actividad.')
            return codigo
        return None

    def clean_avance(self):
        avance = self.cleaned_data.get('avance')
        if avance is None:
            return 100
        if avance < 0 or avance > 100:
            raise ValidationError('El porcentaje de avance debe estar entre 0 y 100.')
        return avance

    def clean(self):
        cleaned = super().clean()
        fecha = cleaned.get('fecha')
        fecha_limite = cleaned.get('fecha_limite_tubo')
        fecha_prog_visita = cleaned.get('fecha_programada_visita')
        fecha_visita = cleaned.get('fecha_visita')

        if fecha and fecha_limite and fecha_limite < fecha:
            self.add_error(
                'fecha_limite_tubo',
                'La fecha de compromiso / límite tubo no puede ser anterior a la fecha de la actividad.'
            )
        if fecha and fecha_prog_visita and fecha_prog_visita < fecha:
            self.add_error(
                'fecha_programada_visita',
                'La fecha programada de visita no puede ser anterior a la fecha de la actividad.'
            )
        if fecha and fecha_visita and fecha_visita < fecha:
            self.add_error(
                'fecha_visita',
                'La fecha de visita realizada no puede ser anterior a la fecha de la actividad.'
            )

        id_tipo = cleaned.get('id_tipo')
        id_subatencion = cleaned.get('id_subatencion')
        if id_tipo and id_subatencion and id_subatencion.id_tipo_id != id_tipo.id_tipo:
            self.add_error(
                'id_subatencion',
                f'El subtipo "{id_subatencion.nombre}" no pertenece al tipo de atención "{id_tipo.nombre}".'
            )

        id_delegacion = cleaned.get('id_delegacion')
        territorio_rel = cleaned.get('territorio_rel')
        if id_delegacion and territorio_rel and territorio_rel.delegacion_id != id_delegacion.id_delegacion:
            self.add_error(
                'territorio_rel',
                f'El territorio "{territorio_rel.nombre}" no pertenece a la delegación "{id_delegacion.nombre}".'
            )

        for bool_field in ('ingreso_tubo', 'es_gestion_social', 'requiere_visita'):
            raw_val = str(self.data.get(bool_field, '')).strip().upper()
            if raw_val in ('NO', '0', 'FALSE'):
                cleaned[bool_field] = False
            elif raw_val in ('SI', 'SÍ', '1', 'TRUE', 'ON'):
                cleaned[bool_field] = True

        if not cleaned.get('origen'):
            cleaned['origen'] = 'Requerimiento Vecinal'
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Realizado'
        return cleaned


class GestionSocialForm(forms.ModelForm):
    class Meta:
        model = GestionSocial
        fields = [
            'codigo', 'fecha_ingreso', 'fecha_atencion',
            'id_tipo', 'id_subatencion',
            'beneficiario_vecino', 'usuario', 'rut', 'telefono', 'direccion',
            'derivacion', 'requiere_visita', 'fecha_programada_visita',
            'ingreso_tubo', 'observaciones', 'informe_detalle', 'beneficio_entregado',
            'primera_gestion', 'segunda_gestion', 'fecha_visita',
            'fecha_entrega_informe', 'tercera_gestion', 'fecha_entrega_beneficio',
            'id_funcionario', 'id_delegacion', 'asignacion_meta',
            'estado', 'resultado_texto'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['usuario'].required = False
        self.fields['primera_gestion'].required = False
        self.fields['fecha_ingreso'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = GestionSocial.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya pertenece a otra gestión social.')
            return codigo
        return None

    def clean(self):
        cleaned = super().clean()
        fecha_ingreso = cleaned.get('fecha_ingreso')
        fecha_atencion = cleaned.get('fecha_atencion')
        fecha_prog = cleaned.get('fecha_programada_visita')
        fecha_visita = cleaned.get('fecha_visita')
        fecha_informe = cleaned.get('fecha_entrega_informe')
        fecha_beneficio = cleaned.get('fecha_entrega_beneficio')

        if fecha_ingreso and fecha_atencion and fecha_atencion < fecha_ingreso:
            self.add_error('fecha_atencion', 'La fecha de atención no puede ser anterior a la fecha de ingreso.')
        if fecha_ingreso and fecha_prog and fecha_prog < fecha_ingreso:
            self.add_error('fecha_programada_visita', 'La fecha programada de visita no puede ser anterior a la fecha de ingreso.')
        if fecha_ingreso and fecha_visita and fecha_visita < fecha_ingreso:
            self.add_error('fecha_visita', 'La fecha de visita no puede ser anterior a la fecha de ingreso.')
        if fecha_ingreso and fecha_informe and fecha_informe < fecha_ingreso:
            self.add_error('fecha_entrega_informe', 'La fecha de entrega de informe no puede ser anterior a la fecha de ingreso.')
        if fecha_ingreso and fecha_beneficio and fecha_beneficio < fecha_ingreso:
            self.add_error('fecha_entrega_beneficio', 'La fecha de entrega de beneficio no puede ser anterior a la fecha de ingreso.')

        id_tipo = cleaned.get('id_tipo')
        id_subatencion = cleaned.get('id_subatencion')
        if id_tipo and id_subatencion and id_subatencion.id_tipo_id != id_tipo.id_tipo:
            self.add_error(
                'id_subatencion',
                f'El subtipo "{id_subatencion.nombre}" no pertenece al tipo de atención "{id_tipo.nombre}".'
            )

        beneficiario = cleaned.get('beneficiario_vecino')
        usuario = (cleaned.get('usuario') or '').strip()
        if not beneficiario and not usuario:
            self.add_error('usuario', 'Debe indicar el vecino beneficiario o el nombre del usuario atendido.')
        elif beneficiario and not usuario:
            cleaned['usuario'] = beneficiario.nombre
            if not cleaned.get('rut'):
                cleaned['rut'] = beneficiario.rut

        for bool_field in ('requiere_visita', 'ingreso_tubo'):
            raw_val = str(self.data.get(bool_field, '')).strip().upper()
            if raw_val in ('NO', '0', 'FALSE'):
                cleaned[bool_field] = False
            elif raw_val in ('SI', 'SÍ', '1', 'TRUE', 'ON'):
                cleaned[bool_field] = True

        if not cleaned.get('primera_gestion'):
            cleaned['primera_gestion'] = 'ATENCIÓN SOCIAL A USUARIO PRESENCIAL'
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Pendiente'
        return cleaned


class TipoAtencionForm(forms.ModelForm):
    class Meta:
        model = TipoAtencion
        fields = ['codigo', 'nombre', 'descripcion', 'estado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = TipoAtencion.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya pertenece a otro tipo de atención.')
            return codigo
        return None

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activo'
        return cleaned


class SubAtencionForm(forms.ModelForm):
    class Meta:
        model = SubAtencion
        fields = ['codigo', 'id_tipo', 'nombre', 'estado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = SubAtencion.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya pertenece a otro subtipo de atención.')
            return codigo
        return None

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activo'
        return cleaned


class ItemMetaForm(forms.ModelForm):
    class Meta:
        model = ItemMeta
        fields = [
            'codigo', 'nombre', 'descripcion',
            'tipo_meta', 'unidad_medida', 'requisito_evidencia', 'estado'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['unidad_medida'].required = False
        self.fields['requisito_evidencia'].required = False
        self.fields['tipo_meta'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = ItemMeta.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya pertenece a otra meta.')
            return codigo
        return None

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('unidad_medida'):
            cleaned['unidad_medida'] = 'Gestiones Verificadas'
        if not cleaned.get('requisito_evidencia'):
            cleaned['requisito_evidencia'] = 'Fotografía georreferenciada o Acta firmada'
        if not cleaned.get('tipo_meta'):
            cleaned['tipo_meta'] = 'Cuantitativa'
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activo'
        return cleaned


class MetaFuncionarioForm(forms.ModelForm):
    class Meta:
        model = MetaFuncionario
        fields = [
            'codigo', 'id_item_meta', 'item', 'id_funcionario', 'id_periodo',
            'meta_periodo', 'ponderador', 'avance_actual',
            'fecha_asignacion', 'observacion', 'estado'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['item'].required = False
        self.fields['avance_actual'].required = False
        self.fields['fecha_asignacion'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = MetaFuncionario.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya pertenece a otra asignación de meta.')
            return codigo
        return None

    def clean_meta_periodo(self):
        meta_periodo = self.cleaned_data.get('meta_periodo')
        if meta_periodo is None or meta_periodo <= 0:
            raise ValidationError('La cantidad objetivo (meta del período) debe ser mayor a 0.')
        return meta_periodo

    def clean_ponderador(self):
        ponderador = self.cleaned_data.get('ponderador')
        if ponderador is None or ponderador < 0 or ponderador > 100:
            raise ValidationError('La ponderación debe estar entre 0 y 100%.')
        return ponderador

    def clean(self):
        cleaned = super().clean()
        id_item_meta = cleaned.get('id_item_meta')
        item = (cleaned.get('item') or '').strip()
        if not id_item_meta and not item:
            self.add_error('id_item_meta', 'Debe seleccionar una meta del catálogo o indicar el ítem de evaluación.')
        elif id_item_meta and not item:
            cleaned['item'] = id_item_meta.nombre
        if cleaned.get('avance_actual') is None:
            cleaned['avance_actual'] = 0
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activa'
        return cleaned


class EvidenciaForm(forms.ModelForm):
    class Meta:
        model = Evidencia
        fields = [
            'codigo', 'id_actividad', 'id_gestion_social',
            'archivo_ruta', 'tipo_archivo', 'observacion',
            'fecha_evidencia', 'id_funcionario', 'verificador',
            'estado_validacion', 'imagen', 'imagen_verificada', 'verificador_valido', 'resultado'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['imagen'].required = False
        self.fields['resultado'].required = False
        self.fields['tipo_archivo'].required = False
        self.fields['fecha_evidencia'].required = False
        self.fields['estado_validacion'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = Evidencia.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya está registrado en otra evidencia.')
            return codigo
        return ''

    def clean(self):
        cleaned = super().clean()
        id_actividad = cleaned.get('id_actividad')
        id_gestion_social = cleaned.get('id_gestion_social')
        if not id_actividad and not id_gestion_social:
            self.add_error('id_actividad', 'La evidencia debe estar asociada a una Actividad o a una Gestión Social.')
        elif id_actividad and id_gestion_social:
            self.add_error('id_gestion_social', 'La evidencia debe asociarse a un único origen (Actividad o Gestión Social, no ambos).')

        archivo_ruta = (cleaned.get('archivo_ruta') or '').strip()
        imagen = cleaned.get('imagen')
        if not archivo_ruta and not imagen:
            self.add_error('archivo_ruta', 'Debe indicar el nombre o referencia del archivo de evidencia.')
        elif imagen and not archivo_ruta:
            cleaned['archivo_ruta'] = getattr(imagen, 'name', 'evidencia_adjunta.jpg')

        if not cleaned.get('tipo_archivo'):
            cleaned['tipo_archivo'] = 'Fotografía JPG/PNG'
        if not cleaned.get('estado_validacion'):
            cleaned['estado_validacion'] = 'Pendiente'
        if cleaned.get('resultado') is None:
            cleaned['resultado'] = 1 if cleaned.get('estado_validacion') == 'Aprobada' else 0
        return cleaned


class PeriodoEvaluacionForm(forms.ModelForm):
    class Meta:
        model = PeriodoEvaluacion
        fields = [
            'codigo', 'nombre', 'anio', 'numero',
            'fecha_inicio', 'fecha_cierre', 'estado'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['estado'].required = False

    def clean_codigo(self):
        codigo = (self.cleaned_data.get('codigo') or '').strip().upper()
        if codigo:
            qs = PeriodoEvaluacion.objects.filter(codigo__iexact=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código "{codigo}" ya pertenece a otro trimestre.')
            return codigo
        return None

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        if numero is None or numero < 1 or numero > 4:
            raise ValidationError('El número de trimestre debe estar entre 1 y 4.')
        return numero

    def clean(self):
        cleaned = super().clean()
        fecha_inicio = cleaned.get('fecha_inicio')
        fecha_cierre = cleaned.get('fecha_cierre')
        if fecha_inicio and fecha_cierre and fecha_cierre < fecha_inicio:
            self.add_error(
                'fecha_cierre',
                'La fecha de término / cierre debe ser igual o posterior a la fecha de inicio del trimestre.'
            )
        if not cleaned.get('estado'):
            cleaned['estado'] = 'Activo'
        return cleaned
