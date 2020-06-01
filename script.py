from pprint import PrettyPrinter
from urllib.parse import urljoin

import requests as r
from bs4 import BeautifulSoup

HOSTNAME = "https://svse-v2-sint.edge-sint.k2ng-dev.net"

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


def extend_links_to_visit(new_links, links_to_visit, visited):
    for link in new_links:
        if (link not in links_to_visit) and (link not in visited):
            links_to_visit.add(link)

    return links_to_visit


# pylint:disable=dangerous-default-value
def looper(visited=set(), links_to_visit=None):
    links_to_visit = process_page(HOSTNAME)

    while True:
        if visited != links_to_visit:
            for link in list(links_to_visit):
                if link not in visited:
                    visited.add(link)
                    links_to_visit = extend_links_to_visit(
                        process_page(link), links_to_visit, visited
                    )
                else:
                    continue
        break
    return visited


def main():
    visited = looper()
    printer = PrettyPrinter(indent=2)
    printer.pprint({"URLs visited": visited})


if __name__ == "__main__":
    main()
