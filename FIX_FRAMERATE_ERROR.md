# 🔧 ERROR RESUELTO: "Error reinitializing filters" con carátula

## ❌ Error Reportado

```
[fc#0 @ 0000022cc64d1e00] Error reinitializing filters!
[fc#0 @ 0000022cc64d1e00] Task finished with error code: -22 (Invalid argument)
Error en codificación. Código de salida: 4294967274
```

---

## 🔍 Causa del Problema

El filtro `concat` de FFmpeg es **extremadamente estricto** con el formato de framerate. Ambos streams (carátula y video) deben tener **exactamente** el mismo formato.

### Lo que estaba pasando:

```bash
# Carátula generada con:
-framerate 23.976023976023978  # ← Número decimal (float)

# Filtro aplicado:
fps=24000/1001                 # ← Forma de fracción

# FFmpeg interpreta estos como DIFERENTES → ERROR -22
```

Aunque matemáticamente son equivalentes:
- `23.976023976023978` ≈ `24000/1001`

FFmpeg los ve como formatos diferentes y el filtro `concat` falla.

---

## ✅ Solución Implementada

### 1. **Framerate Consistente**

**Antes**:
```python
# Línea 358 (INCORRECTO)
fps_value = float(num) / float(den)  # Convierte a decimal
'-framerate', str(fps_value),        # 23.976023976023978

# Líneas 366, 369
f'fps={video_fps}'                   # 24000/1001
# ↑ INCONSISTENCIA → ERROR
```

**Ahora**:
```python
# Línea 358 (CORREGIDO)
'-framerate', video_fps,             # 24000/1001 (forma original)

# Líneas 366, 369
f'fps={video_fps}'                   # 24000/1001
# ↑ CONSISTENTE → ✓
```

### 2. **Sincronización de Timestamps**

Añadido `setpts=PTS-STARTPTS` para asegurar que ambos streams empiezan desde timestamp 0:

```python
# Línea 366 - Carátula
f'format=yuv420p,fps={video_fps},setpts=PTS-STARTPTS[cover];'

# Línea 369 - Video principal
f'format=yuv420p,fps={video_fps},setpts=PTS-STARTPTS[main];'

# Línea 370 - Concat
f'[cover][main]concat=n=2:v=1:a=0[vout]'
```

---

## 📊 Comparación Técnica

| Aspecto | Antes (Buggy) | Ahora (Corregido) |
|---------|---------------|-------------------|
| **-framerate** | 23.976023976023978 | 24000/1001 |
| **fps filter** | 24000/1001 | 24000/1001 |
| **Consistencia** | ❌ Diferentes | ✅ Idénticos |
| **setpts** | ❌ Sin setpts | ✅ PTS-STARTPTS |
| **Resultado** | Error -22 | ✓ Funciona |

---

## 🎯 Casos de Framerate Soportados

El script ahora maneja correctamente todos estos framerates:

| Framerate | Forma de Fracción | Decimal | Usado en |
|-----------|-------------------|---------|----------|
| 23.976 fps | 24000/1001 | 23.976023976... | Películas, TV |
| 29.97 fps | 30000/1001 | 29.970029970... | NTSC, TV USA |
| 24 fps | 24/1 o 24 | 24.0 | Cine |
| 25 fps | 25/1 o 25 | 25.0 | PAL, TV EU |
| 30 fps | 30/1 o 30 | 30.0 | Web, streams |
| 60 fps | 60/1 o 60 | 60.0 | Gaming, deportes |

**Nota**: El script usa automáticamente la forma original detectada por ffprobe.

---

## 🧪 Prueba del Fix

Para verificar que funciona con tu video problemático:

```bash
# 1. Descargar el nuevo script
git pull

# 2. Probar con el video que fallaba
python video_converter_fixed.py
```

Deberías ver:
```
[11:57:55] Configurando carátula a 23.976 fps para coincidir con el video
[11:57:55] Iniciando codificación con NVENC multipass...
[11:58:00] Progreso: 00:00:05.42
[11:58:05] Progreso: 00:00:10.84
...
[12:35:15] ✓ Transcodificación completada (1080p HD)
[12:35:15] ✓✓✓ COMPLETADO: The Mandalorian 2x08.mkv
```

---

## 🔧 Detalles Técnicos del Filtro

### Filtro Completo Generado:

```bash
# Input 0: Carátula (cover.jpg)
-loop 1
-framerate 24000/1001  # ← Ahora usa forma de fracción
-t 1
-i cover.jpg

# Input 1: Video original
-i video.mkv

# Filtro complex:
-filter_complex "\
[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,\
     pad=1920:1080:(ow-iw)/2:(oh-ih)/2,\
     format=yuv420p,\
     fps=24000/1001,\
     setpts=PTS-STARTPTS[cover];\
[1:v]scale=1920:1080:force_original_aspect_ratio=decrease,\
     pad=1920:1080:(ow-iw)/2:(oh-ih)/2,\
     format=yuv420p,\
     fps=24000/1001,\
     setpts=PTS-STARTPTS[main];\
[cover][main]concat=n=2:v=1:a=0[vout]"

-map [vout]
-map 1:a:0?
```

### Explicación de cada paso:

1. **scale**: Escala a 1920x1080 manteniendo aspecto
2. **pad**: Rellena con negro para mantener dimensiones exactas
3. **format=yuv420p**: Asegura formato de píxeles consistente
4. **fps=24000/1001**: Fuerza framerate exacto (DEBE ser idéntico en ambos)
5. **setpts=PTS-STARTPTS**: Resetea timestamps a 0 (evita problemas de sincronización)
6. **concat**: Une los dos streams (ahora con formato idéntico)

---

## ❓ Por Qué FFmpeg es Tan Estricto

El filtro `concat` necesita que los streams sean **bit-por-bit compatibles**:

- ✅ Mismo framerate (exactamente igual)
- ✅ Mismas dimensiones (1920x1080)
- ✅ Mismo formato de píxeles (yuv420p)
- ✅ Mismo timebase
- ✅ Timestamps consistentes

Si **cualquiera** de estos difiere, obtienes el error `-22 (Invalid argument)`.

---

## 📝 Otros Errores Relacionados que Esto Resuelve

Este fix también resuelve:

```
[vost#0:0/hevc_nvenc] Task finished with error code: -22
[AVFilterGraph @ ...] Error initializing filters
Cannot determine format of input stream
Conversion failed!
```

Todos estos errores están relacionados con inconsistencias en el filtro.

---

## 🎓 Lección Aprendida

Al trabajar con filtros de FFmpeg:

1. **Mantén formatos consistentes**: Si ffprobe devuelve `24000/1001`, usa eso en todas partes
2. **Usa setpts**: Siempre resetea timestamps cuando combinas streams
3. **Forma de fracción > decimal**: La forma de fracción es más precisa y evita errores de redondeo
4. **Testa con videos reales**: Los framerates "exóticos" (23.976, 29.97) son los que causan problemas

---

## 🚀 Próximos Pasos

1. **Descarga la versión actualizada**:
   ```bash
   git pull
   ```

2. **Vuelve a procesar los videos que fallaron**:
   - El script detectará que ya existen archivos procesados
   - Elimínalos manualmente si quieres reprocesarlos

3. **Reporta si encuentras más problemas**:
   - Incluye el framerate del video (`ffprobe -show_entries stream=r_frame_rate`)
   - Incluye el log completo del error

---

**Fecha de fix**: 2025-11-17
**Commit**: `43463e7`
**Archivos modificados**: `video_converter_fixed.py` (líneas 358, 366, 369)
