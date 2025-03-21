import os
import sys
import shutil
import yaml
import pathlib
import datetime
import argparse
from typing import Dict

parser = argparse.ArgumentParser(description='Create MPAS ICs')
parser.add_argument('-f','--file', help='YAML configuration file', required=True)
args = vars(parser.parse_args())

CONFIG_FILE = args['file']
if pathlib.Path(CONFIG_FILE).is_file():
    print(f"Using YAML configuration file: {CONFIG_FILE}")
else:
    sys.exit(f"YAML configuration file: {CONFIG_FILE} does not exist... Exiting")


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

# Link current run directory to easy name
#linkrun = pathlib.Path.cwd() / pathlib.Path('latest_run')
#if linkrun.is_symlink(): linkrun.unlink(missing_ok=True)
#linkrun.symlink_to(rundirpath, target_is_directory=True)

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
        dst = rundirpath / pathlib.Path(f)
        if src.is_file():
            link_or_copy(src, dst, link)
        else:
            print(f"*******")
            print(f"WARNING...File not found ")
            print(f"and will NOT be linked or copied to run directory: {src}")
            print(f"*******")

# Create script to run init and ideal case
runscript = rundirpath / pathlib.Path("run.sh")
fwrite = open(runscript, "x")
fwrite.write(f"#!/bin/bash\n")
fwrite.write(f"set -x\n\n")
sub_job01 = f"sbatch --account={config['account']} run_init_atmosphere_model.sh\n"
fwrite.write(sub_job01)
# sub_job02 = f"sbatch -d afterok:${{runid}} --account={config['account']} run_atmosphere_model.sh\n"
# fwrite.write(sub_job02)
fwrite.close()

# Link latest run directory to this folder
linkrun = pathlib.Path.cwd() / pathlib.Path('latest_run_ics')
if linkrun.is_symlink(): linkrun.unlink(missing_ok=True)
linkrun.symlink_to(rundirpath, target_is_directory=True)

