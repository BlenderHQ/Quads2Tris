# SPDX-FileCopyrightText: 2020-2024 Ivan Perevala <ivan95perevala@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import subprocess
import math
import time
from PyQt5 import QtWidgets, QtCore
import sys


class TriangulationApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        # set stylesheet
        with open("style.qt", 'r') as stylesheet_file:
            stylesheet_data = stylesheet_file.read()

        self.setStyleSheet(stylesheet_data)

        # Layout setup
        layout = QtWidgets.QVBoxLayout()

        # Working Directory Selection
        self.working_dir_label = QtWidgets.QLabel("Select Working Directory:")
        self.working_dir_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.working_dir_label)

        self.working_dir_button = QtWidgets.QPushButton("Select Directory")
        self.working_dir_button.clicked.connect(self.select_working_directory)
        self.working_dir_button.setFixedHeight(40)
        layout.addWidget(self.working_dir_button)

        self.working_dir_display = QtWidgets.QLabel("No directory selected")
        self.working_dir_display.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.working_dir_display)

        # Output Folder Selection
        self.output_dir_label = QtWidgets.QLabel("Select Output Folder:")
        self.output_dir_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.output_dir_label)

        self.output_dir_button = QtWidgets.QPushButton("Select Directory")
        self.output_dir_button.clicked.connect(self.select_output_directory)
        self.output_dir_button.setFixedHeight(40)
        layout.addWidget(self.output_dir_button)

        self.output_dir_display = QtWidgets.QLabel("No directory selected")
        self.output_dir_display.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.output_dir_display)

        # Number of Threads SpinBox
        self.threads_label = QtWidgets.QLabel("Number of Threads:")
        layout.addWidget(self.threads_label)

        self.threads_spinbox = QtWidgets.QSpinBox()
        self.threads_spinbox.setRange(1, 64)
        self.threads_spinbox.setValue(8)
        self.threads_spinbox.setFixedHeight(30)
        layout.addWidget(self.threads_spinbox)

        # Purge Counter SpinBox
        self.purge_label = QtWidgets.QLabel("Purge Frequency (Number of Meshes):")
        self.purge_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.purge_label)

        self.purge_spinbox = QtWidgets.QSpinBox()
        self.purge_spinbox.setRange(1, 1000)
        self.purge_spinbox.setValue(25)
        self.purge_spinbox.setFixedHeight(30)
        layout.addWidget(self.purge_spinbox)

        # Start Button
        self.start_button = QtWidgets.QPushButton("Start Triangulation")
        self.start_button.clicked.connect(self.start_triangulation)
        self.start_button.setFixedHeight(40)
        layout.addWidget(self.start_button)

        # Set layout
        self.setLayout(layout)
        self.setWindowTitle("OBJ Triangulation Tool")
        self.setGeometry(300, 300, 400, 300)

        # set alway on top
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    def select_working_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if directory:
            self.working_dir_display.setText(directory)
            self.input_folder = directory

    def select_output_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_display.setText(directory)
            self.output_folder = directory
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)

    def start_triangulation(self):
        if not hasattr(self, 'input_folder') or not hasattr(self, 'output_folder'):
            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                "Please select both a working directory and an output directory first."
            )
            return

        input_folder = self.input_folder
        output_folder = self.output_folder
        num_processes = self.threads_spinbox.value()
        purge_frequency = self.purge_spinbox.value()

        # Get a list of all OBJ files in the input folder
        obj_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith('.obj')])

        # Split the list into batches for each process
        batch_size = math.ceil(len(obj_files) / num_processes)
        batches = [obj_files[i:i + batch_size] for i in range(0, len(obj_files), batch_size)]

        # Start timing
        start_time = time.time()

        # Create and launch a Python subprocess for each batch using pipes
        processes = []
        for idx, batch in enumerate(batches):
            # Construct the command
            cmd = ["python", "triangulate_mesh_batch.py", input_folder, output_folder]
            print(f"Launching subprocess {idx} with command: {' '.join(cmd)}")

            # Run the triangulation script in a subprocess and use the pipe to send the batch data
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True, start_new_session=True)
            process.stdin.write('\n'.join(batch) + '\n')
            process.stdin.close()  # Close stdin to indicate we're done writing to it
            processes.append(process)

        # Wait for all subprocesses to complete
        for process in processes:
            process.wait()

        # End timing
        end_time = time.time()

        # Print summary
        total_time = end_time - start_time
        total_files = len(obj_files)
        print("All subprocesses completed.")
        print(f"Processed {total_files} OBJ files in {num_processes} parallel processes.")
        print(f"Total processing time: {total_time:.2f} seconds")


if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))

    app = QtWidgets.QApplication(sys.argv)
    window = TriangulationApp()
    window.show()
    sys.exit(app.exec_())
