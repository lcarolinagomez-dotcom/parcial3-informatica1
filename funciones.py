# Parcial 3 - Informática I 
# Grupo 2
# Estudiantes:
# - Lizeth Carolina Gomez Bastidas
# - Nombre Jose Alejandro Sanchez Alzate

import os
import csv
import json
import xml.etree.ElementTree as ET

def crear_carpetas(base_dir):
    """Crea sistema_uci/ y sus subcarpetas verificando si ya existen."""
    json_dir = os.path.join(base_dir, "exportaciones_json")
    csv_dir = os.path.join(base_dir, "exportaciones_csv")
    for ruta in (base_dir, json_dir, csv_dir):
        if os.path.isdir(ruta):
            print(f"La carpeta ya existe: {ruta}")
        else:
            os.makedirs(ruta, exist_ok=True)
            print(f"Carpeta creada: {ruta}")
    return json_dir, csv_dir

def a_numero(texto):
    """Convierte a número si se puede; si no, deja el texto igual."""
    try:
        return int(texto)
    except ValueError:
        pass
    try:
        return float(texto)
    except ValueError:
        return texto

def extraer_Paciente_hl7(dir_pacientes):
    lista_pacientes = {}
    if not os.path.exists(dir_pacientes):
        return lista_pacientes
    for archivo in os.listdir(dir_pacientes):
        if archivo.endswith("_hl7.txt"):
            ruta_archivo = os.path.join(dir_pacientes, archivo)
            paciente_id, paciente_nombre, ubicacion = "", "", ""
            with open(ruta_archivo, 'r', encoding='utf-8-sig') as f:
                for linea in f:
                    partes = linea.strip().split("|")
                    if partes[0] == "PID" and len(partes) > 5:
                        paciente_id = partes[3].split("^")[0]
                        paciente_nombre = partes[5].replace("^", " ")
                    elif partes[0] == "PV1" and len(partes) > 3:
                        ubicacion = partes[3].replace("^", " - ")
            if paciente_id:
                lista_pacientes[paciente_id] = {"id": paciente_id, "nombre": paciente_nombre, "ubicacion": ubicacion}
    return lista_pacientes

def extraer_signos_vitales(dir_pacientes):
    signos_por_paciente = {}
    if not os.path.exists(dir_pacientes):
        return signos_por_paciente
    for archivo in os.listdir(dir_pacientes):
        if archivo.endswith(".xml") and "signos" in archivo:
            ruta_archivo = os.path.join(dir_pacientes, archivo)
            try:
                root = ET.parse(ruta_archivo).getroot()
                paciente_id = ""
                subject = root.find('.//{*}subject')
                if subject is not None:
                    reference_tag = subject.find('{*}reference')
                    if reference_tag is not None:
                        paciente_id = reference_tag.attrib.get('value', '')

                lista_signos = []
                for signo in root.findall('.//{*}sign'):
                    lista_signos.append({
                        "nombre": signo.attrib.get('name', ''),
                        "valor": a_numero(signo.attrib.get('value', '')),
                        "unidad": signo.attrib.get('unit', '')
                    })
                if paciente_id:
                    signos_por_paciente[paciente_id] = lista_signos
            except Exception:
                continue
    return signos_por_paciente

def extraer_inf_diagnostico(dir_pacientes):
    inf_paciente = {}
    if not os.path.exists(dir_pacientes):
        return inf_paciente
    for archivo in os.listdir(dir_pacientes):
        if archivo.endswith(".xml") and ("diagnostico" in archivo or "expediente" in archivo):
            ruta_archivo = os.path.join(dir_pacientes, archivo)
            try:
                root = ET.parse(ruta_archivo).getroot()
                def texto(etiqueta):
                    elemento = root.find('.//{*}' + etiqueta)
                    return elemento.text.strip() if elemento is not None and elemento.text else ""

                paciente_id = texto('patientId')
                if paciente_id:
                    inf_paciente[paciente_id] = {
                        "Categoria": texto('category'),
                        "Conclusion": texto('conclusion'),
                        "Medico": texto('physician')
                    }
            except Exception:
                continue
    return inf_paciente

def extraer_telemetria(dir_pacientes):
    telemetria_por_paciente = {}
    if not os.path.exists(dir_pacientes):
        return telemetria_por_paciente
    for archivo in os.listdir(dir_pacientes):
        if "telemetria" in archivo or "log" in archivo:
            ruta_archivo = os.path.join(dir_pacientes, archivo)
            with open(ruta_archivo, 'r', encoding='utf-8-sig') as f:
                for linea in f:
                    partes = linea.strip().split("|")
                    if len(partes) >= 5:
                        p_id = partes[1]
                        registro = {
                            "fecha_hora": partes[0],
                            "sensor": partes[2],
                            "valor": a_numero(partes[3]),
                            "estado": partes[4]
                        }
                        telemetria_por_paciente.setdefault(p_id, []).append(registro)
    return telemetria_por_paciente

def cargar_archivos(historia):
    dir_pacientes = os.path.join(os.getcwd(), 'pacientes_3p')
    
    pacientes = extraer_Paciente_hl7(dir_pacientes)
    signos = extraer_signos_vitales(dir_pacientes)
    diagnosticos = extraer_inf_diagnostico(dir_pacientes)
    telemetrias = extraer_telemetria(dir_pacientes)

    todos_ids = set(pacientes.keys()) | set(signos.keys()) | set(diagnosticos.keys()) | set(telemetrias.keys())

    for p_id in todos_ids:
        historia[p_id] = {
            "informacion_personal": pacientes.get(p_id, {}),
            "signos_vitales": signos.get(p_id, []),
            "diagnostico": diagnosticos.get(p_id, {}),
            "telemetria": telemetrias.get(p_id, [])
        }

def exportar_json(historia, json_dir):
    for p_id, datos in historia.items():
        ruta_json = os.path.join(json_dir, f"{p_id}_historia_clinica.json")
        with open(ruta_json, 'w', encoding='utf-8') as f_json:
            json.dump(datos, f_json, indent=4, ensure_ascii=False)

def exportar_csv(historia, csv_dir):
    columnas_signos = [] 
    for datos in historia.values():
        for s in datos["signos_vitales"]:
            if s["nombre"] not in [c[0] for c in columnas_signos]:
                columnas_signos.append((s["nombre"], s["unidad"]))

    ruta_csv = os.path.join(csv_dir, "signos_vitales_consolidado.csv")
    with open(ruta_csv, 'w', newline='', encoding='utf-8-sig') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["paciente_id", "nombre_paciente"] + [f"{n} ({u})" for n, u in columnas_signos])
        for p_id, datos in historia.items():
            valores = {s["nombre"]: s["valor"] for s in datos["signos_vitales"]}
            fila = [p_id, datos["informacion_personal"].get("nombre", "Desconocido")]
            fila += [valores.get(n, "") for n, _ in columnas_signos]
            writer.writerow(fila)
    return ruta_csv

def ejecutar_menu_principal(json_dir, csv_dir):
    historia_clinica_general = {}

    while True:
        try:
            print("\n" + "=" * 45)
            print("   SISTEMA DE GESTIÓN UCI - HISTORIA CLÍNICA")
            print("=" * 45)
            print("1. Cargar y unificar información de la carpeta pacientes_3p")
            print("2. Exportar datos a JSON y CSV")
            print("3. Visualizar resumen de Historia Clínica General")
            print("4. Salir")

            opcion = input("Seleccione una opción (1-4): ").strip()

            if opcion == "1":
                cargar_archivos(historia_clinica_general)
                print(f" Cargados exitosamente {len(historia_clinica_general)} pacientes a la historia clínica.")

            elif opcion == "2":
                if not historia_clinica_general:
                    print(" Primero debe cargar la información (Opción 1).")
                    continue
                exportar_json(historia_clinica_general, json_dir)
                ruta_c = exportar_csv(historia_clinica_general, csv_dir)
                print(f" Archivos JSON guardados en: {json_dir}")
                print(f" Archivo CSV guardado en: {ruta_c}")

            elif opcion == "3":
                if not historia_clinica_general:
                    print("No hay datos cargados aún. Seleccione la opción 1 primero.")
                else:
                    print("\n--- RESUMEN HISTORIA CLÍNICA GENERAL ---")
                    print(json.dumps(historia_clinica_general, indent=2, ensure_ascii=False))

            elif opcion == "4":
                print("Saliendo del programa")
                break
            else:
                print(" Opción inválida. Intente de nuevo.")

        except Exception as error:
            print(f" Ocurrió un error en el menú: {error}")