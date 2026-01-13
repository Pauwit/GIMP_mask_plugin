#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This GIMP 3.0 plugin was coded by Paul Witkowski.

import os
import glob
import sys
import gi
gi.require_version("Gimp", "3.0")
from gi.repository import Gimp, Gio, GLib, Gegl
from enum import Enum
import re
import json

IMG_DIR = os.path.expanduser("~\\Documents\\Stage\\papillae_detection\\new_images\\pngs")
CONFIG_FILE = os.path.expanduser("~\\AppData\\Roaming\\GIMP\\3.0\\plug-ins\\save_mask_and_next\\config.json")
DEBUG_FILE = os.path.expanduser("~\\AppData\\Roaming\\GIMP\\3.0\\plug-ins\\save_mask_and_next\\gimp_plugin_debug.txt")
OPACITY = 10.0

# Debug
class DebugLevel(Enum):
    INFO = 'INFO'
    WARNING = 'WARN'
    ERROR = 'ERROR'

def log(msg, level: DebugLevel = DebugLevel.INFO):
    message = f"[{str(level)}] {msg}"
    if level != DebugLevel.INFO:
        Gimp.message(message)
    with open(DEBUG_FILE, "a") as f:  # append mode
        f.write(message + "\n")
        f.flush()

#Config
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)
    
def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

# PlugIn
class SaveMaskAndNext(Gimp.PlugIn):

    def do_query_procedures(self):
        return ["python-save-mask-and-next"]

    def do_create_procedure(self, name):
        proc = Gimp.ImageProcedure.new(
            self, name,
            Gimp.PDBProcType.PLUGIN,
            self.run,
            None
        )
        proc.set_image_types("*")
        proc.set_attribution("Paul Witkowski", "MIT", "2026/01/13")
        proc.set_documentation(
            f"Saves the top mask layer as <basename>_mask.png in {IMG_DIR}_masks folder, closes the current image, then opens the next PNG and creates a new mask layer",
            ""
        )
        proc.set_menu_label("Save Mask and Next")
        proc.add_menu_path("<Image>/File")
        return proc

    def first_run(self, procedure, run_mode, image, drawables, config, run_data):
        # Create a new mask layer
        width = image.get_width()
        height = image.get_height()

        mask_layer = Gimp.Layer.new(
            image, "Mask", width, height,
            Gimp.ImageType.RGB_IMAGE, OPACITY,
            Gimp.LayerMode.NORMAL
        )
        image.insert_layer(mask_layer, None, 0)

        # Fill with black
        Gimp.context_set_foreground(Gegl.Color.new("#ffffff"))
        Gimp.context_set_background(Gegl.Color.new("#000000"))
        mask_layer.fill(Gimp.FillType.BACKGROUND)

        log("Mask layer created and ready for painting!")

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

    def run(self, procedure, run_mode, image, drawables, _, run_data):
        log("Start")

        # Init config
        config = load_config()
        log(f"Loaded config: {config}")
        current_file = config.get('current_file', None) # string
        current_display_id = config.get('current_display_id', 1) # int
        ppid = config.get('ppid', 0) # int

        # Restarted?
        if ppid != os.getppid():
            log("First run of session. Identifying file...")

            raw_name = image.get_name()
            log(f"GIMP Image Name: {raw_name}")

            match = re.search(r"\[(.*?)\]", raw_name)

            if not match:
                log("Could not find image name to match with regex.", DebugLevel.ERROR)
                return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, None)

            base_filename = match.group(1)
            log(f"Extracted base name: {base_filename}")
            
            config['current_file'] = os.path.join(IMG_DIR, base_filename + ".png")
            config['current_display_id'] = 1
            config['ppid'] = os.getppid()
            save_config(config)

            log(f"Mapped to filesystem: {config['current_file']}")
            return self.first_run(procedure, run_mode, image, drawables, _, run_data)
        
        log("Not first run of session.")
        # --- Get filename of current image ---
        image_filename = current_file
        log(f"File name : {image_filename}")
        if not image_filename:
            log("Image must be saved on disk before using this plugin.", DebugLevel.WARNING)
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, None)

        log("Getting filenames...")
        src_dir = os.path.dirname(image_filename)  # e.g. project/train
        base_name = os.path.splitext(os.path.basename(image_filename))[0]

        # --- Mask folder (sibling to image folder) ---
        mask_dir = src_dir + "_masks"
        log(f"src_dir: {src_dir} ; base_name: {base_name} ; mask_dir : {mask_dir}")
        if not os.path.exists(mask_dir):
            try:
                os.makedirs(mask_dir)
                log(f"Created mask directory.")
            except Exception as e:
                log(f"Could not create mask folder: {e}", DebugLevel.ERROR)
                return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, None)
    
        mask_name = f"{base_name}_mask.png"
        mask_path = os.path.join(mask_dir, mask_name)
        log(f"File name will be: {str(mask_path)}")

        # --- Find the "Mask" layer ---
        mask_layer = None
        for layer in image.get_layers():
            if layer.get_name() == "Mask":
                mask_layer = layer
                break

        log(f"Mask layer found: {mask_layer}")

        if mask_layer:
            try:
                # Duplicate image and keep only the mask layer
                #temp_image = Gimp.Image.new(image.get_width(), image.get_height(), Gimp.ImageBaseType.RGB)
                #dup_layer = mask_layer.copy()
                #dup_layer.set_opacity(100.0)  # force full opacity when saving
                #temp_image.insert_layer(dup_layer, None, 0)

                # Flatten to remove alpha
                #temp_image.flatten()
                mask_layer.set_opacity(100.0)
                image.flatten()
            except Exception as e:
                log(f"Error while preparing: {e}", DebugLevel.ERROR)
                return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, None)

            log("Finished preparing image.")

            # Save mask
            try:
                log("Start save.")
                mask_file = Gio.File.new_for_path(mask_path)
                log(f"mask_file: {mask_file.get_path()}")
                success = Gimp.file_save(
                    Gimp.RunMode.NONINTERACTIVE,  # or INTERACTIVE if you want dialogs
                    image,
                    mask_file,
                    None  # options not used
                )
                if success:
                    log(f"Saved mask: {mask_path}")
                else:
                    log(f"Failed to save mask at {mask_path}", DebugLevel.ERROR)
                    return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, None)
            except Exception as e:
                log(f"Error saving mask: {e}", DebugLevel.ERROR)
            #finally:
                #Gimp.image_delete(temp_image)
        else:
            log("No layer named 'Mask' found!", DebugLevel.ERROR)
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, None)

        # --- Find next image in folder ---
        pattern = os.path.join(src_dir, "*.png")
        all_png = sorted(glob.glob(pattern))
        next_file = None
        try:
            idx = all_png.index(image_filename)
        except ValueError:
            log("ValueError", DebugLevel.ERROR)
            idx = -1
        if idx >= 0 and idx + 1 < len(all_png):
            next_file = all_png[idx + 1]
        log(f"next_file: {next_file}")
        if next_file == None:
            log("Couldn't find next file.", DebugLevel.ERROR)
        config['current_file'] = next_file # save next file path
        save_config(config)
        next_file = Gio.File.new_for_path(next_file)

        # --- Close current image ---
        try:
            log("Deleting...")
            id = image.get_id()
            log(id)
            display = Gimp.Display.get_by_id(current_display_id)
            log(display)
            image.delete()
            #display.delete()
            log("Deleted.")
        except Exception as e:
            log(f"Error while deleting: {e}", DebugLevel.ERROR)
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, None)

        #log(display.delete())
        #for display in image.list_displays():
        #    display.delete()
        #try:
        #    if self.current_display != None:
        #        self.current_display.delete()
        #        image.delete()
        #    log(f"Closed image.")
        #except Exception as e:
        #    log(f"Exception while deleting: {e}", DebugLevel.ERROR)

        # --- Open next image ---
        if next_file:
            try:
                log("Trying to load next file.")
                loaded = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, next_file)
                current_display_id = Gimp.Display.new(loaded).get_id()
                log(f"current_display_id: {current_display_id}")
                config['current_display_id'] = current_display_id
                save_config(config)
                log("Loaded successfully")

                # Create a new mask layer (black, opacity)
                width = loaded.get_width()
                height = loaded.get_height()
                mask_layer = Gimp.Layer.new(
                    loaded, "Mask", width, height,
                    Gimp.ImageType.RGB_IMAGE, OPACITY,
                    Gimp.LayerMode.NORMAL
                )
                loaded.insert_layer(mask_layer, None, 0)
                log("Inserted new layer.")

                # Fill with black
                Gimp.context_set_foreground(Gegl.Color.new("#ffffff"))
                Gimp.context_set_background(Gegl.Color.new("#000000"))
                mask_layer.fill(Gimp.FillType.BACKGROUND)

                log("Setup complete.")

            except Exception as e:
                log(f"Could not open next image {next_file.get_path()}: {e}", DebugLevel.ERROR)
                return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, None)
        else:
            log("No more .png images in folder.", DebugLevel.WARNING)

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)


Gimp.main(SaveMaskAndNext.__gtype__, sys.argv)