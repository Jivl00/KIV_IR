import time
import json
from lxml import html
import requests
import os


def crawl(seed_url, wait_time=1):
    """
    Crawl the website and return list of topics references
    :param seed_url:  URL of the seed page
    :param wait_time:  time to wait between requests - politeness
    :return:  list of topics references
    """
    visited = set()  # set of visited URLs
    url_queue = set()
    topics_refs = []
    url_queue.add(seed_url)
    visited.add(seed_url)
    while url_queue:  # while there are still URLs to visit
        url = url_queue.pop()  # get the next URL
        page = requests.get(url)  # get the page
        tree = html.fromstring(page.content)  # parse the page
        links = tree.xpath('//div[@class="mw-allpages-nav"]//a/@href')  # get links on the page
        for link in links:  # for each link
            link = 'https://theelderscrolls.fandom.com' + link  # create full URL
            if link not in visited:  # if the link was not visited
                visited.add(link)
                url_queue.add(link)
        topics_refs.append(tree.xpath('//div[@class="mw-allpages-body"]//a/@href'))  # get topics references
        time.sleep(wait_time)  # politeness
    topics_refs = [item for sublist in topics_refs for item in sublist]  # flatten the list
    return topics_refs


def scrape_urls(topics_refs, folder, wait_time=1):
    """
    Scrape the URLs and save the content to JSON files
    :param topics_refs:  list of topics references
    :param folder:  folder to save the JSON files
    :param wait_time:  time to wait between requests - politeness
    :return:  None
    """
    unique_topics = set()  # set of unique topics URLs to avoid duplicates
    for topic in topics_refs:
        subpage = requests.get('https://theelderscrolls.fandom.com' + topic)  # get the page
        subpage_url = subpage.request.url  # get the URL
        subpage_url = subpage_url.split('#')[0]  # remove the anchor
        if subpage_url in unique_topics:  # if the URL was already visited, skip it
            continue
        unique_topics.add(subpage_url)
        print(subpage_url)
        subtree = html.fromstring(subpage.content)  # parse the page
        try:
            title = subtree.xpath('//span[@class="mw-page-title-main"]/text()')  # get the title
            print(title)

            content = subtree.xpath('string(//div[@class="mw-parser-output"])')  # get the content - full text

            toc = subtree.xpath('string(//div[@class="toc"])')  # get the table of contents

            infobox = subtree.xpath('string(//table[@class="infobox"])')  # get the infobox

            if toc:  # if there is a table of contents
                content = content.replace(toc, '')  # remove it from the content
                toc = toc.split('\n')  # split the table of contents by new line
                toc = list(filter(None, toc))  # remove empty strings from the list

            if infobox:  # if there is an infobox
                content = content.replace(infobox, '')  # remove it from the content
                infobox = infobox.replace('\n', ' ')  # remove new lines
                infobox = ' '.join(infobox.split())  # remove more than 1 space in a row

            content = content.replace('[]', '').replace('↑', '')  # remove some characters - bullet points artefacts

            # remove unnecessary parts of the content
            if 'Zdroje\n' in content:
                content = content.split('Zdroje\n')[0]
            if 'Reference\n' in content:
                content = content.split('Reference\n')[0]
            if 'Reference a poznámky\n' in content:
                content = content.split('Reference a poznámky\n')[0]
            if 'Galerie\n' in content:
                content = content.split('Galerie\n')[0]

            content = content.replace('\n', ' ')  # remove new lines
            content = ' '.join(content.split())  # remove more than 1 space in a row

            json_output = {
                'title': title[0],
                'table_of_contents': toc,
                'infobox': infobox,
                'content': content
            }
            # remove quotes from title, replace / and : with _
            title[0] = title[0].replace('"', '').replace('/', '_').replace(':', '_')

            with open(folder + '/' + title[0] + '.json', 'w', encoding="utf-8") as f:  # save the JSON file
                json.dump(json_output, f, ensure_ascii=False, indent=4)

        except Exception as e:  # if there is an exception, print the error
            print('Error: ' + topic)
            print('Exception: ' + str(e))
        time.sleep(wait_time)  # politeness


def main():
    seed_url = 'https://theelderscrolls.fandom.com/cs/wiki/Speci%C3%A1ln%C3%AD:V%C5%A1echny_str%C3%A1nky?from=%22%C5%A0%C3%ADlenci%22+z+Pl%C3%A1n%C3%AD'
    wait_time = 1  # seconds

    topics_refs = crawl(seed_url, wait_time)  # get the topics references from the website

    # if folder does not exist, create it
    if not os.path.exists('data'):
        os.makedirs('data')

    scrape_urls(topics_refs, folder='data', wait_time=wait_time)  # scrape the URLs and save the content to JSON files


if __name__ == '__main__':
    main()
