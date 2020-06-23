# This is a command line tool to transform a Tombo per-read statistics file into a CSV file

# TODO: Implement --progress option
# TODO: Implement --overwrite option
# TODO: Speed up the step that fills in the table
# TODO: Rewrite the code so it works with more arbitrary data.
# (Particularly data in which read ids or positions are not all contiguous.)

import numpy as np
import os
import sys
import h5py
import argparse

### Argparse ###

parser = argparse.ArgumentParser(description='Read the data from a Tombo per-read statistics'
		+ ' file, then save that data to a CSV file.')
parser.add_argument('READPATH', help='path to the per-read'
		+ ' statistics file')
parser.add_argument('WRITEPATH', help='path to the file where the CSV results will be written')
parser.add_argument('-p', '--progress', help='show percent progress while running',
		action='store_true')
parser.add_argument('-o', '--overwrite',
		help='overwrite the file at WRITEPATH if it already exists', action='store_true')
args = parser.parse_args()

print('This script will unpack HDF5 file {} into a CSV file and store the result at {}.'.format(args.READPATH, args.WRITEPATH))
if args.progress: print('This script will show progress as it transforms the data.')
if args.overwrite: print('This script will overwrite the CSV file at {} if it already exists.'.format(args.WRITEPATH))

### Checking validity of input ###

if not os.path.exists(args.READPATH):
    print('Error: The file {} does not exist.'.format(args.READPATH))
if os.path.exists(args.WRITEPATH) and not args.overwrite:
    errstring = 'Error: This program will not overwrite files unless the command-line argument --overwrite is used. There is already a file at {}'.format(args.WRITEPATH)
    print('errstring')
    sys.exit()

# TODO: Assert we have write permissions and read permissions

### Reading the HDF5 file ###

prs_path = args.READPATH

with h5py.File(prs_path, 'r') as hdf5file:
    block_stats = hdf5file['Statistic_Blocks']['Block_0']['block_stats'] 
    read_ids = hdf5file['Statistic_Blocks']['Block_0']['read_ids']
    '''There is another dataset in Block 0. It's called read_id_vals.
    When I wrote this code, read_id_vals was just a 1-dimensional dataset
    that assumed the value i at index i. As far as I can tell, read_id_vals
    is not important.
    '''
    
    bs_struct_array = np.asarray(block_stats)

bs_rec_array = np.rec.array(bs_struct_array)

### Calculate some basic data ###

pos_array = bs_rec_array['pos']
pos_set = set(pos_array)
num_poss = len(pos_set)
pos_list = list(pos_set).sort()
# TODO: Iterate through min_pos, num_poss, num_reads and ensure I didn't assume things were intervals
#min_pos = min(pos_set)

ri_array = bs_rec_array['read_id']
ri_set = set(ri_array)
ri_list = list(ri_set).sort()
num_reads = len(ri_set)

### Process the data into table form ###

# Sort bs_rec_array. Maybe try sorting primarily by 'pos'. That might help us fill the table faster below.
# This step took me 20 seconds on a bs_rec_array with 28 million entries (Owens cluster, 1 node, 28 cores)
bs_rec_array_sorted = bs_rec_array.copy()
bs_rec_array_sorted.sort(order=['read_id','pos'], kind='mergesort')

table = np.full((num_reads, num_poss), np.nan, np.dtype('f8'), order='C') # Interestingly, order='F' doesn't seem slower

# On a 28-core CPU in the Owens cluster this loop took a little over 3 minutes on a rec_array with 28 million entries:
for pos, stat, read in bs_rec_array_sorted:
    table[ri_list.index(read), pos_list.index(pos)] = stat

### Write data ###

assert len(table) > 0, 'Trying to write a table with no entries'

row_labels = np.asarray(ri_list).reshape(-1,1)

with open(args.WRITEPATH, 'wb') as fh:
    
    header_entries = map(str, ['read_id'] + ri_list)
    header = ','.join(header_entries) + '\n'
    fh.write(header)
    
    for i, row in enumerate(table):
        row_entries = map(str, [i] + list(row))
        row = ','.join(row_entries)+'\n'
        fh.write(row)

print('DONE')
