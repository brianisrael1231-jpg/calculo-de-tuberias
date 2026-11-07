# Verificación Rápida de Tuberías - Hazen-Williams

Aplicación web ágil y responsiva para el cálculo y verificación preliminar de pérdidas de carga en cañerías a sección llena según la **fórmula de Hazen-Williams**.

---

## 1. Para qué sirve
Permite a los proyectistas verificar de forma instantánea si una tubería cumple con los requerimientos de caudal y presión antes de pasar a un diseño de red más avanzado, facilitando cálculos preliminares desde cualquier dispositivo sin instalaciones pesadas ni configuraciones complejas.

---

## 2. Datos que debemos ingresar (Inputs)
El usuario completa un formulario web simple con cuatro datos esenciales:
1. **Longitud del tramo de cañería:** Expresada en metros [m].
2. **Diámetro del caño:** Seleccionable en milímetros [mm] o pulgadas [pulg / "].
3. **Caudal requerido:** Seleccionable en litros por segundo [L/s] o metros cúbicos por segundo [m³/s].
4. **Material del caño:** Seleccionable mediante menú desplegable:
   - **PVC (Policloruro de Vinilo)**
   - **Polietileno (PEAD)**
   - **Acero / Hierro Galvanizado**
   - **Hierro Fundido (Dúctil)**

---

## 3. Cálculos que hace el software (Proceso interno)
La aplicación procesa los datos utilizando fórmulas estándar de la hidráulica y el saneamiento:
* **a) Asignación de Rugosidad ($C$):** Lee internamente el valor del coeficiente de Hazen-Williams correspondiente al material seleccionado:
  - $\text{PVC} \implies C = 150$
  - $\text{Polietileno (PEAD)} \implies C = 140$
  - $\text{Hierro Fundido} \implies C = 130$
  - $\text{Acero} \implies C = 120$
* **b) Cálculo de la Velocidad del Agua:** Relaciona el caudal ingresado con el área de la sección transversal del diámetro para calcular la velocidad del fluido:
  $$A = \frac{\pi \cdot D^2}{4}, \qquad V = \frac{Q}{A}$$
* **c) Cálculo de la Pérdida de Carga:** Aplica la fórmula de Hazen-Williams combinando la longitud, el caudal, el diámetro y la rugosidad:
  $$J = 10{,}67 \cdot \frac{Q^{1{,}852}}{C^{1{,}852} \cdot D^{4{,}87}} \quad [\text{m/m}]$$
  $$h_f = J \cdot L \quad [\text{m.c.a.}]$$
  $$h_{f,\text{bar}} = h_f \times 0{,}0980665 \quad [\text{bar}]$$

---

## 4. Valores que nos devuelve (Outputs)
La pantalla muestra de forma inmediata los resultados del cálculo:
1. **El coeficiente de rugosidad ($C$)** aplicado automáticamente según el material elegido.
2. **La velocidad resultante del flujo ($V$ en m/s):**
   - Indicando mediante mensaje y semáforo si está en:
     - 🟢 **Rango óptimo de diseño** ($0{,}60\text{ m/s} \le V \le 2{,}00\text{ m/s}$): previene sedimentaciones y evita desgaste por erosión.
     - 🟡 **Baja velocidad** ($V < 0{,}60\text{ m/s}$): advertencia de riesgo de sedimentación de partículas.
     - 🔴 **Exceso de velocidad** ($V > 2{,}00\text{ m/s}$): advertencia de riesgo de erosión interna y golpe de ariete.
3. **La pérdida de carga total acumulada en el tramo ($h_f$):**
   - En **metros de columna de agua** [m.c.a.].
   - En **bar** [bar].
   - Gradiente unitario $J$ en m/100m.
4. **Memoria técnica de cálculo paso a paso:** Detalle de cada fórmula algebraica, sustitución numérica y resultado.

---

## 5. Requisitos y Ejecución

### Ejecución Local
```bash
python run.py
```
Acceder en el navegador: `http://localhost:5000`

### Pruebas Unitarias Automatizadas
```bash
python -m pytest -v
```

---

## 6. Arquitectura Stateless
La aplicación es estrictamente **sin estado (stateless)**:
- No almacena datos en disco ni bases de datos.
- No utiliza cookies ni almacenamiento en el navegador (`localStorage` / `sessionStorage`).
- La impresión y generación de informes en PDF se realiza directamente con el motor del navegador mediante `window.print()` y reglas de estilo limpias en `@media print`.
