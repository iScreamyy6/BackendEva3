from django.utils import timezone
from organizacion.models import Delegacion, PerfilUsuario


class EmptyValues:
    """Objeto centinela compatible con Django 6.x: devuelve string vacío
    para cualquier atributo o clave que se intente acceder en un template.
    Evita VariableDoesNotExist cuando un formulario se abre en modo edición o creación sin valores previos.
    """
    def __getattr__(self, name):
        return ''

    def __getitem__(self, key):
        return ''

    def get(self, key, default=''):
        return default


class ObjetoTodasDelegaciones:
    """Objeto centinela para representar el ámbito global 'Todas las Delegaciones' (Comunal)."""
    pk = 'TODAS'
    id = 0
    id_delegacion = 0
    codigo = 'COMUNAL'
    nombre = 'Todas las Delegaciones'
    estado = 'Activa'
    es_todas = True

    def __str__(self):
        return self.nombre

    def __int__(self):
        return 0

    def __bool__(self):
        return True

    def __eq__(self, other):
        if isinstance(other, ObjetoTodasDelegaciones):
            return True
        if other in ('TODAS', 'todas', 0, '0'):
            return True
        return False


def delegacion_context(request):
    hoy_str = timezone.now().date().strftime('%Y-%m-%d')
    if not request.user.is_authenticated:
        return {
            'delegacion_activa': None,
            'delegaciones_disponibles': Delegacion.objects.none(),
            'puede_cambiar_delegacion': False,
            'es_todas_delegaciones': False,
            'usuario_perfil': None,
            'rol_usuario': None,
            'valores': EmptyValues(),
            'datos': EmptyValues(),
            'hoy': hoy_str,
        }

    perfil = getattr(request.user, 'perfil', None)
    if not perfil:
        perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)

    # Determinar delegaciones autorizadas según perfil
    if perfil.rol and perfil.rol.alcance_autorizado == 'COMUNAL':
        delegaciones_disponibles = Delegacion.objects.filter(estado='Activa')
    elif perfil.delegaciones_autorizadas.exists():
        delegaciones_disponibles = perfil.delegaciones_autorizadas.filter(estado='Activa')
    else:
        delegaciones_disponibles = Delegacion.objects.filter(estado='Activa')

    delegacion_activa_id = request.session.get('delegacion_activa_id')
    es_todas = str(delegacion_activa_id).strip().upper() in ('TODAS', '0')
    delegacion_activa = None

    if es_todas:
        delegacion_activa = ObjetoTodasDelegaciones()
    elif delegacion_activa_id:
        delegacion_activa = Delegacion.objects.filter(pk=delegacion_activa_id, estado='Activa').first()

    if not delegacion_activa and not es_todas:
        if perfil.delegacion_activa and perfil.delegacion_activa.estado == 'Activa':
            delegacion_activa = perfil.delegacion_activa
        else:
            delegacion_activa = delegaciones_disponibles.first()
        if delegacion_activa:
            request.session['delegacion_activa_id'] = delegacion_activa.pk

    # Determinar Nivel de Acceso y Perfil Oficial (Administrador, Gestión, Supervisor, Consulta, Administrativo)
    es_admin = bool(
        request.user.is_superuser or
        request.user.groups.filter(name='Administrador').exists() or
        (perfil.rol and perfil.rol.codigo == 'ROL-ADM')
    )
    es_gestion = bool(
        request.user.groups.filter(name__in=['Gestión', 'Gestion']).exists() or
        (perfil.rol and perfil.rol.codigo == 'ROL-GEST')
    )
    es_consulta = bool(
        request.user.groups.filter(name='Consulta').exists() or
        (perfil.rol and perfil.rol.codigo == 'ROL-CON')
    )
    es_super = bool(
        es_admin or
        es_gestion or
        request.user.groups.filter(name='Supervisor').exists() or
        (perfil.rol and perfil.rol.codigo in ('ROL-COORD', 'ROL-DEL'))
    )
    es_adminis = request.user.is_authenticated and not es_consulta

    if es_admin:
        perfil_tier_nombre = 'Administrador'
    elif es_gestion:
        perfil_tier_nombre = 'Gestión'
    elif es_consulta:
        perfil_tier_nombre = 'Consulta'
    elif es_super:
        perfil_tier_nombre = 'Supervisor'
    else:
        perfil_tier_nombre = 'Administrativo'

    grupo_principal = request.user.groups.first().name if request.user.groups.exists() else perfil_tier_nombre
    puede_gestionar = bool(es_admin or es_gestion or (es_super and not es_consulta))
    puede_ver_mantenedores = bool(es_admin or es_gestion or es_super or es_consulta)
    puede_gestionar_usuarios = bool(es_admin or es_gestion)

    return {
        'delegacion_activa': delegacion_activa,
        'delegaciones_disponibles': delegaciones_disponibles,
        'puede_cambiar_delegacion': delegaciones_disponibles.count() > 1 or es_admin or es_super or es_consulta,
        'es_todas_delegaciones': es_todas,
        'usuario_perfil': perfil,
        'rol_usuario': perfil.rol,
        'es_administrador': es_admin,
        'es_gestion': es_gestion,
        'es_consulta': es_consulta,
        'es_supervisor': es_super,
        'es_administrativo': es_adminis,
        'puede_gestionar': puede_gestionar,
        'puede_ver_mantenedores': puede_ver_mantenedores,
        'puede_gestionar_usuarios': puede_gestionar_usuarios,
        'perfil_tier_nombre': perfil_tier_nombre,
        'grupo_usuario_nombre': grupo_principal,
        'valores': EmptyValues(),
        'datos': EmptyValues(),
        'hoy': hoy_str,
    }
