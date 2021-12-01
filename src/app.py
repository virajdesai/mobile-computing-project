import tkinter as tk
import pickle
from tkinter import Listbox, ttk
from tkinter import dnd
from tkinter.constants import NW, OUTSIDE
from utils import *


available_services = []
available_things = []

recLine = []

class DragDropListbox(Listbox):
    """ A Tkinter listbox with drag'n'drop reordering of entries. """
    def __init__(self, master, **kw):
        kw['selectmode'] = tk.SINGLE
        Listbox.__init__(self, master, kw)
        self.bind('<Button-1>', self.setCurrent)
        self.bind('<B1-Motion>', self.shiftSelection)
        self.curIndex = None

    def setCurrent(self, event):
        self.curIndex = self.nearest(event.y)

    def shiftSelection(self, event):
        i = self.nearest(event.y)
        if i < self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i+1, x)
            self.curIndex = i
        elif i > self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i-1, x)
            self.curIndex = i
  
class ServiceButton():
    def __init__(self, container, where: DragDropListbox, name):
        self.button = ttk.Button(container, text='Add Service', 
                   command=lambda:where.insert(0, name)).pack()
    #Change TODO
    

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
        recipes = tk.Frame(self, bg='dark grey')
        recipes.grid(row=0, column=1, sticky=tk.NSEW)

        d = DragDropListbox(recipes)
        d.pack()
        d.place(bordermode=OUTSIDE, anchor=NW, height=500, width=250, rely=0.05, relx=0.0025)

        #Textbox for service arguments
        inputtxt = tk.Text(recipes, height=5, width=20).pack(side=tk.LEFT)
        txtRules = tk.Label(recipes, text="Comma for args, SemiColon for func", fg="grey").pack(side=tk.LEFT)

        # Adding some buttons to the recipe view and a title
        ttk.Label(recipes, text ="Recipes: This is where the services are dragged and arranged").pack()
        ttk.Button(recipes, text='Save').pack(side=tk.RIGHT)

        output = tk.Text(recipes, state='disabled', width=44, height=20)
        output.pack()
        
        def clear():
            d.delete(0,tk.END)
            recLine.clear()
            output.configure(state='normal')
            output.delete('1.0', 'end')
            output.configure(state='disabled')

        clr = ttk.Button(recipes, text='Clear', command=clear)
        clr.pack()
        
        
        
        def run():
            for entry in d.get(0, tk.END):
                recLine.append(entry)

            for s in recLine:
                for sobj in available_services:
                    if s == sobj.name:
                        result = sobj.exec([])
                        if sobj.has_output:
                            output.configure(state='normal')
                            output.insert('end', result)
                            output.configure(state='disabled')
                        break
                
        ttk.Button(recipes, text='Run', command=run).pack(side=tk.RIGHT)
        
        # def run():
        #     #implement run function
        # ttk.Button(recipies, text='Run', command=clear).pack(side=tk.RIGHT)

        


        # Buttons and descriptions for services that can be pressed to add them to the 
        # recipe area.
        
        print(len(available_things), len(available_services))
        for s in available_services:
            print(s.name)
            ttk.Label(services, text='Name: ' + s.name).pack()
            ttk.Label(services, text='Thing: ' + s.thing.id).pack()
            ttk.Label(services, text='Smart Space: ' + s.thing.space).pack()
            ServiceButton(services, d, s.name)
            
       
        



if __name__ == "__main__":
    # tweets = [json_to_tweet(t) for t in listen_for_json()]
    # available_things = tweets_to_things(tweets)
    # available_services = tweets_to_services(tweets)

    with open('services.txt', 'rb') as f:
        available_services = pickle.load(f)

    with open('things.txt', 'rb') as f:
        available_things = pickle.load(f)
    
    app = App()
    app.mainloop()
    