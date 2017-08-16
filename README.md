## Dataset Toolkit

For quickly turning raw data into usable training sets for ML algorithms.

`datasettoolkit/configs` should only contain one config file, that you will edit according to what your dataset needs are. This reduces the amount of at-terminal attention you need to give while it runs.

`datasettoolkit/datasets` should include raw datasets for cleaning and labelling in .txt format, and the tool will write out .csv files to the same directory.

### Example Datasets

The example `text_from_reddit.txt.example` dataset is a collection of some of the text content from the top "selftext" posts from http://www.reddit.com/r/spacex. This was chosen as the example for reddit text content as the self posts tend to be several paragraphs long, giving ample data to work with. The text can range from being very similar to very dissimilar to that found in research papers, so should make for a decent realworld example of when there is a lot of noise to compete with the signal in a dataset. Or such is my thinking.

The example `text_from_papers.txt.example` dataset is a collection of text content pulled from Machine Learning-focused scientific research papers available on Arxiv. The data is pulled from the first page or two of ~12 papers recently listed on the Arxiv website under the Machine Learning category, encompassing the full Abstract and a portion of the Introduction from the respective papers.

Neither of these datasets are expected to produce a well-generalizing algorithm as neither are necessarily a good representation of their medium (reddit posts from /r/spacex don't adequately represent all of reddit, and neither does the ML-focused Arxiv papers represent all of scientific research papers), but are a starting point for me for making this utility.