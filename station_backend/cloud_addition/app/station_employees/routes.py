import json
import os
import urllib.error
import urllib.parse
import urllib.request

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy import select

from app.core.roles import normalize_role
from app.core.tenant import tenant_context, visible_station_ids
from app.extensions import get_session
from app.models import Station


station_employees = Blueprint("station_employees", __name__)
WRITE_ROLES = {"Super Admin", "Company Admin", "Station Admin"}


def _role():
    return normalize_role(session.get("unified_role", "Viewer"))


def _require_write():
    if _role() not in WRITE_ROLES:
        abort(403)


def _visible_stations():
    ids = visible_station_ids()
    if not ids:
        return []
    return get_session().scalars(
        select(Station)
        .where(Station.id.in_(ids), Station.deleted_at.is_(None))
        .order_by(Station.name_ar)
    ).all()


def _selected_station(stations):
    raw = request.values.get("station_id") or session.get("station_id")
    if raw:
        for station in stations:
            if str(station.id) == str(raw) or station.station_id == str(raw):
                tenant_context().authorize_station(station)
                return station
    return stations[0] if len(stations) == 1 else None


def _backend(method, path, *, query=None, payload=None):
    token = os.getenv("STATION_APP_INTERNAL_TOKEN", "")
    if not token:
        raise RuntimeError("STATION_APP_INTERNAL_TOKEN_NOT_CONFIGURED")
    base = os.getenv("STATION_APP_INTERNAL_URL", "http://127.0.0.1:18092").rstrip("/")
    url = base + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "X-Station-Internal-Token": token,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        try:
            error = json.loads(exc.read()).get("error", "BACKEND_REQUEST_FAILED")
        except (ValueError, AttributeError):
            error = "BACKEND_REQUEST_FAILED"
        raise RuntimeError(error) from exc


@station_employees.get("/station-employees")
def index():
    _require_write()
    stations = _visible_stations()
    station = _selected_station(stations)
    employees = []
    totals = []
    recent = []
    backend_error = None
    if station:
        try:
            employees = _backend(
                "GET", "/internal/v1/employees", query={"station_id": station.id}
            ).get("employees", [])
            sales = _backend(
                "GET",
                "/internal/v1/employee-sales",
                query={"station_id": station.id},
            )
            totals = sales.get("totals", [])
            recent = sales.get("recent", [])
        except RuntimeError as exc:
            backend_error = str(exc)
    return render_template(
        "unified/station_employees/index.html",
        stations=stations,
        selected_station=station,
        employees=employees,
        totals=totals,
        recent_sales=recent,
        backend_error=backend_error,
        current_station=station,
        current_role=_role().lower().replace(" ", "_"),
    )


@station_employees.post("/station-employees/create")
def create_employee():
    _require_write()
    stations = _visible_stations()
    station = _selected_station(stations)
    if station is None:
        abort(400, "station_id is required")
    payload = {
        "stationId": station.id,
        "name": request.form.get("name", ""),
        "password": request.form.get("password", ""),
        "createdByUserId": session.get("unified_user_id"),
    }
    try:
        _backend("POST", "/internal/v1/employees", payload=payload)
        flash("تم إنشاء حساب موظف المحطة بنجاح.", "success")
    except RuntimeError as exc:
        flash(_message(str(exc)), "error")
    return redirect(url_for("station_employees.index", station_id=station.id))


@station_employees.post("/station-employees/<employee_id>/toggle")
def toggle_employee(employee_id):
    _require_write()
    stations = _visible_stations()
    station = _selected_station(stations)
    if station is None:
        abort(400, "station_id is required")
    visible = _backend(
        "GET", "/internal/v1/employees", query={"station_id": station.id}
    ).get("employees", [])
    employee = next((item for item in visible if item.get("id") == employee_id), None)
    if employee is None:
        abort(404)
    _backend(
        "PATCH",
        f"/internal/v1/employees/{employee_id}",
        payload={"enabled": not bool(employee.get("enabled"))},
    )
    flash("تم تحديث حالة الحساب.", "success")
    return redirect(url_for("station_employees.index", station_id=station.id))


def _message(code):
    return {
        "PASSWORD_ALREADY_ASSIGNED": "كلمة المرور مستخدمة لموظف آخر؛ اختر كلمة مختلفة.",
        "PASSWORD_LENGTH_INVALID": "كلمة المرور يجب أن تكون من 6 إلى 128 حرفًا.",
        "INVALID_EMPLOYEE_NAME": "أدخل اسم الموظف بصورة صحيحة.",
        "STATION_APP_INTERNAL_TOKEN_NOT_CONFIGURED": "خدمة تطبيق المحطة غير مهيأة بعد.",
    }.get(code, f"تعذر تنفيذ العملية: {code}")

