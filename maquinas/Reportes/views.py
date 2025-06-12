
from .models import Lineas_Embotelladoras
from django.http import JsonResponse

from q_learning.models import Simulacion_estado
from django.shortcuts import render, get_object_or_404
from django.utils.dateparse import parse_date

import numpy as np
import os
from django.conf import settings

def reportes_view(request):
    lineas = Lineas_Embotelladoras.objects.all()
    return render(request, 'reportes.html', {'lineas': lineas})

def reporte_qlearning_data(request):

    nombre_linea = request.GET.get('linea')
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')

    if not nombre_linea:
        return JsonResponse({'error': 'El nombre de la línea es requerido.'}, status=400)


    eventos = Simulacion_estado.objects.filter(Linea_id__Nombre=nombre_linea)


    if fecha_inicio_str:
        fecha_inicio = parse_date(fecha_inicio_str)
        if fecha_inicio:
            eventos = eventos.filter(Fecha__gte=fecha_inicio)
    
    if fecha_fin_str:
        fecha_fin = parse_date(fecha_fin_str)
        if fecha_fin:
            eventos = eventos.filter(Fecha__lte=fecha_fin)

    eventos = eventos.order_by('-Fecha')

    data = list(eventos.values(
        'Fecha',
        'Acc_IA',
        'Acc_humana',
        'acc_final',
        'Invervencion',
        'Temperatura',
        'Presion',
        'Uso',
        'Recompensa',
        'Comentario',
        'Usuario_id__username' 
    ))


    for item in data:
        item['Fecha'] = item['Fecha'].strftime('%Y-%m-%d %H:%M:%S') if item['Fecha'] else None
        item['Recompensa'] = round(item['Recompensa'], 2) if item['Recompensa'] is not None else None

    return JsonResponse(data, safe=False)



def reporte_entrenamiento_data(request):

    try:
 
        eval_path = os.path.join(settings.BASE_DIR, 'logs_eval', 'evaluations.npz')

        if not os.path.exists(eval_path):
            return JsonResponse({'error': 'El archivo de evaluación (evaluations.npz) no fue encontrado.'}, status=404)

      
        eval_data = np.load(eval_path)
        
      
        timesteps = eval_data['timesteps'].tolist()
        results = eval_data['results'].tolist()
        ep_lengths = eval_data['ep_lengths'].tolist()
        
       
        mean_rewards = [np.mean(res) for res in results]
        std_rewards = [np.std(res) for res in results]
        mean_ep_lengths = [np.mean(epl) for epl in ep_lengths]

    
        data = {
            'timesteps': timesteps,
            'mean_rewards': mean_rewards,
            'std_rewards': std_rewards,
            'mean_ep_lengths': mean_ep_lengths,
        }

        return JsonResponse(data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error al procesar el archivo de evaluación: {str(e)}'}, status=500)

