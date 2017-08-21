#!/usr/bin/env python
import csv
import json
import logging
import os
from math import ceil
from pprint import pprint


class TextCleaningAndLabellingClient():
    """
    Class for cleaning and labelling a raw dataset.
    """

    def __init__(self):
        """
        Set up logger and parse the config file.

        Config file will include the following:

        max_sentence_size: The max number of words to interpret for a sentence. Example: 59
        output_labels: List of Strings, each string being an output label. Example: ['Spam','Not Spam']

        """

        try:
            # Set up logging handler.
            self.logger = logging.getLogger(__name__)
            logging.basicConfig(level=logging.DEBUG)

            # Load config and populate instance vars.
            self.configs_path = os.path.join('datasettoolkit', 'configs')
            self.dataset_path = os.path.join('datasettoolkit', 'datasets')
            config_data = json.loads(open(os.path.join(self.configs_path, 'config.json')).read())

            self.max_sentence_length = config_data['max_sentence_length']
            self.output_labels = []
            for output_label in config_data['output_labels']:
                self.output_labels.append(output_label)

            # Verify received config params.
            self.logger.info('max_sentence_length={}'.format(self.max_sentence_length))
            self.logger.info('output_labels={}'.format(str(self.output_labels)))

            return

        except Exception as e:
            self.logger.error(e)

    def writer_single_row(self, single_row, filename):
        """
        Given a List, write as a new row to a CSV file. Basically the same thing as .writer() but for individual rows.
        Expected to be comparatively inefficient since this will involve multiple file accesses rather than .writer()'s
        single access to write all elements at once. Basically your harddrive IO becomes the limiting factor here.

        Expected format is like the following:

        single_row = [
            'A sentence as the first element.', '1.0'
        ]

        :param single_row: List of strings to be written as columns in a CSV file.
        :param filename: CSV file to write to.
        :return:
        """

        with open(os.path.join(self.dataset_path, filename), 'ab+') as output_file:
            wr = csv.writer(output_file, dialect='excel')
            wr.writerow(single_row)
        return

    def writer(self, multi_rows, filename):
        """
        Given a list of lists of strings,

        multi_rows looks like:

        multi_rows = [
            ['First sentence', '1.0'],
            ['Second sentence', '0.0']
        ]
        :param multi_rows:
        :param filename:
        :return:
        """
        with open(os.path.join(self.dataset_path, filename), 'ab+') as output_file:
            wr = csv.writer(output_file, dialect='excel')
            wr.writerows(multi_rows)
        return

    def cleanall(self):
        """
        Find all .txt files in datasets/ and call cleaner() on them. That way this tool can process multiple text files, or just a single one, depending on user's needs.
        :return:
        """
        return

    def cleaner(self, filename, label=-1):
        """
        From the given text file, read text as stream ('cause these will be huge) and strip out unnecessary characters (including newlines and commas). For each segment of max_sentence_length, write to a .txc file.

        Could also just overwrite the original file but I dislike the idea of mutating the source data. This also makes it possible to set up checkpoints to stop and come back to if the labeler() takes a long time to finish.

        :param filename: The name of the .txt file to read from.
        :param label: An optional Integer value of which output_label to add to the data, indexed from 0. Making optional in case you want to create a dataset of live data for an algorithm, rather than a training or test set, or in case you'll invoke the labeler() function later.
        :return:
        """
        try:
            # Determine the file path based on the self.dataset_path and the passed-in filename.
            full_input_filename = os.path.join(self.dataset_path, filename)

            with open(full_input_filename, 'rb') as raw_text_file:
                # This is not scalable! Reads in whole file rather than piece by piece.
                # Use .read().splitlines() to cross newline boundaries.
                cleaned_text_fileraw = ' '.join(raw_text_file.read().splitlines()).split(' ')
                total_number_of_raw_words = len(cleaned_text_fileraw)

            while len(cleaned_text_fileraw) > self.max_sentence_length:
                # Make line var out of the first max_sentence_length elements from the file, then delete them from the
                # original collection to prepare for next iteration.
                line = ' '.join(cleaned_text_fileraw[:self.max_sentence_length]).replace(',', '')
                del cleaned_text_fileraw[:self.max_sentence_length]

                # Write to file.
                if label == -1:
                    # Create the output filename based on input filename.
                    cleaned_text_filename = '{}.txc'.format(filename.split('.txt')[0])

                    with open(os.path.join(self.dataset_path, cleaned_text_filename), 'a+') as cleaned_file:
                        line += '\n'
                        cleaned_file.writelines(line)
                    self.logger.info('Wrote: {}'.format(line))

                else:
                    # If label wasn't -1, the user is expected to have passed in the index of the output label, so we'll
                    # create an actual CSV out of it with our writer function.
                    line_list = [line, self.output_labels[label]]

                    # Create the output filename based on input filename.
                    cleaned_text_filename = '{}.csv'.format(filename.split('.txt')[0])

                    self.writer_single_row(line_list, cleaned_text_filename)

                    # DEBUG
                    # self.logger.info('Label: {} Wrote: {}'.format(self.output_labels[label], line))

                # Give the user some indication of how far we are through the processing - could be millions of lines
                # left to go. This is not working correctly at the moment because of an apparent division problem, so
                # I'll come back to this later.
                # progress_percentage = ceil(100 - (len(cleaned_text_fileraw) / total_number_of_raw_words))
                # if progress_percentage % 2 == 0:
                #     self.logger.info('{}/{} words processed. ({}%)'.format(len(cleaned_text_fileraw), total_number_of_raw_words, progress_percentage))

            self.logger.info('{} cleaned and written to disk.'.format(filename))  # DEBUG
            return

        except Exception as e:
            self.logger.error(e)

    def labeler(self, filename):
        """
        For the given .txc file, check if a checkpoint marker exists (.txcc file). If so, start from that line in the file. If not, start from top of file. Ask the user (StdIn) which class this line belongs to. User gives 0, 1, 2, etc. based on the index of the output_labels options, and it is saved to the CSV as a new line followed by a comma, followed by the label the user offered. Update the checkpoint marker file to indicate the readline position, and update the user's percentage progress through the file so they know how much farther they have to go.

        Could also just lop off the just-finished line in the .txc file to avoid the use of a checkpoint file altogether, but I'd prefer keeping the .txc file so the user can clobber the checkpoint file to restart it if they so chose.

        To reduce the amount of actual changes written to disk, we'll write multiple rows in bulk to the .csv file, every ten decisions. They'll be passed to writer() in the format:
        multi_rows = [
            ['A positive sentence.', '1.0'],
            ['A negative sentence.', '0.0']
        ]

        :return:
        """
        return


def main():
    client = TextCleaningAndLabellingClient()

    # Testing the writer.
    # multi_rows = [
    #     ['A positive sentence.', '1.0'],
    #     ['A negative sentence.', '0.0']
    # ]
    # client.writer(multi_rows=multi_rows, filename='debugging.csv')

    client.cleaner(filename='text_from_papers.txt.example', label=0)
    #client.cleaner(filename='text_from_reddit.txt.example', label=1)
    client.logger.info('Done.')

if __name__ == '__main__':
    main()
