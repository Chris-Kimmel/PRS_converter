# Run this script with "bash -i test.sh". Otherwise, conda will complain it's not initialized.
# Apparently "bash -i" uses the user's bashrc. You could also run it with "source", but that will
# change your working directory and current conda environment.

set -e # Quit if there is an error

echo "setting up environment"

# TODO: How do you properly set up a conda environment from within a shell script? Shouldn't need.
conda activate tombo2 # TODO: make everything portable!! bundle environment with PRS_converter!!

echo "running tests"

set -u # Throw an error if an undefined variable is used
set -x # Echo every line before running it

cd ~/PRS_converter/test # TODO: Because activating conda changes the current directory to home

declare -a test_basenames
declare -a correct_md5sums
test_basenames[0]=061120_8079m6A_IVTcarrierRNA_ligation_polyA.tombo.per_read_stats
correct_md5sums[0]=9cf208e3468da031c7a3c7ec32361f7a # Very trustworthy
test_basenames[1]=depth_50k_fisher_3_v14.tombo.per_read_stats
correct_md5sums[1]=30bc20e364f440f5dc93a55c820a44b2 # Not as trustworthy

fail_flag=false
for i in 0 1
do
    test_basename=${test_basenames[i]}
    correct_md5sum=${correct_md5sums[i]}
    for py_version in 2 # TODO: stupid code, get rid of it
    do
        dest_file=${test_basename}_python${py_version}_test.csv
        python${py_version} ../PRS_converter.py -o ${test_basename} ${dest_file}
        resulting_md5sum=`md5sum ${dest_file} | cut -d " " -f1`
        if [ "${resulting_md5sum}" != "${correct_md5sum}" ]; then
            fail_flag=true
            echo "failed test (python${py_version}): ${test_basename}"
        fi
    done
done

if [ ${fail_flag} == false ]; then
    echo "all tests successful"
fi
