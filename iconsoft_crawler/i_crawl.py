
import argparse
from start import IconSoftwareRunner
from random import seed
import pendulum
from random import randint


def get_random():
    """Function for returning a random number sequence for a unique
    file name.

    command for running the Splash server inside a docker container.
    ** docker run -it -p 8050:8050 --rm scrapinghub/splash **

    Returns:
        string: Random number with date.
    """
    now = pendulum.now().format("MM-DD-YYYY")

    return f'{str(randint(10000, 99999))}-{now}'


def main():
    """main function that initializes the crawler. Parses arguments
    when ran from the command line that controls the behavior of the
    crawler.

    Returns:
        function: Calls the function that initializes the crawler.
    """

    parser = argparse.ArgumentParser(
        description='Crawl case data from iconsoftware websites -- **\
             CRAWLER NEEDS A SPLASH SERVER IN ORDER TO ACQUIRE HTTP \
                 RESPONSES **')

    parser.add_argument('-url',
                        type=str,
                        action='append',
                        required=True,
                        help='the url to be crawled')

    parser.add_argument('-u',
                        metavar='username',
                        type=str,
                        required=True,
                        help='the username of the account that will \
                            be logged in')

    parser.add_argument('-p',
                        metavar='password',
                        type=str,
                        required=True,
                        help='the password of the account that will \
                            be logged in')

    parser.add_argument('-s',
                        metavar='start_date',
                        type=str,
                        help='the start date for cases to be crawled')

    parser.add_argument('-e',
                        metavar='end_date',
                        type=str,
                        help='the end date for cases to be crawled')

    parser.add_argument('-v',
                        metavar='verbose',
                        type=bool,
                        default=True,
                        help='if True, will print debug data')

    parser.add_argument('-f',
                        metavar='filename',
                        default=get_random(),
                        help='.csv filename for crawled data to be \
                            saved as')

    args = parser.parse_args()

    if '.csv' in args.f:
        args.f = args.f.replace('.csv', '')

    cr = IconSoftwareRunner(args.url, args.u,
                            args.p, args.s,
                            args.e, args.f, args.v)

    if args.v:
        print(args)

    return cr.initialize()


if __name__ == "__main__":
    main()
