#!/usr/bin/env python3
"""
Script de prueba para verificar configuración NVENC
Prueba la codificación con los parámetros corregidos
"""

import subprocess
import sys
import json

def check_ffmpeg():
    """Verificar que FFmpeg está instalado"""
    print("=" * 60)
    print("1. Verificando instalación de FFmpeg...")
    print("=" * 60)
    try:
        result = subprocess.run(['ffmpeg', '-version'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ FFmpeg encontrado: {version_line}")
            return True
        else:
            print("✗ FFmpeg no funciona correctamente")
            return False
    except FileNotFoundError:
        print("✗ FFmpeg no está instalado o no está en PATH")
        return False

def check_nvenc():
    """Verificar soporte NVENC"""
    print("\n" + "=" * 60)
    print("2. Verificando soporte NVENC...")
    print("=" * 60)
    try:
        result = subprocess.run(['ffmpeg', '-encoders'],
                              capture_output=True, text=True)

        # Buscar codificadores NVENC
        nvenc_encoders = []
        for line in result.stdout.split('\n'):
            if 'nvenc' in line.lower():
                nvenc_encoders.append(line.strip())

        if nvenc_encoders:
            print(f"✓ Soporte NVENC detectado")
            print(f"\nCodecadores NVENC disponibles:")
            for encoder in nvenc_encoders:
                if 'hevc_nvenc' in encoder:
                    print(f"  ✓ {encoder} ← ESTE ES EL QUE USAMOS")
                else:
                    print(f"    {encoder}")

            if any('hevc_nvenc' in e for e in nvenc_encoders):
                print(f"\n✓✓ hevc_nvenc (H.265) está disponible")
                return True
            else:
                print(f"\n✗ hevc_nvenc NO está disponible")
                return False
        else:
            print("✗ No se encontró soporte NVENC")
            print("  Tu GPU puede no ser compatible o no tienes drivers NVIDIA")
            return False
    except Exception as e:
        print(f"✗ Error verificando NVENC: {e}")
        return False

def check_nvenc_options():
    """Verificar opciones disponibles de hevc_nvenc"""
    print("\n" + "=" * 60)
    print("3. Verificando opciones de hevc_nvenc...")
    print("=" * 60)
    try:
        result = subprocess.run(['ffmpeg', '-h', 'encoder=hevc_nvenc'],
                              capture_output=True, text=True)

        if result.returncode == 0:
            # Buscar opciones importantes
            important_options = [
                '-preset',
                '-rc',
                '-multipass',
                '-b:v',
                '-maxrate',
                '-bufsize',
                '-spatial-aq',
                '-temporal-aq'
            ]

            print("Opciones importantes disponibles:")
            for option in important_options:
                if option in result.stdout:
                    print(f"  ✓ {option}")
                else:
                    print(f"  ✗ {option} (puede no estar disponible)")

            # Verificar si soporta multipass
            if '-multipass' in result.stdout or 'multipass' in result.stdout:
                print(f"\n✓ Soporta -multipass (recomendado)")
            elif '-2pass' in result.stdout:
                print(f"\n⚠ Solo soporta -2pass (funcionalidad limitada)")

            return True
        else:
            print("✗ No se pudo obtener información de hevc_nvenc")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_simple_encode():
    """Probar una codificación simple de prueba"""
    print("\n" + "=" * 60)
    print("4. Prueba de codificación (generando video de prueba)...")
    print("=" * 60)

    # Generar un video de prueba de 5 segundos
    test_input = "test_input.mp4"
    test_output = "test_output_nvenc.mp4"

    print("\nGenerando video de prueba de 5 segundos...")
    cmd_generate = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', 'testsrc=duration=5:size=1920x1080:rate=30',
        '-f', 'lavfi',
        '-i', 'sine=frequency=1000:duration=5',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-c:a', 'aac',
        test_input
    ]

    try:
        result = subprocess.run(cmd_generate, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"✗ Error generando video de prueba: {result.stderr[:500]}")
            return False
        print(f"✓ Video de prueba generado: {test_input}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    # Codificar con NVENC usando parámetros corregidos
    print("\nCodificando con NVENC (parámetros corregidos)...")
    print("Parámetros usados:")
    print("  -rc vbr")
    print("  -multipass fullres")
    print("  -b:v 5000k")
    print("  -maxrate 6500k")
    print("  -bufsize 10000k")
    print("  -spatial-aq 1")
    print("  -temporal-aq 1")

    cmd_encode = [
        'ffmpeg', '-y',
        '-i', test_input,
        '-c:v', 'hevc_nvenc',
        '-preset', 'medium',
        '-profile:v', 'main',
        '-tier', 'high',
        '-rc', 'vbr',
        '-multipass', 'fullres',
        '-b:v', '5000k',
        '-maxrate', '6500k',
        '-bufsize', '10000k',
        '-spatial-aq', '1',
        '-temporal-aq', '1',
        '-c:a', 'aac',
        '-b:a', '256k',
        test_output
    ]

    try:
        print("\nCodificando...")
        result = subprocess.run(cmd_encode, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✓✓ Codificación exitosa: {test_output}")

            # Verificar información del archivo resultante
            import os
            if os.path.exists(test_output):
                size_mb = os.path.getsize(test_output) / (1024 * 1024)
                print(f"\nInformación del archivo generado:")
                print(f"  Tamaño: {size_mb:.2f} MB")

                # Obtener bitrate real
                probe_cmd = [
                    'ffprobe', '-v', 'error',
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=bit_rate,codec_name',
                    '-of', 'json',
                    test_output
                ]

                probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                if probe_result.returncode == 0:
                    info = json.loads(probe_result.stdout)
                    if 'streams' in info and len(info['streams']) > 0:
                        codec = info['streams'][0].get('codec_name', 'unknown')
                        bitrate = int(info['streams'][0].get('bit_rate', 0)) / 1000
                        print(f"  Codec: {codec}")
                        print(f"  Bitrate real: {bitrate:.0f} kbps")

                        # Verificar si está cerca del objetivo (5000 kbps)
                        target = 5000
                        diff_percent = abs(bitrate - target) / target * 100

                        if diff_percent <= 20:
                            print(f"  ✓ Bitrate dentro del rango esperado (±20%)")
                        else:
                            print(f"  ⚠ Bitrate difiere {diff_percent:.1f}% del objetivo")

                print(f"\n✓✓✓ PRUEBA EXITOSA")
                print(f"\nArchivos de prueba generados:")
                print(f"  - {test_input}")
                print(f"  - {test_output}")
                print(f"\nPuedes eliminarlos con:")
                print(f"  rm {test_input} {test_output}")

                return True
            else:
                print(f"✗ El archivo de salida no fue creado")
                return False
        else:
            print(f"✗ Error en codificación:")
            print(result.stderr[:1000])

            # Intentar sin multipass si falla
            print("\n⚠ Intentando sin -multipass...")
            cmd_encode_fallback = [
                'ffmpeg', '-y',
                '-i', test_input,
                '-c:v', 'hevc_nvenc',
                '-preset', 'medium',
                '-rc', 'vbr',
                '-b:v', '5000k',
                '-maxrate', '6500k',
                '-bufsize', '10000k',
                '-c:a', 'aac',
                '-b:a', '256k',
                test_output
            ]

            result2 = subprocess.run(cmd_encode_fallback, capture_output=True, text=True)
            if result2.returncode == 0:
                print(f"✓ Codificación exitosa sin -multipass")
                print(f"⚠ Nota: Tu versión de FFmpeg puede no soportar -multipass")
                print(f"  El script funcionará pero sin optimización multipaso")
                return True
            else:
                print(f"✗ También falló sin -multipass")
                print(result2.stderr[:1000])
                return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  VERIFICACIÓN DE CONFIGURACIÓN NVENC".center(58) + "║")
    print("║" + "  Script de prueba para video_converter_fixed.py".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    results = []

    # 1. Verificar FFmpeg
    results.append(("FFmpeg instalado", check_ffmpeg()))

    # 2. Verificar NVENC
    if results[-1][1]:
        results.append(("Soporte NVENC", check_nvenc()))
    else:
        print("\n⚠ Saltando pruebas de NVENC (FFmpeg no disponible)")
        results.append(("Soporte NVENC", False))

    # 3. Verificar opciones
    if results[-1][1]:
        results.append(("Opciones NVENC", check_nvenc_options()))
    else:
        print("\n⚠ Saltando prueba de opciones (NVENC no disponible)")
        results.append(("Opciones NVENC", False))

    # 4. Prueba de codificación
    if results[-1][1]:
        results.append(("Codificación de prueba", test_simple_encode()))
    else:
        print("\n⚠ Saltando prueba de codificación (requisitos no cumplidos)")
        results.append(("Codificación de prueba", False))

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE VERIFICACIÓN")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓✓✓ TODAS LAS PRUEBAS PASARON")
        print("\nTu sistema está correctamente configurado para usar")
        print("el script video_converter_fixed.py con NVENC")
        print("\nPuedes proceder a usarlo con confianza.")
    else:
        print("\n✗✗✗ ALGUNAS PRUEBAS FALLARON")
        print("\nRevisa los errores anteriores antes de usar el script.")
        print("\nPosibles soluciones:")
        print("  1. Actualiza los drivers de NVIDIA")
        print("  2. Reinstala FFmpeg con soporte NVENC")
        print("  3. Verifica que tu GPU es compatible (serie GTX 600+)")

    print("\n")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
