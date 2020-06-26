# PRS_converter
Convert [Tombo](https://github.com/nanoporetech/tombo) per-read statistics files into CSV files.

# Usage
Suppose you have a Tombo per-read statistics file at `/path/to/prs/file`, and you want to transform it into a CSV file at `/path/to/future/csv/file.csv`. Then run the following code at your terminal. (Don't type the `$`.)
```bash
$ python /path/to/PRS_converter.py /path/to/prs/file /path/to/future/csv/file.csv
```
(If you are in the same directory as this readme file, use `PRS_converter.py` as `/path/to/PRS_converter.py`.)

PRS_converter will not delete the per-read statistics file.

# Output format
The output CSV file will have a row for every read and a column for every nucleotide position. Rows are labeled by labeled by their read IDs, and columns are labeled by  numbers representing nucleotide positions. (These labels come from the "read_id" and "pos" fields of Tombo's per-read statistics file. "pos" seems to correspond with nuleotide position on the reference genome.)

# Troubleshooting
Make sure Python is installed (or that a Python module is loaded). This script was written for Python 2 but it should work with Python 3 as well. You can check Python's version (and whether it's installed) by typing `python --version` at the terminal.

To see available command-line options for PRS_converter.py, run
```bash
$ python /path/to/PRS_converter.py -h
```
at your terminal.

# Notes
* This script was inadequately tested. Be careful.
* Per-read statistics files are produced by Tombo's `tombo detect_modifications` command. If `tombo detect_modifications` is fed the `--processes` or `--multiprocess-region-size` options then *this script will not work right*: it will only produce a CSV file containing per-read statistics for part of your genome.
* The output CSV may be smaller than the per-read statistics file, because the per-read statistics file stores data in an inefficient way.
* Ignore the Jupyter notebook(s).
