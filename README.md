## Dataset Toolkit

For quickly turning raw data into usable training sets for ML algorithms.

`datasettoolkit/configs` should only contain one config file, that you will edit according to what your dataset needs are. This reduces the amount of at-terminal attention you need to give while it runs.
`datasettoolkit/datasets` should include raw datasets for cleaning and labelling in .txt format, and the tool will write out .csv files to the same directory.