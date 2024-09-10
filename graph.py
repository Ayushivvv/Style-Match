"""
===============================
Style Match
===============================
...
"""

from __future__ import annotations
import uuid
import csv
from typing import Any
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet


class WeightedVertex:
    """A weighted vertex."""
    item_id: str
    item_name: str
    item_description: str
    price: float
    urls: list[str]
    neighbours: dict[WeightedVertex, float]
    website: str

    def __init__(self, item_id: str, item_name: str, item_description: str, price: float,
                 urls: list[str], website: str) -> None:
        """Initialize a new vertex with the given item."""
        self.item_id = item_id
        self.item_name = item_name
        self.item_description = item_description
        self.price = price
        self.urls = urls
        self.neighbours = {}
        self.website = website

    def get_ordered_neighbours(self) -> list[WeightedVertex]:
        """Returns a list of the neighbours ordered by decreasing weights"""

        n = dict(sorted(self.neighbours.items(), key=lambda i: -i[1]))
        return list(n.keys())

    def load_vertex_image(self) -> list[str]:
        """Returns urls of the given colthing item"""
        return self.urls


class WeightedGraph:
    """A weighted graph."""

    vertices: dict[str, WeightedVertex]

    def __init__(self) -> None:
        """Initialize an empty graph (no vertices or edges)."""
        self.vertices = {}

    def add_vertex(self, item_id: str, item_name: str, item_description: str,
                   price: float, urls: list[str], website: str) -> None:
        """
        Add a vertex with the given parameters to this graph.
        The new vertex is not adjacent to any other vertices.
        Do nothing if the given item is already in this graph.
        """
        if item_id not in self.vertices:
            self.vertices[item_id] = WeightedVertex(item_id, item_name, item_description, price, urls, website)

    def add_edge(self, item_id1: Any, item_id2: Any, weight: float = 1) -> None:
        """Add an edge between the two vertices with the given item_ids in this graph,
        with the given weight.

        Raise a ValueError if item1 or item2 do not appear as vertices in this graph.

        Preconditions:
            - item1 != item2
        """

        # check if both vertices exist
        if item_id1 in self.vertices and item_id2 in self.vertices:
            v1 = self.vertices[item_id1]
            v2 = self.vertices[item_id2]

            # Add the new edge
            v1.neighbours[v2] = weight
            v2.neighbours[v1] = weight
        else:
            raise ValueError

    def get_neighbours(self, item_id: str) -> list[WeightedVertex]:
        """Returns the neighbours of the vertex with the given id ordered by decreasing weight."""
        return self.vertices[item_id].get_ordered_neighbours()

    def create_clothing_item(self, item_description: str) -> WeightedVertex:
        """Add new vertex with given parameters to the weighted graph and calculate its neighbours
        and return its item_id"""

        item_id = str(uuid.uuid4())  # generate random id
        v = WeightedVertex(item_id, "", item_description, 0, [], '')
        self.vertices[item_id] = v

        for other_id in self.vertices:
            create_edge(self, item_id, other_id)

        return v


def load_clothing_items(clothing_items_file: str) -> WeightedGraph:
    """Create a weighted graph containing each clothing item from the file as vertices."""

    g = WeightedGraph()

    with open(clothing_items_file) as file:
        reader = csv.reader(file)
        for line in reader:

            # skip headers
            if line[0] == "brand":
                continue

            # create vertex for each clothing item
            urls = str_to_list(line[7])
            g.add_vertex(line[2], line[3], line[4], float(line[5]), urls, line[1])

    return g


def create_edge(g: WeightedGraph, id1: str, id2: str) -> None:
    """Check the similarity of the vertices with the given ids
    and add an edge if the score passes a certain threshold.

    No edge is added if the ids are identical."""

    if id1 == id2:
        return

    v1 = g.vertices[id1]
    v2 = g.vertices[id2]

    # calculate similarity score of two vertices
    if v1.item_name == '':
        score = get_similarity_score(v1.item_description, v2.item_description + v2.item_name)
    elif v2.item_name == '':
        score = get_similarity_score(v1.item_description + v1.item_name, v2.item_description)
    else:
        score = get_similarity_score(v1.item_description, v2.item_description)

    # add edge
    g.add_edge(v1.item_id, v2.item_id, score)


def get_similarity_score(user_desc: str, item_desc: str) -> float:
    """Return the similarity score between the two given texts.
    The similarity score is calculated as so:
    The synonyms for each generated image description (from the user's image) are generated
    Then item_desc is generated """

    colours = ['black', 'white', 'gold', 'silver', 'blue', 'red', 'orange', 'yellow', 'green', 'purple', 'pink',
               'brown', 'tan', 'beige']
    clothes = ['shirt', 'short', 'skirt', 'dress', 'jacket', 'pants', 'leggings', 'jeans', 'top', 'bottom', 'sweater',
               'crop top', 'vest', 'underwear', 'shorts', 'sneakers', 'shoes']

    # dataset description
    zara_txt = filter_out_data(item_desc)

    score = 0

    for word in zara_txt:
        if str.lower(word) in user_desc:
            if word in colours:
                score += 500
            if word in clothes:
                score += 1000
            score += 100

    if len(zara_txt) > 0:
        return score / len(zara_txt)
    else:
        return 0


def str_to_list(text: str) -> list[str]:
    """Takes in a string representation of a list of strings and converts them into a list of strings."""

    lst = text[1:-1].split(", ")         # remove brackets and split by comma
    for i in range(len(lst)):
        lst[i] = lst[i][1:-1]            # remove quotations

    return lst


def synonym_extractor(phrase: str) -> list[str]:
    """Returns a dictionary of synoymns.
    Maps keyword to its given synonyms
    Utilizes nltk library. """

    word_lst = []

    for word in phrase:
        word_lst.append(word)
        if word in ['black', 'white', 'blue', 'pink', 'purple', 'yellow', 'red', 'orange', 'green', 'gold', 'silver']:
            word_lst.append(word)
            continue
        s = []
        for syn in wordnet.synsets(word):
            for lem in syn.lemmas():
                s.append(lem.name())
        word_lst.extend(s)

    return word_lst


def filter_out_user(user_description: str) -> list:
    """Filtering out 'stopwords' for the user description
    - aka words that are not important to the clothing item's description
    """
    clothes = ['shirt', 'short', 'skirt', 'dress', 'jacket', 'pants', 'leggings', 'jeans', 'top', 'bottom', 'sweater',
               'crop top', 'vest', 'underwear', 'shorts', 'sneakers', 'shoes']

    word_tokens = word_tokenize(user_description)
    stop_words = set(stopwords.words('english'))

    filtered_sentence = []

    for w in word_tokens:
        if w not in stop_words:
            filtered_sentence.append(w)

    clothes_in_description = []
    for things in filtered_sentence:
        if things in clothes:
            clothes_in_description.append(things)

    tags = nltk.pos_tag(filtered_sentence)
    adjectives = [word for word, t in tags if t == 'JJ']
    return adjectives + clothes_in_description


def filter_out_data(item_desc: str) -> list:
    """Filtering out 'stopwords' for the given zara clothing item
    - aka words that are not important to the clothing item's description
    """

    # JUST FOR THE ZARA DESCRIPTION
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(item_desc)

    filtered_sentence = []

    for w in word_tokens:
        if w not in stop_words:
            filtered_sentence.append(w)

    return filtered_sentence
