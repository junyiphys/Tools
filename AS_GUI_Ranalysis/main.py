'''GUI for the Resistance data output
202405 Modified by Junyi Tsai@ Academia Sinica

Intro
It's an easy script to analyze the resistance from various source, which is easy to optimize.

The output file style can also be optimize, but already selected a certian theme. 
The only global function: df

TODO: select I or T function
TODO: plot decoration
TODO: save all plots at one click

Essential package to install with the following commend:

pip3 install pandas pandastable matplotlib scikit-learn numpy
conda install pandas pandastable matplotlib scikit-learn numpy
'''

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import pandas as pd
from pandastable import Table
import re
from os.path import splitext, basename, dirname, realpath

#plot functions
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from subprocess import Popen


from sklearn.linear_model import LinearRegression
import numpy as np
def calculate_R(x, y):
    #IV curve calculation
    #define predictor and response variables
    x = np.reshape(x, (-1, 1))
    #fit regression model
    model = LinearRegression()
    model.fit(x, y)
    Res = model.coef_ #resistance 
    R_dev = model.score(x, y) #calculate R-squared of regression model
    return Res, R_dev

import matplotlib.pyplot as plt


class PlotApp:
    def __init__(self, master, df):
        self.master=master
        self.df_data = df
        self.window = tk.Toplevel(parent=None)
        self.window.title("Plot Window")

        # Create a figure and plot
        self.fig = Figure(figsize=(6, 4), dpi=150)
        self.ax = self.fig.add_subplot(111)

        # Create a canvas to display the plot
        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        canvas.draw() 
        canvas.get_tk_widget().pack()
        # creating the Matplotlib toolbar
        toolbar = NavigationToolbar2Tk(canvas, self.window)
        toolbar.update()

    def plot_CDF(self, bool_exclude = False):
        # Create a CDF plot
        self.ax.cla()
        colormaps = iter(plt.cm.viridis(np.linspace(0, 1, len(self.df_data['filename'].unique()))))
        for keys in self.df_data['filename'].unique():
            #copy and sort the data by resistance value
            sorted_data = self.df_data[self.df_data['filename']==keys].copy()
            sorted_data = np.sort(sorted_data['R'])
            #exclude R>1e6
            if bool_exclude ==True:
                sorted_data[sorted_data > 1e6] = np.nan
            #exclude <0
            sorted_data[sorted_data < 0] = np.nan
            sorted_data = sorted_data[~np.isnan(sorted_data)]

            color_line = next(colormaps)
            y = np.arange(1, len(sorted_data) + 1)
            self.ax.plot(sorted_data, y, marker='none', color=color_line, linestyle='-', label=keys, lw=2)
            # print(sorted_data.mean())
            # print(sorted_data.std())

        self.ax.set_xlabel("R (Ohm)")
        self.ax.set_ylabel("CDF (counts)")
        # ax.set_title("IV curve test")
        self.ax.legend()
        # plt.grid()
    
    def plot_IV(self):
        # Generate some exmple data (you can replace this with your own data)
        self.ax.cla() 
        for filename in self.df_data["filename"].unique():
            df_temp = self.df_data[self.df_data['filename']==filename]
            for X in df_temp['X'].unique():
                select_dataX = df_temp[(df_temp['X'] == X)]
                for Y in df_temp['Y'].unique():
                    select_dataXY = select_dataX[(select_dataX['Y'] == Y)]
                    self.ax.plot(select_dataXY['V']*1000,select_dataXY['I']*1000000, '-x', markersize=2)

        self.ax.set_xlabel("V (mV)")
        self.ax.set_ylabel("I (uA)")
        self.ax.set_title("IV curve test")
        # self.ax.legend()

    def plot_Rmap(self, lim_RTop = 1e5):
        # plots all mapping at once from the selection
        for filename in self.df_data["filename"].unique():
            self.fig.clf() # clean the preset axis
            self.fig.set_size_inches(6, 5, forward=True) #set retangle size
            self.ax = self.fig.add_subplot(111)
            df_temp = self.df_data[self.df_data['filename']==filename]
            # Sample data (X and Y locations and values)
            X = df_temp['X']
            Y = df_temp['Y']
            values = df_temp['R'].copy() # copy the data to prevent the change when replacing the data
            values.loc[values > lim_RTop] = lim_RTop
            
            clim_min, clim_max = values.quantile([0, .8])
            # Create the heatmap
            psc = self.ax.scatter(X, Y, c=values, cmap='viridis', marker='s', s=200)
            cbar = self.fig.colorbar(psc, ax=self.ax) # add colorbar
            cbar.set_label('R (ohm)', rotation=270)

            self.ax.set_xlabel("X Location")
            self.ax.set_ylabel("Y Location")
            # self.ax.clim(0, clim_max*0.9)  # Set the color limit to 0-100
            # plt.clim(0, 8e4)  # Set the color limit to 0-100
            self.fig.savefig("Rmap_"+filename + ".png")

            # Find the directory in which the current script resides:
            _file_dir = dirname(realpath(__file__)).replace('/', '\\')
            Popen(r'explorer /select,"'+_file_dir+'"', shell=True)
            


class FileLoaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Analysis")
        self.root.geometry("400x300")

        # Initialize an empty DataFrame
        self.df_data = pd.DataFrame()
        self.df_output = pd.DataFrame()
        self.df_select = pd.DataFrame()

        # Row0: showing the program status
        tk.Label(self.root, text="Program status:").grid(column = 0, 
                                                         row = 0, padx = 3, pady = 5)
        self.label_status = tk.Label(self.root, text="Idle")
        self.label_status.grid(column = 1, row = 0, padx = 3, pady = 5)

        # Row1: load data
        Rowload = 1
        # Button to load files
        self.load_button = tk.Button(self.root, text="0.Load I Files", command=self.load_I)
        self.load_button.grid(column = 0, row = Rowload, padx = 3, pady = 5)
        self.load_button = tk.Button(self.root, text="0.Load T Files", command=self.load_T)
        self.load_button.grid(column = 1, row = Rowload, padx = 3, pady = 5)

        # Button to view the loaded data
        self.process_button = tk.Button(self.root, text="Data Viewer", command=self.data_viewer)
        self.process_button.grid(column = 2, row = Rowload, padx = 3, pady = 5)

        #Row 2: analysis
        RowAnalysis = 2
        # Button to analysis IV curve
        self.plot_IV_button = tk.Button(self.root, text="Plot IV",
                                        command =lambda:PlotApp(self.root, self.df_data).plot_IV())
        self.plot_IV_button.grid(column = 0, row = RowAnalysis, padx = 3, pady = 5)

        # Button to analysis R
        self.process_button = tk.Button(self.root, text="Calculate R", command=self.calculate_R)
        self.process_button.grid(column = 1, row = RowAnalysis, padx = 3, pady = 5)


        #Row 3: plots
        Rowplot = 3 
        # Button to plot mapping resistance over 8" wafer
        self.outputdata_botton = tk.Button(self.root, text="Data Save", command= self.save_files)
        self.outputdata_botton.grid(column = 0, row = Rowplot, padx = 3, pady = 5)

        # Button to plot mapping resistance over 8" wafer
        self.plotRmap_botton = tk.Button(self.root, text="Plot map R",
                                        command= lambda: PlotApp(self.root, self.df_output).plot_Rmap())
        self.plotRmap_botton.grid(column = 1, row = Rowplot, padx = 3, pady = 5)

        # Button to plot CDF
        self.plotCDF_botton = tk.Button(self.root, text="Plot CDF",
                                        command= lambda: PlotApp(self.root, self.df_output).plot_CDF())
        self.plotCDF_botton.grid(column = 2, row = Rowplot, padx = 3, pady = 5)

        # Row4: select dataframe
        RowSelectFrame = 4
        #select dataframe
        tk.Label(self.root, text="Select Dataframe:").grid(column = 0, 
                                                    row = RowSelectFrame, padx = 3, pady = 5)
        self.combobox_df = ttk.Combobox(self.root, values=['df_data', 'df_output'])
        self.combobox_df.grid(column = 1, row = RowSelectFrame, columnspan=2, padx=3, pady = 5)
        self.combobox_df.bind('<<ComboboxSelected>>', self.make_df)  # use virtual event instead of button

    def make_df(self, event=None):
        selected_df = self.combobox_df.get()
        if selected_df == 'df_data':
            self.df_select = self.df_data.copy()
        else:
           self.df_select = self.df_output.copy()

    def load_T(self):
            # Open a file dialog to select multiple files
            files_path = filedialog.askopenfilenames(parent=self.root, title="Choose files", filetypes=(("CSV files", "*.csv"), ("dat files", "*.dat"), ("All files", "*.*")))

            if files_path:
                for filepath in files_path:
                    df_in = pd.read_csv(filepath)
                    print(df_in)
                    for X in df_in['DieX'].unique():
                        for Y in df_in['DieY'].unique():
                            for Module in df_in['Module'].unique():
                                select_data = df_in[(df_in['DieX'] == X)&(df_in['DieY'] == Y)&(df_in['Module'] == Module)]
                                I = select_data['IHi'].to_numpy().copy()
                                V = select_data['VHi'].to_numpy().copy()
                                if(len(I)<3):
                                    continue
                                _fname = '_'.join(basename(splitext(filepath)[0]).split('_')[:2])
                                temp =pd.DataFrame({'filename':_fname, 'X':X, 'Y':Y, 'V':V, 'I':I})
                            self.df_data = pd.concat([self.df_data,temp])

                    self.df_data = self.df_data.astype({'V':'float','I':'float','X':'int','Y':'int'})

                self.label_status.config(text=f"{len(files_path)} files loaded")
            else:
                self.label_status.config(text="No file selected")

    def load_I(self):
        # Open a file dialog to select multiple files
        files_path = filedialog.askopenfilenames(parent=self.root, title="Choose files", filetypes=(("dat files", "*.dat"),("CSV files", "*.csv"), ("All files", "*.*")))

        if files_path:
            for filepath in files_path:
                data_input = [i.strip().split() for i in open(filepath).readlines()]
                num = len(data_input)
                i = 0
                while i < num:
                    if(len(data_input[i])!=2):
                        X, Y = re.findall('-?\d+\.?\d*', data_input[i][-1])
                        i+=1
                        continue
                    else:
                        V = data_input[i][0]
                        I = data_input[i][1]
                        _fname = basename(splitext(filepath)[0])
                        temp =pd.DataFrame({'filename':_fname, 'X':X, 'Y':Y, 'V':V, 'I':I}, index=[i])
                        self.df_data = pd.concat([self.df_data,temp])
                        
                    i+=1

                self.df_data = self.df_data.astype({'V':'float','I':'float','X':'int','Y':'int'})
            self.label_status.config(text=f"{len(files_path)} files loaded")
        else:
            self.label_status.config(text="No file selected")
    

    def save_files(self):
        if self.df_output.empty:
            self.label_status.config(text="No data calculation for saving.")
        else:
            df_analysis=pd.DataFrame(columns=['filename', 'avg','std','std/avg','median', '<100k','<20'])
            for filename in self.df_output["filename"].unique():
                df_target = self.df_output[self.df_output['filename']==filename]
                df_temp = df_target['R'].copy()
                df_temp_analysis = self.R_analysis(filename, df_temp)
                df_analysis = pd.concat([df_analysis, df_temp_analysis])

            # save the data
            # tab2: statistics
            # tab1: all R
            df_ROutput = pd.DataFrame()
            with pd.ExcelWriter('R_analysis.xlsx', engine='xlsxwriter') as writer:
                df_analysis.T.to_excel(writer, sheet_name='analysis')
                for filename in self.df_output["filename"].unique():
                    df_target = self.df_output[self.df_output['filename']==filename].copy()
                    df_target.rename(columns={'R':filename}, inplace=True)
                    df_target = df_target.sort_values(by=[filename])
                    #drop the index to avoid the error
                    df_target = df_target.reset_index(drop=True)
                    df_ROutput = df_ROutput.reset_index(drop=True)
                    df_ROutput = pd.concat([df_ROutput, df_target[filename]], axis=1)
                df_ROutput.to_excel(writer, sheet_name='R')

            # Find the directory in which the current script resides:
            _file_dir = dirname(realpath(__file__)).replace('/', '\\')
            Popen(r'explorer /select,"'+_file_dir+'"', shell=True)

    def data_viewer(self):
        # Display the DataFrame in a new window using PandasTable
        if not self.df_select.empty:
            
            # Create a new Toplevel window
            new_window = tk.Toplevel(self.root)
            new_window.title("DataFrame Viewer")

            # Create a PandasTable widget in the new window
            table = Table(new_window, dataframe=self.df_select, showtoolbar=True, showstatusbar=True)
            table.show()

        else:
            tk.messagebox.showwarning("Warning","Dataframe is empty.")

    def calculate_R(self):
        for filename in self.df_data["filename"].unique():
            df_target = self.df_data[self.df_data['filename']==filename]
            list_locx = df_target['X'].unique()
            list_locy = df_target['Y'].unique()
            #iterating all the locations
            for loc_x in list_locx:
                select_dataX = df_target[(df_target['X'] == loc_x)]
                for loc_y in list_locy:
                    select_dataXY = select_dataX[(select_dataX['Y'] == loc_y)]
                    if len(select_dataXY)>2:
                        Res, R_dev = calculate_R(select_dataXY['I'].to_numpy(), select_dataXY['V'].to_numpy())
                        df_temp = pd.DataFrame(data={'X':loc_x, 'Y':loc_y, 'filename':filename, 'R':Res, 'R_dev': R_dev})
                        self.df_output = pd.concat([self.df_output, df_temp])
        
    # Calculate some basic analysis
    def R_analysis(self, filename, _df_temp):
        # output the data (just like the previous statisical results)
        # average R, dR/Ravg, dR(std. dev.), midian, < 100k %, < 20Ohm %
        _df_temp.loc[_df_temp > 1e5] = np.nan   # exclude R> 100k
        _df_temp.loc[_df_temp < 0] = np.nan
        df_results = pd.DataFrame(data={
            'filename': filename,
            'avg':np.nanmean(_df_temp), 
            'std':np.nanstd(_df_temp),
            'std/avg':np.nanstd(_df_temp)/np.nanmean(_df_temp)*100,
            'median':np.nanmedian(_df_temp),
            '<100k': len(_df_temp[_df_temp<1e5])/len(_df_temp)*100,
            '<20': len(_df_temp[_df_temp<20])/len(_df_temp)*100}, index=[0])
        return df_results

if __name__ == "__main__":
    root_tk = tk.Tk()
    app = FileLoaderApp(root_tk)
    root_tk.mainloop()