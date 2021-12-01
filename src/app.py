import tkinter as tk
import pickle
from tkinter import ttk
from utils import *


available_services = []
available_things = []

execute = []

class DragDropListbox(tk.Listbox):
    def __init__(self, master, **kw):
        kw['selectmode'] = tk.SINGLE
        tk.Listbox.__init__(self, master, kw)
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

    def remove(self):
        if self.curIndex != None:
            self.delete(self.curIndex, self.curIndex)
       

class EntryWithPlaceholder(tk.Entry):
    def __init__(self, master, placeholder="PLACEHOLDER", **kw):
        super().__init__(master, kw)

        self.placeholder = placeholder
        self.placeholder_color = 'grey'
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()
  
class ServiceInfo():
    def __init__(self, master, program: DragDropListbox, service: Service):
        self.program = program
        self.service = service
        self.frame = ttk.Frame(master)
        
        ttk.Label(self.frame, text='Service: ' + service.name.capitalize()).pack()
        ttk.Label(self.frame, text='Provider: ' + service.thing.id).pack()
        self.frame.pack()

        self.inputs = [tk.StringVar() for _ in range(service.argc)]

        for i, input in enumerate(self.inputs):
            EntryWithPlaceholder(self.frame, f'Input #{i+1}', textvariable=input).pack(fill='x', expand=True) 
        
        ttk.Button(self.frame, text='+', command=self.add_to_recipe).pack()

    def add_to_recipe(self):
        inputs = [input.get() for input in self.inputs if input.get().isnumeric()]
        args = '(' + ', '.join(inputs) + ')' if len(inputs) == self.service.argc and len(inputs) != 0 else ''
        self.program.insert(tk.END, self.service.name.capitalize() + args)


class ThingInfo():
    def __init__(self, master, thing: Thing):
        self.frame = ttk.Frame(master)
        self.frame.pack()
        self.enabled = False
        ttk.Label(self.frame, text='Thing: ' + thing.id).pack()
        ttk.Label(self.frame, text='Space: ' + thing.space).pack()
        ttk.Label(self.frame, text='IP Adress: ' + thing.address).pack()
        ttk.Checkbutton(master, text='Show Services', variable=self.enabled, onvalue=1, offvalue=0, command=self.toggle).pack()

    def toggle(self):
        self.enabled = not self.enabled
        print('Checked', self.enabled)

class RelationshipInfo():
    def __init__(self, master, program: DragDropListbox, name):
        self.frame = ttk.Frame(master)
        self.frame.pack()
        self.name = name
        self.program = program

        ttk.Label(self.frame, text="Relationship: " + name).pack()
        ttk.Button(self.frame, text='+', command=self.add_to_recipe).pack()

    def add_to_recipe(self):
        self.program.insert(tk.END, self.name, 'Service A', 'Service B')


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

        self.program = DragDropListbox(recipes)
        self.program.pack()
        self.program.place(bordermode=tk.OUTSIDE, anchor=tk.NW, height=500, width=250, rely=0.05, relx=0.0025)
        self.execution = []

        # Adding some buttons to the recipe view and a title
        ttk.Label(recipes, text='Recipes').pack()

        self.output = tk.Text(recipes, state='disabled', width=44, height=20)
        self.output.pack()

        #buttons for recipe box
        ttk.Button(recipes, text='Clear', command=self.clear).pack()
        ttk.Button(recipes, text='Remove', command=self.program.remove).pack()
        ttk.Button(recipes, text='Run', command=self.run).pack()
        ttk.Button(recipes, text='Save').pack()      


        #Create information boxes for each Tab
        for s in available_services:
            ServiceInfo(services, self.program, s)

        for t in available_things:
            ThingInfo(things, t)

        RelationshipInfo(relationships, self.program, "Relationship: Drive")

    def clear(self):
            self.program.delete(0,tk.END)

    def parse_service(self, action: str, services):
        x = action.find('(')
        if x > 0:
            name = action[:x].lower()
            args = [int(arg) for arg in action[x+1:-1].split(', ')]
        else:
            name = action.lower()
            args = []

        return (services[name], args) if name in services else None

    def log(self, line: str):
        self.output.configure(state='normal')
        self.output.insert('end', line)
        self.output.configure(state='disabled')
        

    def run(self):
        self.output.configure(state='normal')
        self.output.delete('1.0', 'end')
        self.output.configure(state='disabled')

        services = {s.name:s for s in available_services}

        listing = self.program.get(0, tk.END)
        i = 0
        while (i < len(listing)):
            print("Entered wile looop")
            action = listing[i]
            print("here + i: " +  str(i))
            # see Relationship: 
            if 'Relationship: ' in action:
                if i+2 >= len(listing):
                    print('err')
                    return
                
                v = self.parse_service(listing[i+1], services)
                if v != None:
                    (service_a, args_a) = v

                v = self.parse_service(listing[i+2], services)
                if v != None:
                    (service_b, args_b) = v

                if 'Relationship: Drive' in action:
                    if len(args_b) != 0: 
                        self.log('Service B cannot take input with "Drives" relationship')
                        return
                    Relationship.Cooperative.Drive(service_a, service_b).exec(args_a)

                i += 2
            else:
                v = self.parse_service(action, services)
                if v != None:
                    (service, args) = v
                result = service.exec(args)
                if service.has_output:
                    self.log(result)
            
            i += 1
                

            
            
            
            # get the name of the RElationship
            #construc the R
            # skip over two lines in the listbox and grab those two as ser a and b
            # exec this line:
            

    
            

        

                    
            
       
        



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
    