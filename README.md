# GIMP 3.0 Save Mask and Next

A Python GIMP 3.0 plugin designed to accelerate manual image segmentation and masking workflows. It automates the "Save -> Close -> Open Next -> Setup Layers" cycle.

## Overview

When performing manual image segmentation (painting masks), the overhead of saving each mask and opening the next file adds up. This plugin allows you to:

1.  **Extract** the current image name from GIMP's `[Name] (imported)` format.
2.  **Save** a layer named "Mask" as a `.png` into a specific `..._masks` folder.
3.  **Close** the current image.
4.  **Open** the next alphabetical PNG in the directory.
5.  **Initialize** a new "Mask" layer automatically so you can keep painting.

## Requirements

- **GIMP 3.0** (or higher)
- **Python 3**
- **GObject Introspection (gi) libraries** (included with standard GIMP 3.0 Python environments)

## Installation

1.  **Locate your GIMP 3.0 Plug-ins folder:**
    - **Windows:** `%APPDATA%\GIMP\3.0\plug-ins\`
    - **Linux:** `~/.config/GIMP/3.0/plug-ins/`
2.  **Create a subfolder** named `save_mask_and_next`.
3.  **Place the script** inside that folder and rename it to `save_mask_and_next.py`.
4.  **Make it executable** (Linux/macOS only):
    ```bash
    chmod +x save_mask_and_next.py
    ```

## Configuration

### File paths

**Important:** You must edit the top of the script to set your specific file paths:

- `IMG_DIR` (**IMPORTANT**): The directory where your source PNG images are stored.
- `OPACITY` (_Optional_): The default opacity (0-100) for the new mask layer.
- `CONFIG_FILE` (_Optional_): A path where the plugin can save its internal state (JSON).
- `DEBUG_FILE` (_Optional_): A path for the debug log (useful if things go wrong).

### Keyboard shortcut

To make your workflow significantly faster, assign a keyboard shortcut to this plugin:

1.  Go to **Edit > Keyboard Shortcuts**.
2.  Search for **"Save Mask and Next"**.
3.  Click on the row and press your preferred key combination.
4.  Now you can save and move to the next image with a single keystroke!

## Usage

### 1. The First Run

1.  Open GIMP 3.0.
2.  Open your **first image** normally via `File > Open`.
3.  Go to **File > Save Mask and Next**.
4.  The plugin will detect this is a new session. It will create a new layer named **"Mask"** at the specified opacity and fill it with black.
5.  Paint your mask on this layer (using white/colors as needed).

### 2. The Sequential Workflow

1.  Once you finish painting the mask, go to **File > Save Mask and Next** again.
2.  The plugin will:
    - Flatten the image (applying the mask).
    - Save the result to `YOUR_FOLDER_masks/ORIGINAL_NAME_mask.png`.
    - Close the current image.
    - Open the next PNG in the folder.
    - Create a fresh "Mask" layer on the new image.

## Debugging

If the plugin fails to run:

1.  Check the `gimp_plugin_debug.txt` file (path defined in the script).
2.  Ensure that a folder named `_masks` can be created in your source directory.
3.  Ensure the GIMP console is open for error messages (`Windows > Dockable Dialogs > Error Console`).

## License

This project is licensed under the MIT License.
