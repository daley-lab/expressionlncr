# ExpressionLncr

ExpressionLncr was a 2017 tool written in Python2 to help finding GEO expression data related to long non-coding RNAs.

This re-release rewrites ExpressionLncr for Python3, improves performance, fixes up some bugs, and accounts for changes to the underlying data sources.

## Requirements

ExpressionLncr needs `bedtools` and `sort` available on your `$PATH`.

```bash
apt install coreutils bedtools
```

Alternatively, install a newer version of bedtools. For example:

```bash
wget https://github.com/arq5x/bedtools2/releases/download/v2.31.0/bedtools.static
mv bedtools.static bedtools
chmod +x bedtools
sudo mv bedtools /usr/local/bin
```

### Python 3 package requirements

Developed and tested under python-3.11.

If using the python scripts directly (instead of the built GUI executable), there's some extra steps...

An extra system library is required for Qt 6, xcb-cursor0.

```bash
sudo apt install libxcb-cursor0
```

Python-3 requirements are in `requirements.txt`:

```
PySide6

Optional:
numpy
pandas
```

(Optional)

Using a virtual environment is optional but recommended. If you install requirements into virtual environment, make sure to use it when running things.

```bash
python -m venv .venv
source .venv/bin/activate
```

To install the project's requirements:

```bash
python -m pip install -r requirements.txt
```

## Run

### GUI via Python:

Run gui.py with python.

### Pre-built Linux build:

The release comes with a pre-built executable for the GUI: expressionlncr. Feel free to extract and install the release archive wherever. The executable needs to be kept in the same folder as the python scripts, as the GUI runs the scripts as jobs and needs to be able to find them.

### Running Scripts:

Specify --help for every script to get the options, defaults, and an example. The default pipeline with minimal options (at the time of this writing) is *not* the help example but rather the script defaults and is:

#### 1. Get lncRNA

```
./get_lncrna.py
```

This downloads a file lncrnas.bed from NONCODE for Human to data/lncrnas.bed. It has over 200k lncRNAs in it. Specify your own BED file of any identifiers at all (not just lncRNAs) using -c or --custom-bed.

#### 2. Get Ensembl Probes

```
./get_ensembl_probes.py 
```

This downloads files from ENSEMBL funcgen database's FTP server's flat GZ archives and creates a new file data/probes.bed. This BED file has over 20 million expression array probe sites in it.

If Ensembl's funcgen database isn't sufficient for your needs, a more experimental usage of the tool would be to roll your own archives to the paths the tool expects and specify -n or --no-download to create your own BED file of probes...or just skip this step altogether and use a custom probes.bed.

#### 3. Find Overlap

```
./find_overlap.py
```

Finds the overlap between data/lncrnas.bed and data/probes.bed; outputs the overlap to three files: data/overlap.bed, data/lncrnas.overlap.bed, data/probes.overlap.bed. The first is a BED-like file that contains each overlapping pair. Other two are just subsets of the input files with only the overlapping features.

#### 4. Find GEO DataSeries

```
./find_geo_dataseries.py
```

Searches for relevant GEO platforms, ones with array probes overlapping the data/probes.overlap.bed file via the NCBI Entrez E-Utils.

Then, it looks for human (or --organism if you've been specifying an Ensembl alternative the whole time) GEO DataSets from the NCBI GDS database according to a --search-terms string. This search terms string should be the same format as the regular GEO terms constructed by the "Advanced Search Builder" on the GEO website, with one caveat. It must not specify the following terms since they're already specified in the tool: [Organism], [Entry Type], [GEO Accession].

You should craft a relevant set of terms that cuts down the search space to only useful samples. In fact, the tool forces this on you to an extent by always specifying "GDS[Entry Type]" to restrict to curated GEO DataSets. (But this is not an artificial limitation: GEO DataSets always have the series matrix annotation files which are needed in the pipeline.)

Files with the found GEO Series (but not actual data) corresponding to found DataSets are downloaded to data/matrices/..., namely: series.txt, summary.txt, summary.txt.esearch, and summary.txt.esummary. You can check the size of the data to be downloaded in summary.txt.

This step takes about 10 minutes (depending on your internet and the GEO FTP server load) for all human GEO Data Sets using Ensembl funcgen GEO Platforms (800ish as of this writing). You can skip the step that retrieves the size of the GEO series matrix annotation files (the GEO data retrieved later in the pipeline) by specifying -k or --skip-series-info. Then, find_geo_dataseries.py will only take a couple seconds (or whatever the time it takes to run two queries on the NCBI Entrez E-Utils server).

If you are interested in retrieving information on *all* GEO Series, not just the curated GEO DataSets, then you may pass the -s, --allow-data-series flag. This should reduce the case where Ensembl funcgen probes are found to overlap lncRNAs but there are no corresponding GEO DataSets to those probe platforms, only GEO Series.

Finally, if you don't care about the size of data downloaded in the next step you may skip the process of retrieving info about the matrix file sizes using the -k, --skip-series-info flag. This will speed up this speed considerably, which is significant if retrieving information on all GEO Series.

#### 5. Get GEO DataSeries

```
./get_geo_dataseries.py
```

Downloads the GEO Series in data/matrices/series.txt to data/matrices/GSExxxxx_series.matrix.txt.gz. The speed of this step is dependant on your internet connection and the NCBI FTP server. For the 800ish GEO Series corresponding to the 800 GEO DataSets using Ensembl human funcgen platforms, it took about half an hour on 150Mbps fibre to download the 4GB of data averaging 15Mbps from the NCBI FTP server.

You can terminate the get_geo_dataseries.py process while it reads "downloading data for series XXXX ..." and restart the script later; download completion progress is saved to a file (-c, --completed-series-file) which defaults to data/matrices/completed_series.txt. Series which cannot be downloaded are logged to file (-k, --skipped-series-file), by default at data/matrices/skipped_series.txt. You might need to kill and restart this process if your connection to NCBI's FTP server hangs on downloading a file.

It's worth noting if you're more interested in a pseudo-random subset of data than downloading it all, then check out and adapt the example shell scripts at: generateGeoDataSetCount.sh, generateOverlaps.sh, generateProbeFiles.sh.

#### 6. Parse GEO DataSeries

```
./parse_geo_dataseries.py
```

Parses the series in data/matrices using overlap file data/overlap.bed and BED file data/lncrnas.bed; outputs results to data/results/.

A more detailed explanation is that the parser generates a map of GEO Platform -> Probe Set -> Probe Name -> List of max probe value among samples for each GEO series. Then, it reads in data/overlap.bed and makes a map of the previously found lncRNA (or whatever you specified as "lncRNAs") -> probe relationships. It uses these two maps to generate a map of lncRNA -> expression. Then, it bins out the lncRNAs based on expression/no probe data/no probes to these files: data/results/expressed.lncrnas.txt, data/results/noexpressiondata.lncrnas.txt, data/results/nonoverlapping.lncrnas.txt.

By the time this step is over, you will likely get several warning messages like "... expected expression data for lncRNA ... but none found". It can be safely ignored as it will just result in fewer found lncRNA/expression data matches, but this is likely due to one of the following reasons:

*a. Your overlap.bed file has more matches than you downloaded information for, i.e. you truncated the search step.

*b. An Ensembl funcgen database expression array has no GPL number mapped to it in org_array_gpl.py (for ex. Human HT 12 v3, v4), and this array's probe(s) overlaps your lncRNA file.

*c. There are no GEO DataSets corresponding to expression arrays overlapping your lncRNAs, only GEO Series. You may re-run the find_geo_dataseries.py step using flag "-s" or "--allow-data-series" to include Series.

*d. A probe overlapping the lncRNA is called something slightly different in the Ensembl funcgen database file compared to the GEO Series matrix summary file.

You can terminate the parse_geo_dataseries.py process while it reads "parsing file (x/y): filename @ time ..." and restart the script later; parsing completion progress is saved to a file (-c, --completed-files-file) which defaults to data/results/expressed_series/completed_files.txt.

### Pipeline Runtimes

The complete pipeline runtime depends mostly on 2 factors: your internet connection speed to NCBI's FTP server, and the number of GEO Series or DataSets to be downloaded and parsed. As a rough estimate, budget 4 hours for running the pipeline on Human with no search filters restricting to GEO DataSets only, and budget 24 hours for Human with no search filters allowing all GEO Series.

Please note that at certain points in Steps 5 and 6 (retrieving and parsing GEO data, see step details for when) the python processes are killable to allow restarting the jobs as convenient. Basically all the pipeline runtime is in retrieving and parsing the GEO data; fetching the lncRNAs and probes and finding their overlap takes minutes.
