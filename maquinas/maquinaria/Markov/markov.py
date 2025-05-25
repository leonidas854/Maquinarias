import numpy as np

class Markov:
    def __init__(self, matrix=None,vector=None):
        self.matrix = np.array(matrix) if matrix is not None else None
        self.vector = np.array(vector) if vector is not None else None
        
        if self.matrix is not None and self.vector is not None:
            if not self.Verificar():
                raise ValueError("Matriz no válida")
    def Verificar(self):
        if self.vector is None or self.matrix is None:
            return False
        if not np.isclose(sum(self.vector), 1):
            return False
        for i in range(len(self.matrix)):
            if not np.isclose(sum(self.matrix[i]), 1):
                return False 
        return True
    def set_matriz(self, matrix):
        self.matrix = np.array(matrix)
        if self.vector is not None and not self.Verificar():
            raise ValueError("Matriz no válida al establecer matriz")
    def set_vector(self, vector):
        self.vector = np.array(vector)
        if self.matrix is not None and not self.Verificar():
            raise ValueError("Vector no válido al establecer vector")
    def resolver_vector_estacionario(self):
        n = self.matrix.shape[0]
        A = self.matrix.T - np.eye(n)
        A = np.vstack([A, np.ones(n)])
        b = np.zeros(n + 1)
        b[-1] = 1
        solucion = np.linalg.lstsq(A, b, rcond=None)[0]
        return solucion  
    def Resolver_saltos(self, saltos):
        if self.matrix is None or self.vector is None:
            raise ValueError("Matriz o vector no inicializados")
        new_vector = self.vector
        for _ in range(saltos):
            new_vector = np.dot(new_vector, self.matrix)
        return new_vector
    def Convertir_Probabilidad(self,Matriz):
        self.matrix = []
        for i in range(len(Matriz)):
            suma = sum(Matriz[i])
            fila= [Matriz[i][j] /suma for j in range(len(Matriz[i]))]
            self.matrix.append(np.array(fila))
        self.matrix = np.array(self.matrix)
        return self.matrix
        
    