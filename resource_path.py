"""
Utility module to find resource files in both development and packaged (py2app) environments.
"""
import os
import sys

def get_resource_path(relative_path):
    """
    Get the absolute path to a resource file.
    
    Works in both:
    - Development mode (files in same directory as script)
    - Packaged mode (files in Contents/Resources inside .app bundle)
    
    Args:
        relative_path: Path relative to the resource directory (e.g., "music/song.mp3")
    
    Returns:
        Absolute path to the resource file
    """
    # In a py2app bundle, sys.frozen is set to a py2app-specific value
    if getattr(sys, 'frozen', None) == 'macosx_app':
        # py2app case - the script files are in Contents/Resources/
        # and all resources are also in Contents/Resources/
        base_path = os.path.dirname(os.path.dirname(sys.executable))  # Go from MacOS/python to Contents
        base_path = os.path.join(base_path, 'Resources')
    else:
        # Development mode - get directory of this file
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    resource_path = os.path.join(base_path, relative_path)
    
    if not os.path.exists(resource_path):
        print(f"WARNING: Resource not found at {resource_path}")
        print(f"Base path: {base_path}")
        print(f"Relative path: {relative_path}")
        print(f"sys.frozen: {getattr(sys, 'frozen', None)}")
        print(f"sys.executable: {sys.executable}")
    
    return resource_path


# For backwards compatibility - expose the common use case
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
