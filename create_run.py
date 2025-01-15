import os
import sys
import shutil
import yaml
import pathlib
import datetime
import subprocess
from typing import Dict


CONFIG_FILE = './config_run.yaml'

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


def get_git_hash(path: pathlib.Path) -> str:
    """Changes to github directory, gets the short hash and returns to previous directory

    Args:
        path (pathlib.Path): github path

    Returns:
        git code hash
    """    
    prev_cwd = pathlib.Path.cwd()
    os.chdir(path)
    codehash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    os.chdir(prev_cwd)

    return codehash
    
# ------------------------------------------------------------------------------------- #

print(f"")
print(f"Running create_ideal.py with python version: {sys.version}")

# Read configuration file
config = read_config(pathlib.Path(CONFIG_FILE))
if config['verbose']: print(config)

# Create runtime directory
rundirpath = pathlib.Path(config['rootdir'] + config['rundir'])

if config['date_as_dir']:
    rightnow = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    rundirpath = rundirpath / rightnow

rundirpath.mkdir(parents=True, exist_ok=False)
print(f"Created directory: {rundirpath}")
print(f"")

# Link or copy all file groups under key mpasfiles
key = 'mpasfiles'
for filesetkey in config[key]:
    dstdir = config[key][filesetkey]['dir']

    if not '/' in dstdir:
        resolved_path = pathlib.Path('./' + dstdir).resolve()
    else:
        resolved_path = pathlib.Path(dstdir).resolve()
        
    files = config[key][filesetkey]['files']
    linkorcopy = config[key][filesetkey]['action']
    link = True
    if linkorcopy == 'copy': link = False
    for f in files:
        src = pathlib.Path(resolved_path) / pathlib.Path(f)
        dst = rundirpath / pathlib.Path(f)
        if src.is_file():
            link_or_copy(src, dst, link)
        else:
            print(f"*******")
            print(f"WARNING...File not found ")
            print(f"and will NOT be linked or copied to run directory: {src}")
            print(f"*******")

        if src == pathlib.Path(config['mpasexedir']) / pathlib.Path(config['mpasexefile']):
            print(f"Found compiled executable")
            saveexedir = pathlib.Path(config['mpasexedir'])
        
# Create script to run init and ideal case
runscript = rundirpath / pathlib.Path("run.sh")
fwrite = open(runscript, "x")
fwrite.write(f"#!/bin/bash\n")
fwrite.write(f"set -x\n\n")
sub_job01 = f"sbatch --account={config['account']} run_atmosphere_model.sh\n"
fwrite.write(sub_job01)
# sub_job02 = f"sbatch -d afterok:${{runid}} --account={config['account']} run_atmosphere_model.sh\n"
# fwrite.write(sub_job02)
fwrite.close()

# Link latest run directory to this folder
linkrun = pathlib.Path.cwd() / pathlib.Path('latest_run')
if linkrun.is_symlink(): linkrun.unlink(missing_ok=True)
linkrun.symlink_to(rundirpath, target_is_directory=True)

# Write MPAS executable code hash
gitcodehash = get_git_hash(saveexedir)
writecodehash = rundirpath / pathlib.Path("MPAS-HASH")
fwrite = open(writecodehash, "x")
fwrite.write(f"{gitcodehash}")
fwrite.close()

