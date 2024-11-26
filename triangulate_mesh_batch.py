import bpy
import os
import sys

# Read input arguments
if len(sys.argv) < 3:
    raise ValueError("Not enough arguments provided. Usage: python triangulate_mesh_batch.py <input_folder> <output_folder> <obj_files...>")

input_folder = sys.argv[1]
output_folder = sys.argv[2]
obj_files = sys.stdin.read().splitlines()  # Read the list of OBJ files from stdin

print(f"Starting processing with input folder: {input_folder} and output folder: {output_folder}")
print(f"Processing files: {obj_files}")

# Clear existing mesh objects to start fresh
bpy.ops.wm.read_factory_settings(use_empty=True)

# Counter for purging orphaned data blocks, initialized to 100
purge_counter = 100

# Function to process a single OBJ file
def process_obj_file(obj_file, input_folder, output_folder):
    global purge_counter
    print(f"Processing OBJ file: {obj_file}")

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
    bpy.ops.wm.obj_export(filepath=output_file, export_triangulated_mesh=False, export_uv=True, export_normals=False, export_materials=False, filter_glob='*.obj;*.mtl')

    # Print the result
    print(f"Successfully saved triangulated OBJ to: {output_file}")

    # Delete all imported objects from the scene to clear memory completely
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Purge orphaned data blocks every 100 meshes
    purge_counter -= 1
    if purge_counter == 0:
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        purge_counter = 100

# Process each OBJ file sequentially
for obj_file in obj_files:
    process_obj_file(obj_file, input_folder, output_folder)
