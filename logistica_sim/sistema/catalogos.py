"""
Módulo de Catálogos
Contiene los datos maestros de productos, clientes y vehículos.
"""

# Catálogo de productos (SKU) - MASTER DATA
# Cada producto tiene configuración completa para simulación ERP
dic_sku = {
    "P001": {
        "nombre": "Filtro hidráulico 3/4",
        "stock_objetivo": 800,  # Aumentado de 200 a 800
        "stock_minimo": 200,    # Aumentado de 50 a 200
        "lead_time_dias": 3,
        "costo_unitario": 45.50,
        "precio_venta": 68.25,
        "categoria": "Hidráulica",
        "peso_kg": 0.5
    },
    "P002": {
        "nombre": "Bomba centrífuga 1HP",
        "stock_objetivo": 600,  # Aumentado de 150 a 600
        "stock_minimo": 150,    # Aumentado de 30 a 150
        "lead_time_dias": 5,
        "costo_unitario": 320.00,
        "precio_venta": 480.00,
        "categoria": "Equipos",
        "peso_kg": 12.0
    },
    "P003": {
        "nombre": "Válvula de presión 2\"",
        "stock_objetivo": 700,  # Aumentado de 200 a 700
        "stock_minimo": 180,    # Aumentado de 60 a 180
        "lead_time_dias": 3,
        "costo_unitario": 85.75,
        "precio_venta": 128.63,
        "categoria": "Válvulas",
        "peso_kg": 2.5
    },
    "P004": {
        "nombre": "Kit de sellos",
        "stock_objetivo": 1000, # Aumentado de 300 a 1000
        "stock_minimo": 250,    # Aumentado de 80 a 250
        "lead_time_dias": 2,
        "costo_unitario": 25.00,
        "precio_venta": 37.50,
        "categoria": "Accesorios",
        "peso_kg": 0.1
    },
    "P005": {
        "nombre": "Motor eléctrico 5HP",
        "stock_objetivo": 400,  # Aumentado de 100 a 400
        "stock_minimo": 100,    # Aumentado de 20 a 100
        "lead_time_dias": 7,
        "costo_unitario": 850.00,
        "precio_venta": 1275.00,
        "categoria": "Equipos",
        "peso_kg": 45.0
    }
}

# Catálogo de clientes (Empresas Fijas) - MASTER DATA
# Cartera de 10 clientes clave para análisis de fidelidad y frecuencia
dic_clientes = {
    "C01": {
        "nombre": "Industrias Mineras del Sur S.A.",
        "tipo": "Corporativo",
        "frecuencia_compra": "Alta",  # Compra frecuentemente
        "credito_limite": 50000,
        "probabilidad_espera": 0.95 # Muy alta fidelidad
    },
    "C02": {
        "nombre": "Constructora Edificar SAC",
        "tipo": "Empresa Mediana",
        "frecuencia_compra": "Media",
        "credito_limite": 25000,
        "probabilidad_espera": 0.60
    },
    "C03": {
        "nombre": "Agroexportadora Frutas del Norte",
        "tipo": "Empresa Grande",
        "frecuencia_compra": "Alta",
        "credito_limite": 40000,
        "probabilidad_espera": 0.85
    },
    "C04": {
        "nombre": "Manufacturas Textiles Unidos",
        "tipo": "Empresa Mediana",
        "frecuencia_compra": "Media",
        "credito_limite": 20000,
        "probabilidad_espera": 0.60
    },
    "C05": {
        "nombre": "Servicios Logísticos Express",
        "tipo": "Empresa Grande",
        "frecuencia_compra": "Muy Alta",
        "credito_limite": 60000,
        "probabilidad_espera": 0.90
    },
    "C06": {
        "nombre": "Pesquera del Pacífico S.A.",
        "tipo": "Corporativo",
        "frecuencia_compra": "Alta",
        "credito_limite": 45000,
        "probabilidad_espera": 0.95
    },
    "C07": {
        "nombre": "Plásticos Industriales SAC",
        "tipo": "Empresa Pequeña",
        "frecuencia_compra": "Baja",
        "credito_limite": 10000,
        "probabilidad_espera": 0.30 # Baja fidelidad, compra donde haya
    },
    "C08": {
        "nombre": "Metalmecánica Precision EIRL",
        "tipo": "Empresa Pequeña",
        "frecuencia_compra": "Baja",
        "credito_limite": 8000,
        "probabilidad_espera": 0.30
    },
    "C09": {
        "nombre": "Químicos y Solventes del Perú",
        "tipo": "Empresa Mediana",
        "frecuencia_compra": "Media",
        "credito_limite": 30000,
        "probabilidad_espera": 0.60
    },
    "C10": {
        "nombre": "Transportes Carga Pesada SAC",
        "tipo": "Empresa Grande",
        "frecuencia_compra": "Alta",
        "credito_limite": 35000,
        "probabilidad_espera": 0.80
    }
}

# Pesos de probabilidad para generación de pedidos según frecuencia
FRECUENCIA_PESOS = {
    "Muy Alta": 5,
    "Alta": 3,
    "Media": 2,
    "Baja": 1
}

# Catálogo de zonas (Destinos)
dic_zonas = {
    "Z01": "Zona Norte",
    "Z02": "Zona Sur",
    "Z03": "Zona Centro",
    "Z04": "Zona Este",
    "Z05": "Zona Oeste"
}

# Catálogo de vehículos
dic_vehiculos = {
    "V01": {"capacidad": 100, "costo_km": 4.5},
    "V02": {"capacidad": 120, "costo_km": 5.0},
    "V03": {"capacidad": 80, "costo_km": 3.8}
}
