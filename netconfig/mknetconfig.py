# !/usr/bin/env python3

"""
mknetconfig.py - create network DNS/DHCP configuration files from tabular host description
"""

__author__      = "Graham Klyne (GK@ACM.ORG)"
__copyright__   = "Copyright 2021, Graham Klyne"
__license__     = "MIT (http://opensource.org/licenses/MIT)"

import sys
import os
import os.path
import re
import argparse
import logging
import csv

log = logging.getLogger(__name__)

# Make sure MiscUtils can be found on path
if __name__ == "__main__":
    sys.path.append(os.path.join(sys.path[0],".."))

from grid.grid import GridCSV, GridTSV, GridExcel

VERSION = "0.1"

def program_name(args):
    return os.path.basename(args[0])

def gethostdata(grid, baseuri):
    """
    Get host data from grid, return dictionary of host records indexed by IP address
    """
    hostdata = {}
    for h in grid:
        try:
            name    = h[1].strip()
            ipaddr  = h[2].strip()
            macaddr = h[3].strip()
            descr   = h[4].strip()
            if name:
                print(f"host: {name:16}, IP {ipaddr:16}, MAC {macaddr:18} # {descr}")
                hostdata[name] = {'name':name, 'ipaddr':ipaddr, 'macaddr':macaddr, 'descr':descr}
        except IndexError as e:
            continue
    return (0, hostdata)

def mkdhcpdconf(hostdata, filebase):
    """
    Output DHCP host configuration data to <filebase>.dhcpd.conf
    """
    dhcpdconf_filepath = filebase+".dhcpd.conf"
    _, dhcpdconf_filename = os.path.split(dhcpdconf_filepath)
    with open(dhcpdconf_filepath, "wt") as f:
        f.write(f"""# {dhcpdconf_filename}
#
# Copy this file to /etc/dhcp on the server system, and 
# include in /etc/dhcp/dhcpd.conf with this line:
#   include "/etc/dhcp/{dhcpdconf_filename}" ;
#
""")
        for (ipaddr,h) in hostdata.items():
            if h['macaddr']:
                dhcpd_entry = f"""host {h['name']}
    {{   # {h['descr']}
        hardware ethernet {h['macaddr']} ;
        fixed-address     {h['name']}.atuin.ninebynine.org ;
    }}
"""
                f.write(dhcpd_entry)
            # f.write(f"host: {h['name']:16}, IP {h['ipaddr']:16}, MAC {h['macaddr']:18} # {h['descr']}\n")
    return 0

def mkzonehosts(hostdata, filebase):
    """
    Output DHCP host configuration data to <filebase>.zone.hosts
    """
    zonehosts_filepath = filebase+".zone.hosts"
    _, zonehosts_filename = os.path.split(zonehosts_filepath)
    with open(zonehosts_filepath, "wt") as f:
        f.write(f"""; {zonehosts_filename}
;
; Copy this file to /etc/bind/atuin on the server system, and 
; include in /etc/bind/atuin/atuin.ninebynine.org.zone with this line:
;   $INCLUDE {zonehosts_filename}
;
""")
        for (ipaddr,h) in hostdata.items():
            dns_entry = f"{h['name']:16} IN A {h['ipaddr']:16}   ; {h['descr']}\n"
            f.write(dns_entry)
            # f.write(f"host: {h['name']:16}, IP {h['ipaddr']:16}, MAC {h['macaddr']:18} # {h['descr']}\n")
    return 0

def run(configbase, filebase, options, progname):
    """
    Access input file as grid, and generate config data
    """
    status = 0
    # open spreadsheet file as grid
    log.debug("%s: open grid %s"%(progname, options.hosts))
    gridfilename = os.path.join(filebase,options.hosts)
    log.debug("CSV file: %s"%gridfilename)
    base = ""
    outfilebase = gridfilename
    if gridfilename.endswith(".csv"):
        try:
            with open(gridfilename, "rt") as csvfile:
                grid = GridCSV(csvfile, baseuri="", dialect=csv.excel)
                outfilebase = gridfilename[0:-4]
        except IOError as e:
            print("Failed to open grid CSV file %s"%(e))
            return 2
    elif gridfilename.endswith(".tsv"):
        try:
            with open(gridfilename, "rt") as tsvfile:
                grid = GridTSV(tsvfile, baseuri="", dialect=csv.excel_tab)
                outfilebase = gridfilename[0:-4]
        except IOError as e:
            print("Failed to open grid CSV file %s"%(e))
            return 2
    elif gridfilename.endswith(".xls"):
        try:
            grid = GridExcel(gridfilename, baseuri="")
            outfilebase = gridfilename[0:-4]
        except IOError as e:
            print("Failed to open grid XLS file %s"%(e))
            return 2
    else:
        print("Unrecognized grid file type %s; must be CSV, TSV or XLS."%(gridfilename))
        return 2
    # Make minim file
    log.debug("mknetconfig %s"%(repr(options)))
    (status, hostdata) = gethostdata(grid,  baseuri=grid.resolveUri(""))
    # Serialize results to output files
    if status == 0:
        status = mkdhcpdconf(hostdata, outfilebase)
    if status == 0:
        status = mkzonehosts(hostdata, outfilebase)
    # Exit
    return status

def parseCommandArgs(argv):
    """
    Parse command line arguments

    prog -- program name from command line
    argv -- argument list from command line

    Returns a pair consisting of options specified as returned by
    OptionParser, and any remaining unparsed arguments.
    """
    # create a parser for the command line options
    parser = argparse.ArgumentParser(
                description="Generate network DNS/DHCP configuration data from tabular hosts description.",
                epilog="The generated files are written to <filename>.dhcpd.conf and <filename>.zone.hosts.")
    # parser.add_argument("-a", "--all",
    #                     action="store_true",
    #                     dest="all",
    #                     default=False,
    #                     help="All, list all files, depends on the context")
    parser.add_argument("hosts", help="File containing hosts description in tabular format")
    parser.add_argument('--version', action='version', version='%(prog)s '+VERSION)
    parser.add_argument("--debug",
                        action="store_true", 
                        dest="debug", 
                        default=False,
                        help="Run with full debug output enabled")
    # parse command line now
    options = parser.parse_args(argv)
    log.debug("Options: %s"%(repr(options)))
    return options

def runCommand(configbase, filebase, argv):
    """
    Run program with supplied configuration base directory, Base directory
    from which to start looking for research objects, and arguments.

    This is called by main function (below), and also by test suite routines.

    Returns exit status.
    """
    options = parseCommandArgs(argv[1:])
    if not options or options.debug:
        logging.basicConfig(level=logging.DEBUG)
    log.debug("runCommand: configbase %s, filebase %s, argv %s"%(configbase, filebase, repr(argv)))
    # else:
    #     logging.basicConfig()
    status = 1
    if options:
        progname = program_name(argv)
        status   = run(configbase, filebase, options, progname)
    return status

def runMain():
    """
    Main program transfer function for setup.py console script
    """
    userhome = os.path.expanduser("~")
    filebase = os.getcwd()
    return runCommand(userhome, filebase, sys.argv)

if __name__ == "__main__":
    """
    Program invoked from the command line.
    """
    status = runMain()
    sys.exit(status)
