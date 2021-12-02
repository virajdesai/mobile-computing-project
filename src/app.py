import tkinter as tk
import pickle
from tkinter import ttk
from utils import *
from tkinter import simpledialog
import os
import shutil

available_services = []
available_things = []
enabled_services = []

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

    def getCurrent(self):
        return self.curIndex
       

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
        self.frame = ttk.Frame(master, padding=[5,5,5,5], relief="groove")
        
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
    def __init__(self, master, thing: Thing, service_frame, program: DragDropListbox):
        self.frame = ttk.Frame(master, padding=[5,10,5,10], relief="groove")
        self.frame.pack()
        self.enabled = False
        self.name = thing.id
        self.service_frame = service_frame
        self.program = program

        ttk.Label(self.frame, text='Thing: ' + thing.id).pack()
        ttk.Label(self.frame, text='Space: ' + thing.space).pack()
        ttk.Label(self.frame, text='IP Adress: ' + thing.address).pack()
        ttk.Checkbutton(master, text='Show Services', variable=self.enabled, onvalue=1, offvalue=0, command=self.toggle).pack()

    def clear_frame(self):
        for widget in self.service_frame.winfo_children():
            widget.destroy()
    
    def toggle(self):
        self.enabled = not self.enabled
        self.clear_frame()
        if self.enabled:
            for service in available_services:
                if service.thing.id == self.name:
                    enabled_services.append(service)
            for s in enabled_services:
                ServiceInfo(self.service_frame, self.program, s)
        else:
            for service in available_services:
                if service.thing.id == self.name:
                    enabled_services.remove(service)
            

class RelationshipInfo():
    def __init__(self, master, program: DragDropListbox, name):
        self.frame = ttk.Frame(master, padding=[5,10,5,10], relief="groove")
        self.frame.pack()
        self.name = name
        self.program = program

        ttk.Label(self.frame, text=name).pack()

        self.input = tk.StringVar()

        if self.name == 'Control':
            EntryWithPlaceholder(self.frame, f'Condition (ex. x > 30)', textvariable=self.input).pack(fill='x', expand=True) 

        ttk.Button(self.frame, text='+', command=self.add_to_recipe).pack()

       

    def add_to_recipe(self):
        if self.name == 'Control':
            self.program.insert(tk.END, f'Relationship: Control({self.input.get()})', '   Service A', '   Service B')
        else:
            self.program.insert(tk.END, "Relationship: " + self.name, '   Service A', '   Service B')


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
        self.program.place(bordermode=tk.OUTSIDE, anchor=tk.NW, height=500, width=250, rely=0.05, relx=0.025)
        self.execution = []

        # Adding some buttons to the recipe view and a title
        ttk.Label(recipes, text='Recipes').pack(anchor='w', pady=6, padx=120)
        
        ttk.Label(recipes, text='Console Log').pack(anchor='e', padx=240, pady=6)
        
        self.output = tk.Text(recipes, state='disabled', width=44, height=20)
        self.output.pack(anchor='e', padx = 100)

        self.app_list = {}

        def save_to_app_list():
            app_name = simpledialog.askstring("Input", "Application Name", parent=self)
            if app_name in self.app_list:
                self.log(f'Project named {app_name} already exists!')
                return
            self.app_list[app_name] = self.program.get(0, tk.END)
            app_box.insert(tk.END, app_name)

        #buttons for recipe box
<<<<<<< HEAD
        
        ttk.Button(recipes, text='Clear', command=self.clear).pack(anchor='e', padx = 240, pady=6)
        ttk.Button(recipes, text='Remove', command=self.program.remove).pack(anchor='e', padx = 240, pady=6)
        ttk.Button(recipes, text='Run', command=self.run).pack(anchor='e', padx = 240, pady=6)
        ttk.Button(recipes, text='Build', command=save_to_app_list).pack(anchor='e', padx = 240, pady=6)
=======
        ttk.Button(recipes, text='Clear', command=self.clear).pack(anchor='e', padx = 240, pady=6)
        ttk.Button(recipes, text='Remove', command=self.program.remove).pack(anchor='e', padx = 240, pady=6)
        ttk.Button(recipes, text='Run', command=self.run).pack(anchor='e', padx = 240, pady=6)
        ttk.Button(recipes, text='Save', command=save_to_app_list).pack(anchor='e', padx = 240, pady=6)
>>>>>>> 0692b89f0465c2a8dbd80d894065d10008567dcf


        #Create information boxes for each Tab

        # for s in available_services:
        #     ServiceInfo(services, self.program, s)

        for t in available_things:
            ThingInfo(things, t, services, self.program)
        


        # APP FRAME

        app_box = DragDropListbox(apps)
        app_box.pack()

        def activate():
            cursor = app_box.getCurrent()
            if cursor == None:
                return
            name = app_box.get(cursor, cursor)
            self.clear()
            for action in self.app_list[name[0]]:
                self.program.insert(tk.END, action)
        ttk.Button(apps, text='Load', command=activate).pack()

        def save_to_file():
            cursor = app_box.getCurrent()
            if cursor == None:
                return
            name = app_box.get(cursor, cursor)[0]
            try:
                os.makedirs(os.path.join(os.getcwd(), 'saves/' + name))
            except:
                self.log(f'Updating IoT Application {name}')
            with open('saves/'+name+'/services', 'wb') as f:
                pickle.dump(available_services, f)
            with open('saves/'+name+'/program', 'w') as f:
                f.write('\n'.join(self.app_list[name]))
            self.log(f'Saved {name} to {os.getcwd()}/saves/{name}.')
        ttk.Button(apps, text='Save', command=save_to_file).pack()


        def delete():
            cursor = app_box.getCurrent()
            if cursor == None:
                return
            name = app_box.get(cursor, cursor)[0]
            self.app_list.pop(name)
            app_box.delete(cursor)
            try:
                shutil.rmtree('./saves/' + name)
                self.log(f'Removed {name} from saves.')
            except:
                self.log(f'{name} was removed from App Manager List')
                

        ttk.Button(apps, text='Delete', command=delete).pack()

        def upload():
            for _, subdirectories, _ in os.walk('./saves'):
                for proj in subdirectories:
                    with open(os.path.join(os.getcwd(), 'saves/'+proj+'/services'), 'rb') as f:
                        for service in pickle.load(f):
                            available_services.append(service)
                    with open(os.path.join(os.getcwd(), 'saves/'+proj+'/program'), 'r') as f:
                        actions = f.readlines()
                    self.app_list[proj] = actions
                    app_box.insert(tk.END, proj)

        upload()




        #pos
        RelationshipInfo(relationships, self.program, "Drive")
        RelationshipInfo(relationships, self.program, "Control")
        RelationshipInfo(relationships, self.program, "Support")
        RelationshipInfo(relationships, self.program, "Extend")

        #comp
        RelationshipInfo(relationships, self.program, "Interfere")
        RelationshipInfo(relationships, self.program, "Contest")
        RelationshipInfo(relationships, self.program, "Refine")
        RelationshipInfo(relationships, self.program, "Subsume")


    

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
        self.output.insert('end', line+'\n')
        self.output.configure(state='disabled')
        

    def run(self):
        self.output.configure(state='normal')
        self.output.delete('1.0', 'end')
        self.output.configure(state='disabled')

        services = {s.name:s for s in available_services}
        blacklist = []

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


                #Cooperative
                if 'Relationship: Drive' in action:
                    if len(args_b) != 0: 
                        self.log('Service B cannot take input with "Drives" relationship')
                        return
                    Relationship.Cooperative.Drive(service_a, service_b).exec(args_a)

                if 'Relationship: Support' in action:
                    Relationship.Cooperative.Support(service_a, service_b).exec(args_a, args_b)

                if 'Relationship: Extend' in action:
                    
                    Relationship.Cooperative.Extend(service_a, service_b).exec(args_a+args_b)
                
                if 'Relationship: Control' in action:
                    condition = action[action.find('(')+1:action.find(')')].replace(' ','')
                    if condition[0] != 'x':
                        self.log("expecting x variable for boolean expression")
                        return
                    if condition[1] not in ('>', '<', '='):
                        self.log("expecting comparison for condition (ex. >, <, =)")
                        return
                    if not condition[2:].isnumeric():
                        self.log("expecting integer value for comparison")
                        return
                    if not service_a.has_output:
                        self.log('Service A must output a value for the "Control" relationship')
                    a = int(condition[2:])
                    if condition[1] == '>':
                        c = lambda x: int(x) > a
                    if condition[1] == '<':
                        c = lambda x: int(x) < a
                    if condition[1] == '=':
                        c = lambda x: int(x) == a

                    Relationship.Cooperative.Control(service_a, service_b).exec(args_a, args_b, c)
                
                #Competitive
                if 'Relationship: Interfere' in action or 'Relationship: Contest' in action:
                    blacklist.append(service_a.name)
                    blacklist.append(service_b.name)

                if 'Relationship: Refine' in action:
                    services[service_b.name] = services[service_a.name]
                
                if 'Relationship: Subsume' in action:
                    services[service_a.name] = services[service_b.name]
                
                i += 2
            else:
                v = self.parse_service(action, services)
                if v != None:
                    (service, args) = v
                if service.name in blacklist:
                    if len(blacklist) == 2:
                        blacklist.remove(service.name)
                    elif  len(blacklist) == 1:
                        self.log(f'Service {service.name} is interfered or contested with.')
                        return
                    
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
    