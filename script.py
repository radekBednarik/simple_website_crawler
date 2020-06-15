import csv
import signal
import sys
from datetime import datetime as dt
from datetime import timedelta
from multiprocessing import get_context
from pprint import PrettyPrinter
from time import sleep
from typing import Any, Set, Tuple, Union, Optional
from urllib.parse import urljoin, urlsplit

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
    if string == "418":
        return color_yellow(string)
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
    if time_.total_seconds() <= 1:
        return color_green(str(time_))
    if (time_.total_seconds() > 1) and (time_.total_seconds() <= 3):
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
    """Returns parsed HTML content of web page on provided <url> as <BeautifulSoup> object
    and response statistics of <url> visited.

    Arguments:
        url {str} -- url to page to parse
        session {r.Session} -- requests.Session() object

    Returns:
        Tuple[Any, Tuple[str, timedelta, int]] -- parsed content of the page as BeautifulSoup() object
        and response statistics of <url> visited
    """
    # check head first, if not file
    headers = session.head(url).headers
    content_type = headers.get('content-type')
    if ("text" in content_type.lower()) or ("html" in content_type.lower()):
        try:
            response = session.get(url, timeout=(60, 120))
            soup = BeautifulSoup(response.text, "lxml")
        except Exception as e:
            print(f"Func 'cook_soup': Exception encountered: {str(e)}")
            response = r.Response()
            response.elapsed = timedelta(seconds=0)
            response.status_code = 400
            soup = BeautifulSoup("<html></html>", "lxml")
    else:
        # return dummies
        response = r.Response()
        response.elapsed = timedelta(seconds=0)
        response.status_code = 418
        soup = BeautifulSoup("<html></html>", "lxml")

    print(
        "URL: '{}' :: it took: '{}' :: response status: '{}'".format(
            color_blue(url),
            color_response_time(response.elapsed),
            color_response_status(str(response.status_code)),
        )
    )
    sleep(0.1)
    return (soup, (url, response.elapsed, response.status_code))


def get_internal_links(
    soup: Tuple[Any, Tuple[str, timedelta, int]]
) -> Tuple[Set[str], Tuple[str, timedelta, int]]:
    """Returns all internal links, which can be found in provided parsed page content, 
    and response statistics of url visited.

    Links are selected via this css filters:

        'a[href^="{get_hostname()}"], a[href^="/"]'

    Arguments:
        soup {Tuple[Any, Tuple[str, timedelta, int]]} -- parsed page content 
        and passed visited url statistics

    Returns:
        Tuple[Set[str], Tuple[str, timedelta, int]] -- set of internal hrefs (links)
        and statistics of url visited
    """
    output = []
    base = get_hostname()
    elements = soup[0].select(f'a[href^="{base}"], a[href^="/"]')

    for element in elements:
        output.append(element["href"])

    return (set(output), soup[1])


def create_full_link(hostname: str, internal_link: str) -> Optional[str]:
    """Returns full link from <hostname> and <internal_link> parts.

    Uses urllib.parse.urljoin() method.

    Arguments:
        hostname {str} -- hostname part of URL
        internal_link {str} -- part of URL parsed from webpage HTML code

    Returns:
        str -- full URL link
    """
    hostname_split = urlsplit(hostname)
    internal_link_split = urlsplit(internal_link)

    # if found internal link has netloc part
    # check, if this part of url contains some part
    # of hostname netloc. If so, than consider it
    # internal link and urljoin() full hostname and internal link
    # that will use netloc part from internal link
    # that is useful in case of big websites with subdomains
    if internal_link_split.netloc != "":
        parts = hostname_split.netloc.split(sep=".")
        for part in parts[1:-1]:
            if part in internal_link_split.netloc:
                return urljoin(hostname, internal_link)
        else:
            return None

    return urljoin(hostname, internal_link_split.path)


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
        Tuple[Set[str], Tuple[str, timedelta, int]] -- set of full URL links found on parsed page retrieved via provided <url>
        and response statistics for visited <url>
    """
    links = get_internal_links(cook_soup(url, session))
    full_links = {create_full_link(get_hostname(), link) for link in links[0]}
    full_links_ = {link for link in full_links if link is not None}
    return (full_links_, links[1])


def pool(
    links_to_visit: Tuple[Set[str], Tuple[str, timedelta, int]],
    session: r.Session,
    visited: Set[str],
    stats: Set[Tuple[str, timedelta, int]],
) -> Tuple[
    Tuple[Set[str], Tuple[str, timedelta, int]],
    Set[str],
    Set[Tuple[str, timedelta, int]],
]:
    """Runs process_page() func as worker using multiprocessing module for all links.
    Returns new links to scan, visited links and request stats for visited links.

    Args:
        links_to_visit (Tuple[Set[str], Tuple[str, timedelta, int]]): URL links to scan and request stat for URL
        session (r.Session): session object
        visited (Set[str]): set of visited links
        stats (Set[Tuple[str, timedelta, int]]): set of links response stats

    Returns:
        Tuple[ Tuple[Set[str], Tuple[str, timedelta, int]], Set[str], Set[Tuple[str, timedelta, int]], ]: 
        ((set of links to visit, url's response stats), set of visited urls, set of tuple with visited url, response time, response status code)
    """
    args = [(link, session) for link in links_to_visit[0]]

    with get_context("spawn").Pool(maxtasksperchild=1) as p:
        list_links_to_visit = p.starmap(process_page, args)

    final_set: Set[str] = list_links_to_visit[0][0]

    # add all visited links to set
    for item in list_links_to_visit:
        visited.add(item[1][0])
        stats.add(item[1])
        final_set = item[0].difference(final_set) | final_set

    final_set = {link for link in final_set if link not in visited}
    links_to_visit = (final_set, list_links_to_visit[0][1])

    return (links_to_visit, visited, stats)


def looper_with_pool(
    session: r.Session,
    visited: Union[Set[Any], Set[str]] = set(),
    links_to_visit: Union[None, Tuple[Set[str], Tuple[str, timedelta, int]]] = None,
) -> Set[Tuple[str, timedelta, int]]:
    """Loops pool() funs until there is no unvisited link left.
    Returns set with tuples of visited links, their response time and response code.

    Args:
        session (r.Session): session object
        visited (Union[Set[Any], Set[str]], optional): set of visited links. Defaults to set().
        links_to_visit (Union[None, Tuple[Set[str], Tuple[str, timedelta, int]]], optional): links to be scanned. Defaults to None.

    Returns:
        Set[Tuple[str, timedelta, int]]: set with tuples of visited links, their response time and response code
    """
    links_to_visit = process_page(get_hostname(), session)
    visited = {links_to_visit[1][0]}
    stats = set()

    while True:
        print(f"Found new links to scan: {len(links_to_visit[0])}")
        if len(list(links_to_visit)[0]) > 0:
            links_to_visit, visited, stats = pool(
                links_to_visit, session, visited, stats
            )
        else:
            break

    return stats


def save_urls(visited: Set[Tuple[str, timedelta, int]]) -> None:
    """Saves found URLs stats into .csv file.

    Arguments:
        visited {Set[Tuple[str, timedelta, int]]} -- set of all found URLs response stats on the site
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
        visited {Set[Tuple[str, timedelta, int]]} -- set of all found URLs on the site
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
    visited = looper_with_pool(session)
    close_session(session)
    pretty_print(visited)
    save_urls(visited)


if __name__ == "__main__":
    main()
