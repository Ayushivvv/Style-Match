"""
...
"""

import random
from tkinter import Tk, Entry, Toplevel, Label, Frame, Button, TOP, LEFT, RIGHT, filedialog, PhotoImage
import urllib.request
import urllib.error
import webbrowser
from PIL import ImageTk
import graph as g
import image_to_text as f


class StyleMatch:
    """ When given a dataset, program will create a python interface where users can either upload their own images
    or search few words to find similar items/styles in the coresponding datasbase. Program will display top 5
    similar items and provide options for user to explore further items or can be connected to a website showing
    further details about it.

    Instance Attributes:
    - graph: A weighted graph whose vertex all represent items from our database.
    - window: The screen our data will be displayed on using tkinter
    - items: Represents a list of all the weighted vertexes from our weighted graph
    - dataset: A string linking to the dataset we are pulling information from
    """
    graph: g.WeightedGraph
    window: Tk
    items: list[g.WeightedVertex]
    dataset: str

    widgets: dict[int, list]

    def __init__(self, dataset: str) -> None:
        """Initialize variables, create/display a window, and starts our application."""
        self.graph = g.load_clothing_items(dataset)
        self.dataset = dataset

        # initialize items to be a list of 5 random vertices
        self.items = random.sample(list(self.graph.vertices.values()), 5)

        # create window and widgets
        self.window = Tk()
        self.window.geometry("1000x700")
        self.window.title("Style Match")

        # create title widgets
        title_frame = Frame(self.window, pady=20)

        title_label = Label(title_frame, text="Style Match", font=("Arial", 40, "bold"))
        title_label.pack(side=TOP)

        instructions = Label(title_frame, text="Select an Image to Find Similar Style Clothes or Search for Keywords."
                                               "\nClick on an Image to View Details About the Item.")
        instructions.pack(side=TOP)

        button = Button(title_frame, text="Choose Image", command=self.browse)
        button.pack(side=TOP)

        search_frame = Frame(title_frame)
        search_bar = Entry(search_frame)
        search_bar.pack(side=LEFT)
        button = Button(search_frame, text="Search",
                        command=lambda: self.find_similar_from_desc(search_bar.get()))
        button.pack(side=RIGHT)
        search_frame.pack(side=TOP)

        title_frame.pack(side=TOP)

        # create widgets to display clothing items
        image_display_frame = Frame(self.window, pady=20)
        self.widgets = {}
        for i in range(5):
            frame = Frame(image_display_frame, pady=20)

            image_label = Button(frame, text="Missing Image", padx=10, pady=20, height=240, width=200, borderwidth=0,
                                 activebackground="#D3D3D3",
                                 command=lambda x=self.items[i]: self.display_item_popup(x))
            image_label.pack(side=TOP)

            name_label = Label(frame, wraplength=200)
            name_label.pack(side=TOP)

            web_button = Button(frame, text="website")
            web_button.pack(side=TOP)

            sim_button = Button(frame, text="find similar")
            sim_button.pack(side=TOP)

            frame.pack(side=LEFT)
            self.widgets[i] = [image_label, name_label, web_button, sim_button]

        image_display_frame.pack(side=TOP)
        self.update_labels()
        self.window.mainloop()

    def display_item_popup(self, item: g.WeightedVertex) -> None:
        """Create a popup window displaying the info for the given weighted vertex cloting item."""
        popup = Toplevel()

        name_label = Label(popup, text=item.item_name, font=('Arial', 15, 'bold'))
        price_label = Label(popup, text="$" + str(item.price) + " (USD)")
        desc_label = Label(popup, text=item.item_description, pady=5, wraplength=1000)
        image_frame = Frame(popup)
        row_frame = Frame(image_frame)
        for i in range(len(item.urls)):
            if i % 5 == 0 and i != 0:
                row_frame.pack(side=TOP)
                row_frame = Frame(image_frame)
            image = self.image_from_url(item.urls[i])
            if image:
                image_label = Label(row_frame, image=image)
                image_label.image = image
                image_label.pack(side=LEFT)
        row_frame.pack(side=TOP)

        name_label.pack(side=TOP)
        price_label.pack(side=TOP)
        desc_label.pack(side=TOP)
        image_frame.pack(side=TOP)

    def browse(self) -> None:
        """Try to get the file path of the selected file and find the similar images of the selected file
        if successful. Otherwise, do nothing."""
        try:
            file_path = filedialog.askopenfilename(filetypes=(('JPG Image', '.jpg'),
                                                              ('PNG Image', '.png'),
                                                              ('All Image Files', '.jpg .png')))
        except FileNotFoundError:
            pass
        else:
            # check if file path is valid
            if file_path == "":
                return
            self.find_similar_from_image(file_path)

    def open_url(self, url: str) -> None:
        """Opens the given url in a new tab in the default browser."""
        webbrowser.open_new_tab(url)

    def find_similar_from_desc(self, item_description: str) -> None:
        """Update items to be a list of the clothing items most similar to the given item_description
        as Weighted Vertices."""

        # create graph and new vertex
        self.graph = g.load_clothing_items(self.dataset)
        user_vertex = self.graph.create_clothing_item(item_description)

        # create edges
        for vertex in self.graph.vertices:
            g.create_edge(self.graph, user_vertex.item_id, self.graph.vertices[vertex].item_id)

        # get top 5 similar items and update items and labels
        self.items = user_vertex.get_ordered_neighbours()[:5]
        self.update_labels()

    def find_similar_from_image(self, file_location: str) -> None:
        """Update items to be a list of the clothing items most similar to the photo with the given file_location
        as Weighted Vertices."""

        photo_description = f.user_image_description(file_location)
        self.find_similar_from_desc(photo_description)

    def update_labels(self) -> None:
        """Update labels in window based on current clothing items in items list."""
        for i in range(len(self.items)):

            # update image
            image = self.image_from_url(self.items[i].urls[1])
            self.widgets[i][0].config(image=image, command=lambda x=self.items[i]: self.display_item_popup(x))
            self.widgets[i][0].image = image

            # update name
            self.widgets[i][1].config(text=self.items[i].item_name)

            # update website url
            self.widgets[i][2].config(command=lambda url=self.items[i].website: self.open_url(url))

            # update find similar button
            self.widgets[i][3].config(
                command=lambda desc=self.items[i].item_description: self.find_similar_from_desc(desc))

    def image_from_url(self, url: str) -> PhotoImage | None:
        """Return the photo with the given url as a resized PhotoImage."""

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as file:
                data = file.read()
                image = ImageTk.PhotoImage(data=data)
        except (ValueError, urllib.error.URLError) as _:
            return None
        else:
            return self.resize_image(image, 200, 200)

    def resize_image(self, image: PhotoImage, max_height: int, max_width: int) -> PhotoImage:
        """Resizes the given image while maintaining aspect ratio and making sure the height and width
        do not exceed the max height and width. A PhotoImage is returned."""

        # convert to PhotoImage to Image
        image = ImageTk.getimage(image)

        # calculate new dimensions
        aspect_ratio = image.width / image.height

        if aspect_ratio > 1:  # wider
            new_width = max_width
            new_height = new_width / aspect_ratio
        else:
            new_height = max_height
            new_width = max_height * aspect_ratio

        # resize
        image = image.resize((int(new_width), int(new_height)))

        # convert Image to PhotoImage and return
        return ImageTk.PhotoImage(image)


if __name__ == "__main__":

    # Start application
    app = StyleMatch("data/store_zara_small_women.csv")

    import doctest

    doctest.testmod(verbose=True)

    import python_ta

    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': ['E1136', 'W0221'],
        'max-nested-blocks': 4
    })
