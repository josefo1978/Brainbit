import sys
import os
import pandas as pd
import numpy as np
import mne
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget, QComboBox, QPushButton, \
    QMessageBox, QHBoxLayout, QRadioButton, QButtonGroup, QLabel, QLineEdit, QDockWidget, QSizePolicy
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt, QTranslator

# Establece la configuración regional a español (cambia 'es' según tu configuración)
os.environ["LANG"] = "es_ES.UTF-8"

# Importa Matplotlib después de configurar la configuración regional
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from qtawesome import icon

class BrainBit(QMainWindow):
    def __init__(self):
            super().__init__()

            self.setWindowTitle('Analizador de Ondas EEG - BrainBit')
            self.setWindowIcon(icon('fa.signal'))
            self.setGeometry(100, 100, 800, 600)

            screen_geometry = QApplication.desktop().screenGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

            # Contenedor principal
            main_layout = QVBoxLayout()

            # Contenedor de botones
            button_container = QHBoxLayout()

            # Botón de carga
            self.load_button = QPushButton(icon('fa.file'), ' Cargar Archivo EDF', self)
            self.load_button.setCursor(QCursor(Qt.PointingHandCursor))
            self.load_button.clicked.connect(self.load_edf)
            self.load_button.setStyleSheet("background-color: #4CAF50; color: black; font-weight: bold;")  # Cambios aquí
            self.load_button.setToolTip("Haz clic para cargar un archivo EDF")  # Agregado el tooltip
            button_container.addWidget(self.load_button)

            # Grupo de botones de tipo de gráfico
            self.chart_type_group = QButtonGroup(self)
            self.muestra_button = QRadioButton("Amplitud vs Muestra", self)
            self.tiempo_button = QRadioButton("Amplitud vs Tiempo", self)
            self.frequencia_button = QRadioButton("Amplitud vs Frequencia", self)
            self.chart_type_group.addButton(self.muestra_button)
            self.chart_type_group.addButton(self.tiempo_button)
            self.chart_type_group.addButton(self.frequencia_button)
            self.chart_type_group.setExclusive(True)

            # Aplicar estilos a los radio buttons
            self.muestra_button.setStyleSheet("color: black; font-weight: bold;")  # Ajusta según tus preferencias
            self.tiempo_button.setStyleSheet("color: black; font-weight: bold;")  # Ajusta según tus preferencias
            self.frequencia_button.setStyleSheet("color: black; font-weight: bold;")  # Ajusta según tus preferencias

            button_container.addWidget(self.muestra_button)
            button_container.addWidget(self.tiempo_button)
            button_container.addWidget(self.frequencia_button)

            # Botón de ayuda
            self.help_button = QPushButton(icon('fa.question-circle'), ' Ayuda', self)
            self.help_button.setCursor(QCursor(Qt.PointingHandCursor))
            self.help_button.clicked.connect(self.show_help)
            self.help_button.setStyleSheet("background-color: #3498db; color: black; font-weight: bold;")  # Cambios aquí
            self.help_button.setToolTip("Haz clic para obtener ayuda")  # Agregado el tooltip
            button_container.addWidget(self.help_button)

            main_layout.addLayout(button_container)

            # Selector de columna
            self.chart_selector = QComboBox(self)
            self.chart_selector.setStyleSheet("background-color: #ecf0f1; color: black; font-weight: bold;")  # Añadir estilos aquí
            self.chart_selector.setEditText("Seleccione una columna")
            self.chart_selector.setToolTip("Selecciona la columna para visualizar en el gráfico")  # Agregar tooltip
            main_layout.addWidget(self.chart_selector)

            # Selector de item max
            item_layout = QVBoxLayout()
            item_container = QHBoxLayout()

            self.item_max_label = QLabel("Test")
            item_container.addWidget(self.item_max_label)

            self.item_max_text = QLineEdit()
            item_container.addWidget(self.item_max_text)

            self.item_max_text.returnPressed.connect(self.plot_chart)

            item_layout.addLayout(item_container)
            main_layout.addLayout(item_layout)

            self.item_max_label.setVisible(False)
            self.item_max_text.setVisible(False)

            # Configuración de la figura de Matplotlib
            self.figure = Figure()
            self.canvas = FigureCanvas(self.figure)
            self.toolbar = NavigationToolbar(self.canvas, self)

            # Cambia los tooltips de la barra de herramientas a español
            self.toolbar.actions()[0].setToolTip("Inicio")
            self.toolbar.actions()[1].setToolTip("Atrás")
            self.toolbar.actions()[2].setToolTip("Adelante")
            self.toolbar.actions()[4].setToolTip("Mover")
            self.toolbar.actions()[5].setToolTip("Agrandar")
            self.toolbar.actions()[6].setToolTip("Configurar Subplots")
            self.toolbar.actions()[7].setToolTip("Personalizar ejes, curva e imagen")
            self.toolbar.actions()[9].setToolTip("Guardar")

            main_layout.addWidget(self.toolbar)
            main_layout.addWidget(self.canvas)

            # Configuración de la traducción para Matplotlib
            translator = QTranslator()
            translator.load("es", "translations")
            QApplication.installTranslator(translator)

            # Establecer el diseño principal
            central_widget = QWidget()
            central_widget.setLayout(main_layout)
            self.setCentralWidget(central_widget)

            self.df = None
            self.selected_column = None

            # Configuración de botones y señales
            self.muestra_button.setChecked(False)
            self.tiempo_button.setChecked(False)
            self.frequencia_button.setChecked(False)
            self.muestra_button.setEnabled(False)
            self.tiempo_button.setEnabled(False)
            self.frequencia_button.setEnabled(False)
            self.chart_selector.setEnabled(False)
            self.chart_type_group.buttonClicked.connect(self.plot_chart)
            self.chart_selector.currentIndexChanged.connect(self.plot_chart)

    def load_edf(self):

        try:
            file_dialog = QFileDialog.getOpenFileName(self, 'Seleccionar archivo EDF', filter="Archivos EDF (*.edf)")
            file_path = file_dialog[0]

            if file_path:
                if file_path.endswith('.edf'):
                    # Cargar el archivo .edf
                    self.raw_data = mne.io.read_raw_edf(file_path, preload=True, stim_channel='auto', verbose='DEBUG')

                    # Aplicar un filtro después de cargar los datos
                    self.raw_data.filter(l_freq=0.1, h_freq=100.0)
                    
                    # Obtener los nombres de los canales
                    nombres_canales = self.raw_data.ch_names

                    self.chart_selector.setEnabled(True)
                    self.chart_selector.clear()

                    # Conservar los nombres con la primera letra en mayúscula en el ComboBox
                    self.chart_selector.addItems([col for col in nombres_canales])

                    self.figure.clear()  # Limpiar la figura al cargar un nuevo CSV
                    self.canvas.draw()
                    self.chart_selector.setEditText("Seleccione una columna")  # Restaurar el texto "Seleccione una columna"

                    self.chart_type_group.setExclusive(False)
                    self.muestra_button.setChecked(False)
                    self.tiempo_button.setChecked(False)
                    self.frequencia_button.setChecked(False)
                    self.muestra_button.setEnabled(True)
                    self.tiempo_button.setEnabled(True)
                    self.frequencia_button.setEnabled(True)
                    self.chart_type_group.setExclusive(True)
    
                else:
                    raise Exception("El archivo seleccionado no es un archivo EDF.")

            else:
                pass
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))
            self.chart_selector.setEnabled(False)
            self.muestra_button.setEnabled(False)
            self.tiempo_button.setEnabled(False)
            self.frequencia_button.setEnabled(False)
            self.figure.clear()  # Limpiar la figura al cargar un nuevo EDF
            self.canvas.draw()
            self.chart_selector.setEditText("Seleccione una columna")  # Restaurar el texto "Seleccione una columna"

    def plot_chart(self):
        if self.raw_data is not None:
            self.selected_column = self.chart_selector.currentText().upper()
            if self.selected_column and self.selected_column != "Seleccione una columna":
                self.figure.clear()
                ax = self.figure.add_subplot(111)

                try:
                    if self.muestra_button.isChecked():

                        self.item_max_label.setVisible(False)
                        self.item_max_text.setVisible(False)

                        # Crear un DataFrame de pandas
                        df = pd.DataFrame(self.raw_data.get_data().T, columns=self.raw_data.ch_names)
                        ax.plot(df.index, df[self.selected_column], color='#3498db')
                        ax.set(xlabel='Muestra', ylabel='Amplitud', title=f'Datos del canal {self.selected_column}')
                        ax.legend()

                    elif self.tiempo_button.isChecked():

                        self.item_max_label.setVisible(True)
                        self.item_max_text.setVisible(True)
                        self.item_max_label.setText("Tiempo maximo (ms): ")
                        if not self.item_max_text.text():
                            self.item_max_text.setText("10") # Atribui valor estandar 
                        self.item_max_text.setInputMask("000")
                        self.item_max_text.setToolTip("Entre con el tiempo maximo para el grafico (ms)")  # Agregar tooltip

                        tiempo_max_abs = max(self.raw_data.times.T)
                        tiempo_max_value = int(self.item_max_text.text())
                        if tiempo_max_value > tiempo_max_abs:
                            raise ValueError(f"Valor maximo para el tiempo (ms) es de {tiempo_max_abs} ms.")
                        
                        df = pd.DataFrame(data=self.raw_data.get_data().T, index=self.raw_data.times.T, columns=self.raw_data.ch_names)
                        df_subset = df[df.index < int(self.item_max_text.text())]
                        
                        ax.plot(df_subset.index, df_subset[self.selected_column])
                        ax.set(xlabel='Tiempo (ms)', ylabel='Amplitud', title=f'Datos del canal {self.selected_column}')

                    elif self.frequencia_button.isChecked():

                        self.item_max_label.setVisible(True)
                        self.item_max_text.setVisible(True)
                        self.item_max_label.setText("Frequencia maxima (Hz): ")
                        if not self.item_max_text.text():
                            self.item_max_text.setText("50") # Atribui valor estandar 
                        self.item_max_text.setInputMask("000")
                        self.item_max_text.setToolTip("Entre con la frecuencia maxima para el grafico (Hz)")  # Agregar tooltip

                        frequencia_max_value = int(self.item_max_text.text())
                        self.raw_data.plot_psd(ax=ax, fmax=frequencia_max_value, n_fft=2048, picks=self.selected_column, show=False, color="#2ecc71")
                        plt.title(f'Potencia espectral para el canal {self.selected_column}')
                        ax.set(xlabel='Frecuencia (Hz)', ylabel='Amplitud', title=f'Amplitud vs Frecuencia for {self.selected_column}')
                        ax.legend()
                        
                except ValueError as e:
                    QMessageBox.critical(self, 'Error', f"Error al procesar las columnas: {str(e)}")

                self.canvas.draw()


    def show_help(self):
        QMessageBox.information(self, 'Ayuda', "Bienvenido al Analizador de Ondas EEG - Transformada de Fourier.\n\n"
            "Pasos para usar la aplicación:\n"
            "1. Haga clic en 'Cargar Archivo CSV' para cargar un archivo CSV.\n"
            "2. Seleccione 'Amplitud vs Frecuencia' o 'Voltaje vs Tiempo' con los radio buttons.\n"
            "3. Seleccione la columna deseada en el menú desplegable.\n"
            "4. Explore las ondas EEG en el gráfico.\n"
            "5. Formato requerido del archivo CSV:\n"
            "El archivo CSV debe contener las siguientes columnas:\n"
            "\t1. 'time' - Tiempo en segundos.\n"
            "\t2. 'Alpha1' - Datos de la columna Alpha1.\n"
            "\t3. 'Alpha2' - Datos de la columna Alpha2.\n"
            "\t4. 'Beta1' - Datos de la columna Beta1.\n"
            "\t5. 'Beta2' - Datos de la columna Beta2.\n\n"
            "¡Disfrute de la aplicación!")

def run_app():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Establecer el estilo de la aplicación (puedes cambiarlo según tus preferencias)
    window = BrainBit()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_app()
