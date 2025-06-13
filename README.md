# 🏭 Sistema Web Inteligente de Gestión Predictiva – Maquinarias

### Escuela Militar de Ingeniería “MCAL. ANTONIO JOSÉ DE SUCRE”  
**Carrera de Ingeniería de Sistemas**  
**Cochabamba - Bolivia, 2025**

---

## 📌 Descripción General

**Maquinarias** es un sistema web inteligente desarrollado para anticipar fallas en las líneas de embotellado de la empresa EMBOL S.A., combinando tecnologías de inteligencia artificial, modelos estocásticos y monitoreo en tiempo real mediante WebSockets. Esta solución permite integrar información proveniente de PLCs, registros de calidad y mantenimiento, y utilizarla para transitar de un mantenimiento correctivo/preventivo a un enfoque predictivo y prescriptivo.

---

## 🎯 Objetivos

### 🎯 Objetivo General
Desarrollar un sistema web inteligente que integre modelos estocásticos, inteligencia artificial y cableado estructurado para anticipar fallas y optimizar el mantenimiento en las líneas de embotellado de EMBOL S.A.

### 🧩 Objetivos Específicos
- Analizar variables operativas desde PLCs, mantenimiento y calidad.
- Implementar Cadenas de Markov para modelar la degradación de los equipos.
- Entrenar un agente IA (Q-Learning) para ajustar predicciones no lineales.
- Automatizar reportes del estado de las máquinas y generar alertas.
- Diseñar una arquitectura de red con cableado estructurado.
- Ejecutar pruebas funcionales al sistema completo integrado.

---

## ⚙️ Tecnologías y Herramientas

| Componente         | Tecnología / Librería                              |
|--------------------|----------------------------------------------------|
| Framework Web      | Django 5.2.1                                       |
| WebSockets         | Django Channels 4.2.2 + Daphne 4.2.0               |
| Backend de canal   | Redis 6.2.0                                        |
| Inteligencia Artificial | stable-baselines3 2.6.0, Gymnasium 1.1.1      |
| Modelado Estocástico | NumPy, Pandas, Cadenas de Markov                |
| Visualización      | Matplotlib, HTML templating                       |
| Base de Datos      | PostgreSQL + psycopg2-binary                      |
| Red simulada       | Topología estrella, VLAN (Packet Tracer)         |
| Servidor           | ASGI + Daphne                                     |

---

## 📁 Estructura del Proyecto

Maquinarias/
├── Entrenamiento/ # Entrenamiento IA y Markov
│ ├── Entorno_.py
│ └── Entrenamiento.py
│
├── SistemaEmbol/ # Proyecto Django principal
│ ├── settings.py
│ ├── asgi.py
│ ├── routing.py
│ └── urls.py
│
├── Reportes/ # App con lógica de mantenimiento
├── templates/ # Interfaz web (HTML)
├── static/ # Archivos CSS/JS
├── requirements.txt # Dependencias del proyecto
└── manage.py


---

## ⚡ Instalación y Configuración

### 1. Clonar el Repositorio
# 

# git clone https://github.com/leonidas854/Maquinarias.git
cd Maquinarias


# https://github.com/leonidas854/Maquinarias

## crear entorno virtual 

python -m venv env
source env/bin/activate       
env\Scripts\activate.bat      

pip install -r requirements.txt


### Configurar la Base de Datos
python manage.py makemigrations
python manage.py migrate

## Ejecutar el Proyecto con Daphne

daphne SistemaEmbol.asgi:application
daphne -b 0.0.0.0 -p 8000 SistemaEmbol.asgi:application



