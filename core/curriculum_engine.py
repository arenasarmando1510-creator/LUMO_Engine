# ============================================================
# NOMBRE_ARCHIVO: /core/curriculum_engine.py
# ============================================================
# ============================================================
# curriculum_engine.py – MAPEO SEP/NEM
# LUMO ENGINE v0.9 – CONGELADO
# ============================================================

from typing import Dict, List

# ============================================================
# CAMPOS FORMATIVOS NEM
# ============================================================

CAMPOS_FORMATIVOS_NEM = {
    "SABERES": "Saberes y Pensamiento Científico",
    "LENGUAJES": "Lenguajes",
    "ETICA": "Ética, Naturaleza y Sociedades",
    "HUMANO": "De lo Humano y lo Comunitario"
}

# ============================================================
# CURRÍCULO BASE
# ============================================================

CURRICULUM_BASE = {
    "grado_1": {
        "temas": [
            {"tema": "Números", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Vocales", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Lectura", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Escritura", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Sumas", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Restas", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Formas", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Colores", "campo": "ETICA", "materia": "Artes"}
        ]
    },
    "grado_2": {
        "temas": [
            {"tema": "Números hasta 200", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Sumas/Restas", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Multiplicación", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Escritura", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Lectura", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Cuerpo humano", "campo": "HUMANO", "materia": "Ciencias"},
            {"tema": "Geografía", "campo": "ETICA", "materia": "Geografía"},
            {"tema": "Historia", "campo": "ETICA", "materia": "Historia"}
        ]
    },
    "grado_3": {
        "temas": [
            {"tema": "Multiplicación", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "División", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Fracciones", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Lectura comprensión", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Escritura", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Historia", "campo": "ETICA", "materia": "Historia"},
            {"tema": "Ciencias", "campo": "SABERES", "materia": "Ciencias"},
            {"tema": "Geografía", "campo": "ETICA", "materia": "Geografía"}
        ]
    },
    "grado_4": {
        "temas": [
            {"tema": "Operaciones combinadas", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Fracciones", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Decimales", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Lectura inferencial", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Escritura", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Historia", "campo": "ETICA", "materia": "Historia"},
            {"tema": "Geografía", "campo": "ETICA", "materia": "Geografía"},
            {"tema": "Ciencias", "campo": "SABERES", "materia": "Ciencias"}
        ]
    },
    "grado_5": {
        "temas": [
            {"tema": "Fracciones", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Decimales", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Álgebra básica", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Lectura crítica", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Redacción", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Historia", "campo": "ETICA", "materia": "Historia"},
            {"tema": "Geografía", "campo": "ETICA", "materia": "Geografía"},
            {"tema": "Ética", "campo": "ETICA", "materia": "Formación Cívica"}
        ]
    },
    "grado_6": {
        "temas": [
            {"tema": "Álgebra", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Ecuaciones", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Preálgebra", "campo": "SABERES", "materia": "Matemáticas"},
            {"tema": "Lectura crítica", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Redacción formal", "campo": "LENGUAJES", "materia": "Lengua Materna"},
            {"tema": "Historia universal", "campo": "ETICA", "materia": "Historia"},
            {"tema": "Geografía", "campo": "ETICA", "materia": "Geografía"},
            {"tema": "Ética", "campo": "ETICA", "materia": "Formación Cívica"}
        ]
    }
}

# ============================================================
# FUNCIONES DE CURRÍCULO
# ============================================================

def curriculum_mapper(grado: int, semana: int, tema: str = None) -> Dict:
    grado_key = f"grado_{grado}"
    if grado_key not in CURRICULUM_BASE:
        return {
            "grado": grado,
            "semana": semana,
            "tema": "Matemáticas y lenguaje",
            "campo_formativo": "Saberes y Pensamiento Científico",
            "materia": "Matemáticas",
            "proposito": "Fortalecer el pensamiento lógico-matemático"
        }
    
    temas_disponibles = CURRICULUM_BASE[grado_key]["temas"]
    if tema:
        for t in temas_disponibles:
            if t["tema"].lower() == tema.lower():
                return {
                    "grado": grado,
                    "semana": semana,
                    "tema": t["tema"],
                    "campo_formativo": CAMPOS_FORMATIVOS_NEM.get(t["campo"], t["campo"]),
                    "materia": t["materia"],
                    "proposito": f"Comprender y aplicar {t['tema'].lower()} en contextos cotidianos"
                }
    
    idx = (semana - 1) % len(temas_disponibles)
    t = temas_disponibles[idx]
    return {
        "grado": grado,
        "semana": semana,
        "tema": t["tema"],
        "campo_formativo": CAMPOS_FORMATIVOS_NEM.get(t["campo"], t["campo"]),
        "materia": t["materia"],
        "proposito": f"Comprender y aplicar {t['tema'].lower()} en contextos cotidianos"
    }

def obtener_tema(grado: int, semana: int) -> str:
    return curriculum_mapper(grado, semana)["tema"]

def generar_curriculum_completo() -> Dict:
    curriculum = {}
    for grado_key in CURRICULUM_BASE.keys():
        curriculum[grado_key] = {}
        for semana in range(1, 41):
            clave_semana = f"semana_{semana}"
            mapper = curriculum_mapper(int(grado_key.split("_")[1]), semana)
            curriculum[grado_key][clave_semana] = {
                "temas": [mapper["tema"]],
                "campo": [list(CAMPOS_FORMATIVOS_NEM.keys())[0]],
                "nodo": f"Semana_{semana}_{mapper['campo_formativo']}"
            }
    return curriculum

