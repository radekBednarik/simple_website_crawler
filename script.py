import csv
import signal
import sys
from datetime import datetime as dt
from datetime import timedelta
from pprint import PrettyPrinter
from time import sleep
from typing import Any, Set, Union, Tuple
from urllib.parse import urljoin

import requests as r

# pyre-ignore
from bs4 import BeautifulSoup

# pyre-ignore
from colorama import Fore, init


# pylint:disable=unused-argument
def signal_handler(signum: int, stack_frame: Any) -> None:
    """Cleanly exits the running script without ugly stacktrace in the console.

    Arguments:
        signum {int} -- signal.SIGINT number
        stack_frame {Any} -- stack frame
    
    See:
        https://docs.python.org/3/library/signal.html#signal.signal
    """
    print("\rYou terminated the script execution.")
    sys.exit(0)


def start_sigint_catching() -> None:
    """Sets the handling function for SIGINT.

    See:
        https://docs.python.org/3/library/signal.html#signal.signal
    """
    signal.signal(signal.SIGINT, signal_handler)


def start_coloring() -> None:
    """Initializes coloring of the console output via Colorama.

    See:
        https://github.com/tartley/colorama
    """
    init()


def color_green(string: str) -> str:
    """Returns string to be printed out by given colour.

    Arguments:
        string {str} -- string to be colourized

    Returns:
        str -- colourized string
    """
    return f"{Fore.GREEN}{string}{Fore.RESET}"


def color_red(string: str) -> str:
    """Returns string to be printed out by given colour.

    Arguments:
        string {str} -- string to be colourized

    Returns:
        str -- colourized string
    """
    return f"{Fore.RED}{string}{Fore.RESET}"


def color_yellow(string: str) -> str:
    """Returns string to be printed out by given colour.

    Arguments:
        string {str} -- string to be colourized

    Returns:
        str -- colourized string
    """
    return f"{Fore.YELLOW}{string}{Fore.RESET}"


def color_blue(string: str) -> str:
    """Returns string to be printed out by given colour.

    Arguments:
        string {str} -- string to be colourized

    Returns:
        str -- colourized string
    """
    return f"{Fore.BLUE}{string}{Fore.RESET}"


def color_response_status(string: str) -> str:
    """Returns colorized requests response status code to be printed in the console.

        Green: 200 - 299

        Red: 300 - 399

        Yellow: other

    Arguments:
        string {str} -- string to be colourized

    Returns:
        str -- colourized string
    """
    if string.startswith("2"):
        return color_green(string)
    if string.startswith("4"):
        return color_red(string)
    return color_yellow(string)


def color_response_time(time_: timedelta) -> str:
    """Returns colorized request response timedelta value to be printed in the console.

        timedelta.seconds <= 1: green

        timedelta.seconds > 1 and <= 5: yellow

        other: red

    Arguments:
        time_ {timedelta} -- timedelta value returned by requests.response()

    Returns:
        str -- colourized string
    """
    if time_.seconds <= 1:
        return color_green(str(time_))
    if (time_.seconds > 1) or (time_.seconds <= 5):
        return color_yellow(str(time_))
    return color_red(str(time_))


def get_hostname() -> str:
    """Returns provided URL hostname as sys.argv[1]

    Returns:
        str -- URL hostname, e.g. https://www.ihned.cz
    """
    try:
        return sys.argv[1]
    except IndexError as e:
        print(
            f"You have to provide hostname URL, e.g. https://www.ihned.cz.\nError: {str(e)}"
        )
        sys.exit(1)


def start_session() -> r.Session:
    """Returns requests module Session object

    Returns:
        {r.Session} -- requests.Session() object
    """
    return r.Session()


def close_session(session: r.Session) -> None:
    """Closes requests.Session() session.

    Arguments:
        session {r.Session()} -- requests.Session() object
    """
    session.close()


def cook_soup(url: str, session: r.Session) -> Tuple[Any, Tuple[str, timedelta, int]]:
    """Returns parsed HTML content of web page on provided <url> as <BeautifulSoup> object.

    Arguments:
        url {str} -- url to page to parse
        session {r.Session} -- requests.Session() object

    Returns:
        BeautifulSoup -- parsed content of the page as BeautifulSoup() object
    """
    response = session.get(url, timeout=(30, 60))
    soup = BeautifulSoup(response.text, "lxml")
    print(
        "URL: '{}' :: it took: '{}' :: response status: '{}'".format(
            color_blue(url),
            color_response_time(response.elapsed),
            color_response_status(str(response.status_code)),
        )
    )
    return (soup, (url, response.elapsed, response.status_code))


def get_internal_links(
    soup: Tuple[Any, Tuple[str, timedelta, int]]
) -> Tuple[Set[str], Tuple[str, timedelta, int]]:
    """Returns all internal links, which can be found in provided parsed page content.

    Links are selected via this css filters:

        'a[href^="{get_hostname()}"], a[href^="/"]'

    Arguments:
        soup {BeautifulSoup} -- parsed page content.

    Returns:
        Set[str] -- set of internal hrefs (links)
    """
    output = []
    elements = soup[0].select(f'a[href^="{get_hostname()}"], a[href^="/"]')

    for element in elements:
        output.append(element["href"])

    return (set(output), soup[1])


def create_full_link(hostname: str, internal_link: str) -> str:
    """Returns full link from <hostname> and <internal_link> parts.

    Uses urllib.parse.urljoin() method.

    Arguments:
        hostname {str} -- hostname part of URL
        internal_link {str} -- part of URL parsed from webpage HTML code

    Returns:
        str -- full URL link
    """
    return urljoin(hostname, internal_link)


def process_page(
    url: str, session: r.Session
) -> Tuple[Set[str], Tuple[str, timedelta, int]]:
    """Wraps several functions under one hood.

    Visits URL, gets HTML, parses it, gets internal links, converts them to full links
    and returns them as set.

    Arguments:
        url {str} -- URL to be scanned for links.
        session {r.Session} -- requests.Session() object

    Returns:
        Set[str] -- set of full URL links found on parsed page retrieved via provided <url>
    """
    links = get_internal_links(cook_soup(url, session))
    full_links = {create_full_link(get_hostname(), link) for link in links[0]}
    return (full_links, links[1])


def update_links_to_visit(
    new_links: Tuple[Set[str], Tuple[str, timedelta, int]],
    links_to_visit: Tuple[Set[str], Tuple[str, timedelta, int]],
    visited: Set[str],
    stats: Set[Tuple[str, timedelta, int]],
) -> Tuple[Set[str], Tuple[str, timedelta, int]]:
    """Updates set of URL links, which are to be scanned.

    Each link of new_links set is validated, whether to be added to links_to_visit set or be discarded from it.

    Arguments:
        new_links {Set[str]} -- set of new URLs retrieved from page
        links_to_visit {Set[str]} -- set of URLs to be visited
        visited {Set[str]} -- set of URLs which were visited

    Returns:
        Set[str] -- updated set of URLs to be visited
    """
    for link in new_links[0]:
        if link in visited:
            links_to_visit[0].discard(link)
        else:
            links_to_visit[0].add(link)

    stats.add(new_links[1])

    return links_to_visit


# pylint:disable=dangerous-default-value
def looper(
    session: r.Session,
    visited: Union[Set[Any], Set[str]] = set(),
    links_to_visit: Union[None, Tuple[Set[str], Tuple[str, timedelta, int]]] = None,
) -> Set[Tuple[str, timedelta, int]]:
    """Scans for all internal URLs, starting with provided hostname of the site.

    Scan leverages infinite loop to avoid exceeding recursion limit in case of very large number
    of links on large sites.

    Arguments:
        session {r.Session} -- requests.Session() object

    Keyword Arguments:
        visited {Union[Set[Any], Set[str]]} -- set of visited URLs, starts as empty set (default: {set()})
        links_to_visit {Union[None, Set[str]]} -- set of URLs to visit. Loop will continue, until this set is empty (default: {None})

    Returns:
        Set[str] -- set of visited URLs
    """
    links_to_visit = process_page(get_hostname(), session)
    stats = set()

    while True:
        if len(links_to_visit[0]) > 0:
            for link in list(links_to_visit[0]):
                try:
                    # quick hack to avoid actually sending requests to files - can lose some links due to this, maybe
                    if "." in [link[-4], link[-5]]:
                        links_to_visit[0].discard(link)
                        visited.add(link)
                        stats.add((link, timedelta(milliseconds=0.0), 0))
                        continue
                    if link not in visited:
                        visited.add(link)
                        links_to_visit = update_links_to_visit(
                            process_page(link, session), links_to_visit, visited, stats
                        )
                    else:
                        links_to_visit[0].discard(link)
                    sleep(0.1)
                except Exception as e:
                    print(
                        f"Exception encountered. Link '{link}' discarded. Possible links on this page are therefore lost. \
                        \nException: {str(e)}"
                    )
                    links_to_visit[0].discard(link)
                    visited.add(link)
                    stats.add((link, timedelta(milliseconds=0.0), 0))
        else:
            break
    return stats


def save_urls(visited: Set[Tuple[str, timedelta, int]]) -> None:
    """Saves found URLs into .csv file.

    Arguments:
        visited {Set[str]} -- set of all found URLs on the site
    """
    filename = "scanned_links.csv"
    timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
    filepath = "_".join([timestamp, filename])

    with open(filepath, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scanned_links", "response_time", "response_status_code"])
        for link in visited:
            writer.writerow(link)

    print(f"Scanned urls saved to: '{filepath}'")


def pretty_print(visited: Set[Tuple[str, timedelta, int]]) -> None:
    """PrettyPrints all found URLs on the site and total count of them.

    Arguments:
        visited {Set[str]} -- set of all found URLs on the site
    """
    printer = PrettyPrinter(indent=2)
    printer.pprint({"URLs scanned": [items[0] for items in visited]})
    print(f"No. of URLs scanned: {len(visited)}")


def main() -> None:
    """Main func.
    """
    start_sigint_catching()
    start_coloring()
    session = start_session()
    visited = looper(session)
    close_session(session)
    pretty_print(visited)
    save_urls(visited)


if __name__ == "__main__":
    main()
