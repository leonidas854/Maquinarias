from django.shortcuts import render
from Services.markov import Markov




def resolver_saltos(request,n):
    solution = Markov()
    
def markov(request):
    return render(request, 'markov.html')

# Create your views here.
