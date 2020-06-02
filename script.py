import csv
import sys
from pprint import PrettyPrinter
from urllib.parse import urljoin

import requests as r
from bs4 import BeautifulSoup


def get_hostname():
    try:
        return sys.argv[1]
    except IndexError as e:
        print(f"You have to provide hostname URL, e.g. https://matejimposv2-master.edge.k2ng-dev.net/.\nError: {str(e)}")
        sys.exit(1)


def start_session():
    return r.Session()


def close_session(session):
    session.close()


def cook_soup(url, session):
    response = session.get(url, timeout=(120, 180))
    print(f"URL: '{url}':: it took: '{response.elapsed}' :: response status: '{response.status_code}'")
    return BeautifulSoup(response.text, "lxml")


def get_internal_links(soup):
    output = []
    elements = soup.select(f'a[href^="{get_hostname()}"]')

    for element in elements:
        if "/_doc/" not in element["href"]:
            output.append(element["href"])

    return set(output)


def create_full_link(hostname, internal_link):
    return urljoin(hostname, internal_link)


def process_page(url, session):
    links = get_internal_links(cook_soup(url, session))
    full_links = {create_full_link(get_hostname(), link) for link in links}
    return full_links


def update_links_to_visit(new_links, links_to_visit, visited):
    for link in new_links:
        if link in visited:
            links_to_visit.discard(link)
        else:
            links_to_visit.add(link)

    return links_to_visit


# pylint:disable=dangerous-default-value
def looper(session, visited=set(), links_to_visit=None):
    links_to_visit = process_page(get_hostname(), session)

    while True:
        if len(links_to_visit) > 0:
            for link in list(links_to_visit):
                # quick hack to avoid files - can lose some links due to this, maybe
                if link[-4] == ".":
                    links_to_visit.discard(link)
                    continue
                if link not in visited:
                    visited.add(link)
                    links_to_visit = update_links_to_visit(
                        process_page(link, session), links_to_visit, visited
                    )
                else:
                    links_to_visit.discard(link)
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
    print(f"No. of URLs scanned: {len(visited)}")


def main():
    session = start_session()
    visited = looper(session)
    close_session(session)
    pretty_print(visited)
    save_urls(visited)


if __name__ == "__main__":
    main()
