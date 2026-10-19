# Parcial 3 - Informática I 
# Grupo X
# Estudiantes:
# - Lizeth Carolina Gomez Bastidas
# - Nombre Jose Alejandro Sanchez Alzate

import os
import funciones as f

try:
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
except NameError:  
    directorio_actual = os.getcwd()

base_dir = os.path.join(directorio_actual, "sistema_uci")
json_dir, csv_dir = f.crear_carpetas(base_dir)

f.ejecutar_menu_principal(json_dir, csv_dir)
