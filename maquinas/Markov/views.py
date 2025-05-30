from django.shortcuts import render
from .Services.ServicesMarkov_ import ServicesMarkov
from Reportes.models import Lineas_Embotelladoras
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
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


@csrf_exempt  # solo si usas POST sin token desde JS
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