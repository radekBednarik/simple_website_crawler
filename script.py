import sys

from pprint import PrettyPrinter
from urllib.parse import urljoin

import requests as r
from bs4 import BeautifulSoup

HOSTNAME = "https://svse-v2-sint.edge-sint.k2ng-dev.net"

# if there are lots of links
sys.setrecursionlimit(sys.getrecursionlimit() * 2)

s = r.Session()


def cook_soup(url):
    response = s.get(url, timeout=(60, 120))
    print(f"URL: {url} : response status --> {response.status_code}")
    return BeautifulSoup(response.text, "lxml")


def get_internal_links(soup):
    output = []
    elements = soup.select('a[href^="https://svse-v2-sint.edge-sint.k2ng-dev.net"]')

    for element in elements:
        if "/_doc/" not in element["href"]:
            output.append(element["href"])

    return set(output)


def create_full_link(hostname, internal_link):
    return urljoin(hostname, internal_link)


def process_page(url):
    links = get_internal_links(cook_soup(url))
    full_links = {create_full_link(HOSTNAME, link) for link in links}
    return full_links


def extend_links_to_visit(new_links, links_to_visit):
    for link in new_links:
        if link not in links_to_visit:
            links_to_visit.add(link)

    return links_to_visit


# pylint:disable=dangerous-default-value
def looper(links, visited=set(), links_to_visit=None):
    links_to_visit = extend_links_to_visit(links, links_to_visit)

    for link_ in links_to_visit:
        if link_ not in visited:
            visited.add(link_)
            if visited != links_to_visit:
                return looper(
                    process_page(link_), visited=visited, links_to_visit=links_to_visit
                )

    return visited


def main():
    links_to_visit = process_page(HOSTNAME)
    visited = looper(links_to_visit, links_to_visit=links_to_visit)
    printer = PrettyPrinter(indent=2)
    printer.pprint({"URLs visited": visited})


if __name__ == "__main__":
    main()
