from django.shortcuts import render
from .Services.ServicesMarkov_ import ServicesMarkov
from Reportes.models import Lineas_Embotelladoras
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

@login_required
def Markov(request):
    usuario = request.user
    lineas = usuario.lineas_asignadas.all()
    return render(request, 'markov.html', {
        'lineas': lineas
    })
@require_GET
@login_required
def obtener_estado_actual(request):
    nombre_linea = request.GET.get('linea')
    if not nombre_linea:
        return JsonResponse({'error': 'No se proporcionó una línea'})

    servicio = ServicesMarkov(nombre_linea)
    estado_actual = servicio.get_ultimo_estado()
    estados_posibles = servicio.get_estados()

    return JsonResponse({
        'estado_actual': estado_actual.get('estado', 'Sin datos'),
        'estados_posibles': estados_posibles
    })
    



@require_POST
@login_required
def predecir_markov(request):
    if request.method == 'POST':
        nombre_linea = request.POST.get('linea')
        saltos = int(request.POST.get('saltos', 1))

        servicio = ServicesMarkov(nombre_linea)
        resultado = servicio.Resolver_probabilidad(saltos)
        servicio.guardar_predicciones(request.user,saltos)
        if 'error' in resultado:
            return JsonResponse({'error': resultado['error']})
        return JsonResponse(resultado)

@require_GET
@login_required
def obtener_matriz_transiciones(request):
    nombre_linea = request.GET.get('linea')
    if not nombre_linea:
        return JsonResponse({'error': 'No se proporcionó una línea'}, status=400)
    
    servicio = ServicesMarkov(nombre_linea)
    matriz_conteo= servicio.construir_matriz_transicion()
    estados  =servicio.get_estados()

    if matriz_conteo is None or len(estados) == 0:
        return JsonResponse({'error': 'No hay suficientes datos para generar la matriz de transiciones.'})
    heatmap_data = []
    for i, estado_origen in enumerate(estados):
        for j, estado_destino in enumerate(estados):
            conteo = matriz_conteo[i, j]
            if conteo > 0:
                heatmap_data.append({'x': estado_destino, 'y': estado_origen, 'v': int(conteo)})

    return JsonResponse({
        'estados': estados,
        'heatmap_data': heatmap_data
    })