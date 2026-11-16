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
-- FIN DEL SCRIPT SGR MUNICIPALIDAD DE LA SERENA (17 ENTIDADES OBLIGATORIAS)
-- ==============================================================================
