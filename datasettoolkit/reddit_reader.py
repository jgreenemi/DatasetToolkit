#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Reads reddit self-text posts and writes them to a file!

import os
import requests
from pprint import pprint


class RedditReader():
    def __init__(self):
        """
        A class for handling both the retrieval of text data from the reddit website, and for passing that to files
        per interactive user instruction. Use querystrings for limiting response, i.e. /r/bitcoin/new/.json?limit=1

        """

        self.subreddit_url = r'http://www.reddit.com/r/bitcoin/new/.json'
        self.headers = {
            'User-Agent': r'DSTK-RedditReader/0.1'
        }
        self.classes = {
            '1': 'datasettoolkit/datasets/Exp01-reddit-bitcoin-faqs.txt',
            '2': 'datasettoolkit/datasets/Exp01-reddit-bitcoin-nonfaqs.txt'
        }
        self.checkpoint_file = 'datasettoolkit/datasets/Exp01-checkpoint.txt'

        if os.path.isfile(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as checkpoint:
                self.current_after = checkpoint.read()
            print('Found a checkpoint file! Starting with after={}'.format(self.current_after))
        else:
            self.current_after = ''

        return

    def read(self):
        """
        Ask reddit for some data from a sub, and we'll step through each returned item for processing.

        :return:
        """

        try:
            post_count = 0
            post_counter = 0

            while post_counter < 1000:
                if not self.current_after:
                    reddit_response = requests.get(
                        self.subreddit_url,
                        headers=self.headers
                    ).json()['data']
                else:
                    reddit_response = requests.get(
                        '{}?after={}'.format(
                            self.subreddit_url,
                            self.current_after
                        ),
                        headers=self.headers
                    ).json()['data']
                reddit_post_list = reddit_response['children']

                post_count += len(reddit_post_list)
                self.current_after = reddit_response['after']

                # Also save the self.current_after value to a checkpoint file to pick up from this point later if you
                # leave and return to classify more posts.
                with open(self.checkpoint_file, 'wb+') as checkpoint:
                    checkpoint.write(self.current_after)

                for reddit_post in reddit_post_list:
                    post_counter += 1
                    if reddit_post['data']['is_self']:
                        # This is a self-post. Save the text, ommitting newlines.
                        candidate_text = '{} {}'.format(
                            reddit_post['data']['title'].encode('utf-8'),
                            reddit_post['data']['selftext'].encode('utf-8'))
                        candidate_text = candidate_text.replace('\n', ' ').replace('\r', '')

                        # Can prompt the user now about which class this should be sent to.
                        self.prompt_and_write(candidate_text)
                    print('[{}/{} posts evaluated.]'.format(post_counter, post_count))
            return

        except Exception as e:
            self.exception_handling(e)

    def prompt_and_write(self, candidate_text):
        """
        When items are passed in, you can ask the viewer to classify the text for writing to one file, or another, based
        on what the text is about. i.e. a selftext post from reddit is shown to the user, and they're asked if it should
        be categorized as type A or type B. Based on the response, the text is appended to a file for type A or B text.
        :return:
        """
        try:
            # Present the class options to the user.
            print('\n====\n{}\n====\n'.format(candidate_text))
            prompt_string = 'This text can be classified as one of the following, or 0 to skip: \n'
            for key, value in self.classes.iteritems():
                prompt_string = '{}{} for {}\n'.format(prompt_string, key, value)

            print(prompt_string)
            user_class_choice = str(input("Which class does this text belong to? \n>"))

            if user_class_choice != '0':
                outfile = open(self.classes[user_class_choice], 'ab+')
                # Don't forget that final newline character - that's how the cleaner knows to separate training examples!
                outfile.write('{}\n'.format(candidate_text))
                print('\nWrote to {}\n'.format(self.classes[user_class_choice]))

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
    reddit_client = RedditReader()
    reddit_client.read()
    return

if __name__ == '__main__':
    main()
