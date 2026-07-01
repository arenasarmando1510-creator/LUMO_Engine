# ============================================================
# NOMBRE_ARCHIVO: /core/acc_controller.py
# ============================================================
# ============================================================
# acc_controller.py – META-CONTROL DE DIFICULTAD (ACC + TCC)
# LUMO ENGINE v0.9 – CONGELADO
# ============================================================

from datetime import datetime
from typing import Dict, List, Optional
from core.curriculum_engine import obtener_tema
from utils.date_utils import parsear_fecha

# ============================================================
# ACC (Adaptive Compression Core) – DIFICULTAD ADAPTATIVA
# ============================================================

def calcular_acc(error_count: int, aciertos: int) -> str:
    if error_count >= 3:
        return "ACC_1"
    elif error_count == 2:
        return "ACC_2"
    elif error_count == 1:
        return "ACC_3"
    elif aciertos >= 3:
        return "ACC_4"
    else:
        return "ACC_3"

def calcular_acc_mejorado(error_count: int, aciertos: int, intentos: int = 0) -> Dict:
    if error_count >= 3:
        return {"nivel": "ACC_1", "dificultad": 1, "tipo_ejercicio": "reconocimiento", "ayuda_nivel": "maxima"}
    elif error_count == 2:
        return {"nivel": "ACC_2", "dificultad": 1, "tipo_ejercicio": "basica", "ayuda_nivel": "guiada"}
    elif error_count == 1:
        return {"nivel": "ACC_3", "dificultad": 2, "tipo_ejercicio": "aplicacion", "ayuda_nivel": "estandar"}
    elif aciertos >= 3:
        return {"nivel": "ACC_4", "dificultad": 3, "tipo_ejercicio": "transferencia", "ayuda_nivel": "minima"}
    else:
        return {"nivel": "ACC_3", "dificultad": 2, "tipo_ejercicio": "basica", "ayuda_nivel": "estandar"}

def generar_explicacion_segun_acc(tema: str, nivel_acc: str, error_count: int) -> str:
    if nivel_acc == "ACC_1":
        return f"🌈 Vamos a empezar desde cero, sin presiones...\n\n🎨 Piensa en algo que ya sepas: {tema} es como contar tus dedos.\n\n👣 Sigamos juntos paso a paso:\n   1. Mira tus manos\n   2. Cuenta despacio\n   3. Dime qué ves"
    elif nivel_acc == "ACC_2":
        return f"🔍 Vamos a verlo paso a paso...\n\n📖 PASO 1: Imagina que tienes objetos que conoces\n🔢 PASO 2: Dividamos el problema en partes chiquitas\n✨ PASO 3: Fíjate bien en cada número"
    elif nivel_acc == "ACC_4":
        return f"🌟 ¡Vas increíble! Ahora un pequeño desafío...\n\n¿Puedes explicarme con tus palabras cómo se relaciona {tema} con algo que viste hoy en casa? 🏠"
    else:
        return f"📚 Repasemos {tema}. Observa bien los números y dime qué piensas. 💭"

# ============================================================
# TCC – TEMPORAL CURRICULUM COMPRESSION
# ============================================================

class TCC_MOTOR:
    def __init__(self):
        self.activo = False
        self.tipo = None
        self.dias_totales = 0
        self.tasa_compresion = 1.0
        self.semanas_sep = 0
        self.temas_comprimidos = []
        self.mensaje_usuario = ""
        self.fecha_inicio = None
        self.fecha_fin = None
        self.grado = 1
        self.modo = "BASIC"
        self.mision = None
    
    def activar(self, state: dict, memory: dict) -> Dict:
        self.modo = state.get("modo", "BASIC")
        self.mision = state.get("mision")
        self.grado = state.get("grado_num", 1)
        fecha_inicio_str = state.get("fecha_inicio_str", "")
        fecha_fin_str = state.get("fecha_fin_str", "")
        self.mensaje_usuario = ""
        
        if self.modo == "BASIC" and self.mision in ["A", "B"]:
            hoy = datetime.now().date()
            fin = self._parsear_fecha(fecha_fin_str)
            if fin and fin > hoy:
                self.dias_totales = (fin - hoy).days
                self.activo = True
                self.tipo = "futuro"
                self.fecha_inicio = hoy
                self.fecha_fin = fin
                self.semanas_sep = self._calcular_semanas_sep(self.grado, hoy, fin)
                self.tasa_compresion = self._calcular_tasa_compresion(self.dias_totales, self.semanas_sep)
                self.temas_comprimidos = self._consultar_curriculum_entre_fechas(self.grado, hoy, fin)
                self.mensaje_usuario = f"📊 {self.semanas_sep} semanas en {self.dias_totales} días."
                return self._generar_config()
            self.mensaje_usuario = "✅ Curso estándar."
            return self._generar_config()
        
        elif self.modo == "INTENSIVE" and self.mision in ["A", "B", "D"]:
            inicio = self._parsear_fecha(fecha_inicio_str)
            fin = self._parsear_fecha(fecha_fin_str)
            if inicio and fin and fin > inicio:
                self.dias_totales = (fin - inicio).days
                self.activo = True
                self.tipo = "elastico"
                self.fecha_inicio = inicio
                self.fecha_fin = fin
                self.semanas_sep = self._calcular_semanas_sep(self.grado, inicio, fin)
                self.tasa_compresion = self._calcular_tasa_compresion(self.dias_totales, self.semanas_sep)
                self.temas_comprimidos = self._consultar_curriculum_entre_fechas(self.grado, inicio, fin)
                self.mensaje_usuario = f"📊 {self.semanas_sep} semanas en {self.dias_totales} días."
                return self._generar_config()
            self.mensaje_usuario = "✅ Curso estándar."
            return self._generar_config()
        
        self.mensaje_usuario = "✅ Misión seleccionada."
        return self._generar_config()
    
    def _generar_config(self) -> Dict:
        return {
            "activo": self.activo,
            "tipo": self.tipo,
            "dias_totales": self.dias_totales,
            "tasa_compresion": round(self.tasa_compresion, 2),
            "temas_comprimidos": self.temas_comprimidos[:10],
            "semanas_sep": self.semanas_sep,
            "mensaje": self.mensaje_usuario,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_fin": self.fecha_fin.isoformat() if self.fecha_fin else None,
        }
    
    def _calcular_tasa_compresion(self, dias_totales: int, semanas_sep: int) -> float:
        if dias_totales <= 0 or semanas_sep <= 0:
            return 1.0
        tasa = (semanas_sep * 7) / dias_totales
        return min(tasa, 4.0)
    
    def _calcular_semanas_sep(self, grado: int, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        semanas = (fecha_fin - fecha_inicio).days // 7
        return max(1, min(semanas, 40))
    
    def _consultar_curriculum_entre_fechas(self, grado: int, fecha_inicio: datetime, fecha_fin: datetime) -> List[str]:
        temas = []
        semanas_totales = (fecha_fin - fecha_inicio).days // 7
        for i in range(min(semanas_totales, 40)):
            tema = obtener_tema(grado, i + 1)
            if tema not in temas:
                temas.append(tema)
        return temas
    
    def _parsear_fecha(self, fecha_str: str) -> Optional[datetime]:
        if not fecha_str:
            return None
        try:
            resultado = parsear_fecha(fecha_str)
            if resultado:
                if len(resultado) == 6:
                    return datetime(resultado[2], resultado[1], resultado[0])
                return datetime(resultado[2], resultado[1], resultado[0])
        except:
            pass
        return None

