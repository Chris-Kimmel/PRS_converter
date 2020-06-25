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

# major_version = sys.version_info.major # major_version equals 2 or 3

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
    sys.exit()
if not os.access(args.READPATH, os.R_OK):
    print('Error: The file {} is not readable with your permissions.'.format(args.READPATH))
    sys.exit()
if os.path.exists(args.WRITEPATH):
    if not os.access(args.WRITEPATH, os.R_OK):
        print('Error: The file {} is not readable with your permissions.'.format(args.WRITEPATH))
        sys.exit()
    sys.exit()
    if not args.overwrite:
        errstring = 'Error: This program will not overwrite files unless the command-line argument --overwrite is used. There is already a file at {}'.format(args.WRITEPATH)
        print(errstring)
        sys.exit()
    if not os.access(args.WRITEPATH, os.W_OK):
        print('Error: The file {} is not writable with your permissions.'.format(args.WRITEPATH))
        sys.exit()
    if args.overwrite:
        print('Deleting file {}...'.format(args.WRITEPATH))
        os.remove(args.WRITEPATH)
else:
    dirpath = os.path.split(os.path.abspath(args.WRITEPATH))[0]
    if not os.access(dirpath, os.W_OK):
        print('Error: Cannot create files in directory {} with your permissions.'.format(dirpath))
        sys.exit()


### A note about the HDF5 per-read statistics file format

'''A note about the HDF file:
The HDF5 file consists of one or more blocks. As long as multiprocessing wasn't used to create the
per-read statistics HDF5 file, there will only be one block: Block_0.

Each block contains three datasets: block_stats, read_ids, and read_id_vals. Block stats is a
three-column array. Each entry looks like (pos, stat, read_id), and signifies that on read
read_id, nucleotide position pos was assigned statistic stat. Unfortunately, read_id in
the block_stats dataset is just an arbitrary integer. The TRUE read id looks like this:
4fc2fd1f-8671-4b99-a598-8d91ec81e496. To get the TRUE read id for an entry (pos, stat, read_id)
in the block_stats database, look in read_id_vals under the index read_id.

The dataset read_ids seems to encode the identity function (by which I mean the entry in position
x of database read_ids equals the number x). I assume this is always the case, but it could be
that in larger datasets, or in multiprocessed datasets, the database read_ids is used in some
intermediate step between the databases block_stats and read_id_vals (like, "To decode the read_id
field from the block_stats database, look up position read_id in database read_ids; then THAT will
tell you where to look in read_id_vals"). I'm just ignoring the read_ids database for now.

So we have a notational problem: "read id" could refer to the "true" read id (which looks like
4fc2fd1f-8671-4b99-a598-8d91ec81e496) or it could refer to the read_id column of the block_stats
database. In the following code, we will use the abbreviation rin (read id number) to refer to
the numbers in the block_stats database, and we will use the abbreviation riv (read id value) to
refer to the "true" read ids.
'''


### Reading the HDF5 file ###

print('Reading {}...'.format(args.READPATH))

prs_path = args.READPATH

with h5py.File(prs_path, 'r') as hdf5file:
    block_stats = hdf5file['Statistic_Blocks']['Block_0']['block_stats'] 
    read_ids = hdf5file['Statistic_Blocks']['Block_0']['read_ids']
    
    bs_struct_array = np.asarray(block_stats)
    riv_array = np.asarray(read_ids)

bs_rec_array = np.rec.array(bs_struct_array)


### Calculate some basic data and initialize the table ###

pos_array = bs_rec_array['pos'] # make array from the nucleotide-position column
rin_array = bs_rec_array['read_id'] # make array from the read-id-number column

pos_set = set(pos_array)
num_poss = len(pos_set)
pos_tuple = sorted(tuple(pos_set))

rin_set = set(rin_array)
num_reads = len(rin_set)
rin_tuple = sorted(tuple(rin_set))

table = np.full((num_reads, num_poss), np.nan, np.dtype('f8'), order='C') # Interestingly, order='F' doesn't seem slower
''' There is one row in table for every rin, and one column for every position.
The rin corresponding to row i is rin_tuple(i). The position corresponding to position j is pos_tuple(j).
We need to fill the table very quickly, so we need a fast way to look up the *row* corresponding
to a given *rin*, and the *column* corresponding to a given *position*.
That's what pos_to_col_index and rin_to_row_index are for.
'''
pos_to_col_index = {pos: index for index, pos in enumerate(pos_tuple)}
rin_to_row_index = {read_id_number: index for index, read_id_number in enumerate(rin_tuple)}

### Process the data into table form ###

print('Converting per-read statistics data into a table... (This is the slow step.)')

# Sort bs_rec_array. Maybe try sorting primarily by 'pos'. That might help us fill the table faster below.
# This step took me 20 seconds on a bs_rec_array with 28 million entries (Owens cluster, 1 node, 28 cores)
bs_rec_array_sorted = bs_rec_array.copy()
bs_rec_array_sorted.sort(order=['read_id','pos'], kind='mergesort')

# On a 28-core CPU in the Owens cluster this loop took a little over 3 minutes on a rec_array with 28 million entries:
num_checkpoints = 20
checkpoint_size = len(bs_rec_array_sorted)//num_checkpoints
for i, (pos, stat, read_id_number) in enumerate(bs_rec_array_sorted):
    # TODO: Assert that this table position is already empty?
    row_index = rin_to_row_index[read_id_number]
    col_index = pos_to_col_index[pos]
    table[row_index, col_index] = stat
    if i % checkpoint_size == 0:
        print('Progress: {}/{}'.format(i//checkpoint_size, num_checkpoints))


### Write data ###

print('Writing data to CSV file...')

# TODO: Make read_id_number_col and read_id_value_col and attach them to table (store in new var)
#read_id_number_col = np.asarray([rin

assert len(table) > 0, 'Trying to write a table with no entries'

with open(args.WRITEPATH, 'w') as fh:
    
    # TODO: Add read_id_value to the header
    header_entries = map(str, ['read_id_number'] + pos_tuple)
    header = ','.join(header_entries) + '\n'
    fh.write(header)
    
    # TODO: Print rows from the table that has the rin and riv columns
    for i, row in enumerate(table):
        row_entries = map(str, [rin_tuple[i]] + list(row))
        row = ','.join(row_entries)+'\n'
        fh.write(row)

print('DONE')
