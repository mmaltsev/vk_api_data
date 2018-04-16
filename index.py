"""Module for creating a storage of last names by localities fetching from VK."""

import urllib.request
import numpy as np
import scriptdata  # https://gist.github.com/anonymous/2204527
import json
import re
import time


def main():
    """Describe abstract algorithm of the module."""
    vk_people = []
    last_names = {}
    # 483 678 400 accounts registered in VK by 16.04.18 (https://vk.com/catalog.php)
    start_id, end_id, step = 1, 50000, 500
    start_time = time.time()
    for i in range(start_id, end_id, step):
        # data for 500 ids is fetched via one request
        vk_api_data = get_vk_api_data(i)
        for person in vk_api_data:
            if is_eligible(person):
                person_data = get_person_data(person)
                vk_people.append(person_data)
                enrich_last_names(last_names, person_data)
        if (i - 1) % 5000 == 0:
            print('execution time: ', str('{0:.2f}'.format(time.time() - start_time)))
            start_time = time.time()
    save_and_print_logs(vk_people, last_names)


def get_vk_api_data(start):
    """Get VK API data."""
    user_ids = np.ndarray.tolist(np.linspace(start, start + 500, 500))
    user_ids_int = list(map(int, user_ids))
    vk_api_user_ids = list(map(str, user_ids_int))
    vk_api_fields = ['city', 'country', 'home_town']
    vk_api_lang = 'ru'
    vk_api_v = '5.74'
    url = 'https://api.vk.com/method/users.get?user_ids=' + ','.join(vk_api_user_ids) + \
        '&fields=' + ','.join(vk_api_fields) + '&lang=' + vk_api_lang + '&v=' + vk_api_v
    contents = urllib.request.urlopen(url).read()
    vk_data = json.loads(contents.decode())['response']
    return vk_data


def is_eligible(person):
    """Check if eligible person."""
    if person.get('deactivated') != 'deleted':
        last_name = person.get('last_name')
        if last_name and is_cyrillic(last_name):
            country = person.get('country')
            if country:
                return True
    return False


def is_cyrillic(last_name):
    """Check if last_name is cyrillic."""
    return scriptdata.cat(last_name[0]) == ('Cyrillic', 'L')


def get_person_data(person):
    """Get person data."""
    last_name = masculinize(person.get('last_name'))
    first_name = person.get('first_name')
    country_title = person.get('country').get('title')
    city_title = get_city_title(person)
    vk_id = person.get('id')
    person_data = {
        'last_name': last_name,
        'first_name': first_name or '',
        'country': country_title,
        'city': city_title or '',
        'vk_id': vk_id,
    }
    return person_data


def masculinize(last_name):
    """Masculinize last name."""
    r1 = re.compile(r'(о|е|ё)ва$')
    r2 = re.compile(r'ина$')
    r3 = re.compile(r'ая$')
    if r1.search(last_name) or r2.search(last_name):
        last_name = last_name[:-1]
    if r3.search(last_name):
        last_name = last_name[:-2] + 'ий'
    return last_name


def get_city_title(person):
    """Get city title."""
    city_title = ''
    home_town = person.get('home_town')
    if not home_town:
        city = person.get('city')
        if city:
            city_title = city.get('title')
    else:
        city_title = home_town
    return city_title


def enrich_last_names(last_names, person_data):
    """Enrich last names."""
    last_name = person_data['last_name']
    if last_name not in last_names:
        last_names[last_name] = {}
        last_names[last_name]['total'] = 0
    person_city = person_data['city']
    person_country = person_data['country']
    if person_city not in last_names[last_name]:
        last_names[last_name][person_city] = 0
    if person_country not in last_names[last_name]:
        last_names[last_name][person_country] = 0
    last_names[last_name][person_city] += 1
    last_names[last_name][person_country] += 1
    last_names[last_name]['total'] += 1


def save_as_txt(contents, filename):
    """Save as txt file."""
    with open(filename, 'w') as text_file:
        text_file.write(str(contents))


def save_and_print_logs(vk_people, last_names):
    """Save and print logs."""
    save_as_txt(vk_people, 'vk_people.txt')
    save_as_txt(last_names, 'last_names.txt')
    sorted_last_names = sort_last_names(last_names)
    save_as_txt(sorted_last_names, 'sorted_last_names.txt')
    print('Overall analyzed ' + str(len(last_names)) + ' family names.')


def sort_last_names(last_names):
    """Sort last names by popularity."""
    cleaned_last_names = {(k, v['total']) for k, v in last_names.items()}
    sorted_last_names = sorted(cleaned_last_names, key=lambda tup: tup[1], reverse=True)
    return sorted_last_names


if __name__ == "__main__":
    main()
