import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse

from organizacion.models import (
    Delegacion, Rol, PerfilUsuario, Funcionario,
    Territorio, JuntaVecinos, ParticipacionJunta, Cargo, Hito
)
from actividades.models import (
    TipoAtencion, SubAtencion, AtencionCiudadana, Actividad,
    Vecino, GestionSocial, Evidencia
)
from resultados.models import ItemMeta, MetaFuncionario, PeriodoEvaluacion
from .forms import (
    DelegacionForm, TerritorioForm, CargoForm, RolForm,
    UsuarioFuncionarioForm, VecinoForm, JuntaVecinosForm,
    ParticipacionJuntaForm, HitoForm, TipoAtencionForm,
    SubAtencionForm, ItemMetaForm, MetaFuncionarioForm,
    PeriodoEvaluacionForm
)


class EmptyValues:
    """Objeto centinela compatible con Django 6.x: devuelve string vacío
    para cualquier atributo o clave no presente cuando se accede en un template.
    """
    def __init__(self, data=None):
        self._data = data or {}

    def __getattr__(self, name):
        if name == '_data':
            return {}
        return self._data.get(name, '')

    def __getitem__(self, key):
        return self._data.get(key, '')

    def get(self, key, default=''):
        return self._data.get(key, default)


# ==============================================================================
# HELPER DE EXPORTACIÓN EXCEL INSTITUCIONAL
# ==============================================================================
def generar_excel_institucional(titulo_hoja, filename, columnas, filas):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = titulo_hoja

    fill_header = PatternFill(start_color="AD0000", end_color="AD0000", fill_type="solid")
    font_header = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="Arial", size=10)

    ws.append(columnas)
    for col_idx in range(1, len(columnas) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = fill_header
        cell.font = font_header
        cell.alignment = Alignment(horizontal="center", vertical="center")
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = 22

    for row_idx, fila in enumerate(filas, start=2):
        ws.append(fila)
        for col_idx in range(1, len(fila) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = font_data

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    wb.save(response)
    return response


# ==============================================================================
# HELPERS DE SEGURIDAD Y PERMISOS POR ROL / GRUPO DJANGO
# ==============================================================================
def mapear_rol_a_grupo(rol):
    if not rol:
        return Group.objects.filter(name='Administrativo').first()
    if rol.grupo_django:
        return rol.grupo_django
    if rol.codigo == 'ROL-ADM':
        return Group.objects.filter(name='Administrador').first()
    if rol.codigo == 'ROL-GEST':
        return Group.objects.filter(name__in=['Gestión', 'Gestion']).first()
    if rol.codigo == 'ROL-CON':
        return Group.objects.filter(name='Consulta').first()
    if rol.codigo in ('ROL-COORD', 'ROL-DEL', 'ROL-VERIF'):
        return Group.objects.filter(name='Supervisor').first()
    return Group.objects.filter(name='Administrativo').first()


def es_consulta(user):
    if not user.is_authenticated:
        return False
    if user.groups.filter(name='Consulta').exists():
        return True
    perfil = getattr(user, 'perfil', None)
    return bool(perfil and perfil.rol and perfil.rol.codigo == 'ROL-CON')


def es_gestion(user):
    if not user.is_authenticated:
        return False
    if user.groups.filter(name__in=['Gestión', 'Gestion']).exists():
        return True
    perfil = getattr(user, 'perfil', None)
    return bool(perfil and perfil.rol and perfil.rol.codigo == 'ROL-GEST')


def es_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.groups.filter(name='Administrador').exists():
        return True
    perfil = getattr(user, 'perfil', None)
    return bool(perfil and perfil.rol and perfil.rol.codigo == 'ROL-ADM')


def es_admin_o_gestion(user):
    return es_admin(user) or es_gestion(user)


def es_admin_o_coord(user):
    if not user.is_authenticated:
        return False
    if es_admin_o_gestion(user):
        return True
    if user.groups.filter(name='Supervisor').exists():
        return True
    perfil = getattr(user, 'perfil', None)
    return bool(perfil and perfil.rol and perfil.rol.codigo in ('ROL-ADM', 'ROL-GEST', 'ROL-COORD', 'ROL-DEL', 'ROL-VERIF'))


def puede_consultar_mantenedor(user, solo_admin=False):
    if not user.is_authenticated:
        return False
    if es_consulta(user) or es_gestion(user) or es_admin(user):
        return True
    if not solo_admin and es_admin_o_coord(user):
        return True
    return False


def puede_escribir_mantenedor(user, solo_admin=False):
    if not user.is_authenticated or es_consulta(user):
        return False
    if es_admin(user) or es_gestion(user):
        return True
    if not solo_admin and es_admin_o_coord(user):
        return True
    return False


def respuesta_403(request, mensaje=None):
    msg = mensaje or 'Acceso restringido: Su perfil de rol no tiene permisos para ejecutar esta acción.'
    messages.error(request, msg)
    return render(request, '403.html', {'mensaje': msg}, status=403)


def reportar_errores_form(request, form):
    for campo, lista_errores in form.errors.items():
        etiqueta = form.fields[campo].label if campo in form.fields and form.fields[campo].label else campo
        for err in lista_errores:
            if campo == '__all__':
                messages.error(request, f'{err}')
            else:
                messages.error(request, f'{etiqueta}: {err}')


# ==============================================================================
# PANEL CONSOLIDADO DE LOS 17 MANTENEDORES SGR
# ==============================================================================
@login_required(login_url='login')
def mantenedores_inicio(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido al módulo de mantenedores.')

    entidades_17 = [
        {
            'num': 1, 'nombre': 'Delegación', 'modelo': 'organizacion.Delegacion',
            'total': Delegacion.objects.count(),
            'activos': Delegacion.objects.filter(estado='Activa').count(),
            'inactivos': Delegacion.objects.filter(estado='Inactiva').count(),
            'url_lista': 'delegaciones_lista', 'url_crear': 'delegaciones_crear',
            'descripcion': 'Unidades territoriales municipales, dirección, comuna y delegado.'
        },
        {
            'num': 2, 'nombre': 'Territorio', 'modelo': 'organizacion.Territorio',
            'total': Territorio.objects.count(),
            'activos': Territorio.objects.filter(estado='Activo').count(),
            'inactivos': Territorio.objects.filter(estado='Inactivo').count(),
            'url_lista': 'territorios_lista', 'url_crear': 'territorios_crear',
            'descripcion': 'Sectores y polígonos territoriales asociados a cada delegación.'
        },
        {
            'num': 3, 'nombre': 'Usuario Funcionario', 'modelo': 'auth.User + PerfilUsuario',
            'total': User.objects.count(),
            'activos': PerfilUsuario.objects.filter(estado='Activo').count(),
            'inactivos': PerfilUsuario.objects.filter(estado='Inactivo').count(),
            'url_lista': 'usuarios_lista', 'url_crear': 'usuarios_crear',
            'descripcion': 'Cuentas de funcionarios, RUT ficticio, cargo, delegación, roles y último acceso.'
        },
        {
            'num': 4, 'nombre': 'Cargo', 'modelo': 'organizacion.Cargo',
            'total': Cargo.objects.count(),
            'activos': Cargo.objects.filter(estado='Activo').count(),
            'inactivos': Cargo.objects.filter(estado='Inactivo').count(),
            'url_lista': 'cargos_lista', 'url_crear': 'cargos_crear',
            'descripcion': 'Catálogo institucional de cargos y funciones de funcionarios.'
        },
        {
            'num': 5, 'nombre': 'Rol', 'modelo': 'organizacion.Rol',
            'total': Rol.objects.count(),
            'activos': Rol.objects.filter(estado='Activo').count(),
            'inactivos': Rol.objects.filter(estado='Inactivo').count(),
            'url_lista': 'roles_lista', 'url_crear': 'roles_crear',
            'descripcion': 'Perfiles de acceso, alcance territorial y asociación con grupos Django.'
        },
        {
            'num': 6, 'nombre': 'Vecino', 'modelo': 'actividades.Vecino',
            'total': Vecino.objects.count(),
            'activos': Vecino.objects.filter(estado='Activo').count(),
            'inactivos': Vecino.objects.filter(estado='Inactivo').count(),
            'url_lista': 'vecinos_lista', 'url_crear': 'vecinos_crear',
            'descripcion': 'Padrón ciudadano con RUT ficticio, nombres, apellidos y territorio asociado.'
        },
        {
            'num': 7, 'nombre': 'Junta de Vecinos', 'modelo': 'organizacion.JuntaVecinos',
            'total': JuntaVecinos.objects.count(),
            'activos': JuntaVecinos.objects.filter(estado='Activa').count(),
            'inactivos': JuntaVecinos.objects.filter(estado='Inactiva').count(),
            'url_lista': 'juntas_vecinos_lista', 'url_crear': 'juntas_vecinos_crear',
            'descripcion': 'Organizaciones comunitarias territoriales asociadas a delegación y territorio.'
        },
        {
            'num': 8, 'nombre': 'Participación en Junta', 'modelo': 'organizacion.ParticipacionJunta',
            'total': ParticipacionJunta.objects.count(),
            'activos': ParticipacionJunta.objects.filter(estado='Activo').count(),
            'inactivos': ParticipacionJunta.objects.filter(estado='Inactivo').count(),
            'url_lista': 'participaciones_lista', 'url_crear': 'participaciones_crear',
            'descripcion': 'Vínculo entre vecinos y juntas de vecinos (dirigentes y socios).'
        },
        {
            'num': 9, 'nombre': 'Hito', 'modelo': 'organizacion.Hito',
            'total': Hito.objects.count(),
            'activos': Hito.objects.exclude(estado='Inactivo').count(),
            'inactivos': Hito.objects.filter(estado='Inactivo').count(),
            'url_lista': 'hitos_lista', 'url_crear': 'hitos_crear',
            'descripcion': 'Hitos territoriales programados con fechas coherentes y funcionarios responsables.'
        },
        {
            'num': 10, 'nombre': 'Actividad', 'modelo': 'actividades.Actividad',
            'total': Actividad.objects.count(),
            'activos': Actividad.objects.exclude(estado='Inactivo').count(),
            'inactivos': Actividad.objects.filter(estado='Inactivo').count(),
            'url_lista': 'lista_actividades', 'url_crear': 'nueva_actividad',
            'descripcion': 'Registro operativo de gestiones, atenciones, terreno y tubo de trabajo.'
        },
        {
            'num': 11, 'nombre': 'Gestión Social', 'modelo': 'actividades.GestionSocial',
            'total': GestionSocial.objects.count(),
            'activos': GestionSocial.objects.exclude(estado='Inactiva').count(),
            'inactivos': GestionSocial.objects.filter(estado='Inactiva').count(),
            'url_lista': 'lista_gestiones_sociales', 'url_crear': 'nueva_gestion_social',
            'descripcion': 'Casos sociales, visitas domiciliarias, informes técnicos y entrega de beneficios.'
        },
        {
            'num': 12, 'nombre': 'Tipo de Atención', 'modelo': 'actividades.TipoAtencion',
            'total': TipoAtencion.objects.count(),
            'activos': TipoAtencion.objects.filter(estado='Activo').count(),
            'inactivos': TipoAtencion.objects.filter(estado='Inactivo').count(),
            'url_lista': 'tipos_atencion_lista', 'url_crear': 'tipos_atencion_crear',
            'descripcion': 'Catálogo superior de tipologías de atención y gestión.'
        },
        {
            'num': 13, 'nombre': 'Subtipo de Atención', 'modelo': 'actividades.SubAtencion',
            'total': SubAtencion.objects.count(),
            'activos': SubAtencion.objects.filter(estado='Activo').count(),
            'inactivos': SubAtencion.objects.filter(estado='Inactivo').count(),
            'url_lista': 'subatenciones_lista', 'url_crear': 'subatenciones_crear',
            'descripcion': 'Subcategorías dependientes de cada tipo de atención.'
        },
        {
            'num': 14, 'nombre': 'Meta', 'modelo': 'resultados.ItemMeta',
            'total': ItemMeta.objects.count(),
            'activos': ItemMeta.objects.filter(estado='Activo').count(),
            'inactivos': ItemMeta.objects.filter(estado='Inactivo').count(),
            'url_lista': 'items_lista', 'url_crear': 'items_crear',
            'descripcion': 'Catálogo de metas institucionales, unidad de medida y requisito de evidencia.'
        },
        {
            'num': 15, 'nombre': 'Asignación de Meta', 'modelo': 'resultados.MetaFuncionario',
            'total': MetaFuncionario.objects.count(),
            'activos': MetaFuncionario.objects.filter(estado='Activa').count(),
            'inactivos': MetaFuncionario.objects.filter(estado='Inactiva').count(),
            'url_lista': 'asignaciones_metas_lista', 'url_crear': 'asignaciones_metas_crear',
            'descripcion': 'Asignación de metas por funcionario y trimestre con cantidad objetivo y ponderación.'
        },
        {
            'num': 16, 'nombre': 'Evidencia', 'modelo': 'actividades.Evidencia',
            'total': Evidencia.objects.count(),
            'activos': Evidencia.objects.exclude(estado_validacion='Inactiva').count(),
            'inactivos': Evidencia.objects.filter(estado_validacion='Inactiva').count(),
            'url_lista': 'lista_evidencias', 'url_crear': 'crear_evidencia',
            'descripcion': 'Medios de verificación asociados a una Actividad o Gestión Social.'
        },
        {
            'num': 17, 'nombre': 'Trimestre', 'modelo': 'resultados.PeriodoEvaluacion',
            'total': PeriodoEvaluacion.objects.count(),
            'activos': PeriodoEvaluacion.objects.filter(estado='Activo').count(),
            'inactivos': PeriodoEvaluacion.objects.exclude(estado='Activo').count(),
            'url_lista': 'trimestres_lista', 'url_crear': 'trimestres_crear',
            'descripcion': 'Períodos trimestrales de evaluación (año, trimestre 1 a 4, vigencia).'
        },
    ]
    return render(request, 'mantenedores/inicio_17_entidades.html', {
        'entidades_17': entidades_17,
    })


# ==============================================================================
# ENTIDAD 1: DELEGACIÓN
# ==============================================================================
@login_required(login_url='login')
def delegaciones_lista(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil de rol no tiene permisos para gestionar delegaciones.')

    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = Delegacion.objects.select_related('delegado').all().order_by('codigo', 'nombre')

    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) |
            Q(nombre__icontains=q) |
            Q(ambito__icontains=q) |
            Q(responsable__icontains=q) |
            Q(comuna__icontains=q)
        )
    if estado:
        queryset = queryset.filter(estado=estado)

    if exportar:
        columnas = ['Código', 'Nombre Delegación', 'Dirección', 'Comuna', 'Ámbito Territorial', 'Delegado / Responsable', 'Estado']
        filas = [
            [d.codigo, d.nombre, d.direccion, d.comuna, d.ambito, d.responsable, d.estado]
            for d in queryset
        ]
        return generar_excel_institucional('Delegaciones', 'delegaciones_sgr', columnas, filas)

    paginador = Paginator(queryset, 10)
    page_obj = paginador.get_page(request.GET.get('page'))

    return render(request, 'mantenedores/delegaciones/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'estado_filtro': estado,
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def delegaciones_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)
    delegacion = get_object_or_404(Delegacion.objects.select_related('delegado'), pk=pk)
    territorios = delegacion.territorios.all()
    funcionarios = delegacion.funcionarios.all()
    juntas = delegacion.juntas_vecinos.all()
    return render(request, 'mantenedores/delegaciones/detalle.html', {
        'delegacion': delegacion,
        'territorios': territorios,
        'funcionarios': funcionarios,
        'juntas': juntas,
    })


@login_required(login_url='login')
def delegaciones_crear(request):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para crear delegaciones.')

    funcionarios = Funcionario.objects.filter(activo=True).order_by('nombre')
    if request.method == 'POST':
        form = DelegacionForm(request.POST)
        if form.is_valid():
            d = form.save()
            messages.success(request, f'Delegación "{d.nombre}" [{d.codigo}] creada exitosamente.')
            return redirect('delegaciones_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/delegaciones/formulario.html', {
            'form': form,
            'valores': EmptyValues(request.POST),
            'funcionarios': funcionarios,
            'titulo': 'Crear Delegación',
        })

    return render(request, 'mantenedores/delegaciones/formulario.html', {
        'form': DelegacionForm(),
        'titulo': 'Crear Delegación',
        'funcionarios': funcionarios,
        'valores': EmptyValues(),
    })


@login_required(login_url='login')
def delegaciones_editar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para editar delegaciones.')

    delegacion = get_object_or_404(Delegacion, pk=pk)
    funcionarios = Funcionario.objects.filter(activo=True).order_by('nombre')

    if request.method == 'POST':
        form = DelegacionForm(request.POST, instance=delegacion)
        if form.is_valid():
            d = form.save()
            messages.success(request, f'Delegación "{d.nombre}" actualizada con éxito.')
            return redirect('delegaciones_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/delegaciones/formulario.html', {
            'form': form,
            'delegacion': delegacion,
            'valores': EmptyValues(request.POST),
            'funcionarios': funcionarios,
            'titulo': 'Editar Delegación',
        })

    return render(request, 'mantenedores/delegaciones/formulario.html', {
        'form': DelegacionForm(instance=delegacion),
        'delegacion': delegacion,
        'funcionarios': funcionarios,
        'titulo': 'Editar Delegación',
    })


@login_required(login_url='login')
def delegaciones_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para eliminar delegaciones.')

    delegacion = get_object_or_404(Delegacion, pk=pk)
    tiene_relaciones = (
        delegacion.funcionarios.exists() or
        delegacion.territorios.exists() or
        delegacion.juntas_vecinos.exists() or
        delegacion.actividades_delegacion.exists() or
        delegacion.atenciones_ciudadanas.exists() or
        delegacion.compromisos.exists()
    )

    if request.method == 'POST':
        if tiene_relaciones:
            delegacion.estado = 'Inactiva'
            delegacion.save(update_fields=['estado'])
            messages.warning(
                request,
                f'La delegación "{delegacion.nombre}" posee registros vinculados (territorios, funcionarios o gestiones). '
                'Se ha desactivado lógicamente ("Inactiva") para proteger la integridad referencial.'
            )
        else:
            nom = delegacion.nombre
            delegacion.delete()
            messages.success(request, f'Delegación "{nom}" eliminada permanentemente.')
        return redirect('delegaciones_lista')

    return render(request, 'mantenedores/confirmar_eliminacion.html', {
        'entidad_nombre': 'Delegación',
        'objeto_nombre': f'[{delegacion.codigo}] {delegacion.nombre}',
        'objeto': delegacion,
        'tiene_relaciones': tiene_relaciones,
        'detalle_relaciones': 'Funcionarios, Territorios, Juntas de Vecinos o Actividades históricas vinculadas.',
        'url_cancelar': 'delegaciones_lista',
    })


# ==============================================================================
# ENTIDAD 2: TERRITORIO
# ==============================================================================
@login_required(login_url='login')
def territorios_lista(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido a este mantenedor.')

    q = request.GET.get('q', '').strip()
    delegacion_filtro = request.GET.get('delegacion', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = Territorio.objects.select_related('delegacion').all().order_by('delegacion__nombre', 'nombre')

    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) |
            Q(nombre__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(delegacion__nombre__icontains=q)
        )
    if delegacion_filtro:
        queryset = queryset.filter(delegacion_id=delegacion_filtro)

    if exportar:
        columnas = ['Código', 'Nombre Territorio / Sector', 'Delegación Asignada', 'Descripción', 'Estado']
        filas = [
            [t.codigo, t.nombre, t.delegacion.nombre, t.descripcion or '', t.estado]
            for t in queryset
        ]
        return generar_excel_institucional('Territorios', 'territorios_la_serena', columnas, filas)

    delegaciones = Delegacion.objects.filter(estado='Activa').order_by('nombre')
    paginador = Paginator(queryset, 10)
    page_obj = paginador.get_page(request.GET.get('page'))

    return render(request, 'mantenedores/territorios/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'delegacion_filtro': delegacion_filtro,
        'delegaciones': delegaciones,
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def territorios_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)
    territorio = get_object_or_404(Territorio.objects.select_related('delegacion'), pk=pk)
    juntas = territorio.juntas_vecinos.all()
    vecinos = territorio.vecinos_sector.all()
    hitos = territorio.hitos.all()
    return render(request, 'mantenedores/territorios/detalle.html', {
        'territorio': territorio,
        'juntas': juntas,
        'vecinos': vecinos,
        'hitos': hitos,
    })


@login_required(login_url='login')
def territorios_crear(request):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para crear territorios.')

    if request.method == 'POST':
        form = TerritorioForm(request.POST)
        if form.is_valid():
            t = form.save()
            messages.success(request, f'Territorio "{t.nombre}" [{t.codigo}] creado exitosamente.')
            return redirect('territorios_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/territorios/formulario.html', {
            'form': form,
            'datos': EmptyValues(request.POST),
            'delegaciones': Delegacion.objects.all(),
            'es_edicion': False,
        })

    return render(request, 'mantenedores/territorios/formulario.html', {
        'form': TerritorioForm(),
        'datos': EmptyValues(),
        'delegaciones': Delegacion.objects.filter(estado='Activa'),
        'es_edicion': False,
    })


@login_required(login_url='login')
def territorios_editar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para editar territorios.')

    territorio = get_object_or_404(Territorio, pk=pk)

    if request.method == 'POST':
        form = TerritorioForm(request.POST, instance=territorio)
        if form.is_valid():
            t = form.save()
            messages.success(request, f'Territorio "{t.nombre}" actualizado exitosamente.')
            return redirect('territorios_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/territorios/formulario.html', {
            'form': form,
            'datos': territorio,
            'delegaciones': Delegacion.objects.all(),
            'es_edicion': True,
        })

    return render(request, 'mantenedores/territorios/formulario.html', {
        'form': TerritorioForm(instance=territorio),
        'datos': territorio,
        'delegaciones': Delegacion.objects.all(),
        'es_edicion': True,
    })


@login_required(login_url='login')
def territorios_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para eliminar territorios.')

    territorio = get_object_or_404(Territorio, pk=pk)
    tiene_relaciones = (
        territorio.juntas_vecinos.exists() or
        territorio.vecinos_sector.exists() or
        territorio.hitos.exists() or
        territorio.actividades_territorio.exists()
    )

    if request.method == 'POST':
        if tiene_relaciones:
            territorio.estado = 'Inactivo'
            territorio.save(update_fields=['estado'])
            messages.warning(
                request,
                f'El territorio "{territorio.nombre}" tiene juntas, vecinos o hitos asociados. '
                'Se cambió su estado a "Inactivo" para preservar la trazabilidad.'
            )
        else:
            nom = territorio.nombre
            territorio.delete()
            messages.success(request, f'Territorio "{nom}" eliminado del catálogo.')
        return redirect('territorios_lista')

    return render(request, 'mantenedores/territorios/eliminar_confirmar.html', {
        'territorio': territorio,
        'tiene_relaciones': tiene_relaciones,
    })


# ==============================================================================
# ENTIDAD 3: USUARIO FUNCIONARIO
# ==============================================================================
@login_required(login_url='login')
def usuarios_lista(request):
    if not puede_consultar_mantenedor(request.user, solo_admin=True):
        return respuesta_403(request, 'Acceso restringido: Su perfil de rol no tiene permisos para administrar usuarios.')

    q = request.GET.get('q', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = User.objects.select_related(
        'perfil__rol', 'perfil__delegacion_activa', 'perfil__cargo', 'funcionario'
    ).prefetch_related('groups', 'perfil__roles').all().order_by('username')

    if q:
        queryset = queryset.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(perfil__rut__icontains=q) |
            Q(perfil__rol__nombre__icontains=q) |
            Q(perfil__delegacion_activa__nombre__icontains=q)
        )

    if exportar:
        columnas = ['Usuario', 'RUT', 'Nombre Completo', 'Correo Electrónico', 'Cargo', 'Rol Asignado', 'Delegación Principal', 'Estado']
        filas = [
            [
                u.username,
                u.perfil.rut if hasattr(u, 'perfil') and u.perfil.rut else '—',
                u.get_full_name() or '—',
                u.email or '—',
                (u.perfil.cargo.nombre if hasattr(u, 'perfil') and u.perfil.cargo else (u.funcionario.cargo if hasattr(u, 'funcionario') else '—')),
                u.perfil.rol.nombre if hasattr(u, 'perfil') and u.perfil.rol else 'Sin Rol',
                u.perfil.delegacion_activa.nombre if hasattr(u, 'perfil') and u.perfil.delegacion_activa else 'Sin Delegación',
                u.perfil.estado if hasattr(u, 'perfil') else 'Activo',
            ]
            for u in queryset
        ]
        return generar_excel_institucional('Usuarios', 'usuarios_sgr', columnas, filas)

    paginador = Paginator(queryset, 10)
    page_obj = paginador.get_page(request.GET.get('page'))

    return render(request, 'mantenedores/usuarios/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def usuarios_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user, solo_admin=True):
        return respuesta_403(request)
    user_obj = get_object_or_404(User.objects.select_related('perfil__rol', 'perfil__delegacion_activa', 'perfil__cargo'), pk=pk)
    perfil, _ = PerfilUsuario.objects.get_or_create(user=user_obj)
    funcionario = getattr(user_obj, 'funcionario', None)
    return render(request, 'mantenedores/usuarios/detalle.html', {
        'user_obj': user_obj,
        'perfil': perfil,
        'funcionario': funcionario,
    })


@login_required(login_url='login')
def usuarios_crear(request):
    if not puede_escribir_mantenedor(request.user, solo_admin=True):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para crear usuarios.')

    roles = Rol.objects.filter(estado='Activo')
    delegaciones = Delegacion.objects.filter(estado='Activa')
    cargos = Cargo.objects.filter(estado='Activo')
    grupos = Group.objects.all().order_by('name')

    if request.method == 'POST':
        form = UsuarioFuncionarioForm(request.POST, request_user=request.user)
        if form.is_valid():
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email'].lower()
            password = form.cleaned_data['password']

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.rut = form.cleaned_data.get('rut')
            perfil.cargo = form.cleaned_data.get('cargo')
            perfil.rol = form.cleaned_data.get('rol')
            perfil.delegacion_activa = form.cleaned_data.get('delegacion_activa') or Delegacion.objects.filter(estado='Activa').first()
            perfil.telefono = form.cleaned_data.get('telefono')
            perfil.estado = form.cleaned_data.get('estado') or 'Activo'
            perfil.save()

            roles_m2m = form.cleaned_data.get('roles')
            if roles_m2m:
                perfil.roles.set(roles_m2m)
            elif perfil.rol:
                perfil.roles.set([perfil.rol])

            delegaciones_ids = request.POST.getlist('delegaciones_autorizadas')
            if delegaciones_ids:
                perfil.delegaciones_autorizadas.set(delegaciones_ids)
            elif perfil.delegacion_activa:
                perfil.delegaciones_autorizadas.add(perfil.delegacion_activa)

            if not es_admin(request.user) and perfil.rol and perfil.rol.codigo == 'ROL-ADM':
                perfil.rol = Rol.objects.filter(codigo='ROL-CON').first() or perfil.rol
                perfil.save(update_fields=['rol'])

            grupo_id = request.POST.get('grupo')
            grupo_obj = Group.objects.filter(pk=grupo_id).first() if grupo_id else mapear_rol_a_grupo(perfil.rol)
            if grupo_obj and grupo_obj.name == 'Administrador' and not es_admin(request.user):
                grupo_obj = Group.objects.filter(name='Consulta').first()
            if grupo_obj:
                user.groups.set([grupo_obj])

            # Sincronizar registro de Funcionario
            if perfil.delegacion_activa:
                cargo_nombre = perfil.cargo.nombre if perfil.cargo else (request.POST.get('cargo_texto') or 'Funcionario Municipal')
                Funcionario.objects.update_or_create(
                    user=user,
                    defaults={
                        'id_delegacion': perfil.delegacion_activa,
                        'rut': perfil.rut,
                        'nombres': first_name,
                        'apellidos': last_name,
                        'nombre': f"{first_name} {last_name}".strip() or username,
                        'correo': email,
                        'telefono': perfil.telefono,
                        'cargo_rel': perfil.cargo,
                        'cargo': cargo_nombre,
                        'estado': perfil.estado,
                        'activo': perfil.estado == 'Activo',
                    }
                )

            messages.success(request, f'Usuario "{user.username}" registrado exitosamente con perfil "{grupo_obj.name if grupo_obj else "Asignado"}".')
            return redirect('usuarios_lista')

        reportar_errores_form(request, form)
        return render(request, 'mantenedores/usuarios/formulario.html', {
            'form': form,
            'roles': roles,
            'grupos': grupos,
            'cargos': cargos,
            'delegaciones': delegaciones,
            'valores': EmptyValues(request.POST),
            'titulo': 'Crear Usuario',
        })

    return render(request, 'mantenedores/usuarios/formulario.html', {
        'form': UsuarioFuncionarioForm(request_user=request.user),
        'roles': roles,
        'grupos': grupos,
        'cargos': cargos,
        'delegaciones': delegaciones,
        'titulo': 'Crear Usuario',
        'valores': EmptyValues(),
    })


@login_required(login_url='login')
def usuarios_editar(request, pk):
    if not puede_escribir_mantenedor(request.user, solo_admin=True):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para editar usuarios.')

    user_obj = get_object_or_404(User, pk=pk)
    perfil, _ = PerfilUsuario.objects.get_or_create(user=user_obj)
    roles = Rol.objects.filter(estado='Activo')
    delegaciones = Delegacion.objects.filter(estado='Activa')
    cargos = Cargo.objects.filter(estado='Activo')
    grupos = Group.objects.all().order_by('name')

    if request.method == 'POST':
        post_data = request.POST.copy()
        if not post_data.get('username'):
            post_data['username'] = user_obj.username
        form = UsuarioFuncionarioForm(post_data, instance=perfil, user_instance=user_obj, request_user=request.user)
        if form.is_valid():
            user_obj.first_name = form.cleaned_data['first_name']
            user_obj.last_name = form.cleaned_data['last_name']
            user_obj.email = form.cleaned_data['email'].lower()
            password = form.cleaned_data.get('password')
            if password:
                user_obj.set_password(password)

            rol_original = perfil.rol
            grupos_originales = list(user_obj.groups.all())

            perfil = form.save(commit=False)
            if not perfil.delegacion_activa:
                perfil.delegacion_activa = Delegacion.objects.filter(estado='Activa').first()
            # Impedir autoasignación o modificación de rol propio por usuarios no-superusuarios
            if (user_obj.pk == request.user.pk and not request.user.is_superuser) or (not es_admin(request.user) and perfil.rol and perfil.rol.codigo == 'ROL-ADM'):
                perfil.rol = rol_original
            perfil.save()
            form.save_m2m()

            delegaciones_ids = request.POST.getlist('delegaciones_autorizadas')
            if delegaciones_ids:
                perfil.delegaciones_autorizadas.set(delegaciones_ids)

            if user_obj.pk == request.user.pk and not request.user.is_superuser:
                user_obj.groups.set(grupos_originales)
            else:
                grupo_id = request.POST.get('grupo')
                grupo_obj = Group.objects.filter(pk=grupo_id).first() if grupo_id else mapear_rol_a_grupo(perfil.rol)
                # Evitar autoasignación de grupo Administrador por usuarios que no son Administrador
                if grupo_obj and grupo_obj.name == 'Administrador' and not es_admin(request.user):
                    grupo_obj = Group.objects.filter(name='Gestión').first() or user_obj.groups.first()
                if grupo_obj:
                    user_obj.groups.set([grupo_obj])

            user_obj.is_active = (perfil.estado == 'Activo')
            user_obj.save()

            func = getattr(user_obj, 'funcionario', None)
            if func:
                func.nombres = user_obj.first_name
                func.apellidos = user_obj.last_name
                func.nombre = f"{user_obj.first_name} {user_obj.last_name}".strip() or user_obj.username
                func.rut = perfil.rut
                func.correo = user_obj.email
                func.telefono = perfil.telefono
                if perfil.cargo:
                    func.cargo_rel = perfil.cargo
                    func.cargo = perfil.cargo.nombre
                if perfil.delegacion_activa:
                    func.id_delegacion = perfil.delegacion_activa
                func.estado = perfil.estado
                func.activo = (perfil.estado == 'Activo')
                func.save()

            messages.success(request, f'Usuario "{user_obj.username}" actualizado con éxito.')
            return redirect('usuarios_lista')

        reportar_errores_form(request, form)
        return render(request, 'mantenedores/usuarios/formulario.html', {
            'form': form,
            'user_obj': user_obj,
            'perfil': perfil,
            'roles': roles,
            'grupos': grupos,
            'cargos': cargos,
            'grupo_actual': user_obj.groups.first(),
            'delegaciones': delegaciones,
            'titulo': 'Editar Usuario',
        })

    return render(request, 'mantenedores/usuarios/formulario.html', {
        'form': UsuarioFuncionarioForm(instance=perfil, user_instance=user_obj, request_user=request.user),
        'user_obj': user_obj,
        'perfil': perfil,
        'roles': roles,
        'grupos': grupos,
        'cargos': cargos,
        'grupo_actual': user_obj.groups.first(),
        'delegaciones': delegaciones,
        'titulo': 'Editar Usuario',
    })


@login_required(login_url='login')
def usuarios_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user, solo_admin=True):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para eliminar usuarios.')

    user_obj = get_object_or_404(User, pk=pk)
    if user_obj.is_superuser:
        messages.error(request, 'No es posible desactivar o eliminar la cuenta de superusuario principal.')
        return redirect('usuarios_lista')

    func = getattr(user_obj, 'funcionario', None)
    tiene_relaciones = bool(
        user_obj.actividades_creadas.exists() or
        user_obj.atenciones_ingresadas.exists() or
        (func and (func.actividades.exists() or func.gestiones_sociales.exists() or func.metas.exists()))
    )

    if request.method == 'POST':
        if tiene_relaciones:
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user_obj)
            perfil.estado = 'Inactivo'
            perfil.save(update_fields=['estado'])
            if func:
                func.estado = 'Inactivo'
                func.activo = False
                func.save(update_fields=['estado', 'activo'])
            messages.warning(
                request,
                f'El funcionario "{user_obj.username}" posee historial de gestiones o metas asociadas. '
                'Se ha desactivado lógicamente ("Inactivo") para preservar la trazabilidad.'
            )
        else:
            nom = user_obj.username
            if func:
                func.delete()
            user_obj.delete()
            messages.success(request, f'Usuario "{nom}" eliminado permanentemente.')
        return redirect('usuarios_lista')

    return render(request, 'mantenedores/confirmar_eliminacion.html', {
        'entidad_nombre': 'Usuario Funcionario',
        'objeto_nombre': f'{user_obj.get_full_name() or user_obj.username} (@{user_obj.username})',
        'objeto': user_obj,
        'tiene_relaciones': tiene_relaciones,
        'detalle_relaciones': 'Actividades, Gestiones Sociales o Asignaciones de Metas asociadas al funcionario.',
        'url_cancelar': 'usuarios_lista',
    })


# ==============================================================================
# ENTIDAD 4: CARGO
# ==============================================================================
@login_required(login_url='login')
def cargos_lista(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)

    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = Cargo.objects.all().order_by('codigo', 'nombre')
    if q:
        queryset = queryset.filter(Q(codigo__icontains=q) | Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    if estado:
        queryset = queryset.filter(estado=estado)

    if exportar:
        columnas = ['Código', 'Nombre del Cargo', 'Descripción / Funciones', 'Estado']
        filas = [[c.codigo, c.nombre, c.descripcion, c.estado] for c in queryset]
        return generar_excel_institucional('Cargos', 'cargos_sgr', columnas, filas)

    paginador = Paginator(queryset, 10)
    page_obj = paginador.get_page(request.GET.get('page'))
    return render(request, 'mantenedores/cargos/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'estado_filtro': estado,
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def cargos_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)
    cargo = get_object_or_404(Cargo, pk=pk)
    funcionarios = cargo.funcionarios.select_related('id_delegacion').all()
    return render(request, 'mantenedores/cargos/detalle.html', {
        'cargo': cargo,
        'funcionarios': funcionarios,
    })


@login_required(login_url='login')
def cargos_crear(request):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    if request.method == 'POST':
        form = CargoForm(request.POST)
        if form.is_valid():
            c = form.save()
            messages.success(request, f'Cargo "{c.nombre}" [{c.codigo}] creado exitosamente.')
            return redirect('cargos_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/cargos/formulario.html', {
            'form': form,
            'valores': EmptyValues(request.POST),
            'titulo': 'Crear Cargo',
        })

    return render(request, 'mantenedores/cargos/formulario.html', {
        'form': CargoForm(),
        'valores': EmptyValues(),
        'titulo': 'Crear Cargo',
    })


@login_required(login_url='login')
def cargos_editar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == 'POST':
        form = CargoForm(request.POST, instance=cargo)
        if form.is_valid():
            c = form.save()
            messages.success(request, f'Cargo "{c.nombre}" actualizado con éxito.')
            return redirect('cargos_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/cargos/formulario.html', {
            'form': form,
            'cargo': cargo,
            'titulo': 'Editar Cargo',
        })

    return render(request, 'mantenedores/cargos/formulario.html', {
        'form': CargoForm(instance=cargo),
        'cargo': cargo,
        'titulo': 'Editar Cargo',
    })


@login_required(login_url='login')
def cargos_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    cargo = get_object_or_404(Cargo, pk=pk)
    tiene_relaciones = cargo.funcionarios.exists() or cargo.perfiles.exists()

    if request.method == 'POST':
        if tiene_relaciones:
            cargo.estado = 'Inactivo'
            cargo.save(update_fields=['estado'])
            messages.warning(
                request,
                f'El cargo "{cargo.nombre}" tiene funcionarios asignados. Se ha cambiado su estado a "Inactivo".'
            )
        else:
            nom = cargo.nombre
            cargo.delete()
            messages.success(request, f'Cargo "{nom}" eliminado permanentemente.')
        return redirect('cargos_lista')

    return render(request, 'mantenedores/confirmar_eliminacion.html', {
        'entidad_nombre': 'Cargo',
        'objeto_nombre': f'[{cargo.codigo}] {cargo.nombre}',
        'objeto': cargo,
        'tiene_relaciones': tiene_relaciones,
        'detalle_relaciones': 'Funcionarios o perfiles de usuario asignados a este cargo.',
        'url_cancelar': 'cargos_lista',
    })


# ==============================================================================
# ENTIDAD 5: ROL
# ==============================================================================
@login_required(login_url='login')
def roles_lista(request):
    if not puede_consultar_mantenedor(request.user, solo_admin=True):
        return respuesta_403(request, 'Acceso restringido: Su perfil de rol no tiene permisos para administrar roles.')

    q = request.GET.get('q', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = Rol.objects.select_related('grupo_django').all().order_by('codigo')

    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) | Q(nombre__icontains=q) | Q(descripcion__icontains=q)
        )

    if exportar:
        columnas = ['Código', 'Nombre del Rol', 'Alcance Territorial', 'Grupo Django', 'Permisos Asignados', 'Estado']
        filas = [
            [r.codigo, r.nombre, r.get_alcance_autorizado_display(), r.grupo_django.name if r.grupo_django else '—', r.permisos, r.estado]
            for r in queryset
        ]
        return generar_excel_institucional('Roles', 'roles_sgr', columnas, filas)

    paginador = Paginator(queryset, 10)
    page_obj = paginador.get_page(request.GET.get('page'))

    return render(request, 'mantenedores/roles/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def roles_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user, solo_admin=True):
        return respuesta_403(request)
    rol = get_object_or_404(Rol.objects.select_related('grupo_django'), pk=pk)
    usuarios = rol.usuarios.select_related('user', 'delegacion_activa').all()
    permisos_django = rol.grupo_django.permissions.select_related('content_type').all() if rol.grupo_django else []
    return render(request, 'mantenedores/roles/detalle.html', {
        'rol': rol,
        'usuarios': usuarios,
        'permisos_django': permisos_django,
    })


@login_required(login_url='login')
def roles_crear(request):
    if not puede_escribir_mantenedor(request.user, solo_admin=True):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para crear roles.')

    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            r = form.save()
            messages.success(request, f'Rol "{r.nombre}" [{r.codigo}] creado exitosamente.')
            return redirect('roles_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/roles/formulario.html', {
            'form': form,
            'valores': EmptyValues(request.POST),
            'titulo': 'Crear Rol',
        })

    return render(request, 'mantenedores/roles/formulario.html', {
        'form': RolForm(),
        'titulo': 'Crear Rol',
        'valores': EmptyValues(),
    })


@login_required(login_url='login')
def roles_editar(request, pk):
    if not puede_escribir_mantenedor(request.user, solo_admin=True):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para editar roles.')

    rol = get_object_or_404(Rol, pk=pk)

    if request.method == 'POST':
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            r = form.save()
            messages.success(request, f'Rol "{r.nombre}" actualizado con éxito.')
            return redirect('roles_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/roles/formulario.html', {
            'form': form,
            'rol': rol,
            'titulo': 'Editar Rol',
        })

    return render(request, 'mantenedores/roles/formulario.html', {
        'form': RolForm(instance=rol),
        'rol': rol,
        'titulo': 'Editar Rol',
    })


@login_required(login_url='login')
def roles_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user, solo_admin=True):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para eliminar roles.')

    rol = get_object_or_404(Rol, pk=pk)
    tiene_relaciones = rol.usuarios.exists() or rol.perfiles_asignados.exists()

    if request.method == 'POST':
        if tiene_relaciones:
            rol.estado = 'Inactivo'
            rol.save(update_fields=['estado'])
            messages.warning(request, f'El rol "{rol.nombre}" posee usuarios asociados. Se ha cambiado su estado a "Inactivo".')
        else:
            nom = rol.nombre
            rol.delete()
            messages.success(request, f'Rol "{nom}" eliminado permanentemente.')
        return redirect('roles_lista')

    return render(request, 'mantenedores/confirmar_eliminacion.html', {
        'entidad_nombre': 'Rol',
        'objeto_nombre': f'[{rol.codigo}] {rol.nombre}',
        'objeto': rol,
        'tiene_relaciones': tiene_relaciones,
        'detalle_relaciones': 'Usuarios funcionarios asociados a este rol.',
        'url_cancelar': 'roles_lista',
    })


# ==============================================================================
# ENTIDAD 6: VECINO
# ==============================================================================
@login_required(login_url='login')
def vecinos_lista(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)

    q = request.GET.get('q', '').strip()
    territorio_filtro = request.GET.get('territorio', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = Vecino.objects.select_related('territorio_rel').all().order_by('nombre')

    if q:
        queryset = queryset.filter(
            Q(rut__icontains=q) |
            Q(nombre__icontains=q) |
            Q(nombres__icontains=q) |
            Q(apellidos__icontains=q) |
            Q(telefono__icontains=q) |
            Q(correo__icontains=q) |
            Q(direccion__icontains=q) |
            Q(territorio__icontains=q)
        )
    if territorio_filtro:
        queryset = queryset.filter(Q(territorio__icontains=territorio_filtro) | Q(territorio_rel__nombre__icontains=territorio_filtro))

    if exportar:
        columnas = ['RUT', 'Nombre Completo', 'Teléfono', 'Correo', 'Dirección', 'Territorio / Sector', 'Estado', 'Fecha Registro']
        filas = [
            [v.rut, v.nombre, v.telefono or '', v.correo or '', v.direccion or '', v.territorio or '', v.estado, v.fecha_registro.strftime('%d/%m/%Y')]
            for v in queryset
        ]
        return generar_excel_institucional('PadronVecinos', 'padron_vecinos_la_serena', columnas, filas)

    territorios = Territorio.objects.filter(estado='Activo').order_by('nombre')
    paginador = Paginator(queryset, 15)
    page_obj = paginador.get_page(request.GET.get('page'))

    return render(request, 'mantenedores/vecinos/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'territorio_filtro': territorio_filtro,
        'territorios': territorios,
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def vecinos_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)
    vecino = get_object_or_404(Vecino.objects.select_related('territorio_rel__delegacion'), pk=pk)
    participaciones = vecino.participaciones_junta.select_related('junta').all()
    actividades = vecino.actividades.all()[:15]
    gestiones_sociales = vecino.gestiones_sociales_vecino.all()[:15]
    return render(request, 'mantenedores/vecinos/detalle.html', {
        'vecino': vecino,
        'participaciones': participaciones,
        'actividades': actividades,
        'gestiones_sociales': gestiones_sociales,
    })


@login_required(login_url='login')
def vecinos_crear(request):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para crear vecinos.')

    if request.method == 'POST':
        form = VecinoForm(request.POST)
        if form.is_valid():
            v = form.save()
            messages.success(request, f'Vecino {v.nombre} (RUT: {v.rut}) registrado exitosamente en el padrón comunal.')
            return redirect('vecinos_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/vecinos/formulario.html', {
            'form': form,
            'datos': EmptyValues(request.POST),
            'territorios': Territorio.objects.filter(estado='Activo'),
            'es_edicion': False,
        })

    return render(request, 'mantenedores/vecinos/formulario.html', {
        'form': VecinoForm(),
        'datos': EmptyValues(),
        'territorios': Territorio.objects.filter(estado='Activo'),
        'es_edicion': False,
    })


@login_required(login_url='login')
def vecinos_editar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para editar vecinos.')

    vecino = get_object_or_404(Vecino, pk=pk)

    if request.method == 'POST':
        form = VecinoForm(request.POST, instance=vecino)
        if form.is_valid():
            v = form.save()
            messages.success(request, f'Ficha del vecino {v.nombre} actualizada exitosamente.')
            return redirect('vecinos_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/vecinos/formulario.html', {
            'form': form,
            'datos': vecino,
            'territorios': Territorio.objects.filter(estado='Activo'),
            'es_edicion': True,
        })

    return render(request, 'mantenedores/vecinos/formulario.html', {
        'form': VecinoForm(instance=vecino),
        'datos': vecino,
        'territorios': Territorio.objects.filter(estado='Activo'),
        'es_edicion': True,
    })


@login_required(login_url='login')
def vecinos_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para eliminar vecinos.')

    vecino = get_object_or_404(Vecino, pk=pk)
    gestiones_count = Actividad.objects.filter(id_vecino=vecino).count()
    atenciones_count = AtencionCiudadana.objects.filter(id_vecino=vecino).count()
    social_count = GestionSocial.objects.filter(beneficiario_vecino=vecino).count()
    part_count = vecino.participaciones_junta.count()
    total_rel = gestiones_count + atenciones_count + social_count + part_count

    if request.method == 'POST':
        if total_rel > 0:
            vecino.estado = 'Inactivo'
            vecino.save(update_fields=['estado'])
            messages.warning(
                request,
                f'El vecino {vecino.nombre} cuenta con {total_rel} registro(s) históricos o participaciones asociadas. '
                'Se ha cambiado su estado a "Inactivo" para preservar la trazabilidad municipal.'
            )
            return redirect('vecinos_lista')

        nom = vecino.nombre
        vecino.delete()
        messages.success(request, f'Registro del vecino {nom} eliminado exitosamente.')
        return redirect('vecinos_lista')

    return render(request, 'mantenedores/vecinos/eliminar_confirmar.html', {
        'vecino': vecino,
        'tiene_relaciones': total_rel > 0,
        'total_rel': total_rel,
    })


# ==============================================================================
# ENTIDAD 7: JUNTA DE VECINOS
# ==============================================================================
@login_required(login_url='login')
def juntas_vecinos_lista(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido a este mantenedor.')

    q = request.GET.get('q', '').strip()
    delegacion_filtro = request.GET.get('delegacion', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = JuntaVecinos.objects.select_related('delegacion', 'territorio').all().order_by('nombre')

    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) |
            Q(nombre__icontains=q) |
            Q(direccion__icontains=q) |
            Q(delegacion__nombre__icontains=q) |
            Q(territorio__nombre__icontains=q)
        )
    if delegacion_filtro:
        queryset = queryset.filter(delegacion_id=delegacion_filtro)

    if exportar:
        columnas = ['Código', 'Nombre Junta de Vecinos', 'Dirección Sede', 'Delegación', 'Territorio / Sector', 'Estado']
        filas = [
            [j.codigo, j.nombre, j.direccion or '', j.delegacion.nombre, j.territorio.nombre if j.territorio else 'Sin asignar', j.estado]
            for j in queryset
        ]
        return generar_excel_institucional('JuntasVecinos', 'juntas_de_vecinos_la_serena', columnas, filas)

    delegaciones = Delegacion.objects.filter(estado='Activa').order_by('nombre')
    paginador = Paginator(queryset, 10)
    page_obj = paginador.get_page(request.GET.get('page'))

    return render(request, 'mantenedores/juntas_vecinos/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'delegacion_filtro': delegacion_filtro,
        'delegaciones': delegaciones,
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def juntas_vecinos_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)
    junta = get_object_or_404(JuntaVecinos.objects.select_related('delegacion', 'territorio'), pk=pk)
    participaciones = junta.dirigentes_socios.select_related('vecino').all()
    vecinos_disponibles = Vecino.objects.exclude(id_vecino__in=participaciones.values_list('vecino_id', flat=True)).order_by('nombre')

    return render(request, 'mantenedores/juntas_vecinos/detalle.html', {
        'junta': junta,
        'participaciones': participaciones,
        'vecinos_disponibles': vecinos_disponibles,
        'cargos': ParticipacionJunta.CARGOS_DIRIGENTE,
    })


@login_required(login_url='login')
def juntas_vecinos_crear(request):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para crear juntas de vecinos.')

    if request.method == 'POST':
        form = JuntaVecinosForm(request.POST)
        if form.is_valid():
            junta = form.save()
            messages.success(request, f'Junta de Vecinos "{junta.nombre}" creada con éxito (Código: {junta.codigo}).')
            return redirect('juntas_vecinos_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/juntas_vecinos/formulario.html', {
            'form': form,
            'datos': EmptyValues(request.POST),
            'delegaciones': Delegacion.objects.all(),
            'territorios': Territorio.objects.all(),
            'es_edicion': False,
        })

    return render(request, 'mantenedores/juntas_vecinos/formulario.html', {
        'form': JuntaVecinosForm(),
        'datos': EmptyValues(),
        'delegaciones': Delegacion.objects.filter(estado='Activa'),
        'territorios': Territorio.objects.filter(estado='Activo'),
        'es_edicion': False,
    })


@login_required(login_url='login')
def juntas_vecinos_editar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para editar juntas de vecinos.')

    junta = get_object_or_404(JuntaVecinos, pk=pk)

    if request.method == 'POST':
        form = JuntaVecinosForm(request.POST, instance=junta)
        if form.is_valid():
            j = form.save()
            messages.success(request, f'Junta de Vecinos "{j.nombre}" actualizada correctamente.')
            return redirect('juntas_vecinos_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/juntas_vecinos/formulario.html', {
            'form': form,
            'datos': junta,
            'delegaciones': Delegacion.objects.all(),
            'territorios': Territorio.objects.all(),
            'es_edicion': True,
        })

    return render(request, 'mantenedores/juntas_vecinos/formulario.html', {
        'form': JuntaVecinosForm(instance=junta),
        'datos': junta,
        'delegaciones': Delegacion.objects.all(),
        'territorios': Territorio.objects.all(),
        'es_edicion': True,
    })


@login_required(login_url='login')
def juntas_vecinos_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil no tiene permisos para eliminar juntas de vecinos.')

    junta = get_object_or_404(JuntaVecinos, pk=pk)
    tiene_relaciones = junta.dirigentes_socios.exists()

    if request.method == 'POST':
        if tiene_relaciones:
            junta.estado = 'Inactiva'
            junta.save(update_fields=['estado'])
            messages.warning(
                request,
                f'La junta "{junta.nombre}" tiene dirigentes o vecinos asociados. Se cambia su estado a "Inactiva".'
            )
        else:
            nom = junta.nombre
            junta.delete()
            messages.success(request, f'Junta de Vecinos "{nom}" eliminada del registro.')
        return redirect('juntas_vecinos_lista')

    return render(request, 'mantenedores/juntas_vecinos/eliminar_confirmar.html', {
        'junta': junta,
        'tiene_relaciones': tiene_relaciones,
    })


@login_required(login_url='login')
def juntas_vecinos_agregar_dirigente(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    junta = get_object_or_404(JuntaVecinos, pk=pk)
    if request.method == 'POST':
        vecino_id = request.POST.get('vecino')
        cargo = request.POST.get('cargo', 'Socio/a Activo/a')
        es_dirigente = request.POST.get('es_dirigente') == '1'
        fecha_inc = request.POST.get('fecha_incorporacion') or None

        vecino = get_object_or_404(Vecino, pk=vecino_id)
        part, created = ParticipacionJunta.objects.get_or_create(
            vecino=vecino,
            junta=junta,
            defaults={
                'cargo': cargo,
                'es_dirigente': es_dirigente or (cargo != 'Socio/a Activo/a'),
                'fecha_incorporacion': fecha_inc,
                'estado': 'Activo',
            }
        )
        if not created:
            part.cargo = cargo
            part.es_dirigente = es_dirigente or (cargo != 'Socio/a Activo/a')
            if fecha_inc:
                part.fecha_incorporacion = fecha_inc
            part.save()
            messages.success(request, f'Cargo de {vecino.nombre} actualizado a {cargo}.')
        else:
            messages.success(request, f'{vecino.nombre} incorporado a la directiva/nómina como {cargo}.')

    return redirect('juntas_vecinos_detalle', pk=pk)


@login_required(login_url='login')
def juntas_vecinos_quitar_dirigente(request, pk_participacion):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    participacion = get_object_or_404(ParticipacionJunta, pk=pk_participacion)
    junta_pk = participacion.junta.pk
    if request.method == 'POST':
        nom = participacion.vecino.nombre
        participacion.delete()
        messages.success(request, f'{nom} desvinculado de la junta de vecinos.')
    return redirect('juntas_vecinos_detalle', pk=junta_pk)


# ==============================================================================
# ENTIDAD 8: PARTICIPACIÓN EN JUNTA
# ==============================================================================
@login_required(login_url='login')
def participaciones_lista(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)

    q = request.GET.get('q', '').strip()
    junta_filtro = request.GET.get('junta', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = ParticipacionJunta.objects.select_related('vecino', 'junta__delegacion').all().order_by('-es_dirigente', 'junta__nombre', 'vecino__nombre')
    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) |
            Q(vecino__nombre__icontains=q) |
            Q(vecino__rut__icontains=q) |
            Q(junta__nombre__icontains=q) |
            Q(cargo__icontains=q)
        )
    if junta_filtro:
        queryset = queryset.filter(junta_id=junta_filtro)

    if exportar:
        columnas = ['Código', 'Vecino', 'RUT', 'Junta de Vecinos', 'Rol / Cargo', '¿Es Dirigente?', 'Fecha Incorporación', 'Estado']
        filas = [
            [
                p.codigo, p.vecino.nombre, p.vecino.rut, p.junta.nombre,
                p.cargo, 'Sí' if p.es_dirigente else 'No',
                p.fecha_incorporacion.strftime('%d/%m/%Y') if p.fecha_incorporacion else '—',
                p.estado
            ]
            for p in queryset
        ]
        return generar_excel_institucional('Participaciones', 'participaciones_juntas_sgr', columnas, filas)

    paginador = Paginator(queryset, 12)
    page_obj = paginador.get_page(request.GET.get('page'))
    return render(request, 'mantenedores/participaciones/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'junta_filtro': junta_filtro,
        'juntas': JuntaVecinos.objects.all().order_by('nombre'),
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def participaciones_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)
    participacion = get_object_or_404(ParticipacionJunta.objects.select_related('vecino', 'junta__delegacion', 'junta__territorio'), pk=pk)
    return render(request, 'mantenedores/participaciones/detalle.html', {
        'participacion': participacion,
    })


@login_required(login_url='login')
def participaciones_crear(request):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    if request.method == 'POST':
        form = ParticipacionJuntaForm(request.POST)
        if form.is_valid():
            p = form.save()
            messages.success(request, f'Participación [{p.codigo}] registrada exitosamente.')
            return redirect('participaciones_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/participaciones/formulario.html', {
            'form': form,
            'vecinos': Vecino.objects.all(),
            'juntas': JuntaVecinos.objects.all(),
            'cargos': ParticipacionJunta.CARGOS_DIRIGENTE,
            'valores': EmptyValues(request.POST),
            'titulo': 'Registrar Participación en Junta',
        })

    return render(request, 'mantenedores/participaciones/formulario.html', {
        'form': ParticipacionJuntaForm(),
        'vecinos': Vecino.objects.filter(estado='Activo'),
        'juntas': JuntaVecinos.objects.filter(estado='Activa'),
        'cargos': ParticipacionJunta.CARGOS_DIRIGENTE,
        'valores': EmptyValues(),
        'titulo': 'Registrar Participación en Junta',
    })


@login_required(login_url='login')
def participaciones_editar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    participacion = get_object_or_404(ParticipacionJunta, pk=pk)
    if request.method == 'POST':
        form = ParticipacionJuntaForm(request.POST, instance=participacion)
        if form.is_valid():
            p = form.save()
            messages.success(request, f'Participación [{p.codigo}] actualizada con éxito.')
            return redirect('participaciones_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/participaciones/formulario.html', {
            'form': form,
            'participacion': participacion,
            'vecinos': Vecino.objects.all(),
            'juntas': JuntaVecinos.objects.all(),
            'cargos': ParticipacionJunta.CARGOS_DIRIGENTE,
            'titulo': 'Editar Participación en Junta',
        })

    return render(request, 'mantenedores/participaciones/formulario.html', {
        'form': ParticipacionJuntaForm(instance=participacion),
        'participacion': participacion,
        'vecinos': Vecino.objects.all(),
        'juntas': JuntaVecinos.objects.all(),
        'cargos': ParticipacionJunta.CARGOS_DIRIGENTE,
        'titulo': 'Editar Participación en Junta',
    })


@login_required(login_url='login')
def participaciones_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    participacion = get_object_or_404(ParticipacionJunta.objects.select_related('vecino', 'junta'), pk=pk)
    if request.method == 'POST':
        if request.POST.get('modo') == 'desactivar':
            participacion.estado = 'Inactivo'
            participacion.save(update_fields=['estado'])
            messages.warning(request, f'Participación de {participacion.vecino.nombre} marcada como "Inactivo".')
        else:
            nom = f"{participacion.vecino.nombre} en {participacion.junta.nombre}"
            participacion.delete()
            messages.success(request, f'Participación de {nom} eliminada exitosamente.')
        return redirect('participaciones_lista')

    return render(request, 'mantenedores/confirmar_eliminacion.html', {
        'entidad_nombre': 'Participación en Junta',
        'objeto_nombre': f'[{participacion.codigo}] {participacion.vecino.nombre} -> {participacion.junta.nombre}',
        'objeto': participacion,
        'tiene_relaciones': False,
        'detalle_relaciones': '',
        'url_cancelar': 'participaciones_lista',
    })


# ==============================================================================
# ENTIDAD 9: HITO
# ==============================================================================
@login_required(login_url='login')
def hitos_lista(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)

    q = request.GET.get('q', '').strip()
    delegacion_filtro = request.GET.get('delegacion', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = Hito.objects.select_related('delegacion', 'territorio', 'responsable').all().order_by('-fecha_inicio')
    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) |
            Q(nombre__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(delegacion__nombre__icontains=q)
        )
    if delegacion_filtro:
        queryset = queryset.filter(delegacion_id=delegacion_filtro)

    if exportar:
        columnas = ['Código', 'Nombre del Hito', 'Periodicidad', 'Fecha Inicio', 'Fecha Término', 'Delegación', 'Territorio', 'Estado']
        filas = [
            [
                h.codigo, h.nombre, h.periodicidad,
                h.fecha_inicio.strftime('%d/%m/%Y'), h.fecha_termino.strftime('%d/%m/%Y'),
                h.delegacion.nombre, h.territorio.nombre if h.territorio else '—', h.estado
            ]
            for h in queryset
        ]
        return generar_excel_institucional('Hitos', 'hitos_territoriales_sgr', columnas, filas)

    paginador = Paginator(queryset, 10)
    page_obj = paginador.get_page(request.GET.get('page'))
    return render(request, 'mantenedores/hitos/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'delegacion_filtro': delegacion_filtro,
        'delegaciones': Delegacion.objects.filter(estado='Activa'),
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def hitos_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)
    hito = get_object_or_404(Hito.objects.select_related('delegacion', 'territorio', 'responsable').prefetch_related('responsables'), pk=pk)
    actividades = hito.actividades_hito.all()
    return render(request, 'mantenedores/hitos/detalle.html', {
        'hito': hito,
        'actividades': actividades,
    })


@login_required(login_url='login')
def hitos_crear(request):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    if request.method == 'POST':
        form = HitoForm(request.POST)
        if form.is_valid():
            h = form.save()
            messages.success(request, f'Hito "{h.nombre}" [{h.codigo}] creado exitosamente.')
            return redirect('hitos_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/hitos/formulario.html', {
            'form': form,
            'delegaciones': Delegacion.objects.all(),
            'territorios': Territorio.objects.all(),
            'funcionarios': Funcionario.objects.filter(activo=True),
            'valores': EmptyValues(request.POST),
            'titulo': 'Crear Hito Territorial',
        })

    return render(request, 'mantenedores/hitos/formulario.html', {
        'form': HitoForm(),
        'delegaciones': Delegacion.objects.filter(estado='Activa'),
        'territorios': Territorio.objects.filter(estado='Activo'),
        'funcionarios': Funcionario.objects.filter(activo=True),
        'valores': EmptyValues(),
        'titulo': 'Crear Hito Territorial',
    })


@login_required(login_url='login')
def hitos_editar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    hito = get_object_or_404(Hito, pk=pk)
    if request.method == 'POST':
        form = HitoForm(request.POST, instance=hito)
        if form.is_valid():
            h = form.save()
            messages.success(request, f'Hito "{h.nombre}" actualizado con éxito.')
            return redirect('hitos_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/hitos/formulario.html', {
            'form': form,
            'hito': hito,
            'delegaciones': Delegacion.objects.all(),
            'territorios': Territorio.objects.all(),
            'funcionarios': Funcionario.objects.all(),
            'titulo': 'Editar Hito Territorial',
        })

    return render(request, 'mantenedores/hitos/formulario.html', {
        'form': HitoForm(instance=hito),
        'hito': hito,
        'delegaciones': Delegacion.objects.all(),
        'territorios': Territorio.objects.all(),
        'funcionarios': Funcionario.objects.all(),
        'titulo': 'Editar Hito Territorial',
    })


@login_required(login_url='login')
def hitos_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    hito = get_object_or_404(Hito, pk=pk)
    tiene_relaciones = hito.actividades_hito.exists()

    if request.method == 'POST':
        if tiene_relaciones:
            hito.estado = 'Inactivo'
            hito.save(update_fields=['estado'])
            messages.warning(
                request,
                f'El hito "{hito.nombre}" tiene actividades vinculadas. Se ha cambiado su estado a "Inactivo".'
            )
        else:
            nom = hito.nombre
            hito.delete()
            messages.success(request, f'Hito "{nom}" eliminado permanentemente.')
        return redirect('hitos_lista')

    return render(request, 'mantenedores/confirmar_eliminacion.html', {
        'entidad_nombre': 'Hito Territorial',
        'objeto_nombre': f'[{hito.codigo}] {hito.nombre}',
        'objeto': hito,
        'tiene_relaciones': tiene_relaciones,
        'detalle_relaciones': 'Actividades operativas asociadas a este hito.',
        'url_cancelar': 'hitos_lista',
    })


# ==============================================================================
# ENTIDAD 12: TIPO DE ATENCIÓN
# ==============================================================================
@login_required(login_url='login')
def tipos_atencion_lista(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil de rol no tiene permisos para acceder a este catálogo.')

    q = request.GET.get('q', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = TipoAtencion.objects.all().order_by('codigo')

    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) | Q(nombre__icontains=q) | Q(descripcion__icontains=q)
        )

    if exportar:
        columnas = ['Código', 'Nombre Tipo de Atención', 'Descripción', 'Estado']
        filas = [[t.codigo, t.nombre, t.descripcion, t.estado] for t in queryset]
        return generar_excel_institucional('Tipos_Atencion', 'tipos_atencion_sgr', columnas, filas)

    paginador = Paginator(queryset, 10)
    page_obj = paginador.get_page(request.GET.get('page'))

    return render(request, 'mantenedores/tipos_atencion/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def tipos_atencion_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)
    tipo = get_object_or_404(TipoAtencion, pk=pk)
    subatenciones = tipo.subatenciones.all()
    return render(request, 'mantenedores/tipos_atencion/detalle.html', {
        'tipo': tipo,
        'subatenciones': subatenciones,
    })


@login_required(login_url='login')
def tipos_atencion_crear(request):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    if request.method == 'POST':
        form = TipoAtencionForm(request.POST)
        if form.is_valid():
            t = form.save()
            messages.success(request, f'Tipo de Atención "{t.nombre}" [{t.codigo}] creado exitosamente.')
            return redirect('tipos_atencion_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/tipos_atencion/formulario.html', {
            'form': form,
            'valores': EmptyValues(request.POST),
            'titulo': 'Crear Tipo de Atención',
        })

    return render(request, 'mantenedores/tipos_atencion/formulario.html', {
        'form': TipoAtencionForm(),
        'titulo': 'Crear Tipo de Atención',
        'valores': EmptyValues(),
    })


@login_required(login_url='login')
def tipos_atencion_editar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    tipo = get_object_or_404(TipoAtencion, pk=pk)

    if request.method == 'POST':
        form = TipoAtencionForm(request.POST, instance=tipo)
        if form.is_valid():
            t = form.save()
            messages.success(request, f'Tipo de Atención "{t.nombre}" actualizado con éxito.')
            return redirect('tipos_atencion_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/tipos_atencion/formulario.html', {
            'form': form,
            'tipo': tipo,
            'titulo': 'Editar Tipo de Atención',
        })

    return render(request, 'mantenedores/tipos_atencion/formulario.html', {
        'form': TipoAtencionForm(instance=tipo),
        'tipo': tipo,
        'titulo': 'Editar Tipo de Atención',
    })


@login_required(login_url='login')
def tipos_atencion_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    tipo = get_object_or_404(TipoAtencion, pk=pk)
    tiene_relaciones = (
        tipo.subatenciones.exists() or
        tipo.atenciones.exists() or
        tipo.actividades_clasificadas.exists() or
        tipo.gestiones_sociales.exists()
    )

    if request.method == 'POST':
        if tiene_relaciones:
            tipo.estado = 'Inactivo'
            tipo.save(update_fields=['estado'])
            messages.warning(
                request,
                f'El tipo de atención "{tipo.nombre}" posee subtipos o registros asociados. Se ha cambiado su estado a "Inactivo".'
            )
        else:
            nom = tipo.nombre
            tipo.delete()
            messages.success(request, f'Tipo de Atención "{nom}" eliminado.')
        return redirect('tipos_atencion_lista')

    return render(request, 'mantenedores/confirmar_eliminacion.html', {
        'entidad_nombre': 'Tipo de Atención',
        'objeto_nombre': f'[{tipo.codigo}] {tipo.nombre}',
        'objeto': tipo,
        'tiene_relaciones': tiene_relaciones,
        'detalle_relaciones': 'Subtipos de atención, Actividades o Gestiones Sociales asociadas.',
        'url_cancelar': 'tipos_atencion_lista',
    })


# ==============================================================================
# ENTIDAD 13: SUBTIPO DE ATENCIÓN
# ==============================================================================
@login_required(login_url='login')
def subatenciones_lista(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil de rol no tiene permisos para acceder a este catálogo.')

    q = request.GET.get('q', '').strip()
    tipo_filtro = request.GET.get('tipo', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = SubAtencion.objects.select_related('id_tipo').all().order_by('id_tipo__nombre', 'codigo')

    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) | Q(nombre__icontains=q) | Q(id_tipo__nombre__icontains=q)
        )
    if tipo_filtro:
        queryset = queryset.filter(id_tipo_id=tipo_filtro)

    if exportar:
        columnas = ['Código', 'Sub Atención', 'Tipo de Atención Asociado', 'Estado']
        filas = [[s.codigo, s.nombre, s.id_tipo.nombre, s.estado] for s in queryset]
        return generar_excel_institucional('Sub_Atenciones', 'subatenciones_sgr', columnas, filas)

    paginador = Paginator(queryset, 10)
    page_obj = paginador.get_page(request.GET.get('page'))

    return render(request, 'mantenedores/subatenciones/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'tipo_filtro': tipo_filtro,
        'tipos': TipoAtencion.objects.filter(estado='Activo'),
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def subatenciones_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)
    sub = get_object_or_404(SubAtencion.objects.select_related('id_tipo'), pk=pk)
    actividades = sub.actividades_clasificadas.all()[:15]
    gestiones = sub.gestiones_sociales.all()[:15]
    return render(request, 'mantenedores/subatenciones/detalle.html', {
        'sub': sub,
        'actividades': actividades,
        'gestiones': gestiones,
    })


@login_required(login_url='login')
def subatenciones_crear(request):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    tipos = TipoAtencion.objects.all()
    if request.method == 'POST':
        form = SubAtencionForm(request.POST)
        if form.is_valid():
            s = form.save()
            messages.success(request, f'Sub Atención "{s.nombre}" [{s.codigo}] creada exitosamente.')
            return redirect('subatenciones_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/subatenciones/formulario.html', {
            'form': form,
            'tipos': tipos,
            'valores': EmptyValues(request.POST),
            'titulo': 'Crear Sub Atención',
        })

    return render(request, 'mantenedores/subatenciones/formulario.html', {
        'form': SubAtencionForm(),
        'tipos': TipoAtencion.objects.filter(estado='Activo'),
        'titulo': 'Crear Sub Atención',
        'valores': EmptyValues(),
    })


@login_required(login_url='login')
def subatenciones_editar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    sub = get_object_or_404(SubAtencion, pk=pk)
    tipos = TipoAtencion.objects.all()

    if request.method == 'POST':
        form = SubAtencionForm(request.POST, instance=sub)
        if form.is_valid():
            s = form.save()
            messages.success(request, f'Sub Atención "{s.nombre}" actualizada con éxito.')
            return redirect('subatenciones_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/subatenciones/formulario.html', {
            'form': form,
            'sub': sub,
            'tipos': tipos,
            'titulo': 'Editar Sub Atención',
        })

    return render(request, 'mantenedores/subatenciones/formulario.html', {
        'form': SubAtencionForm(instance=sub),
        'sub': sub,
        'tipos': tipos,
        'titulo': 'Editar Sub Atención',
    })


@login_required(login_url='login')
def subatenciones_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    sub = get_object_or_404(SubAtencion.objects.select_related('id_tipo'), pk=pk)
    tiene_relaciones = (
        sub.atenciones.exists() or
        sub.actividades_clasificadas.exists() or
        sub.gestiones_sociales.exists()
    )

    if request.method == 'POST':
        if tiene_relaciones:
            sub.estado = 'Inactivo'
            sub.save(update_fields=['estado'])
            messages.warning(
                request,
                f'La subatención "{sub.nombre}" tiene atenciones o gestiones vinculadas. Se ha cambiado su estado a "Inactivo".'
            )
        else:
            nom = sub.nombre
            sub.delete()
            messages.success(request, f'Sub Atención "{nom}" eliminada.')
        return redirect('subatenciones_lista')

    return render(request, 'mantenedores/confirmar_eliminacion.html', {
        'entidad_nombre': 'Subtipo de Atención',
        'objeto_nombre': f'[{sub.codigo}] {sub.nombre} ({sub.id_tipo.nombre})',
        'objeto': sub,
        'tiene_relaciones': tiene_relaciones,
        'detalle_relaciones': 'Actividades, Atenciones Ciudadanas o Gestiones Sociales clasificadas en este subtipo.',
        'url_cancelar': 'subatenciones_lista',
    })


# ==============================================================================
# ENTIDAD 14: META (CATÁLOGO DE ÍTEMS Y METAS)
# ==============================================================================
@login_required(login_url='login')
def items_lista(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request, 'Acceso restringido: Su perfil de rol no tiene permisos para acceder a este catálogo.')

    q = request.GET.get('q', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = ItemMeta.objects.all().order_by('codigo')

    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) | Q(nombre__icontains=q) | Q(descripcion__icontains=q)
        )

    if exportar:
        columnas = ['Código', 'Nombre de la Meta', 'Tipo de Meta', 'Unidad de Medida', 'Requisito Evidencia', 'Estado']
        filas = [[it.codigo, it.nombre, it.tipo_meta, it.unidad_medida, it.requisito_evidencia, it.estado] for it in queryset]
        return generar_excel_institucional('Items_Metas', 'items_metas_sgr', columnas, filas)

    paginador = Paginator(queryset, 10)
    page_obj = paginador.get_page(request.GET.get('page'))

    return render(request, 'mantenedores/items/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def items_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)
    item = get_object_or_404(ItemMeta, pk=pk)
    asignaciones = item.asignaciones.select_related('id_funcionario', 'id_periodo').all()
    return render(request, 'mantenedores/items/detalle.html', {
        'item': item,
        'asignaciones': asignaciones,
    })


@login_required(login_url='login')
def items_crear(request):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    if request.method == 'POST':
        form = ItemMetaForm(request.POST)
        if form.is_valid():
            it = form.save()
            messages.success(request, f'Meta "{it.nombre}" [{it.codigo}] creada exitosamente.')
            return redirect('items_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/items/formulario.html', {
            'form': form,
            'valores': EmptyValues(request.POST),
            'titulo': 'Crear Meta Institucional',
        })

    return render(request, 'mantenedores/items/formulario.html', {
        'form': ItemMetaForm(),
        'titulo': 'Crear Meta Institucional',
        'valores': EmptyValues(),
    })


@login_required(login_url='login')
def items_editar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    item = get_object_or_404(ItemMeta, pk=pk)

    if request.method == 'POST':
        form = ItemMetaForm(request.POST, instance=item)
        if form.is_valid():
            it = form.save()
            messages.success(request, f'Meta "{it.nombre}" actualizada con éxito.')
            return redirect('items_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/items/formulario.html', {
            'form': form,
            'item': item,
            'titulo': 'Editar Meta Institucional',
        })

    return render(request, 'mantenedores/items/formulario.html', {
        'form': ItemMetaForm(instance=item),
        'item': item,
        'titulo': 'Editar Meta Institucional',
    })


@login_required(login_url='login')
def items_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    item = get_object_or_404(ItemMeta, pk=pk)
    tiene_relaciones = item.asignaciones.exists() or MetaFuncionario.objects.filter(item__iexact=item.nombre).exists()

    if request.method == 'POST':
        if tiene_relaciones:
            item.estado = 'Inactivo'
            item.save(update_fields=['estado'])
            messages.warning(request, f'La meta "{item.nombre}" tiene asignaciones activas/históricas. Se ha cambiado su estado a "Inactivo".')
        else:
            nom = item.nombre
            item.delete()
            messages.success(request, f'Meta "{nom}" eliminada permanentemente.')
        return redirect('items_lista')

    return render(request, 'mantenedores/confirmar_eliminacion.html', {
        'entidad_nombre': 'Meta Institucional',
        'objeto_nombre': f'[{item.codigo}] {item.nombre}',
        'objeto': item,
        'tiene_relaciones': tiene_relaciones,
        'detalle_relaciones': 'Asignaciones de meta a funcionarios vinculadas a este ítem.',
        'url_cancelar': 'items_lista',
    })


# ==============================================================================
# ENTIDAD 15: ASIGNACIÓN DE META
# ==============================================================================
@login_required(login_url='login')
def asignaciones_metas_lista(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)

    q = request.GET.get('q', '').strip()
    funcionario_filtro = request.GET.get('funcionario', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = MetaFuncionario.objects.select_related('id_funcionario__id_delegacion', 'id_periodo', 'id_item_meta').all().order_by('id_funcionario__nombre', 'item')
    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) |
            Q(item__icontains=q) |
            Q(id_funcionario__nombre__icontains=q) |
            Q(id_periodo__nombre__icontains=q)
        )
    if funcionario_filtro:
        queryset = queryset.filter(id_funcionario_id=funcionario_filtro)

    if exportar:
        columnas = ['Código', 'Funcionario', 'Delegación', 'Trimestre', 'Meta Asociada', 'Cantidad Objetivo', 'Ponderación (%)', 'Avance', 'Estado']
        filas = [
            [
                m.codigo, m.id_funcionario.nombre, m.id_funcionario.id_delegacion.nombre,
                m.id_periodo.nombre if m.id_periodo else '—', m.item,
                m.meta_periodo, float(m.ponderador), m.avance_actual, m.estado
            ]
            for m in queryset
        ]
        return generar_excel_institucional('Asignaciones_Metas', 'asignaciones_metas_sgr', columnas, filas)

    paginador = Paginator(queryset, 12)
    page_obj = paginador.get_page(request.GET.get('page'))
    return render(request, 'mantenedores/asignaciones_metas/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'funcionario_filtro': funcionario_filtro,
        'funcionarios': Funcionario.objects.all().order_by('nombre'),
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def asignaciones_metas_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)
    asignacion = get_object_or_404(
        MetaFuncionario.objects.select_related('id_funcionario__id_delegacion', 'id_periodo', 'id_item_meta'),
        pk=pk
    )
    actividades = asignacion.actividades_asociadas.all()
    gestiones = asignacion.gestiones_sociales_asociadas.all()
    return render(request, 'mantenedores/asignaciones_metas/detalle.html', {
        'asignacion': asignacion,
        'actividades': actividades,
        'gestiones': gestiones,
    })


@login_required(login_url='login')
def asignaciones_metas_crear(request):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    if request.method == 'POST':
        form = MetaFuncionarioForm(request.POST)
        if form.is_valid():
            m = form.save()
            messages.success(request, f'Asignación de Meta [{m.codigo}] creada exitosamente.')
            return redirect('asignaciones_metas_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/asignaciones_metas/formulario.html', {
            'form': form,
            'items_meta': ItemMeta.objects.all(),
            'funcionarios': Funcionario.objects.all(),
            'periodos': PeriodoEvaluacion.objects.all(),
            'valores': EmptyValues(request.POST),
            'titulo': 'Crear Asignación de Meta',
        })

    return render(request, 'mantenedores/asignaciones_metas/formulario.html', {
        'form': MetaFuncionarioForm(),
        'items_meta': ItemMeta.objects.filter(estado='Activo'),
        'funcionarios': Funcionario.objects.filter(activo=True),
        'periodos': PeriodoEvaluacion.objects.all(),
        'valores': EmptyValues(),
        'titulo': 'Crear Asignación de Meta',
    })


@login_required(login_url='login')
def asignaciones_metas_editar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    asignacion = get_object_or_404(MetaFuncionario, pk=pk)
    if request.method == 'POST':
        form = MetaFuncionarioForm(request.POST, instance=asignacion)
        if form.is_valid():
            m = form.save()
            messages.success(request, f'Asignación de Meta [{m.codigo}] actualizada con éxito.')
            return redirect('asignaciones_metas_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/asignaciones_metas/formulario.html', {
            'form': form,
            'asignacion': asignacion,
            'items_meta': ItemMeta.objects.all(),
            'funcionarios': Funcionario.objects.all(),
            'periodos': PeriodoEvaluacion.objects.all(),
            'titulo': 'Editar Asignación de Meta',
        })

    return render(request, 'mantenedores/asignaciones_metas/formulario.html', {
        'form': MetaFuncionarioForm(instance=asignacion),
        'asignacion': asignacion,
        'items_meta': ItemMeta.objects.all(),
        'funcionarios': Funcionario.objects.all(),
        'periodos': PeriodoEvaluacion.objects.all(),
        'titulo': 'Editar Asignación de Meta',
    })


@login_required(login_url='login')
def asignaciones_metas_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    asignacion = get_object_or_404(MetaFuncionario.objects.select_related('id_funcionario'), pk=pk)
    tiene_relaciones = (
        asignacion.actividades_asociadas.exists() or
        asignacion.gestiones_sociales_asociadas.exists() or
        asignacion.avance_actual > 0
    )

    if request.method == 'POST':
        if tiene_relaciones:
            asignacion.estado = 'Inactiva'
            asignacion.save(update_fields=['estado'])
            messages.warning(
                request,
                f'La asignación [{asignacion.codigo}] posee actividades o avance registrado. Se ha cambiado su estado a "Inactiva".'
            )
        else:
            cod = asignacion.codigo
            asignacion.delete()
            messages.success(request, f'Asignación de meta [{cod}] eliminada permanentemente.')
        return redirect('asignaciones_metas_lista')

    return render(request, 'mantenedores/confirmar_eliminacion.html', {
        'entidad_nombre': 'Asignación de Meta',
        'objeto_nombre': f'[{asignacion.codigo}] {asignacion.id_funcionario.nombre} - {asignacion.item}',
        'objeto': asignacion,
        'tiene_relaciones': tiene_relaciones,
        'detalle_relaciones': 'Actividades, Gestiones Sociales o avances de cumplimiento vinculados.',
        'url_cancelar': 'asignaciones_metas_lista',
    })


# ==============================================================================
# ENTIDAD 17: TRIMESTRE (PERÍODO DE EVALUACIÓN)
# ==============================================================================
@login_required(login_url='login')
def trimestres_lista(request):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)

    q = request.GET.get('q', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    queryset = PeriodoEvaluacion.objects.all().order_by('-anio', '-numero')
    if q:
        queryset = queryset.filter(Q(codigo__icontains=q) | Q(nombre__icontains=q) | Q(anio__icontains=q))

    if exportar:
        columnas = ['Código', 'Nombre del Trimestre', 'Año', 'Número Trimestre', 'Fecha Inicio', 'Fecha Término', 'Estado']
        filas = [
            [t.codigo, t.nombre, t.anio, t.numero, t.fecha_inicio.strftime('%d/%m/%Y'), t.fecha_cierre.strftime('%d/%m/%Y'), t.estado]
            for t in queryset
        ]
        return generar_excel_institucional('Trimestres', 'trimestres_sgr', columnas, filas)

    paginador = Paginator(queryset, 10)
    page_obj = paginador.get_page(request.GET.get('page'))
    return render(request, 'mantenedores/trimestres/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def trimestres_detalle(request, pk):
    if not puede_consultar_mantenedor(request.user):
        return respuesta_403(request)
    trimestre = get_object_or_404(PeriodoEvaluacion, pk=pk)
    asignaciones = trimestre.metas.select_related('id_funcionario__id_delegacion').all()
    return render(request, 'mantenedores/trimestres/detalle.html', {
        'trimestre': trimestre,
        'asignaciones': asignaciones,
    })


@login_required(login_url='login')
def trimestres_crear(request):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    if request.method == 'POST':
        form = PeriodoEvaluacionForm(request.POST)
        if form.is_valid():
            t = form.save()
            messages.success(request, f'Trimestre "{t.nombre}" [{t.codigo}] creado exitosamente.')
            return redirect('trimestres_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/trimestres/formulario.html', {
            'form': form,
            'valores': EmptyValues(request.POST),
            'titulo': 'Crear Trimestre / Período',
        })

    return render(request, 'mantenedores/trimestres/formulario.html', {
        'form': PeriodoEvaluacionForm(),
        'valores': EmptyValues(),
        'titulo': 'Crear Trimestre / Período',
    })


@login_required(login_url='login')
def trimestres_editar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    trimestre = get_object_or_404(PeriodoEvaluacion, pk=pk)
    if request.method == 'POST':
        form = PeriodoEvaluacionForm(request.POST, instance=trimestre)
        if form.is_valid():
            t = form.save()
            messages.success(request, f'Trimestre "{t.nombre}" actualizado con éxito.')
            return redirect('trimestres_lista')
        reportar_errores_form(request, form)
        return render(request, 'mantenedores/trimestres/formulario.html', {
            'form': form,
            'trimestre': trimestre,
            'titulo': 'Editar Trimestre / Período',
        })

    return render(request, 'mantenedores/trimestres/formulario.html', {
        'form': PeriodoEvaluacionForm(instance=trimestre),
        'trimestre': trimestre,
        'titulo': 'Editar Trimestre / Período',
    })


@login_required(login_url='login')
def trimestres_eliminar(request, pk):
    if not puede_escribir_mantenedor(request.user):
        return respuesta_403(request)

    trimestre = get_object_or_404(PeriodoEvaluacion, pk=pk)
    tiene_relaciones = trimestre.metas.exists() or trimestre.indicadores.exists()

    if request.method == 'POST':
        if tiene_relaciones:
            trimestre.estado = 'Inactivo'
            trimestre.activo = False
            trimestre.save(update_fields=['estado', 'activo'])
            messages.warning(
                request,
                f'El trimestre "{trimestre.nombre}" tiene asignaciones de metas o indicadores asociados. Se ha cambiado su estado a "Inactivo".'
            )
        else:
            nom = trimestre.nombre
            trimestre.delete()
            messages.success(request, f'Trimestre "{nom}" eliminado permanentemente.')
        return redirect('trimestres_lista')

    return render(request, 'mantenedores/confirmar_eliminacion.html', {
        'entidad_nombre': 'Trimestre',
        'objeto_nombre': f'[{trimestre.codigo}] {trimestre.nombre}',
        'objeto': trimestre,
        'tiene_relaciones': tiene_relaciones,
        'detalle_relaciones': 'Asignaciones de metas a funcionarios e indicadores de delegación en este trimestre.',
        'url_cancelar': 'trimestres_lista',
    })


# ==============================================================================
# INGRESO Y GESTIÓN DE ATENCIÓN CIUDADANA + APIs AJAX
# ==============================================================================
@login_required(login_url='login')
def atencion_nueva(request):
    if es_consulta(request.user):
        return respuesta_403(request, 'Acceso restringido: El perfil Consulta no puede crear registros.')

    tipos = TipoAtencion.objects.filter(estado='Activo')
    delegacion_activa_id = request.session.get('delegacion_activa_id')
    es_todas = str(delegacion_activa_id).strip().upper() in ('TODAS', '0')
    delegacion_activa = None
    if not es_todas and delegacion_activa_id:
        try:
            delegacion_activa = Delegacion.objects.filter(pk=int(delegacion_activa_id), estado='Activa').first()
        except (ValueError, TypeError):
            pass
    if not delegacion_activa:
        delegacion_activa = Delegacion.objects.filter(estado='Activa').first()

    if request.method == 'POST':
        solicitante = request.POST.get('solicitante', '').strip()
        rut = request.POST.get('rut_solicitante', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        correo = request.POST.get('correo', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        id_tipo = request.POST.get('id_tipo')
        id_subatencion = request.POST.get('id_subatencion')
        descripcion = request.POST.get('descripcion', '').strip()

        if not solicitante or not id_tipo or not id_subatencion or not descripcion:
            messages.error(request, 'Por favor complete todos los campos obligatorios (*).')
            return render(request, 'atenciones/formulario.html', {
                'tipos': tipos,
                'delegacion_activa': delegacion_activa,
                'valores': EmptyValues(request.POST)
            })

        tipo_obj = get_object_or_404(TipoAtencion, pk=id_tipo)
        sub_obj = get_object_or_404(SubAtencion, pk=id_subatencion, id_tipo=tipo_obj)

        atencion = AtencionCiudadana.objects.create(
            solicitante=solicitante,
            rut_solicitante=rut,
            telefono=telefono,
            correo=correo,
            direccion=direccion,
            id_tipo=tipo_obj,
            id_subatencion=sub_obj,
            descripcion=descripcion,
            id_delegacion=delegacion_activa,
            id_usuario_responsable=request.user,
            estado='Ingresada'
        )

        funcionario_default = Funcionario.objects.first()
        Actividad.objects.create(
            id_funcionario=funcionario_default,
            id_delegacion=delegacion_activa,
            id_atencion=atencion,
            fecha=atencion.fecha_registro.date(),
            solicitante=solicitante,
            rut_solicitante=rut,
            telefono=telefono,
            correo=correo,
            direccion=direccion,
            territorio=direccion or (delegacion_activa.nombre if delegacion_activa else ''),
            contacto=solicitante,
            id_tipo=tipo_obj,
            id_subatencion=sub_obj,
            solicitud=descripcion,
            accion='Atención ciudadana registrada e integrada en gestiones',
            responsable=request.user.get_full_name() or request.user.username,
            item_evaluacion='ATENCION DE USUARIO TELEFONO Y PRESENCIAL',
            estado='Pendiente'
        )

        messages.success(
            request,
            f'¡Atención registrada exitosamente! Se ha generado el Folio Oficial: {atencion.folio} y ha quedado integrada al Módulo de Gestiones.'
        )
        return redirect('atenciones_lista')

    return render(request, 'atenciones/formulario.html', {
        'tipos': tipos,
        'delegacion_activa': delegacion_activa,
        'valores': EmptyValues(),
    })


@login_required(login_url='login')
def atenciones_lista(request):
    q = request.GET.get('q', '').strip()
    exportar = request.GET.get('exportar') == 'excel'

    delegacion_activa_id = request.session.get('delegacion_activa_id')

    queryset = AtencionCiudadana.objects.select_related(
        'id_tipo', 'id_subatencion', 'id_delegacion', 'id_usuario_responsable'
    ).all()

    es_todas = str(delegacion_activa_id).strip().upper() in ('TODAS', '0')
    if not es_todas and delegacion_activa_id:
        try:
            queryset = queryset.filter(id_delegacion_id=int(delegacion_activa_id))
        except (ValueError, TypeError):
            pass

    if q:
        queryset = queryset.filter(
            Q(folio__icontains=q) |
            Q(solicitante__icontains=q) |
            Q(rut_solicitante__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(id_tipo__nombre__icontains=q) |
            Q(id_subatencion__nombre__icontains=q)
        )

    if exportar:
        columnas = ['Folio', 'Fecha Registro', 'Solicitante', 'RUT', 'Tipo Atención', 'Sub Atención', 'Delegación', 'Responsable', 'Estado']
        filas = [
            [
                a.folio,
                a.fecha_registro.strftime('%d/%m/%Y %H:%M'),
                a.solicitante,
                a.rut_solicitante or '—',
                a.id_tipo.nombre,
                a.id_subatencion.nombre,
                a.id_delegacion.nombre,
                a.id_usuario_responsable.get_full_name() or a.id_usuario_responsable.username,
                a.estado,
            ]
            for a in queryset
        ]
        return generar_excel_institucional('Atenciones', 'atenciones_ciudadanas_sgr', columnas, filas)

    paginador = Paginator(queryset, 10)
    page_obj = paginador.get_page(request.GET.get('page'))

    return render(request, 'atenciones/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'total_registros': queryset.count(),
    })


@login_required(login_url='login')
def atenciones_detalle(request, pk):
    atencion = get_object_or_404(AtencionCiudadana.objects.select_related(
        'id_tipo', 'id_subatencion', 'id_delegacion', 'id_usuario_responsable'
    ), pk=pk)
    return render(request, 'atenciones/detalle.html', {'atencion': atencion})


@login_required(login_url='login')
def api_subatenciones_por_tipo(request):
    tipo_id = request.GET.get('tipo_id')
    subatenciones = []
    if tipo_id:
        subs = SubAtencion.objects.filter(id_tipo_id=tipo_id, estado='Activo').order_by('nombre')
        subatenciones = [{'id': s.pk, 'nombre': s.nombre, 'codigo': s.codigo} for s in subs]
    return JsonResponse({'subatenciones': subatenciones})


@login_required(login_url='login')
def api_territorios_por_delegacion(request):
    delegacion_id = request.GET.get('delegacion_id')
    territorios = []
    if delegacion_id:
        ters = Territorio.objects.filter(delegacion_id=delegacion_id, estado='Activo').order_by('nombre')
        territorios = [{'id': t.pk, 'nombre': t.nombre, 'codigo': t.codigo} for t in ters]
    return JsonResponse({'territorios': territorios})
