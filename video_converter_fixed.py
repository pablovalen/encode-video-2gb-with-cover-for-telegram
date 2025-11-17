import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import subprocess
import json
import threading
import time
from pathlib import Path
import shutil
from datetime import datetime

class VideoConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Video H265 NVEnc")
        self.root.geometry("900x700")

        # Variables
        self.source_dir = tk.StringVar()
        self.dest_dir = tk.StringVar()
        self.output_format = tk.StringVar(value="mkv")
        self.preset = tk.StringVar(value="medium")
        self.is_processing = False

        self.setup_ui()

    def setup_ui(self):
        # Frame principal - Usar tk.Frame en lugar de ttk.Frame para tener acceso a rowconfigure
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Directorio origen
        ttk.Label(main_frame, text="Directorio de Origen:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.source_dir, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(main_frame, text="Buscar", command=self.select_source_dir).grid(row=0, column=2, padx=5)

        # Directorio destino
        ttk.Label(main_frame, text="Directorio de Destino:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.dest_dir, width=60).grid(row=1, column=1, padx=5)
        ttk.Button(main_frame, text="Buscar", command=self.select_dest_dir).grid(row=1, column=2, padx=5)

        # Opciones
        options_frame = ttk.LabelFrame(main_frame, text="Opciones de Conversión", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=5)

        # Formato de salida
        ttk.Label(options_frame, text="Formato de salida:").grid(row=0, column=0, sticky=tk.W)
        format_frame = ttk.Frame(options_frame)
        format_frame.grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(format_frame, text="MP4", variable=self.output_format, value="mp4").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="MKV", variable=self.output_format, value="mkv").pack(side=tk.LEFT, padx=5)

        # Preset
        ttk.Label(options_frame, text="Preset del codificador:").grid(row=1, column=0, sticky=tk.W, pady=5)
        preset_frame = ttk.Frame(options_frame)
        preset_frame.grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(preset_frame, text="Fast", variable=self.preset, value="fast").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(preset_frame, text="Medium", variable=self.preset, value="medium").pack(side=tk.LEFT, padx=5)

        # Información
        info_frame = ttk.LabelFrame(main_frame, text="Información de Procesamiento", padding="10")
        info_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=5)

        info_text = """• Videos ≤ 2GB: Remux sin recodificación (preserva calidad y resolución original)
• Videos > 2GB: Recodificación H.265 a ~1.95GB con límite 1080p HD (1920x1080)
• Escalado anamórfico automático (mantiene relación de aspecto)
• Codec de video: H265 NVEnc (GPU NVIDIA)
• Codec de audio: AAC 256kbps
• Subtítulos: Prioriza forzados en castellano
• Carátula incrustada en videos transcodificados (1 segundo al inicio)"""

        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(padx=10, pady=5)

        # Botones de control
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=3, pady=10)

        self.start_btn = ttk.Button(control_frame, text="Iniciar Procesamiento",
                                    command=self.start_processing)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="Detener",
                                   command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log de Procesamiento", padding="5")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10, padx=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configurar expansión de columnas y filas
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)

    def log(self, message):
        """Añadir mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def select_source_dir(self):
        directory = filedialog.askdirectory(title="Seleccionar directorio de origen")
        if directory:
            self.source_dir.set(directory)
            self.log(f"Directorio origen seleccionado: {directory}")

    def select_dest_dir(self):
        directory = filedialog.askdirectory(title="Seleccionar directorio de destino")
        if directory:
            self.dest_dir.set(directory)
            self.log(f"Directorio destino seleccionado: {directory}")

    def get_video_info(self, video_path):
        """Obtener información del video usando ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,duration,codec_name,pix_fmt,r_frame_rate',
                '-show_entries', 'format=duration,size',
                '-of', 'json',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if result.returncode != 0:
                self.log(f"Error ffprobe: {result.stderr}")
                return None

            info = json.loads(result.stdout)

            # Obtener duración del format o del stream
            duration = None
            if 'format' in info and 'duration' in info['format']:
                duration = float(info['format']['duration'])
            elif 'streams' in info and len(info['streams']) > 0:
                if 'duration' in info['streams'][0]:
                    duration = float(info['streams'][0]['duration'])

            if duration is None or duration == 0:
                self.log(f"Advertencia: No se pudo obtener la duración del video")
                duration = 1  # Valor por defecto para evitar división por cero

            size = int(info['format'].get('size', 0))

            # Obtener dimensiones del video
            width = 1920
            height = 1080
            fps = "30"
            if 'streams' in info and len(info['streams']) > 0:
                width = info['streams'][0].get('width', 1920)
                height = info['streams'][0].get('height', 1080)
                fps = info['streams'][0].get('r_frame_rate', '30')

            return {
                'duration': duration,
                'size': size,
                'size_kb': size // 1024,
                'width': width,
                'height': height,
                'fps': fps
            }
        except Exception as e:
            self.log(f"Error obteniendo info del video: {e}")
            return None

    def find_cover(self, directory):
        """Buscar archivo de carátula en el directorio"""
        cover_names = ['cover', 'folder', 'Cover', 'Folder', 'COVER', 'FOLDER']
        extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']

        for name in cover_names:
            for ext in extensions:
                cover_path = os.path.join(directory, name + ext)
                if os.path.exists(cover_path):
                    self.log(f"Carátula encontrada: {os.path.basename(cover_path)}")
                    return cover_path
        return None

    def calculate_bitrate(self, duration, target_size_kb, has_cover=False):
        """Calcular bitrate necesario para alcanzar el tamaño objetivo

        Args:
            duration: Duración del video original en segundos
            target_size_kb: Tamaño objetivo en KB
            has_cover: Si se va a añadir 1 segundo de carátula
        """
        # CORRECCIÓN: Si hay carátula, añadir 1 segundo a la duración total
        total_duration = duration + 1 if has_cover else duration

        # Reservar espacio para audio (256 kbps)
        audio_size_kb = (256 * total_duration) / 8
        video_size_kb = target_size_kb - audio_size_kb

        # Calcular bitrate de video en kbps
        video_bitrate = (video_size_kb * 8) / total_duration

        # Limitar el bitrate máximo y mínimo
        video_bitrate = max(500, min(video_bitrate, 50000))  # Entre 500 kbps y 50 Mbps

        return int(video_bitrate)

    def get_subtitle_tracks(self, video_path):
        """Obtener información de pistas de subtítulos"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 's',
                '-show_entries', 'stream=index,codec_name:stream_tags=language,title',
                '-of', 'json',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if result.returncode != 0:
                return []

            info = json.loads(result.stdout)

            subtitles = []
            for stream in info.get('streams', []):
                tags = stream.get('tags', {})
                subtitle = {
                    'index': stream['index'],
                    'codec': stream.get('codec_name', ''),
                    'language': tags.get('language', 'und'),
                    'title': tags.get('title', ''),
                    'forced': 'forced' in tags.get('title', '').lower() or
                             tags.get('forced', '0') == '1'
                }
                subtitles.append(subtitle)

            # Ordenar: forzados en castellano primero
            subtitles.sort(key=lambda x: (
                not (x['forced'] and x['language'] in ['spa', 'es', 'esp', 'spanish']),
                not x['forced'],
                x['language'] not in ['spa', 'es', 'esp', 'spanish']
            ))

            return subtitles
        except Exception as e:
            self.log(f"Error obteniendo subtítulos: {e}")
            return []

    def remux_video(self, input_path, output_path, output_format):
        """Remuxear video sin recodificación - Para archivos ≤ 2GB"""
        self.log(f"Iniciando remux (preservando resolución original)")

        cmd = ['ffmpeg', '-i', input_path]

        # Mapear streams
        cmd.extend([
            '-map', '0:v',  # Video
            '-map', '0:a?',  # Audio (opcional)
        ])

        # Configuración de video y audio
        cmd.extend([
            '-c:v', 'copy',  # Copiar video sin recodificar
            '-c:a', 'aac',   # Convertir audio a AAC
            '-b:a', '256k',
        ])

        # Gestión de subtítulos
        subtitles = self.get_subtitle_tracks(input_path)
        if subtitles:
            if output_format == 'mp4':
                # Solo incluir el primer subtítulo (preferentemente forzado en castellano)
                cmd.extend(['-map', '0:s:0?', '-c:s', 'mov_text'])
            else:  # mkv
                # Incluir todos los subtítulos
                cmd.extend(['-map', '0:s?', '-c:s', 'copy'])

        # Opciones específicas del formato
        if output_format == 'mp4':
            cmd.extend(['-movflags', '+faststart'])

        cmd.extend(['-y', output_path])

        try:
            self.log(f"Ejecutando remux...")
            process = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if process.returncode == 0:
                output_size = os.path.getsize(output_path) / (1024 * 1024)
                self.log(f"✓ Remux completado: {os.path.basename(output_path)} ({output_size:.1f} MB)")
                return True
            else:
                self.log(f"Error en remux: {process.stderr}")
                return False
        except Exception as e:
            self.log(f"Error ejecutando remux: {e}")
            return False

    def transcode_video_with_cover_fallback(self, input_path, output_path, output_format, video_info, cover_path):
        """Método alternativo: Generar video de carátula temporalmente y concatenar archivos

        Este método es más lento pero más robusto cuando el filtro concat falla
        """
        self.log(f"Usando método alternativo: concatenación de archivos")

        import tempfile

        duration = video_info['duration']
        has_cover = cover_path is not None and os.path.exists(cover_path)
        target_bitrate = self.calculate_bitrate(duration, 1900000, has_cover=has_cover)

        video_fps = video_info.get('fps', '30')
        output_width = 1920
        output_height = 1080

        try:
            # Paso 1: Generar video temporal de la carátula (1 segundo)
            temp_cover_video = tempfile.NamedTemporaryFile(suffix='.mkv', delete=False).name

            self.log(f"Generando video temporal de carátula...")
            cmd_cover = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', cover_path,
                '-vf', f'scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,'
                       f'pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2,fps={video_fps}',
                '-t', '1',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-pix_fmt', 'yuv420p',
                '-an',  # Sin audio
                temp_cover_video
            ]

            result = subprocess.run(cmd_cover, capture_output=True, text=True, encoding='utf-8')
            if result.returncode != 0:
                self.log(f"Error generando video de carátula: {result.stderr[:500]}")
                if os.path.exists(temp_cover_video):
                    os.remove(temp_cover_video)
                return False

            # Paso 2: Crear archivo de lista para concat demuxer
            temp_list = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8').name

            with open(temp_list, 'w', encoding='utf-8') as f:
                # Escapar rutas para Windows
                cover_escaped = temp_cover_video.replace('\\', '/').replace("'", "'\\''")
                input_escaped = input_path.replace('\\', '/').replace("'", "'\\''")
                f.write(f"file '{cover_escaped}'\n")
                f.write(f"file '{input_escaped}'\n")

            self.log(f"Concatenando carátula + video y transcodificando con NVENC...")

            # Paso 3: Concatenar y transcodificar
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', temp_list,
                '-i', input_path,  # Input adicional solo para audio/subtítulos
                '-map', '0:v',  # Video del concat
                '-map', '1:a:0?',  # Audio del original
            ]

            # Subtítulos
            subtitles = self.get_subtitle_tracks(input_path)
            if output_format == 'mkv' and subtitles:
                cmd.extend(['-map', '1:s?', '-c:s', 'copy'])
            elif output_format == 'mp4' and subtitles:
                cmd.extend(['-map', '1:s:0?', '-c:s', 'mov_text'])

            # Codificación NVENC
            cmd.extend([
                '-vf', f'scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,'
                       f'pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2',
                '-c:v', 'hevc_nvenc',
                '-preset', self.preset.get(),
                '-profile:v', 'main',
                '-tier', 'high',
                '-rc', 'vbr',
                '-b:v', f'{target_bitrate}k',
                '-maxrate', f'{int(target_bitrate * 1.3)}k',
                '-bufsize', f'{int(target_bitrate * 2)}k',
                '-c:a', 'aac',
                '-b:a', '256k',
                '-ac', '2'
            ])

            if output_format == 'mp4':
                cmd.extend(['-movflags', '+faststart'])

            cmd.append(output_path)

            process = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

            # Limpiar archivos temporales
            if os.path.exists(temp_cover_video):
                os.remove(temp_cover_video)
            if os.path.exists(temp_list):
                os.remove(temp_list)

            if process.returncode == 0:
                output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                self.log(f"✓ Transcodificación completada (método alternativo)")
                self.log(f"  Tamaño final: {output_size_mb:.1f} MB")
                return True
            else:
                self.log(f"Error en método alternativo: {process.stderr[:1000]}")
                return False

        except Exception as e:
            self.log(f"Error en método alternativo: {e}")
            return False

    def transcode_video(self, input_path, output_path, output_format, video_info, cover_path):
        """Transcodificar video con H265 NVEnc optimizado - Para archivos > 2GB

        CORRECCIONES IMPLEMENTADAS:
        1. Eliminado -cq para usar VBR con bitrate target correcto
        2. Cálculo de bitrate incluye el segundo de la carátula
        3. Filtro concat con framerate igualado y número exacto de frames
        4. Uso de -multipass de NVENC en lugar de -2pass
        5. Filtros simplificados para evitar problemas CPU/GPU
        6. Método de respaldo si concat filter falla
        """
        self.log(f"Iniciando transcodificación NVENC: {os.path.basename(input_path)}")

        duration = video_info['duration']
        has_cover = cover_path is not None and os.path.exists(cover_path)

        # CORRECCIÓN: Calcular bitrate incluyendo el segundo de carátula si existe
        target_bitrate = self.calculate_bitrate(duration, 1900000, has_cover=has_cover)

        if has_cover:
            self.log(f"Bitrate objetivo: {target_bitrate} kbps (calculado para {duration:.1f}s + 1s carátula)")
        else:
            self.log(f"Bitrate objetivo: {target_bitrate} kbps (calculado para {duration:.1f}s)")

        # Para videos > 2GB, SIEMPRE limitar a 1080p HD
        video_width = video_info['width']
        video_height = video_info['height']
        video_fps = video_info.get('fps', '30')

        # SIEMPRE escalar a máximo 1920x1080 para videos > 2GB
        output_width = 1920
        output_height = 1080

        self.log(f"Resolución original: {video_width}x{video_height} @ {video_fps} fps")
        self.log(f"Escalando a máximo 1080p HD (1920x1080) manteniendo framerate")

        # Construir comando FFmpeg
        cmd = ['ffmpeg', '-y']

        if has_cover:
            # CORRECCIÓN: Configurar la carátula con el framerate del video
            # Parsear framerate para calcular número de frames
            try:
                if '/' in video_fps:
                    num, den = video_fps.split('/')
                    fps_value = float(num) / float(den)
                else:
                    fps_value = float(video_fps)
            except:
                fps_value = 30.0

            # Calcular número exacto de frames para 1 segundo
            num_frames = round(fps_value)  # Redondear al frame más cercano

            self.log(f"Configurando carátula a {fps_value:.3f} fps ({num_frames} frames para 1 segundo)")

            # MÉTODO MEJORADO: Usar número exacto de frames en lugar de duración
            # Esto evita problemas con framerates no-enteros (23.976, 29.97, etc.)
            cmd.extend([
                '-loop', '1',
                '-r', video_fps,  # Forzar framerate de salida
                '-vframes', str(num_frames),  # Número exacto de frames (en lugar de -t 1)
                '-i', cover_path,
                '-i', input_path,
                '-filter_complex',
                # Filtro simplificado - sin fps filter porque ya está correcto
                f'[0:v]scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,'
                f'pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2,'
                f'format=yuv420p,setpts=PTS-STARTPTS[cover];'
                f'[1:v]scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,'
                f'pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2,'
                f'format=yuv420p,setpts=PTS-STARTPTS[main];'
                f'[cover][main]concat=n=2:v=1:a=0,fps={video_fps}[vout]',  # fps al final del concat
                '-map', '[vout]',
                '-map', '1:a:0?'  # Audio del segundo input (video original)
            ])

            # Subtítulos del video original (input 1)
            subtitles = self.get_subtitle_tracks(input_path)
            if output_format == 'mkv' and subtitles:
                cmd.extend(['-map', '1:s?', '-c:s', 'copy'])
            elif output_format == 'mp4' and subtitles:
                cmd.extend(['-map', '1:s:0?', '-c:s', 'mov_text'])
        else:
            # Sin carátula
            cmd.extend([
                '-i', input_path,
                '-vf', f'scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,'
                       f'pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2,'
                       f'format=yuv420p,fps={video_fps}',
                '-map', '0:v',
                '-map', '0:a:0?'
            ])

            subtitles = self.get_subtitle_tracks(input_path)
            if output_format == 'mkv' and subtitles:
                cmd.extend(['-map', '0:s?', '-c:s', 'copy'])
            elif output_format == 'mp4' and subtitles:
                cmd.extend(['-map', '0:s:0?', '-c:s', 'mov_text'])

        # CORRECCIÓN: Configuración NVENC optimizada SIN -cq
        # Usar VBR puro con multipass de NVENC
        cmd.extend([
            '-c:v', 'hevc_nvenc',
            '-preset', self.preset.get(),
            '-profile:v', 'main',
            '-tier', 'high',
            '-rc', 'vbr',  # Variable Bitrate
            '-multipass', 'fullres',  # CORRECCIÓN: Usar multipass de NVENC (no -2pass)
            '-b:v', f'{target_bitrate}k',  # Bitrate target
            '-maxrate', f'{int(target_bitrate * 1.3)}k',  # Maxrate más conservador
            '-bufsize', f'{int(target_bitrate * 2)}k',  # Buffer para VBR
            '-spatial-aq', '1',  # Adaptive Quantization espacial
            '-temporal-aq', '1',  # Adaptive Quantization temporal
            # NOTA: NO usar -cq aquí, eso ignora el bitrate target
            '-c:a', 'aac',
            '-b:a', '256k',
            '-ac', '2'
        ])

        if output_format == 'mp4':
            cmd.extend(['-movflags', '+faststart'])

        cmd.append(output_path)

        try:
            self.log("Iniciando codificación con NVENC multipass...")
            self.log(f"Comando: {' '.join(cmd[:15])}...")  # Mostrar parte del comando

            # Ejecutar con monitoreo de progreso
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8'
            )

            # Monitorear stderr para ver el progreso
            last_progress = ""
            for line in process.stderr:
                if 'frame=' in line and 'fps=' in line:
                    # Extraer información de progreso
                    if 'time=' in line:
                        time_part = line.split('time=')[1].split()[0]
                        if time_part != last_progress:
                            last_progress = time_part
                            self.log(f"Progreso: {time_part}")
                elif 'error' in line.lower() and 'deprecated' not in line.lower():
                    self.log(f"Advertencia: {line.strip()}")

            process.wait()

            if process.returncode == 0:
                # Verificar el tamaño del archivo resultante
                if os.path.exists(output_path):
                    output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    output_size_kb = os.path.getsize(output_path) / 1024

                    self.log(f"✓ Transcodificación completada (1080p HD)")
                    self.log(f"  Tamaño final: {output_size_mb:.1f} MB ({output_size_kb:.0f} KB)")

                    # Verificar si está cerca del objetivo (1900000 KB)
                    target_kb = 1900000
                    diff_percent = abs(output_size_kb - target_kb) / target_kb * 100

                    if diff_percent > 10:
                        self.log(f"  ADVERTENCIA: El tamaño difiere del objetivo en {diff_percent:.1f}%")
                        if output_size_kb < target_kb * 0.5:
                            self.log(f"  El archivo es mucho más pequeño de lo esperado.")
                    else:
                        self.log(f"  Tamaño dentro del rango objetivo (±10%)")

                    return True
                else:
                    self.log(f"✗ Error: No se generó el archivo de salida")
                    return False
            else:
                stderr_output = ""
                try:
                    # Intentar leer stderr si está disponible
                    if hasattr(process.stderr, 'read'):
                        stderr_output = process.stderr.read()
                except:
                    pass

                self.log(f"Error en codificación. Código de salida: {process.returncode}")

                # Verificar si es error de filtro concat
                is_filter_error = (
                    'reinitializing filters' in stderr_output.lower() or
                    'error code: -22' in stderr_output.lower() or
                    'invalid argument' in stderr_output.lower()
                )

                if is_filter_error and has_cover:
                    self.log(f"⚠ Detectado error en filtro concat")
                    self.log(f"→ Intentando con método alternativo (concatenación de archivos)...")
                    return self.transcode_video_with_cover_fallback(
                        input_path, output_path, output_format, video_info, cover_path
                    )
                else:
                    if stderr_output:
                        self.log(f"Detalles: {stderr_output[:1000]}")
                    return False

        except Exception as e:
            self.log(f"Error ejecutando transcodificación: {e}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}")

            # Si hay carátula, intentar método alternativo
            if has_cover:
                self.log(f"→ Intentando con método alternativo...")
                return self.transcode_video_with_cover_fallback(
                    input_path, output_path, output_format, video_info, cover_path
                )
            return False

    def process_video(self, source_file, source_dir, dest_base):
        """Procesar un archivo de video individual"""
        try:
            # Verificar que origen y destino no sean el mismo
            if os.path.abspath(source_dir) == os.path.abspath(dest_base):
                self.log(f"⚠ ADVERTENCIA: El directorio de origen y destino son iguales.")
                self.log(f"  Se creará subcarpeta 'converted' para evitar sobrescribir archivos.")
                dest_base = os.path.join(dest_base, 'converted')
                os.makedirs(dest_base, exist_ok=True)

            # Obtener información del video
            self.log(f"\n{'='*60}")
            self.log(f"Analizando: {os.path.basename(source_file)}")
            video_info = self.get_video_info(source_file)
            if not video_info:
                self.log(f"✗ Error: No se pudo obtener información del video")
                return

            # Crear estructura de directorios en destino
            rel_path = os.path.relpath(source_dir, self.source_dir.get())
            dest_dir = os.path.join(dest_base, rel_path)
            os.makedirs(dest_dir, exist_ok=True)

            # Definir archivo de salida
            base_name = os.path.splitext(os.path.basename(source_file))[0]
            output_format = self.output_format.get()
            output_file = os.path.join(dest_dir, f"{base_name}.{output_format}")

            # Si el archivo de salida es el mismo que el de entrada, añadir sufijo
            if os.path.abspath(output_file) == os.path.abspath(source_file):
                output_file = os.path.join(dest_dir, f"{base_name}_converted.{output_format}")

            # Verificar si ya existe
            if os.path.exists(output_file):
                self.log(f"⚠ El archivo ya existe, saltando: {os.path.basename(output_file)}")
                return

            # Buscar carátula
            cover_path = self.find_cover(source_dir)

            # Copiar carátula al destino
            if cover_path:
                cover_dest = os.path.join(dest_dir, os.path.basename(cover_path))
                if not os.path.exists(cover_dest):
                    try:
                        shutil.copy2(cover_path, cover_dest)
                        self.log(f"✓ Carátula copiada al destino")
                    except Exception as e:
                        self.log(f"⚠ No se pudo copiar la carátula: {e}")

            # Decidir si remuxear o transcodificar
            size_kb = video_info['size_kb']
            size_mb = size_kb / 1024
            size_gb = size_mb / 1024

            self.log(f"Tamaño: {size_mb:.1f} MB ({size_gb:.2f} GB)")
            self.log(f"Duración: {video_info['duration']:.1f} segundos ({video_info['duration']/60:.1f} minutos)")

            success = False

            if size_kb <= 2000000:  # <= 2GB
                self.log(f"→ Tamaño ≤ 2GB: Remuxing (preservando resolución)...")
                self.log(f"  Resolución: {video_info['width']}x{video_info['height']} (se mantiene)")
                success = self.remux_video(source_file, output_file, output_format)
            else:  # > 2GB
                self.log(f"→ Tamaño > 2GB: Transcodificación a ~1.9GB...")
                self.log(f"  Resolución máxima: 1080p HD (1920x1080)")
                if cover_path:
                    self.log(f"  Se añadirá carátula de 1 segundo al inicio")
                success = self.transcode_video(source_file, output_file, output_format,
                                               video_info, cover_path)

            # Verificar resultado final
            if success and os.path.exists(output_file):
                final_size_mb = os.path.getsize(output_file) / (1024 * 1024)
                final_size_gb = final_size_mb / 1024
                self.log(f"{'='*60}")
                self.log(f"✓✓✓ COMPLETADO: {os.path.basename(output_file)}")
                self.log(f"    Tamaño final: {final_size_mb:.1f} MB ({final_size_gb:.2f} GB)")
                self.log(f"{'='*60}\n")
            else:
                self.log(f"✗✗✗ ERROR: No se pudo procesar el video correctamente")
                if os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                        self.log(f"    Archivo incompleto eliminado")
                    except:
                        pass

        except Exception as e:
            self.log(f"✗ Error procesando {source_file}: {str(e)}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}")

    def find_videos(self, directory):
        """Encontrar todos los archivos de video en el directorio"""
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm',
                          '.m4v', '.mpg', '.mpeg', '.3gp', '.ts', '.vob']
        videos = []

        self.log("Buscando archivos de video...")
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext.lower()) for ext in video_extensions):
                    videos.append((os.path.join(root, file), root))

        return videos

    def processing_thread(self):
        """Thread principal de procesamiento"""
        try:
            source = self.source_dir.get()
            dest = self.dest_dir.get()

            # Validar directorios
            if not os.path.exists(source):
                messagebox.showerror("Error", "El directorio de origen no existe")
                return

            if not os.path.exists(dest):
                os.makedirs(dest, exist_ok=True)

            # Encontrar todos los videos
            videos = self.find_videos(source)
            if not videos:
                self.log("No se encontraron archivos de video")
                messagebox.showwarning("Advertencia", "No se encontraron archivos de video en el directorio origen")
                return

            self.log(f"✓ Encontrados {len(videos)} videos para procesar")
            self.log("=" * 60)

            # Procesar cada video
            processed = 0
            failed = 0

            for i, (video_path, video_dir) in enumerate(videos, 1):
                if not self.is_processing:
                    self.log(f"\n⚠ Procesamiento detenido por el usuario")
                    break

                self.log(f"\n[{i}/{len(videos)}] Procesando video...")

                try:
                    self.process_video(video_path, video_dir, dest)
                    processed += 1
                except Exception as e:
                    self.log(f"✗ Error procesando video: {e}")
                    failed += 1

            if self.is_processing:
                self.log("\n" + "=" * 60)
                self.log("=" * 60)
                self.log("PROCESAMIENTO FINALIZADO")
                self.log("=" * 60)
                self.log(f"Total de videos: {len(videos)}")
                self.log(f"Procesados exitosamente: {processed}")
                if failed > 0:
                    self.log(f"Fallidos: {failed}")
                self.log("\nResumen:")
                self.log("• Videos ≤2GB: Remuxeados con resolución original")
                self.log("• Videos >2GB: Transcodificados a 1080p HD (~1.9GB)")
                self.log("=" * 60)

                messagebox.showinfo("Completado",
                                  f"Procesamiento finalizado\n\n"
                                  f"Total: {len(videos)} videos\n"
                                  f"Exitosos: {processed}\n"
                                  f"Fallidos: {failed}")

        except Exception as e:
            self.log(f"\n✗ Error crítico en el procesamiento: {str(e)}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Error durante el procesamiento:\n{str(e)}")

        finally:
            self.is_processing = False
            self.progress.stop()
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    def start_processing(self):
        """Iniciar el procesamiento de videos"""
        if not self.source_dir.get() or not self.dest_dir.get():
            messagebox.showwarning("Advertencia",
                                  "Por favor selecciona los directorios de origen y destino")
            return

        # Verificar que ffmpeg esté instalado
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("FFmpeg no funciona correctamente")

            # Verificar soporte NVENC
            result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
            if 'hevc_nvenc' not in result.stdout:
                response = messagebox.askyesno("Advertencia",
                    "No se detectó soporte para NVENC (GPU NVIDIA).\n" +
                    "El proceso podría fallar o usar CPU.\n" +
                    "¿Desea continuar de todos modos?")
                if not response:
                    return
        except Exception as e:
            messagebox.showerror("Error",
                f"FFmpeg no está instalado o no está en el PATH del sistema.\n{str(e)}")
            return

        self.is_processing = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start(10)

        # Limpiar log
        self.log_text.delete(1.0, tk.END)
        self.log("=" * 60)
        self.log("CONVERSOR DE VIDEO H265 NVENC - VERSIÓN CORREGIDA")
        self.log("=" * 60)
        self.log(f"Directorio origen: {self.source_dir.get()}")
        self.log(f"Directorio destino: {self.dest_dir.get()}")
        self.log(f"Formato de salida: {self.output_format.get().upper()}")
        self.log(f"Preset de codificación: {self.preset.get()}")
        self.log("\nReglas de procesamiento:")
        self.log("• Videos ≤ 2GB: Remux (mantiene resolución original)")
        self.log("• Videos > 2GB: Recodificación a 1080p HD máximo (~1.9GB)")
        self.log("  - Bitrate calculado individualmente por video")
        self.log("  - Carátula de 1 segundo al inicio (si existe)")
        self.log("  - Codec: H.265/HEVC NVENC")
        self.log("  - Audio: AAC 256 kbps")
        self.log("=" * 60)

        # Iniciar thread de procesamiento
        thread = threading.Thread(target=self.processing_thread, daemon=True)
        thread.start()

    def stop_processing(self):
        """Detener el procesamiento"""
        self.is_processing = False
        self.log("\n⏹ Deteniendo procesamiento...")
        self.stop_btn.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    root.resizable(True, True)
    app = VideoConverterApp(root)

    # Centrar ventana
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()

if __name__ == "__main__":
    main()
