#!/usr/bin/env python
# Reads reddit self-text posts and writes them to a file!

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
            '1': 'datasets/Exp01-reddit-bitcoin-faqs.txt',
            '2': 'datasets/Exp01-reddit-bitcoin-nonfaqs.txt'
        }

        return

    def read(self):
        """
        Ask reddit for some data from a sub, and we'll step through each returned item for processing.

        :return:
        """

        try:
            reddit_response = requests.get(self.subreddit_url, headers=self.headers).json()['data']
            reddit_post_list = reddit_response['children']

            post_count = len(reddit_post_list)
            post_counter = 0

            for reddit_post in reddit_post_list:
                post_counter += 1
                if reddit_post['data']['is_self']:
                    # This is a self-post. Save the text, ommitting newlines.
                    candidate_text = reddit_post['data']['selftext']
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
            prompt_string = 'This text can be classified as one of the following, or 0 to skip: \n'
            for key, value in self.classes:
                prompt_string = '{}{} for {}\n'.format(prompt_string, key, value)

            print(prompt_string)
            user_class_choice = input("Which class does this text belong to? \n>").toUpper()

            if user_class_choice != '0':
                with open(self.classes['user_class_choice'], 'ab+') as outfile:
                    outfile.write(candidate_text)
                    print('\nWrote to {}\n'.format(self.classes['user_class_choice']))

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
