# q_learning/views.py
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from Reportes.models import Lineas_Embotelladoras
from .Services.rl_service  import RLModelManager  
from Markov.Services.ServicesMarkov_ import ServicesMarkov
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required




from django.utils.dateparse import parse_date
from .models import Simulacion_estado

@require_POST
@login_required
def registrar_ajuste_manual(request):
   
    try:
        nombre_linea = request.POST.get('linea')
        accion_manual = request.POST.get('accion')
        comentario = request.POST.get('comentario')
        fecha_str = request.POST.get('fecha')

        if not all([nombre_linea, accion_manual, comentario]):
            return JsonResponse({'error': 'Todos los campos son requeridos.'}, status=400)

      
        linea_obj = get_object_or_404(Lineas_Embotelladoras, Nombre=nombre_linea)
        usuario_obj = request.user
        
        try:
            temp = float(request.POST.get('temperatura'))
            pres = float(request.POST.get('presion'))
            uso = float(request.POST.get('uso'))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'No se recibieron datos válidos de los sensores.'}, status=400)

        if not all([nombre_linea, accion_manual, comentario, fecha_str]):
            return JsonResponse({'error': 'Todos los campos del formulario son requeridos.'}, status=400)
        
        try:
      
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
      
           
        except ValueError:
            return JsonResponse({'error': 'El formato de fecha y hora es inválido.'}, status=400)

        Simulacion_estado.objects.create(
            Linea_id=linea_obj,
            Usuario_id=usuario_obj,
            Fecha= fecha_obj,
            Acc_IA=None, 
            Acc_humana=accion_manual,
            acc_final=accion_manual,
            Invervencion=True, 
            Comentario=comentario,
            Temperatura=temp,
            Presion=pres,
            Uso=uso,
            Recompensa=None 
        )
        return JsonResponse({'status': 'ok', 'message': f'Ajuste manual "{accion_manual}" para la línea "{nombre_linea}" registrado correctamente.'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def select_linea_dashboard(request):
    lineas = Lineas_Embotelladoras.objects.all().order_by('Nombre')
    context = {
        'lineas': lineas
    }
    return render(request, 'select_linea.html', context)

def qlearning_dashboard(request, nombre_linea):
    linea = get_object_or_404(Lineas_Embotelladoras, Nombre=nombre_linea)
    
    context = {
        'linea': linea
    }
    return render(request, 'qlearning_dashboard.html', context)

def get_linea_config(request):
    nombre_linea = request.GET.get('linea')
    if not nombre_linea:
        return JsonResponse({'error': 'Parámetro "linea" es requerido.'}, status=400)
    
    try:
      
        config = Lineas_Embotelladoras.objects.filter(Nombre=nombre_linea).values(
            'Temp_min', 'Temp_max', 'Presion_base', 'Presion_maxima', 'Uso_operativo'
        ).first()
        
        if config is None:
            return JsonResponse({'error': f'No se encontró la configuración para la línea {nombre_linea}.'}, status=404)
            
        return JsonResponse(config)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def get_linea_estado_actual(request):
    nombre_linea = request.GET.get('linea')
    
    if not nombre_linea:
        return JsonResponse({'error': 'Parámetro "linea" es requerido.'}, status=400)
    
    try:
        markov = ServicesMarkov(nombre_linea)
        ultimo_estado = markov.get_ultimo_estado().get('estado')
        return JsonResponse({'estado_actual': ultimo_estado})
    except ultimo_estado.DoesNotExist:
        return JsonResponse({'error': f'No hay registros de estado para la línea {nombre_linea}.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def get_todas_las_lineas(request):
   
    try:
        lineas = Lineas_Embotelladoras.objects.all().order_by('id')
        data = []
        for linea in lineas:
            data.append({
                "nombre": linea.Nombre,
                "config": {
                    'Temp_min': linea.Temp_min,
                    'Temp_max': linea.Temp_max,
                    'Presion_base': linea.Presion_base,
                    'Presion_maxima': linea.Presion_maxima,
                    'Uso_operativo': linea.Uso_operativo
                }
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def ajuste_manual_view(request):
    lineas = Lineas_Embotelladoras.objects.all().order_by('Nombre')
    context = {'lineas': lineas}
    return render(request, 'manual.html', context)