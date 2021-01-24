# from https://medium.com/analytics-vidhya/optimized-ways-to-read-large-csvs-in-python-ab2b36a7914e
from dask import dataframe as dd

# install like this (according to https://docs.dask.org/en/latest/install.html#pip):
# pip install "dask[complete]"

# use dask to circumvent memory-issues, which occur according to https://community.brain-map.org/t/reading-rna-seq-data-into-python/658
def read():
  return dd.read_csv('data-rnaseq/aibs_human_m1_10x/matrix.csv')
  
#Read csv with dask:  0.07900428771972656 sec