from django.shortcuts import render

def qlearning(request):
    return render(request, 'qlearning.html')

def manual(request):
    return render(request, 'manual.html')

# Create your views here.
