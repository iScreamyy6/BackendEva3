# Guía de Defensa Técnica: Preguntas Frecuentes del Código y Arquitectura SGR
**Sistema de Gestión de Resultados (SGR) — Ilustre Municipalidad de La Serena**  
*Documento de Preparación para Interrogación y Evaluación Docente (Backend Django / AWS EC2)*

---

## 1. Mapa Rápido de Ubicación del Código

Si el docente pide: *"Ábreme el archivo donde está X..."*, usa esta tabla de referencia inmediata:

| Componente / Funcionalidad | Archivo Clave | Funciones / Clases Relevantes |
|---|---|---|
| **Configuración General & AWS** | `Municipalidad/settings.py` | `DATABASES`, `STATICFILES_STORAGE`, `MIDDLEWARE`, `AUTH_PASSWORD_VALIDATORS` |
| **Control de Acceso RBAC & Permisos** | `Municipalidad/views_mantenedores.py` | `es_consulta()`, `puede_escribir_mantenedor()`, `respuesta_403()` |
| **Gestión de Sesión & Delegación Activa** | `Municipalidad/context_processors.py` | `delegacion_context()` |
| **Login / Logout / Recuperación Token** | `Municipalidad/views_auth.py` | `login_view()`, `recuperar_solicitar_view()`, `recuperar_reset_confirm_view()` |
| **CRUD de las 17 Entidades SGR** | `Municipalidad/views_mantenedores.py` | Vistas `*_lista`, `*_crear`, `*_detalle`, `*_editar`, `*_eliminar` |
| **Formularios y Validaciones Servidor** | `Municipalidad/forms_mantenedores.py` | `ModelForm`, métodos `clean_codigo()`, `clean()`, validación de RUT y fechas |
| **Gestión Unificada & Atenciones** | `actividades/views.py` | `formulario_actividad()`, `lista_actividades()`, `api_buscar_vecino()` |
| **Tablero Kanban (Tubo de Trabajo)** | `agenda/views.py` | `resumen_agenda()`, `cambiar_estado_compromiso()`, `puede_mover_compromiso()` |
| **Indicadores y Metas Trimestrales** | `resultados/views.py` y `models.py` | `lista_metas()`, `MetaFuncionario.porcentaje_cumplimiento` |
| **Seeder de Superhéroes y 17 Entidades** | `organizacion/management/commands/poblar_datos.py` | `Command.handle()`, creación con clave única `admin` |
| **Suite de Pruebas Automatizadas** | `test_suite.py` y `organizacion/tests.py` | Pruebas de 17 entidades, ModelForms, HTTP 403, 404, filtros y dashboards |

---

## 2. Bloque 1: Arquitectura y Estructura del Software

### P1: "¿Qué patrón de arquitectura utiliza el proyecto y cómo está organizado?"
* **Respuesta Técnica:**  
  El proyecto utiliza el patrón **MVT (Model-View-Template)** nativo de Django, con una separación modular en aplicaciones desacopladas:
  1. `Municipalidad`: Núcleo del proyecto, orquestación de rutas globales (`urls.py`), mantenedores de las 17 entidades (`views_mantenedores.py`), autenticación central (`views_auth.py`) y procesador de contexto global (`context_processors.py`).
  2. `organizacion`: Entidades estructurales (Delegaciones, Territorios, Cargos, Roles, Funcionarios, Juntas de Vecinos, Hitos).
  3. `actividades`: Registro de atenciones ciudadanas, gestiones unificadas, casos sociales y evidencias fotográficas.
  4. `agenda`: Tablero Kanban del Tubo de Trabajo y compromisos con fechas límites.
  5. `resultados`: Catálogo de ítems de evaluación, períodos trimestrales, asignaciones de metas a funcionarios y semáforo comunal.

### P2: "¿Por qué tienen un `context_processors.py` y qué función cumple?"
* **Respuesta Técnica:**  
  Permite inyectar variables globales a **todos los templates HTML automáticamente**, sin necesidad de consultar la base de datos ni pasar los mismos datos vista por vista.  
  En nuestro sistema resuelve:
  - La **Delegación Activa** del usuario actual (extraída de la sesión o su perfil).
  - La lista de delegaciones disponibles a las que tiene acceso.
  - Los flags booleanos de perfil: `es_admin`, `es_gestion`, `es_consulta`, `es_super`.

---

## 3. Bloque 2: Modelo de Datos, Integridad Referencial y las 17 Entidades

### P3: "¿Cómo estructuraron las 17 entidades obligatorias en la base de datos?"
* **Respuesta Técnica:**  
  Están modeladas mediante el ORM de Django con claves foráneas e integridad referencial estricta:
  1. **Organizacionales (1-9):** `Delegacion` → `Territorio`, `Cargo`, `Rol`, `Funcionario` + `PerfilUsuario`, `Vecino`, `JuntaVecinos` + `ParticipacionJunta`, `Hito`.
  2. **Operativas (10-13, 16):** `Actividad` (Gestión Unificada), `GestionSocial`, `TipoAtencion`, `SubAtencion`, `Evidencia`.
  3. **Estratégicas (14-15, 17):** `ItemMeta` (Catálogo), `PeriodoEvaluacion` (Trimestres), `MetaFuncionario` (Asignación ponderada con cálculo de cumplimiento).

### P4: "¿Qué estrategia de borrado usaron: físico o lógico? ¿Cómo protegen la integridad referencial?"
* **Respuesta Técnica:**  
  Implementamos una **estrategia híbrida de seguridad referencial**:
  - **Borrado Lógico (Desactivación):** Si un registro ya tiene registros dependientes (por ejemplo, una Delegación con territorios o funcionarios, o un Cargo con personas asignadas), el sistema rechaza el borrado físico para evitar errores de integridad (`ProtectedError` o fallas en cascada) y **cambia su estado a `Inactivo`**.
  - **Borrado Físico Seguro:** Si el registro es nuevo o no posee dependencias hijas, se permite la eliminación física mediante confirmación explícita vía método `POST` (protegido contra ataques CSRF).
  - En los modelos usamos `on_delete=models.RESTRICT` o `models.PROTECT` en entidades críticas para impedir que se borren datos transaccionales históricos por accidente.

### P5: "¿Cómo garantizan que existan registros activos e inactivos de las 17 entidades?"
* **Respuesta Técnica:**  
  En el comando `python manage.py poblar_datos`, cada una de las 17 entidades cuenta con al menos 2 registros activos y **al menos 1 registro en estado 'Inactivo'** (ej. delegación costera histórica, cargos descontinuados, metas archivadas, directivas vecinales vencidas), lo que permite validar filtros y estados en la interfaz.

---

## 4. Bloque 3: Seguridad, Autenticación y RBAC (La Clave de la Evaluación #3)

### P6: "¿Cómo implementaron el control de acceso basado en roles (RBAC) y la diferencia entre Gestión y Consulta?"
* **Respuesta Técnica:**  
  La seguridad se implementa en múltiples capas:
  1. **Capa de Grupos y Permisos Django (`auth_group`):** Se asigna a cada usuario un grupo Django (`Administrador`, `Gestión`, `Consulta`, `Supervisor`, `Administrativo`).
  2. **Capa de Modelo Extendido (`PerfilUsuario`):** Cada cuenta tiene un `Rol` institucional (`ROL-ADM`, `ROL-GEST`, `ROL-CON`, etc.) con un alcance territorial (`COMUNAL` o `DELEGACION`).
  3. **Capa de Vistas (Controladores):**
     - En `views_mantenedores.py`, las funciones `puede_consultar_mantenedor(user)` y `puede_escribir_mantenedor(user)` inspeccionan si el usuario pertenece al perfil `Consulta`.
     - Si el usuario **`batman`** (Perfil Consulta) intenta ingresar por GET o enviar un POST a cualquier URL de creación (`/crear/`), edición (`/editar/`) o borrado (`/eliminar/`), el sistema intercepta la petición y retorna una respuesta oficial con código **`HTTP 403 Forbidden`** (`respuesta_403()`).
     - El usuario **`mujermaravilla`** (Perfil Gestión) tiene habilitados todos los métodos GET y POST, permitiendo operaciones CRUD completas con respuestas `200 OK` y `302 Redirect`.

### P7: "¿Cómo se almacenan las contraseñas en la base de datos? ¿Están en texto plano?"
* **Respuesta Técnica:**  
  **Nunca en texto plano.** Django utiliza por defecto el algoritmo **PBKDF2 con hash SHA-256** y una sal criptográfica (*salt*) única por usuario con más de 720.000 iteraciones. En la base de datos se almacena una cadena hash con el formato `pbkdf2_sha256$720000$...`. En el seeder se aplicó `make_password('admin')`.

### P8: "¿Cómo funciona el flujo de recuperación de contraseña?"
* **Respuesta Técnica:**  
  En [views_auth.py](file:///c:/Users/iScreamyy6/Downloads/Backend-main/Backend-main/Municipalidad/views_auth.py#L230-L380):
  1. El usuario ingresa su correo institucional (`recuperar_solicitar_view`).
  2. El servidor genera un **código numérico de 6 dígitos** (almacenado en sesión con timestamp de expiración a 15 minutos) y un **token criptográfico de un solo uso** mediante `default_token_generator` y codificación base64 del ID del usuario (`uidb64`).
  3. Se simula el despacho de un correo HTML corporativo con el código y el enlace directo seguro `/recuperar/reset/<uidb64>/<token>/`.
  4. Tras validar el código o token, el usuario define su nueva contraseña, la cual es validada y hasheada, invalidando el token consumido.

---

## 5. Bloque 4: Formularios, Validaciones y ModelForms

### P9: "¿Dónde y cómo validan que los datos ingresados sean correctos?"
* **Respuesta Técnica:**  
  En `Municipalidad/forms_mantenedores.py` mediante clases `forms.ModelForm`:
  - **Unicidad de Código:** Métodos `clean_codigo()` verifican que el código institucional (ej. `D01`, `CRG-01`, `TER-01`) no esté duplicado, excluyendo la propia instancia al editar (`.exclude(pk=self.instance.pk)`).
  - **Coherencia de Fechas:** En Hitos, Metas y Actividades, el método `clean()` valida que la fecha de término o de compromiso sea posterior o igual a la fecha de inicio.
  - **Rangos Numéricos:** En asignaciones de metas se valida que el ponderador esté entre 1% y 100%, y que las metas no sean negativas.
  - **Validación de RUT:** Limpieza de puntos y guion con algoritmo de dígito verificador.

### P10: "¿Qué pasa si un usuario envía un formulario vacío o con datos inválidos?"
* **Respuesta Técnica:**  
  El método `form.is_valid()` retorna `False`. El controlador no guarda en la base de datos, re-renderiza la plantilla pasando `form.errors`, y la interfaz despliega mensajes contextuales en color rojo bajo cada campo afectado, conservando los datos previamente tipeados para no obligar al usuario a reescribir todo.

---

## 6. Bloque 5: Códigos de Estado HTTP y Manejo de Errores

### P11: "¿Cómo manejan los códigos HTTP 403, 404 y 500?"
* **Respuesta Técnica:**
  - **HTTP 403 Forbidden:** Implementado en `respuesta_403()`. Si un usuario intenta una acción no autorizada (ej. Batman intentando editar), se retorna una vista con código 403 explicando el motivo.
  - **HTTP 404 Not Found:** Usamos `get_object_or_404(Modelo, pk=pk)`. Si alguien manipula la URL buscando un ID inexistente (ej. `/mantenedores/delegaciones/999999/detalle/`), Django detiene la ejecución limpiamente y retorna una plantilla 404 personalizada en lugar de un error 500.
  - **HTTP 500:** Manejado a nivel de configuración con `DEBUG = False` en producción, mostrando una pantalla amigable sin exponer trazas de código fuente ni credenciales de base de datos.

---

## 7. Bloque 6: Despliegue en AWS EC2 y Producción

### P12: "¿Cómo está desplegado el proyecto en AWS EC2?"
* **Respuesta Técnica:**  
  - **Servidor:** Instancia EC2 Linux en la IP elástica pública `3.229.11.31:8000`.
  - **Base de Datos:** Doble soporte: base de datos local SQLite para testing rápido y desarrollo, y motor **MySQL 8.0** en AWS configurado en `settings.py` mediante variables de entorno.
  - **Archivos Estáticos:** Servidos directamente por la aplicación mediante **WhiteNoise** (`whitenoise.middleware.WhiteNoiseMiddleware`), lo que elimina la necesidad obligatoria de configurar un servidor Nginx separado para CSS/JS estáticos.
  - **Seguridad en Producción:** `SECRET_KEY`, credenciales de base de datos y llaves de cifrado están desacopladas en el archivo `.env` (`python-decouple`). El archivo `.env` está en `.gitignore` para jamás filtrarse en el repositorio Git público.

---

## 8. Bloque 7: Pruebas Automatizadas y Calidad

### P13: "¿Cómo comprobaron que el software cumple con todos los requisitos?"
* **Respuesta Técnica:**  
  Contamos con dos suites automatizadas:
  1. `test_suite.py`: Prueba integral de 42 pasos que recorre el ciclo de vida completo: login, las 17 entidades CRUD, bloqueo 403 de Batman, permiso completo de Mujer Maravilla, 404 en IDs inexistentes, exportación Excel, cambio de delegación, restablecimiento de contraseña y tablero Kanban.
  2. `manage.py test organizacion`: 8 pruebas unitarias oficiales con la clase `TestCase` de Django que se ejecutan sobre una base de datos aislada en memoria.
  Ambas suites corren con **100% de éxito y cero fallas**.
