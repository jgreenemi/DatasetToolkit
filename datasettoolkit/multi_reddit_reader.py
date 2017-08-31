#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Reads thousands of a subreddit's posts and writes them to files!

import json
import os
import requests
import time
from pprint import pprint


class MultiRedditReader:
    def __init__(self):
        """
        A class for handling both the retrieval of text data from the reddit website, and for passing that to files.
        Use querystrings for limiting response, i.e. /r/subreddit/new/.json?limit=100

        """
        config_contents = json.load(open('datasettoolkit/configs/config.json'))

        self.subreddits = config_contents['subreddit_labels']
        self.subreddit_url_prefix = r'http://www.reddit.com/r/'
        self.subreddit_url_suffix = r'/new/.json?limit=100'
        self.headers = {
            'User-Agent': r'DSTK-MultiRedditReader/0.2'
        }
        self.checkpoint_filepath = 'datasettoolkit/checkpoints/'
        self.output_filepath = 'datasettoolkit/datasets/'
        self.post_limit = 10000
        self.current_after = ''

        if 'destination_dir' in config_contents and config_contents['destination_dir']:
            # If the destination dir is present and not empty, let the function copy the new datasets to the
            # specified directory upon finishing. Absolute path recommended over relative path due to potential
            # filesystem scope issues.
            self.destination_dir = config_contents['destination_dir']
            print('Upon completion of script, new datasets will be copied to: \n{}'.format(self.destination_dir))
        else:
            print('No destination_dir value configured in config.json, will not copy files from local dir /datasets/.')

        return

    def read(self):
        """
        Go through each of the interest/avoid lists and read posts from each sub. Create a checkpoint file containing
        keys of "", "done", or a token for continuing. If none, assume it hasn't been done yet. If "done", skip it.
        Else, read token and continue where you left off, as well as checking the counter of how many posts we've
        already read in.

        :return:
        """

        try:
            for category, values in self.subreddits.iteritems():
                print('Now working on category "{}".'.format(category))

                # If a file exists for this category, remove it, else we'll append to old data and possibly introduce
                # duplicate entries, skewing our training results later on.
                category_filepath = '{}{}.txt'.format(self.output_filepath, category)
                if os.path.isfile(category_filepath):
                    os.remove(category_filepath)

                for subreddit_name in (self.subreddits[category]):
                    print('Reading /r/{}.'.format(subreddit_name))
                    post_count = 0
                    post_counter = 0
                    self.current_after = ''

                    # Adhere to 10ms artificial delay to go easy on the Reddit API.
                    time.sleep(0.01)

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

                            print('[{}/{} posts from /r/{} classed as "{}".]'.format(post_counter, post_count, subreddit_name, category))
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
    reddit_client = MultiRedditReader()
    reddit_client.read()
    return

if __name__ == '__main__':
    main()
