/**
 * Hazen-Williams Calc - Interacción de interfaz (Stateless)
 * Sin almacenamiento local (localStorage/sessionStorage/cookies).
 */

document.addEventListener("DOMContentLoaded", function () {
  const tramosContainer = document.getElementById("tramos-container");
  const btnAgregarTramo = document.getElementById("btn-agregar-tramo");
  const inputCantidadTramos = document.getElementById("cantidad_tramos");

  // Metadatos de materiales pasados desde la plantilla
  const materialesData = window.MATERIALES_CONFIG || {};
  const accesoriosData = window.ACCESORIOS_CONFIG || [];

  /**
   * Actualiza los números visibles y nombres de campos de los tramos
   */
  function actualizarIndicesTramos() {
    if (!tramosContainer) return;
    const cards = tramosContainer.querySelectorAll(".tramo-card");
    const total = cards.length;

    if (inputCantidadTramos) {
      inputCantidadTramos.value = total;
    }

    cards.forEach((card, idx) => {
      const num = idx + 1;
      card.setAttribute("data-tramo-index", num);

      // Título
      const titleSpan = card.querySelector(".tramo-numero-span");
      if (titleSpan) titleSpan.textContent = num;

      // Actualizar names e ids de inputs
      card.querySelectorAll("[data-name-pattern]").forEach((el) => {
        const pattern = el.getAttribute("data-name-pattern");
        el.name = `tramo_${num}_${pattern}`;
        el.id = `tramo_${num}_${pattern}`;
      });

      // Botón eliminar: solo mostrar si hay más de 1 tramo
      const btnEliminar = card.querySelector(".btn-eliminar-tramo");
      if (btnEliminar) {
        btnEliminar.style.display = total > 1 ? "inline-block" : "none";
      }
    });

    if (btnAgregarTramo) {
      btnAgregarTramo.disabled = total >= 10;
      if (total >= 10) {
        btnAgregarTramo.title = "Máximo de 10 tramos en serie alcanzado";
      } else {
        btnAgregarTramo.title = "Agregar otro tramo en serie";
      }
    }
  }

  /**
   * Configura eventos interactivos de un tramo
   */
  function configurarEventosTramo(card) {
    const selectMaterial = card.querySelector(".select-material");
    const inputC = card.querySelector(".input-c-valor");
    const ayudaMaterial = card.querySelector(".ayuda-material-texto");
    const badgeRango = card.querySelector(".badge-rango-c");
    const selectDiametro = card.querySelector(".select-diametro-comercial");
    const inputDInterior = card.querySelector(".input-d-interior");

    if (selectMaterial) {
      selectMaterial.addEventListener("change", function () {
        const matId = this.value;
        const info = materialesData[matId];
        if (info) {
          if (inputC) inputC.value = info.c_default;
          if (ayudaMaterial) ayudaMaterial.textContent = info.uso_tipico;

          if (badgeRango) {
            if (info.es_rango && info.c_min && info.c_max) {
              badgeRango.textContent = `Rango: ${info.c_min} - ${info.c_max} (Sugerido más desfavorable: ${info.c_default})`;
              badgeRango.classList.remove("d-none");
            } else {
              badgeRango.classList.add("d-none");
            }
          }
        }
      });
    }

    if (selectDiametro && inputDInterior) {
      selectDiametro.addEventListener("change", function () {
        const dVal = this.value;
        if (dVal) {
          inputDInterior.value = dVal;
        }
      });
    }

    // Accesorios del tramo
    const btnAgregarAccesorio = card.querySelector(".btn-agregar-accesorio");
    const listaAccesorios = card.querySelector(".lista-accesorios");

    if (btnAgregarAccesorio && listaAccesorios) {
      btnAgregarAccesorio.addEventListener("click", function () {
        agregarFilaAccesorio(card, listaAccesorios);
      });
    }

    // Configurar filas de accesorios existentes
    card.querySelectorAll(".fila-accesorio").forEach((fila) => {
      configurarFilaAccesorio(fila);
    });

    // Botón eliminar tramo
    const btnEliminar = card.querySelector(".btn-eliminar-tramo");
    if (btnEliminar) {
      btnEliminar.addEventListener("click", function () {
        const total = tramosContainer.querySelectorAll(".tramo-card").length;
        if (total > 1) {
          card.remove();
          actualizarIndicesTramos();
        }
      });
    }
  }

  function agregarFilaAccesorio(card, container) {
    const numTramo = card.getAttribute("data-tramo-index") || "1";
    const div = document.createElement("div");
    div.className = "row g-2 align-items-center mb-2 fila-accesorio border-bottom pb-2";

    let opcionesHtml = '<option value="">-- Seleccionar accesorio --</option>';
    accesoriosData.forEach((acc) => {
      opcionesHtml += `<option value="${acc.id}" data-k="${acc.k_default}" data-nombre="${acc.nombre}">${acc.nombre} (K=${acc.k_default})</option>`;
    });

    div.innerHTML = `
      <div class="col-md-5 col-12">
        <select class="form-select form-select-sm select-tipo-accesorio">
          ${opcionesHtml}
        </select>
        <input type="hidden" name="tramo_${numTramo}_acc_id[]" class="input-acc-id" value="">
        <input type="hidden" name="tramo_${numTramo}_acc_nombre[]" class="input-acc-nombre" value="">
      </div>
      <div class="col-md-3 col-6">
        <div class="input-group input-group-sm">
          <span class="input-group-text">Cant.</span>
          <input type="number" min="0" step="1" class="form-control input-acc-cant" name="tramo_${numTramo}_acc_cantidad[]" value="1">
        </div>
      </div>
      <div class="col-md-3 col-6">
        <div class="input-group input-group-sm">
          <span class="input-group-text">K</span>
          <input type="text" class="form-control input-acc-k" name="tramo_${numTramo}_acc_k[]" value="0.00" title="Coeficiente K editable (PENDIENTE DE VERIFICAR)">
        </div>
      </div>
      <div class="col-md-1 col-12 text-end">
        <button type="button" class="btn btn-outline-danger btn-sm btn-remover-accesorio" title="Quitar accesorio">
          &times;
        </button>
      </div>
    `;

    container.appendChild(div);
    configurarFilaAccesorio(div);
  }

  function configurarFilaAccesorio(fila) {
    const selectTipo = fila.querySelector(".select-tipo-accesorio");
    const inputK = fila.querySelector(".input-acc-k");
    const inputNombre = fila.querySelector(".input-acc-nombre");
    const inputId = fila.querySelector(".input-acc-id");
    const btnRemover = fila.querySelector(".btn-remover-accesorio");

    if (selectTipo) {
      selectTipo.addEventListener("change", function () {
        const opt = this.options[this.selectedIndex];
        if (opt && opt.value) {
          if (inputK) inputK.value = opt.getAttribute("data-k") || "0.00";
          if (inputNombre) inputNombre.value = opt.getAttribute("data-nombre") || opt.text;
          if (inputId) inputId.value = opt.value;
        }
      });
    }

    if (btnRemover) {
      btnRemover.addEventListener("click", function () {
        fila.remove();
      });
    }
  }

  // Inicializar tramos existentes
  if (tramosContainer) {
    tramosContainer.querySelectorAll(".tramo-card").forEach((card) => {
      configurarEventosTramo(card);
    });
    actualizarIndicesTramos();

    if (btnAgregarTramo) {
      btnAgregarTramo.addEventListener("click", function () {
        const cards = tramosContainer.querySelectorAll(".tramo-card");
        if (cards.length >= 10) return;

        // Clonar el primer tramo como plantilla
        const primera = cards[0];
        const clon = primera.cloneNode(true);

        // Limpiar valores en el clon
        const inputD = clon.querySelector(".input-d-interior");
        const inputL = clon.querySelector(".input-longitud");
        const listaAcc = clon.querySelector(".lista-accesorios");

        if (inputD) inputD.value = "100";
        if (inputL) inputL.value = "100";
        if (listaAcc) listaAcc.innerHTML = ""; // sin accesorios por defecto en nuevo tramo

        tramosContainer.appendChild(clon);
        configurarEventosTramo(clon);
        actualizarIndicesTramos();
      });
    }
  }
});
