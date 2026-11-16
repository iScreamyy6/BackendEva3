from django.contrib import admin
from .models import (
    Delegacion, Funcionario, Rol, PerfilUsuario, CargoTipoGestion,
    Cargo, Territorio, JuntaVecinos, ParticipacionJunta, Hito
)


class FuncionarioInline(admin.TabularInline):
    model = Funcionario
    extra = 1
    fields = ('nombre', 'cargo', 'activo', 'fecha_ingreso')
    fk_name = 'id_delegacion'


@admin.register(Delegacion)
class DelegacionAdmin(admin.ModelAdmin):
    list_display = ('id_delegacion', 'codigo', 'nombre', 'ambito', 'comuna', 'responsable', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'ambito', 'comuna')
    search_fields = ('codigo', 'nombre', 'responsable', 'ambito', 'direccion')
    ordering = ('id_delegacion',)
    inlines = [FuncionarioInline]


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id_rol', 'codigo', 'nombre', 'alcance_autorizado', 'permisos', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'alcance_autorizado')
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('id_rol',)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_username', 'get_email', 'rol', 'delegacion_activa', 'estado')
    list_filter = ('estado', 'rol', 'delegacion_activa')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    filter_horizontal = ('delegaciones_autorizadas',)

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Usuario'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Correo'


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('id_funcionario', 'nombre', 'cargo', 'user', 'id_delegacion', 'activo', 'fecha_ingreso')
    list_filter = ('activo', 'id_delegacion', 'cargo')
    search_fields = ('nombre', 'cargo', 'id_delegacion__nombre', 'user__username')
    ordering = ('id_funcionario',)


@admin.register(CargoTipoGestion)
class CargoTipoGestionAdmin(admin.ModelAdmin):
    list_display = ('id_cargo_tipo', 'cargo', 'id_tipo', 'fecha_creacion')
    list_filter = ('cargo', 'id_tipo')
    search_fields = ('cargo', 'id_tipo__nombre')
    ordering = ('cargo', 'id_tipo')


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('id_cargo', 'codigo', 'nombre', 'estado', 'fecha_creacion')
    list_filter = ('estado',)
    search_fields = ('codigo', 'nombre', 'descripcion')


@admin.register(Territorio)
class TerritorioAdmin(admin.ModelAdmin):
    list_display = ('id_territorio', 'codigo', 'nombre', 'delegacion', 'estado')
    list_filter = ('estado', 'delegacion')
    search_fields = ('codigo', 'nombre', 'descripcion')


@admin.register(JuntaVecinos)
class JuntaVecinosAdmin(admin.ModelAdmin):
    list_display = ('id_junta', 'codigo', 'nombre', 'delegacion', 'territorio', 'estado')
    list_filter = ('estado', 'delegacion')
    search_fields = ('codigo', 'nombre', 'direccion')


@admin.register(ParticipacionJunta)
class ParticipacionJuntaAdmin(admin.ModelAdmin):
    list_display = ('id_participacion', 'codigo', 'vecino', 'junta', 'cargo', 'es_dirigente', 'estado')
    list_filter = ('estado', 'es_dirigente', 'junta')
    search_fields = ('codigo', 'vecino__nombre', 'junta__nombre')


@admin.register(Hito)
class HitoAdmin(admin.ModelAdmin):
    list_display = ('id_hito', 'codigo', 'nombre', 'periodicidad', 'delegacion', 'territorio', 'fecha_inicio', 'fecha_termino', 'estado')
    list_filter = ('estado', 'periodicidad', 'delegacion')
    search_fields = ('codigo', 'nombre', 'descripcion')



