#!/usr/bin/env python
import csv
import json
import logging
import os
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

    def cleaner(self, filename):
        """
        From the given text file, read text as stream ('cause these will be huge) and strip out unnecessary characters (including newlines and commas). For each segment of max_sentence_length, write to a .txc file.

        Could also just overwrite the original file but I dislike the idea of mutating the source data. This also makes it possible to set up checkpoints to stop and come back to if the labeler() takes a long time to finish.

        :return:
        """
        try:
            cleaned_text_filename = '{}.txc'.format(filename.split('.txt')[0])

            fullfilename = os.path.join(self.dataset_path, filename)
            with open(fullfilename, 'rb') as raw_text_file:
                # This is not scalable! Reads in whole file rather than piece by piece.
                cleaned_text_fileraw = str(raw_text_file.read().splitlines()).split(' ')

            while len(cleaned_text_fileraw) > self.max_sentence_length:
                line = '{}\n'.format(str(cleaned_text_fileraw[:self.max_sentence_length]))
                del cleaned_text_fileraw[:self.max_sentence_length]
                with open(os.path.join(self.dataset_path, cleaned_text_filename), 'a') as cleaned_file:
                    cleaned_file.write(line)
                self.logger.info('Wrote: {}'.format(line))

            self.logger.info('{} cleaned and written to {}.'.format(filename, cleaned_text_filename))
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

    multi_rows = [
        ['A positive sentence.', '1.0'],
        ['A negative sentence.', '0.0']
    ]
    client.writer(multi_rows=multi_rows, filename='debugging.csv')

    client.cleaner(filename='text_from_papers.txt.example')
    client.cleaner(filename='text_from_reddit.txt.example')
    client.logger.info('Done.')

if __name__ == '__main__':
    main()
