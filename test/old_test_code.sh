test_prs=/fs/project/PAS1405/General/Kimmel_Chris/061120_8079m6A_IVTcarrierRNA_ligation_polyA.tombo.per_read_stats

conda activate tombo
echo "Python 3 test"
python --version
python3 PRS_converter.py -op $test_prs out_py2.csv

conda activate tombo2
echo "Python 2 test"
python --version
python PRS_converter.py -op $test_prs out_py3.csv

# This is the new script:

test1_basename=061120_8079m6A_IVTcarrierRNA_ligation_polyA.tombo.per_read_stats
test1_correct_md5sum= # TODO
test2_basename=depth_50k_fisher_3_v14.tombo.per_read_stats
test2_correct_md5sum= # TODO

for basename in test1_basename

# Let's try that again

# This script must be run from the PRS_converter/test directory

set -e # Quit if there is an error
set -u # Throw an error if an undefined variable is used

declare -a test_basenames
declare -a correct_md5sums
test_basenames[0]=061120_8079m6A_IVTcarrierRNA_ligation_polyA.tombo.per_read_stats
correct_md5sums[0]= # TODO
test_basenames[1]=depth_50k_fisher_3_v14.tombo.per_read_stats
correct_md5sums[1]= # TODO

fail_flag=0
for i in {0..1}
do
    test_basename=test_basenames[i]
    correct_md5sum=correct_md5sums[i]
    for py_version in 0 3
    do
        dest_file=${test_basename}_python${py_version}.csv
        set -x
        python${py_version} ../PRS_converter.py ${test_basename} ${dest_file}
        set +x
        resulting_md5sum=`md5sum ${dest_file}`
        if [ ${resulting_md5sum} != ${correct_md5sum} ]; then
            fail_flag=1
            echo "failed test (python${py_version}): ${test_basename}"
        fi
    done
done

if [ fail_flag=0 ]; then
    echo "all tests succeeded"
fi
