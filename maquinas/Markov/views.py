from django.shortcuts import render


def markov(request):
    return render(request, 'markov.html')

# Create your views here.
