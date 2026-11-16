-- ==============================================================================
-- PROYECTO: Sistema de Gestión de Resultados (SGR) — Ilustre Municipalidad de La Serena
-- ARTEFACTO: Script DDL/DML para MySQL 8.x (Modelo Relacional de las 17 Entidades SGR)
-- EVALUACIÓN: Tercera Evaluación (Eva 3) — BackEnd CRUD, Validaciones y Seguridad RBAC
-- MOTOR: InnoDB | CHARSET: utf8mb4 | COLLATION: utf8mb4_unicode_ci
-- ==============================================================================

DROP DATABASE IF EXISTS sgr_municipalidad;
CREATE DATABASE sgr_municipalidad
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE sgr_municipalidad;

SET FOREIGN_KEY_CHECKS = 0;

-- ==============================================================================
-- 1. BLOQUE ORGANIZACIONAL Y TERRITORIAL (ENTIDADES #1 A #9)
-- ==============================================================================

-- ENTIDAD #1: Delegación Municipal
DROP TABLE IF EXISTS delegaciones;
CREATE TABLE delegaciones (
    id_delegacion INT AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE COMMENT 'Código institucional (D01, D02, D03, D04)',
    nombre VARCHAR(200) NOT NULL UNIQUE,
    direccion VARCHAR(250) NULL,
    comuna VARCHAR(100) NOT NULL DEFAULT 'La Serena',
    ambito VARCHAR(150) NOT NULL,
    responsable VARCHAR(200) NOT NULL,
    foco_estrategico TEXT NULL,
    estado ENUM('Activa', 'Inactiva') NOT NULL DEFAULT 'Activa',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_delegacion)
) ENGINE=InnoDB COMMENT='Entidad #1: Delegaciones Municipales';

-- ENTIDAD #2: Territorio
DROP TABLE IF EXISTS territorios;
CREATE TABLE territorios (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE COMMENT 'Código único territorial (TER-01)',
    nombre VARCHAR(150) NOT NULL,
    sector VARCHAR(150) NULL,
    delegacion_id INT NOT NULL,
    descripcion TEXT NULL,
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo',
    PRIMARY KEY (id),
    CONSTRAINT fk_territorio_delegacion FOREIGN KEY (delegacion_id)
        REFERENCES delegaciones (id_delegacion) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='Entidad #2: Territorios adscritos a una Delegación';

-- ENTIDAD #4: Cargo
DROP TABLE IF EXISTS cargos;
CREATE TABLE cargos (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE COMMENT 'Código único del cargo (CRG-01)',
    nombre VARCHAR(150) NOT NULL UNIQUE,
    descripcion TEXT NULL,
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB COMMENT='Entidad #4: Catálogo de Cargos Municipales';

-- ENTIDAD #5: Rol
DROP TABLE IF EXISTS roles;
CREATE TABLE roles (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE COMMENT 'Código único de rol (ROL-ADM, ROL-GEST, ROL-CON...)',
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT NULL,
    alcance_autorizado VARCHAR(50) NOT NULL DEFAULT 'Su Delegación',
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB COMMENT='Entidad #5: Roles del Sistema y Nivel de Acceso';

-- ENTIDAD #3: Usuario Funcionario (funcionarios + perfiles_usuario)
DROP TABLE IF EXISTS funcionarios;
CREATE TABLE funcionarios (
    id_funcionario INT AUTO_INCREMENT,
    id_delegacion INT NOT NULL,
    id_cargo INT NULL,
    rut VARCHAR(15) NULL,
    nombres VARCHAR(120) NULL,
    apellidos VARCHAR(120) NULL,
    nombre VARCHAR(200) NOT NULL,
    correo VARCHAR(150) NULL,
    telefono VARCHAR(30) NULL,
    cargo VARCHAR(150) NOT NULL,
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo',
    activo TINYINT(1) NOT NULL DEFAULT 1,
    fecha_ingreso DATE NULL,
    PRIMARY KEY (id_funcionario),
    CONSTRAINT fk_funcionarios_delegacion FOREIGN KEY (id_delegacion)
        REFERENCES delegaciones (id_delegacion) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_funcionarios_cargo FOREIGN KEY (id_cargo)
        REFERENCES cargos (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='Entidad #3: Usuario Funcionario Municipal';

DROP TABLE IF EXISTS perfiles_usuario;
CREATE TABLE perfiles_usuario (
    id INT AUTO_INCREMENT,
    rut VARCHAR(15) NULL,
    nombres VARCHAR(120) NULL,
    apellidos VARCHAR(120) NULL,
    correo VARCHAR(150) NULL,
    telefono VARCHAR(30) NULL,
    rol_id INT NULL,
    cargo_id INT NULL,
    delegacion_principal_id INT NULL,
    territorio_principal_id INT NULL,
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo',
    PRIMARY KEY (id),
    CONSTRAINT fk_perfil_rol FOREIGN KEY (rol_id) REFERENCES roles (id) ON DELETE SET NULL,
    CONSTRAINT fk_perfil_cargo FOREIGN KEY (cargo_id) REFERENCES cargos (id) ON DELETE SET NULL,
    CONSTRAINT fk_perfil_delegacion FOREIGN KEY (delegacion_principal_id) REFERENCES delegaciones (id_delegacion) ON DELETE SET NULL,
    CONSTRAINT fk_perfil_territorio FOREIGN KEY (territorio_principal_id) REFERENCES territorios (id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Entidad #3 (Extensión RBAC): Perfil de Usuario Funcionario';

-- ENTIDAD #6: Vecino
DROP TABLE IF EXISTS vecinos;
CREATE TABLE vecinos (
    id INT AUTO_INCREMENT,
    rut VARCHAR(15) NOT NULL UNIQUE,
    nombres VARCHAR(120) NULL,
    apellidos VARCHAR(120) NULL,
    nombre VARCHAR(200) NOT NULL,
    telefono VARCHAR(30) NULL,
    correo VARCHAR(120) NULL,
    direccion VARCHAR(250) NULL,
    sector VARCHAR(150) NULL,
    territorio_id INT NULL,
    delegacion_id INT NULL,
    observaciones TEXT NULL,
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_vecino_territorio FOREIGN KEY (territorio_id) REFERENCES territorios (id) ON DELETE SET NULL,
    CONSTRAINT fk_vecino_delegacion FOREIGN KEY (delegacion_id) REFERENCES delegaciones (id_delegacion) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Entidad #6: Padrón de Vecinos y Ciudadanos';

-- ENTIDAD #7: Junta de Vecinos
DROP TABLE IF EXISTS juntas_vecinos;
CREATE TABLE juntas_vecinos (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE COMMENT 'Código único (JJVV-01)',
    nombre VARCHAR(200) NOT NULL,
    personalidad_juridica VARCHAR(60) NULL,
    direccion_sede VARCHAR(250) NULL,
    telefono_contacto VARCHAR(30) NULL,
    correo_contacto VARCHAR(120) NULL,
    territorio_id INT NOT NULL,
    delegacion_id INT NULL,
    estado ENUM('Activa', 'Inactiva') NOT NULL DEFAULT 'Activa',
    PRIMARY KEY (id),
    CONSTRAINT fk_jjvv_territorio FOREIGN KEY (territorio_id) REFERENCES territorios (id) ON DELETE RESTRICT,
    CONSTRAINT fk_jjvv_delegacion FOREIGN KEY (delegacion_id) REFERENCES delegaciones (id_delegacion) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Entidad #7: Juntas de Vecinos y Organizaciones Comunitarias';

-- ENTIDAD #8: Participación en Junta
DROP TABLE IF EXISTS participaciones_junta;
CREATE TABLE participaciones_junta (
    id INT AUTO_INCREMENT,
    junta_id INT NOT NULL,
    vecino_id INT NOT NULL,
    cargo VARCHAR(30) NOT NULL DEFAULT 'Socio',
    fecha_inicio DATE NULL,
    fecha_termino DATE NULL,
    observacion VARCHAR(250) NULL,
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo',
    activo TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT fk_part_junta FOREIGN KEY (junta_id) REFERENCES juntas_vecinos (id) ON DELETE CASCADE,
    CONSTRAINT fk_part_vecino FOREIGN KEY (vecino_id) REFERENCES vecinos (id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Entidad #8: Participación y Directiva en Junta de Vecinos';

-- ENTIDAD #9: Hito Territorial
DROP TABLE IF EXISTS hitos;
CREATE TABLE hitos (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE COMMENT 'Código único del hito (HIT-01)',
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT NULL,
    periodicidad VARCHAR(40) NOT NULL DEFAULT 'Trimestral',
    fecha_inicio DATE NOT NULL,
    fecha_termino DATE NOT NULL,
    delegacion_id INT NOT NULL,
    territorio_id INT NULL,
    responsable_id INT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'Programado',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_hito_delegacion FOREIGN KEY (delegacion_id) REFERENCES delegaciones (id_delegacion) ON DELETE RESTRICT,
    CONSTRAINT fk_hito_territorio FOREIGN KEY (territorio_id) REFERENCES territorios (id) ON DELETE SET NULL,
    CONSTRAINT fk_hito_responsable FOREIGN KEY (responsable_id) REFERENCES funcionarios (id_funcionario) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Entidad #9: Hitos Territoriales y Operativos Estratégicos';

-- ==============================================================================
-- 2. BLOQUE TIPOLOGÍAS, GESTIÓN Y EVIDENCIAS (ENTIDADES #10 A #16)
-- ==============================================================================

-- ENTIDAD #12: Tipo de Atención
DROP TABLE IF EXISTS tipos_atencion;
CREATE TABLE tipos_atencion (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE COMMENT 'Código único (TIP-SOC, TIP-TER...)',
    nombre VARCHAR(150) NOT NULL UNIQUE,
    descripcion TEXT NULL,
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB COMMENT='Entidad #12: Tipos de Atención Municipal';

-- ENTIDAD #13: Subtipo de Atención
DROP TABLE IF EXISTS sub_atenciones;
CREATE TABLE sub_atenciones (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE COMMENT 'Código único (SUB-SOC-01...)',
    tipo_id INT NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT NULL,
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_subatencion_tipo FOREIGN KEY (tipo_id) REFERENCES tipos_atencion (id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Entidad #13: Subtipos de Atención dependientes de Tipo de Atención';

-- ENTIDAD #14: Meta (Catálogo ItemMeta)
DROP TABLE IF EXISTS items_metas;
CREATE TABLE items_metas (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE COMMENT 'Código único de meta (ITM-01)',
    nombre VARCHAR(200) NOT NULL UNIQUE,
    descripcion TEXT NULL,
    unidad_medida VARCHAR(60) NOT NULL DEFAULT 'Gestiones',
    cargo_asociado VARCHAR(150) NULL,
    id_cargo INT NULL,
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_item_cargo FOREIGN KEY (id_cargo) REFERENCES cargos (id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Entidad #14: Catálogo de Metas Institucionales';

-- ENTIDAD #17: Trimestre (Período de Evaluación)
DROP TABLE IF EXISTS periodos_evaluacion;
CREATE TABLE periodos_evaluacion (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE COMMENT 'Código único trimestral (TRI-2026-03)',
    anio INT NOT NULL DEFAULT 2026,
    numero INT NOT NULL DEFAULT 3 COMMENT 'Trimestre 1 a 4',
    nombre VARCHAR(100) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_cierre DATE NOT NULL,
    dias_totales INT NOT NULL DEFAULT 90,
    dias_transcurridos INT NOT NULL DEFAULT 89,
    estado ENUM('Activo', 'Cerrado', 'Planificado', 'Inactivo') NOT NULL DEFAULT 'Activo',
    activo TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (id)
) ENGINE=InnoDB COMMENT='Entidad #17: Trimestres de Evaluación Institucional';

-- ENTIDAD #15: Asignación de Meta a Funcionario
DROP TABLE IF EXISTS metas_funcionario;
CREATE TABLE metas_funcionario (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(30) NULL UNIQUE COMMENT 'Código de asignación (ASG-0001)',
    id_funcionario INT NOT NULL,
    id_periodo INT NOT NULL,
    id_item_meta INT NULL,
    item VARCHAR(200) NOT NULL,
    ponderador DECIMAL(5,2) NOT NULL COMMENT 'Ponderación 0 a 100%',
    meta_periodo INT NOT NULL COMMENT 'Cantidad objetivo > 0',
    avance_actual INT NOT NULL DEFAULT 0,
    porcentaje_cumplimiento DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    cumplimiento_ponderado DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    felicitaciones INT NOT NULL DEFAULT 0,
    reclamos INT NOT NULL DEFAULT 0,
    fecha_asignacion DATE NULL,
    observacion TEXT NULL,
    estado ENUM('Activa', 'Cumplida', 'Inactiva') NOT NULL DEFAULT 'Activa',
    PRIMARY KEY (id),
    CONSTRAINT fk_asg_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionarios (id_funcionario) ON DELETE CASCADE,
    CONSTRAINT fk_asg_periodo FOREIGN KEY (id_periodo) REFERENCES periodos_evaluacion (id) ON DELETE CASCADE,
    CONSTRAINT fk_asg_item FOREIGN KEY (id_item_meta) REFERENCES items_metas (id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Entidad #15: Asignaciones de Metas por Funcionario y Trimestre';

-- ENTIDAD #10: Actividad
DROP TABLE IF EXISTS actividades;
CREATE TABLE actividades (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(25) NULL UNIQUE COMMENT 'Folio correlativo (GES-00001)',
    nombre VARCHAR(200) NULL,
    id_funcionario INT NOT NULL,
    id_delegacion INT NULL,
    id_territorio INT NULL,
    id_hito INT NULL,
    id_vecino INT NULL,
    id_junta_vecinos INT NULL,
    id_tipo_atencion INT NULL,
    id_sub_atencion INT NULL,
    id_item_meta INT NULL,
    fecha DATE NOT NULL,
    fecha_termino DATE NULL,
    lugar VARCHAR(200) NULL,
    solicitud TEXT NOT NULL,
    accion VARCHAR(300) NOT NULL,
    observacion TEXT NULL,
    responsable VARCHAR(200) NOT NULL,
    item_evaluacion VARCHAR(200) NOT NULL,
    estado ENUM('Pendiente', 'En Proceso', 'Realizado', 'Inactivo') NOT NULL DEFAULT 'Pendiente',
    contacto VARCHAR(200) NULL,
    telefono VARCHAR(30) NULL,
    ingreso_tubo TINYINT(1) NOT NULL DEFAULT 0,
    codigo_evidencia VARCHAR(50) NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_act_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionarios (id_funcionario) ON DELETE CASCADE,
    CONSTRAINT fk_act_delegacion FOREIGN KEY (id_delegacion) REFERENCES delegaciones (id_delegacion) ON DELETE SET NULL,
    CONSTRAINT fk_act_territorio FOREIGN KEY (id_territorio) REFERENCES territorios (id) ON DELETE SET NULL,
    CONSTRAINT fk_act_hito FOREIGN KEY (id_hito) REFERENCES hitos (id) ON DELETE SET NULL,
    CONSTRAINT fk_act_vecino FOREIGN KEY (id_vecino) REFERENCES vecinos (id) ON DELETE SET NULL,
    CONSTRAINT fk_act_junta FOREIGN KEY (id_junta_vecinos) REFERENCES juntas_vecinos (id) ON DELETE SET NULL,
    CONSTRAINT fk_act_tipo FOREIGN KEY (id_tipo_atencion) REFERENCES tipos_atencion (id) ON DELETE SET NULL,
    CONSTRAINT fk_act_sub FOREIGN KEY (id_sub_atencion) REFERENCES sub_atenciones (id) ON DELETE SET NULL,
    CONSTRAINT fk_act_item FOREIGN KEY (id_item_meta) REFERENCES items_metas (id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Entidad #10: Actividades y Gestiones Municipales';

-- ENTIDAD #11: Gestión Social
DROP TABLE IF EXISTS gestiones_sociales;
CREATE TABLE gestiones_sociales (
    id INT AUTO_INCREMENT,
    folio VARCHAR(20) NOT NULL UNIQUE COMMENT 'Folio correlativo (SOC-00001)',
    fecha_ingreso DATE NOT NULL,
    fecha_compromiso DATE NULL,
    fecha_cierre DATE NULL,
    delegacion_id INT NOT NULL,
    territorio_id INT NULL,
    gestor_responsable_id INT NOT NULL,
    vecino_id INT NULL,
    junta_vecinos_id INT NULL,
    tipo_atencion_id INT NULL,
    sub_atencion_id INT NULL,
    actividad_asociada_id INT NULL,
    prioridad VARCHAR(20) NOT NULL DEFAULT 'Media',
    canal_ingreso VARCHAR(30) NOT NULL DEFAULT 'Presencial',
    rut_solicitante VARCHAR(15) NOT NULL,
    nombre_solicitante VARCHAR(200) NOT NULL,
    telefono_solicitante VARCHAR(30) NULL,
    direccion_solicitante VARCHAR(250) NULL,
    grupo_familiar INT NOT NULL DEFAULT 1,
    diagnostico_social TEXT NOT NULL,
    beneficio_solicitado VARCHAR(200) NOT NULL,
    monto_estimado INT NOT NULL DEFAULT 0,
    visita_domiciliaria TINYINT(1) NOT NULL DEFAULT 0,
    fecha_visita DATE NULL,
    informe_social_emitido TINYINT(1) NOT NULL DEFAULT 0,
    folio_informe VARCHAR(50) NULL,
    estado_caso VARCHAR(30) NOT NULL DEFAULT 'Recibido',
    derivar_tubo TINYINT(1) NOT NULL DEFAULT 0,
    observaciones_seguimiento TEXT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_soc_delegacion FOREIGN KEY (delegacion_id) REFERENCES delegaciones (id_delegacion) ON DELETE RESTRICT,
    CONSTRAINT fk_soc_territorio FOREIGN KEY (territorio_id) REFERENCES territorios (id) ON DELETE SET NULL,
    CONSTRAINT fk_soc_gestor FOREIGN KEY (gestor_responsable_id) REFERENCES funcionarios (id_funcionario) ON DELETE RESTRICT,
    CONSTRAINT fk_soc_vecino FOREIGN KEY (vecino_id) REFERENCES vecinos (id) ON DELETE SET NULL,
    CONSTRAINT fk_soc_junta FOREIGN KEY (junta_vecinos_id) REFERENCES juntas_vecinos (id) ON DELETE SET NULL,
    CONSTRAINT fk_soc_tipo FOREIGN KEY (tipo_atencion_id) REFERENCES tipos_atencion (id) ON DELETE SET NULL,
    CONSTRAINT fk_soc_sub FOREIGN KEY (sub_atencion_id) REFERENCES sub_atenciones (id) ON DELETE SET NULL,
    CONSTRAINT fk_soc_actividad FOREIGN KEY (actividad_asociada_id) REFERENCES actividades (id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Entidad #11: Gestiones Sociales Especializadas';

-- ENTIDAD #16: Evidencia
DROP TABLE IF EXISTS evidencias;
CREATE TABLE evidencias (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(50) NOT NULL UNIQUE COMMENT 'Código verificador (EVI-2026-XXXX)',
    titulo VARCHAR(200) NULL,
    descripcion TEXT NULL,
    tipo_archivo VARCHAR(40) NOT NULL DEFAULT 'Fotografía',
    fecha_registro DATE NULL,
    id_actividad INT NULL,
    id_gestion_social INT NULL,
    id_asignacion_meta INT NULL,
    id_verificador INT NULL,
    archivo VARCHAR(255) NOT NULL,
    imagen_verificada TINYINT(1) NOT NULL DEFAULT 0,
    verificador_valido TINYINT(1) NOT NULL DEFAULT 0,
    resultado INT NOT NULL DEFAULT 0,
    estado_validacion ENUM('Pendiente', 'Aprobada', 'Rechazada', 'Corregir', 'Inactiva') NOT NULL DEFAULT 'Pendiente',
    observacion TEXT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_evi_actividad FOREIGN KEY (id_actividad) REFERENCES actividades (id) ON DELETE CASCADE,
    CONSTRAINT fk_evi_social FOREIGN KEY (id_gestion_social) REFERENCES gestiones_sociales (id) ON DELETE SET NULL,
    CONSTRAINT fk_evi_asg FOREIGN KEY (id_asignacion_meta) REFERENCES metas_funcionario (id) ON DELETE SET NULL,
    CONSTRAINT fk_evi_verif FOREIGN KEY (id_verificador) REFERENCES funcionarios (id_funcionario) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Entidad #16: Evidencias Fotográficas y Documentales';

-- TABLAS COMPLEMENTARIAS DE AGENDA (TUBO KANBAN) E INDICADORES SEMÁFORO
DROP TABLE IF EXISTS compromisos_tubo;
CREATE TABLE compromisos_tubo (
    id INT AUTO_INCREMENT,
    codigo VARCHAR(25) NULL UNIQUE,
    id_delegacion INT NOT NULL,
    id_responsable INT NULL,
    fecha_solicitud DATE NOT NULL,
    actividad TEXT NOT NULL,
    tipo ENUM('INT', 'EXT') NOT NULL DEFAULT 'EXT',
    solicitante VARCHAR(200) NOT NULL,
    territorio VARCHAR(200) NULL,
    responsable VARCHAR(200) NOT NULL,
    fecha_compromiso DATE NULL,
    area_apoyo VARCHAR(200) NULL,
    observaciones TEXT NULL,
    estado ENUM('INGRESADO', 'PENDIENTE', 'EN PROCESO', 'REALIZADO') NOT NULL DEFAULT 'INGRESADO',
    unidad INT NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT fk_tubo_delegacion FOREIGN KEY (id_delegacion) REFERENCES delegaciones (id_delegacion) ON DELETE CASCADE,
    CONSTRAINT fk_tubo_responsable FOREIGN KEY (id_responsable) REFERENCES funcionarios (id_funcionario) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Tablero Kanban del Tubo de Trabajo';

DROP TABLE IF EXISTS indicadores_delegacion;
CREATE TABLE indicadores_delegacion (
    id INT AUTO_INCREMENT,
    id_delegacion INT NOT NULL,
    id_periodo INT NOT NULL,
    area VARCHAR(150) NOT NULL,
    responsable VARCHAR(200) NOT NULL,
    avance_porcentaje DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    estado_semaforo ENUM('verde', 'amarillo', 'rojo') NOT NULL DEFAULT 'verde',
    licencias INT NOT NULL DEFAULT 0,
    vacaciones INT NOT NULL DEFAULT 0,
    emergencias INT NOT NULL DEFAULT 0,
    compensatorios INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    CONSTRAINT fk_ind_delegacion FOREIGN KEY (id_delegacion) REFERENCES delegaciones (id_delegacion) ON DELETE CASCADE,
    CONSTRAINT fk_ind_periodo FOREIGN KEY (id_periodo) REFERENCES periodos_evaluacion (id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Consolidado Semáforo SGR por Delegación';

SET FOREIGN_KEY_CHECKS = 1;

-- ==============================================================================
-- 3. POBLADO DE DATOS FICTICIOS (SUPERHÉROES Y 17 ENTIDADES SGR)
-- ==============================================================================

-- 3.1 Entidad #1: Delegaciones
INSERT INTO delegaciones (id_delegacion, codigo, nombre, direccion, comuna, ambito, responsable, foco_estrategico, estado) VALUES
(1, 'D01', 'Delegación Municipal Las Compañías', 'Esmeralda #2422, Las Compañías', 'La Serena', 'Las Compañías Alta y Baja', 'He-Man', 'Atención integral comunitaria, operativos sociales y resolución territorial rápida', 'Activa'),
(2, 'D02', 'Delegación Municipal La Antena', '12 de Octubre #1255, La Antena', 'La Serena', 'Sector La Antena y Florida', 'Acuaman', 'Seguridad vecinal, recuperación de espacios públicos y mediación comunitaria', 'Activa'),
(3, 'D03', 'Delegación Municipal Centro y Casco Histórico', 'Los Carrera #301, Centro', 'La Serena', 'Centro Urbano y Casco Histórico', 'Pantera Negra', 'Fiscalización comercial, turismo patrimonial y aseo urbano', 'Activa'),
(4, 'D04', 'Delegación Municipal Rural', 'Ruta D-41 Km 15, El Arrayán', 'La Serena', 'Valles y Localidades Rurales', 'Capitana Marvel', 'Conectividad hídrica, caminos rurales y apoyo a crianceros', 'Activa'),
(5, 'D05', 'Delegación Municipal Costera (Histórica)', 'Av. del Mar #4500, Sector El Faro', 'La Serena', 'Borde Costero Estacional', 'Coordinación Estival', 'Delegación estacional inactiva', 'Inactiva');

-- 3.2 Entidad #2: Territorios
INSERT INTO territorios (id, codigo, nombre, sector, delegacion_id, descripcion, estado) VALUES
(1, 'TER-01', 'Las Compañías Alta', 'Norte', 1, 'Sector El Olivar, Minas del Brillador y Villa El Indio', 'Activo'),
(2, 'TER-02', 'Las Compañías Baja', 'Norte Poniente', 1, 'Sector Islón, Villa Lambert y Eje Esmeralda Poniente', 'Activo'),
(3, 'TER-03', 'Sector La Antena y Florida', 'Oriente', 2, 'Población Juan XXIII, Coll y Panorámica La Florida', 'Activo'),
(4, 'TER-04', 'Centro Urbano y Casco Histórico', 'Centro', 3, 'Cuadrante Patrimonial, Barrio Almagro y Eje Balmaceda', 'Activo'),
(5, 'TER-05', 'Valle El Romero y El Arrayán', 'Rural', 4, 'Localidades rurales de la ribera norte y sur del Río Elqui', 'Activo'),
(6, 'TER-06', 'Polígono Industrial Norte (Inactivo)', 'Norte', 1, 'Polígono territorial en revisión catastral', 'Inactivo');

-- 3.3 Entidad #4: Cargos
INSERT INTO cargos (id, codigo, nombre, descripcion, estado) VALUES
(1, 'CRG-01', 'Delegado Municipal', 'Jefatura territorial representante del Alcalde en la delegación municipal', 'Activo'),
(2, 'CRG-02', 'Territorial OO.CC.', 'Encargado de vinculación con Juntas de Vecinos y organizaciones comunitarias', 'Activo'),
(3, 'CRG-03', 'Gestor Social', 'Profesional encargado de diagnósticos sociales, visitas domiciliarias y ayudas paliativas', 'Activo'),
(4, 'CRG-04', 'Prof. Planificación y Control', 'Analista de cumplimiento de metas trimestrales, indicadores y control de gestión', 'Activo'),
(5, 'CRG-05', 'Coordinador DISERCO', 'Coordinador operativo de cuadrillas, tolvas, mantención de plazas y alumbrado', 'Activo'),
(6, 'CRG-06', 'Asistente Técnico Histórico', 'Cargo en desuso para pruebas de estado inactivo', 'Inactivo');

-- 3.4 Entidad #5: Roles
INSERT INTO roles (id, codigo, nombre, descripcion, alcance_autorizado, estado) VALUES
(1, 'ROL-ADM', 'Administrador General', 'Acceso total y configuración comunal transversal de las 17 entidades', 'COMUNAL', 'Activo'),
(2, 'ROL-COORD', 'Coordinador Municipal', 'Supervisión transversal y monitoreo de compromisos comunales', 'COMUNAL', 'Activo'),
(3, 'ROL-DEL', 'Delegado Municipal', 'Gestión y jefatura de delegación territorial asignada', 'DELEGACION', 'Activo'),
(4, 'ROL-OPE', 'Funcionario Operador', 'Atención ciudadana, registro de casos y gestiones en terreno', 'DELEGACION', 'Activo'),
(5, 'ROL-VERIF', 'Verificador Técnico', 'Auditoría y validación de evidencias fotográficas y documentales', 'DELEGACION', 'Activo'),
(6, 'ROL-GES', 'Gestor Social', 'Profesional de atención social, visitas domiciliarias e informes FIBE', 'DELEGACION', 'Activo'),
(7, 'ROL-TER', 'Gestor Territorial OO.CC.', 'Coordinación con Juntas de Vecinos, hitos barriales y operativos en terreno', 'DELEGACION', 'Activo'),
(8, 'ROL-DIS', 'Coordinador DISERCO', 'Enlace de servicios a la comunidad y apoyo operativo rural/urbano', 'DELEGACION', 'Activo'),
(9, 'ROL-GEST', 'Perfil Gestión SGR', 'Perfil oficial con permisos completos CRUD en las 17 entidades', 'COMUNAL', 'Activo'),
(10, 'ROL-CON', 'Perfil Consulta SGR', 'Perfil oficial de solo lectura (HTTP 403 en escritura)', 'COMUNAL', 'Activo'),
(11, 'ROL-INA', 'Auditor Externo Histórico (Inactivo)', 'Rol temporal inactivo', 'COMUNAL', 'Inactivo');

-- 3.5 Entidad #3: Usuarios Funcionarios (Superhéroes - Clave en Django: admin)
INSERT INTO funcionarios (id_funcionario, id_delegacion, id_cargo, rut, nombres, apellidos, nombre, correo, telefono, cargo, estado, activo, fecha_ingreso) VALUES
(1, 1, 1, '15.111.111-1', 'He-Man', 'Delegado', 'He-Man', 'heman@laserena.cl', '+56 9 8000 1000', 'Delegado Municipal', 'Activo', 1, '2024-01-01'),
(2, 2, 2, '15.222.222-2', 'Acuaman', 'Territorial', 'Acuaman', 'acuaman@laserena.cl', '+56 9 8000 1000', 'Territorial OO.CC. 1', 'Activo', 1, '2024-03-15'),
(3, 1, 3, '15.333.333-3', 'Flash', 'Social', 'Flash', 'flash@laserena.cl', '+56 9 8000 1000', 'Gestor Social 1', 'Activo', 1, '2024-02-01'),
(4, 3, 4, '15.444.444-4', 'Pantera', 'Negra', 'Pantera Negra', 'panteranegra@laserena.cl', '+56 9 8000 1000', 'Prof. Planificación y Control', 'Activo', 1, '2024-01-10'),
(5, 4, 5, '15.555.555-5', 'Capitana', 'Marvel', 'Capitana Marvel', 'capitanamarvel@laserena.cl', '+56 9 8000 1000', 'Coordinador DISERCO', 'Activo', 1, '2024-04-01'),
(6, 3, 3, '15.666.666-6', 'Hulk', 'Social', 'Hulk', 'hulk@laserena.cl', '+56 9 8000 1000', 'Gestor Social 3', 'Activo', 1, '2024-02-15'),
(7, 2, 3, '15.777.777-7', 'Capitán', 'América', 'Capitán América', 'capitanamerica@laserena.cl', '+56 9 8000 1000', 'Gestor Social 2', 'Activo', 1, '2024-03-01'),
(8, 1, 2, '15.888.888-8', 'Spider', 'Man', 'Spider-Man', 'spiderman@laserena.cl', '+56 9 8000 1000', 'Territorial OO.CC. 2', 'Activo', 1, '2024-05-10'),
(9, 1, 3, '15.999.999-9', 'Iron', 'Man', 'Iron Man (Inactivo)', 'ironman@laserena.cl', '+56 9 8000 1000', 'Gestor Social', 'Inactivo', 0, '2023-06-01');

INSERT INTO perfiles_usuario (id, rut, nombres, apellidos, correo, telefono, rol_id, cargo_id, delegacion_principal_id, territorio_principal_id, estado) VALUES
(1, '11.111.111-1', 'Administrador', 'Municipal SGR', 'admin@laserena.cl', '+56 9 9000 0001', 1, 4, 1, 1, 'Activo'),
(2, '12.222.222-2', 'Doctor Strange', '(Coordinador Comunal)', 'doctorstrange@laserena.cl', '+56 9 8000 1000', 2, 4, 1, 1, 'Activo'),
(3, '13.333.333-3', 'Mujer Maravilla', '(Gestión SGR)', 'mujermaravilla@laserena.cl', '+56 9 8000 1000', 9, 4, 1, 1, 'Activo'),
(4, '14.444.444-4', 'Batman', '(Consulta SGR)', 'batman@laserena.cl', '+56 9 8000 1000', 10, 4, 1, 1, 'Activo'),
(5, '15.111.111-1', 'He-Man', 'Delegado', 'heman@laserena.cl', '+56 9 8000 1000', 3, 1, 1, 1, 'Activo'),
(6, '15.222.222-2', 'Acuaman', 'Territorial', 'acuaman@laserena.cl', '+56 9 8000 1000', 7, 2, 2, 3, 'Activo'),
(7, '15.333.333-3', 'Flash', 'Social', 'flash@laserena.cl', '+56 9 8000 1000', 6, 3, 1, 1, 'Activo'),
(8, '15.444.444-4', 'Pantera', 'Negra', 'panteranegra@laserena.cl', '+56 9 8000 1000', 4, 4, 3, 4, 'Activo'),
(9, '15.555.555-5', 'Capitana', 'Marvel', 'capitanamarvel@laserena.cl', '+56 9 8000 1000', 8, 5, 4, 5, 'Activo'),
(10, '15.666.666-6', 'Hulk', 'Social', 'hulk@laserena.cl', '+56 9 8000 1000', 6, 3, 3, 4, 'Activo'),
(11, '15.777.777-7', 'Capitán', 'América', 'capitanamerica@laserena.cl', '+56 9 8000 1000', 6, 3, 2, 3, 'Activo'),
(12, '15.888.888-8', 'Spider', 'Man', 'spiderman@laserena.cl', '+56 9 8000 1000', 7, 2, 1, 2, 'Activo'),
(13, '15.999.999-9', 'Iron', 'Man (Inactivo)', 'ironman@laserena.cl', '+56 9 8000 1000', 4, 3, 1, 1, 'Inactivo');

-- 3.6 Entidad #6: Vecinos (Superhéroes)
INSERT INTO vecinos (id, rut, nombres, apellidos, nombre, telefono, correo, direccion, sector, territorio_id, delegacion_id, estado) VALUES
(1, '16.100.100-1', 'Diana', 'Prince (Mujer Maravilla)', 'Diana Prince (Mujer Maravilla)', '+56 9 7111 2201', 'mujermaravilla@vecinoslaserena.cl', 'Av. Viña del Mar #1420, Las Compañías', 'Las Compañías Alta', 1, 1, 'Activo'),
(2, '16.200.200-2', 'Clark', 'Kent (Superman)', 'Clark Kent (Superman)', '+56 9 7111 2202', 'superman@vecinoslaserena.cl', 'Calle 18 de Septiembre #880, La Antena', 'La Antena', 3, 2, 'Activo'),
(3, '16.300.300-3', 'Bruce', 'Wayne (Batman)', 'Bruce Wayne (Batman)', '+56 9 7111 2203', 'batman@vecinoslaserena.cl', 'Calle Almagro #412, Casco Histórico', 'Centro', 4, 3, 'Activo'),
(4, '16.400.400-4', 'Thor', 'Odinson (Asgard)', 'Thor Odinson (Asgard)', '+56 9 7111 2204', 'thor@vecinoslaserena.cl', 'Parcela 14 El Romero, Sector Rural', 'El Romero', 5, 4, 'Activo'),
(5, '16.500.500-5', 'Natasha', 'Romanoff (Viuda Negra)', 'Natasha Romanoff (Viuda Negra)', '+56 9 7111 2205', 'viudanegra@vecinoslaserena.cl', 'Pasaje El Brillador #210, Las Compañías', 'Las Compañías Baja', 2, 1, 'Activo'),
(6, '16.600.600-6', 'Hal', 'Jordan (Linterna Verde)', 'Hal Jordan (Linterna Verde)', '+56 9 7111 2206', 'linternaverde@vecinoslaserena.cl', 'Calle Esmeralda #1990, Las Compañías', 'Las Compañías Alta', 1, 1, 'Inactivo');

-- 3.7 Entidad #7: Juntas de Vecinos
INSERT INTO juntas_vecinos (id, codigo, nombre, personalidad_juridica, direccion_sede, territorio_id, delegacion_id, estado) VALUES
(1, 'JJVV-01', 'Junta de Vecinos N° 12 Villa El Indio', 'PJ-1998-012', 'Sede Comunitaria Pasaje Arauco #340, Las Compañías', 1, 1, 'Activa'),
(2, 'JJVV-02', 'Junta de Vecinos N° 8 Juan XXIII La Antena', 'PJ-1995-008', 'Av. 12 de Octubre #1410, La Antena', 3, 2, 'Activa'),
(3, 'JJVV-03', 'Junta de Vecinos N° 1 Casco Histórico', 'PJ-1992-001', 'Calle Rengifo #245, Centro', 4, 3, 'Activa'),
(4, 'JJVV-04', 'Junta de Vecinos N° 25 El Arrayán Rural', 'PJ-2004-025', 'Camino Principal s/n Km 16, El Arrayán', 5, 4, 'Activa'),
(5, 'JJVV-05', 'Junta de Vecinos N° 99 Sector Antiguo (Inactiva)', 'PJ-2001-099', 'Sede Provisoria Sector Norte #102', 2, 1, 'Inactiva');

-- 3.8 Entidad #8: Participaciones en Junta
INSERT INTO participaciones_junta (id, junta_id, vecino_id, cargo, fecha_inicio, estado, activo) VALUES
(1, 1, 1, 'Presidente/a', '2024-03-01', 'Activo', 1),
(2, 2, 2, 'Secretario/a', '2024-04-10', 'Activo', 1),
(3, 3, 3, 'Socio/a Activo/a', '2024-06-15', 'Activo', 1),
(4, 1, 4, 'Tesorero/a', '2023-05-20', 'Inactivo', 0);

-- 3.9 Entidad #9: Hitos Territoriales
INSERT INTO hitos (id, codigo, nombre, descripcion, periodicidad, fecha_inicio, fecha_termino, delegacion_id, territorio_id, responsable_id, estado) VALUES
(1, 'HIT-01', 'Operativo Integral de Invierno Las Compañías', 'Despliegue preventivo de limpieza de sumideros, entrega de nylon y atención FIBE en terreno', 'Anual', '2026-01-15', '2026-02-15', 1, 1, 1, 'Realizado'),
(2, 'HIT-02', 'Mesa Territorial de Seguridad Vecinal La Antena', 'Coordinación trimestral con dirigentes vecinales, Carabineros e Inspección Municipal', 'Trimestral', '2026-02-01', '2026-03-30', 2, 3, 2, 'En Ejecución'),
(3, 'HIT-03', 'Cabildo Patrimonial y Limpieza Centro Histórico', 'Jornada participativa de recuperación de fachadas y fiscalización de comercio ambulante', 'Semestral', '2026-03-01', '2026-03-25', 3, 4, 4, 'Programado'),
(4, 'HIT-04', 'Feria Comunitaria Sector Norte (Inactivo)', 'Hito reprogramado sin actividades vinculadas', 'Único', '2026-01-10', '2026-01-12', 1, 2, 8, 'Inactivo');

-- 3.10 Entidad #12 y #13: Tipos y Subtipos de Atención
INSERT INTO tipos_atencion (id, codigo, nombre, descripcion, estado) VALUES
(1, 'TIP-SOC', 'Atención Social y Beneficios', 'Asistencia económica, subsidios familiares y ayudas técnicas inmediatas', 'Activo'),
(2, 'TIP-TERR', 'Gestión Territorial y Obras', 'Requerimientos de luminarias, bacheo, aseo y plazas vecinales', 'Activo'),
(3, 'TIP-SEG', 'Seguridad Ciudadana e Inspección', 'Denuncias vecinales, patrullaje preventivo y mediación comunitaria', 'Activo'),
(4, 'TIP-INA', 'Zonificación Piloto Histórica (Inactiva)', 'Tipología en desuso sin subatenciones asociadas', 'Inactivo');

INSERT INTO sub_atenciones (id, codigo, tipo_id, nombre, estado) VALUES
(1, 'SUB-ORI', 1, 'Orientación Social y Registro Social de Hogares', 'Activo'),
(2, 'SUB-FIBE', 1, 'Aplicación de Ficha FIBE', 'Activo'),
(3, 'SUB-SUBS', 1, 'Postulación a Subsidios de Agua y Vivienda', 'Activo'),
(4, 'SUB-ALIM', 1, 'Entrega de Cajas de Alimentos y Albergue', 'Activo'),
(5, 'SUB-INA', 1, 'Subatención Piloto Suspendida (Inactiva)', 'Inactivo'),
(6, 'SUB-LUM', 2, 'Reparación de Luminarias y Alumbrado Público', 'Activo'),
(7, 'SUB-ASEO', 2, 'Operativo de Tolvas y Retiro de Escombros', 'Activo'),
(8, 'SUB-PLAZ', 2, 'Mantención y Riego de Áreas Verdes / Plazas', 'Activo'),
(9, 'SUB-BACH', 2, 'Bacheo y Señalización Vial', 'Activo'),
(10, 'SUB-PATR', 3, 'Solicitud de Patrullaje Preventivo', 'Activo'),
(11, 'SUB-RUID', 3, 'Mediación Vecinal por Ruidos Molestos', 'Activo'),
(12, 'SUB-COME', 3, 'Fiscalización de Comercio Informal', 'Activo');

-- 3.11 Entidad #14: Metas (ItemMeta)
INSERT INTO items_metas (id, codigo, nombre, descripcion, unidad_medida, estado) VALUES
(1, 'I01', 'Atención de Usuario Presencial y Telefónica', 'Recepción, registro y orientación personalizada de vecinos en delegación', 'Atenciones registradas', 'Activo'),
(2, 'I02', 'Informes Sociales y Ficha FIBE', 'Levantamiento de peritajes sociales y aplicación de ficha básica de emergencia', 'Informes emitidos', 'Activo'),
(3, 'I03', 'Gestión Territorial y Operativos en Terreno', 'Visitas a juntas de vecinos, supervisión de microbasurales y espacios públicos', 'Operativos ejecutados', 'Activo'),
(4, 'I04', 'Emergencias Comunales y Contingencias', 'Respuesta rápida ante emergencias climáticas, cortes de servicios o siniestros', 'Contingencias atendidas', 'Activo'),
(5, 'I05', 'Capacitación y Participación Ciudadana', 'Talleres comunitarios, mesas de trabajo barriales y difusión municipal', 'Jornadas participativas', 'Activo'),
(6, 'I06', 'Meta Histórica de Archivo Físico (Inactiva)', 'Meta descontinuada tras la digitalización del SGR municipal', 'Expedientes archivados', 'Inactivo');

-- 3.12 Entidad #17: Trimestres (PeriodoEvaluacion)
INSERT INTO periodos_evaluacion (id, codigo, anio, numero, nombre, fecha_inicio, fecha_cierre, estado, activo) VALUES
(1, 'TRI-2025-4', 2025, 4, '4° Trimestre 2025 (Octubre - Diciembre)', '2025-10-01', '2025-12-31', 'Cerrado', 0),
(2, 'TRI-2026-1', 2026, 1, '1° Trimestre 2026 (Enero - Marzo)', '2026-01-01', '2026-03-31', 'Activo', 1),
(3, 'TRI-2026-2', 2026, 2, '2° Trimestre 2026 (Abril - Junio) - En Preparación', '2026-04-01', '2026-06-30', 'Inactivo', 0);

-- 3.13 Entidad #15: Asignaciones de Metas (MetaFuncionario)
INSERT INTO metas_funcionario (id, codigo, id_funcionario, id_periodo, id_item_meta, item, ponderador, meta_periodo, avance_actual, estado) VALUES
(1, 'ASG-0001', 1, 2, 3, 'Gestión Territorial y Operativos en Terreno', 50.00, 20, 14, 'Activa'),
(2, 'ASG-0002', 2, 2, 3, 'Gestión Territorial y Operativos en Terreno', 60.00, 25, 19, 'Activa'),
(3, 'ASG-0003', 3, 2, 2, 'Informes Sociales y Ficha FIBE', 50.00, 20, 16, 'Activa'),
(4, 'ASG-0017', 4, 1, 5, 'Capacitación y Participación Ciudadana', 25.00, 10, 0, 'Inactiva');

-- 3.14 Entidad #10: Actividades
INSERT INTO actividades (id, codigo, id_funcionario, id_delegacion, id_territorio, id_hito, id_vecino, id_tipo_atencion, id_sub_atencion, id_item_meta, fecha, solicitud, accion, responsable, item_evaluacion, estado, contacto, telefono, ingreso_tubo, codigo_evidencia) VALUES
(1, 'GES-00001', 1, 1, 1, 1, 1, 2, 6, 3, '2026-01-17', 'Reposición de 8 luminarias LED en Av. Viña del Mar', 'Coordinación con cuadrilla eléctrica municipal y verificación nocturna', 'He-Man', 'Gestión Territorial y Operativos en Terreno', 'Realizado', 'Diana Prince (Mujer Maravilla)', '+56 9 7111 2201', 1, 'EVI-2026-0001'),
(2, 'GES-00004', 2, 2, 3, 2, 2, 2, 8, 3, '2026-01-23', 'Recuperación de juegos infantiles y poda en Plaza Juan XXIII', 'Desmalezado, pintura de mobiliario urbano y reparación de escaños', 'Acuaman', 'Gestión Territorial y Operativos en Terreno', 'Realizado', 'Clark Kent (Superman)', '+56 9 7111 2202', 1, 'EVI-2026-0004'),
(3, 'GES-00007', 3, 1, 1, 1, 1, 1, 2, 2, '2026-01-29', 'Aplicación de Ficha FIBE e informe social por emergencia habitacional', 'Visita domiciliaria, peritaje social y entrega de kit de abrigo', 'Flash', 'Informes Sociales y Ficha FIBE', 'Realizado', 'Diana Prince (Mujer Maravilla)', '+56 9 7111 2201', 1, 'EVI-2026-0007'),
(4, 'GES-00012', 4, 3, 4, NULL, 3, 1, 1, 1, '2026-02-08', 'Jornada informativa suspendida por contingencia climática (Inactiva)', 'Registro administrativo desactivado', 'Pantera Negra', 'Atención de Usuario Presencial y Telefónica', 'Inactivo', 'Bruce Wayne (Batman)', '+56 9 7111 2203', 0, 'EVI-2026-0012');

-- 3.15 Entidad #11: Gestiones Sociales
INSERT INTO gestiones_sociales (id, folio, fecha_ingreso, delegacion_id, territorio_id, gestor_responsable_id, vecino_id, tipo_atencion_id, sub_atencion_id, rut_solicitante, nombre_solicitante, telefono_solicitante, direccion_solicitante, diagnostico_social, beneficio_solicitado, estado_caso) VALUES
(1, 'SOC-00001', '2026-01-18', 1, 1, 3, 1, 1, 2, '16.100.100-1', 'Diana Prince (Mujer Maravilla)', '+56 9 7111 2201', 'Av. Viña del Mar #1420, Las Compañías', 'Requerimiento de ayuda paliativa e informe social FIBE', '1 Caja de Alimentos + 2 Frazadas térmicas', 'Resuelto'),
(2, 'SOC-00002', '2026-02-03', 2, 3, 7, 2, 1, 4, '16.200.200-2', 'Clark Kent (Superman)', '+56 9 7111 2202', 'Calle 18 de Septiembre #880, La Antena', 'Apoyo alimentario y actualización de RSH', 'Canasta familiar social', 'En Proceso'),
(3, 'SOC-00004', '2026-01-08', 1, 1, 3, 4, 1, 1, '16.400.400-4', 'Thor Odinson (Asgard)', '+56 9 7111 2204', 'Parcela 14 El Romero, Sector Rural', 'Registro social inactivo sin actividades asociadas', 'Orientación RSH', 'Inactiva');

-- 3.16 Entidad #16: Evidencias
INSERT INTO evidencias (id, codigo, titulo, tipo_archivo, fecha_registro, id_actividad, id_gestion_social, id_verificador, archivo, imagen_verificada, verificador_valido, resultado, estado_validacion, observacion) VALUES
(1, 'EVI-2026-0001', 'Luminarias Las Compañías', 'Fotografía JPG/PNG', '2026-01-18', 1, NULL, 4, 'evidencias/2026/luminarias_las_companias_d01.jpg', 1, 1, 1, 'Aprobada', 'Registro fotográfico nocturno de las 8 luminarias LED operativas.'),
(2, 'EVI-2026-0002', 'Operativo Plaza Juan XXIII', 'Fotografía JPG/PNG', '2026-01-24', 2, NULL, 4, 'evidencias/2026/operativo_plaza_juan_xxiii_d02.jpg', 1, 1, 1, 'Aprobada', 'Fotografía antes y después de mantención de áreas verdes.'),
(3, 'EVI-2026-0006', 'Borrador Reemplazado (Inactiva)', 'Informe Social PDF', '2026-02-12', NULL, 2, 1, 'evidencias/2026/borrador_reemplazado_soc00002.pdf', 0, 0, 0, 'Inactiva', 'Evidencia desactivada para pruebas de estado Inactiva.');

-- ==============================================================================
-- FIN DEL SCRIPT SGR MUNICIPALIDAD DE LA SERENA (17 ENTIDADES OBLIGATORIAS)
-- ==============================================================================
