# SPDX-FileCopyrightText: 2020-2024 Ivan Perevala <ivan95perevala@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import sys
import math
import time
import multiprocessing
import concurrent.futures as cf
from functools import partial
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QListView, QTreeView, QAbstractItemView

def process_obj_files(files, input_folder, output_folder, purge_frequency):
    import bpy

    process_id = os.getpid()

    purge_counter = purge_frequency
    for obj_file in files:

        print(f"[{process_id}] Processing OBJ file: {obj_file}")
        
        input_file = os.path.join(input_folder, obj_file)
        output_file = os.path.join(output_folder, obj_file)

        # Import the Wavefront OBJ using wm.obj_import
        bpy.ops.wm.obj_import(filepath=input_file, filter_glob='*.obj;*.mtl')

        # Get the imported object by name (OBJ files will have the same name as the file, excluding the extension)
        obj_name = os.path.splitext(obj_file)[0]
        imported_object = bpy.data.objects.get(obj_name)

        if imported_object and imported_object.type == 'MESH':
            # Make the object active
            bpy.context.view_layer.objects.active = imported_object
            # Select the object
            imported_object.select_set(True)
            # Enter Edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            # Select all faces
            bpy.ops.mesh.select_all(action='SELECT')
            # Triangulate the mesh
            bpy.ops.mesh.quads_convert_to_tris(quad_method='FIXED', ngon_method='BEAUTY')
            # Return to Object mode
            bpy.ops.object.mode_set(mode='OBJECT')
            # Deselect the object
            imported_object.select_set(False)

        # Export the Wavefront OBJ with triangulation using wm.obj_export
        bpy.ops.wm.obj_export(
            filepath=output_file,
            export_triangulated_mesh=False,
            export_uv=True,
            export_normals=False,
            export_materials=False,
            filter_glob='*.obj;*.mtl'
        )

        # Print the result
        print(f"[{process_id}] Successfully saved triangulated OBJ to: {output_file}")

        # Delete all imported objects from the scene to clear memory completely
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        # Purge orphaned data blocks every N meshes
        purge_counter -= 1
        if purge_counter == 0:
            bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
            purge_counter = purge_frequency


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
        #self.working_dir_button.clicked.connect(self.select_working_directory)
        self.working_dir_button.clicked.connect(self.select_multiply_directory)
        self.working_dir_button.setFixedHeight(40)
        layout.addWidget(self.working_dir_button)

        self.working_dir_display = QtWidgets.QLabel("No directory selected")
        self.working_dir_display.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.working_dir_display)

        # Output Folder Selection

        self.output_dir_label = QtWidgets.QLabel("Select Output SubFolder:")
        self.output_dir_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.output_dir_label)

        self.output_dir_display = QtWidgets.QLineEdit()
        self.output_dir_display.editingFinished.connect(self.select_output_directory)
        self.output_dir_display.setText("tris")
        self.output_dir_display.setFixedHeight(30)
        layout.addWidget(self.output_dir_display)

        # self.output_dir_button = QtWidgets.QPushButton("Select Directory")
        # self.output_dir_button.clicked.connect(self.select_output_directory)
        # self.output_dir_button.setFixedHeight(40)
        # layout.addWidget(self.output_dir_button)

        # self.output_dir_display = QtWidgets.QLabel("No directory selected")
        # self.output_dir_display.setAlignment(QtCore.Qt.AlignCenter)
        # layout.addWidget(self.output_dir_display)

        # Number of Threads SpinBox
        self.threads_label = QtWidgets.QLabel("Number of Threads:")
        layout.addWidget(self.threads_label)

        self.threads_spinbox = QtWidgets.QSpinBox()
        self.threads_spinbox.setRange(1, 64)
        self.threads_spinbox.setValue(multiprocessing.cpu_count()//2)
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

        # Set alway on top
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    def select_working_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if directory:
            self.working_dir_display.setText(directory)
            self.input_folder = directory

    def select_multiply_directory(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)  # Force non-native dialog to enable multiple selection
        dialog.setOption(QFileDialog.ShowDirsOnly, True)         # Show directories only

        dialog.setWindowTitle("Select Working Directories")
        dialog.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # Use the QListView and QTreeView to allow multi-selection
        list_view = dialog.findChild(QListView, 'listView')
        if list_view:
            list_view.setSelectionMode(QAbstractItemView.MultiSelection)

        tree_view = dialog.findChild(QTreeView, 'treeView')
        if tree_view:
            tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

        if dialog.exec_():
            directories = dialog.selectedFiles()  # Retrieve selected directories
            self.working_dir_display.setText("Multiple directories selected")
            self.input_folders = directories

    # def select_output_directory(self):
    #     directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory")
    #     if directory:
    #         self.output_dir_display.setText(directory)
    #         self.output_folder = directory
    #         if not os.path.exists(self.output_folder):
    #             os.makedirs(self.output_folder)

    def select_output_directory(self):
        directory = QtWidgets.QLineEdit.text(self.output_dir_display)
        if directory:
            self.output_dir_display.setText(directory)
            self.output_sub_folder = directory

    def start_triangulation(self):
        if not hasattr(self, 'input_folders'):
            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                "Please select a working directory[es]."
            )
            return

        start_time = time.time()
        total_files = 0

        input_folders = self.input_folders
        output_sub_folder = self.output_dir_display.text()
        num_processes = self.threads_spinbox.value()
        purge_frequency = self.purge_spinbox.value()

        for input_folder in input_folders:
            print(f"Processing OBJ files in: {input_folder}")
            output_folder = os.path.join(input_folder, output_sub_folder)
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            print(f"Saving triangulated OBJ files to: {output_folder}")

            # Get a list of all OBJ files in the input folder
            obj_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith('.obj')])

            # Split the list into batches for each process
            batch_size = math.ceil(len(obj_files) / num_processes)
            chunks = [obj_files[i:i + batch_size] for i in range(0, len(obj_files), batch_size)]

            # Start timing
            local_start_time = time.time()

            process_obj_files_with_args = partial(process_obj_files, input_folder=input_folder, output_folder=output_folder, purge_frequency=purge_frequency)
        
            with cf.ProcessPoolExecutor(max_workers=num_processes) as executor:
                executor.map(process_obj_files_with_args, chunks)

            # End timing
            local_end_time = time.time()

            # Print summary
            local_total_time = local_end_time - local_start_time
            local_total_files = len(obj_files)
            print("All subprocesses completed.")
            print(f"Processed {local_total_files} OBJ files in {num_processes} parallel processes.")
            print(f"Total processing time: {local_total_time:.2f} seconds")
            total_files += local_total_files

        # End timing
        end_time = time.time()
        total_time = end_time - start_time
        print("All files completed.")
        print(f"Processed {total_files} OBJ files in {num_processes} parallel processes.")
        print(f"Total processing time: {total_time:.2f} seconds")

if __name__ == '__main__':
    original_dir = os.getcwd()
    os.chdir(os.path.dirname(__file__))

    app = QtWidgets.QApplication(sys.argv)
    window = TriangulationApp()
    window.show()
    sys.exit(app.exec_())

    os.chdir(original_dir)
