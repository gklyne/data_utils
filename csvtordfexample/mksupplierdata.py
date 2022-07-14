# !/usr/bin/env python3

"""
mksupplierdata.py - create Annalist supplier data from CSV/TSV file.
"""

__author__      = "Graham Klyne (GK@ACM.ORG)"
__copyright__   = "Copyright 2022, Graham Klyne"
__license__     = "MIT (http://opensource.org/licenses/MIT)"

import sys
import os
import os.path
import re
import argparse
import logging
import traceback
import csv

log = logging.getLogger(__name__)

from grid.grid import GridCSV, GridTSV, GridExcel

VERSION = "0.1"

def program_name(args):
    return os.path.basename(args[0])

def getsupplierdata(grid, baseuri):
    """
    Get supplier data from grid, return dictionary of supplier records indexed by supplier id
    """
    def map_bool(v):
        v = v.lower()
        return (
            True  if v in ["yes", "y", "true",  "t"] else
            False if v in ["no",  "n", "false", "f"] else
            None
            )
    NAME_ID_TABLE = str.maketrans(" /.", "___", ":,'+&")
    def translate_name_id(n):
        return n.translate(NAME_ID_TABLE)

    supplierdata = {}
    row = 0
    for h in grid:
        row += 1
        if row <= 5:
            continue
        try:
            product_type         = h[0].strip()
            supplier_name        = h[1].strip()
            location             = h[2].strip()
            supplier_status      = h[3].strip()
            animal_use           = h[4].strip()
            packaging_recyclable = h[5].strip()
            retail_availability  = h[6].strip()
            multinational_org    = h[7].strip()
            supplier_web_page    = h[8].strip()
            comments             = h[9].strip()
            if animal_use in ["Unsure", ""]:
                animal_use = "Unknown"
            recycling_status = (
                "Food_packaging_recyclable"      if packaging_recyclable == "Yes"    else
                "Food_packaging_part_recyclable" if packaging_recyclable == "Mostly" else
                "Unknown"                        if packaging_recyclable == "Unsure" else
                "" )
            if supplier_name and supplier_name[0] != "[":
                supplier_id = translate_name_id(supplier_name)
                print(f"supplier_id: {supplier_id:32s}")
                supplierdata[supplier_id] = (
                    { '@id': f"Potential_suppliers/{supplier_id}"
                    , "@type": 
                        [ "fp:Potential_suppliers"
                        , "annal:EntityData" 
                        ]
                    , "annal:id":                      supplier_id
                    , "annal:type":                    "fp:Potential_suppliers"
                    , "annal:type_id":                 "Potential_suppliers"
                    , "annal:uri":                     f"fp:{supplier_id}"
                    , "fp:company_status":             f"Company_status/{supplier_status}"
                    , "fp:company_website":            supplier_web_page
                    , "fp:location_ref":               f"Location/{location}"
                    , "fp:multinational_organization": map_bool(multinational_org)
                    , "fp:product_animal_use":         f"Animal_use/{animal_use}"
                    , "fp:product_type_ref":           f"Product_type/{translate_name_id(product_type)}"
                    , "fp:recycling_status":           f"Recycling_status/{recycling_status}"
                    , "fp:retail_availability":        map_bool(retail_availability)
                    , "rdfs:comment":                  comments
                    , "rdfs:label":                    supplier_name
                    })
        except IndexError as e:
            continue
    return (0, supplierdata)

def mksupplierjson(supplierdata, outfilebase):
    try:
        os.mkdir(outfilebase)
    except FileExistsError as e:
        pass
    for sid,sdata in supplierdata.items():
        supplier_dirpath  = outfilebase + "/" + sdata["annal:id"] + "/"
        supplier_filepath = supplier_dirpath + "entity_data.jsonld"
        try:
            os.mkdir(supplier_dirpath)
        except FileExistsError as e:
            pass
        print(f"Create file {supplier_filepath}")
        with open(supplier_filepath, "wt", encoding="utf-8") as f:
            f.write(
                '''{\n''' +
                '''  "@context": [\n''' +
                '''    {\n''' +
                '''      "@base": "../../"\n''' +
                '''    },\n''' +
                '''    "../../coll_context.jsonld"\n''' +
                '''  ]'''
            )
            for k, v in sdata.items():
                ks = f'''"{k}":'''
                f.write(",\n")
                f.write(f'''{ks:<34s}''')
                if isinstance(v, list):
                    f.write(f'''[ "{v[0]}"''')
                    for itm in v[1:]:
                        f.write(f''', "{itm}"''')
                    f.write(" ]")
                elif isinstance(v, bool):
                    f.write("true" if v else "false")
                else:
                    f.write(f'''"{v}"''')
            f.write("\n}\n")
    return 0

def run(configbase, filebase, options, progname):
    """
    Access input file as grid, and generate Annalist JSON data
    """
    status = 0
    # open spreadsheet file as grid
    log.debug("%s: open grid %s"%(progname, options.suppliers))
    gridfilename = os.path.join(filebase,options.suppliers)
    log.debug("CSV file: %s"%gridfilename)
    base = ""
    outfilebase = gridfilename
    if gridfilename.endswith(".csv"):
        try:
            with open(gridfilename, "rt", encoding="utf-8") as csvfile:
                grid = GridCSV(csvfile, baseuri="", dialect=csv.excel)
                outfilebase = gridfilename[0:-4]
        except IOError as e:
            print("Failed to open grid CSV file %s"%(e))
            return 2
    elif gridfilename.endswith(".tsv"):
        try:
            with open(gridfilename, "rt", encoding="utf-8") as tsvfile:
                grid = GridTSV(tsvfile, baseuri="", dialect=csv.excel_tab)
                outfilebase = gridfilename[0:-4]
        except IOError as e:
            print("Failed to open grid TSV file %s"%(e))
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
    # Make Annalist data files
    log.debug("mksupplierdata %s"%(repr(options)))
    (status, supplierdata) = getsupplierdata(grid,  baseuri=grid.resolveUri(""))
    # Serialize results to output files
    if status == 0:
        try:
            status = mksupplierjson(supplierdata, outfilebase)
        except Exception as e:
            print("Failed to create supplier data %s"%(e))
            traceback.print_exc()
            status = 2
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
                description="Generate Annalist data from tabular supplier descriptions.",
                epilog="The generated files are written to '<basename>/<supplierid>/entity_data.jsonld'.")
    parser.add_argument("suppliers", help="File containing supplier in tabular format")
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
