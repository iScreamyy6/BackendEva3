from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.views.static import serve
from django.conf import settings
from . import views
from . import views_auth
from . import views_mantenedores
from actividades import views as act_views
from actividades.views import api_buscar_vecino

urlpatterns = [
    # Panel Django Admin oficial
    path('admin/', admin.site.urls),

    # Wireframe Interactivo (Artefacto para Ingeniería de Software TI2043)
    path('wireframes/', TemplateView.as_view(template_name='wireframes/wireframe_interactivo_sgr.html'), name='wireframes_interactivos'),

    # Página principal
    path('', views.inicio, name='inicio'),

    # Autenticación y Flujo de Recuperación de Contraseña
    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('recuperar/', views_auth.recuperar_solicitar_view, name='recuperar_solicitar'),
    path('recuperar/validar/', views_auth.recuperar_validar_view, name='recuperar_validar'),
    path('recuperar/nueva-clave/', views_auth.recuperar_nueva_clave_view, name='recuperar_nueva_clave'),
    path('recuperar/reset/<str:uidb64>/<str:token>/', views_auth.recuperar_reset_confirm_view, name='recuperar_reset_confirm'),
    path('cambiar-delegacion/<str:delegacion_id>/', views_auth.cambiar_delegacion_view, name='cambiar_delegacion'),

    # Panel Consolidado de las 17 Entidades Obligatorias SGR
    path('mantenedores/', views_mantenedores.mantenedores_inicio, name='mantenedores_inicio'),

    # 1. Delegación
    path('mantenedores/delegaciones/', views_mantenedores.delegaciones_lista, name='delegaciones_lista'),
    path('mantenedores/delegaciones/crear/', views_mantenedores.delegaciones_crear, name='delegaciones_crear'),
    path('mantenedores/delegaciones/<int:pk>/detalle/', views_mantenedores.delegaciones_detalle, name='delegaciones_detalle'),
    path('mantenedores/delegaciones/<int:pk>/editar/', views_mantenedores.delegaciones_editar, name='delegaciones_editar'),
    path('mantenedores/delegaciones/<int:pk>/eliminar/', views_mantenedores.delegaciones_eliminar, name='delegaciones_eliminar'),

    # 2. Territorio
    path('mantenedores/territorios/', views_mantenedores.territorios_lista, name='territorios_lista'),
    path('mantenedores/territorios/crear/', views_mantenedores.territorios_crear, name='territorios_crear'),
    path('mantenedores/territorios/<int:pk>/detalle/', views_mantenedores.territorios_detalle, name='territorios_detalle'),
    path('mantenedores/territorios/<int:pk>/editar/', views_mantenedores.territorios_editar, name='territorios_editar'),
    path('mantenedores/territorios/<int:pk>/eliminar/', views_mantenedores.territorios_eliminar, name='territorios_eliminar'),

    # 3. Usuario Funcionario
    path('mantenedores/usuarios/', views_mantenedores.usuarios_lista, name='usuarios_lista'),
    path('mantenedores/usuarios/crear/', views_mantenedores.usuarios_crear, name='usuarios_crear'),
    path('mantenedores/usuarios/<int:pk>/detalle/', views_mantenedores.usuarios_detalle, name='usuarios_detalle'),
    path('mantenedores/usuarios/<int:pk>/editar/', views_mantenedores.usuarios_editar, name='usuarios_editar'),
    path('mantenedores/usuarios/<int:pk>/eliminar/', views_mantenedores.usuarios_eliminar, name='usuarios_eliminar'),

    # 4. Cargo
    path('mantenedores/cargos/', views_mantenedores.cargos_lista, name='cargos_lista'),
    path('mantenedores/cargos/crear/', views_mantenedores.cargos_crear, name='cargos_crear'),
    path('mantenedores/cargos/<int:pk>/detalle/', views_mantenedores.cargos_detalle, name='cargos_detalle'),
    path('mantenedores/cargos/<int:pk>/editar/', views_mantenedores.cargos_editar, name='cargos_editar'),
    path('mantenedores/cargos/<int:pk>/eliminar/', views_mantenedores.cargos_eliminar, name='cargos_eliminar'),

    # 5. Rol
    path('mantenedores/roles/', views_mantenedores.roles_lista, name='roles_lista'),
    path('mantenedores/roles/crear/', views_mantenedores.roles_crear, name='roles_crear'),
    path('mantenedores/roles/<int:pk>/detalle/', views_mantenedores.roles_detalle, name='roles_detalle'),
    path('mantenedores/roles/<int:pk>/editar/', views_mantenedores.roles_editar, name='roles_editar'),
    path('mantenedores/roles/<int:pk>/eliminar/', views_mantenedores.roles_eliminar, name='roles_eliminar'),

    # 6. Vecino
    path('mantenedores/vecinos/', views_mantenedores.vecinos_lista, name='vecinos_lista'),
    path('mantenedores/vecinos/crear/', views_mantenedores.vecinos_crear, name='vecinos_crear'),
    path('mantenedores/vecinos/<int:pk>/detalle/', views_mantenedores.vecinos_detalle, name='vecinos_detalle'),
    path('mantenedores/vecinos/<int:pk>/editar/', views_mantenedores.vecinos_editar, name='vecinos_editar'),
    path('mantenedores/vecinos/<int:pk>/eliminar/', views_mantenedores.vecinos_eliminar, name='vecinos_eliminar'),

    # 7. Junta de Vecinos
    path('mantenedores/juntas-vecinos/', views_mantenedores.juntas_vecinos_lista, name='juntas_vecinos_lista'),
    path('mantenedores/juntas-vecinos/crear/', views_mantenedores.juntas_vecinos_crear, name='juntas_vecinos_crear'),
    path('mantenedores/juntas-vecinos/<int:pk>/detalle/', views_mantenedores.juntas_vecinos_detalle, name='juntas_vecinos_detalle'),
    path('mantenedores/juntas-vecinos/<int:pk>/editar/', views_mantenedores.juntas_vecinos_editar, name='juntas_vecinos_editar'),
    path('mantenedores/juntas-vecinos/<int:pk>/eliminar/', views_mantenedores.juntas_vecinos_eliminar, name='juntas_vecinos_eliminar'),
    path('mantenedores/juntas-vecinos/<int:pk>/agregar-dirigente/', views_mantenedores.juntas_vecinos_agregar_dirigente, name='juntas_vecinos_agregar_dirigente'),
    path('mantenedores/participacion/<int:pk_participacion>/quitar/', views_mantenedores.juntas_vecinos_quitar_dirigente, name='juntas_vecinos_quitar_dirigente'),

    # 8. Participación en Junta
    path('mantenedores/participaciones/', views_mantenedores.participaciones_lista, name='participaciones_lista'),
    path('mantenedores/participaciones/crear/', views_mantenedores.participaciones_crear, name='participaciones_crear'),
    path('mantenedores/participaciones/<int:pk>/detalle/', views_mantenedores.participaciones_detalle, name='participaciones_detalle'),
    path('mantenedores/participaciones/<int:pk>/editar/', views_mantenedores.participaciones_editar, name='participaciones_editar'),
    path('mantenedores/participaciones/<int:pk>/eliminar/', views_mantenedores.participaciones_eliminar, name='participaciones_eliminar'),

    # 9. Hito
    path('mantenedores/hitos/', views_mantenedores.hitos_lista, name='hitos_lista'),
    path('mantenedores/hitos/crear/', views_mantenedores.hitos_crear, name='hitos_crear'),
    path('mantenedores/hitos/<int:pk>/detalle/', views_mantenedores.hitos_detalle, name='hitos_detalle'),
    path('mantenedores/hitos/<int:pk>/editar/', views_mantenedores.hitos_editar, name='hitos_editar'),
    path('mantenedores/hitos/<int:pk>/eliminar/', views_mantenedores.hitos_eliminar, name='hitos_eliminar'),

    # 10. Actividad (rutas directas en mantenedores y alias sin namespace)
    path('mantenedores/actividades/', act_views.lista_actividades, name='lista_actividades'),
    path('mantenedores/actividades/crear/', act_views.formulario_actividad, name='nueva_actividad'),
    path('mantenedores/actividades/<int:actividad_id>/detalle/', act_views.detalle_actividad, name='detalle_actividad_mant'),
    path('mantenedores/actividades/<int:actividad_id>/editar/', act_views.editar_actividad, name='editar_actividad_mant'),
    path('mantenedores/actividades/<int:actividad_id>/eliminar/', act_views.eliminar_actividad, name='eliminar_actividad_mant'),

    # 11. Gestión Social (rutas directas en mantenedores y alias sin namespace)
    path('mantenedores/gestiones-sociales/', act_views.lista_gestiones_sociales, name='lista_gestiones_sociales'),
    path('mantenedores/gestiones-sociales/crear/', act_views.formulario_gestion_social, name='nueva_gestion_social'),
    path('mantenedores/gestiones-sociales/<int:pk>/detalle/', act_views.detalle_gestion_social, name='detalle_gestion_social_mant'),
    path('mantenedores/gestiones-sociales/<int:pk>/editar/', act_views.editar_gestion_social, name='editar_gestion_social_mant'),
    path('mantenedores/gestiones-sociales/<int:pk>/eliminar/', act_views.eliminar_gestion_social, name='eliminar_gestion_social_mant'),

    # 12. Tipo de Atención
    path('mantenedores/tipos-atencion/', views_mantenedores.tipos_atencion_lista, name='tipos_atencion_lista'),
    path('mantenedores/tipos-atencion/crear/', views_mantenedores.tipos_atencion_crear, name='tipos_atencion_crear'),
    path('mantenedores/tipos-atencion/<int:pk>/detalle/', views_mantenedores.tipos_atencion_detalle, name='tipos_atencion_detalle'),
    path('mantenedores/tipos-atencion/<int:pk>/editar/', views_mantenedores.tipos_atencion_editar, name='tipos_atencion_editar'),
    path('mantenedores/tipos-atencion/<int:pk>/eliminar/', views_mantenedores.tipos_atencion_eliminar, name='tipos_atencion_eliminar'),

    # 13. Subtipo de Atención
    path('mantenedores/subatenciones/', views_mantenedores.subatenciones_lista, name='subatenciones_lista'),
    path('mantenedores/subatenciones/crear/', views_mantenedores.subatenciones_crear, name='subatenciones_crear'),
    path('mantenedores/subatenciones/<int:pk>/detalle/', views_mantenedores.subatenciones_detalle, name='subatenciones_detalle'),
    path('mantenedores/subatenciones/<int:pk>/editar/', views_mantenedores.subatenciones_editar, name='subatenciones_editar'),
    path('mantenedores/subatenciones/<int:pk>/eliminar/', views_mantenedores.subatenciones_eliminar, name='subatenciones_eliminar'),

    # 14. Meta (Catálogo de Ítems y Metas)
    path('mantenedores/items/', views_mantenedores.items_lista, name='items_lista'),
    path('mantenedores/items/crear/', views_mantenedores.items_crear, name='items_crear'),
    path('mantenedores/items/<int:pk>/detalle/', views_mantenedores.items_detalle, name='items_detalle'),
    path('mantenedores/items/<int:pk>/editar/', views_mantenedores.items_editar, name='items_editar'),
    path('mantenedores/items/<int:pk>/eliminar/', views_mantenedores.items_eliminar, name='items_eliminar'),

    # 15. Asignación de Meta
    path('mantenedores/asignaciones-metas/', views_mantenedores.asignaciones_metas_lista, name='asignaciones_metas_lista'),
    path('mantenedores/asignaciones-metas/crear/', views_mantenedores.asignaciones_metas_crear, name='asignaciones_metas_crear'),
    path('mantenedores/asignaciones-metas/<int:pk>/detalle/', views_mantenedores.asignaciones_metas_detalle, name='asignaciones_metas_detalle'),
    path('mantenedores/asignaciones-metas/<int:pk>/editar/', views_mantenedores.asignaciones_metas_editar, name='asignaciones_metas_editar'),
    path('mantenedores/asignaciones-metas/<int:pk>/eliminar/', views_mantenedores.asignaciones_metas_eliminar, name='asignaciones_metas_eliminar'),

    # 16. Evidencia (rutas directas en mantenedores y alias sin namespace)
    path('mantenedores/evidencias/', act_views.lista_evidencias, name='lista_evidencias'),
    path('mantenedores/evidencias/crear/', act_views.crear_evidencia, name='crear_evidencia'),
    path('mantenedores/evidencias/<int:evidencia_id>/detalle/', act_views.detalle_evidencia, name='detalle_evidencia_mant'),
    path('mantenedores/evidencias/<int:evidencia_id>/editar/', act_views.editar_evidencia, name='editar_evidencia_mant'),
    path('mantenedores/evidencias/<int:evidencia_id>/eliminar/', act_views.eliminar_evidencia, name='eliminar_evidencia_mant'),

    # 17. Trimestre (Período de Evaluación)
    path('mantenedores/trimestres/', views_mantenedores.trimestres_lista, name='trimestres_lista'),
    path('mantenedores/trimestres/crear/', views_mantenedores.trimestres_crear, name='trimestres_crear'),
    path('mantenedores/trimestres/<int:pk>/detalle/', views_mantenedores.trimestres_detalle, name='trimestres_detalle'),
    path('mantenedores/trimestres/<int:pk>/editar/', views_mantenedores.trimestres_editar, name='trimestres_editar'),
    path('mantenedores/trimestres/<int:pk>/eliminar/', views_mantenedores.trimestres_eliminar, name='trimestres_eliminar'),

    # Ingreso y Módulo de Atención Ciudadana
    path('atenciones/', views_mantenedores.atenciones_lista, name='atenciones_lista'),
    path('atenciones/nueva/', views_mantenedores.atencion_nueva, name='atencion_nueva'),
    path('atenciones/<int:pk>/', views_mantenedores.atenciones_detalle, name='atenciones_detalle'),
    path('api/subatenciones/', views_mantenedores.api_subatenciones_por_tipo, name='api_subatenciones'),
    path('api/territorios-por-delegacion/', views_mantenedores.api_territorios_por_delegacion, name='api_territorios_por_delegacion'),
    path('api/vecinos/buscar/', api_buscar_vecino, name='api_buscar_vecino'),

    # Módulos preexistentes de Evaluaciones Anteriores
    path('organizacion/', include('organizacion.urls')),
    path('actividades/', include('actividades.urls')),
    path('agenda/', include('agenda.urls')),
    path('resultados/', include('resultados.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]