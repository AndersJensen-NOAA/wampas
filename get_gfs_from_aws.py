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

# ------------------------------------------------------------------------------------- #

print(f"")
print(f"Running data puller with python version: {sys.version}")

# Read configuration file
config = read_config(pathlib.Path(CONFIG_FILE))
if config['verbose']: print(config)

start_date = datetime.datetime.strptime(config['data_init'], '%Y-%m-%d_%H:%M:%S')
end_date = start_date + datetime.timedelta(hours=config['data_stop_hours'])
delta_date = datetime.timedelta(hours=config['data_frequency_hours'])
date_string = start_date.strftime('%Y%m%d')

f = open(f"data_puller_{date_string}.txt", "w")

savedirs = []
# iterate over range of dates
while (start_date <= end_date):

    data_dir = pathlib.Path(config['rootdir']) / pathlib.Path(config['data_type']) / pathlib.Path(start_date.strftime('%Y%m%d'))
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {data_dir}")

    data_location = f"noaa-gfs-bdp-pds/gfs.{start_date.strftime('%Y%m%d')}/{start_date.strftime('%H')}/atmos/gfs.t{start_date.strftime('%H')}z.pgrb2.0p25.f000"
    print(f"... data location: {data_location}")

    data_destination = data_dir / pathlib.Path(f"gfs.t{start_date.strftime('%H')}z.pgrb2.0p25.f000")
    print(f"... data destination: {data_destination}")    

    f.write(f"{data_location} {data_destination}\n")

    savedirs.append(data_dir)
            
    start_date += delta_date
    
f.close()    



fgrib = open(f"link_grib_command_args_{date_string}.txt", "w")
dirs_for_grib = list(set(savedirs))
for f in dirs_for_grib:
    fgrib.write(f"{str(f)}/* ")
fgrib.close()

fglobus = open(f"globus_transfer_{date_string}.txt", "w")
fglobus.write(f"globus transfer $UUID_AWS_S3_PUBLIC:/ $UUID_JET_DTN:/ --batch data_puller.txt")
fglobus.close()
print("")
print(f"GLOBUS TRANSFER COMMAND: globus transfer $UUID_AWS_S3_PUBLIC:/ $UUID_JET_DTN:/ --batch data_puller.txt")

# noaa-gfs-bdp-pds/gfs.20230107/00/atmos/gfs.t00z.pgrb2.0p25.f000 mnt/lfs5/BMC/wrfruc/jensen/pear/ics/gfs.t00z.pgrb2.0p25.f000
# noaa-gfs-bdp-pds/gfs.20230107/06/atmos/gfs.t06z.pgrb2.0p25.f000 mnt/lfs5/BMC/wrfruc/jensen/pear/ics/gfs.t06z.pgrb2.0p25.f000
# Run command
# globus transfer $UUID_AWS_S3_PUBLIC:/ $UUID_JET_DTN:/ --batch data_puller.txt

