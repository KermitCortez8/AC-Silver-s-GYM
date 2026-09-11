"""Solamente el administrador registra asistencia; cada cliente consulta la suya."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query

from dependencies import get_gym_service, require_roles
from models.attendance import AttendanceAnnulment, AttendanceCorrection, AttendanceFilters
from models.gym import AsistenciaEntradaInput, AsistenciaSalidaInput, CheckinAsistenciaDniInput, CheckinAsistenciaInput
from services.attendance_service import AttendanceService, AttendanceConflict, DAYS

router = APIRouter(prefix="/asistencia", tags=["asistencia"])
administrator = require_roles("admin")
reader = require_roles("admin", "user")


def service(gym=Depends(get_gym_service)):
    return AttendanceService(gym)


def run(action):
    try:
        return action()
    except AttendanceConflict as error:
        raise HTTPException(409, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except (RuntimeError, OSError) as error:
        raise HTTPException(503, "No se pudo guardar la asistencia. Comprueba la conexión y que se haya ejecutado backend/migrations/005_harden_attendance.sql en Supabase.") from error


@router.get("")
def list_attendance(user=Depends(reader), attendance=Depends(service)):
    return run(lambda: [row for row in attendance.records(user) if not row.get("anulado")])


@router.get("/historial")
def history(filters: AttendanceFilters = Depends(), page: int = Query(1, ge=1), page_size: int = Query(15, ge=1, le=100),
            user=Depends(reader), attendance=Depends(service)):
    rows = run(lambda: attendance.records(user, **filters.model_dump()))
    offset = (page - 1) * page_size
    return {"items": rows[offset:offset + page_size], "total": len(rows), "page": page, "page_size": page_size}


@router.get("/resumen")
def summary(user=Depends(administrator), attendance=Depends(service)):
    return attendance.summary(user)


@router.get("/exportar")
def export_history(filters: AttendanceFilters = Depends(), user=Depends(reader), attendance=Depends(service)):
    # Una sola lectura evita repetir u omitir filas si entran visitas mientras
    # el administrador descarga varias páginas del historial.
    return run(lambda: attendance.records(user, **filters.model_dump()))


@router.get("/cliente")
def lookup(dni: str = Query(pattern=r"^\d{8}$"), user=Depends(administrator), attendance=Depends(service)):
    return run(lambda: attendance.lookup(dni))


@router.get("/mi-semana")
def week(inicio: date | None = None, user=Depends(require_roles("user")), attendance=Depends(service)):
    start = inicio or attendance.now().date()
    start -= timedelta(days=start.weekday())
    end = start + timedelta(days=6)
    rows = run(lambda: attendance.records(user, desde=start, hasta=end))
    items = []
    for enrollment in attendance.gym.state.get("matriculas_horario", []):
        if enrollment.get("id_cliente") != user.id_cliente or enrollment.get("estado") != "ACTIVA":
            continue
        schedule = attendance.gym.get_horario_servicio(enrollment["id_horario_servicio"]) or {}
        if not schedule.get("activo") or schedule.get("dia") not in DAYS:
            continue
        day = (start + timedelta(days=DAYS.index(schedule["dia"]))).isoformat()
        if str(enrollment.get("fecha_matricula") or "")[:10] > day:
            continue
        record = next((r for r in rows if r.get("id_matricula") == enrollment["id_matricula"] and r["fecha"] == day), None)
        items.append({**schedule, "id_matricula": enrollment["id_matricula"], "fecha": day, "asistencia": record})
    return {"inicio": start.isoformat(), "fin": end.isoformat(), "hoy": attendance.now().date().isoformat(),
            "horarios": sorted(items, key=lambda i: (i["fecha"], i["hora_inicio"])), "visitas": len(rows)}


@router.post("/entrada")
def entry(payload: AsistenciaEntradaInput, user=Depends(administrator), attendance=Depends(service)):
    return run(lambda: attendance.enter(payload.model_dump(), user))


@router.post("/checkin")
def checkin(payload: CheckinAsistenciaInput, user=Depends(administrator), attendance=Depends(service)):
    return run(lambda: attendance.enter(payload.model_dump(), user))


@router.post("/checkin-dni")
def checkin_dni(payload: CheckinAsistenciaDniInput, user=Depends(administrator), attendance=Depends(service)):
    return run(lambda: attendance.enter(payload.model_dump(), user))


@router.post("/salida")
def exit_attendance(payload: AsistenciaSalidaInput, user=Depends(administrator), attendance=Depends(service)):
    return run(lambda: attendance.exit(payload.id_asistencia, user))


@router.put("/{record_id}")
def correct(record_id: int, payload: AttendanceCorrection, user=Depends(administrator), attendance=Depends(service)):
    return run(lambda: attendance.correct(record_id, payload.model_dump(mode="json"), user))


@router.post("/{record_id}/anular")
@router.delete("/{record_id}")
def annul(record_id: int, payload: AttendanceAnnulment, user=Depends(administrator), attendance=Depends(service)):
    return run(lambda: attendance.correct(record_id, payload.model_dump(), user, annul=True))
