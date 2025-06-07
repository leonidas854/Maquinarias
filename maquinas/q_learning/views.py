# q_learning/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from Reportes.models import Lineas_Embotelladoras
from .Services.rl_service  import RLModelManager  
from Markov.Services.ServicesMarkov_ import ServicesMarkov
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
    markov = ServicesMarkov()
    if not nombre_linea:
        return JsonResponse({'error': 'Parámetro "linea" es requerido.'}, status=400)
    
    try:
       
        ultimo_estado = markov.get_ultimo_estado()
        return JsonResponse({'estado_actual': ultimo_estado.Estado})
    except ultimo_estado.DoesNotExist:
        return JsonResponse({'error': f'No hay registros de estado para la línea {nombre_linea}.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)