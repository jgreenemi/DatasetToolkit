#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Reads reddit self-text posts and writes them to a file!

import json
import os
import requests
import time
from pprint import pprint


class MultiRedditReader():
    def __init__(self):
        """
        A class for handling both the retrieval of text data from the reddit website, and for passing that to files.
        Use querystrings for limiting response, i.e. /r/subreddit/new/.json?limit=100

        """

        self.subreddits = json.load(open('datasettoolkit/configs/subreddits.json'))
        self.subreddit_url_prefix = r'http://www.reddit.com/r/'
        self.subreddit_url_suffix = r'/new/.json?limit=100'
        self.headers = {
            'User-Agent': r'DSTK-MultiRedditReader/0.1'
        }
        self.checkpoint_filepath = 'datasettoolkit/checkpoints/'
        self.output_filepath = 'datasettoolkit/datasets/'
        self.post_limit = 10000
        self.current_after = {}

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
                for subreddit_name in (self.subreddits[category]):
                    print('Reading /r/{}.'.format(subreddit_name))
                    post_count = 0
                    post_counter = 0

                    # Adhere to 100ms artificial delay to go easy on the Reddit API.
                    time.sleep(0.1)

                    while post_counter < self.post_limit:
                        # Build the target URL.
                        subreddit_url = '{}{}{}'.format(
                            self.subreddit_url_prefix,
                            subreddit_name,
                            self.subreddit_url_suffix
                        )

                        reddit_response = requests.get(
                                subreddit_url,
                                headers=self.headers
                            ).json()['data']

                        #if not self.current_after[subreddit_name]:
                        #    reddit_response = requests.get(
                        #        subreddit_url,
                        #        headers=self.headers
                        #    ).json()['data']

                        #else:
                        #    reddit_response = requests.get(
                        #        '{}?after={}'.format(
                        #            subreddit_url,
                        #            self.current_after
                        #        ),
                        #        headers=self.headers
                        #    ).json()['data']

                        reddit_post_list = reddit_response['children']
                        post_count += len(reddit_post_list)
                        self.current_after[subreddit_name] = reddit_response['after']

                        # Also save the self.current_after value to a checkpoint file to pick up from this point later if
                        # you leave and return to classify more posts.
                        with open('{}{}'.format(self.checkpoint_filepath, subreddit_name), 'wb+') as checkpoint:
                            json.dump(self.current_after, checkpoint)

                        for reddit_post in reddit_post_list:
                            post_counter += 1

                            # This is a self-post. Save the text, ommitting newlines.
                            candidate_text = '{}'.format(
                                reddit_post['data']['title'].encode('utf-8')
                            )
                            candidate_text = candidate_text.replace('\n', ' ').replace('\r', '')

                            # Write to appropriate file.
                            outfile = open('{}{}.txt'.format(self.output_filepath, category), 'ab+')
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
