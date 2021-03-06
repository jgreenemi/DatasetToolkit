#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Reads thousands of a subreddit's posts and writes them to files!

import json
import os
import requests
import time
from pprint import pprint
from shutil import copyfile


class MultiRedditReader:
    def __init__(self, posts, stage='training'):
        """
        A class for handling both the retrieval of text data from the reddit website, and for passing that to files.
        Use querystrings for limiting response, i.e. /r/subreddit/new/.json?limit=100

        :param stage: ['training', 'eval'] Choose one for setting aside what portion of your data is to be used for training purposes, and which is to be used as evaluation.
        :type stage: str
        """
        self.stage = stage
        config_contents = json.load(open('datasettoolkit/configs/config.{}.json'.format(self.stage)))

        self.subreddits = config_contents['subreddit_labels']
        self.subreddit_url_prefix = r'http://www.reddit.com/r/'
        self.subreddit_url_suffix = r'/new/.json?limit=100'
        self.headers = {
            'User-Agent': r'DSTK-MultiRedditReader/0.2'
        }
        self.checkpoint_filepath = 'datasettoolkit/checkpoints/'
        self.output_filepath = 'datasettoolkit/datasets/'
        self.post_limit = posts
        self.current_after = ''

        if 'destination_dir' in config_contents and config_contents['destination_dir']:
            # If the destination dir is present and not empty, let the function copy the new datasets to the
            # specified directory upon finishing. Absolute path recommended over relative path due to potential
            # filesystem scope issues.
            self.destination_dir = config_contents['destination_dir']
            print('Upon completion of script, new datasets will be copied to: \n{}'.format(self.destination_dir))
        else:
            self.destination_dir = None
            print('No destination_dir value configured in config.*.json, will not copy files from local dir /datasets/.')

        return

    def read(self, noclobber=False):
        """
        Go through each of the interest/avoid lists and read posts from each sub. Create a checkpoint file containing
        keys of "", "done", or a token for continuing. If none, assume it hasn't been done yet. If "done", skip it.
        Else, read token and continue where you left off, as well as checking the counter of how many posts we've
        already read in.

        :param noclobber: If set to True, will not remove existing output files, and will cause new lines to append.
        :type noclobber: bool
        :return:
        """

        try:
            for category, values in self.subreddits.iteritems():
                print('Now working on category "{}".'.format(category))

                # If a file exists for this category, remove it, else we'll append to old data and possibly introduce
                # duplicate entries, skewing our training results later on.
                category_filename = '{}-{}.txt'.format(self.stage, category)
                category_filepath = '{}{}'.format(self.output_filepath, category_filename)
                if not noclobber and os.path.isfile(category_filepath):
                    os.remove(category_filepath)

                for subreddit_name in (self.subreddits[category]):
                    print('Reading /r/{}.'.format(subreddit_name))
                    post_count = 0
                    post_counter = 0
                    self.current_after = ''

                    # Adhere to 50ms artificial delay to go easy on the Reddit API.
                    time.sleep(0.05)

                    while post_counter < self.post_limit:
                        # Build the target URL.
                        subreddit_url = '{}{}{}'.format(
                            self.subreddit_url_prefix,
                            subreddit_name,
                            self.subreddit_url_suffix
                        )

                        if not self.current_after:
                            reddit_response = requests.get(
                                subreddit_url,
                                headers=self.headers
                            ).json()['data']
                        else:
                            reddit_response = requests.get(
                                '{}&after={}'.format(
                                    subreddit_url,
                                    self.current_after
                                ),
                                headers=self.headers
                            ).json()['data']

                        reddit_post_list = reddit_response['children']
                        post_count += len(reddit_post_list)
                        self.current_after = reddit_response['after']

                        # Save the self.current_after value to a checkpoint file to pick up from this point later if
                        # you leave and return to classify more posts.
                        # This is a candidate for deletion as new executions of the script will start from the latest
                        # posts and work backward - no need to maintain chronology across multiple executions.
                        #with open('{}{}'.format(self.checkpoint_filepath, subreddit_name), 'wb+') as checkpoint:
                        #    json.dump(self.current_after, checkpoint)

                        for reddit_post in reddit_post_list:
                            post_counter += 1

                            # This is a self-post. Save the text, ommitting newlines.
                            candidate_text = '{}'.format(
                                reddit_post['data']['title'].encode('utf-8')
                            )
                            candidate_text = candidate_text.replace('\n', ' ').replace('\r', '')

                            # Write to appropriate file.
                            outfile = open(category_filepath, 'ab+')
                            # Don't forget that final newline character - that's how the cleaner knows to separate training examples!
                            outfile.write('{}\n'.format(candidate_text))

                            if post_counter % 100 == 0:
                                # Only print this every 100 iters. Reduces time spent writing to buffer.
                                print('[{}/{} posts from /r/{} classed as "{}".]'.format(
                                    post_counter,
                                    self.post_limit,
                                    subreddit_name,
                                    category)
                                )

                print('Dataset retrieval for category "{}" is finished.'.format(category))

                # If a destination_dir has been set, copy the files over.
                if self.destination_dir:
                    print('Destination directory set - copying "{}" category file.'.format(category))
                    copyfile_result = copyfile(
                        category_filepath,
                        '{}{}'.format(self.destination_dir, category_filename)
                    )

            return

        except Exception as e:
            self.exception_handling(e)

    @staticmethod
    def exception_handling(e):
        print('Exception: {}'.format(e))
        return


def main():
    """
    Generally this is what invokes the actual reading from reddit.
    :return:
    """
    import argparse

    parser = argparse.ArgumentParser(description='Retrieve thousands of reddit posts and write them to files!')
    parser.add_argument(
        '--posts',
        type=int,
        action='store',
        default=10000,
        help='The number of posts to retrieve for each subreddit. (default: 10000)'
    )

    flags = parser.parse_args()
    print('Will retrieve {} posts per subreddit.'.format(flags.posts))

    reddit_client = MultiRedditReader(stage='training', posts=flags.posts)
    reddit_client.read(noclobber=False)
    reddit_client = MultiRedditReader(stage='eval', posts=flags.posts)
    reddit_client.read(noclobber=False)
    return

if __name__ == '__main__':
    main()
