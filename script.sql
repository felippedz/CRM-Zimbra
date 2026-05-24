IF DB_ID('zimbra_crm') IS NULL
    CREATE DATABASE zimbra_crm;
GO

USE zimbra_crm;
GO

CREATE TABLE roles (
    id_rol INT IDENTITY(1,1) PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL UNIQUE
);
GO

INSERT INTO roles(nombre_rol) VALUES
('ADMIN'),
('EMPLEADO'),
('CLIENTE');
GO

CREATE TABLE usuarios (
    id_usuario INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    id_rol INT NOT NULL,
    fecha_registro DATETIME DEFAULT GETDATE(),
    estado VARCHAR(10) DEFAULT 'ACTIVO',
    CONSTRAINT chk_usuarios_estado CHECK (estado IN ('ACTIVO','INACTIVO')),
    CONSTRAINT fk_usuarios_roles FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
);
GO

CREATE TABLE departamentos (
    id_departamento INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL
);
GO

INSERT INTO departamentos(nombre) VALUES
('Ventas'),
('Marketing'),
('Administracion');
GO

CREATE TABLE empleados (
    id_empleado INT IDENTITY(1,1) PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_departamento INT NOT NULL,
    cargo VARCHAR(100),
    salario DECIMAL(10,2),
    CONSTRAINT fk_empleados_usuarios FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_empleados_departamentos FOREIGN KEY (id_departamento) REFERENCES departamentos(id_departamento)
);
GO

CREATE TABLE niveles_cliente (
    id_nivel INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE,
    monto_minimo DECIMAL(10,2),
    descuento DECIMAL(5,2)
);
GO

INSERT INTO niveles_cliente(nombre, monto_minimo, descuento) VALUES
('PROSPECTO', 0, 0),
('CLIENTE', 1, 0),
('BRONCE', 1000, 5),
('PLATA', 5000, 10),
('ORO', 10000, 15);
GO

CREATE TABLE clientes (
    id_cliente INT IDENTITY(1,1) PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_nivel INT DEFAULT 1,
    empresa VARCHAR(100),
    telefono VARCHAR(20),
    CONSTRAINT fk_clientes_usuarios FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_clientes_niveles FOREIGN KEY (id_nivel) REFERENCES niveles_cliente(id_nivel)
);
GO

CREATE TABLE servicios (
    id_servicio INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2),
    nivel_servicio VARCHAR(20),
    estado VARCHAR(10) DEFAULT 'ACTIVO',
    CONSTRAINT chk_servicios_nivel CHECK (nivel_servicio IN ('BASICO','PROFESIONAL','ENTERPRISE')),
    CONSTRAINT chk_servicios_estado CHECK (estado IN ('ACTIVO','INACTIVO'))
);
GO

CREATE TABLE campanias (
    id_campania INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(100),
    medio_contacto VARCHAR(40),
    presupuesto DECIMAL(10,2),
    fecha_inicio DATE,
    fecha_fin DATE,
    objetivo TEXT,
    CONSTRAINT chk_campanias_medio CHECK (medio_contacto IN (
        'LLAMADA_TELEFONICA',
        'CORREO_ELECTRONICO',
        'EVENTO_SOCIAL',
        'REDES_SOCIALES',
        'REFERIDO',
        'PUBLICIDAD_WEB'
    ))
);
GO

CREATE TABLE ventas (
    id_venta INT IDENTITY(1,1) PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_campania INT NULL,
    fecha DATETIME DEFAULT GETDATE(),
    total DECIMAL(10,2) DEFAULT 0,
    estado_pago VARCHAR(20) DEFAULT 'PENDIENTE',
    CONSTRAINT chk_ventas_estado CHECK (estado_pago IN ('PENDIENTE','PAGADO','VENCIDO')),
    CONSTRAINT fk_ventas_clientes FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    CONSTRAINT fk_ventas_campanias FOREIGN KEY (id_campania) REFERENCES campanias(id_campania)
);
GO

CREATE TABLE detalle_venta (
    id_detalle INT IDENTITY(1,1) PRIMARY KEY,
    id_venta INT NOT NULL,
    id_servicio INT NOT NULL,
    cantidad INT NOT NULL,
    subtotal DECIMAL(10,2),
    CONSTRAINT fk_detalle_venta_ventas FOREIGN KEY (id_venta) REFERENCES ventas(id_venta),
    CONSTRAINT fk_detalle_venta_servicios FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
);
GO

CREATE TABLE cliente_servicios (
    id_cliente_servicio INT IDENTITY(1,1) PRIMARY KEY,
    id_cliente INT,
    id_servicio INT,
    estado VARCHAR(20) DEFAULT 'ACTIVO',
    fecha_inicio DATE,
    fecha_fin DATE,
    CONSTRAINT chk_cliente_servicios_estado CHECK (estado IN ('ACTIVO','SUSPENDIDO')),
    CONSTRAINT fk_cliente_servicios_clientes FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    CONSTRAINT fk_cliente_servicios_servicios FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
);
GO

CREATE TABLE auditoria_ventas (
    id_auditoria INT IDENTITY(1,1) PRIMARY KEY,
    id_venta INT,
    accion VARCHAR(50),
    fecha DATETIME DEFAULT GETDATE(),
    descripcion TEXT,
    CONSTRAINT fk_auditoria_ventas_ventas FOREIGN KEY (id_venta) REFERENCES ventas(id_venta)
);
GO

CREATE TABLE historial_niveles_cliente (
    id_historial INT IDENTITY(1,1) PRIMARY KEY,
    id_cliente INT,
    id_nivel_anterior INT,
    id_nivel_nuevo INT,
    fecha DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_historial_niveles_cliente FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    CONSTRAINT fk_historial_niveles_anterior FOREIGN KEY (id_nivel_anterior) REFERENCES niveles_cliente(id_nivel),
    CONSTRAINT fk_historial_niveles_nuevo FOREIGN KEY (id_nivel_nuevo) REFERENCES niveles_cliente(id_nivel)
);
GO

INSERT INTO servicios(nombre, descripcion, precio, nivel_servicio) VALUES
('Correo Empresarial Zimbra','Servicio de correo corporativo seguro',120,'BASICO'),
('Zimbra Collaboration Suite','Suite colaborativa empresarial',450,'PROFESIONAL'),
('Almacenamiento en la Nube','Servicio cloud empresarial',300,'PROFESIONAL'),
('Respaldo Automatico','Backup automatizado de correos',180,'BASICO'),
('Videoconferencias Empresariales','Sistema de reuniones virtuales',350,'PROFESIONAL'),
('Servidor Dedicado','Infraestructura dedicada empresarial',1500,'ENTERPRISE'),
('Migracion de Correos','Migracion de plataformas de correo',700,'PROFESIONAL'),
('Seguridad Avanzada','Proteccion anti spam y malware',900,'ENTERPRISE'),
('Licenciamiento Premium','Licencias premium Zimbra',2500,'ENTERPRISE'),
('Soporte 24/7','Soporte tecnico empresarial',800,'ENTERPRISE');
GO

INSERT INTO usuarios(nombre, correo, password_hash, id_rol) VALUES
('Carlos Ramirez','carlos@zimbra.com',CONVERT(VARCHAR(64),HASHBYTES('SHA2_256','123456'),2),1),
('Ana Torres','ana@zimbra.com',CONVERT(VARCHAR(64),HASHBYTES('SHA2_256','123456'),2),2),
('Luis Martinez','luis@empresa.com',CONVERT(VARCHAR(64),HASHBYTES('SHA2_256','123456'),2),3),
('Maria Lopez','maria@empresa.com',CONVERT(VARCHAR(64),HASHBYTES('SHA2_256','123456'),2),3);
GO

INSERT INTO empleados(id_usuario, id_departamento, cargo, salario) VALUES
(1,3,'Administrador General',5000),
(2,1,'Ejecutiva de Ventas',3000);
GO

INSERT INTO clientes(id_usuario, empresa, telefono) VALUES
(3,'Tech Solutions SAS','3001112233'),
(4,'Global Services LTDA','3019998877');
GO

INSERT INTO campanias(nombre, medio_contacto, presupuesto, fecha_inicio, fecha_fin, objetivo) VALUES
('Campania Empresarial 2026','CORREO_ELECTRONICO',5000,'2026-01-01','2026-06-30','Captar empresas medianas'),
('Expo Tecnologia','EVENTO_SOCIAL',10000,'2026-03-01','2026-03-10','Promocionar soluciones cloud');
GO

IF OBJECT_ID('registrar_venta','P') IS NOT NULL
    DROP PROCEDURE registrar_venta;
GO

CREATE PROCEDURE registrar_venta
    @p_id_cliente INT,
    @p_id_campania INT,
    @p_id_servicio INT,
    @p_cantidad INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @v_precio DECIMAL(10,2);
        DECLARE @v_total DECIMAL(10,2);
        DECLARE @v_id_venta INT;

        SELECT @v_precio = precio
        FROM servicios
        WHERE id_servicio = @p_id_servicio;

        SET @v_total = @v_precio * @p_cantidad;

        INSERT INTO ventas(id_cliente, id_campania, total, estado_pago)
        VALUES(@p_id_cliente, @p_id_campania, @v_total, 'PAGADO');

        SET @v_id_venta = SCOPE_IDENTITY();

        INSERT INTO detalle_venta(id_venta, id_servicio, cantidad, subtotal)
        VALUES(@v_id_venta, @p_id_servicio, @p_cantidad, @v_total);

        INSERT INTO cliente_servicios(id_cliente, id_servicio, fecha_inicio, fecha_fin)
        VALUES(@p_id_cliente, @p_id_servicio, CONVERT(DATE,GETDATE()), DATEADD(YEAR,1,CONVERT(DATE,GETDATE())));

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

IF OBJECT_ID('actualizar_nivel_cliente','P') IS NOT NULL
    DROP PROCEDURE actualizar_nivel_cliente;
GO

CREATE PROCEDURE actualizar_nivel_cliente
    @p_id_cliente INT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @total_compras DECIMAL(10,2) = 0;

    SELECT @total_compras = SUM(total)
    FROM ventas
    WHERE id_cliente = @p_id_cliente
      AND estado_pago = 'PAGADO';

    IF @total_compras >= 10000
        UPDATE clientes SET id_nivel = 5 WHERE id_cliente = @p_id_cliente;
    ELSE IF @total_compras >= 5000
        UPDATE clientes SET id_nivel = 4 WHERE id_cliente = @p_id_cliente;
    ELSE IF @total_compras >= 1000
        UPDATE clientes SET id_nivel = 3 WHERE id_cliente = @p_id_cliente;
    ELSE IF @total_compras > 0
        UPDATE clientes SET id_nivel = 2 WHERE id_cliente = @p_id_cliente;
END;
GO

IF OBJECT_ID('trg_actualizar_nivel','TR') IS NOT NULL
    DROP TRIGGER trg_actualizar_nivel;
GO

CREATE TRIGGER trg_actualizar_nivel
ON ventas
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO clientes(id_nivel)
    SELECT 0 WHERE 1 = 0; -- no-op for compatibility
    DECLARE @id_cliente INT;
    SELECT TOP 1 @id_cliente = id_cliente FROM inserted;
    EXEC actualizar_nivel_cliente @p_id_cliente = @id_cliente;
END;
GO

IF OBJECT_ID('trg_suspender_servicio','TR') IS NOT NULL
    DROP TRIGGER trg_suspender_servicio;
GO

CREATE TRIGGER trg_suspender_servicio
ON ventas
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE cs
    SET cs.estado = 'SUSPENDIDO'
    FROM cliente_servicios cs
    INNER JOIN detalle_venta dv ON cs.id_servicio = dv.id_servicio
    INNER JOIN inserted i ON dv.id_venta = i.id_venta
    WHERE i.estado_pago = 'VENCIDO'
      AND cs.id_cliente = i.id_cliente;
END;
GO

IF OBJECT_ID('trg_auditoria_ventas','TR') IS NOT NULL
    DROP TRIGGER trg_auditoria_ventas;
GO

CREATE TRIGGER trg_auditoria_ventas
ON ventas
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO auditoria_ventas(id_venta, accion, descripcion)
    SELECT id_venta, 'INSERT', 'Nueva venta registrada. Total: ' + CAST(total AS VARCHAR(50))
    FROM inserted;
END;
GO

IF OBJECT_ID('trg_historial_niveles','TR') IS NOT NULL
    DROP TRIGGER trg_historial_niveles;
GO

CREATE TRIGGER trg_historial_niveles
ON clientes
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO historial_niveles_cliente(id_cliente, id_nivel_anterior, id_nivel_nuevo)
    SELECT i.id_cliente, d.id_nivel, i.id_nivel
    FROM inserted i
    JOIN deleted d ON i.id_cliente = d.id_cliente
    WHERE d.id_nivel <> i.id_nivel;
END;
GO

CREATE VIEW vista_ventas_mensuales AS
SELECT
    YEAR(fecha) AS anio,
    MONTH(fecha) AS mes,
    SUM(total) AS total_ventas
FROM ventas
GROUP BY YEAR(fecha), MONTH(fecha);
GO

CREATE VIEW vista_mejores_clientes AS
SELECT
    c.id_cliente,
    u.nombre,
    n.nombre AS nivel,
    SUM(v.total) AS total_compras
FROM clientes c
INNER JOIN usuarios u ON c.id_usuario = u.id_usuario
INNER JOIN niveles_cliente n ON c.id_nivel = n.id_nivel
INNER JOIN ventas v ON c.id_cliente = v.id_cliente
GROUP BY c.id_cliente, u.nombre, n.nombre;
GO

CREATE VIEW vista_rendimiento_campanias AS
SELECT
    c.nombre,
    c.medio_contacto,
    COUNT(v.id_venta) AS ventas_generadas,
    SUM(v.total) AS ingresos
FROM campanias c
LEFT JOIN ventas v ON c.id_campania = v.id_campania
GROUP BY c.id_campania, c.nombre, c.medio_contacto;
GO

CREATE VIEW vista_departamentos AS
SELECT
    d.nombre AS departamento,
    COUNT(e.id_empleado) AS total_empleados
FROM departamentos d
LEFT JOIN empleados e ON d.id_departamento = e.id_departamento
GROUP BY d.nombre;
GO
