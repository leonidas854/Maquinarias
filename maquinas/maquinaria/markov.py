import numpy as np

class Markov:
    def __init__(self, matrix,vector):
        self.matrix = np.array(matrix) 
        self.vector = np.array(vector) 
    def Verificar(self):
        for i in range(len(self.matrix)):
            if sum(self.matrix[i]) != 1:
                return False
        return True
        
        
    def Resolver_saltos(self,saltos):
        new_vector = self.vector
        for i in range(1,saltos+1):
            
            new_vector = np.dot(new_vector,self.matrix)
           
        return new_vector
        
        