import os
import datetime
from django.test import TestCase, Client
from django.core.management import call_command
from django.contrib.auth.models import User, Group
from django.conf import settings

from organizacion.models import (
    Delegacion, Territorio, Cargo, Rol, PerfilUsuario, Funcionario,
    JuntaVecinos, ParticipacionJunta, Hito
)
from actividades.models import (
    Actividad, GestionSocial, Evidencia, TipoAtencion, SubAtencion, Vecino
)
from resultados.models import ItemMeta, MetaFuncionario, PeriodoEvaluacion
from agenda.models import Compromiso


class SGRBaseTestCase(TestCase):
    """Base de pruebas que reconstruye y pobla las 17 entidades desde una BD limpia."""
    @classmethod
    def setUpTestData(cls):
        call_command('poblar_datos', verbosity=0)


class Test01MigracionesYModeloRelacional17Entidades(SGRBaseTestCase):
    """Criterios 1 y 2: Reconstrucción por migraciones desde BD vacía, MySQL DDL y 17 entidades con relaciones."""

    def test_01_reconstruccion_esquema_y_conteos_17_entidades(self):
        entidades = [
            ('1. Delegación', Delegacion.objects.count(), Delegacion.objects.filter(estado='Inactiva').count()),
            ('2. Territorio', Territorio.objects.count(), Territorio.objects.filter(estado='Inactivo').count()),
            ('3. Usuario Funcionario', PerfilUsuario.objects.count(), PerfilUsuario.objects.filter(estado='Inactivo').count()),
            ('4. Cargo', Cargo.objects.count(), Cargo.objects.filter(estado='Inactivo').count()),
            ('5. Rol', Rol.objects.count(), Rol.objects.filter(estado='Inactivo').count()),
            ('6. Vecino', Vecino.objects.count(), Vecino.objects.filter(estado='Inactivo').count()),
            ('7. Junta de Vecinos', JuntaVecinos.objects.count(), JuntaVecinos.objects.filter(estado='Inactiva').count()),
            ('8. Participación en Junta', ParticipacionJunta.objects.count(), ParticipacionJunta.objects.filter(estado='Inactivo').count()),
            ('9. Hito', Hito.objects.count(), Hito.objects.filter(estado='Inactivo').count()),
            ('10. Actividad', Actividad.objects.count(), Actividad.objects.filter(estado='Inactivo').count()),
            ('11. Gestión Social', GestionSocial.objects.count(), GestionSocial.objects.filter(estado='Inactiva').count()),
            ('12. Tipo de Atención', TipoAtencion.objects.count(), TipoAtencion.objects.filter(estado='Inactivo').count()),
            ('13. Subtipo de Atención', SubAtencion.objects.count(), SubAtencion.objects.filter(estado='Inactivo').count()),
            ('14. Meta (ItemMeta)', ItemMeta.objects.count(), ItemMeta.objects.filter(estado='Inactivo').count()),
            ('15. Asignación de Meta', MetaFuncionario.objects.count(), MetaFuncionario.objects.filter(estado='Inactiva').count()),
            ('16. Evidencia', Evidencia.objects.count(), Evidencia.objects.filter(estado_validacion='Inactiva').count()),
            ('17. Trimestre', PeriodoEvaluacion.objects.count(), PeriodoEvaluacion.objects.exclude(estado='Activo').count()),
        ]
        for nombre, total, inactivos in entidades:
            self.assertGreaterEqual(total, 2, f'{nombre} debe tener al menos 2 registros')
            self.assertGreaterEqual(inactivos, 1, f'{nombre} debe tener al menos 1 registro inactivo')

    def test_02_relaciones_orm_y_configuracion_mysql(self):
        # Verificar relaciones ORM entre las 17 entidades
        ter = Territorio.objects.select_related('delegacion').first()
        self.assertIsNotNone(ter.delegacion)
        jv = JuntaVecinos.objects.select_related('delegacion', 'territorio').first()
        self.assertEqual(jv.territorio.delegacion_id, jv.delegacion_id)
        part = ParticipacionJunta.objects.select_related('vecino', 'junta').first()
        self.assertIsNotNone(part.vecino)
        self.assertIsNotNone(part.junta)
        hito = Hito.objects.select_related('delegacion', 'territorio', 'responsable').first()
        self.assertGreaterEqual(hito.responsables.count(), 1)
        act = Actividad.objects.select_related('id_funcionario', 'id_delegacion', 'id_tipo', 'id_subatencion', 'asignacion_meta').first()
        self.assertEqual(act.id_subatencion.id_tipo_id, act.id_tipo_id)
        soc = GestionSocial.objects.select_related('id_tipo', 'id_subatencion', 'id_funcionario', 'id_delegacion', 'beneficiario_vecino').first()
        self.assertIsNotNone(soc.beneficiario_vecino)
        ev = Evidencia.objects.first()
        self.assertTrue(bool(ev.id_actividad_id or ev.id_gestion_social_id))

        # Verificar driver mysqlclient y script DDL MySQL de las 17 entidades
        import MySQLdb  # noqa: F401
        sql_path = os.path.join(settings.BASE_DIR, 'datos', 'script_mysql_sgr.sql')
        self.assertTrue(os.path.exists(sql_path))
        sql_text = open(sql_path, encoding='utf-8').read()
        for tabla in [
            'delegaciones', 'territorios', 'cargos', 'roles', 'funcionarios', 'perfiles_usuario',
            'vecinos', 'juntas_vecinos', 'participaciones_junta', 'hitos', 'actividades',
            'gestiones_sociales', 'tipos_atencion', 'sub_atenciones', 'items_metas',
            'metas_funcionario', 'evidencias', 'periodos_evaluacion'
        ]:
            self.assertIn(tabla, sql_text)


class Test02CRUDCompleto17Entidades(SGRBaseTestCase):
    """Criterios 3, 4, 5 y 6: Creación, Consulta, Edición (mismo PK sin duplicar) y Eliminación/Desactivación en las 17 entidades."""

    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.client.post('/login/', {'username': 'mujermaravilla', 'password': 'admin'})

    def test_crud_completo_en_las_17_entidades(self):
        del_base = Delegacion.objects.filter(estado='Activa').first()
        ter_base = Territorio.objects.filter(delegacion=del_base, estado='Activo').first()
        cargo_base = Cargo.objects.filter(estado='Activo').first()
        rol_base = Rol.objects.filter(codigo='ROL-OPE').first()
        func_base = Funcionario.objects.filter(activo=True).first()
        vec_base = Vecino.objects.filter(estado='Activo').first()
        jv_base = JuntaVecinos.objects.filter(estado='Activa').first()
        tipo_base = TipoAtencion.objects.filter(codigo='TIP-SOC').first()
        sub_base = SubAtencion.objects.filter(id_tipo=tipo_base, estado='Activo').first()
        item_base = ItemMeta.objects.filter(estado='Activo').first()
        per_base = PeriodoEvaluacion.objects.filter(estado='Activo').first()
        asg_base = MetaFuncionario.objects.filter(estado='Activa').first()
        act_base = Actividad.objects.exclude(estado='Inactivo').first()

        # 1. DELEGACIÓN
        c_antes = Delegacion.objects.count()
        r = self.client.post('/mantenedores/delegaciones/crear/', {
            'codigo': 'D99', 'nombre': 'Delegación CRUD Test', 'direccion': 'Av Test 100',
            'comuna': 'La Serena', 'ambito': 'Urbano Test', 'responsable': 'He-Man', 'estado': 'Activa'
        })
        self.assertEqual(r.status_code, 302)
        obj1 = Delegacion.objects.get(codigo='D99')
        pk1 = obj1.pk
        self.assertEqual(Delegacion.objects.count(), c_antes + 1)
        self.assertEqual(self.client.get(f'/mantenedores/delegaciones/{pk1}/detalle/').status_code, 200)
        r_ed = self.client.post(f'/mantenedores/delegaciones/{pk1}/editar/', {
            'codigo': 'D99', 'nombre': 'Delegación CRUD Editada', 'direccion': 'Av Test 200',
            'comuna': 'La Serena', 'ambito': 'Urbano Edit', 'responsable': 'He-Man', 'estado': 'Activa'
        })
        self.assertEqual(r_ed.status_code, 302)
        obj1.refresh_from_db()
        self.assertEqual(obj1.pk, pk1)
        self.assertEqual(obj1.nombre, 'Delegación CRUD Editada')
        self.assertEqual(Delegacion.objects.filter(codigo='D99').count(), 1)
        self.assertEqual(self.client.get(f'/mantenedores/delegaciones/{pk1}/eliminar/').status_code, 200)
        self.assertTrue(Delegacion.objects.filter(pk=pk1).exists())
        self.client.post(f'/mantenedores/delegaciones/{pk1}/eliminar/')
        self.assertFalse(Delegacion.objects.filter(pk=pk1).exists())
        # Desactivación lógica en delegación con relaciones
        self.client.post(f'/mantenedores/delegaciones/{del_base.pk}/eliminar/')
        del_base.refresh_from_db()
        self.assertEqual(del_base.estado, 'Inactiva')
        del_base.estado = 'Activa'
        del_base.save()

        # 2. TERRITORIO
        r = self.client.post('/mantenedores/territorios/crear/', {
            'codigo': 'TER-99', 'nombre': 'Territorio CRUD Test', 'delegacion': del_base.pk,
            'descripcion': 'Desc test', 'estado': 'Activo'
        })
        self.assertEqual(r.status_code, 302)
        obj2 = Territorio.objects.get(codigo='TER-99')
        pk2 = obj2.pk
        self.assertEqual(self.client.get(f'/mantenedores/territorios/{pk2}/detalle/').status_code, 200)
        self.client.post(f'/mantenedores/territorios/{pk2}/editar/', {
            'codigo': 'TER-99', 'nombre': 'Territorio CRUD Editado', 'delegacion': del_base.pk,
            'descripcion': 'Desc editada', 'estado': 'Activo'
        })
        obj2.refresh_from_db()
        self.assertEqual(obj2.pk, pk2)
        self.assertEqual(obj2.nombre, 'Territorio CRUD Editado')
        self.assertEqual(self.client.get(f'/mantenedores/territorios/{pk2}/eliminar/').status_code, 200)
        self.client.post(f'/mantenedores/territorios/{pk2}/eliminar/')
        self.assertFalse(Territorio.objects.filter(pk=pk2).exists())

        # 3. USUARIO FUNCIONARIO (con cuenta admin porque usuarios es solo_admin)
        c_admin = Client(SERVER_NAME='localhost')
        c_admin.post('/login/', {'username': 'admin', 'password': 'admin'})
        r = c_admin.post('/mantenedores/usuarios/crear/', {
            'username': 'user_crud_17', 'first_name': 'Nombre', 'last_name': 'Apellido',
            'rut': '21.111.222-3', 'email': 'user_crud_17@laserena.cl', 'password': 'admin1234',
            'cargo': cargo_base.pk, 'rol': rol_base.pk, 'delegacion_activa': del_base.pk, 'estado': 'Activo'
        })
        self.assertEqual(r.status_code, 302)
        obj3 = User.objects.get(username='user_crud_17')
        pk3 = obj3.pk
        self.assertEqual(c_admin.get(f'/mantenedores/usuarios/{pk3}/detalle/').status_code, 200)
        c_admin.post(f'/mantenedores/usuarios/{pk3}/editar/', {
            'username': 'user_crud_17', 'first_name': 'NombreEdit', 'last_name': 'ApellidoEdit',
            'rut': '21.111.222-3', 'email': 'user_crud_17@laserena.cl',
            'cargo': cargo_base.pk, 'rol': rol_base.pk, 'delegacion_activa': del_base.pk, 'estado': 'Activo'
        })
        obj3.refresh_from_db()
        self.assertEqual(obj3.pk, pk3)
        self.assertEqual(obj3.first_name, 'NombreEdit')
        self.assertEqual(c_admin.get(f'/mantenedores/usuarios/{pk3}/eliminar/').status_code, 200)
        c_admin.post(f'/mantenedores/usuarios/{pk3}/eliminar/')
        self.assertFalse(User.objects.filter(pk=pk3).exists())

        # 4. CARGO
        r = self.client.post('/mantenedores/cargos/crear/', {
            'codigo': 'CRG-99', 'nombre': 'Cargo CRUD 17', 'descripcion': 'Test', 'estado': 'Activo'
        })
        self.assertEqual(r.status_code, 302)
        obj4 = Cargo.objects.get(codigo='CRG-99')
        pk4 = obj4.pk
        self.client.post(f'/mantenedores/cargos/{pk4}/editar/', {
            'codigo': 'CRG-99', 'nombre': 'Cargo CRUD 17 Editado', 'descripcion': 'Edit', 'estado': 'Activo'
        })
        obj4.refresh_from_db()
        self.assertEqual(obj4.pk, pk4)
        self.assertEqual(obj4.nombre, 'Cargo CRUD 17 Editado')
        self.assertEqual(self.client.get(f'/mantenedores/cargos/{pk4}/eliminar/').status_code, 200)
        self.client.post(f'/mantenedores/cargos/{pk4}/eliminar/')
        self.assertFalse(Cargo.objects.filter(pk=pk4).exists())

        # 5. ROL
        r = c_admin.post('/mantenedores/roles/crear/', {
            'codigo': 'ROL-99', 'nombre': 'Rol CRUD 17', 'descripcion': 'Test',
            'alcance_autorizado': 'DELEGACION', 'permisos': 'Lectura', 'estado': 'Activo'
        })
        self.assertEqual(r.status_code, 302)
        obj5 = Rol.objects.get(codigo='ROL-99')
        pk5 = obj5.pk
        c_admin.post(f'/mantenedores/roles/{pk5}/editar/', {
            'codigo': 'ROL-99', 'nombre': 'Rol CRUD 17 Editado', 'descripcion': 'Edit',
            'alcance_autorizado': 'COMUNAL', 'permisos': 'Lectura/Escritura', 'estado': 'Activo'
        })
        obj5.refresh_from_db()
        self.assertEqual(obj5.pk, pk5)
        self.assertEqual(obj5.nombre, 'Rol CRUD 17 Editado')
        self.assertEqual(c_admin.get(f'/mantenedores/roles/{pk5}/eliminar/').status_code, 200)
        c_admin.post(f'/mantenedores/roles/{pk5}/eliminar/')
        self.assertFalse(Rol.objects.filter(pk=pk5).exists())

        # 6. VECINO
        r = self.client.post('/mantenedores/vecinos/crear/', {
            'rut': '22.333.444-5', 'nombres': 'Vecino', 'apellidos': 'CRUD Test',
            'telefono': '+56911112222', 'correo': 'vecino99@test.cl', 'direccion': 'Calle 1',
            'territorio_rel': ter_base.pk, 'estado': 'Activo'
        })
        self.assertEqual(r.status_code, 302)
        obj6 = Vecino.objects.get(rut='22.333.444-5')
        pk6 = obj6.pk
        self.client.post(f'/mantenedores/vecinos/{pk6}/editar/', {
            'rut': '22.333.444-5', 'nombres': 'Vecino Editado', 'apellidos': 'CRUD Test',
            'telefono': '+56911112222', 'correo': 'vecino99@test.cl', 'direccion': 'Calle 2',
            'territorio_rel': ter_base.pk, 'estado': 'Activo'
        })
        obj6.refresh_from_db()
        self.assertEqual(obj6.pk, pk6)
        self.assertEqual(obj6.direccion, 'Calle 2')
        self.assertEqual(self.client.get(f'/mantenedores/vecinos/{pk6}/eliminar/').status_code, 200)
        self.client.post(f'/mantenedores/vecinos/{pk6}/eliminar/')
        self.assertFalse(Vecino.objects.filter(pk=pk6).exists())

        # 7. JUNTA DE VECINOS
        r = self.client.post('/mantenedores/juntas-vecinos/crear/', {
            'codigo': 'JJVV-99', 'nombre': 'JJVV CRUD 17', 'direccion': 'Sede 99',
            'delegacion': del_base.pk, 'territorio': ter_base.pk, 'estado': 'Activa'
        })
        self.assertEqual(r.status_code, 302)
        obj7 = JuntaVecinos.objects.get(codigo='JJVV-99')
        pk7 = obj7.pk
        self.client.post(f'/mantenedores/juntas-vecinos/{pk7}/editar/', {
            'codigo': 'JJVV-99', 'nombre': 'JJVV CRUD 17 Editada', 'direccion': 'Sede 100',
            'delegacion': del_base.pk, 'territorio': ter_base.pk, 'estado': 'Activa'
        })
        obj7.refresh_from_db()
        self.assertEqual(obj7.pk, pk7)
        self.assertEqual(obj7.nombre, 'JJVV CRUD 17 Editada')
        self.assertEqual(self.client.get(f'/mantenedores/juntas-vecinos/{pk7}/eliminar/').status_code, 200)
        self.client.post(f'/mantenedores/juntas-vecinos/{pk7}/eliminar/')
        self.assertFalse(JuntaVecinos.objects.filter(pk=pk7).exists())

        # 8. PARTICIPACIÓN EN JUNTA
        vec_disp = Vecino.objects.filter(rut='16.500.500-5').first()
        r = self.client.post('/mantenedores/participaciones/crear/', {
            'codigo': 'PAR-99', 'vecino': vec_disp.pk, 'junta': jv_base.pk,
            'cargo': 'Socio/a Activo/a', 'fecha_incorporacion': '2026-01-10', 'estado': 'Activo'
        })
        self.assertEqual(r.status_code, 302)
        obj8 = ParticipacionJunta.objects.get(codigo='PAR-99')
        pk8 = obj8.pk
        self.client.post(f'/mantenedores/participaciones/{pk8}/editar/', {
            'codigo': 'PAR-99', 'vecino': vec_disp.pk, 'junta': jv_base.pk,
            'cargo': 'Primer Director/a', 'fecha_incorporacion': '2026-01-10', 'estado': 'Activo'
        })
        obj8.refresh_from_db()
        self.assertEqual(obj8.pk, pk8)
        self.assertEqual(obj8.cargo, 'Primer Director/a')
        self.assertEqual(self.client.get(f'/mantenedores/participaciones/{pk8}/eliminar/').status_code, 200)
        self.client.post(f'/mantenedores/participaciones/{pk8}/eliminar/')
        self.assertFalse(ParticipacionJunta.objects.filter(pk=pk8).exists())

        # 9. HITO
        r = self.client.post('/mantenedores/hitos/crear/', {
            'codigo': 'HIT-99', 'nombre': 'Hito CRUD 17', 'descripcion': 'Desc',
            'periodicidad': 'Trimestral', 'fecha_inicio': '2026-03-01', 'fecha_termino': '2026-03-15',
            'delegacion': del_base.pk, 'territorio': ter_base.pk, 'responsable': func_base.pk, 'estado': 'Programado'
        })
        self.assertEqual(r.status_code, 302)
        obj9 = Hito.objects.get(codigo='HIT-99')
        pk9 = obj9.pk
        self.client.post(f'/mantenedores/hitos/{pk9}/editar/', {
            'codigo': 'HIT-99', 'nombre': 'Hito CRUD 17 Editado', 'descripcion': 'Desc Edit',
            'periodicidad': 'Trimestral', 'fecha_inicio': '2026-03-01', 'fecha_termino': '2026-03-20',
            'delegacion': del_base.pk, 'territorio': ter_base.pk, 'responsable': func_base.pk, 'estado': 'En Ejecución'
        })
        obj9.refresh_from_db()
        self.assertEqual(obj9.pk, pk9)
        self.assertEqual(obj9.nombre, 'Hito CRUD 17 Editado')
        self.assertEqual(self.client.get(f'/mantenedores/hitos/{pk9}/eliminar/').status_code, 200)
        self.client.post(f'/mantenedores/hitos/{pk9}/eliminar/')
        self.assertFalse(Hito.objects.filter(pk=pk9).exists())

        # 10. ACTIVIDAD
        r = self.client.post('/actividades/nueva/', {
            'fecha': '2026-03-10', 'id_tipo': tipo_base.pk, 'id_subatencion': sub_base.pk,
            'solicitante': 'Ciudadano Test 10', 'rut_solicitante': '16.100.100-1',
            'solicitud': 'Solicitud CRUD 10', 'accion': 'Acción inicial',
            'responsable': func_base.nombre, 'item_evaluacion': item_base.nombre, 'estado': 'Pendiente'
        })
        self.assertEqual(r.status_code, 302)
        obj10 = Actividad.objects.filter(solicitud='Solicitud CRUD 10').first()
        self.assertIsNotNone(obj10)
        pk10 = obj10.pk
        self.client.post(f'/actividades/actividad/{pk10}/editar/', {
            'fecha': '2026-03-10', 'id_tipo': tipo_base.pk, 'id_subatencion': sub_base.pk,
            'id_funcionario': func_base.pk, 'id_delegacion': del_base.pk,
            'solicitante': 'Ciudadano Test 10', 'rut_solicitante': '16.100.100-1',
            'solicitud': 'Solicitud CRUD 10 Editada', 'accion': 'Acción editada',
            'responsable': func_base.nombre, 'item_evaluacion': item_base.nombre, 'estado': 'Realizado'
        })
        obj10.refresh_from_db()
        self.assertEqual(obj10.pk, pk10)
        self.assertEqual(obj10.solicitud, 'Solicitud CRUD 10 Editada')
        self.assertEqual(self.client.get(f'/actividades/actividad/{pk10}/eliminar/').status_code, 200)
        self.client.post(f'/actividades/actividad/{pk10}/eliminar/')
        self.assertFalse(Actividad.objects.filter(pk=pk10).exists())

        # 11. GESTIÓN SOCIAL
        r = self.client.post('/actividades/social/nueva/', {
            'fecha_ingreso': '2026-03-12', 'id_tipo': tipo_base.pk, 'id_subatencion': sub_base.pk,
            'usuario': 'Beneficiario CRUD 11', 'rut': '16.100.100-1',
            'observaciones': 'Caso social CRUD 11', 'primera_gestion': 'ENTREVISTA',
            'id_funcionario': func_base.pk, 'estado': 'Ingresada'
        })
        self.assertEqual(r.status_code, 302)
        obj11 = GestionSocial.objects.filter(observaciones='Caso social CRUD 11').first()
        self.assertIsNotNone(obj11)
        pk11 = obj11.pk
        # Limpiar actividad espejo generada por formulario social para probar eliminación limpia luego
        Actividad.objects.filter(id_gestion_social=obj11).delete()
        self.client.post(f'/actividades/social/{pk11}/editar/', {
            'fecha_ingreso': '2026-03-12', 'id_tipo': tipo_base.pk, 'id_subatencion': sub_base.pk,
            'usuario': 'Beneficiario CRUD 11 Editado', 'rut': '16.100.100-1',
            'observaciones': 'Caso social CRUD 11 Editado', 'primera_gestion': 'ENTREVISTA',
            'id_funcionario': func_base.pk, 'id_delegacion': del_base.pk, 'estado': 'En Proceso'
        })
        obj11.refresh_from_db()
        self.assertEqual(obj11.pk, pk11)
        self.assertEqual(obj11.usuario, 'Beneficiario CRUD 11 Editado')
        self.assertEqual(self.client.get(f'/actividades/social/{pk11}/eliminar/').status_code, 200)
        self.client.post(f'/actividades/social/{pk11}/eliminar/')
        self.assertFalse(GestionSocial.objects.filter(pk=pk11).exists())

        # 12. TIPO DE ATENCIÓN
        r = self.client.post('/mantenedores/tipos-atencion/crear/', {
            'codigo': 'TIP-99', 'nombre': 'Tipo Atención CRUD 12', 'descripcion': 'Desc', 'estado': 'Activo'
        })
        self.assertEqual(r.status_code, 302)
        obj12 = TipoAtencion.objects.get(codigo='TIP-99')
        pk12 = obj12.pk
        self.client.post(f'/mantenedores/tipos-atencion/{pk12}/editar/', {
            'codigo': 'TIP-99', 'nombre': 'Tipo Atención CRUD 12 Editado', 'descripcion': 'Edit', 'estado': 'Activo'
        })
        obj12.refresh_from_db()
        self.assertEqual(obj12.pk, pk12)
        self.assertEqual(obj12.nombre, 'Tipo Atención CRUD 12 Editado')
        self.assertEqual(self.client.get(f'/mantenedores/tipos-atencion/{pk12}/eliminar/').status_code, 200)
        self.client.post(f'/mantenedores/tipos-atencion/{pk12}/eliminar/')
        self.assertFalse(TipoAtencion.objects.filter(pk=pk12).exists())

        # 13. SUBTIPO DE ATENCIÓN
        r = self.client.post('/mantenedores/subatenciones/crear/', {
            'codigo': 'SUB-99', 'id_tipo': tipo_base.pk, 'nombre': 'Subtipo CRUD 13', 'estado': 'Activo'
        })
        self.assertEqual(r.status_code, 302)
        obj13 = SubAtencion.objects.get(codigo='SUB-99')
        pk13 = obj13.pk
        self.client.post(f'/mantenedores/subatenciones/{pk13}/editar/', {
            'codigo': 'SUB-99', 'id_tipo': tipo_base.pk, 'nombre': 'Subtipo CRUD 13 Editado', 'estado': 'Activo'
        })
        obj13.refresh_from_db()
        self.assertEqual(obj13.pk, pk13)
        self.assertEqual(obj13.nombre, 'Subtipo CRUD 13 Editado')
        self.assertEqual(self.client.get(f'/mantenedores/subatenciones/{pk13}/eliminar/').status_code, 200)
        self.client.post(f'/mantenedores/subatenciones/{pk13}/eliminar/')
        self.assertFalse(SubAtencion.objects.filter(pk=pk13).exists())

        # 14. META (ItemMeta)
        r = self.client.post('/mantenedores/items/crear/', {
            'codigo': 'I99', 'nombre': 'Meta CRUD 14', 'descripcion': 'Desc',
            'tipo_meta': 'Cuantitativa', 'unidad_medida': 'Informes', 'estado': 'Activo'
        })
        self.assertEqual(r.status_code, 302)
        obj14 = ItemMeta.objects.get(codigo='I99')
        pk14 = obj14.pk
        self.client.post(f'/mantenedores/items/{pk14}/editar/', {
            'codigo': 'I99', 'nombre': 'Meta CRUD 14 Editada', 'descripcion': 'Edit',
            'tipo_meta': 'Cuantitativa', 'unidad_medida': 'Operativos', 'estado': 'Activo'
        })
        obj14.refresh_from_db()
        self.assertEqual(obj14.pk, pk14)
        self.assertEqual(obj14.nombre, 'Meta CRUD 14 Editada')
        self.assertEqual(self.client.get(f'/mantenedores/items/{pk14}/eliminar/').status_code, 200)
        self.client.post(f'/mantenedores/items/{pk14}/eliminar/')
        self.assertFalse(ItemMeta.objects.filter(pk=pk14).exists())

        # 15. ASIGNACIÓN DE META (MetaFuncionario)
        r = self.client.post('/mantenedores/asignaciones-metas/crear/', {
            'codigo': 'ASG-9999', 'id_funcionario': func_base.pk, 'id_periodo': per_base.pk,
            'id_item_meta': item_base.pk, 'item': item_base.nombre,
            'meta_periodo': 25, 'ponderador': 30, 'avance_actual': 0, 'estado': 'Activa'
        })
        self.assertEqual(r.status_code, 302)
        obj15 = MetaFuncionario.objects.get(codigo='ASG-9999')
        pk15 = obj15.pk
        self.client.post(f'/mantenedores/asignaciones-metas/{pk15}/editar/', {
            'codigo': 'ASG-9999', 'id_funcionario': func_base.pk, 'id_periodo': per_base.pk,
            'id_item_meta': item_base.pk, 'item': item_base.nombre,
            'meta_periodo': 40, 'ponderador': 35, 'avance_actual': 0, 'estado': 'Activa'
        })
        obj15.refresh_from_db()
        self.assertEqual(obj15.pk, pk15)
        self.assertEqual(obj15.meta_periodo, 40)
        self.assertEqual(self.client.get(f'/mantenedores/asignaciones-metas/{pk15}/eliminar/').status_code, 200)
        self.client.post(f'/mantenedores/asignaciones-metas/{pk15}/eliminar/')
        self.assertFalse(MetaFuncionario.objects.filter(pk=pk15).exists())

        # 16. EVIDENCIA
        r = self.client.post('/actividades/evidencias/crear/', {
            'codigo': 'EVI-CRUD-16', 'id_actividad': act_base.pk, 'id_funcionario': func_base.pk,
            'archivo_ruta': 'evidencias/test_16.jpg', 'tipo_archivo': 'Fotografía JPG/PNG',
            'fecha_evidencia': '2026-03-10', 'observacion': 'Evidencia inicial', 'estado_validacion': 'Pendiente'
        })
        self.assertEqual(r.status_code, 302)
        obj16 = Evidencia.objects.get(codigo='EVI-CRUD-16')
        pk16 = obj16.pk
        self.client.post(f'/actividades/evidencia/{pk16}/editar/', {
            'codigo': 'EVI-CRUD-16', 'id_actividad': act_base.pk, 'id_funcionario': func_base.pk,
            'archivo_ruta': 'evidencias/test_16_edit.jpg', 'tipo_archivo': 'Fotografía JPG/PNG',
            'fecha_evidencia': '2026-03-10', 'observacion': 'Evidencia editada', 'estado_validacion': 'Pendiente'
        })
        obj16.refresh_from_db()
        self.assertEqual(obj16.pk, pk16)
        self.assertEqual(obj16.observacion, 'Evidencia editada')
        self.assertEqual(self.client.get(f'/actividades/evidencia/{pk16}/eliminar/').status_code, 200)
        self.client.post(f'/actividades/evidencia/{pk16}/eliminar/')
        self.assertFalse(Evidencia.objects.filter(pk=pk16).exists())

        # 17. TRIMESTRE (PeriodoEvaluacion)
        r = self.client.post('/mantenedores/trimestres/crear/', {
            'codigo': 'TRI-2027-1', 'nombre': '1° Trimestre 2027', 'anio': 2027, 'numero': 1,
            'fecha_inicio': '2027-01-01', 'fecha_cierre': '2027-03-31', 'estado': 'Inactivo'
        })
        self.assertEqual(r.status_code, 302)
        obj17 = PeriodoEvaluacion.objects.get(codigo='TRI-2027-1')
        pk17 = obj17.pk
        self.client.post(f'/mantenedores/trimestres/{pk17}/editar/', {
            'codigo': 'TRI-2027-1', 'nombre': '1° Trimestre 2027 Editado', 'anio': 2027, 'numero': 1,
            'fecha_inicio': '2027-01-01', 'fecha_cierre': '2027-03-31', 'estado': 'Cerrado'
        })
        obj17.refresh_from_db()
        self.assertEqual(obj17.pk, pk17)
        self.assertEqual(obj17.nombre, '1° Trimestre 2027 Editado')
        self.assertEqual(self.client.get(f'/mantenedores/trimestres/{pk17}/eliminar/').status_code, 200)
        self.client.post(f'/mantenedores/trimestres/{pk17}/eliminar/')
        self.assertFalse(PeriodoEvaluacion.objects.filter(pk=pk17).exists())


class Test03ValidacionesModelForm17Entidades(SGRBaseTestCase):
    """Criterio 7: Validaciones server-side con ModelForm en las 17 entidades sin alterar BD ante error."""

    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.client.post('/login/', {'username': 'admin', 'password': 'admin'})

    def test_rechazo_campos_vacios_y_reglas_de_negocio_en_17_entidades(self):
        # 1. Campos obligatorios vacíos en las 17 rutas de creación -> ninguno debe crear registro
        endpoints_creacion = [
            ('/mantenedores/delegaciones/crear/', Delegacion),
            ('/mantenedores/territorios/crear/', Territorio),
            ('/mantenedores/usuarios/crear/', User),
            ('/mantenedores/cargos/crear/', Cargo),
            ('/mantenedores/roles/crear/', Rol),
            ('/mantenedores/vecinos/crear/', Vecino),
            ('/mantenedores/juntas-vecinos/crear/', JuntaVecinos),
            ('/mantenedores/participaciones/crear/', ParticipacionJunta),
            ('/mantenedores/hitos/crear/', Hito),
            ('/actividades/nueva/', Actividad),
            ('/actividades/social/nueva/', GestionSocial),
            ('/mantenedores/tipos-atencion/crear/', TipoAtencion),
            ('/mantenedores/subatenciones/crear/', SubAtencion),
            ('/mantenedores/items/crear/', ItemMeta),
            ('/mantenedores/asignaciones-metas/crear/', MetaFuncionario),
            ('/actividades/evidencias/crear/', Evidencia),
            ('/mantenedores/trimestres/crear/', PeriodoEvaluacion),
        ]
        for url_crear, model_cls in endpoints_creacion:
            antes = model_cls.objects.count()
            resp = self.client.post(url_crear, {})
            self.assertEqual(resp.status_code, 200, f'{url_crear} debe re-renderizar formulario con error ante POST vacío')
            self.assertEqual(model_cls.objects.count(), antes, f'{url_crear} alteró la BD con datos vacíos')

        # 2. Unicidad de códigos (Delegación, Cargo, Vecino RUT)
        c_del = Delegacion.objects.count()
        self.client.post('/mantenedores/delegaciones/crear/', {
            'codigo': 'D01', 'nombre': 'Dup', 'ambito': 'A', 'responsable': 'R', 'estado': 'Activa'
        })
        self.assertEqual(Delegacion.objects.count(), c_del)

        c_vec = Vecino.objects.count()
        self.client.post('/mantenedores/vecinos/crear/', {
            'rut': '16.100.100-1', 'nombres': 'Dup', 'apellidos': 'Rut', 'correo': 'correo_invalido'
        })
        self.assertEqual(Vecino.objects.count(), c_vec)

        # 3. Coherencia de fechas (Hito, Participación, Trimestre)
        del_base = Delegacion.objects.first()
        c_hito = Hito.objects.count()
        self.client.post('/mantenedores/hitos/crear/', {
            'codigo': 'HIT-ERR', 'nombre': 'Fechas malas', 'fecha_inicio': '2026-06-10',
            'fecha_termino': '2026-06-01', 'delegacion': del_base.pk
        })
        self.assertEqual(Hito.objects.count(), c_hito)

        c_tri = PeriodoEvaluacion.objects.count()
        self.client.post('/mantenedores/trimestres/crear/', {
            'codigo': 'TRI-ERR', 'nombre': 'Trimestre inválido', 'anio': 2026, 'numero': 5,
            'fecha_inicio': '2026-06-10', 'fecha_cierre': '2026-06-01'
        })
        self.assertEqual(PeriodoEvaluacion.objects.count(), c_tri)

        # 4. Rangos de Asignación de Meta (meta_periodo <= 0, ponderador > 100)
        c_asg = MetaFuncionario.objects.count()
        self.client.post('/mantenedores/asignaciones-metas/crear/', {
            'id_funcionario': Funcionario.objects.first().pk,
            'id_periodo': PeriodoEvaluacion.objects.first().pk,
            'id_item_meta': ItemMeta.objects.first().pk,
            'meta_periodo': 0, 'ponderador': 120
        })
        self.assertEqual(MetaFuncionario.objects.count(), c_asg)

        # 5. Coherencia de relaciones (Territorio de otra delegación en JuntaVecinos, Evidencia huérfana)
        del_1 = Delegacion.objects.get(codigo='D01')
        ter_d02 = Territorio.objects.filter(delegacion__codigo='D02').first()
        c_jv = JuntaVecinos.objects.count()
        self.client.post('/mantenedores/juntas-vecinos/crear/', {
            'codigo': 'JJVV-ERR', 'nombre': 'JJVV Relación incoherente',
            'delegacion': del_1.pk, 'territorio': ter_d02.pk
        })
        self.assertEqual(JuntaVecinos.objects.count(), c_jv)

        c_ev = Evidencia.objects.count()
        self.client.post('/actividades/evidencias/crear/', {
            'codigo': 'EVI-HUERFANA', 'archivo_ruta': 'sin_origen.jpg', 'observacion': 'Sin actividad ni caso social'
        })
        self.assertEqual(Evidencia.objects.count(), c_ev)


class Test04AutenticacionPermisosYSeguridad(SGRBaseTestCase):
    """Criterios 8, 9 y 10: Sesiones, Login/Logout POST+CSRF, Acceso Anónimo, Consulta (403) vs Gestión, 404 y Redirecciones."""

    def test_01_login_valido_invalido_inactivo_y_open_redirect(self):
        c = Client(SERVER_NAME='localhost')
        # Login inválido (clave errónea)
        r_bad = c.post('/login/', {'username': 'admin', 'password': 'clave_incorrecta'})
        self.assertEqual(r_bad.status_code, 200)
        self.assertNotIn('_auth_user_id', c.session)

        # Login inválido (usuario inactivo)
        r_ina = c.post('/login/', {'username': 'ironman', 'password': 'admin'})
        self.assertNotIn('_auth_user_id', c.session)

        # Rechazo de redirección externa en login (?next=https://evil.example.com)
        r_ext = c.post('/login/?next=https://evil.example.com/phish', {'username': 'batman', 'password': 'admin'})
        self.assertEqual(r_ext.status_code, 302)
        self.assertEqual(r_ext['Location'], '/')

    def test_02_logout_post_csrf_y_cambio_delegacion_post(self):
        c_csrf = Client(SERVER_NAME='localhost', enforce_csrf_checks=True)
        r_login_page = c_csrf.get('/login/')
        csrf_token = r_login_page.cookies['csrftoken'].value
        r_log = c_csrf.post('/login/', {'username': 'admin', 'password': 'admin', 'csrfmiddlewaretoken': csrf_token})
        self.assertEqual(r_log.status_code, 302)

        # GET a /logout/ debe ser rechazado con 405
        r_get_logout = c_csrf.get('/logout/')
        self.assertEqual(r_get_logout.status_code, 405)

        # POST a /logout/ sin CSRF debe ser rechazado con 403
        r_no_csrf = c_csrf.post('/logout/', {})
        self.assertEqual(r_no_csrf.status_code, 403)

        # GET a /cambiar-delegacion/ debe ser rechazado con 405
        self.assertEqual(c_csrf.get('/cambiar-delegacion/todas/').status_code, 405)

        # POST a /cambiar-delegacion/ con CSRF y rechazo de HTTP_REFERER externo
        csrf_token = c_csrf.cookies['csrftoken'].value
        r_del = c_csrf.post(
            '/cambiar-delegacion/todas/',
            {'csrfmiddlewaretoken': csrf_token},
            HTTP_REFERER='https://malicious.site/attack'
        )
        self.assertEqual(r_del.status_code, 302)
        self.assertEqual(r_del['Location'], '/')

        # POST a /logout/ con CSRF válido cierra la sesión
        r_ok_logout = c_csrf.post('/logout/', {'csrfmiddlewaretoken': csrf_token})
        self.assertEqual(r_ok_logout.status_code, 302)
        self.assertNotIn('_auth_user_id', c_csrf.session)

    def test_03_acceso_anonimo_redirige_a_login_en_todas_las_rutas(self):
        c_anon = Client(SERVER_NAME='localhost')
        rutas_protegidas = [
            '/', '/mantenedores/',
            '/mantenedores/delegaciones/', '/mantenedores/delegaciones/crear/',
            '/mantenedores/territorios/', '/mantenedores/territorios/crear/',
            '/mantenedores/usuarios/', '/mantenedores/usuarios/crear/',
            '/mantenedores/cargos/', '/mantenedores/cargos/crear/',
            '/mantenedores/roles/', '/mantenedores/roles/crear/',
            '/mantenedores/vecinos/', '/mantenedores/vecinos/crear/',
            '/mantenedores/juntas-vecinos/', '/mantenedores/juntas-vecinos/crear/',
            '/mantenedores/participaciones/', '/mantenedores/participaciones/crear/',
            '/mantenedores/hitos/', '/mantenedores/hitos/crear/',
            '/actividades/', '/actividades/nueva/',
            '/actividades/social/', '/actividades/social/nueva/',
            '/mantenedores/tipos-atencion/', '/mantenedores/tipos-atencion/crear/',
            '/mantenedores/subatenciones/', '/mantenedores/subatenciones/crear/',
            '/mantenedores/items/', '/mantenedores/items/crear/',
            '/mantenedores/asignaciones-metas/', '/mantenedores/asignaciones-metas/crear/',
            '/actividades/evidencias/', '/actividades/evidencias/crear/',
            '/mantenedores/trimestres/', '/mantenedores/trimestres/crear/',
            '/agenda/', '/agenda/resumen/', '/agenda/nuevo/',
            '/resultados/', '/resultados/informe/', '/organizacion/',
        ]
        for ruta in rutas_protegidas:
            resp = c_anon.get(ruta)
            self.assertEqual(resp.status_code, 302, f'Ruta anónima {ruta} no redirigió a login')
            self.assertIn('/login', resp['Location'])

    def test_04_matriz_completa_consulta_403_y_404_en_las_17_entidades(self):
        c_con = Client(SERVER_NAME='localhost')
        c_con.post('/login/', {'username': 'batman', 'password': 'admin'})

        entidades_rutas = [
            (Delegacion.objects.first().pk, '/mantenedores/delegaciones/', '/mantenedores/delegaciones/crear/', '/mantenedores/delegaciones/{pk}/detalle/', '/mantenedores/delegaciones/{pk}/editar/', '/mantenedores/delegaciones/{pk}/eliminar/'),
            (Territorio.objects.first().pk, '/mantenedores/territorios/', '/mantenedores/territorios/crear/', '/mantenedores/territorios/{pk}/detalle/', '/mantenedores/territorios/{pk}/editar/', '/mantenedores/territorios/{pk}/eliminar/'),
            (User.objects.first().pk, '/mantenedores/usuarios/', '/mantenedores/usuarios/crear/', '/mantenedores/usuarios/{pk}/detalle/', '/mantenedores/usuarios/{pk}/editar/', '/mantenedores/usuarios/{pk}/eliminar/'),
            (Cargo.objects.first().pk, '/mantenedores/cargos/', '/mantenedores/cargos/crear/', '/mantenedores/cargos/{pk}/detalle/', '/mantenedores/cargos/{pk}/editar/', '/mantenedores/cargos/{pk}/eliminar/'),
            (Rol.objects.first().pk, '/mantenedores/roles/', '/mantenedores/roles/crear/', '/mantenedores/roles/{pk}/detalle/', '/mantenedores/roles/{pk}/editar/', '/mantenedores/roles/{pk}/eliminar/'),
            (Vecino.objects.first().pk, '/mantenedores/vecinos/', '/mantenedores/vecinos/crear/', '/mantenedores/vecinos/{pk}/detalle/', '/mantenedores/vecinos/{pk}/editar/', '/mantenedores/vecinos/{pk}/eliminar/'),
            (JuntaVecinos.objects.first().pk, '/mantenedores/juntas-vecinos/', '/mantenedores/juntas-vecinos/crear/', '/mantenedores/juntas-vecinos/{pk}/detalle/', '/mantenedores/juntas-vecinos/{pk}/editar/', '/mantenedores/juntas-vecinos/{pk}/eliminar/'),
            (ParticipacionJunta.objects.first().pk, '/mantenedores/participaciones/', '/mantenedores/participaciones/crear/', '/mantenedores/participaciones/{pk}/detalle/', '/mantenedores/participaciones/{pk}/editar/', '/mantenedores/participaciones/{pk}/eliminar/'),
            (Hito.objects.first().pk, '/mantenedores/hitos/', '/mantenedores/hitos/crear/', '/mantenedores/hitos/{pk}/detalle/', '/mantenedores/hitos/{pk}/editar/', '/mantenedores/hitos/{pk}/eliminar/'),
            (Actividad.objects.first().pk, '/actividades/', '/actividades/nueva/', '/actividades/actividad/{pk}/', '/actividades/actividad/{pk}/editar/', '/actividades/actividad/{pk}/eliminar/'),
            (GestionSocial.objects.first().pk, '/actividades/social/', '/actividades/social/nueva/', '/actividades/social/{pk}/', '/actividades/social/{pk}/editar/', '/actividades/social/{pk}/eliminar/'),
            (TipoAtencion.objects.first().pk, '/mantenedores/tipos-atencion/', '/mantenedores/tipos-atencion/crear/', '/mantenedores/tipos-atencion/{pk}/detalle/', '/mantenedores/tipos-atencion/{pk}/editar/', '/mantenedores/tipos-atencion/{pk}/eliminar/'),
            (SubAtencion.objects.first().pk, '/mantenedores/subatenciones/', '/mantenedores/subatenciones/crear/', '/mantenedores/subatenciones/{pk}/detalle/', '/mantenedores/subatenciones/{pk}/editar/', '/mantenedores/subatenciones/{pk}/eliminar/'),
            (ItemMeta.objects.first().pk, '/mantenedores/items/', '/mantenedores/items/crear/', '/mantenedores/items/{pk}/detalle/', '/mantenedores/items/{pk}/editar/', '/mantenedores/items/{pk}/eliminar/'),
            (MetaFuncionario.objects.first().pk, '/mantenedores/asignaciones-metas/', '/mantenedores/asignaciones-metas/crear/', '/mantenedores/asignaciones-metas/{pk}/detalle/', '/mantenedores/asignaciones-metas/{pk}/editar/', '/mantenedores/asignaciones-metas/{pk}/eliminar/'),
            (Evidencia.objects.first().pk, '/actividades/evidencias/', '/actividades/evidencias/crear/', '/actividades/evidencia/{pk}/', '/actividades/evidencia/{pk}/editar/', '/actividades/evidencia/{pk}/eliminar/'),
            (PeriodoEvaluacion.objects.first().pk, '/mantenedores/trimestres/', '/mantenedores/trimestres/crear/', '/mantenedores/trimestres/{pk}/detalle/', '/mantenedores/trimestres/{pk}/editar/', '/mantenedores/trimestres/{pk}/eliminar/'),
        ]

        c_admin = Client(SERVER_NAME='localhost')
        c_admin.post('/login/', {'username': 'admin', 'password': 'admin'})

        for pk, u_list, u_create, u_det, u_edit, u_del in entidades_rutas:
            # Consulta puede listar y ver detalle (200 OK)
            self.assertEqual(c_con.get(u_list).status_code, 200)
            self.assertEqual(c_con.get(u_det.format(pk=pk)).status_code, 200)

            # Consulta recibe HTTP 403 en GET y POST de crear, editar y eliminar en las 17 entidades
            for u_write in [u_create, u_edit.format(pk=pk), u_del.format(pk=pk)]:
                self.assertEqual(c_con.get(u_write).status_code, 403, f'Consulta GET {u_write} debe ser 403')
                self.assertEqual(c_con.post(u_write, {}).status_code, 403, f'Consulta POST {u_write} debe ser 403')

            # IDs inexistentes (999999) devuelven HTTP 404 en Detalle, Editar y Eliminar
            for u_404 in [u_det.format(pk=999999), u_edit.format(pk=999999), u_del.format(pk=999999)]:
                self.assertEqual(c_admin.get(u_404).status_code, 404, f'ID inexistente en {u_404} debe devolver 404')
