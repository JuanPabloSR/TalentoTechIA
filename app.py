import numpy as np
import matplotlib.pyplot as plt

class Perceptron: #creación de la clase Perceptron
    """pereceptron classifier
    parametros
    
    eta: float
        tasa de aprendizaje (entre 0.0 y 1.0)
    n_iter: int
        iteraciones  sobre el conjunto de datos de entrenamiento
    random_state: int
        semilla del generador de números aleatorios para la inicialización aleatoria de pesos

    Attributes
    ----------
    w_: 1d-array
        pesos despues del entrenamiento
    b_: escalar
        sesgo despues del entrenamiento

    errors_: list
        Número de errores de clasificación (actualizaciones) en cada época
            
        """
    def __init__(self, eta=0.01, n_iter=50, random_state=42): # Inicializa los hiperparámetros
        self.eta = eta # Tasa de aprendizaje, un valor entre 0.0 y 1.0 que controla cuánto se ajustan los pesos en cada iteración.
        self.n_iter = n_iter # Número de iteraciones (épocas) sobre el conjunto de datos de entrenamiento.
        self.random_state = random_state # Semilla para el generador de números aleatorios, lo que permite reproducir los resultados al inicializar los pesos de manera aleatoria.

    def fit(self, X, y): # Ajuste de datos de entrenamiento 
        """Ajuste de datos de entrenamiento

        Parámetros
        ----------
        X: {array-like}, shape = [n_samples, n_features]
            Vectores de entrenamiento, donde n_samples es el número de muestras y
            n_features es el número de características. Significa que puede ser cualquier objeto que se comporte como un array (arreglo), por ejemplo: Una lista de listas de Python, Un array de NumPy (numpy.ndarray), Un DataFrame de Pandas (Siempre que tenga forma de tabla).
        y: array-like, shape = [n_samples]
            es el nombre convencional para el vector de salida, también llamado etiqueta, target o variable dependiente. Valores objetivo. Es decir, son los valores que quieres predecir o clasificar con tu modelo.
            array-like:
            Significa que puede ser una lista de Python, un array de NumPy o una Serie de Pandas, pero debe comportarse como un vector (no una tabla).
        """
        rgen = np.random.RandomState(self.random_state) # generador de números aleatorios de Numpy con semilla 42 ver línea 26 (valor por defecto asignado de manera arbitraria)
        self.w_ = rgen.normal(loc=0.0, scale=0.01, size=X.shape[1]) # Inicializa los pesos con una distribución normal centrada loc en 0.0 y desviación estándar, scale, de 0.01, size: número de características (columnas) en X, lo que significa que el vector de pesos tendrá la misma longitud que el número de características en los datos de entrada.
        self.b_ = np.float64(0.0) # Inicializa el sesgo (bias) a 0.0, np.float_ es una forma de asegurar que el tipo de dato sea un número flotante de Numpy, lo que es útil para mantener la consistencia en cálculos posteriores.
        self.errors_ = [] # Lista para almacenar el número de errores en cada iteración (época)

        for _ in range(self.n_iter): # Itera sobre el número de épocas especificado por n_iter
            """- for: Inicia un bucle que se repetirá un número determinado de veces.
            - _ (guion bajo): Es una convención en Python que indica “no me importa esta variable”. Es decir, aunque Python necesita un nombre para cada iteración, en este caso no necesitas usarlo dentro del bucle.
            - range(self.n_iter): Crea una secuencia de números desde 0 hasta self.n_iter - 1. Si self.n_iter = 50, se harán 50 repeticiones."""

            errors = 0 # Inicializa el contador de errores para esta época
            for xi, target in zip(X, y): # Itera sobre cada muestra de entrenamiento (xi) y su correspondiente etiqueta (target)
                """- zip(X, y): Combina los elementos de X e y en pares.
                - xi: Es un vector que representa una sola muestra de entrenamiento (una fila de X).
                - target: Es la etiqueta correspondiente a la muestra xi.
                """
                update = self.eta * (target - self.predict(xi)) # Calcula la actualización de los pesos. Aquí, self.predict(xi) devuelve la predicción del perceptrón para la muestra xi, y target es la etiqueta real. La diferencia (target - self.predict(xi)) indica cuánto se desvía la predicción del objetivo real.
                self.w_ += update * xi # Actualiza los pesos multiplicando la actualización por la muestra xi. Esto ajusta los pesos en función de la entrada y la diferencia entre la predicción y el objetivo.
                self.b_ += update # Actualiza el sesgo (bias) con la misma actualización calculada anteriormente.
                errors += int(update != 0.0) # Incrementa el contador de errores si la actualización no es cero. Esto significa que hubo un error de clasificación, ya que el perceptrón ajustó sus pesos para corregir la predicción.
            self.errors_.append(errors) # Almacena el número de errores para esta época en la lista errors_
        
        return self # Devuelve la instancia del perceptrón para permitir el encadenamiento de métodos
    def net_input(self, X): 
        """Calcula la entrada neta para un vector de características X"""
        return np.dot(X, self.w_) + self.b_ # Calcula el producto punto entre las características X y los pesos w_, y luego suma el sesgo b_. Esto da como resultado la entrada neta del perceptrón, que es la suma ponderada de las características más el sesgo.

    def predict(self, X):
        """Realiza una predicción para un vector de características X"""
        return np.where(self.net_input(X) >= 0.0, 1, 0) # Devuelve 1 si la entrada neta es mayor o igual a 0, de lo contrario devuelve 0.


# Datos de entrenamiento
X = np.array([[2, 3],
              [4, 1],
              [1, 6],
              [2, 4],
              [6, 2],
              [7, 3]])
y = np.array([0, 0, 1, 1, 0, 0])  # Etiquetas binarias

# Crear y entrenar el Perceptrón
modelo = Perceptron(eta=0.1, n_iter=10)
modelo.fit(X, y)

# Ver errores por época
print("Errores por época:", modelo.errors_)

# Predecir nuevas muestras
nuevas = np.array([[3, 2], [1, 5]])
predicciones = modelo.predict(nuevas)
print("Predicciones:", predicciones)

plt.scatter(X[:, 0], X[:, 1], c=y, marker='o', label='Datos de entrenamiento')
plt.scatter(nuevas[:, 0], nuevas[:, 1], c='red', marker='x', label='Nuevas muestras')
plt.xlabel('Característica 1')
plt.ylabel('Característica 2')
plt.legend()
plt.show()