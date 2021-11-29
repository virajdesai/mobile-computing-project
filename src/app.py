import tkinter as tk
from tkinter import ttk
from tkinter import dnd


class ServiceButton():
    def __init__(self, container, where, name):
        ttk.Button(container, text='Add Service', 
                   command=lambda: Draggable(name).attach(where.canvas)).pack()


class Reciever:
    def __init__(self, root, id):
        self.top = root
        self.canvas = tk.Canvas(self.top, width=200, height=100)
        self.canvas.pack()
        self.canvas.dnd_accept = self.dnd_accept
        self.id = id
        self.contains = 0

    def dnd_accept(self, source, event):
        return self

    def dnd_enter(self, source, event):
        self.canvas.focus_set() # Show highlight border
        x, y = source.where(self.canvas, event)
        x1, y1, x2, y2 = source.canvas.bbox(source.id)
        dx, dy = x2-x1, y2-y1
        self.dndid = self.canvas.create_rectangle(x, y, x+dx, y+dy)
        self.dnd_motion(source, event)

    def dnd_motion(self, source, event):
        x, y = source.where(self.canvas, event)
        x1, y1, x2, y2 = self.canvas.bbox(self.dndid)
        self.canvas.move(self.dndid, x-x1, y-y1)

    def dnd_leave(self, source, event):
        self.top.focus_set() # Hide highlight border
        self.canvas.delete(self.dndid)
        self.dndid = None

    def dnd_commit(self, source, event):
        self.dnd_leave(source, event)
        x, y = source.where(self.canvas, event)
        source.attach(self.canvas, x, y)
        self.contains += 1
        print("Block is in Receiver #" + str(self.id) + ' which now contains ' + str(self.contains) + ' block(s).')


class Draggable:
    def __init__(self, name):
        self.name = name
        self.canvas = self.label = self.id = None

    def attach(self, canvas, x=10, y=10):
        if canvas is self.canvas:
            self.canvas.coords(self.id, x, y)
            return
        if self.canvas is not None:
            self.detach()
        if canvas is None:
            return
        label = tk.Label(canvas, text=self.name,
                              borderwidth=2, relief="groove")
        id = canvas.create_window(x, y, window=label, anchor="nw")
        self.canvas = canvas
        self.label = label
        self.id = id
        label.bind("<ButtonPress>", self.press)

    def detach(self):
        canvas = self.canvas
        if canvas is None:
            return
        id = self.id
        label = self.label
        self.canvas = self.label = self.id = None
        canvas.delete(id)
        label.destroy()

    def press(self, event):
        if dnd.dnd_start(self, event):
            # where the pointer is relative to the label widget:
            self.x_off = event.x
            self.y_off = event.y
            # where the widget is relative to the canvas:
            self.x_orig, self.y_orig = self.canvas.coords(self.id)

    def move(self, event):
        x, y = self.where(self.canvas, event)
        self.canvas.coords(self.id, x, y)

    def putback(self):
        self.canvas.coords(self.id, self.x_orig, self.y_orig)

    def where(self, canvas, event):
        # where the corner of the canvas is relative to the screen:
        x_org = canvas.winfo_rootx()
        y_org = canvas.winfo_rooty()
        # where the pointer is relative to the canvas widget:
        x = event.x_root - x_org
        y = event.y_root - y_org
        # compensate for initial pointer offset
        return x - self.x_off, y - self.y_off

    def dnd_end(self, target, event):
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # configure the root window
        self.title('Atlas IoT IDE')
        self.geometry('1200x600')

        # splits the window into two columns with the second one
        # being twice the size of the first given by the weight
        self.columnconfigure(0, weight=1, uniform=tk.X)
        self.columnconfigure(1, weight=2, uniform=tk.X)
        self.rowconfigure(0, weight=1)

        # Information tab group
        # colomn 0 is the smaller one aligned left
        info = ttk.Notebook(self)
        info.grid(row=0, column=0, sticky=tk.NSEW)

        # These are the frames that are in the tab group that we
        # can fill with information from the devices
        # ideally we'll have functions/classes that fill the frames
        # instead of doing it all in this class so we can work on diff parts
        things = ttk.Frame(info)
        services = ttk.Frame(info)
        relationships = ttk.Frame(info)
        apps = ttk.Frame(info)

        # Adding the frames to the tab group
        info.add(things, text='Things')
        info.add(services, text='Services')
        info.add(relationships, text='Relationships')
        info.add(apps, text='Apps')
        
        # Recipe editor / just a blank frame aligned left
        recipies = tk.Frame(self, bg='pink')
        recipies.grid(row=0, column=1, sticky=tk.NSEW)

        # Adding some buttons to the recipe view and a title
        ttk.Label(recipies, text ="Recipes: This is where the services are dragged and arranged").pack()
        ttk.Button(recipies, text='Save').pack(side=tk.RIGHT)
        ttk.Button(recipies, text='Clear').pack(side=tk.RIGHT)

        # Makes 4 places to add 'code blocks' to
        areas = [Reciever(recipies, i) for i in range(4)]

        # Buttons and descriptions for services that can be pressed to add them to the 
        # recipe area.
        thing_name = 'RaspberryPi 4'
        space_name = 'My Virtual Smart Space 1'

        ttk.Label(services, text='Turn on Light').pack()
        ttk.Label(services, text=thing_name).pack()
        ttk.Label(services, text=space_name).pack()
        ServiceButton(services, areas[0], 'Turn on Light')

        ttk.Label(services, text='Turn off Light').pack()
        ttk.Label(services, text=thing_name).pack()
        ttk.Label(services, text=space_name).pack()
        ServiceButton(services, areas[0], 'Turn off Light')


if __name__ == "__main__":
    app = App()
    app.mainloop()