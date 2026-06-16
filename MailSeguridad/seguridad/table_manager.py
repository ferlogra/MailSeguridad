"""
table_manager — Registro centralizado de configuraciones de tablas.

Cada vista que muestra una tabla con selector de columnas, ordenación
multi-columna y guardado de configuraciones se registra aquí con un
único ``TableView`` que describe sus columnas, campos ordenables y etiquetas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpRequest


# ── Helpers ──────────────────────────────────────────────────────


def _parse_sort(raw: str, whitelist: list[str]) -> list[dict[str, str]]:
    """Parse ?sort=field1,-field2 into a list of {field, direction} dicts."""
    if not raw:
        return []
    spec: list[dict[str, str]] = []
    for p in (s.strip() for s in raw.split(",") if s.strip()):
        desc = p.startswith("-")
        name = p.lstrip("-")
        if name in whitelist:
            spec.append({"field": name, "direction": "desc" if desc else "asc"})
    return spec


def _spec_to_url(spec: list[dict[str, str]]) -> str:
    """Serialize a sort spec back to a URL query string."""
    return ",".join(
        f"-{s['field']}" if s["direction"] == "desc" else s["field"]
        for s in spec
    )


def _load_table_config(user, menu_option: str) -> dict | None:
    """Load the 'default' config for a user + menu_option, or None."""
    from .models import TableConfig

    try:
        config = TableConfig.objects.get(
            usuario=user, menu_option=menu_option, name="default"
        )
        return {
            "selected_fields": config.selected_fields,
            "sort_order": config.sort_order,
        }
    except TableConfig.DoesNotExist:
        return None


# ── SortInfo ─────────────────────────────────────────────────────


@dataclass
class SortInfo:
    """Metadata for a sortable column header."""

    field: str
    label: str
    is_sorted: bool = False
    order: int = 0
    direction: str = ""
    href_toggle: str = ""
    href_ctrl: str = ""
    href_ctrl_shift: str = ""


def build_sort_info(
    field: str, label: str, current_sort_raw: str, sort_fields: list[str],
    base_query_string: str = "",
) -> SortInfo:
    """Build SortInfo for one column given the current multi-column sort string.

    If *base_query_string* is provided, it is prepended to every sort href so
    that active filters are preserved across sort interactions.
    """
    spec = _parse_sort(current_sort_raw, sort_fields)

    def _href(sort_val: str = "") -> str:
        if not sort_val:
            return f"?{base_query_string}" if base_query_string else "?"
        if base_query_string:
            return f"?{base_query_string}&sort={sort_val}"
        return f"?sort={sort_val}"

    order = 0
    direction = ""
    for i, s in enumerate(spec):
        if s["field"] == field:
            order = i + 1
            direction = s["direction"]
            break

    is_sorted = order > 0

    if order == 1 and direction == "asc":
        href_toggle = _href(f"-{field}")
    elif order == 1 and direction == "desc":
        href_toggle = _href("")
    else:
        href_toggle = _href(field)

    if is_sorted:
        new_spec = [dict(s) for s in spec]
        for s in new_spec:
            if s["field"] == field:
                s["direction"] = "desc" if s["direction"] == "asc" else "asc"
        href_ctrl = _href(_spec_to_url(new_spec))
    else:
        href_ctrl = _href(
            _spec_to_url(spec + [{"field": field, "direction": "asc"}])
        )

    if is_sorted:
        new_spec = [dict(s) for s in spec]
        for s in new_spec:
            if s["field"] == field:
                s["direction"] = "desc" if s["direction"] == "asc" else "asc"
        href_ctrl_shift = _href(_spec_to_url(new_spec))
    else:
        href_ctrl_shift = _href(
            _spec_to_url(spec + [{"field": field, "direction": "desc"}])
        )

    return SortInfo(
        field=field,
        label=label,
        is_sorted=is_sorted,
        order=order,
        direction=direction,
        href_toggle=href_toggle,
        href_ctrl=href_ctrl,
        href_ctrl_shift=href_ctrl_shift,
    )


# ── TableView descriptor ────────────────────────────────────────


@dataclass
class TableView:
    """Configuration for a table-managed view.

    Attributes:
        menu_option: Key used for TableConfig DB lookups (e.g. 'mensajes_list').
        columns: Ordered dict mapping field_key → display label for ALL columns.
        sort_fields: List of field keys that are sortable.
        sort_labels: Dict mapping field_key → sort header label.
        default_cols: Default visible columns.
        paginate_by: Items per page (0 = no pagination).
        row_action_url_name: URL name for a detail view. When set, each row
            gets an action button in the first column that links to that URL
            with the record's PK.
    """

    menu_option: str
    columns: dict[str, str]
    sort_fields: list[str]
    sort_labels: dict[str, str] | None = None
    default_cols: list[str] | None = None
    paginate_by: int = 0
    row_action_url_name: str = ""

    def __post_init__(self):
        if self.sort_labels is None:
            self.sort_labels = {f: self.columns.get(f, f) for f in self.sort_fields}
        if self.default_cols is None:
            self.default_cols = list(self.sort_fields)


# ── Registry ────────────────────────────────────────────────────


class TableRegistry(dict[str, TableView]):
    def register(self, view: TableView) -> TableView:
        self[view.menu_option] = view
        return view


tables = TableRegistry()


# ── Column definitions ──────────────────────────────────────────


MENSAJES_ALL_COLS: dict[str, str] = {
    "id": "ID",
    "familia": "Familia",
    "id_principal": "ID principal",
    "grupo": "Grupo",
    "filtro": "Filtro",
    "asunto_resumen": "Asunto resumen",
    "estado": "Estado",
    "accion_tipo": "Acción / Tipo",
    "inc_relacionado": "INC relacionado",
    "cs_relacionado": "CS relacionado",
    "crq_asociado": "CRQ asociado",
    "ventana_o_fecha": "Ventana / Fecha",
    "ultimo_email": "Último email",
    "remitente_ultimo": "Remitente último",
    "num_mensajes": "Nº mensajes",
    "message_ids": "Message IDs",
    "outlook_urls": "URLs Outlook",
    "revision": "Revisión",
    "id_actuacion": "Id. Actuación",
}


# ── TipoActuaciones columns ──────────────────────


TIPO_ACTUACIONES_ALL_COLS: dict[str, str] = {
    "id_tipo_actuacion": "ID",
    "grupo": "Grupo",
    "orden": "Orden",
    "breve": "Breve",
    "amplio": "Amplio",
    "cierra": "Cierra",
}

# ── Actuaciones columns ──────────────────────────


ACTUACIONES_ALL_COLS: dict[str, str] = {
    "id_actuacion": "ID",
    "id_tipo_actuacion": "Tipo actuación",
    "id_user": "Usuario",
    "fecha_hora": "Fecha/Hora",
    "breve": "Breve",
    "amplio": "Amplio",
    "cierra": "Cierra",
}


# ── Register tables ─────────────────────────────────────────────


tables.register(TableView(
    menu_option="mensajes_list",
    columns=MENSAJES_ALL_COLS,
    sort_fields=[
        "id", "familia", "id_principal", "grupo", "estado",
        "accion_tipo", "num_mensajes", "ultimo_email", "revision",
        "id_actuacion",
    ],
    sort_labels={
        "id": "ID", "familia": "Familia", "id_principal": "ID principal",
        "grupo": "Grupo", "estado": "Estado",
        "accion_tipo": "Acción / Tipo",
        "num_mensajes": "Nº mensajes",
        "ultimo_email": "Último email",
        "revision": "Revisión",
        "id_actuacion": "Id. Actuación",
    },
    default_cols=[
        "id", "familia", "id_principal", "grupo", "asunto_resumen",
        "estado", "accion_tipo", "num_mensajes", "ultimo_email",
        "remitente_ultimo", "revision", "id_actuacion",
    ],
    paginate_by=50,
    row_action_url_name="mensaje_detail",
))

tables.register(TableView(
    menu_option="tipoactuaciones_list",
    columns=TIPO_ACTUACIONES_ALL_COLS,
    sort_fields=["id_tipo_actuacion", "grupo", "orden", "breve", "cierra"],
    sort_labels={
        "id_tipo_actuacion": "ID",
        "grupo": "Grupo",
        "orden": "Orden",
        "breve": "Breve",
        "cierra": "Cierra",
    },
    default_cols=["id_tipo_actuacion", "grupo", "orden", "breve", "amplio", "cierra"],
    paginate_by=50,
    row_action_url_name="tipoactuacion_detail",
))

tables.register(TableView(
    menu_option="actuaciones_list",
    columns=ACTUACIONES_ALL_COLS,
    sort_fields=["id_actuacion", "fecha_hora", "id_tipo_actuacion", "breve", "cierra"],
    sort_labels={
        "id_actuacion": "ID",
        "fecha_hora": "Fecha/Hora",
        "id_tipo_actuacion": "Tipo",
        "breve": "Breve",
        "cierra": "Cierra",
    },
    default_cols=["id_actuacion", "fecha_hora", "id_tipo_actuacion", "breve", "amplio", "cierra"],
    paginate_by=50,
    row_action_url_name="actuacion_detail",
))


# ── Public helpers ──────────────────────────────────────────────


def list_user_configs(user, menu_option: str) -> list[dict]:
    """Return saved configs for a user + menu_option as a list of dicts."""
    from .models import TableConfig

    configs = (
        TableConfig.objects.filter(usuario=user, menu_option=menu_option)
        .only("id", "name", "selected_fields", "sort_order", "size_columns")
        .order_by("name")
    )
    return [
        {
            "id": c.pk,
            "name": c.name,
            "selected_fields": c.selected_fields,
            "sort_order": c.sort_order,
            "size_columns": c.size_columns,
        }
        for c in configs
    ]


def build_table_context(
    request: HttpRequest,
    user: Any,
    cfg: TableView,
    base_query_string: str = "",
) -> dict[str, Any]:
    """Build the template context dict for a table-managed view.

    Returns keys: sort_info, all_cols, ordered_cols, current_sort, default_cols, sort_spec
    """
    current_sort_raw = request.GET.get("sort", "")
    sort_spec = _parse_sort(current_sort_raw, cfg.sort_fields)

    # Fall back to saved default config for sort order
    if not current_sort_raw:
        saved = _load_table_config(user, cfg.menu_option)
        if saved and saved.get("sort_order"):
            current_sort_raw = saved["sort_order"]
            sort_spec = _parse_sort(current_sort_raw, cfg.sort_fields)

    sort_info = {
        fld: build_sort_info(
            fld, cfg.sort_labels.get(fld, fld), current_sort_raw, cfg.sort_fields,
            base_query_string=base_query_string,
        )
        for fld in cfg.sort_fields
    }

    # Default visible columns: saved config → TableView default → all
    default_cols = (
        list(cfg.default_cols)
        if cfg.default_cols
        else list(cfg.columns.keys())
    )
    saved = _load_table_config(user, cfg.menu_option)
    if saved and saved.get("selected_fields"):
        default_cols = saved["selected_fields"]

    ordered_cols: dict[str, str] = {}
    for col in default_cols:
        if col in cfg.columns:
            ordered_cols[col] = cfg.columns[col]
    for col, label in cfg.columns.items():
        if col not in ordered_cols:
            ordered_cols[col] = label

    return {
        "sort_info": sort_info,
        "all_cols": cfg.columns,
        "ordered_cols": ordered_cols,
        "current_sort": current_sort_raw,
        "default_cols": default_cols,
        "sort_spec": sort_spec,
        "row_action_url_name": cfg.row_action_url_name,
    }


def paginate_queryset(
    request: HttpRequest,
    queryset: Any,
    paginate_by: int = 30,
) -> tuple[Any, Any, bool]:
    """Paginate a queryset using Django's Paginator."""
    if paginate_by <= 0:
        return queryset, None, False

    paginator = Paginator(queryset, paginate_by)
    page = request.GET.get("page", 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return page_obj.object_list, page_obj, page_obj.has_other_pages()


# ── Hyperlink rendering ────────────────────────────────────────────

# Matches =HYPERLINK("url","text") or =HYPERLINK("url", "text")
_HYPERLINK_RE = re.compile(
    r'=HYPERLINK\(\s*'
    r'"([^"]*)"'       # arg1: URL (double-quoted)
    r'\s*,\s*'
    r'"([^"]*)"'       # arg2: display text (double-quoted)
    r'\s*\)'
    r'|'               # OR — single-quoted variant
    r"=HYPERLINK\(\s*"
    r"'([^']*)'"       # arg1: URL (single-quoted)
    r"\s*,\s*"
    r"'([^']*)'"       # arg2: display text (single-quoted)
    r"\s*\)",
    re.IGNORECASE,
)


def render_hyperlinks(value: str | None) -> str:
    """Replace ``=HYPERLINK(url, text)`` patterns with HTML anchor tags.

    Returns the original string with all HYPERLINK formulas replaced by
    ``<a href="url" target="_blank" rel="noopener">text</a>``.
    Non-matching text is left untouched.
    """
    if not value:
        return value or ""

    def _replace(m: re.Match) -> str:
        # Groups 1/2 for double-quoted, 3/4 for single-quoted
        url = m.group(1) or m.group(3) or ""
        text = m.group(2) or m.group(4) or ""
        # Sanitise: escape quotes in attributes
        url_safe = url.replace('"', "&quot;").replace("'", "&#39;")
        text_safe = text.replace('"', "&quot;").replace("'", "&#39;")
        return f'<a class="hl-link" href="{url_safe}" target="_blank" rel="noopener">{text_safe}</a>'

    return _HYPERLINK_RE.sub(_replace, value)
