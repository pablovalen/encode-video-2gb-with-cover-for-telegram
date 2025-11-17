# 🎬 Conversor de Video H.265 NVENC - Versión Corregida

Script Python con interfaz gráfica para convertir videos a H.265/HEVC usando aceleración GPU NVIDIA, optimizado para Telegram (límite 2GB).

## 📋 Características

### ✅ Conversión Inteligente
- **Videos ≤ 2GB**: Remux sin recodificación (rápido, sin pérdida de calidad)
- **Videos > 2GB**: Recodificación a ~1.9GB con H.265 NVENC

### 🎯 Especificaciones Técnicas
- **Codec de video**: H.265/HEVC (NVENC - GPU acelerada)
- **Codec de audio**: AAC 256 kbps estéreo
- **Resolución máxima** (videos >2GB): 1080p HD (1920x1080)
- **Escalado**: Anamórfico automático (mantiene relación de aspecto)
- **Bitrate**: Calculado individualmente por video según duración
- **Carátula**: Incrustada 1 segundo al inicio (solo videos >2GB)

### 📁 Gestión de Archivos
- Replica estructura de directorios de origen → destino
- Soporta múltiples subdirectorios
- Busca carátulas automáticamente (cover.jpg, folder.png, etc.)
- Formatos de salida: MP4 o MKV

### 📝 Subtítulos
- **Prioridad**: Forzados en castellano
- **MP4**: Convierte a mov_text (máxima compatibilidad)
- **MKV**: Incluye todos los subtítulos originales

---

## 🔧 Requisitos

### Software
- Python 3.7+
- FFmpeg con soporte NVENC
- Drivers NVIDIA actualizados

### Hardware
- GPU NVIDIA compatible con NVENC:
  - Serie GTX 600 o superior
  - Serie RTX (todas)
  - Serie Tesla, Quadro (mayoría)

---

## 📦 Instalación

### 1. Instalar Python
Si no lo tienes instalado:
```bash
# Windows: Descargar de python.org
# Linux (Ubuntu/Debian):
sudo apt update
sudo apt install python3 python3-tk

# Linux (Fedora):
sudo dnf install python3 python3-tkinter
```

### 2. Instalar FFmpeg con NVENC

#### Windows:
1. Descargar FFmpeg de: https://www.gyan.dev/ffmpeg/builds/
2. Descargar versión "ffmpeg-git-full"
3. Extraer y añadir a PATH

#### Linux:
```bash
# Ubuntu/Debian (versión estática con NVENC):
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xf ffmpeg-release-amd64-static.tar.xz
sudo cp ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/
sudo cp ffmpeg-*-amd64-static/ffprobe /usr/local/bin/

# O instalar desde repositorio (puede no tener NVENC):
sudo apt install ffmpeg
```

### 3. Verificar instalación

Ejecuta el script de prueba:
```bash
python test_nvenc.py
```

Esto verificará:
- ✓ FFmpeg instalado correctamente
- ✓ Soporte NVENC disponible
- ✓ Opciones de codificación
- ✓ Prueba de codificación real

Si todo pasa, ¡estás listo! 🎉

---

## 🚀 Uso

### Interfaz Gráfica

1. **Ejecutar el script**:
   ```bash
   python video_converter_fixed.py
   ```

2. **Configurar directorios**:
   - **Origen**: Carpeta con tus videos (puede tener subdirectorios)
   - **Destino**: Donde se guardarán los videos convertidos

3. **Opciones**:
   - **Formato**: MP4 (máxima compatibilidad) o MKV (más características)
   - **Preset**:
     - **Fast**: Más rápido, ligeramente menor calidad
     - **Medium**: Balance óptimo (recomendado)

4. **Iniciar**: Click en "Iniciar Procesamiento"

5. **Monitorear**: Observa el log en tiempo real

### Estructura de Archivos Esperada

```
📁 Videos_Origen/
│
├── 📁 Pelicula_1/
│   ├── 🎬 pelicula.mkv (3.5GB)
│   └── 🖼️ cover.jpg
│
├── 📁 Pelicula_2/
│   ├── 🎬 video.mp4 (1.8GB)
│   └── 🖼️ folder.png
│
└── 📁 Serie_S01E01/
    ├── 🎬 episodio.mkv (4.2GB)
    └── 🖼️ Cover.jpeg

Después de procesar:

📁 Videos_Destino/
│
├── 📁 Pelicula_1/
│   ├── 🎬 pelicula.mkv (1.9GB) ← Recodificado con carátula
│   └── 🖼️ cover.jpg
│
├── 📁 Pelicula_2/
│   ├── 🎬 video.mp4 (1.8GB) ← Remuxeado (sin cambios)
│   └── 🖼️ folder.png
│
└── 📁 Serie_S01E01/
    ├── 🎬 episodio.mkv (1.9GB) ← Recodificado con carátula
    └── 🖼️ Cover.jpeg
```

---

## 🐛 Solución de Problemas

### ❌ Error: "FFmpeg no encontrado"
**Solución**:
1. Verifica instalación: `ffmpeg -version`
2. Añade FFmpeg al PATH del sistema
3. En Windows, reinicia el terminal después de añadir al PATH

### ❌ Error: "No se detectó soporte NVENC"
**Solución**:
1. Actualiza drivers NVIDIA: https://www.nvidia.com/Download/index.aspx
2. Verifica que tu GPU es compatible: https://developer.nvidia.com/video-encode-and-decode-gpu-support-matrix-new
3. Reinstala FFmpeg asegurándote que tiene soporte NVENC
4. Ejecuta: `ffmpeg -encoders | grep nvenc`

### ❌ Archivo final muy pequeño (80-90MB)
**Esto YA ESTÁ CORREGIDO en video_converter_fixed.py**

El problema era el parámetro `-cq` que ignoraba el bitrate. La versión corregida:
- ✓ Usa VBR puro sin `-cq`
- ✓ Respeta el bitrate calculado
- ✓ Genera archivos del tamaño correcto (~1.9GB)

### ❌ Carátula no aparece o está desincronizada
**Esto YA ESTÁ CORREGIDO en video_converter_fixed.py**

El problema era el framerate incompatible. La versión corregida:
- ✓ Detecta el framerate del video original
- ✓ Genera la carátula al mismo framerate
- ✓ Sincroniza correctamente con `concat`

### ⚠️ Proceso muy lento
**Opciones**:
1. Cambia preset a "Fast"
2. Verifica que está usando GPU (debe aparecer "NVENC" en log)
3. Cierra otros programas que usen la GPU

### ⚠️ Archivo final ligeramente diferente de 1.9GB
**Esto es normal**. El tamaño exacto depende de:
- Complejidad del video (escenas rápidas vs. estáticas)
- Duración exacta
- Contenido de la carátula

Rango aceptable: **1.7GB - 2.0GB** (±10%)

---

## 📊 Comparación de Versiones

| Aspecto | Versión Original | Versión Corregida |
|---------|-----------------|-------------------|
| **Tamaño final** | 80-90 MB ❌ | ~1.85-1.95 GB ✅ |
| **Carátula** | Desincronizada ❌ | Sincronizada ✅ |
| **Bitrate** | Ignorado ❌ | Respetado ✅ |
| **Framerate** | No detectado ❌ | Preservado ✅ |
| **Calidad** | Pésima ❌ | Excelente ✅ |

---

## 🎯 Ejemplos de Uso

### Ejemplo 1: Película 4K (4.5GB)
```
Entrada:
  - Tamaño: 4.5 GB
  - Resolución: 3840x2160 (4K)
  - Duración: 120 minutos
  - Formato: MKV

Salida:
  - Tamaño: ~1.9 GB
  - Resolución: 1920x1080 (1080p HD)
  - Duración: 120min + 1s (carátula)
  - Bitrate: ~2200 kbps
  - Formato: MKV
  - Carátula: 1s al inicio
```

### Ejemplo 2: Video HD (1.5GB)
```
Entrada:
  - Tamaño: 1.5 GB
  - Resolución: 1920x1080
  - Duración: 45 minutos
  - Formato: MP4

Salida (REMUX):
  - Tamaño: ~1.5 GB (sin cambios significativos)
  - Resolución: 1920x1080 (mantiene original)
  - Duración: 45 minutos (sin carátula)
  - Formato: MP4
  - Proceso: Rápido (solo remux)
```

---

## 📝 Archivos del Proyecto

```
📁 encode-video-2gb-with-cover-for-telegram/
│
├── 📄 video_converter_fixed.py    ← SCRIPT PRINCIPAL (USA ESTE)
├── 📄 test_nvenc.py               ← Script de verificación
├── 📄 README.md                   ← Este archivo
├── 📄 CORRECCIONES.md            ← Detalles técnicos de las correcciones
│
└── 📄 video_converter.py          ← Versión original (NO USAR)
```

---

## 🔍 Verificación Post-Proceso

Para verificar que un video se procesó correctamente:

```bash
# Ver tamaño e información
ffprobe -v error -show_entries format=size,duration,bit_rate -of json video.mkv

# Ver bitrate de video
ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate -of default=noprint_wrappers=1:nokey=1 video.mkv

# Reproducir primer segundo (verificar carátula)
ffplay -t 2 video.mkv
```

---

## 💡 Tips y Recomendaciones

1. **Haz pruebas primero**: Procesa 1-2 videos antes de procesar toda tu biblioteca
2. **Espacio en disco**: Asegúrate de tener suficiente espacio (original + convertido)
3. **Respaldo**: Mantén los originales hasta verificar la calidad
4. **Batch processing**: El script procesa todos los videos automáticamente
5. **Preset Medium**: Es el mejor balance calidad/velocidad para la mayoría de casos

---

## ❓ Preguntas Frecuentes

### ¿Por qué algunos videos no tienen carátula?
La carátula solo se añade a videos >2GB durante recodificación. Los videos ≤2GB se remuxean sin cambios.

### ¿Puedo cancelar el proceso?
Sí, click en "Detener". El video actual puede tardar en terminar.

### ¿Qué pasa si hay errores?
El script continúa con el siguiente video. Revisa el log para ver cuáles fallaron.

### ¿Se pierden subtítulos?
No. MP4 incluye el principal, MKV incluye todos.

### ¿Cuánto tarda?
Depende de:
- Duración del video
- Preset elegido
- Potencia de tu GPU

Ejemplo RTX 3050: ~10-15 min por hora de video (preset medium)

---

## 📜 Licencia

Este script es de uso libre para fines personales.

---

## 🤝 Contribuciones

Si encuentras bugs o tienes sugerencias:
1. Documenta el problema con ejemplos
2. Incluye el log completo del error
3. Especifica tu configuración (GPU, FFmpeg version, OS)

---

## 📞 Soporte

### Antes de reportar un problema:
1. ✅ Ejecuta `python test_nvenc.py`
2. ✅ Verifica que pasaste todas las pruebas
3. ✅ Lee la sección "Solución de Problemas"
4. ✅ Revisa el log completo del error

### Información necesaria para soporte:
- Versión de Python: `python --version`
- Versión de FFmpeg: `ffmpeg -version`
- GPU: `nvidia-smi` (en Windows/Linux)
- Sistema operativo
- Log completo del error

---

**¡Disfruta de tus videos optimizados para Telegram! 🚀**
