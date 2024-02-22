#custom manually curated mapping of Ensembl funcgen database organism name to 
# funcgen array names to GEO GPL platform accession number, due to limitations
# in GEO services.
#
#below is a list of the organism version numbers this map was curated with,
# which have been stripped from the map.
#note that this should not matter except for cases where new expression arrays have been 
# added to the array.txt.gz file (corresponding to the funcgen schema array table).
#
# bos_taurus_funcgen_85_31
# caenorhabditis_elegans_funcgen_85_250
# canis_familiaris_funcgen_85_31
# ciona_intestinalis_funcgen_85_3
# danio_rerio_funcgen_85_10
# drosophila_melanogaster_funcgen_85_602
# gallus_gallus_funcgen_85_4
# homo_sapiens_funcgen_85_38
# macaca_mulatta_funcgen_85_10
# mus_musculus_funcgen_85_38
# ornithorhynchus_anatinus_funcgen_85_1
# oryctolagus_cuniculus_funcgen_85_2
# pan_troglodytes_funcgen_85_214
# rattus_norvegicus_funcgen_85_6
# saccharomyces_cerevisiae_funcgen_85_4
# sus_scrofa_funcgen_85_102
# xenopus_tropicalis_funcgen_85_42
#


ORG_TO_ARRAY_TO_GPL = {
  'bos_taurus': {
    'GPL2112': 'Bovine'
  },

  'caenorhabditis_elegans': {
    'C_elegans': 'GPL200',
    'GPL9450':  'GPL9450',
    'WUSTL-C_elegans':  '',
    'GPL14144': 'GPL14144',
    'GPL3518':  'GPL3518',
    '15061':  'GPL7727,GPL9209',
    '12795':  '',
    '20186':  '',
    'GPL13394': 'GPL13394',
    'GPL13914': 'GPL13914',
    'GPL8304':  'GPL8304',
    'GPL19516': 'GPL19516',
    'GPL8673':  'GPL8673'
  },

  'canis_familiaris': {
    'Canine_2': 'GPL3738'
  },

  'ciona_intestinalis': {
    'CINT06a520380F': ''
  },

  #*agilent arrays gpls are for probe name / feature #
  'danio_rerio': {
    'Zebrafish': 'GPL1319',
    'G2518A': 'GPL7244,GPL2878',
    'G2519F': 'GPL7302,GPL6563',
    'LEIDEN2': '',
    'LEIDEN': '',
    'MattArray': '',
  },

  'drosophila_melanogaster': {
    'DrosGenome1': 'GPL72',
    'Drosophila_2': 'GPL1322'
  },

  'gallus_gallus': {
    'Chicken': 'GPL3213'
  },

  #*note huex-1_0-st gene / exon version (that order)
  #*note agilent sureprint probe name version / feature number version (that order)
  #*note hugene gene / exon version (that order)
  #*note HTA-2_0 gene / exon version (that order)
  'homo_sapiens': {
    'HumanWG_6_V2': 'GPL6102',
    'HumanWG_6_V3': 'GPL6884',
    'HuEx-1_0-st-v2': 'GPL5188,GPL5175',
    'HC-G110': 'GPL74',
    'HG-Focus': 'GPL201',
    'HG-U133A_2': 'GPL571',
    'HG-U133A': 'GPL96',
    'HG-U133B': 'GPL97',
    'HG-U133_Plus_2': 'GPL570',
    'HG-U95Av2': 'GPL8300',
    'HG-U95B': 'GPL92',
    'HG-U95C': 'GPL93',
    'HG-U95D': 'GPL94',
    'HG-U95E': 'GPL95',
    'HG-U95A': 'GPL91',
    'HuGeneFL': 'GPL80',
    'U133_X3P': 'GPL1352',
    'HuGene-1_0-st-v1': 'GPL6244',
    'CODELINK': 'GPL2895',
    'OneArray': 'GPL6254',
    'CGH_44b': 'GPL2879',
    'HumanWG_6_V1': 'GPL6097',
    'HumanMethylation450': '',  #don't want methylation data leave empty
    'HumanMethylation27': '', #don't want methylation data leave empty
    'SurePrint_G3_GE_8x60k': 'GPL14550',
    'WholeGenome_4x44k_v1': 'GPL6480,GPL4133',
    'WholeGenome_4x44k_v2': 'GPL13497,GPL10332',
    'PrimeView': 'GPL15207',
    'SurePrint_G3_GE_8x60k_v2': 'GPL17077,GPL16699',
    'HuGene-2_0-st-v1': 'GPL16686,GPL19251',
    'HumanHT-12_V3': '',
    'HumanHT-12_V4': '',
    'HumanRef-8_V3': 'GPL6883',
    'HTA-2_0':  'GPL17586,GPL17585',
  },

  'macaca_mulatta': {
    'Rhesus': 'GPL3535'
  },

  #*mousewg_6_v1 is GPL for v1.1
  #*moex-1_0-st gpls are gene / exon version, resp.
  #*mogene-2_1-st-v1 gpls are for gene / exon vs, resp
  #*sureprint_G3_GE_8x60k gpls are for probe name / feature # vs, resp
  #*wholegenome_4x44k_v1 and v2 gpls are probe name / feature # vs, resp
  'mus_musculus': {
    'MoGene-1_0-st-v1': 'GPL6246',
    'MG-U74A': 'GPL32',
    'MG-U74Av2': 'GPL81',
    'MoEx-1_0-st-v1': 'GPL6096,GPL6193',
    'MG-U74B': 'GPL33',
    'MG-U74Bv2': 'GPL82',
    'MG-U74C': 'GPL34',
    'MG-U74Cv2': 'GPL83',
    'MOE430A': 'GPL339',
    'MOE430B': 'GPL340',
    'Mouse430A_2': 'GPL8321',
    'Mouse430_2': 'GPL1261',
    'Mu11ksubA': 'GPL75',
    'Mu11ksubB': 'GPL76',
    'CODELINK': 'GPL2897',
    'OneArray': 'GPL6845',
    'SurePrint_G3_GE_8x60k': 'GPL10787,GPL13912',
    'WholeGenome_4x44k_v1': 'GPL7202,GPL4134',
    'WholeGenome_4x44k_v2': 'GPL11202,GPL10333',
    'MouseRef-8_V2': 'GPL6885',
    'MoGene-2_1-st-v1': 'GPL17400,GPL20041'
  },

  'ornithorhynchus_anatinus': {
    'platypus_exon': ''
  },

  'oryctolagus_cuniculus': {
    'SurePrint_GPL16709_4x44k': 'GPL16709',
    'SurePrint_GPL7083_4x44k': 'GPL7083'
  },

  #*assuming chimp just uses regular human arrays 
  #*huex-1_0-st-v2 gpls are exon / gene version, resp 
  'pan_troglodytes': {
    'HuEx-1_0-st-v2': 'GPL5188,GPL5175',
    'HC-G110': 'GPL74',
    'HG-Focus': 'GPL201',
    'HG-U133A_2': 'GPL571',
    'HG-U133A': 'GPL96',
    'HG-U133B': 'GPL97',
    'HG-U133_Plus_2': 'GPL570',
    'HG_U95Av2': 'GPL8300',
    'HG-U95B': 'GPL92',
    'HG-U95C': 'GPL93',
    'HG-U95D': 'GPL94',
    'HG-U95E': 'GPL95',
    'HG_U95A': 'GPL91',
    'HuGeneFL': 'GPL80',
    'U133_X3P': 'GPL1352',
    'HuGene-1_0-st-v1': 'GPL6244'
  },
  
  #*raex-1_0-st-v1 gpls are exon/gene vs, resp
  #*ragene-1_0-st-v1 gpls are gene/exon vs, resp
  #*CODELINK version for all organisms chosen "GE Healthcare/Amersham Biosciences CodeLink ... Whole Genome Bioarray"
  #*Phalanx OneArray v1 chosen for all organisms
  #*SurePrint_G3_GE_8x60k gpls are for probe name / feature # vs, resp
  #*agilent wholegenome_4x44k_v1 gpls are for feature # / probe name vs, resp
  #*agilent wholegenome_4x44k_v3 gpls are for probe name / feature #, resp
  #*Affymetrix RaGene-2_1-st-v1 gpl is for transcript (gene) version
  'rattus_norvegicus': {
    'RAE230A': 'GPL341',
    'RAE230B': 'GPL342',
    'RG-U34A': 'GPL85',
    'RG-U34B': 'GPL86',
    'RG-U34C': 'GPL87',
    'RN-U34': 'GPL88',
    'RT-U34': '',
    'Rat230_2': 'GPL1355',
    'RaEx-1_0-st-v1': 'GPL6194,GPL6543',
    'RaGene-1_0-st-v1': 'GPL6247,GPL10741',
    'CODELINK': 'GPL2896',
    'RatRef-12_V1': 'GPL6101',
    'OneArray': 'GPL13694',
    'SurePrint_G3_GE_8x60k': 'GPL15084,GPL14797',
    'WholeGenome_4x44k_v1': 'GPL4135,GPL7294',
    'WholeGenome_4x44k_v3': 'GPL14746,GPL14745',
    'RaGene-2_1-st-v1': 'GPL19271'
  },

  'saccharomyces_cerevisiae': {
    'Yeast_2': 'GPL2529',
    'YG-S98': 'GPL90'
  },

  #*only old Affymetrix Porcine expression array in GEO. Called "Affymetrix Porcine Genome Array".
  'sus_scrofa': {
    'Porcine': 'GPL3533'
  },

  'xenopus_tropicalis': {
    'X_tropicalis': 'GPL10263'
  }
}

# List of organism names like: Sus scrofa, Xenopus tropicalis, etc...
ORG_NAMES = [o[0].upper() + o[1:].replace('_', ' ') for o in ORG_TO_ARRAY_TO_GPL.keys()]
