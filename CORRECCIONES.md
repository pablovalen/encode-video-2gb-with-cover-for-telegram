# 🔧 CORRECCIONES APLICADAS AL SCRIPT

## ❌ Problemas Identificados y Solucionados

### 1. **PROBLEMA CRÍTICO: Archivos de 80-90MB en lugar de 1.9GB**
**Causa**: Uso incorrecto del parámetro `-cq` con `-b:v`

#### Código INCORRECTO (línea ~412):
```python
'-rc', 'vbr',
'-cq', '23',  # ← Esto hace que NVENC IGNORE el bitrate
'-b:v', f'{target_bitrate}k',  # ← Este valor es ignorado completamente
```

#### Código CORREGIDO:
```python
'-rc', 'vbr',  # Variable Bitrate
'-multipass', 'fullres',  # Multipass de NVENC
'-b:v', f'{target_bitrate}k',  # Bitrate target AHORA SÍ se respeta
'-maxrate', f'{int(target_bitrate * 1.3)}k',
'-bufsize', f'{int(target_bitrate * 2)}k',
'-spatial-aq', '1',  # Adaptive Quantization
'-temporal-aq', '1',
# NO usar -cq cuando quieres controlar el bitrate
```

**Explicación**:
- El parámetro `-cq` (Constant Quality) hace que NVENC funcione como CRF en x264
- Cuando usas `-cq`, el codificador **IGNORA** completamente el `-b:v`
- Para controlar el tamaño del archivo, debes usar **VBR puro sin -cq**

---

### 2. **PROBLEMA: Carátula con framerate incorrecto**
**Causa**: La carátula se generaba a 1fps pero el video podía ser 23.976, 24, 25, 30fps

#### Código INCORRECTO (línea ~396):
```python
'-loop', '1', '-framerate', '1', '-t', '1', '-i', cover_path,
# ...
f'[cover][main]concat=n=2:v=1:a=0[v]',  # ← Framerates incompatibles
```

#### Código CORREGIDO (línea ~508):
```python
# Detectar framerate del video original
fps_value = float(num) / float(den) if '/' in video_fps else float(video_fps)

# Generar carátula con el MISMO framerate del video
'-loop', '1',
'-framerate', str(fps_value),  # ← Ahora coincide con el video
'-t', '1',
'-i', cover_path,
# ...
f'[0:v]...fps={video_fps}[cover];'  # ← Forzar fps consistente
f'[1:v]...fps={video_fps}[main];'
f'[cover][main]concat=n=2:v=1:a=0[vout]',  # ← Ahora funciona correctamente
```

**Explicación**:
- El filtro `concat` requiere que ambas fuentes tengan el mismo framerate
- Ahora se detecta el framerate del video original y se aplica a la carátula
- Se añade filtro `fps` explícito para garantizar consistencia

---

### 3. **PROBLEMA: Cálculo de bitrate no incluía el segundo de carátula**
**Causa**: Se calculaba bitrate para la duración original, pero el video final duraba 1 segundo más

#### Código INCORRECTO (línea ~149):
```python
def calculate_bitrate(self, duration, target_size_kb):
    # Calcula para la duración original
    total_duration = duration  # ← No considera la carátula
    audio_size_kb = (256 * duration) / 8
```

#### Código CORREGIDO (línea ~149):
```python
def calculate_bitrate(self, duration, target_size_kb, has_cover=False):
    # CORRECCIÓN: Si hay carátula, añadir 1 segundo
    total_duration = duration + 1 if has_cover else duration
    audio_size_kb = (256 * total_duration) / 8  # ← Ahora incluye el segundo extra
```

**Impacto**:
- Video de 5627s + 1s carátula = 5628s total
- Antes: bitrate calculado para 5627s → archivo ligeramente menor
- Ahora: bitrate calculado para 5628s → archivo con tamaño correcto

---

### 4. **PROBLEMA: Uso de `-2pass` en lugar de `-multipass` de NVENC**
**Causa**: NVENC no soporta el sistema tradicional de 2-pass como x264/x265

#### Código INCORRECTO (línea ~309):
```python
'-2pass', '1',  # ← No funciona correctamente con NVENC
# Primera pasada...
'-2pass', '2',  # ← NVENC no implementa esto igual que software
```

#### Código CORREGIDO (línea ~555):
```python
'-multipass', 'fullres',  # ← Sistema nativo de NVENC para multipass
```

**Explicación**:
- NVENC tiene su propio sistema de análisis multipaso
- `-multipass fullres`: Análisis completo en resolución nativa
- `-multipass qres`: Análisis rápido en resolución reducida (más rápido, menor calidad)

---

### 5. **MEJORA: Eliminados filtros CUDA innecesarios**
**Causa**: Mezclar operaciones CPU/GPU causaba problemas de rendimiento

#### Código INCORRECTO (línea ~405):
```python
'-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda'
# ...
f'[1:v]hwdownload,format=yuv420p,...,hwupload_cuda[main];'
# ← Bajando de GPU a CPU y subiendo de nuevo (ineficiente)
```

#### Código CORREGIDO (línea ~545):
```python
# Procesamiento en CPU que es más estable para filtros complejos
f'[1:v]scale=...,format=yuv420p,fps={video_fps}[main];'
# ← Sin transfers GPU<->CPU innecesarios
```

**Explicación**:
- Para operaciones con concat y scale, es más estable procesar en CPU
- NVENC solo se usa para la codificación final (donde realmente importa)
- Evita transfers innecesarios que pueden causar problemas de sincronización

---

### 6. **MEJORA: Validación del tamaño final**

#### Código NUEVO (línea ~607):
```python
# Verificar si está cerca del objetivo (1900000 KB)
target_kb = 1900000
diff_percent = abs(output_size_kb - target_kb) / target_kb * 100

if diff_percent > 10:
    self.log(f"  ADVERTENCIA: El tamaño difiere del objetivo en {diff_percent:.1f}%")
    if output_size_kb < target_kb * 0.5:
        self.log(f"  El archivo es mucho más pequeño de lo esperado.")
else:
    self.log(f"  Tamaño dentro del rango objetivo (±10%)")
```

**Beneficio**: Alerta si el archivo final está muy lejos del objetivo esperado

---

### 7. **MEJORA: Mejor logging y seguimiento**

#### Código NUEVO (línea ~590):
```python
# Monitorear stderr para ver el progreso
last_progress = ""
for line in process.stderr:
    if 'frame=' in line and 'fps=' in line:
        if 'time=' in line:
            time_part = line.split('time=')[1].split()[0]
            if time_part != last_progress:
                last_progress = time_part
                self.log(f"Progreso: {time_part}")
```

**Beneficio**: Ahora puedes ver el progreso real de la codificación en tiempo real

---

### 8. **CORRECCIÓN: Detección de framerate del video**

#### Código NUEVO (línea ~96):
```python
'-show_entries', 'stream=width,height,duration,codec_name,pix_fmt,r_frame_rate',
# ...
fps = info['streams'][0].get('r_frame_rate', '30')
```

**Beneficio**: Ahora se detecta y preserva el framerate original del video

---

## 📊 RESULTADOS ESPERADOS

### Antes (con bugs):
```
Video de 5627s, 4K → Resultado: 80-90 MB ❌
- Bitrate ignorado por -cq
- Carátula con problemas de sincronización
- Tamaño muy por debajo del objetivo
```

### Ahora (corregido):
```
Video de 5627s, 4K → Resultado: ~1850-1950 MB ✅
- Bitrate respetado: 2445 kbps
- Carátula sincronizada a 1 segundo
- Tamaño cercano al objetivo de 1.9GB
- Calidad excelente en 1080p HD
```

---

## 🚀 CÓMO USAR EL SCRIPT CORREGIDO

1. **Ejecutar el nuevo script**:
   ```bash
   python video_converter_fixed.py
   ```

2. **Seleccionar directorios**:
   - Directorio origen: Carpeta con subdirectorios de videos
   - Directorio destino: Donde se guardarán los resultados

3. **Configurar opciones**:
   - Formato: MP4 o MKV
   - Preset: Fast o Medium

4. **Iniciar procesamiento**:
   - Click en "Iniciar Procesamiento"
   - Observa el log en tiempo real
   - Espera a que termine

---

## 🎯 PARÁMETROS CLAVE DE NVENC

### Para VBR con control de tamaño:
```bash
-c:v hevc_nvenc
-preset medium                    # Calidad de codificación
-rc vbr                          # Variable Bitrate
-multipass fullres               # Análisis multipaso
-b:v 2445k                       # Bitrate objetivo
-maxrate 3178k                   # Pico máximo (1.3x)
-bufsize 4890k                   # Buffer VBR (2x)
-spatial-aq 1                    # Calidad adaptativa espacial
-temporal-aq 1                   # Calidad adaptativa temporal
```

### ❌ NO usar juntos:
```bash
-cq 23        # Constant Quality (ignora bitrate)
-b:v 2445k    # Bitrate target (ignorado si hay -cq)
```

---

## 📝 NOTAS ADICIONALES

1. **Carátula**: Solo se añade en videos > 2GB durante transcodificación
2. **Remux**: Videos ≤ 2GB mantienen resolución original sin recodificar
3. **Audio**: Siempre AAC 256kbps estéreo
4. **Subtítulos**: Prioriza forzados en castellano
5. **Framerate**: Se preserva el original del video

---

## 🔍 VERIFICACIÓN

Para verificar que un video procesado está correcto:

```bash
# Ver información del video
ffprobe -v error -show_entries format=size,duration -of json video.mkv

# Ver bitrate real
ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate -of default=noprint_wrappers=1:nokey=1 video.mkv

# Ver si tiene la carátula en el primer segundo
ffmpeg -i video.mkv -ss 0 -t 2 -f null -
```

---

## ⚡ DIFERENCIAS PRINCIPALES

| Aspecto | Código Original | Código Corregido |
|---------|----------------|------------------|
| **Bitrate** | Ignorado por -cq | Respetado correctamente |
| **Tamaño final** | 80-90 MB | ~1850-1950 MB |
| **Carátula** | Desincronizada | Sincronizada correctamente |
| **Framerate** | No detectado | Detectado y preservado |
| **Multipass** | -2pass (no funciona) | -multipass (nativo NVENC) |
| **Duración** | Sin considerar carátula | Incluye +1s de carátula |
| **Logging** | Básico | Detallado con progreso |
| **Validación** | Sin validación | Valida tamaño final |

---

**Fecha de corrección**: 2025-11-17
**Versión**: 2.0 (Corregida)
