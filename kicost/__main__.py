# -*- coding: utf-8 -*- 

# MIT license
#
# Copyright (C) 2018 by XESS Corporation / Hildo Guillardi Júnior
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import print_function

#Libraries.
import argparse as ap # Command argument parser.
import os, sys, platform
import logging, time
#import inspect # To get the internal module and informations of a module/class.

from .global_vars import * # Debug, language and default configurations.

# KiCost definitions and modules/packages functions.
from .kicost import * # kicost core functions.
try:
    from .kicost_gui import * # User guide.
except wxPythonNotPresent as e:
    pass # If the wxPython dependences are not installed and
         # the user just want the KiCost CLI.
from .distributors.global_vars import distributor_dict
from .edas import eda_dict
from . import __version__ # Version control by @xesscorp and collaborator.

###############################################################################
# Additional functions
###############################################################################

def kicost_version_info():
    version_info_str = r'KiCost v.{}.'.format(__version__)
    version_info_str += r'at Python {}.{}.{}.'.format(
                                                      sys.version_info.major,
                                                      sys.version_info.minor,
                                                      sys.version_info.micro)
    version_info_str += r'on {}({}).'.format(
                                              platform.platform(),
                                              platform.architecture()[0])
    try:
        import wx
        version_info_str += 'Graphical library: {}.'.format(wx.version())
    except:
        version_info_str += 'No graphical library installed for the GUI.'
    #version_info_str += r'\n'
    return version_info_str

###############################################################################
# Command-line interface.
###############################################################################

def main():

    parser = ap.ArgumentParser(
        description='Build cost spreadsheet for a KiCAD project.')
    parser.add_argument('-v', '--version',
                        action='version',
                        version='KiCost v.{}'.format(__version__) )
    parser.add_argument('--info',
                        action='version',
                        version=kicost_version_info(),
                        help='Show program\' and library information and version.' )
    parser.add_argument('-i', '--input',
                        nargs='+',
                        type=str,
                        metavar='FILE.XML',
                        help='One or more schematic BOM XML files.')
    parser.add_argument('-o', '--output',
                        nargs='?',
                        type=str,
                        metavar='FILE.XLSX',
                        help='Generated cost spreadsheet.')
    parser.add_argument('-j', '--json',
                        action='store_true',
                        help='Enable json export along with the xlsx output file.')
    parser.add_argument('-f', '--fields',
                        nargs='+',
                        type=str,
                        default=[],
                        metavar='NAME',
                        help='''Specify the names of additional part fields to 
                            extract and insert in the global data section of 
                            the spreadsheet.''')
    parser.add_argument('--translate_fields',
                        nargs='+',
                        type=str,
                        metavar='NAME',
                        help='''Specify or remove field translation
                            (--translate X1 Y1 X2 Y2 X3 ~,
                            translates X1 to Y1 and X2 to Y2 and remove
                            X3 for the internal dictionary).''')
    parser.add_argument('--variant',
                        nargs='+',
                        type=str,
                        default=[' '], # Default variant is a space.
                        help='schematic variant name filter using regular expression.')
    parser.add_argument('-w', '--overwrite',
                        action='store_true',
                        help='Allow overwriting of an existing spreadsheet.')
    parser.add_argument('-q', '--quiet',
                        action='store_true',
                        help='Enable quiet mode with no warnings.')
    parser.add_argument('--ignore_fields',
                        nargs='+',
                        default=[],
                        help='Declare part fields to ignore when reading the BoM file.',
                        metavar='NAME',
                        type=str)
    parser.add_argument('--group_fields',
                        nargs='+',
                        default=[],
                        help='Declare part fields to merge when grouping parts.',
                        metavar='NAME',
                        type=str)
    parser.add_argument('--debug',
                        nargs='?',
                        type=int,
                        default=None,
                        metavar='LEVEL',
                        help='Print debugging info. (Larger LEVEL means more info.)')
    parser.add_argument('--eda', choices=['kicad', 'altium', 'csv'],
                        nargs='+',
                        default=['kicad'],
                        help='Choose EDA tool from which the XML BOM file originated, or use csv for .CSV files.')
    parser.add_argument('--show_dist_list',
                        action='store_true',
                        help='Show list of distributors that can be scraped for cost data, then exit.')
    parser.add_argument('--show_eda_list',
                        action='store_true',
                        help='Show list of EDA tools whose files KiCost can read, then exit.')
    parser.add_argument('--no_collapse',
                        action='store_true',
                        help='Do not collapse the part references in the spreadsheet.')
    parser.add_argument('--show_cat_url',
                        action='store_true',
                        help='Do not suppress the catalogue links into the catalogue code in the spreadsheet.')
    parser.add_argument('-e', '--exclude',
                        nargs='+', type=str, default='',
                        metavar = 'DIST',
                        help='Excludes the given distributor(s) from the scraping process.')
    parser.add_argument('--include',
                        nargs='+', type=str, default='',
                        metavar = 'DIST',
                        help='Includes only the given distributor(s) in the scraping process.')
    parser.add_argument('--no_price',
                        action='store_true',
                        help='Create a spreadsheet without scraping part data from distributor websites.')
    parser.add_argument('--currency',
                        nargs='?',
                        type=str,
                        default='USD',
                        help='Define the priority currency. Use the ISO4217 for currency (`USD`, `EUR`). Default: `USD`.')
    parser.add_argument('--gui',
                        nargs='+',
                        type=str,
                        metavar='FILE.XML',
                        help='Start the GUI to run KiCost passing the file parameter give by "--input", all others parameters are ignored.')
    parser.add_argument('--user',
                        action='store_true',
                        help='Run KiCost on terminal using the parameters in the GUI memory, all passed parameters from terminal take priority.')
    parser.add_argument('--setup',
                        action='store_true',
                        help='Run KiCost integration (with KiCad and OS) configuration script.')
    parser.add_argument('--unsetup',
                        action='store_true',
                        help='Undo the KiCost integration.')

    args = parser.parse_args()

    # Setup and unsetup KiCost integration.
    if args.setup:
        from .kicost_config import kicost_setup
        kicost_setup()
        return
    if args.unsetup:
        from .kicost_config import kicost_unsetup
        kicost_unsetup()
        return

    # Set up logging.
    if args.debug is not None:
        log_level = logging.DEBUG + 1 - args.debug
    elif args.quiet is True:
        log_level = logging.ERROR
    else:
        log_level = logging.WARNING
    logging.basicConfig(level=log_level, format='%(message)s')

    if args.show_dist_list:
        print('Distributor list:', *sorted(list(distributor_dict.keys())))
        return
    if args.show_eda_list:
        #eda_names = [o[0] for o in inspect.getmembers(eda_tools_imports) if inspect.ismodule(o[1])]
        #print('EDA supported list:', ', '.join(eda_names))
        print('EDA supported list:', *sorted(list(eda_dict.keys())))
        return

    # Set up spreadsheet output file.
    if args.output == None:
        # If no output file is given...
        if args.input != None:
            # Send output to spreadsheet with name of input file.
            # Compose a name with the multiple BOM input file names.
            args.output = output_filename(args.input)
        else:
            # Send output to spreadsheet with name of this application.
            args.output = os.path.splitext(sys.argv[0])[0] + '.xlsx'
    else:
        # Output file was given. Make sure it has spreadsheet extension.
        args.output = os.path.splitext(args.output)[0] + '.xlsx'

    # Call the KiCost interface to alredy run KiCost, this is just to use the
    # saved user configurations of the graphical interface.
    if args.user:
        try:
            kicost_gui_runterminal(args)
        except (ImportError,NameError):
            kicost_gui_notdependences()
        return

    # Handle case where output is going into an existing spreadsheet file.
    if os.path.isfile(args.output):
        if not args.overwrite:
            logger.critical('''Output file {} already exists! Use the
                --overwrite option to replace it.'''.format(args.output))
            sys.exit(1)

    if args.gui:
        try:
            kicost_gui([os.path.abspath(fileName) for fileName in args.gui])
        except (ImportError, NameError):
            kicost_gui_notdependences()
        return

    if args.input == None:
        try:
            kicost_gui() # Use the user gui if no input is given.
        except (ImportError, NameError):
            kicost_gui_notdependences()
        return
    else:
        # Match the EDA tool formats with the input files.
        if len(args.eda) == 1:
            # Expand a single EDA format to cover all input files.
            args.eda = args.eda[0:1] * len(args.input)
        if len(args.input) != len(args.eda):
            print('The number of input files must match the number of EDA tool formats.')
            return

        # Match the variants with the input files.
        if len(args.variant) == 1:
            args.variant = args.variant[0:1] * len(args.input)
        if len(args.input) != len(args.variant):
            print('The number of input files must match the number of variants.')
            return

        # Otherwise get XML from the given file.
        for i in range(len(args.input)):
            # Set '.xml' as the default file extension, treating this exception
            # allow other files extension and formats.
            try:
                if os.path.splitext(args.input[i])[1] == '':
                    args.input[i] += '.xml'
                elif os.path.splitext(args.input[i])[1] == '.csv':
                    args.eda[i] = 'csv'
            except IndexError:
                pass

    # Remove all the distributor from the list for not scrape any web site.
    if args.no_price:
        dist_list = None
    else:
        if not args.include:
            dist_list = list(distributor_dict.keys())
        else:
            dist_list = args.include
        for d in args.exclude:
            dist_list.remove(d)

    logger.log(DEBUG_OBSESSIVE, 'Started KiCost v.{} on {}({}) Python {}.{}.{}'.format(
                                              __version__,
                                              platform.platform(),
                                              platform.architecture()[0],
                                              sys.version_info.major,
                                              sys.version_info.minor,
                                              sys.version_info.micro)
                                          )

    #try:
    kicost(in_file=args.input, eda_name=args.eda,
        out_filename=args.output, collapse_refs=not args.no_collapse, suppress_cat_url=not args.show_cat_url,
        user_fields=args.fields, ignore_fields=args.ignore_fields,
        group_fields=args.group_fields, translate_fields=args.translate_fields,
        variant=args.variant,
        dist_list=dist_list, currency=args.currency, export_json=args.json)
    #except Exception as e:
    #    sys.exit(e)

###############################################################################
# Main entrypoint.
###############################################################################
if __name__ == '__main__':
    start_time = time.time()
    main()
    logger.log(logging.DEBUG-2, 'Elapsed time: %f seconds', time.time() - start_time)
