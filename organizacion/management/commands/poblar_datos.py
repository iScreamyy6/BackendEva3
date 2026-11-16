import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType

from organizacion.models import (
    Delegacion, Territorio, Cargo, Funcionario, Rol,
    PerfilUsuario, CargoTipoGestion, JuntaVecinos, ParticipacionJunta, Hito
)
from actividades.models import (
    Actividad, GestionSocial, Evidencia, TipoAtencion, SubAtencion,
    Vecino
)
from agenda.models import Compromiso
from resultados.models import (
    PeriodoEvaluacion, MetaFuncionario, IndicadorDelegacion, ItemMeta
)


class Command(BaseCommand):
    help = 'Pobla la base de datos con información inicial de las 17 entidades SGR (Ilustre Municipalidad de La Serena)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Iniciando poblamiento integral de las 17 entidades SGR...'))

        # ======================================================================
        # 0. GRUPOS Y PERMISOS DE DJANGO (Consulta, Gestión, Administrador, etc.)
        # ======================================================================
        grupos_nombres = ['Administrador', 'Supervisor', 'Administrativo', 'Gestión', 'Consulta']
        grupos_objs = {}
        for g_name in grupos_nombres:
            grp, _ = Group.objects.get_or_create(name=g_name)
            grupos_objs[g_name] = grp

        apps_sgr = ['organizacion', 'actividades', 'agenda', 'resultados', 'auth']
        cts_sgr = ContentType.objects.filter(app_label__in=apps_sgr)
        perms_all = Permission.objects.filter(content_type__in=cts_sgr)
        perms_view = perms_all.filter(codename__startswith='view_')
        perms_write = perms_all.filter(codename__iregex=r'^(view|add|change|delete)_')

        grupos_objs['Consulta'].permissions.set(perms_view)
        grupos_objs['Gestión'].permissions.set(perms_write)
        grupos_objs['Administrador'].permissions.set(perms_all)
        grupos_objs['Supervisor'].permissions.set(
            perms_all.filter(codename__iregex=r'^(view|add|change)_')
        )
        grupos_objs['Administrativo'].permissions.set(
            perms_all.filter(content_type__app_label__in=['actividades', 'agenda'], codename__iregex=r'^(view|add)_')
        )
        self.stdout.write(self.style.SUCCESS('0. Grupos y Permisos Django configurados (Consulta, Gestión, Administrador, Supervisor, Administrativo).'))

        # ======================================================================
        # ENTIDAD 5: ROL
        # ======================================================================
        roles_data = [
            {
                'id': 1,
                'codigo': 'ROL-ADM',
                'nombre': 'Administrador General',
                'descripcion': 'Acceso total y configuración comunal transversal de las 17 entidades',
                'alcance_autorizado': 'COMUNAL',
                'permisos': 'Crear, Editar, Consultar, Listar, Eliminar/Desactivar, Exportar, Configuración',
                'grupo': grupos_objs['Administrador'],
                'estado': 'Activo',
            },
            {
                'id': 2,
                'codigo': 'ROL-COORD',
                'nombre': 'Coordinador Municipal',
                'descripcion': 'Supervisión transversal y monitoreo de compromisos comunales',
                'alcance_autorizado': 'COMUNAL',
                'permisos': 'Consultar, Listar, Exportar, Monitoreo Metas',
                'grupo': grupos_objs['Supervisor'],
                'estado': 'Activo',
            },
            {
                'id': 3,
                'codigo': 'ROL-DEL',
                'nombre': 'Delegado Municipal',
                'descripcion': 'Gestión y jefatura de delegación territorial asignada',
                'alcance_autorizado': 'DELEGACION',
                'permisos': 'Crear, Editar, Consultar, Listar, Exportar, Gestión Local',
                'grupo': grupos_objs['Supervisor'],
                'estado': 'Activo',
            },
            {
                'id': 4,
                'codigo': 'ROL-OPE',
                'nombre': 'Funcionario Operador',
                'descripcion': 'Atención ciudadana, registro de casos y gestiones en terreno',
                'alcance_autorizado': 'DELEGACION',
                'permisos': 'Crear Atención, Consultar, Listar Gestiones',
                'grupo': grupos_objs['Administrativo'],
                'estado': 'Activo',
            },
            {
                'id': 5,
                'codigo': 'ROL-VERIF',
                'nombre': 'Verificador Técnico',
                'descripcion': 'Auditoría y validación de evidencias fotográficas y documentales',
                'alcance_autorizado': 'DELEGACION',
                'permisos': 'Consultar, Validar Evidencias',
                'grupo': grupos_objs['Supervisor'],
                'estado': 'Activo',
            },
            {
                'id': 6,
                'codigo': 'ROL-GES',
                'nombre': 'Gestor Social',
                'descripcion': 'Profesional de atención social, visitas domiciliarias e informes FIBE',
                'alcance_autorizado': 'DELEGACION',
                'permisos': 'Crear Gestión Social, Consultar, Listar Gestiones Propias',
                'grupo': grupos_objs['Administrativo'],
                'estado': 'Activo',
            },
            {
                'id': 7,
                'codigo': 'ROL-TER',
                'nombre': 'Gestor Territorial OO.CC.',
                'descripcion': 'Coordinación con Juntas de Vecinos, hitos barriales y operativos en terreno',
                'alcance_autorizado': 'DELEGACION',
                'permisos': 'Crear Gestión Territorial, Consultar, Listar Gestiones Propias',
                'grupo': grupos_objs['Administrativo'],
                'estado': 'Activo',
            },
            {
                'id': 8,
                'codigo': 'ROL-DIS',
                'nombre': 'Coordinador DISERCO',
                'descripcion': 'Enlace de servicios a la comunidad y apoyo operativo rural/urbano',
                'alcance_autorizado': 'DELEGACION',
                'permisos': 'Crear Gestión Operativa, Consultar, Listar Gestiones Propias',
                'grupo': grupos_objs['Administrativo'],
                'estado': 'Activo',
            },
            {
                'id': 9,
                'codigo': 'ROL-GEST',
                'nombre': 'Perfil Gestión SGR',
                'descripcion': 'Perfil oficial con permisos completos de listado, detalle, creación, edición y eliminación/desactivación',
                'alcance_autorizado': 'COMUNAL',
                'permisos': 'Listar, Ver Detalle, Crear, Editar, Eliminar/Desactivar en las 17 entidades SGR',
                'grupo': grupos_objs['Gestión'],
                'estado': 'Activo',
            },
            {
                'id': 10,
                'codigo': 'ROL-CON',
                'nombre': 'Perfil Consulta SGR',
                'descripcion': 'Perfil oficial de solo lectura para consultar listados y detalles (sin permisos de escritura)',
                'alcance_autorizado': 'COMUNAL',
                'permisos': 'Listar, Ver Detalle (Creación, Edición y Eliminación bloqueadas con HTTP 403)',
                'grupo': grupos_objs['Consulta'],
                'estado': 'Activo',
            },
            {
                'id': 11,
                'codigo': 'ROL-INA',
                'nombre': 'Auditor Externo Histórico (Inactivo)',
                'descripcion': 'Rol temporal utilizado en auditoría anterior, actualmente inactivo y sin usuarios',
                'alcance_autorizado': 'COMUNAL',
                'permisos': 'Solo lectura histórica',
                'grupo': grupos_objs['Consulta'],
                'estado': 'Inactivo',
            },
        ]

        roles_objs = {}
        for r in roles_data:
            obj, _ = Rol.objects.update_or_create(
                codigo=r['codigo'],
                defaults={
                    'nombre': r['nombre'],
                    'descripcion': r['descripcion'],
                    'alcance_autorizado': r['alcance_autorizado'],
                    'permisos': r['permisos'],
                    'estado': r['estado'],
                }
            )
            roles_objs[r['codigo']] = obj
        self.stdout.write(self.style.SUCCESS(f'Entidad 5 (Rol): {len(roles_objs)} registros procesados.'))

        # ======================================================================
        # ENTIDAD 4: CARGO
        # ======================================================================
        cargos_data = [
            {
                'codigo': 'CRG-01',
                'nombre': 'Delegado Municipal',
                'descripcion': 'Jefatura territorial representante del Alcalde en la delegación municipal',
                'estado': 'Activo',
            },
            {
                'codigo': 'CRG-02',
                'nombre': 'Territorial OO.CC.',
                'descripcion': 'Encargado de vinculación con Juntas de Vecinos y organizaciones comunitarias',
                'estado': 'Activo',
            },
            {
                'codigo': 'CRG-03',
                'nombre': 'Gestor Social',
                'descripcion': 'Profesional encargado de diagnósticos sociales, visitas domiciliarias y ayudas paliativas',
                'estado': 'Activo',
            },
            {
                'codigo': 'CRG-04',
                'nombre': 'Prof. Planificación y Control',
                'descripcion': 'Analista de cumplimiento de metas trimestrales, indicadores y control de gestión',
                'estado': 'Activo',
            },
            {
                'codigo': 'CRG-05',
                'nombre': 'Coordinador DISERCO',
                'descripcion': 'Coordinador operativo de cuadrillas, tolvas, mantención de plazas y alumbrado',
                'estado': 'Activo',
            },
            {
                'codigo': 'CRG-06',
                'nombre': 'Asistente Técnico Histórico',
                'descripcion': 'Cargo en desuso para pruebas de estado inactivo y eliminación física',
                'estado': 'Inactivo',
            },
        ]

        cargos_objs = {}
        for c in cargos_data:
            obj, _ = Cargo.objects.update_or_create(
                codigo=c['codigo'],
                defaults={
                    'nombre': c['nombre'],
                    'descripcion': c['descripcion'],
                    'estado': c['estado'],
                }
            )
            cargos_objs[c['codigo']] = obj
        self.stdout.write(self.style.SUCCESS(f'Entidad 4 (Cargo): {len(cargos_objs)} registros procesados.'))

        # ======================================================================
        # ENTIDAD 1: DELEGACIÓN
        # ======================================================================
        delegaciones_data = [
            {
                'id': 1,
                'codigo': 'D01',
                'nombre': 'Delegación Municipal Las Compañías',
                'direccion': 'Esmeralda #2422, Las Compañías',
                'comuna': 'La Serena',
                'ambito': 'Las Compañías Alta y Baja',
                'responsable': 'He-Man',
                'foco_estrategico': 'Atención integral comunitaria, operativos sociales y resolución territorial rápida',
                'estado': 'Activa',
            },
            {
                'id': 2,
                'codigo': 'D02',
                'nombre': 'Delegación Municipal La Antena',
                'direccion': '12 de Octubre #1255, La Antena',
                'comuna': 'La Serena',
                'ambito': 'Sector La Antena y Florida',
                'responsable': 'Acuaman',
                'foco_estrategico': 'Seguridad vecinal, recuperación de espacios públicos y mediación comunitaria',
                'estado': 'Activa',
            },
            {
                'id': 3,
                'codigo': 'D03',
                'nombre': 'Delegación Municipal Centro y Casco Histórico',
                'direccion': 'Los Carrera #301, Centro',
                'comuna': 'La Serena',
                'ambito': 'Centro Urbano y Casco Histórico',
                'responsable': 'Pantera Negra',
                'foco_estrategico': 'Fiscalización comercial, turismo patrimonial y aseo urbano',
                'estado': 'Activa',
            },
            {
                'id': 4,
                'codigo': 'D04',
                'nombre': 'Delegación Municipal Rural',
                'direccion': 'Ruta D-41 Km 15, El Arrayán',
                'comuna': 'La Serena',
                'ambito': 'Valles y Localidades Rurales',
                'responsable': 'Capitana Marvel',
                'foco_estrategico': 'Conectividad hídrica, caminos rurales y apoyo a crianceros',
                'estado': 'Activa',
            },
            {
                'id': 5,
                'codigo': 'D05',
                'nombre': 'Delegación Municipal Costera (Histórica)',
                'direccion': 'Av. del Mar #4500, Sector El Faro',
                'comuna': 'La Serena',
                'ambito': 'Borde Costero Estacional',
                'responsable': 'Coordinación Estival',
                'foco_estrategico': 'Delegación estacional inactiva sin registros dependientes',
                'estado': 'Inactiva',
            },
        ]

        delegacion_objs = {}
        for d in delegaciones_data:
            obj, _ = Delegacion.objects.update_or_create(
                id_delegacion=d['id'],
                defaults={
                    'codigo': d['codigo'],
                    'nombre': d['nombre'],
                    'direccion': d['direccion'],
                    'comuna': d['comuna'],
                    'ambito': d['ambito'],
                    'responsable': d['responsable'],
                    'foco_estrategico': d['foco_estrategico'],
                    'estado': d['estado'],
                }
            )
            delegacion_objs[d['id']] = obj
        self.stdout.write(self.style.SUCCESS(f'Entidad 1 (Delegación): {len(delegacion_objs)} registros procesados.'))

        # ======================================================================
        # ENTIDAD 2: TERRITORIO
        # ======================================================================
        territorios_data = [
            {
                'codigo': 'TER-01',
                'nombre': 'Las Compañías Alta',
                'descripcion': 'Sector El Olivar, Minas del Brillador y Villa El Indio',
                'delegacion_id': 1,
                'estado': 'Activo',
            },
            {
                'codigo': 'TER-02',
                'nombre': 'Las Compañías Baja',
                'descripcion': 'Sector Islón, Villa Lambert y Eje Esmeralda Poniente',
                'delegacion_id': 1,
                'estado': 'Activo',
            },
            {
                'codigo': 'TER-03',
                'nombre': 'Sector La Antena y Florida',
                'descripcion': 'Población Juan XXIII, Coll y Panorámica La Florida',
                'delegacion_id': 2,
                'estado': 'Activo',
            },
            {
                'codigo': 'TER-04',
                'nombre': 'Centro Urbano y Casco Histórico',
                'descripcion': 'Cuadrante Patrimonial, Barrio Almagro y Eje Balmaceda',
                'delegacion_id': 3,
                'estado': 'Activo',
            },
            {
                'codigo': 'TER-05',
                'nombre': 'Valle El Romero y El Arrayán',
                'descripcion': 'Localidades rurales de la ribera norte y sur del Río Elqui',
                'delegacion_id': 4,
                'estado': 'Activo',
            },
            {
                'codigo': 'TER-06',
                'nombre': 'Polígono Industrial Norte (Inactivo)',
                'descripcion': 'Polígono territorial en revisión catastral sin organizaciones asociadas',
                'delegacion_id': 1,
                'estado': 'Inactivo',
            },
        ]

        territorio_objs = {}
        for t in territorios_data:
            obj, _ = Territorio.objects.update_or_create(
                codigo=t['codigo'],
                defaults={
                    'nombre': t['nombre'],
                    'descripcion': t['descripcion'],
                    'delegacion': delegacion_objs[t['delegacion_id']],
                    'estado': t['estado'],
                }
            )
            territorio_objs[t['codigo']] = obj
        self.stdout.write(self.style.SUCCESS(f'Entidad 2 (Territorio): {len(territorio_objs)} registros procesados.'))

        # ======================================================================
        # ENTIDAD 3: USUARIO FUNCIONARIO (auth.User + PerfilUsuario + Funcionario)
        # ======================================================================
        hashed_admin_pw = make_password('admin')
        admin_user, _ = User.objects.get_or_create(username='admin')
        admin_user.email = 'admin@laserena.cl'
        admin_user.first_name = 'Administrador'
        admin_user.last_name = 'Municipal SGR'
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.password = hashed_admin_pw
        admin_user.save()
        admin_user.groups.set([grupos_objs['Administrador']])

        perfil_admin, _ = PerfilUsuario.objects.get_or_create(user=admin_user)
        perfil_admin.rut = '11.111.111-1'
        perfil_admin.cargo = cargos_objs['CRG-04']
        perfil_admin.rol = roles_objs['ROL-ADM']
        perfil_admin.delegacion_activa = delegacion_objs[1]
        perfil_admin.telefono = '+56 9 9000 0001'
        perfil_admin.estado = 'Activo'
        perfil_admin.save()
        perfil_admin.roles.set([roles_objs['ROL-ADM']])
        perfil_admin.delegaciones_autorizadas.set([delegacion_objs[1], delegacion_objs[2], delegacion_objs[3], delegacion_objs[4]])

        usuarios_data = [
            {
                'username': 'coordinador',
                'email': 'coordinador@correo.cl',
                'first_name': 'Doctor Strange',
                'last_name': '(Coordinador Comunal)',
                'password': 'admin',
                'rut': '12.222.222-2',
                'cargo_cod': 'CRG-04',
                'rol_codigo': 'ROL-COORD',
                'grupo': 'Supervisor',
                'delegacion_id': 1,
                'delegaciones_ids': [1, 2, 3, 4],
                'estado': 'Activo',
            },
            {
                'username': 'gestion',
                'email': 'gestion@laserena.cl',
                'first_name': 'Mujer Maravilla',
                'last_name': '(Gestión SGR)',
                'password': 'admin',
                'rut': '13.333.333-3',
                'cargo_cod': 'CRG-04',
                'rol_codigo': 'ROL-GEST',
                'grupo': 'Gestión',
                'delegacion_id': 1,
                'delegaciones_ids': [1, 2, 3, 4],
                'estado': 'Activo',
            },
            {
                'username': 'consulta',
                'email': 'consulta@laserena.cl',
                'first_name': 'Batman',
                'last_name': '(Consulta SGR)',
                'password': 'admin',
                'rut': '14.444.444-4',
                'cargo_cod': 'CRG-04',
                'rol_codigo': 'ROL-CON',
                'grupo': 'Consulta',
                'delegacion_id': 1,
                'delegaciones_ids': [1, 2, 3, 4],
                'estado': 'Activo',
            },
            {
                'username': 'heman',
                'email': 'heman@correo.cl',
                'first_name': 'He-Man',
                'last_name': 'Delegado',
                'password': 'admin',
                'rut': '15.111.111-1',
                'cargo_cod': 'CRG-01',
                'rol_codigo': 'ROL-DEL',
                'grupo': 'Supervisor',
                'delegacion_id': 1,
                'delegaciones_ids': [1],
                'estado': 'Activo',
            },
            {
                'username': 'acuaman',
                'email': 'acuaman@correo.cl',
                'first_name': 'Acuaman',
                'last_name': 'Territorial',
                'password': 'admin',
                'rut': '15.222.222-2',
                'cargo_cod': 'CRG-02',
                'rol_codigo': 'ROL-TER',
                'grupo': 'Administrativo',
                'delegacion_id': 2,
                'delegaciones_ids': [2],
                'estado': 'Activo',
            },
            {
                'username': 'flash',
                'email': 'flash@correo.cl',
                'first_name': 'Flash',
                'last_name': 'Social',
                'password': 'admin',
                'rut': '15.333.333-3',
                'cargo_cod': 'CRG-03',
                'rol_codigo': 'ROL-GES',
                'grupo': 'Administrativo',
                'delegacion_id': 1,
                'delegaciones_ids': [1],
                'estado': 'Activo',
            },
            {
                'username': 'panteranegra',
                'email': 'panteranegra@correo.cl',
                'first_name': 'Pantera',
                'last_name': 'Negra',
                'password': 'admin',
                'rut': '15.444.444-4',
                'cargo_cod': 'CRG-04',
                'rol_codigo': 'ROL-OPE',
                'grupo': 'Administrativo',
                'delegacion_id': 3,
                'delegaciones_ids': [3],
                'estado': 'Activo',
            },
            {
                'username': 'capitanamarvel',
                'email': 'capitanamarvel@correo.cl',
                'first_name': 'Capitana',
                'last_name': 'Marvel',
                'password': 'admin',
                'rut': '15.555.555-5',
                'cargo_cod': 'CRG-05',
                'rol_codigo': 'ROL-DIS',
                'grupo': 'Administrativo',
                'delegacion_id': 4,
                'delegaciones_ids': [4],
                'estado': 'Activo',
            },
            {
                'username': 'hulk',
                'email': 'hulk@correo.cl',
                'first_name': 'Hulk',
                'last_name': 'Social',
                'password': 'admin',
                'rut': '15.666.666-6',
                'cargo_cod': 'CRG-03',
                'rol_codigo': 'ROL-GES',
                'grupo': 'Administrativo',
                'delegacion_id': 3,
                'delegaciones_ids': [3],
                'estado': 'Activo',
            },
            {
                'username': 'capitanamerica',
                'email': 'capitanamerica@correo.cl',
                'first_name': 'Capitán',
                'last_name': 'América',
                'password': 'admin',
                'rut': '15.777.777-7',
                'cargo_cod': 'CRG-03',
                'rol_codigo': 'ROL-GES',
                'grupo': 'Administrativo',
                'delegacion_id': 2,
                'delegaciones_ids': [2],
                'estado': 'Activo',
            },
            {
                'username': 'spiderman',
                'email': 'spiderman@correo.cl',
                'first_name': 'Spider',
                'last_name': 'Man',
                'password': 'admin',
                'rut': '15.888.888-8',
                'cargo_cod': 'CRG-02',
                'rol_codigo': 'ROL-TER',
                'grupo': 'Administrativo',
                'delegacion_id': 1,
                'delegaciones_ids': [1],
                'estado': 'Activo',
            },
            {
                'username': 'funcionario_inactivo',
                'email': 'ironman@correo.cl',
                'first_name': 'Iron',
                'last_name': 'Man (Inactivo)',
                'password': 'admin',
                'rut': '15.999.999-9',
                'cargo_cod': 'CRG-03',
                'rol_codigo': 'ROL-OPE',
                'grupo': 'Consulta',
                'delegacion_id': 1,
                'delegaciones_ids': [1],
                'estado': 'Inactivo',
            },
        ]

        # Eliminar cuentas de prueba huérfanas que no pertenezcan al listado oficial y asegurar clave 'admin' en todas
        usernames_oficiales = {'admin'} | {u['username'] for u in usuarios_data}
        User.objects.exclude(username__in=usernames_oficiales).delete()

        for u in usuarios_data:
            user, _ = User.objects.get_or_create(username=u['username'])
            user.email = u['email']
            user.first_name = u['first_name']
            user.last_name = u['last_name']
            user.is_staff = False
            user.is_superuser = False
            user.is_active = (u['estado'] == 'Activo')
            user.password = hashed_admin_pw
            user.save()
            user.groups.set([grupos_objs[u['grupo']]])

            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.rut = u['rut']
            perfil.cargo = cargos_objs[u['cargo_cod']]
            perfil.rol = roles_objs[u['rol_codigo']]
            perfil.delegacion_activa = delegacion_objs[u['delegacion_id']]
            perfil.telefono = '+56 9 8000 1000'
            perfil.estado = u['estado']
            perfil.save()
            perfil.roles.set([roles_objs[u['rol_codigo']]])
            perfil.delegaciones_autorizadas.set([delegacion_objs[did] for did in u['delegaciones_ids']])

        funcionarios_data = [
            {'id': 1, 'delegacion_id': 1, 'rut': '15.111.111-1', 'nombres': 'He-Man', 'apellidos': 'Delegado', 'nombre': 'He-Man', 'cargo': 'Delegado Municipal', 'cargo_cod': 'CRG-01', 'activo': True, 'estado': 'Activo', 'fecha_ingreso': datetime.date(2024, 1, 1), 'username': 'heman'},
            {'id': 2, 'delegacion_id': 2, 'rut': '15.222.222-2', 'nombres': 'Acuaman', 'apellidos': 'Territorial', 'nombre': 'Acuaman', 'cargo': 'Territorial OO.CC. 1', 'cargo_cod': 'CRG-02', 'activo': True, 'estado': 'Activo', 'fecha_ingreso': datetime.date(2024, 3, 15), 'username': 'acuaman'},
            {'id': 3, 'delegacion_id': 1, 'rut': '15.333.333-3', 'nombres': 'Flash', 'apellidos': 'Social', 'nombre': 'Flash', 'cargo': 'Gestor Social 1', 'cargo_cod': 'CRG-03', 'activo': True, 'estado': 'Activo', 'fecha_ingreso': datetime.date(2024, 2, 1), 'username': 'flash'},
            {'id': 4, 'delegacion_id': 3, 'rut': '15.444.444-4', 'nombres': 'Pantera', 'apellidos': 'Negra', 'nombre': 'Pantera Negra', 'cargo': 'Prof. Planificación y Control', 'cargo_cod': 'CRG-04', 'activo': True, 'estado': 'Activo', 'fecha_ingreso': datetime.date(2024, 1, 10), 'username': 'panteranegra'},
            {'id': 5, 'delegacion_id': 4, 'rut': '15.555.555-5', 'nombres': 'Capitana', 'apellidos': 'Marvel', 'nombre': 'Capitana Marvel', 'cargo': 'Coordinador DISERCO', 'cargo_cod': 'CRG-05', 'activo': True, 'estado': 'Activo', 'fecha_ingreso': datetime.date(2024, 4, 1), 'username': 'capitanamarvel'},
            {'id': 6, 'delegacion_id': 3, 'rut': '15.666.666-6', 'nombres': 'Hulk', 'apellidos': 'Social', 'nombre': 'Hulk', 'cargo': 'Gestor Social 3', 'cargo_cod': 'CRG-03', 'activo': True, 'estado': 'Activo', 'fecha_ingreso': datetime.date(2024, 2, 15), 'username': 'hulk'},
            {'id': 7, 'delegacion_id': 2, 'rut': '15.777.777-7', 'nombres': 'Capitán', 'apellidos': 'América', 'nombre': 'Capitán América', 'cargo': 'Gestor Social 2', 'cargo_cod': 'CRG-03', 'activo': True, 'estado': 'Activo', 'fecha_ingreso': datetime.date(2024, 3, 1), 'username': 'capitanamerica'},
            {'id': 8, 'delegacion_id': 1, 'rut': '15.888.888-8', 'nombres': 'Spider', 'apellidos': 'Man', 'nombre': 'Spider-Man', 'cargo': 'Territorial OO.CC. 2', 'cargo_cod': 'CRG-02', 'activo': True, 'estado': 'Activo', 'fecha_ingreso': datetime.date(2024, 5, 10), 'username': 'spiderman'},
            {'id': 9, 'delegacion_id': 1, 'rut': '15.999.999-9', 'nombres': 'Iron', 'apellidos': 'Man', 'nombre': 'Iron Man (Inactivo)', 'cargo': 'Gestor Social', 'cargo_cod': 'CRG-03', 'activo': False, 'estado': 'Inactivo', 'fecha_ingreso': datetime.date(2023, 6, 1), 'username': 'funcionario_inactivo'},
        ]

        funcionario_objs = {}
        for f in funcionarios_data:
            user_f = User.objects.filter(username=f['username']).first()
            obj, _ = Funcionario.objects.update_or_create(
                id_funcionario=f['id'],
                defaults={
                    'id_delegacion': delegacion_objs[f['delegacion_id']],
                    'rut': f['rut'],
                    'nombres': f['nombres'],
                    'apellidos': f['apellidos'],
                    'nombre': f['nombre'],
                    'cargo': f['cargo'],
                    'cargo_rel': cargos_objs[f['cargo_cod']],
                    'correo': user_f.email if user_f else '',
                    'telefono': '+56 9 8000 1000',
                    'activo': f['activo'],
                    'estado': f['estado'],
                    'fecha_ingreso': f['fecha_ingreso'],
                    'user': user_f,
                }
            )
            funcionario_objs[f['id']] = obj

        # Vincular delegado titular a cada delegación activa
        delegacion_objs[1].delegado = funcionario_objs[1]
        delegacion_objs[1].save()
        delegacion_objs[2].delegado = funcionario_objs[2]
        delegacion_objs[2].save()
        delegacion_objs[3].delegado = funcionario_objs[4]
        delegacion_objs[3].save()
        delegacion_objs[4].delegado = funcionario_objs[5]
        delegacion_objs[4].save()
        self.stdout.write(self.style.SUCCESS(f'Entidad 3 (Usuario Funcionario): {len(usuarios_data) + 1} usuarios y {len(funcionario_objs)} fichas de funcionarios procesados.'))

        # ======================================================================
        # ENTIDAD 6: VECINO
        # ======================================================================
        vecinos_data = [
            {
                'rut': '16.100.100-1',
                'nombres': 'Diana',
                'apellidos': 'Prince (Mujer Maravilla)',
                'nombre': 'Diana Prince (Mujer Maravilla)',
                'telefono': '+56 9 7111 2201',
                'correo': 'mujermaravilla@vecinoslaserena.cl',
                'direccion': 'Av. Viña del Mar #1420, Las Compañías',
                'territorio_cod': 'TER-01',
                'estado': 'Activo',
            },
            {
                'rut': '16.200.200-2',
                'nombres': 'Clark',
                'apellidos': 'Kent (Superman)',
                'nombre': 'Clark Kent (Superman)',
                'telefono': '+56 9 7111 2202',
                'correo': 'superman@vecinoslaserena.cl',
                'direccion': 'Calle 18 de Septiembre #880, La Antena',
                'territorio_cod': 'TER-03',
                'estado': 'Activo',
            },
            {
                'rut': '16.300.300-3',
                'nombres': 'Bruce',
                'apellidos': 'Wayne (Batman)',
                'nombre': 'Bruce Wayne (Batman)',
                'telefono': '+56 9 7111 2203',
                'correo': 'batman@vecinoslaserena.cl',
                'direccion': 'Calle Almagro #412, Casco Histórico',
                'territorio_cod': 'TER-04',
                'estado': 'Activo',
            },
            {
                'rut': '16.400.400-4',
                'nombres': 'Thor',
                'apellidos': 'Odinson (Asgard)',
                'nombre': 'Thor Odinson (Asgard)',
                'telefono': '+56 9 7111 2204',
                'correo': 'thor@vecinoslaserena.cl',
                'direccion': 'Parcela 14 El Romero, Sector Rural',
                'territorio_cod': 'TER-05',
                'estado': 'Activo',
            },
            {
                'rut': '16.500.500-5',
                'nombres': 'Natasha',
                'apellidos': 'Romanoff (Viuda Negra)',
                'nombre': 'Natasha Romanoff (Viuda Negra)',
                'telefono': '+56 9 7111 2205',
                'correo': 'viudanegra@vecinoslaserena.cl',
                'direccion': 'Pasaje El Brillador #210, Las Compañías',
                'territorio_cod': 'TER-02',
                'estado': 'Activo',
            },
            {
                'rut': '16.600.600-6',
                'nombres': 'Hal',
                'apellidos': 'Jordan (Linterna Verde)',
                'nombre': 'Hal Jordan (Linterna Verde)',
                'telefono': '+56 9 7111 2206',
                'correo': 'linternaverde@vecinoslaserena.cl',
                'direccion': 'Calle Esmeralda #1990, Las Compañías',
                'territorio_cod': 'TER-01',
                'estado': 'Inactivo',
            },
        ]

        vecino_objs = {}
        for v in vecinos_data:
            ter_obj = territorio_objs[v['territorio_cod']]
            obj, _ = Vecino.objects.update_or_create(
                rut=v['rut'],
                defaults={
                    'nombres': v['nombres'],
                    'apellidos': v['apellidos'],
                    'nombre': v['nombre'],
                    'telefono': v['telefono'],
                    'correo': v['correo'],
                    'direccion': v['direccion'],
                    'territorio_rel': ter_obj,
                    'territorio': ter_obj.nombre,
                    'estado': v['estado'],
                }
            )
            vecino_objs[v['rut']] = obj
        self.stdout.write(self.style.SUCCESS(f'Entidad 6 (Vecino): {len(vecino_objs)} registros procesados.'))

        # ======================================================================
        # ENTIDAD 7: JUNTA DE VECINOS
        # ======================================================================
        juntas_data = [
            {
                'codigo': 'JJVV-01',
                'nombre': 'Junta de Vecinos N° 12 Villa El Indio',
                'direccion': 'Sede Comunitaria Pasaje Arauco #340, Las Compañías',
                'delegacion_id': 1,
                'territorio_cod': 'TER-01',
                'fecha_constitucion': datetime.date(1998, 5, 14),
                'estado': 'Activa',
            },
            {
                'codigo': 'JJVV-02',
                'nombre': 'Junta de Vecinos N° 8 Juan XXIII La Antena',
                'direccion': 'Av. 12 de Octubre #1410, La Antena',
                'delegacion_id': 2,
                'territorio_cod': 'TER-03',
                'fecha_constitucion': datetime.date(1995, 8, 20),
                'estado': 'Activa',
            },
            {
                'codigo': 'JJVV-03',
                'nombre': 'Junta de Vecinos N° 1 Casco Histórico',
                'direccion': 'Calle Rengifo #245, Centro',
                'delegacion_id': 3,
                'territorio_cod': 'TER-04',
                'fecha_constitucion': datetime.date(1992, 3, 10),
                'estado': 'Activa',
            },
            {
                'codigo': 'JJVV-04',
                'nombre': 'Junta de Vecinos N° 25 El Arrayán Rural',
                'direccion': 'Camino Principal s/n Km 16, El Arrayán',
                'delegacion_id': 4,
                'territorio_cod': 'TER-05',
                'fecha_constitucion': datetime.date(2004, 11, 5),
                'estado': 'Activa',
            },
            {
                'codigo': 'JJVV-05',
                'nombre': 'Junta de Vecinos N° 99 Sector Antiguo (Inactiva)',
                'direccion': 'Sede Provisoria Sector Norte #102',
                'delegacion_id': 1,
                'territorio_cod': 'TER-02',
                'fecha_constitucion': datetime.date(2001, 7, 15),
                'estado': 'Inactiva',
            },
        ]

        junta_objs = {}
        for j in juntas_data:
            obj, _ = JuntaVecinos.objects.update_or_create(
                codigo=j['codigo'],
                defaults={
                    'nombre': j['nombre'],
                    'direccion': j['direccion'],
                    'delegacion': delegacion_objs[j['delegacion_id']],
                    'territorio': territorio_objs[j['territorio_cod']],
                    'fecha_constitucion': j['fecha_constitucion'],
                    'estado': j['estado'],
                }
            )
            junta_objs[j['codigo']] = obj
        self.stdout.write(self.style.SUCCESS(f'Entidad 7 (Junta de Vecinos): {len(junta_objs)} registros procesados.'))

        # ======================================================================
        # ENTIDAD 8: PARTICIPACIÓN EN JUNTA
        # ======================================================================
        participaciones_data = [
            {
                'codigo': 'PAR-01',
                'vecino_rut': '16.100.100-1',
                'junta_cod': 'JJVV-01',
                'es_dirigente': True,
                'cargo': 'Presidente/a',
                'fecha_incorporacion': datetime.date(2024, 3, 1),
                'estado': 'Activo',
            },
            {
                'codigo': 'PAR-02',
                'vecino_rut': '16.200.200-2',
                'junta_cod': 'JJVV-02',
                'es_dirigente': True,
                'cargo': 'Secretario/a',
                'fecha_incorporacion': datetime.date(2024, 4, 10),
                'estado': 'Activo',
            },
            {
                'codigo': 'PAR-03',
                'vecino_rut': '16.300.300-3',
                'junta_cod': 'JJVV-03',
                'es_dirigente': False,
                'cargo': 'Socio/a Activo/a',
                'fecha_incorporacion': datetime.date(2024, 6, 15),
                'estado': 'Activo',
            },
            {
                'codigo': 'PAR-04',
                'vecino_rut': '16.400.400-4',
                'junta_cod': 'JJVV-01',
                'es_dirigente': True,
                'cargo': 'Tesorero/a',
                'fecha_incorporacion': datetime.date(2023, 5, 20),
                'estado': 'Inactivo',
            },
        ]

        part_objs = {}
        for p in participaciones_data:
            obj, _ = ParticipacionJunta.objects.update_or_create(
                vecino=vecino_objs[p['vecino_rut']],
                junta=junta_objs[p['junta_cod']],
                defaults={
                    'codigo': p['codigo'],
                    'es_dirigente': p['es_dirigente'],
                    'cargo': p['cargo'],
                    'fecha_incorporacion': p['fecha_incorporacion'],
                    'estado': p['estado'],
                }
            )
            part_objs[p['codigo']] = obj
        self.stdout.write(self.style.SUCCESS(f'Entidad 8 (Participación en Junta): {len(part_objs)} registros procesados.'))

        # ======================================================================
        # ENTIDAD 9: HITO
        # ======================================================================
        hitos_data = [
            {
                'codigo': 'HIT-01',
                'nombre': 'Operativo Integral de Invierno Las Compañías',
                'descripcion': 'Despliegue preventivo de limpieza de sumideros, entrega de nylon y atención FIBE en terreno',
                'periodicidad': 'Anual',
                'fecha_inicio': datetime.date(2026, 1, 15),
                'fecha_termino': datetime.date(2026, 2, 15),
                'delegacion_id': 1,
                'territorio_cod': 'TER-01',
                'responsable_id': 1,
                'responsables_ids': [1, 3, 8],
                'estado': 'Realizado',
            },
            {
                'codigo': 'HIT-02',
                'nombre': 'Mesa Territorial de Seguridad Vecinal La Antena',
                'descripcion': 'Coordinación trimestral con dirigentes vecinales, Carabineros e Inspección Municipal',
                'periodicidad': 'Trimestral',
                'fecha_inicio': datetime.date(2026, 2, 1),
                'fecha_termino': datetime.date(2026, 3, 30),
                'delegacion_id': 2,
                'territorio_cod': 'TER-03',
                'responsable_id': 2,
                'responsables_ids': [2, 7],
                'estado': 'En Ejecución',
            },
            {
                'codigo': 'HIT-03',
                'nombre': 'Cabildo Patrimonial y Limpieza Centro Histórico',
                'descripcion': 'Jornada participativa de recuperación de fachadas y fiscalización de comercio ambulante',
                'periodicidad': 'Semestral',
                'fecha_inicio': datetime.date(2026, 3, 1),
                'fecha_termino': datetime.date(2026, 3, 25),
                'delegacion_id': 3,
                'territorio_cod': 'TER-04',
                'responsable_id': 4,
                'responsables_ids': [4, 6],
                'estado': 'Programado',
            },
            {
                'codigo': 'HIT-04',
                'nombre': 'Feria Comunitaria Sector Norte (Inactivo)',
                'descripcion': 'Hito reprogramado sin actividades vinculadas para prueba de estado inactivo',
                'periodicidad': 'Único',
                'fecha_inicio': datetime.date(2026, 1, 10),
                'fecha_termino': datetime.date(2026, 1, 12),
                'delegacion_id': 1,
                'territorio_cod': 'TER-02',
                'responsable_id': 8,
                'responsables_ids': [8],
                'estado': 'Inactivo',
            },
        ]

        hito_objs = {}
        for h in hitos_data:
            obj, _ = Hito.objects.update_or_create(
                codigo=h['codigo'],
                defaults={
                    'nombre': h['nombre'],
                    'descripcion': h['descripcion'],
                    'periodicidad': h['periodicidad'],
                    'fecha_inicio': h['fecha_inicio'],
                    'fecha_termino': h['fecha_termino'],
                    'delegacion': delegacion_objs[h['delegacion_id']],
                    'territorio': territorio_objs[h['territorio_cod']],
                    'responsable': funcionario_objs[h['responsable_id']],
                    'estado': h['estado'],
                }
            )
            obj.responsables.set([funcionario_objs[fid] for fid in h['responsables_ids']])
            hito_objs[h['codigo']] = obj
        self.stdout.write(self.style.SUCCESS(f'Entidad 9 (Hito): {len(hito_objs)} registros procesados.'))

        # ======================================================================
        # ENTIDAD 12 (TIPO DE ATENCIÓN) Y ENTIDAD 13 (SUBTIPO DE ATENCIÓN)
        # ======================================================================
        tipos_atencion_data = [
            {
                'codigo': 'TIP-SOC',
                'nombre': 'Atención Social y Beneficios',
                'descripcion': 'Asistencia económica, subsidios familiares y ayudas técnicas inmediatas',
                'estado': 'Activo',
                'subatenciones': [
                    ('SUB-ORI', 'Orientación Social y Registro Social de Hogares', 'Activo'),
                    ('SUB-FIBE', 'Aplicación de Ficha FIBE', 'Activo'),
                    ('SUB-SUBS', 'Postulación a Subsidios de Agua y Vivienda', 'Activo'),
                    ('SUB-ALIM', 'Entrega de Cajas de Alimentos y Albergue', 'Activo'),
                    ('SUB-INA', 'Subatención Piloto Suspendida (Inactiva)', 'Inactivo'),
                ]
            },
            {
                'codigo': 'TIP-TERR',
                'nombre': 'Gestión Territorial y Obras',
                'descripcion': 'Requerimientos de luminarias, bacheo, aseo y plazas vecinales',
                'estado': 'Activo',
                'subatenciones': [
                    ('SUB-LUM', 'Reparación de Luminarias y Alumbrado Público', 'Activo'),
                    ('SUB-ASEO', 'Operativo de Tolvas y Retiro de Escombros', 'Activo'),
                    ('SUB-PLAZ', 'Mantención y Riego de Áreas Verdes / Plazas', 'Activo'),
                    ('SUB-BACH', 'Bacheo y Señalización Vial', 'Activo'),
                ]
            },
            {
                'codigo': 'TIP-SEG',
                'nombre': 'Seguridad Ciudadana e Inspección',
                'descripcion': 'Denuncias vecinales, patrullaje preventivo y mediación comunitaria',
                'estado': 'Activo',
                'subatenciones': [
                    ('SUB-PATR', 'Solicitud de Patrullaje Preventivo', 'Activo'),
                    ('SUB-RUID', 'Mediación Vecinal por Ruidos Molestos', 'Activo'),
                    ('SUB-COME', 'Fiscalización de Comercio Informal', 'Activo'),
                ]
            },
            {
                'codigo': 'TIP-INA',
                'nombre': 'Zonificación Piloto Histórica (Inactiva)',
                'descripcion': 'Tipología en desuso sin subatenciones ni gestiones asociadas',
                'estado': 'Inactivo',
                'subatenciones': []
            },
        ]

        tipo_objs = {}
        subatencion_objs = {}
        for tip in tipos_atencion_data:
            tipo_obj, _ = TipoAtencion.objects.update_or_create(
                codigo=tip['codigo'],
                defaults={
                    'nombre': tip['nombre'],
                    'descripcion': tip['descripcion'],
                    'estado': tip['estado'],
                }
            )
            tipo_objs[tip['codigo']] = tipo_obj

            for sub_cod, sub_nom, sub_est in tip['subatenciones']:
                sub_obj, _ = SubAtencion.objects.update_or_create(
                    codigo=sub_cod,
                    defaults={
                        'id_tipo': tipo_obj,
                        'nombre': sub_nom,
                        'estado': sub_est,
                    }
                )
                subatencion_objs[sub_cod] = sub_obj

        # Mapeo Cargo -> TipoAtencion
        mapeo_cargos = [
            ('Delegado Municipal', ['TIP-SOC', 'TIP-TERR', 'TIP-SEG']),
            ('Territorial OO.CC.', ['TIP-TERR', 'TIP-SEG']),
            ('Gestor Social', ['TIP-SOC']),
            ('Prof. Planificación y Control', ['TIP-SOC', 'TIP-TERR', 'TIP-SEG']),
            ('Coordinador DISERCO', ['TIP-TERR', 'TIP-SEG']),
        ]
        for cargo_txt, lista_tipos in mapeo_cargos:
            for t_cod in lista_tipos:
                CargoTipoGestion.objects.get_or_create(
                    cargo=cargo_txt,
                    id_tipo=tipo_objs[t_cod]
                )
        self.stdout.write(self.style.SUCCESS(f'Entidad 12 (TipoAtencion: {len(tipo_objs)}) y Entidad 13 (SubAtencion: {len(subatencion_objs)}) procesadas.'))

        # ======================================================================
        # ENTIDAD 14: META (ItemMeta)
        # ======================================================================
        items_data = [
            {
                'codigo': 'I01',
                'nombre': 'Atención de Usuario Presencial y Telefónica',
                'descripcion': 'Recepción, registro y orientación personalizada de vecinos en delegación',
                'tipo_meta': 'Cuantitativa',
                'unidad_medida': 'Atenciones registradas',
                'requisito_evidencia': 'Planilla de atención firmada o folio SGR validado',
                'estado': 'Activo',
            },
            {
                'codigo': 'I02',
                'nombre': 'Informes Sociales y Ficha FIBE',
                'descripcion': 'Levantamiento de peritajes sociales y aplicación de ficha básica de emergencia',
                'tipo_meta': 'Cuantitativa',
                'unidad_medida': 'Informes emitidos',
                'requisito_evidencia': 'Informe social firmado o comprobante FIBE',
                'estado': 'Activo',
            },
            {
                'codigo': 'I03',
                'nombre': 'Gestión Territorial y Operativos en Terreno',
                'descripcion': 'Visitas a juntas de vecinos, supervisión de microbasurales y espacios públicos',
                'tipo_meta': 'Cuantitativa',
                'unidad_medida': 'Operativos ejecutados',
                'requisito_evidencia': 'Fotografía georreferenciada antes y después',
                'estado': 'Activo',
            },
            {
                'codigo': 'I04',
                'nombre': 'Emergencias Comunales y Contingencias',
                'descripcion': 'Respuesta rápida ante emergencias climáticas, cortes de servicios o siniestros',
                'tipo_meta': 'Cuantitativa',
                'unidad_medida': 'Contingencias atendidas',
                'requisito_evidencia': 'Acta de entrega de ayuda o reporte de emergencia',
                'estado': 'Activo',
            },
            {
                'codigo': 'I05',
                'nombre': 'Capacitación y Participación Ciudadana',
                'descripcion': 'Talleres comunitarios, mesas de trabajo barriales y difusión municipal',
                'tipo_meta': 'Cualitativa',
                'unidad_medida': 'Jornadas participativas',
                'requisito_evidencia': 'Lista de asistencia y registro fotográfico',
                'estado': 'Activo',
            },
            {
                'codigo': 'I06',
                'nombre': 'Meta Histórica de Archivo Físico (Inactiva)',
                'descripcion': 'Meta descontinuada tras la digitalización del SGR municipal',
                'tipo_meta': 'Cuantitativa',
                'unidad_medida': 'Expedientes archivados',
                'requisito_evidencia': 'Acta de archivo',
                'estado': 'Inactivo',
            },
        ]

        item_objs = {}
        for item in items_data:
            obj, _ = ItemMeta.objects.update_or_create(
                codigo=item['codigo'],
                defaults={
                    'nombre': item['nombre'],
                    'descripcion': item['descripcion'],
                    'tipo_meta': item['tipo_meta'],
                    'unidad_medida': item['unidad_medida'],
                    'requisito_evidencia': item['requisito_evidencia'],
                    'estado': item['estado'],
                }
            )
            item_objs[item['codigo']] = obj
        self.stdout.write(self.style.SUCCESS(f'Entidad 14 (Meta / ItemMeta): {len(item_objs)} registros procesados.'))

        # ======================================================================
        # ENTIDAD 17: TRIMESTRE (PeriodoEvaluacion)
        # ======================================================================
        trimestres_data = [
            {
                'codigo': 'TRI-2025-4',
                'nombre': '4° Trimestre 2025 (Octubre - Diciembre)',
                'anio': 2025,
                'numero': 4,
                'fecha_inicio': datetime.date(2025, 10, 1),
                'fecha_cierre': datetime.date(2025, 12, 31),
                'activo': False,
                'estado': 'Cerrado',
            },
            {
                'codigo': 'TRI-2026-1',
                'nombre': '1° Trimestre 2026 (Enero - Marzo)',
                'anio': 2026,
                'numero': 1,
                'fecha_inicio': datetime.date(2026, 1, 1),
                'fecha_cierre': datetime.date(2026, 3, 31),
                'activo': True,
                'estado': 'Activo',
            },
            {
                'codigo': 'TRI-2026-2',
                'nombre': '2° Trimestre 2026 (Abril - Junio) - En Preparación',
                'anio': 2026,
                'numero': 2,
                'fecha_inicio': datetime.date(2026, 4, 1),
                'fecha_cierre': datetime.date(2026, 6, 30),
                'activo': False,
                'estado': 'Inactivo',
            },
        ]

        periodo_objs = {}
        for p in trimestres_data:
            obj, _ = PeriodoEvaluacion.objects.update_or_create(
                codigo=p['codigo'],
                defaults={
                    'nombre': p['nombre'],
                    'anio': p['anio'],
                    'numero': p['numero'],
                    'fecha_inicio': p['fecha_inicio'],
                    'fecha_cierre': p['fecha_cierre'],
                    'activo': p['activo'],
                    'estado': p['estado'],
                }
            )
            periodo_objs[p['codigo']] = obj
        self.stdout.write(self.style.SUCCESS(f'Entidad 17 (Trimestre / PeriodoEvaluacion): {len(periodo_objs)} registros procesados.'))

        # ======================================================================
        # ENTIDAD 15: ASIGNACIÓN DE META (MetaFuncionario)
        # ======================================================================
        asignaciones_config = [
            (1, 'I03', 20, 50, 14),
            (1, 'I05', 15, 50, 11),
            (2, 'I03', 25, 60, 19),
            (2, 'I05', 15, 40, 12),
            (3, 'I01', 30, 50, 24),
            (3, 'I02', 20, 50, 16),
            (4, 'I01', 20, 50, 15),
            (4, 'I05', 20, 50, 14),
            (5, 'I03', 30, 60, 22),
            (5, 'I04', 15, 40, 11),
            (6, 'I01', 25, 50, 20),
            (6, 'I02', 20, 50, 15),
            (7, 'I01', 25, 50, 18),
            (7, 'I02', 20, 50, 14),
            (8, 'I03', 25, 60, 19),
            (8, 'I04', 15, 40, 10),
        ]

        asignacion_objs = {}
        for idx, (func_id, item_cod, meta_val, pond_val, avance_val) in enumerate(asignaciones_config, start=1):
            cod_asg = f"ASG-{idx:04d}"
            item_m = item_objs[item_cod]
            obj, _ = MetaFuncionario.objects.update_or_create(
                codigo=cod_asg,
                defaults={
                    'id_funcionario': funcionario_objs[func_id],
                    'id_periodo': periodo_objs['TRI-2026-1'],
                    'id_item_meta': item_m,
                    'item': item_m.nombre,
                    'meta_periodo': meta_val,
                    'ponderador': pond_val,
                    'avance_actual': avance_val,
                    'fecha_asignacion': datetime.date(2026, 1, 5),
                    'observacion': f'Asignación trimestral oficial para {funcionario_objs[func_id].nombre}',
                    'estado': 'Activa',
                }
            )
            asignacion_objs[cod_asg] = obj

        # Registro 17 inactivo y sin actividades asociadas (para pruebas de estado inactivo y eliminación física)
        obj_asg_ina, _ = MetaFuncionario.objects.update_or_create(
            codigo='ASG-0017',
            defaults={
                'id_funcionario': funcionario_objs[4],
                'id_periodo': periodo_objs['TRI-2025-4'],
                'id_item_meta': item_objs['I05'],
                'item': item_objs['I05'].nombre,
                'meta_periodo': 10,
                'ponderador': 25,
                'avance_actual': 0,
                'fecha_asignacion': datetime.date(2025, 10, 5),
                'observacion': 'Asignación histórica inactiva sin actividades imputadas',
                'estado': 'Inactiva',
            }
        )
        asignacion_objs['ASG-0017'] = obj_asg_ina
        self.stdout.write(self.style.SUCCESS(f'Entidad 15 (Asignación de Meta): {len(asignacion_objs)} registros procesados.'))

        # ======================================================================
        # ENTIDAD 11: GESTIÓN SOCIAL (GestionSocial)
        # ======================================================================
        gestiones_sociales_data = [
            {
                'codigo': 'SOC-00001',
                'fecha_ingreso': datetime.date(2026, 1, 18),
                'fecha_atencion': datetime.date(2026, 1, 19),
                'tipo_cod': 'TIP-SOC',
                'sub_cod': 'SUB-FIBE',
                'vecino_rut': '16.100.100-1',
                'derivacion': 'DIDECO - Departamento de Asistencia Social',
                'requiere_visita': True,
                'fecha_programada_visita': datetime.date(2026, 1, 20),
                'ingreso_tubo': False,
                'observaciones': 'Hogar unipersonal de adulto mayor con requerimiento de ayuda paliativa e informe social.',
                'informe_detalle': 'Informe Social N° 45/2026 favorable para entrega de caja de alimentos y frazadas.',
                'beneficio_entregado': '1 Caja de Alimentos + 2 Frazadas térmicas',
                'primera_gestion': 'ATENCIÓN SOCIAL A USUARIO PRESENCIAL',
                'segunda_gestion': 'VISITA TERRENO E INFORME FIBE',
                'fecha_visita': datetime.date(2026, 1, 20),
                'fecha_entrega_informe': datetime.date(2026, 1, 22),
                'tercera_gestion': 'ENTREGA BENEFICIO Y MATERIALES',
                'fecha_entrega_beneficio': datetime.date(2026, 1, 24),
                'func_id': 3,
                'del_id': 1,
                'asg_cod': 'ASG-0006',
                'estado': 'Resuelto',
                'resultado_texto': 'Beneficio entregado satisfactoriamente con acta firmada.',
            },
            {
                'codigo': 'SOC-00002',
                'fecha_ingreso': datetime.date(2026, 2, 3),
                'fecha_atencion': datetime.date(2026, 2, 4),
                'tipo_cod': 'TIP-SOC',
                'sub_cod': 'SUB-ALIM',
                'vecino_rut': '16.200.200-2',
                'derivacion': 'Oficina de Subsidios y Pensiones',
                'requiere_visita': True,
                'fecha_programada_visita': datetime.date(2026, 2, 10),
                'ingreso_tubo': True,
                'observaciones': 'Familia numerosa solicita apoyo alimentario y actualización de RSH.',
                'informe_detalle': 'Peritaje socioeconómico en redacción tras visita domiciliaria en La Antena.',
                'beneficio_entregado': 'En gestión de bodega social',
                'primera_gestion': 'ATENCIÓN SOCIAL A USUARIO PRESENCIAL',
                'segunda_gestion': 'VISITA DOMICILIARIA REALIZADA',
                'fecha_visita': datetime.date(2026, 2, 10),
                'fecha_entrega_informe': datetime.date(2026, 2, 12),
                'tercera_gestion': 'PENDIENTE ENTREGA DE BENEFICIO',
                'fecha_entrega_beneficio': None,
                'func_id': 7,
                'del_id': 2,
                'asg_cod': 'ASG-0013',
                'estado': 'En Proceso',
                'resultado_texto': 'Informe social aprobado, programada entrega de aporte.',
            },
            {
                'codigo': 'SOC-00003',
                'fecha_ingreso': datetime.date(2026, 2, 14),
                'fecha_atencion': datetime.date(2026, 2, 15),
                'tipo_cod': 'TIP-SOC',
                'sub_cod': 'SUB-SUBS',
                'vecino_rut': '16.300.300-3',
                'derivacion': 'Departamento de Vivienda y Subsidios Agua Potable',
                'requiere_visita': False,
                'fecha_programada_visita': None,
                'ingreso_tubo': False,
                'observaciones': 'Orientación y postulación a Subsidio de Agua Potable (SAP) urbano.',
                'informe_detalle': 'Documentación verificada y cargada en plataforma ministerial.',
                'beneficio_entregado': 'Postulación SAP Folio #8821',
                'primera_gestion': 'ATENCIÓN SOCIAL A USUARIO PRESENCIAL',
                'segunda_gestion': 'REVISIÓN DOCUMENTAL RSH',
                'fecha_visita': None,
                'fecha_entrega_informe': datetime.date(2026, 2, 16),
                'tercera_gestion': 'DERIVACIÓN A SUBSIDIOS COMUNALES',
                'fecha_entrega_beneficio': datetime.date(2026, 2, 18),
                'func_id': 6,
                'del_id': 3,
                'asg_cod': 'ASG-0011',
                'estado': 'Derivado',
                'resultado_texto': 'Postulación ingresada y derivada a comité comunal.',
            },
            {
                'codigo': 'SOC-00004',
                'fecha_ingreso': datetime.date(2026, 1, 8),
                'fecha_atencion': datetime.date(2026, 1, 8),
                'tipo_cod': 'TIP-SOC',
                'sub_cod': 'SUB-ORI',
                'vecino_rut': '16.400.400-4',
                'derivacion': 'Sin derivación (Solicitud desistida por traslado)',
                'requiere_visita': False,
                'fecha_programada_visita': None,
                'ingreso_tubo': False,
                'observaciones': 'Registro social inactivo sin actividades ni evidencias asociadas.',
                'informe_detalle': 'Cerrado administrativamente por cambio de domicilio comunal.',
                'beneficio_entregado': '',
                'primera_gestion': 'CONSULTA TELEFÓNICA INICIAL',
                'segunda_gestion': '',
                'fecha_visita': None,
                'fecha_entrega_informe': None,
                'tercera_gestion': '',
                'fecha_entrega_beneficio': None,
                'func_id': 3,
                'del_id': 1,
                'asg_cod': 'ASG-0005',
                'estado': 'Inactiva',
                'resultado_texto': 'Caso inactivo para pruebas de filtro y eliminación física.',
            },
        ]

        social_objs = {}
        for s in gestiones_sociales_data:
            vec = vecino_objs[s['vecino_rut']]
            obj, _ = GestionSocial.objects.update_or_create(
                codigo=s['codigo'],
                defaults={
                    'fecha_ingreso': s['fecha_ingreso'],
                    'fecha_atencion': s['fecha_atencion'],
                    'id_tipo': tipo_objs[s['tipo_cod']],
                    'id_subatencion': subatencion_objs[s['sub_cod']],
                    'beneficiario_vecino': vec,
                    'usuario': vec.nombre,
                    'rut': vec.rut,
                    'telefono': vec.telefono,
                    'direccion': vec.direccion,
                    'derivacion': s['derivacion'],
                    'requiere_visita': s['requiere_visita'],
                    'fecha_programada_visita': s['fecha_programada_visita'],
                    'ingreso_tubo': s['ingreso_tubo'],
                    'observaciones': s['observaciones'],
                    'informe_detalle': s['informe_detalle'],
                    'beneficio_entregado': s['beneficio_entregado'],
                    'primera_gestion': s['primera_gestion'],
                    'segunda_gestion': s['segunda_gestion'],
                    'fecha_visita': s['fecha_visita'],
                    'fecha_entrega_informe': s['fecha_entrega_informe'],
                    'tercera_gestion': s['tercera_gestion'],
                    'fecha_entrega_beneficio': s['fecha_entrega_beneficio'],
                    'id_funcionario': funcionario_objs[s['func_id']],
                    'id_delegacion': delegacion_objs[s['del_id']],
                    'asignacion_meta': asignacion_objs[s['asg_cod']],
                    'estado': s['estado'],
                    'resultado_texto': s['resultado_texto'],
                }
            )
            social_objs[s['codigo']] = obj
        self.stdout.write(self.style.SUCCESS(f'Entidad 11 (Gestión Social): {len(social_objs)} registros procesados.'))

        # ======================================================================
        # ENTIDAD 10: ACTIVIDAD (24 Gestiones Principales + 1 Subgestión) Y COMPROMISOS (13)
        # ======================================================================
        # Limpiar actividades y compromisos previos para garantizar conteo exacto (24 principales y 13 compromisos)
        Evidencia.objects.all().delete()
        Actividad.objects.all().delete()
        Compromiso.objects.all().delete()

        # 8 funcionarios x 3 actividades principales = 24 actividades principales
        # Las primeras 13 tendrán ingreso_tubo=True y generarán los 13 Compromisos del Tubo de Trabajo
        plan_24_actividades = [
            # Funcionario 1: He-Man (D01)
            (1, 1, 'TER-01', 'TIP-TERR', 'SUB-LUM', 'ASG-0001', 'HIT-01', '16.100.100-1', 'Reposición de 8 luminarias LED en Av. Viña del Mar', 'Coordinación con cuadrilla eléctrica municipal y verificación nocturna', 'Realizado', True, 'REALIZADO'),
            (1, 1, 'TER-02', 'TIP-SEG', 'SUB-PATR', 'ASG-0002', 'HIT-01', '16.100.100-1', 'Mesa barrial de seguridad y patrullaje mixto en Las Compañías Baja', 'Reunión con directiva JJVV N° 12 y programación de rondas preventivas', 'Realizado', True, 'EN_PROCESO'),
            (1, 1, 'TER-01', 'TIP-TERR', 'SUB-ASEO', 'ASG-0001', 'HIT-01', '16.100.100-1', 'Operativo de tolvas comunitarias en sector Villa El Indio', 'Instalación de 4 bateas de retiro de voluminosos junto a DISERCO', 'En Proceso', False, None),

            # Funcionario 2: Acuaman (D02)
            (2, 2, 'TER-03', 'TIP-TERR', 'SUB-PLAZ', 'ASG-0003', 'HIT-02', '16.200.200-2', 'Recuperación de juegos infantiles y poda en Plaza Juan XXIII', 'Desmalezado, pintura de mobiliario urbano y reparación de escaños', 'Realizado', True, 'REALIZADO'),
            (2, 2, 'TER-03', 'TIP-SEG', 'SUB-RUID', 'ASG-0004', 'HIT-02', '16.200.200-2', 'Mediación comunitaria y fiscalización preventiva en Sector Coll', 'Visita inspectiva y acta de acuerdo vecinal con junta de vecinos', 'Realizado', True, 'PENDIENTE'),
            (2, 2, 'TER-03', 'TIP-TERR', 'SUB-BACH', 'ASG-0003', 'HIT-02', '16.200.200-2', 'Catastro de baches prioritarios en eje 18 de Septiembre', 'Georreferenciación de 6 puntos críticos y envío de oficio a Serviu', 'En Proceso', False, None),

            # Funcionario 3: Flash (D01)
            (3, 1, 'TER-01', 'TIP-SOC', 'SUB-FIBE', 'ASG-0006', 'HIT-01', '16.100.100-1', 'Aplicación de Ficha FIBE e informe social por emergencia habitacional', 'Visita domiciliaria, peritaje social y entrega de kit de abrigo', 'Realizado', True, 'REALIZADO'),
            (3, 1, 'TER-02', 'TIP-SOC', 'SUB-ORI', 'ASG-0005', 'HIT-01', '16.100.100-1', 'Operativo de actualización de Registro Social de Hogares en sede vecinal', 'Atención de 18 familias en terreno con validación de cartola RSH', 'Realizado', True, 'EN_PROCESO'),
            (3, 1, 'TER-01', 'TIP-SOC', 'SUB-ALIM', 'ASG-0006', None, '16.100.100-1', 'Entrega domiciliaria de ayuda alimentaria a adultos mayores postrados', 'Distribución de canastas familiares con firma de acta de recepción', 'Realizado', False, None),

            # Funcionario 4: Pantera Negra (D03)
            (4, 3, 'TER-04', 'TIP-SEG', 'SUB-COME', 'ASG-0007', 'HIT-03', '16.300.300-3', 'Operativo de ordenamiento de comercio en eje Cordovez y Cienfuegos', 'Despliegue conjunto con inspectores municipales y despeje de aceras', 'Realizado', True, 'REALIZADO'),
            (4, 3, 'TER-04', 'TIP-TERR', 'SUB-PLAZ', 'ASG-0008', 'HIT-03', '16.300.300-3', 'Mesa de trabajo patrimonial con residentes del Casco Histórico', 'Levantamiento de compromisos de iluminación peatonal y limpieza de fachadas', 'En Proceso', True, 'INGRESADO'),
            # La actividad #12 en la lista (índice 12, que será la 24 al final o aquí mismo) -> pongamos estado Inactivo en la 3ra de Pantera Negra sin tubo ni hijos
            (4, 3, 'TER-04', 'TIP-SOC', 'SUB-ORI', 'ASG-0007', None, '16.300.300-3', 'Jornada informativa suspendida por contingencia climática (Inactiva)', 'Registro administrativo desactivado sin evidencias ni subgestiones asociadas', 'Inactivo', False, None),

            # Funcionario 5: Capitana Marvel (D04)
            (5, 4, 'TER-05', 'TIP-TERR', 'SUB-BACH', 'ASG-0009', None, '16.400.400-4', 'Perfilado de camino rural y limpieza de badén en El Arrayán', 'Coordinación de motoniveladora municipal en tramo de 3,5 kilómetros', 'Realizado', True, 'REALIZADO'),
            (5, 4, 'TER-05', 'TIP-TERR', 'SUB-ASEO', 'ASG-0010', None, '16.400.400-4', 'Operativo de suministro hídrico de emergencia con camión aljibe en El Romero', 'Verificación de estanques comunitarios y entrega programada de agua potable', 'Realizado', True, 'EN_PROCESO'),
            (5, 4, 'TER-05', 'TIP-SEG', 'SUB-PATR', 'ASG-0009', None, '16.400.400-4', 'Ronda preventiva rural en localidades de Algarrobito y El Romero', 'Inspección de puntos de acopio y coordinación con junta de vigilancia rural', 'Pendiente', False, None),

            # Funcionario 6: Hulk (D03)
            (6, 3, 'TER-04', 'TIP-SOC', 'SUB-SUBS', 'ASG-0011', 'HIT-03', '16.300.300-3', 'Tramitación de Subsidio de Agua Potable y exención de aseo domiciliario', 'Revisión de antecedentes socioeconómicos y postulación en sistema comunal', 'Realizado', True, 'REALIZADO'),
            (6, 3, 'TER-04', 'TIP-SOC', 'SUB-FIBE', 'ASG-0012', 'HIT-03', '16.300.300-3', 'Evaluación social de personas en situación de calle en Barrio Almagro', 'Coordinación con albergue municipal y derivación a red de salud primaria', 'En Proceso', True, 'PENDIENTE'),
            (6, 3, 'TER-04', 'TIP-SOC', 'SUB-ORI', 'ASG-0011', None, '16.300.300-3', 'Atención social presencial de adultos mayores en Delegación Centro', 'Orientación sobre Pensión Garantizada Universal y beneficios tarifarios', 'Realizado', False, None),

            # Funcionario 7: Capitán América (D02)
            (7, 2, 'TER-03', 'TIP-SOC', 'SUB-ALIM', 'ASG-0013', 'HIT-02', '16.200.200-2', 'Visita domiciliaria e informe social por vulnerabilidad severa en La Florida', 'Confección de Informe Social y gestión de ayuda paliativa inmediata', 'Realizado', True, 'EN_PROCESO'),
            (7, 2, 'TER-03', 'TIP-SOC', 'SUB-SUBS', 'ASG-0014', 'HIT-02', '16.200.200-2', 'Taller de postulación a subsidios habitacionales DS49 en JJVV Juan XXIII', 'Charla técnica con comité de allegados y revisión de ahorro previo', 'Realizado', False, None),
            (7, 2, 'TER-03', 'TIP-SOC', 'SUB-ORI', 'ASG-0013', None, '16.200.200-2', 'Seguimiento sociofamiliar de casos derivados desde CESFAM Juan Pablo II', 'Articulación intersectorial para entrega de insumos médicos e informe social', 'En Proceso', False, None),

            # Funcionario 8: Spider-Man (D01)
            (8, 1, 'TER-02', 'TIP-TERR', 'SUB-LUM', 'ASG-0015', 'HIT-01', '16.100.100-1', 'Catastro participativo de puntos oscuros junto a JJVV Villa El Indio', 'Recorrido nocturno con dirigentes y priorización de 12 postes sin luz', 'Realizado', False, None),
            (8, 1, 'TER-01', 'TIP-TERR', 'SUB-PLAZ', 'ASG-0015', 'HIT-01', '16.100.100-1', 'Jornada de arborización comunitaria en Parque Esmeralda Las Compañías', 'Plantación de 30 especies nativas con participación de vecinos y clubes de adulto mayor', 'Realizado', False, None),
            (8, 1, 'TER-02', 'TIP-SEG', 'SUB-PATR', 'ASG-0016', None, '16.100.100-1', 'Coordinación de retiro de vehículos abandonados en pasajes de Las Compañías', 'Notificación municipal e inspección en terreno con Seguridad Ciudadana', 'Pendiente', False, None),
        ]

        actividad_objs = []
        compromiso_count = 0
        base_date = datetime.date(2026, 1, 15)

        for idx, row in enumerate(plan_24_actividades, start=1):
            (func_id, del_id, ter_cod, tipo_cod, sub_cod, asg_cod, hito_cod,
             vec_rut, solicitud_txt, accion_txt, estado_act, es_tubo, est_comp) = row

            func_obj = funcionario_objs[func_id]
            del_obj = delegacion_objs[del_id]
            ter_obj = territorio_objs[ter_cod]
            tipo_obj = tipo_objs[tipo_cod]
            sub_obj = subatencion_objs[sub_cod]
            asg_obj = asignacion_objs[asg_cod]
            hito_obj = hito_objs[hito_cod] if hito_cod else None
            vec_obj = vecino_objs[vec_rut]
            fecha_act = base_date + datetime.timedelta(days=(idx * 2) % 45)
            es_soc = (tipo_cod == 'TIP-SOC')

            comp_obj = None
            if es_tubo:
                compromiso_count += 1
                comp_obj = Compromiso.objects.create(
                    codigo=f"TUB-{compromiso_count:05d}",
                    usuario_creador=func_obj.user,
                    id_delegacion=del_obj,
                    id_responsable=func_obj,
                    fecha_solicitud=fecha_act,
                    tipo='EXT' if idx % 2 == 1 else 'INT',
                    actividad=solicitud_txt,
                    solicitante=vec_obj.nombre,
                    territorio=ter_obj.nombre,
                    responsable=func_obj.nombre,
                    fecha_compromiso=fecha_act + datetime.timedelta(days=10),
                    area_apoyo='DISERCO / Dirección de Operaciones' if not es_soc else 'DIDECO / Asistencia Social',
                    estado=(est_comp or 'INGRESADO').replace('_', ' '),
                    observaciones=accion_txt,
                )

            cod_act = f"GES-{idx:05d}"
            act_obj = Actividad.objects.create(
                codigo=cod_act,
                id_funcionario=func_obj,
                responsable_funcionario=func_obj,
                usuario_creador=func_obj.user,
                id_delegacion=del_obj,
                territorio_rel=ter_obj,
                id_vecino=vec_obj,
                id_tipo=tipo_obj,
                id_subatencion=sub_obj,
                asignacion_meta=asg_obj,
                hito=hito_obj,
                id_gestion_social=social_objs['SOC-00001'] if idx == 7 else (social_objs['SOC-00002'] if idx == 19 else None),
                id_compromiso=comp_obj,
                fecha=fecha_act,
                origen='Requerimiento Vecinal' if idx % 2 == 1 else 'Operativo en Terreno',
                solicitante=vec_obj.nombre,
                rut_solicitante=vec_obj.rut,
                telefono=vec_obj.telefono,
                correo=vec_obj.correo,
                direccion=vec_obj.direccion,
                territorio=ter_obj.nombre,
                solicitud=solicitud_txt,
                accion=accion_txt,
                responsable=func_obj.nombre,
                item_evaluacion=asg_obj.item,
                avance=100 if estado_act == 'Realizado' else (50 if estado_act == 'En Proceso' else 0),
                resultado='Gestión ejecutada y verificada en terreno' if estado_act == 'Realizado' else 'En seguimiento técnico',
                codigo_evidencia=f"EVI-2026-{idx:04d}",
                ingreso_tubo=es_tubo,
                fecha_limite_tubo=(fecha_act + datetime.timedelta(days=10)) if es_tubo else None,
                area_apoyo_tubo='DISERCO / Operaciones' if es_tubo else '',
                es_gestion_social=es_soc,
                requiere_visita=es_soc and (idx % 2 == 1),
                fecha_programada_visita=(fecha_act + datetime.timedelta(days=2)) if es_soc else None,
                observaciones_sociales=accion_txt if es_soc else '',
                primera_gestion='ATENCIÓN INICIAL REGISTRADA' if es_soc else '',
                estado=estado_act,
            )
            actividad_objs.append(act_obj)

        # Subgestión hija para demostrar trazabilidad padre-hijo (no altera el conteo de 24 principales)
        act_raiz = actividad_objs[0]
        Actividad.objects.create(
            codigo=f"{act_raiz.codigo}-S01",
            id_gestion_padre=act_raiz,
            id_funcionario=act_raiz.id_funcionario,
            responsable_funcionario=act_raiz.responsable_funcionario,
            usuario_creador=act_raiz.usuario_creador,
            id_delegacion=act_raiz.id_delegacion,
            territorio_rel=act_raiz.territorio_rel,
            id_vecino=act_raiz.id_vecino,
            id_tipo=act_raiz.id_tipo,
            id_subatencion=act_raiz.id_subatencion,
            asignacion_meta=act_raiz.asignacion_meta,
            hito=act_raiz.hito,
            fecha=act_raiz.fecha + datetime.timedelta(days=3),
            origen='Seguimiento Técnico',
            solicitante=act_raiz.solicitante,
            rut_solicitante=act_raiz.rut_solicitante,
            telefono=act_raiz.telefono,
            correo=act_raiz.correo,
            direccion=act_raiz.direccion,
            territorio=act_raiz.territorio,
            solicitud=f"Seguimiento de verificación nocturna: {act_raiz.solicitud}",
            accion='Inspección de encendido total de luminarias LED junto a presidenta de JJVV',
            responsable=act_raiz.responsable,
            item_evaluacion=act_raiz.item_evaluacion,
            avance=100,
            resultado='100% de luminarias operativas verificadas',
            codigo_evidencia='EVI-2026-S01',
            estado='Realizado',
        )
        self.stdout.write(self.style.SUCCESS(
            f'Entidad 10 (Actividad): {len(actividad_objs)} gestiones principales + 1 subgestión y {compromiso_count} compromisos creados.'
        ))

        # ======================================================================
        # ENTIDAD 16: EVIDENCIA
        # ======================================================================
        evidencias_data = [
            {
                'codigo': 'EVI-2026-0001',
                'actividad': actividad_objs[0],
                'gestion_social': None,
                'archivo_ruta': 'evidencias/2026/luminarias_las_companias_d01.jpg',
                'tipo_archivo': 'Fotografía JPG/PNG',
                'observacion': 'Registro fotográfico nocturno de las 8 luminarias LED operativas en Av. Viña del Mar.',
                'fecha_evidencia': datetime.date(2026, 1, 18),
                'func_id': 1,
                'verif_id': 4,
                'estado_validacion': 'Aprobada',
                'imagen_verificada': True,
                'verificador_valido': True,
                'resultado': 1,
            },
            {
                'codigo': 'EVI-2026-0002',
                'actividad': actividad_objs[3],
                'gestion_social': None,
                'archivo_ruta': 'evidencias/2026/operativo_plaza_juan_xxiii_d02.jpg',
                'tipo_archivo': 'Fotografía JPG/PNG',
                'observacion': 'Fotografía antes y después de mantención de áreas verdes y juegos infantiles en La Antena.',
                'fecha_evidencia': datetime.date(2026, 1, 24),
                'func_id': 2,
                'verif_id': 4,
                'estado_validacion': 'Aprobada',
                'imagen_verificada': True,
                'verificador_valido': True,
                'resultado': 1,
            },
            {
                'codigo': 'EVI-2026-0003',
                'actividad': None,
                'gestion_social': social_objs['SOC-00001'],
                'archivo_ruta': 'evidencias/2026/acta_entrega_beneficio_soc00001.pdf',
                'tipo_archivo': 'Comprobante de Entrega',
                'observacion': 'Acta de recepción conforme de caja de alimentos y frazadas firmada por beneficiaria.',
                'fecha_evidencia': datetime.date(2026, 1, 24),
                'func_id': 3,
                'verif_id': 1,
                'estado_validacion': 'Aprobada',
                'imagen_verificada': True,
                'verificador_valido': True,
                'resultado': 1,
            },
            {
                'codigo': 'EVI-2026-0004',
                'actividad': actividad_objs[9],
                'gestion_social': None,
                'archivo_ruta': 'evidencias/2026/informe_fiscalizacion_centro_d03.pdf',
                'tipo_archivo': 'Acta PDF',
                'observacion': 'Reporte inspectivo de despeje de aceras en Casco Histórico pendiente de visación.',
                'fecha_evidencia': datetime.date(2026, 2, 5),
                'func_id': 4,
                'verif_id': 1,
                'estado_validacion': 'Pendiente',
                'imagen_verificada': False,
                'verificador_valido': False,
                'resultado': 0,
            },
            {
                'codigo': 'EVI-2026-0005',
                'actividad': actividad_objs[12],
                'gestion_social': None,
                'archivo_ruta': 'evidencias/2026/camino_rural_el_arrayan_d04.jpg',
                'tipo_archivo': 'Fotografía JPG/PNG',
                'observacion': 'Se solicita adjuntar plano de kilometraje intervenido por motoniveladora.',
                'fecha_evidencia': datetime.date(2026, 2, 11),
                'func_id': 5,
                'verif_id': 4,
                'estado_validacion': 'Corregir',
                'imagen_verificada': False,
                'verificador_valido': True,
                'resultado': 0,
            },
            {
                'codigo': 'EVI-2026-0006',
                'actividad': None,
                'gestion_social': social_objs['SOC-00002'],
                'archivo_ruta': 'evidencias/2026/borrador_reemplazado_soc00002.pdf',
                'tipo_archivo': 'Informe Social PDF',
                'observacion': 'Evidencia reemplazada y desactivada para pruebas de estado Inactiva y eliminación física.',
                'fecha_evidencia': datetime.date(2026, 2, 12),
                'func_id': 7,
                'verif_id': 1,
                'estado_validacion': 'Inactiva',
                'imagen_verificada': False,
                'verificador_valido': False,
                'resultado': 0,
            },
        ]

        for ev in evidencias_data:
            Evidencia.objects.create(
                codigo=ev['codigo'],
                id_actividad=ev['actividad'],
                id_gestion_social=ev['gestion_social'],
                archivo_ruta=ev['archivo_ruta'],
                tipo_archivo=ev['tipo_archivo'],
                observacion=ev['observacion'],
                fecha_evidencia=ev['fecha_evidencia'],
                id_funcionario=funcionario_objs[ev['func_id']],
                verificador=funcionario_objs[ev['verif_id']],
                estado_validacion=ev['estado_validacion'],
                imagen_verificada=ev['imagen_verificada'],
                verificador_valido=ev['verificador_valido'],
                resultado=ev['resultado'],
            )
        self.stdout.write(self.style.SUCCESS(f'Entidad 16 (Evidencia): {len(evidencias_data)} registros procesados.'))

        # ======================================================================
        # INDICADORES CONSOLIDADOS POR DELEGACIÓN (Tablero Ejecutivo)
        # ======================================================================
        IndicadorDelegacion.objects.all().delete()
        indicadores_data = [
            (1, 'Gestión Social y Territorial Las Compañías', 'He-Man', 99.10, 'verde'),
            (2, 'Operaciones y Seguridad La Antena', 'Acuaman', 88.50, 'amarillo'),
            (3, 'Planificación y Control Casco Histórico', 'Pantera Negra', 99.40, 'verde'),
            (4, 'Conectividad y Emergencias Rurales', 'Capitana Marvel', 92.00, 'amarillo'),
        ]
        for del_id, area_txt, resp_txt, porc_c, semaforo in indicadores_data:
            IndicadorDelegacion.objects.create(
                id_delegacion=delegacion_objs[del_id],
                id_periodo=periodo_objs['TRI-2026-1'],
                area=area_txt,
                responsable=resp_txt,
                avance_porcentaje=porc_c,
                estado_semaforo=semaforo,
            )

        self.stdout.write(self.style.SUCCESS('Poblamiento integral de las 17 entidades SGR finalizado exitosamente.'))
