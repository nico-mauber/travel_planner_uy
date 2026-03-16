"""Componente de item del itinerario expandible.

Usa clases tp-* del design system para badges, bloques de notas
y estilos de items sugeridos. Incluye atributos ARIA para accesibilidad.
"""

import html

import streamlit as st
from config.settings import (
    ITEM_TYPE_ICONS, STATUS_ICONS, ITEM_TYPE_LABELS,
    ItemStatus, ItemType,
)


# Mapeo de estados a clases CSS de badge
_STATUS_BADGE_CLASS = {
    ItemStatus.CONFIRMED: "tp-itinerary-badge--status",
    ItemStatus.PENDING: "tp-itinerary-badge--pending",
    ItemStatus.SUGGESTED: "tp-itinerary-badge--suggested",
}

# Labels de estado en espanol
_STATUS_LABELS = {
    ItemStatus.CONFIRMED: "Confirmado",
    ItemStatus.PENDING: "Pendiente",
    ItemStatus.SUGGESTED: "Sugerido",
}


def render_itinerary_item(item: dict, index: int) -> dict:
    """Renderiza un item del itinerario como expander.

    Retorna: {"action": "accept"|"discard"} o {}
    """
    result = {}
    icon = ITEM_TYPE_ICONS.get(ItemType(item["item_type"]), "\U0001F4E6")
    status_icon = STATUS_ICONS.get(ItemStatus(item["status"]), "")
    type_label = ITEM_TYPE_LABELS.get(ItemType(item["item_type"]), item["item_type"])
    status_enum = ItemStatus(item["status"])
    status_label = _STATUS_LABELS.get(status_enum, item["status"])
    badge_class = _STATUS_BADGE_CLASS.get(status_enum, "tp-itinerary-badge--status")

    is_suggested = item["status"] == ItemStatus.SUGGESTED.value

    # Titulo mejorado con emoji + nombre + badges de hora y estado (HTML)
    time_badge = (
        f'<span class="tp-itinerary-badge tp-itinerary-badge--time">'
        f'{html.escape(item["start_time"])} - {html.escape(item["end_time"])}'
        f'</span>'
    )
    status_badge = (
        f'<span class="tp-itinerary-badge {badge_class}">'
        f'{status_icon} {html.escape(status_label)}'
        f'</span>'
    )

    # El titulo del expander es texto plano (Streamlit no soporta HTML en summary)
    expander_title = f"{icon} {item['name']} \u2014 {item['start_time']} a {item['end_time']}"

    with st.expander(expander_title, expanded=False):
        # Badges HTML de hora y estado dentro del expander
        badges_html = f'{time_badge} {status_badge}'
        st.markdown(badges_html, unsafe_allow_html=True)

        if is_suggested:
            # Banner de sugerencia con estilo del design system
            st.markdown(
                '<div class="tp-suggested-item" style="padding: var(--tp-space-2) var(--tp-space-3); '
                'margin: var(--tp-space-2) 0;">'
                '\U0001F4A1 <em>Sugerencia del agente \u2014 aun no es parte del plan</em>'
                '</div>',
                unsafe_allow_html=True,
            )

        # Grid de informacion: info principal | costos
        info_cols = st.columns(2)
        with info_cols[0]:
            st.markdown(f"**Tipo:** {type_label}")
            if item.get("location"):
                st.markdown(f"\U0001F4CD **Ubicacion:** {item['location']}")
            if item.get("address"):
                st.markdown(f"\U0001F3E0 **Direccion:** {item['address']}")
        with info_cols[1]:
            cost_est = item.get("cost_estimated", 0) or 0
            cost_real = item.get("cost_real", 0) or 0

            if cost_est > 0:
                st.markdown(f"**Costo estimado:** USD {cost_est:,.0f}")
            if cost_real > 0:
                st.markdown(f"**Costo real:** USD {cost_real:,.0f}")

                # Diferencia entre estimado y real
                if cost_est > 0:
                    diff = cost_real - cost_est
                    if diff != 0:
                        diff_pct = (diff / cost_est) * 100
                        if diff > 0:
                            diff_class = "tp-itinerary-cost-diff tp-itinerary-cost-diff--over"
                            diff_text = f"+USD {diff:,.0f} ({diff_pct:+.0f}%)"
                        else:
                            diff_class = "tp-itinerary-cost-diff tp-itinerary-cost-diff--under"
                            diff_text = f"-USD {abs(diff):,.0f} ({diff_pct:+.0f}%)"
                        st.markdown(
                            f'<span class="{diff_class}">{html.escape(diff_text)}</span>',
                            unsafe_allow_html=True,
                        )

            if item.get("provider"):
                st.markdown(f"**Proveedor:** {item['provider']}")

        # Notas en bloque estilizado (quote con borde izquierdo)
        if item.get("notes"):
            safe_notes = html.escape(str(item["notes"]))
            st.markdown(
                f'<div class="tp-itinerary-notes">{safe_notes}</div>',
                unsafe_allow_html=True,
            )

        # Enlace de reserva como CTA discreto
        if item.get("booking_url"):
            st.link_button("\U0001F517 Ver reserva", item["booking_url"])

        # Acciones para sugeridos con colores semanticos
        if is_suggested:
            act_cols = st.columns(2)
            with act_cols[0]:
                if st.button(
                    "\u2705 Aceptar",
                    key=f"accept_{item['id']}_{index}",
                    type="primary",
                    use_container_width=True,
                    help="Aceptar esta sugerencia y agregarla al plan",
                ):
                    result = {"action": "accept", "item_id": item["id"]}
            with act_cols[1]:
                if st.button(
                    "\u274C Descartar",
                    key=f"discard_{item['id']}_{index}",
                    use_container_width=True,
                    help="Descartar esta sugerencia",
                ):
                    result = {"action": "discard", "item_id": item["id"]}

    return result


def render_transfer(transfer_info: dict) -> None:
    """Renderiza un bloque visual de traslado entre items.

    Usa la clase tp-transfer-block del design system con contenido
    mejorado: origen y destino con flecha estilizada, detalles en chips.
    """
    safe_from = html.escape(transfer_info['from'])
    safe_to = html.escape(transfer_info['to'])
    safe_transport = html.escape(str(transfer_info.get('transport', '')))
    safe_duration = html.escape(str(transfer_info.get('duration', '')))
    cost = transfer_info.get('cost_estimated', 0)

    # Aria label descriptivo para accesibilidad
    aria_label = f"Traslado de {transfer_info['from']} a {transfer_info['to']}"

    transfer_html = (
        f'<div class="tp-transfer-block" role="complementary" aria-label="{html.escape(aria_label)}">'
        f'  \U0001F695 <b>{safe_from}</b>'
        f'  <span class="tp-transfer-block__arrow">\u2192</span>'
        f'  <b>{safe_to}</b>'
        f'  <span class="tp-transfer-chip">{safe_transport}</span>'
        f'  <span class="tp-transfer-chip">\u23F1\uFE0F {safe_duration}</span>'
        f'  <span class="tp-transfer-chip">~USD {cost:,.0f}</span>'
        f'</div>'
    )

    st.markdown(transfer_html, unsafe_allow_html=True)
