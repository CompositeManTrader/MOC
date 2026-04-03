# 📊 MOC TWAP Dashboard

Dashboard en tiempo real para la estrategia **Market On Close (MOC)** de la mesa de capitales propia.

## ¿Qué hace?

- Calcula el **TWAP (Time-Weighted Average Price)** por emisora
- Actualización automática **cada segundo** en hora de Ciudad de México
- Muestra posición, lotes/minuto, ejecutado y saldo pendiente por emisora
- Permite elegir ventana de ejecución de **20 o 30 minutos**
- Selección libre de hora de inicio y hora de fin
- Agregar/eliminar emisoras dinámicamente

## Lógica TWAP

```
Posición Neta = Σ Compras − Σ Ventas
Lotes/min = Posición Neta ÷ Minutos Totales
Saldo = Lotes/min × Minutos Restantes
Ejecutado = Posición − |Saldo|
```

## Deploy en Streamlit Cloud

1. Sube este repositorio a GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta el repo y selecciona `app.py`
4. Deploy

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estructura

```
├── app.py                  # Aplicación principal
├── requirements.txt        # Dependencias
├── .streamlit/
│   └── config.toml         # Tema oscuro
└── README.md
```
