# PoliCampo - Sistema de Apoyo a la Toma de Decisiones Agroecológicas

Sistema web desarrollado con **Python, Django, Bootstrap 5 y Modern Web Best Practices** para la optimización del diseño de terrenos de cultivo en **Jujuy (Argentina)**, apoyando la incorporación estratégica de bandas florales y bordes multifuncionales para la recuperación de la biodiversidad y el control biológico.

---

## 🌾 Módulos Desarrollados (Prototipo)

### 1. Módulo de Diagnóstico Espacial y Déficit de Biodiversidad (`/` o `/diagnostico/`)
* **Ficha del Terreno y Cultivo Comercial:** Registro de ubicación en Jujuy, superficie (ha), tipo de suelo, pendiente, riego y cultivo comercial activo (ej. Tomate Redondo).
* **Cálculo de la Regla Agronómica del 20%:** Evaluación del porcentaje actual vs. el 20% recomendado de infraestructura ecológica.
* **Indicadores Visuales y Semáforo:** Muestra el déficit de biodiversidad (ej. -17%), nivel de riesgo (*CRÍTICO*, *MODERADO*, *ADECUADO*) y hectáreas a compensar.
* **Diagnóstico de Vulnerabilidad:** Alertas sobre riesgos de plagas (trips, Tuta absoluta) y ventanas descubiertas de polinización.
* **Identificación de Zonas Aptas:** Propuesta de áreas viables en cabeceras de lote y bordes perimetrales.
* **Simulador Interactivo:** Modal integrado para recalcular parámetros y probar diferentes escenarios de terreno.

### 2. Módulo de Informe Técnico y Rediseño Territorial (`/informe/`)
* **Código de Informe y Ficha Técnica:** Encabezado formal con código único (`INF-JUJ-2026-001`).
* **Resumen Ejecutivo Comparativo:** Estado inicial (deficitario) vs. estado proyectado (estándar agroecológico alcanzado).
* **Esquema Espacial de Rediseño:** Distribución gráfica en el lote (cabeceras norte/sur, borde este y corredores transversales intermedios).
* **Catálogo de Especies Florales y Matriz de Compatibilidad:** Tabla con especies recomendadas (*Caléndula*, *Borraja*, *Vicia villosa*, *Trébol blanco*), ponderación de compatibilidad (-5 a +5), requerimientos de agua/corte y servicios ecosistémicos.
* **Calendario de Actividades Agroecológicas:** Cronograma mensual (Agosto a Mayo) de siembra, floración activa y labores de corte/mantenimiento.
* **Soporte Nativo para Impresión / PDF (`@media print`):** Botón para generar y descargar el informe en PDF con diseño limpio y sin elementos de navegación.

---

## 🚀 Cómo Iniciar el Servidor de Desarrollo

1. Abre tu terminal o PowerShell en la carpeta del proyecto (`PoliCampo`).
2. Activa el entorno virtual e inicia el servidor de Django:

```powershell
.\venv\Scripts\python manage.py runserver
```

3. Abre tu navegador web en:
   * **Módulo de Diagnóstico:** `http://127.0.0.1:8000/`
   * **Módulo de Informe Técnico:** `http://127.0.0.1:8000/informe/`
   * **Panel Administrativo Django:** `http://127.0.0.1:8000/admin/`

---

## 🧪 Pruebas Automatizadas

Para ejecutar las pruebas del sistema:
```powershell
.\venv\Scripts\python manage.py test agroecologia
```
