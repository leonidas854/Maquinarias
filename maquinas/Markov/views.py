from django.shortcuts import render
from .Services import ServicesMarkov


def resolver_saltos(request,n,estado):
    servicio  = ServicesMarkov()
    servicio.set_Name_linea(estado)
    servicio.Resolver(n-1)
    return 
    
    
def markov(request):

    return render(request, 'markov.html')


