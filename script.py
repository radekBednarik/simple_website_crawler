import csv

from pprint import PrettyPrinter
from urllib.parse import urljoin

import requests as r
from bs4 import BeautifulSoup

HOSTNAME = "https://svse-v2-sint.edge-sint.k2ng-dev.net"


def start_session():
    return r.Session()


def close_session(session):
    session.close()


def cook_soup(url, session):
    response = session.get(url, timeout=(60, 120))
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


def process_page(url, session):
    links = get_internal_links(cook_soup(url, session))
    full_links = {create_full_link(HOSTNAME, link) for link in links}
    return full_links


def extend_links_to_visit(new_links, links_to_visit, visited):
    for link in new_links:
        if (link not in links_to_visit) and (link not in visited):
            links_to_visit.add(link)

    return links_to_visit


# pylint:disable=dangerous-default-value
def looper(session, visited=set(), links_to_visit=None):
    links_to_visit = process_page(HOSTNAME, session)

    while True:
        if visited != links_to_visit:
            for link in list(links_to_visit):
                if link not in visited:
                    visited.add(link)
                    links_to_visit = extend_links_to_visit(
                        process_page(link, session), links_to_visit, visited
                    )
                else:
                    continue
        else:
            break
    return visited


def save_urls(visited):
    filepath = "scanned_urls.csv"

    with open(filepath, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scanned_links"])
        for link in visited:
            writer.writerow([link])

    print(f"Scanned urls saved to: '{filepath}'")


def pretty_print(visited):
    printer = PrettyPrinter(indent=2)
    printer.pprint({"URLs visited": visited})


def main():
    session = start_session()
    visited = looper(session)
    close_session(session)
    pretty_print(visited)
    save_urls(visited)


if __name__ == "__main__":
    main()
