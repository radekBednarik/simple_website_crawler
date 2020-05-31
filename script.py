from pprint import PrettyPrinter
from urllib.parse import urljoin

import requests as r
from bs4 import BeautifulSoup

HOSTNAME = "https://en-bz.skoda-auto.com"

s = r.Session()
s.auth = ("skoda", "d42e71")


def cook_soup(url):
    response = s.get(url)
    # response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def get_internal_links(soup):
    output = []
    elements = soup.select("a[href]")

    for element in elements:
        if (
            (element["href"])
            and (element["href"].startswith("/"))
            and (element["href"] != "/")
        ):
            output.append(element["href"])

    return set(output)


def create_full_link(hostname, internal_link):
    return urljoin(hostname, internal_link)


def process_page(url):
    links = get_internal_links(cook_soup(url))
    full_links = {create_full_link(HOSTNAME, link) for link in links}
    return full_links


def looper(links, visited=set(), links_to_visit=None):
    for link_ in links:
        if link_ not in visited:
            print(link_)
            visited.add(link_)
            if visited != links_to_visit:
                return looper(process_page(link_), visited=visited)

    return visited


def main():
    links_to_visit = process_page(HOSTNAME)
    visited = looper(links_to_visit, links_to_visit=links_to_visit)
    printer = PrettyPrinter(indent=2)
    printer.pprint(visited)


if __name__ == "__main__":
    main()
