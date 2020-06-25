test_prs=/fs/project/PAS1405/General/Kimmel_Chris/061120_8079m6A_IVTcarrierRNA_ligation_polyA.tombo.per_read_stats

conda activate tombo
echo "Python 3 test"
python3 PRS_converter.py -op $test_prs out.csv

conda activate tombo2
echo "Python 2 test"
python PRS_converter.py -op $test_prs out.csv

