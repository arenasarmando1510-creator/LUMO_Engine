# ============================================================
# NOMBRE_ARCHIVO: /utils/date_utils.py
# ============================================================
# ============================================================
# date_utils.py – HELPERS DE FECHAS
# LUMO ENGINE v0.9 – CONGELADO
# ============================================================

from typing import Tuple, Optional

def parsear_fecha_simple(fecha_str: str, meses: dict) -> Optional[Tuple[int, int, int]]:
    fecha_str = fecha_str.replace("/", " ").replace("-", " ")
    partes = fecha_str.split()
    if len(partes) >= 3:
        try:
            dia = int(partes[0])
            mes_str = partes[1]
            año = int(partes[2])
            if mes_str in meses:
                return (dia, meses[mes_str], año)
        except:
            pass
    if len(partes) >= 2:
        try:
            mes_str = partes[0]
            dia = int(partes[1])
            if mes_str in meses:
                return (dia, meses[mes_str], 0)
        except:
            pass
    return None

def parsear_fecha(fecha_str: str) -> Optional[Tuple[int, int, int, int, int, int]]:
    meses = {
        "ene":1,"feb":2,"mar":3,"abr":4,"may":5,"jun":6,"jul":7,"ago":8,"sep":9,"oct":10,"nov":11,"dic":12,
        "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,"julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12
    }
    fecha_str = fecha_str.lower().strip()
    fecha_str = fecha_str.replace(" de ", " ").replace(" del ", " ")
    if " al " in fecha_str:
        partes = fecha_str.split(" al ")
        if len(partes) == 2:
            fecha1 = parsear_fecha_simple(partes[0].strip(), meses)
            fecha2 = parsear_fecha_simple(partes[1].strip(), meses)
            if fecha1 and fecha2:
                if fecha1[2] == 0:
                    fecha1 = (fecha1[0], fecha1[1], fecha2[2])
                return (fecha1[0], fecha1[1], fecha1[2], fecha2[0], fecha2[1], fecha2[2])
            return None
    fecha = parsear_fecha_simple(fecha_str, meses)
    if fecha:
        return (fecha[0], fecha[1], fecha[2], fecha[0], fecha[1], fecha[2])
    return None

def obtener_fecha_actual() -> str:
    from datetime import datetime
    return datetime.now().isoformat()

