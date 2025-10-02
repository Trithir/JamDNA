import os
import shutil

CLUSTERS_ROOT = os.path.abspath(os.path.join("..", "data", "clusters"))

def ensure_cluster_folder(name: str) -> str:
    """
    Ensure a folder exists for a given cluster name.
    Returns the absolute path to the folder.
    """
    safe_name = name.replace(" ", "_")
    folder = os.path.join(CLUSTERS_ROOT, safe_name)
    os.makedirs(folder, exist_ok=True)
    return folder

def move_track_to_cluster(track_path: str, cluster_name: str) -> str:
    """
    Move a track file into the correct cluster folder.
    Returns the new absolute path.
    """
    folder = ensure_cluster_folder(cluster_name)
    basename = os.path.basename(track_path)
    new_path = os.path.join(folder, basename)
    shutil.move(track_path, new_path)
    return new_path

def rename_cluster_folder(old_name: str, new_name: str):
    """
    Rename a cluster folder if it exists.
    """
    old_folder = os.path.join(CLUSTERS_ROOT, old_name.replace(" ", "_"))
    new_folder = os.path.join(CLUSTERS_ROOT, new_name.replace(" ", "_"))
    if os.path.exists(old_folder):
        os.rename(old_folder, new_folder)
