import os
import sys
import shutil
import yaml
import pathlib
import datetime
from typing import Dict


CONFIG_FILE = './config_lbcs.yaml'

def read_config(CFILE: pathlib.Path) -> Dict[str, str]:
    """
    Reads a yaml config file

    Args:
        CFILE (pathlib.Path): Config file path.

    Returns:
        config (Dict[str, str]): config dictionary 
    """    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = yaml.safe_load(f)
            
        print(f"Read config file: {CONFIG_FILE}")
        return config_data
    except FileNotFoundError as e:
        print(f"Error: {e}")


def link_or_copy(src: pathlib.Path, dst: pathlib.Path, link: bool = True) -> None:
    """
    Links or copies files from src to dst directories

    Args:
        src (pathlib.Path): source path.
        dst (pathlib.Path): destination path.
        link (boolean): if True, file will be linked, else file will be copied

    Returns:
        None
    """        
    if link:
        dst.symlink_to(src, target_is_directory=False)
        print(f"...Linked file {src} to run directory")
    else:
        shutil.copy(src, dst)
        print(f"...Copied file {src} to run directory")


def check_or_backup(src: pathlib.Path, backup: bool = False) -> None:
    """
    Checks if a file exists with an option to back up the file

    Args:
        src (pathlib.Path): source path.
        backup (boolean): if True, file will be backup, else file existence will be checked

    Returns:
        None
    """        
    if backup:
        print(f"...Backing up file if found")
        rightnow = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        dst = pathlib.Path(str(src) + '_' + rightnow)
        print(f"...Copied file {src} to {dst}")
        shutil.copy(src, dst)
    else:
        print(f"...Checking for file {src}")
        if src.is_file():
            print("   ... File exists")
        else:
            print(f"COULD NOT FIND FILE: {src}")
            
# ------------------------------------------------------------------------------------- #

print(f"")
print(f"Running create_ideal.py with python version: {sys.version}")

# Read configuration file
config = read_config(pathlib.Path(CONFIG_FILE))
if config['verbose']: print(config)

# Check that ICs were created before creating LBCs
icsdir = pathlib.Path('./' + config['rundir'])
print(f"Directory with latest ICs: {icsdir.resolve()}")

# Check for files
key = 'filecheck'
for filesetkey in config[key]:
    dstdir = config[key][filesetkey]['dir']
    files = config[key][filesetkey]['files']
    checkorbackup = config[key][filesetkey]['action']
    backup = False
    if checkorbackup == 'backup': backup = True

    if not '/' in dstdir:
        resolved_path = pathlib.Path('./' + dstdir).resolve()
    else:
        resolved_path = pathlib.Path(dstdir).resolve()

    for f in files:
        src = resolved_path / pathlib.Path(f)
        check_or_backup(src, backup)
        
# Link or copy all file groups under key mpasfiles
key = 'mpasfiles'
for filesetkey in config[key]:
    dstdir = config[key][filesetkey]['dir']
    files = config[key][filesetkey]['files']
    linkorcopy = config[key][filesetkey]['action']
    link = True
    if linkorcopy == 'copy': link = False
    for f in files:
        src = pathlib.Path(dstdir) / pathlib.Path(f)
        dst = icsdir / pathlib.Path(f)
        if src.is_file():
            link_or_copy(src, dst, link)
        else:
            print(f"*******")
            print(f"WARNING...File not found ")
            print(f"and will NOT be linked or copied to run directory: {src}")
            print(f"*******")



