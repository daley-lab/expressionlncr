#!/usr/bin/env python3
#
#constants for ExpressionLncr scripts and GUI
#

#
# Default values for the CLI scripts
#

FIND_GEO_DATASERIES_DEFAULTS = {
  'ftp': 'ftp://ftp.ncbi.nlm.nih.gov/geo/series',
  'organism': 'homo_sapiens_funcgen_87_38',
  'dataDir': 'data',
  'seriesOutput': 'data/matrices/series.txt', 
  'infoOutput': 'data/matrices/summary.txt', 
  'searchTerms': '',
  'esearch': 'data/matrices/summary.txt.esearch', 
  'esummary': 'data/matrices/summary.txt.esummary',
  'getAllPlatforms': False,
  'getPlatformsFromOverlap': 'data/probes.overlap.bed',
  'skipSeriesInfo': False,
  'gdsOnly': True
}

FIND_OVERLAP_DEFAULTS = {
  'inputA': 'data/probes.bed',
  'inputB': 'data/lncrnas.bed',
  'outputA': 'data/probes.overlap.bed',
  'outputB': 'data/lncrnas.overlap.bed',
  'output': 'data/overlap.xml',
  'chunksize': 10000,
  'chromosome': None,
  'swap': False,
  'inputSorted': False,
  'pandasPipeline': False
}

BED_DEFAULTS = {
  'delim': '\t',
  'chromCol': 0,
  'startCol': 1,
  'stopCol': 2,
  'nameCol': 3,
  'strandCol': 5  #last column
}

GET_ENSEMBL_FUNCGEN_ORGANISMS_DEFAULTS = {
  'output': 'data/available_organisms.txt', 
  'url': 'ftp://ftp.ensembl.org/pub/current_mysql/',
  'pretty': False,
  'dataDir': 'data/arrays',
  'arrayFiles': False
}

GET_ENSEMBL_PROBES_DEFAULTS = {
  #max # lines to work with in files at once. tweak according to memory.
  'chunksize': 50000,
  'dataDir': 'data',
  'organism': 'homo_sapiens_funcgen_87_38',
  'output': 'data/probes.bed',
  'forceCurrentSchema': False,
  'fileTypes': ['array', 'array_chip', 'coord_system', 'probe', 'probe_set',
			'probe_feature', 'seq_region'],
  'noDownload': False,
  'pandasPipeline': False,
  'cleanUp': False
}

GET_GEO_DATASERIES_DEFAULTS = {
  'ftp': 'ftp://ftp.ncbi.nlm.nih.gov/geo/series',
  'input': 'data/matrices/series.txt',
  'output': 'data/matrices', 
  'series': '',
  'skippedSeriesFile': 'data/matrices/skipped_series.txt',
  'completedSeriesFile': 'data/matrices/completed_series.txt'
}

PARSE_GEO_DATASERIES_DEFAULTS = {
  'overlapFile': 'data/overlap.xml',
  'dataDir': 'data/matrices',
  'outDir': 'data/results',
  'lncrnaFile': 'data/lncrnas.bed',
  'organism': 'homo_sapiens_funcgen_87_38',
  'completedFilesFile': 'data/results/expressed_series/completed_files.txt'
}

GET_LNCRNA_DEFAULTS = {
  'mode': 'noncode',
  'organism': 'hg38',
  'output': 'data/lncrnas.bed',
  'highconf': True,
  'version': '3.1',
  'year': '2016'
}

#
# Some constants for the lncRNA GUI program
#

APP_MIN_WIDTH = 640
APP_MIN_HEIGHT = 480
APP_QUIT_MESSAGE = 'Quit the program?'
APP_TITLE = 'ExpressionLncr'

ERROR_DEFAULT = 'An error occurred.'
ERROR_INVALID_JOB = 'Invalid job. Please check your parameters and try again.'
ERROR_RUNNING_JOB = 'An error occurred running the job. Please check the terminal output for details.'

GREETER_TAB_LABEL = '&intro'
GREETER_TITLE = 'ExpressionLncr'
GREETER_BUTTON_MSG = 'Continue'
GREETER_TEXT = '<h3>Introduction</h3><p>ExpressionLncr is designed to help you investigate ' + \
    'functionality of lncRNAs by leveraging existing gene expression data.</p>' + \
    '<p>This GUI can be run via either a standalone executable or the source code. ' + \
    'Python3 (tested v3.11) and PySide6 are needed to run the ' + \
    'GUI source.</p><p>Nothing is required to run the standalone ' + \
    'GUI version, but you must download the appropriate build for your operating system.</p>' + \
    '<p>Alternatively, the source behind all the tools can be run as ' + \
    'command-line programs.</p>'  + \
    '<p>You can find more help and ExpressionLncr can be (re-)downloaded ' + \
    'at:</p>' + \
    '<p><a href="https://github.com/daley-lab/expressionlncr">github.com/daley-lab/expressionlncr</a></p>' + \
    '<p><a href="http://genapha.hli.ubc.ca/lncrna">genapha.hli.ubc.ca/lncrna</a></p>'
    #TODO uncomment when tools are in Galaxy toolshed
#    '<p>ExpressionLncr is also available as a Galaxy tool set at: ' + \
#    '<a href="https://toolshed.g2.bx.psu.edu/view/genapha/expressionlncr/MY_HASH">' + \
#    'https://toolshed.g2.bx.psu.edu/view/genapha/expressionlncr/MY_HASH</a></p>'

CHOOSER_DEFAULT_FILE = '(select a file)'
CHOOSER_BUTTON_MSG = 'Select...'
CHOOSER_SAVE_BUTTON_MSG = 'Save as...'
CHOOSER_TITLE = 'Open file...'
CHOOSER_SAVE_TITLE = 'Save as...'
CHOOSER_START_LOCATION = '.'
CHOOSER_FILE_TYPES = 'All Files (*.*)'

#NOTE probably should not hardcode NONCODE organisms. but there's not exactly a 
# standard URL for future updates after NONCODE2016.
LNCRNA_NONCODE_ORGANISMS = {
  'hg38' : 'Homo sapiens (hg38)', # 'Human (hg38)',
  'mm10' : 'Mus musculus (mm10)', # 'Mouse (mm10)',
  'bosTau6' : 'Bos taurus (bosTau6)', # 'Cow (bosTau6)',
  'rn6' : 'Rattus norvegicus (rn6)', # 'Rat (rn6)',
  'galGal4' : 'Gallus gallus (galGal4)', # 'Chicken (galGal4)',
  'ce10' : 'Caenorhabditis elegans (ce10)', # 'C. Elegans (ce10)',
  'dm6' : 'Drosophila melanogaster (dm6)', # 'D. Melanogaster (dm6)',
  'danRer10' : 'Danio rerio (danRer10)', # 'Zebrafish (danRer10)',
  'tair10' : 'A. Thaliana (tair10)',
  'sacCer3' : 'Saccharomyces cerevisiae (sacCer3)', # 'Yeast (sacCer3)',
  'panTro4' : 'Pan troglodytes (panTro4)', # 'Chimp (panTro4)',
  'gorGor3' : 'Gorilla (gorGor3)',
  'ponAbe2' : 'Orangutan (ponAbe2)',
  'rheMac3' : 'Macaca mulatta (rheMac3)', # 'Rhesus (rheMac3)',
  'monDom5' : 'Opossum (monDom5)',
  'ornAna1' : 'Ornithorhynchus anatinus(ornAna1)' # 'Platypus (ornAna1)'
}
LNCRNA_TAB_LABEL = '&lncRNA import'
LNCRNA_TITLE = '<h3>Get lncRNA information</h3>'
LNCRNA_SUBTITLE = '<p>This form lets you download information on lncRNAs ' + \
    'in the BED-6 (Browser Extensible Data) file format. Custom BED files ' + \
    'may be specified for subsequent operations here.</p>'
LNCRNA_SOURCE_MSG = 'lncRNA Source'
LNCRNA_SOURCE_FILE_MSG = ''  #intentionally empty. looks nicer
LNCRNA_ORGANISM_MSG = 'Organism'
LNCRNA_OUTPUT_MSG = 'Output file'
LNCRNA_FILE_BUTTON_MSG = 'Choose'
LNCRNA_RUN_BUTTON_MSG = 'Run'
LNCRNA_CHOOSE_OUTPUT = 'Choose output file - will be created / overwritten'
LNCRNA_START_LOCATION = '.'
LNCRNA_FILE_TYPES = 'BED Files (*.bed)'
LNCRNA_SOURCE_ITEMS = {
  'noncode': 'NONCODE.org',
  'lncipedia': 'LNCipedia.org',
  'custom': 'Custom BED file'
}

#not used if get_ensembl_funcgen_organisms.py works
PROBE_ENSEMBL_ORGANISMS = {
  'bos_taurus_funcgen_87_31': 'Bos taurus v87.31 (Cow)',
  'caenorhabditis_elegans_funcgen_87_250': 'Caenorhabditis elegans v87.250 (C. elegans)',
  'canis_familiaris_funcgen_87_31': 'Canis familiaris v87.31 (Dog)',
  'ciona_intestinalis_funcgen_87_3': 'Ciona intestinalis v87.3 (C. intestinalis)',
  'danio_rerio_funcgen_87_10': 'Danio rerio v87.10 (Zebrafish)',
  'drosophila_melanogaster_funcgen_87_602': 'Drosophila melanogaster v87.602 (D. melanogaster)',
  'gallus_gallus_funcgen_87_5': 'Gallus gallus v87.5 (Chicken)',
  'homo_sapiens_funcgen_87_38': 'Homo sapiens v87.38 (Human)',
  'macaca_mulatta_funcgen_87_801': 'Macaca mulatta v87.801 (Rhesus macaque)',
  'mus_musculus_funcgen_87_38': 'Mus musculus v87.38 (Mouse)',
  'ornithorhynchus_anatinus_funcgen_87_1': 'Ornithorhynchus anatinus v87.1 (Platypus)',
  'oryctolagus_cuniculus_funcgen_87_2': 'Oryctolagus cuniculus v87.2 (European rabbit)',
  'pan_troglodytes_funcgen_87_214': 'Pan troglodytes v87.214 (Chimp)',
  'rattus_norvegicus_funcgen_87_6': 'Rattus norvegicus v87.6 (Rat)',
  'saccharomyces_cerevisiae_funcgen_87_4': 'Saccharomyces cerevisiae v87.4 (Yeast)',
  'sus_scrofa_funcgen_87_102': 'Sus scrofa v87.102 (Wild boar)',
  'xenopus_tropicalis_funcgen_87_42': 'Xenopus tropicalis v87.42 (Western clawed frog)'
}
PROBE_TAB_LABEL = '&probe import'
PROBE_TITLE = '<h3>Get Ensembl expression probes</h3>'
PROBE_SUBTITLE = '<p>This form downloads information on Ensembl ' + \
    'probe expression in the BED-6 (Browser Extensible Data) file format. ' + \
    'Only probes in the Ensembl funcgen database for the organism will be ' + \
    'included in the output.</p>'
PROBE_ORGANISM_MSG = LNCRNA_ORGANISM_MSG
PROBE_DATADIR_MSG = 'Data cache directory'
PROBE_OUTPUT_MSG = LNCRNA_OUTPUT_MSG
PROBE_RUN_BUTTON_MSG = LNCRNA_RUN_BUTTON_MSG
PROBE_REFRESH_BUTTON_MSG = 'Refresh'

OVERLAP_TAB_LABEL = '&overlap'
OVERLAP_TITLE = '<h3>Get lncRNA/probe overlap</h3>'
OVERLAP_SUBTITLE = '<p>This form computes the overlap between the previous ' + \
    ' lncRNAs and Ensembl expression probe, and exports the results to an XML file ' + \
    ' for further steps.</p>'
OVERLAP_INPUT_A_MSG = 'Input A'
OVERLAP_INPUT_B_MSG = 'Input B'
OVERLAP_OUTPUT_A_MSG = 'Output A'
OVERLAP_OUTPUT_B_MSG = 'Output B'
OVERLAP_OUTPUT_XML_MSG = 'Combined Output'
OVERLAP_RUN_BUTTON_MSG = LNCRNA_RUN_BUTTON_MSG

EXPRESSION_TAB_LABEL = '&expression download'
EXPRESSION_TITLE = '<h3>Get GEO probe expression</h3>'
EXPRESSION_SUBTITLE = '<p>This form lets you search and download NCBI GEO probe expression ' + \
    'data for probes overlapping lncRNAs.</p>' + \
    '<p><i><b>Caution</b>: Due to limitations of GEO, large GEO Series ' + \
    'must be downloaded to obtain expression data for even a limited number ' + \
    'of expression probes. ' + \
    'For best results be as specific as possible with your search criteria.</i></p>'
EXPRESSION_INPUT_F_MSG = 'Input probe file'
EXPRESSION_OUTDIR_MSG = 'Output directory'
EXPRESSION_SEARCH_BUTTON_MSG = 'Search'
EXPRESSION_RUN_BUTTON_MSG = LNCRNA_RUN_BUTTON_MSG
EXPRESSION_ORGANISM_MSG = 'Organism'
EXPRESSION_SEARCH_TERMS_MSG = 'Search Terms'
EXPRESSION_SEARCH_BUTTON_ROW_MSG = ''
EXPRESSION_SEARCH_NO_RESULTS = 'No search results. Please run another search.'
EXPRESSION_DEFAULT_SERIES_OUTPUT = 'series.txt'
EXPRESSION_DEFAULT_INFO_OUTPUT = 'summary.txt'

RESULTS_TAB_LABEL = '&results'
RESULTS_TITLE = '<h3>Compute results</h3>'
RESULTS_SUBTITLE = '<p>This form iterates through the downloaded GEO Series, ' + \
    'parsing out expression data for the subset of probes overlapping the given lncRNAs.</p>'
RESULTS_DATADIR_MSG = 'Series matrices directory'
RESULTS_OVERLAP_FILE_MSG = 'lncRNA/probe overlap'
RESULTS_OUTPUT_DIR_MSG = 'Output directory'

BED_FILE_TYPE = 'BED files (*.bed)'
TXT_FILE_TYPE = 'Text files (*.txt)'
TSV_FILE_TYPE = 'Tab-delimited files (*.tsv)'
CSV_FILE_TYPE = 'Comma-delimited files (*.csv)'
XML_FILE_TYPE = 'XML files (*.xml)'
COLUMN_FILE_TYPE = '%s;;%s;;%s' % (TXT_FILE_TYPE, TSV_FILE_TYPE, CSV_FILE_TYPE)

OPEN_DIALOG_TYPE = 'open'
SAVE_DIALOG_TYPE = 'save'
DIRECTORY_OPEN_DIALOG_TYPE = 'open_directory'
DIRECTORY_SAVE_DIALOG_TYPE = 'save_directory'

NAV_NEXT_BUTTON_MSG = 'Next'
NAV_PREV_BUTTON_MSG = 'Prev'
