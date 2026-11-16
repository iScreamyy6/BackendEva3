# Informe Técnico: Credenciales de Acceso, Funciones y Matriz de Permisos RBAC
**Sistema de Gestión de Resultados (SGR) — Ilustre Municipalidad de La Serena**  
*Evaluación Técnica Backend — Módulo de Autenticación, Control de Acceso y Gestión de Delegaciones*

---

## 1. Resumen Ejecutivo y Arquitectura de Seguridad

El Sistema de Gestión de Resultados (SGR) implementa un modelo de control de acceso basado en roles (**RBAC - Role-Based Access Control**), complementado con segregación territorial a nivel de delegación municipal. La arquitectura de seguridad garantiza:

1. **Autenticación Unificada:** Todos los usuarios del sistema cuentan con la contraseña estandarizada de pruebas: `admin`.
2. **Homologación de Identidad:** Cada nombre de usuario (`username`) coincide exactamente con el prefijo local de su correo electrónico institucional corporativo (`<username>@laserena.cl`).
3. **Segregación Estricta de Funciones (Evaluación #3):**
   - **Perfil Gestión SGR (`mujermaravilla`):** Permisos completos CRUD (Crear, Leer, Actualizar y Eliminar/Desactivar) sobre las 17 entidades del sistema.
   - **Perfil Consulta SGR (`batman`):** Permisos de solo lectura (Listados y Vistas de Detalle). Cualquier intento de inserción, modificación o borrado es interceptado con código de estado HTTP `403 Forbidden`.
   - **Superusuario / Administrador (`admin`):** Control total, auditoría, configuración de parámetros y gestión de usuarios.
   - **Coordinador y Delegados (`doctorstrange`, `heman`):** Monitoreo comunal y liderazgo operativo de delegación.
   - **Operadores y Gestores Territoriales/Sociales:** Atención en terreno, levantamiento social y vinculación vecinal.

---

## 2. Tabla Maestra de Credenciales de Acceso

| # | Username | Correo Institucional | Contraseña | Nombre Funcionario / Alias | Rol SGR | Grupo Django | Alcance Territorial |
|---|:---|:---|:---:|:---|:---|:---|:---|
| 1 | **`admin`** | `admin@laserena.cl` | `admin` | Administrador Municipal SGR | ROL-ADM (Admin General) | Administrador | Comunal (Todas) |
| 2 | **`doctorstrange`** | `doctorstrange@laserena.cl` | `admin` | Doctor Strange (Coordinador) | ROL-COORD (Coordinador) | Supervisor | Comunal (Todas) |
| 3 | **`mujermaravilla`** | `mujermaravilla@laserena.cl` | `admin` | Mujer Maravilla (Gestión SGR) | ROL-GEST (Perfil Gestión) | Gestión | Comunal (Todas) |
| 4 | **`batman`** | `batman@laserena.cl` | `admin` | Batman (Consulta SGR) | ROL-CON (Perfil Consulta) | Consulta | Comunal (Todas) |
| 5 | **`heman`** | `heman@laserena.cl` | `admin` | He-Man Delegado | ROL-DEL (Delegado Municipal) | Supervisor | Las Compañías (D01) |
| 6 | **`acuaman`** | `acuaman@laserena.cl` | `admin` | Acuaman Territorial | ROL-TER (Gestor Territorial) | Administrativo | La Antena (D02) |
| 7 | **`flash`** | `flash@laserena.cl` | `admin` | Flash Social | ROL-GES (Gestor Social) | Administrativo | Las Compañías (D01) |
| 8 | **`panteranegra`** | `panteranegra@laserena.cl` | `admin` | Pantera Negra | ROL-OPE (Operador / Control) | Administrativo | Centro Histórico (D03) |
| 9 | **`capitanamarvel`** | `capitanamarvel@laserena.cl` | `admin` | Capitana Marvel | ROL-DIS (Coord. DISERCO) | Administrativo | Delegación Rural (D04) |
| 10 | **`hulk`** | `hulk@laserena.cl` | `admin` | Hulk Social | ROL-GES (Gestor Social) | Administrativo | Centro Histórico (D03) |
| 11 | **`capitanamerica`** | `capitanamerica@laserena.cl` | `admin` | Capitán América | ROL-GES (Gestor Social) | Administrativo | La Antena (D02) |
| 12 | **`spiderman`** | `spiderman@laserena.cl` | `admin` | Spider-Man | ROL-TER (Gestor Territorial) | Administrativo | Las Compañías (D01) |
| 13 | **`ironman`** | `ironman@laserena.cl` | `admin` | Iron Man (Inactivo) | ROL-OPE (Operador Inactivo) | Consulta | Las Compañías (D01) |

---

## 3. Fichas Detalladas por Usuario: Función y Permisos

### 3.1 Cuentas de Control y Administración Transversal

#### 🛡️ 1. Administrador General (`admin`)
* **Credenciales:** `admin` / `admin` (`admin@laserena.cl`)
* **Cargo:** Profesional de Planificación y Control (`CRG-04`)
* **Rol SGR:** `[ROL-ADM] Administrador General`
* **Grupo Django:** `Administrador` (Superuser & Staff: Sí)
* **Alcance:** Comunal (Habilitado en las 4 Delegaciones Municipales)
* **Función:**
  - Administración global del software, base de datos y parámetros institucionales.
  - Gestión de cuentas de usuarios, asignación de roles, delegaciones y cargos.
  - Auditoría de logs, configuración de períodos trimestrales y metas anuales.
* **Permisos Específicos:**
  - **Listar / Detalle:** Acceso total e irrestricto a las 17 entidades.
  - **Crear / Editar:** Todas las entidades (organizacionales, metas, atenciones, evidencias).
  - **Eliminar / Desactivar:** Habilitado para eliminación física o lógica según modelo.
  - **Módulo Django Admin:** Acceso directo a `/admin/`.

---

#### 🔮 2. Coordinador Municipal (`doctorstrange`)
* **Credenciales:** `doctorstrange` / `admin` (`doctorstrange@laserena.cl`)
* **Cargo:** Profesional de Planificación y Control (`CRG-04`)
* **Rol SGR:** `[ROL-COORD] Coordinador Municipal`
* **Grupo Django:** `Supervisor`
* **Alcance:** Comunal (Supervisión transversal de todas las delegaciones)
* **Función:**
  - Supervisión del cumplimiento de compromisos y monitoreo del Tablero Kanban (Tubo de Trabajo).
  - Análisis de reportes semafóricos de gestión (verde, amarillo, rojo).
  - Coordinación entre delegaciones territoriales y la Administración Municipal.
* **Permisos Específicos:**
  - **Listar / Detalle:** Lectura completa sobre todas las entidades y delegaciones.
  - **Gestión:** Aprobación de reportes, visualización de indicadores comunales y exportación de datos.
  - **Escritura:** Registro de compromisos de nivel comunal y reasignación de áreas de apoyo.

---

### 3.2 Cuentas Clave de Evaluación #3 (Gestión vs Consulta)

#### ⚔️ 3. Perfil Oficial de Gestión SGR (`mujermaravilla`)
* **Credenciales:** `mujermaravilla` / `admin` (`mujermaravilla@laserena.cl`)
* **Cargo:** Profesional de Planificación y Control (`CRG-04`)
* **Rol SGR:** `[ROL-GEST] Perfil Gestión SGR`
* **Grupo Django:** `Gestión`
* **Alcance:** Comunal (Autorizada en todas las delegaciones)
* **Función:**
  - Ejecución operativa completa de las 17 entidades del SGR.
  - Verificación del correcto funcionamiento de formularios (`ModelForms`), validaciones y persistencia.
* **Permisos Específicos:**
  - **Listar:** Habilitado en las 17 entidades (`/mantenedores/.../`).
  - **Ver Detalle:** Habilitado en las 17 entidades.
  - **Crear:** Permiso total para registrar nuevas delegaciones, metas, hitos, vecinos, atenciones, evidencias, etc.
  - **Editar:** Modificación de registros existentes con validación de reglas de negocio.
  - **Eliminar / Desactivar:** Confirmación de borrado físico o desactivación lógica (seguridad referencial).
  - **HTTP Status:** Retorna `200 OK` / `302 Redirect` en todas las operaciones CRUD.

---

#### 🦇 4. Perfil Oficial de Consulta SGR (`batman`)
* **Credenciales:** `batman` / `admin` (`batman@laserena.cl`)
* **Cargo:** Profesional de Planificación y Control (`CRG-04`)
* **Rol SGR:** `[ROL-CON] Perfil Consulta SGR`
* **Grupo Django:** `Consulta`
* **Alcance:** Comunal (Lectura transversal)
* **Función:**
  - Auditoría externa, consulta ciudadana e inspección de gestión sin riesgo de alteración de datos.
* **Permisos Específicos:**
  - **Listar:** Habilitado en las 17 entidades (Acceso concedido `200 OK`).
  - **Ver Detalle:** Habilitado en las 17 entidades (Acceso concedido `200 OK`).
  - **Crear:** **DENEGADO**. Interceptado por decoradores de seguridad con **`HTTP 403 Forbidden`**.
  - **Editar:** **DENEGADO**. Interceptado con **`HTTP 403 Forbidden`**.
  - **Eliminar / Desactivar:** **DENEGADO**. Interceptado con **`HTTP 403 Forbidden`**.

---

### 3.3 Cuentas Territoriales y Operativas por Delegación

#### 🗡️ 5. He-Man Delegado (`heman`)
* **Credenciales:** `heman` / `admin` (`heman@laserena.cl`)
* **Cargo:** Delegado Municipal (`CRG-01`)
* **Rol SGR:** `[ROL-DEL] Delegado Municipal`
* **Grupo Django:** `Supervisor`
* **Alcance:** Delegación Municipal Las Compañías (`D01`)
* **Función:** Jefatura territorial en Las Compañías. Priorización de intervenciones y supervisión de cuadrillas y gestores de su delegación.
* **Permisos:** Gestión completa local dentro de su delegación, aprobación de actividades y seguimiento de metas territoriales.

---

#### 🔱 6. Acuaman Territorial (`acuaman`)
* **Credenciales:** `acuaman` / `admin` (`acuaman@laserena.cl`)
* **Cargo:** Territorial Organizaciones Comunitarias (`CRG-02`)
* **Rol SGR:** `[ROL-TER] Gestor Territorial OO.CC.`
* **Grupo Django:** `Administrativo`
* **Alcance:** Delegación Municipal La Antena (`D02`)
* **Función:** Enlace con Juntas de Vecinos, asambleas ciudadanas y levantamiento de requerimientos de infraestructura en La Antena.
* **Permisos:** Creación y seguimiento de hitos territoriales, vinculación de vecinos a juntas vecinales y solicitudes vecinales.

---

#### ⚡ 7. Flash Social (`flash`)
* **Credenciales:** `flash` / `admin` (`flash@laserena.cl`)
* **Cargo:** Gestor Social (`CRG-03`)
* **Rol SGR:** `[ROL-GES] Gestor Social`
* **Grupo Django:** `Administrativo`
* **Alcance:** Delegación Municipal Las Compañías (`D01`)
* **Función:** Aplicación de Ficha Básica de Emergencia (FIBE), visitas domiciliarias e informes sociales de urgencia.
* **Permisos:** Creación y actualización de Gestiones Sociales Especializadas, registro de vecinos vulnerables y emisión de folios.

---

#### 🐾 8. Pantera Negra (`panteranegra`)
* **Credenciales:** `panteranegra` / `admin` (`panteranegra@laserena.cl`)
* **Cargo:** Profesional de Planificación y Control (`CRG-04`)
* **Rol SGR:** `[ROL-OPE] Funcionario Operador`
* **Grupo Django:** `Administrativo`
* **Alcance:** Delegación Municipal Centro y Casco Histórico (`D03`)
* **Función:** Control de atenciones ciudadanas, fiscalización y registro de actividades operativas en el centro de La Serena.
* **Permisos:** Registro de atenciones presenciales/telefónicas y actualización de avances de metas en delegación D03.

---

#### 💫 9. Capitana Marvel (`capitanamarvel`)
* **Credenciales:** `capitanamarvel` / `admin` (`capitanamarvel@laserena.cl`)
* **Cargo:** Coordinador DISERCO (`CRG-05`)
* **Rol SGR:** `[ROL-DIS] Coordinador DISERCO`
* **Grupo Django:** `Administrativo`
* **Alcance:** Delegación Municipal Rural (`D04`)
* **Función:** Operativos rurales de camiones aljibe, retiro de escombros, tolvas comunitarias y conectividad en el Valle Elqui.
* **Permisos:** Registro de operativos territoriales, coordinación de maquinaria y vinculación de solicitudes rurales al Tubo.

---

#### 🟢 10. Hulk Social (`hulk`)
* **Credenciales:** `hulk` / `admin` (`hulk@laserena.cl`)
* **Cargo:** Gestor Social (`CRG-03`)
* **Rol SGR:** `[ROL-GES] Gestor Social`
* **Grupo Django:** `Administrativo`
* **Alcance:** Delegación Municipal Centro y Casco Histórico (`D03`)
* **Función:** Diagnóstico social y ayudas paliativas a vecinos y adultos mayores del sector centro.
* **Permisos:** Ingreso de casos sociales, fichas de evaluación y registro de ayudas directas.

---

#### 🛡️ 11. Capitán América (`capitanamerica`)
* **Credenciales:** `capitanamerica` / `admin` (`capitanamerica@laserena.cl`)
* **Cargo:** Gestor Social (`CRG-03`)
* **Rol SGR:** `[ROL-GES] Gestor Social`
* **Grupo Django:** `Administrativo`
* **Alcance:** Delegación Municipal La Antena (`D02`)
* **Función:** Atención de casos prioritarios y coordinación de subsidios en el territorio de La Antena y Florida.
* **Permisos:** Gestión de beneficios asistenciales, derivación a redes municipales e informes sociales.

---

#### 🕷️ 12. Spider-Man (`spiderman`)
* **Credenciales:** `spiderman` / `admin` (`spiderman@laserena.cl`)
* **Cargo:** Territorial Organizaciones Comunitarias (`CRG-02`)
* **Rol SGR:** `[ROL-TER] Gestor Territorial OO.CC.`
* **Grupo Django:** `Administrativo`
* **Alcance:** Delegación Municipal Las Compañías (`D01`)
* **Función:** Trabajo en terreno, rondas participativas con dirigentes vecinales y verificación barrial en Las Compañías Baja.
* **Permisos:** Creación de compromisos territoriales, inscripción de directivas vecinales y seguimiento de juntas.

---

#### 🤖 13. Iron Man — Cuenta Inactiva de Prueba (`ironman`)
* **Credenciales:** `ironman` / `admin` (`ironman@laserena.cl`)
* **Cargo:** Gestor Social (`CRG-03`)
* **Rol SGR:** `[ROL-OPE] Funcionario Operador`
* **Grupo Django:** `Consulta`
* **Estado:** **Inactivo (`is_active = False`)**
* **Alcance:** Delegación Las Compañías (`D01`)
* **Función:** Cuenta reservada para verificación de reglas de seguridad e inactividad.
* **Comportamiento:** Si intenta iniciar sesión, el sistema rechaza la autenticación notificando que la cuenta se encuentra suspendida/inactiva.

---

## 4. Matriz Comparativa de Permisos sobre las 17 Entidades SGR

| # | Entidad del Sistema | Admin (`admin`) | Gestión (`mujermaravilla`) | Consulta (`batman`) | Delegados (`heman`) | Operadores/Gestores |
|---|:---|:---:|:---:|:---:|:---:|:---:|
| 1 | **Delegación Municipal** | CRUD Total | CRUD Total | Solo Lectura | Solo Lectura | Solo Lectura |
| 2 | **Territorio** | CRUD Total | CRUD Total | Solo Lectura | CRUD (Local) | Solo Lectura |
| 3 | **Usuario Funcionario** | CRUD Total | CRUD Total | Solo Lectura | Consulta Local | Consulta Propia |
| 4 | **Cargo** | CRUD Total | CRUD Total | Solo Lectura | Solo Lectura | Solo Lectura |
| 5 | **Rol** | CRUD Total | CRUD Total | Solo Lectura | Solo Lectura | Solo Lectura |
| 6 | **Vecino** | CRUD Total | CRUD Total | Solo Lectura | CRUD (Local) | CRUD (Local) |
| 7 | **Junta de Vecinos** | CRUD Total | CRUD Total | Solo Lectura | CRUD (Local) | Consulta Local |
| 8 | **Participación en Junta** | CRUD Total | CRUD Total | Solo Lectura | CRUD (Local) | CRUD (Local) |
| 9 | **Hito Territorial** | CRUD Total | CRUD Total | Solo Lectura | CRUD (Local) | CRUD (Local) |
| 10 | **Actividad / Atención** | CRUD Total | CRUD Total | Solo Lectura | CRUD (Local) | CRUD (Local) |
| 11 | **Gestión Social** | CRUD Total | CRUD Total | Solo Lectura | CRUD (Local) | CRUD (Social) |
| 12 | **Tipo de Atención** | CRUD Total | CRUD Total | Solo Lectura | Solo Lectura | Solo Lectura |
| 13 | **Subtipo de Atención** | CRUD Total | CRUD Total | Solo Lectura | Solo Lectura | Solo Lectura |
| 14 | **Meta (ItemMeta)** | CRUD Total | CRUD Total | Solo Lectura | Solo Lectura | Solo Lectura |
| 15 | **Asignación de Meta** | CRUD Total | CRUD Total | Solo Lectura | CRUD (Local) | Consulta Propia |
| 16 | **Evidencia** | CRUD Total | CRUD Total | Solo Lectura | Validar / Ver | Registrar / Ver |
| 17 | **Trimestre (Periodo)** | CRUD Total | CRUD Total | Solo Lectura | Solo Lectura | Solo Lectura |

*Leyenda:*
* **CRUD Total:** Crear, Listar, Ver Detalle, Editar y Eliminar/Desactivar sin restricción territorial.
* **CRUD (Local):** Acceso completo condicionado a los registros de su respectiva delegación municipal.
* **Solo Lectura:** Puede ver listados y fichas de detalle. Si intenta acceder a `/crear/`, `/editar/` o `/eliminar/`, recibe **`HTTP 403 Forbidden`**.

---

## 5. Instrucciones de Validación Rápida

1. **Inicio de Sesión en el Navegador:**
   - Ingrese a `http://localhost:8000/login/` (o en AWS EC2 a `http://3.229.11.31:8000/login/`).
   - Use cualquiera de los `username` indicados con la contraseña `admin`.

2. **Prueba de Escritura (Perfil Gestión):**
   - Iniciar con `mujermaravilla` / `admin`.
   - Dirigirse a `/mantenedores/` y entrar a cualquier entidad (ej. *Vecinos* o *Hitos*).
   - Crear o modificar un registro: La operación se ejecutará con éxito (`HTTP 302 / 200`).

3. **Prueba de Bloqueo 403 (Perfil Consulta):**
   - Iniciar con `batman` / `admin`.
   - Listar los registros de cualquier entidad: Permite visualización completa (`HTTP 200`).
   - Intentar ingresar a la URL de creación (ej. `/mantenedores/vecinos/crear/`): El sistema denegará el acceso arrojando una pantalla oficial de **`HTTP 403 Prohibido`**.
