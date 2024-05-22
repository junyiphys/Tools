'''GUI for the Resistance data output
202405 Modified by Junyi Tsai@ Academia Sinica

Intro
It's an easy script to analyze the resistance from various source, which is easy to optimize.

The output file style can also be optimize, but already selected a certian theme. 
The only global function: df

TODO: select I or T function
TODO: plot decoration
TODO: save all plots at one click
2.IV標題需要使用者定義

Essential package to install with the following commend:
pip3 install pandas pandastable matplotlib scikit-learn numpy xlsxwriter


Note: it's not a good idea to install from the conda... some package are easily missed
'''

# import tkinter as tk
# import pandas as pd
from tkinter import Tk, Toplevel, Label, Button, messagebox, Entry
from tkinter import ttk, StringVar
from tkinter import filedialog
from pandas import DataFrame, read_csv, concat, ExcelWriter
from pandastable import Table
from re import findall
from os.path import splitext, basename
# from os.path import dirname, realpath

#plot functions
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from subprocess import Popen


from sklearn.linear_model import LinearRegression
# import numpy as np
from numpy import nan, reshape, linspace, arange, isnan, sort, histogram
from numpy import nanstd, nanmean, nanmedian
from matplotlib.cm import viridis as cmap_viridis

def calculate_R(x, y):
    #IV curve calculation
    #define predictor and response variables
    #fit regression model
    x = reshape(x, (-1, 1))
    model = LinearRegression()
    model.fit(x, y)
    R = model.coef_ #resistance 
    R_dev = model.score(x, y) #calculate R-squared of regression model
    return R, R_dev

class PlotApp:
    def __init__(self, master, df):
        self.master=master
        self.df_data = df
        self.window = Toplevel(parent=None)
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
        colormaps = iter(cmap_viridis(linspace(0, 1, len(self.df_data['filename'].unique()))))
        for keys in self.df_data['filename'].unique():
            #copy and sort the data by resistance value
            sorted_data = self.df_data[self.df_data['filename']==keys].copy()
            sorted_data = sort(sorted_data['R'])
            #exclude R>1e6
            if bool_exclude ==True:
                sorted_data[sorted_data > 1e6] = nan
            #exclude <0
            sorted_data[sorted_data < 0] = nan
            sorted_data = sorted_data[~isnan(sorted_data)]

            color_line = next(colormaps)
            y = arange(1, len(sorted_data) + 1)
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

    def plot_hist(self, bin_num=10):
        # plots the histogram
        self.fig.clf() # clean the preset axis
        self.fig.set_size_inches(6, 5, forward=True) #set retangle size
        self.ax = self.fig.add_subplot(111)
        colormaps = iter(cmap_viridis(linspace(0, 1, len(self.df_data["filename"].unique()))))
        for filename in self.df_data["filename"].unique():
            color_line = next(colormaps)

            df_temp = self.df_data[self.df_data['filename']==filename]
            values = df_temp['R'].copy() # copy the data to prevent the change when replacing the data
            #Set outliers as 0 or 1e6
            values[values>1e6]=1e6
            values[values<0]=0
            values = values[~isnan(values)]
            
            # values.loc[values > xlim[1]] = xlim # limited time
            # xlim = values.quantile([.1, .9])
            xlim= [values.min(), values.max()]
            def_bins = linspace(xlim[0], xlim[1], num=bin_num)
            #auto select the range
            
            # Create a histogram
            data_hist, bins = histogram(values, bins=def_bins, density=False)
            # bin_centers = (bins[:-1] + bins[1:]) / 2 #for fittng function
            
            # Plot the histogram
            self.ax.hist(values, bins, density=False, alpha=0.4, color=color_line, label=filename)

            # clim_min, clim_max = values.quantile([0, .8])
            # # Create the heatmap
            # psc = self.ax.scatter(X, Y, c=values, cmap='viridis', marker='s', s=200)
            # cbar = self.fig.colorbar(psc, ax=self.ax) # add colorbar
            # cbar.set_label('R (ohm)', rotation=270)

        self.ax.set_xlabel("Resistance (Ohm)")
        self.ax.set_ylabel("Counts")
        self.ax.grid()
        self.ax.legend()
        # self.ax.clim(0, clim_max*0.9)  # Set the color limit to 0-100
        # plt.clim(0, 8e4)  # Set the color limit to 0-100
        self.fig.savefig("Hist_linear.png")

        # # Find the directory in which the current script resides:
        # _file_dir = dirname(realpath(__file__)).replace('/', '\\')
        # Popen(r'explorer /select,"'+_file_dir+'"', shell=True)


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

            # # Find the directory in which the current script resides:
            # _file_dir = dirname(realpath(__file__)).replace('/', '\\')
            # Popen(r'explorer /select,"'+_file_dir+'"', shell=True)
            


class FileLoaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Analysis")
        self.root.geometry("500x300")

        # Initialize an empty DataFrame
        self.df_data = DataFrame()
        self.df_output = DataFrame()
        self.df_select = DataFrame()

        # Row0: showing the program status
        Label(self.root, text="Program status:").grid(column = 0, 
                                                         row = 0, padx = 3, pady = 5)
        self.label_status = Label(self.root, text="Idle")
        self.label_status.grid(column = 1, row = 0, padx = 3, pady = 5)


        # Row1: load data
        Rowload = 1
        # Button to load files
        self.load_button = Button(self.root, text="0.Load I Files", command=self.load_I)
        self.load_button.grid(column = 0, row = Rowload, padx = 3, pady = 5)
        self.load_button = Button(self.root, text="0.Load T Files", command=self.load_T)
        self.load_button.grid(column = 1, row = Rowload, padx = 3, pady = 5)

        # Button to view the loaded data
        self.process_button = Button(self.root, text="Data Viewer", command=self.data_viewer)
        self.process_button.grid(column = 2, row = Rowload, padx = 3, pady = 5)


        #Row 2: analysis
        RowAnalysis = 2
        # Button to analysis IV curve
        self.plot_IV_button = Button(self.root, text="Plot IV",
                                        command =lambda:PlotApp(self.root, self.df_data).plot_IV())
        self.plot_IV_button.grid(column = 0, row = RowAnalysis, padx = 3, pady = 5)
        # Button to analysis R
        self.process_button = Button(self.root, text="Calculate R", command=self.calculate_R)
        self.process_button.grid(column = 1, row = RowAnalysis, padx = 3, pady = 5)


        #Row 3: plots
        Rowplot = 3 
        # Button to plot mapping resistance over 8" wafer
        self.outputdata_botton = Button(self.root, text="Data Save", command= self.save_files)
        self.outputdata_botton.grid(column = 0, row = Rowplot, padx = 3, pady = 5)
        # Button to plot mapping resistance over 8" wafer
        self.plotRmap_botton = Button(self.root, text="Plot map R",
                                        command= lambda: PlotApp(self.root, self.df_output).plot_Rmap())
        self.plotRmap_botton.grid(column = 1, row = Rowplot, padx = 3, pady = 5)
        # Button to plot CDF
        self.plotCDF_botton = Button(self.root, text="Plot CDF",
                                        command= lambda: PlotApp(self.root, self.df_output).plot_CDF())
        self.plotCDF_botton.grid(column = 2, row = Rowplot, padx = 3, pady = 5)
        # Button to plot Histogram
        self.plotCDF_botton = Button(self.root, text="Plot hist",
                                        command= lambda: PlotApp(self.root, self.df_output).plot_hist())
        self.plotCDF_botton.grid(column = 3, row = Rowplot, padx = 3, pady = 5)


        # Row4: select dataframe
        RowSelectFrame = 4
        #select dataframe
        Label(self.root, text="Select Dataframe:").grid(column = 0, 
                                                    row = RowSelectFrame, padx = 3, pady = 5)
        self.combobox_df = ttk.Combobox(self.root, values=['df_data', 'df_output'])
        self.combobox_df.grid(column = 1, row = RowSelectFrame, columnspan=2, padx=3, pady = 5)
        self.combobox_df.bind('<<ComboboxSelected>>', self.make_df)  # use virtual event instead of button


        # Row5: show that only T need to change the label
        Label(self.root, text = 'T label replacement')

        RowT_IV_define = 6
        #Current
        self.current_var = StringVar(self.root, value="Idcrv")
        self.voltage_var = StringVar(self.root, value="Vdcrv")
        self.current_label = Label(self.root, text = 'Current label')
        self.current_entry = Entry(self.root, textvariable = self.current_var)
        #voltage
        self.voltage_label = Label(self.root, text = 'Voltage label')
        self.voltage_entry = Entry(self.root, textvariable = self.voltage_var)


        #pack the location
        self.current_label.grid(column = 0, row = RowT_IV_define, padx=3, pady = 5)
        self.current_entry.grid(column = 1, row = RowT_IV_define, padx=3, pady = 5)
        self.voltage_label.grid(column = 2, row = RowT_IV_define, padx=3, pady = 5)
        self.voltage_entry.grid(column = 3, row = RowT_IV_define, padx=3, pady = 5)


    def make_df(self, event=None):
        selected_df = self.combobox_df.get()
        if selected_df == 'df_data':
            self.df_select = self.df_data.copy()
        else:
           self.df_select = self.df_output.copy()

    def load_T(self):
            #clean the data
            self.df_data = DataFrame()
            self.df_output = DataFrame()
            self.df_select = DataFrame()
            V_label = self.voltage_entry.get()
            I_label = self.current_entry.get()
            if V_label==nan:
                V_label='VHi'
            if I_label==nan:
                I_label='IHi'
            # Open a file dialog to select multiple files
            files_path = filedialog.askopenfilenames(parent=self.root, title="Choose files", filetypes=(("CSV files", "*.csv"), ("dat files", "*.dat"), ("All files", "*.*")))

            if files_path:
                for filepath in files_path:
                    df_in = read_csv(filepath)
                    for X in df_in['DieX'].unique():
                        for Y in df_in['DieY'].unique():
                            for Module in df_in['Module'].unique():
                                select_data = df_in[(df_in['DieX'] == X)&(df_in['DieY'] == Y)&(df_in['Module'] == Module)]
                                I = select_data[I_label].to_numpy().copy()
                                V = select_data[V_label].to_numpy().copy()
                                if(len(I)<3):
                                    continue
                                _fname = '_'.join(basename(splitext(filepath)[0]).split('_')[:2])
                                temp = DataFrame({'filename':_fname, 'X':X, 'Y':Y, 'V':V, 'I':I})
                            self.df_data = concat([self.df_data,temp])

                    self.df_data = self.df_data.astype({'V':'float','I':'float','X':'int','Y':'int'})

                self.label_status.config(text=f"{len(files_path)} files loaded")
            else:
                self.label_status.config(text="No file selected")

    def load_I(self):
        #clean the data
        self.df_data = DataFrame()
        self.df_output = DataFrame()
        self.df_select = DataFrame()

        # Open a file dialog to select multiple files
        files_path = filedialog.askopenfilenames(parent=self.root, title="Choose files", filetypes=(("dat files", "*.dat"),("CSV files", "*.csv"), ("All files", "*.*")))

        if files_path:
            for filepath in files_path:
                data_input = [i.strip().split() for i in open(filepath).readlines()]
                num = len(data_input)
                i = 0
                while i < num:
                    if(len(data_input[i])!=2):
                        X, Y = findall('-?\d+\.?\d*', data_input[i][-1])
                        i+=1
                        continue
                    else:
                        V = data_input[i][0]
                        I = data_input[i][1]
                        _fname = basename(splitext(filepath)[0])
                        temp =DataFrame({'filename':_fname, 'X':X, 'Y':Y, 'V':V, 'I':I}, index=[i])
                        self.df_data = concat([self.df_data,temp])
                        
                    i+=1

                self.df_data = self.df_data.astype({'V':'float','I':'float','X':'int','Y':'int'})
            self.label_status.config(text=f"{len(files_path)} files loaded")
        else:
            self.label_status.config(text="No file selected")
    

    def save_files(self):
        if self.df_output.empty:
            self.label_status.config(text="No data calculation for saving.")
        else:
            df_analysis=DataFrame(columns=['filename', 'avg','std','std/avg','median', '<100k','<20'])
            for filename in self.df_output["filename"].unique():
                df_target = self.df_output[self.df_output['filename']==filename]
                df_temp = df_target['R'].copy()
                df_temp_analysis = self.R_analysis(filename, df_temp)
                df_analysis = concat([df_analysis, df_temp_analysis])

            # save the data
            # tab2: statistics
            # tab1: all R
            df_ROutput = DataFrame()
            with ExcelWriter('R_analysis.xlsx', engine='xlsxwriter') as writer:
                df_analysis.T.to_excel(writer, sheet_name='analysis')
                for filename in self.df_output["filename"].unique():
                    df_target = self.df_output[self.df_output['filename']==filename].copy()
                    df_target.rename(columns={'R':filename}, inplace=True)
                    df_target = df_target.sort_values(by=[filename])
                    #drop the index to avoid the error
                    df_target = df_target.reset_index(drop=True)
                    df_ROutput = df_ROutput.reset_index(drop=True)
                    df_ROutput = concat([df_ROutput, df_target[filename]], axis=1)
                df_ROutput.to_excel(writer, sheet_name='R')
                for filename in self.df_output["filename"].unique():
                    df_target = self.df_output[self.df_output['filename']==filename].copy()
                    df_target.to_excel(writer, sheet_name=filename)

            # # Find the directory in which the current script resides:
            # _file_dir = dirname(realpath(__file__)).replace('/', '\\')
            # Popen(r'explorer /select,"'+_file_dir+'"', shell=True)

    def data_viewer(self):
        # Display the DataFrame in a new window using PandasTable
        if not self.df_select.empty:
            
            # Create a new Toplevel window
            new_window = Toplevel(self.root)
            new_window.title("DataFrame Viewer")

            # Create a PandasTable widget in the new window
            table = Table(new_window, dataframe=self.df_select, showtoolbar=True, showstatusbar=True)
            table.show()

        else:
            messagebox.showwarning("Warning","Dataframe is empty.")

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
                        df_temp = DataFrame(data={'X':loc_x, 'Y':loc_y, 'filename':filename, 'R':Res, 'R_dev': R_dev})
                        self.df_output = concat([self.df_output, df_temp])
        
    # Calculate some basic analysis
    def R_analysis(self, filename, _df_temp):
        # output the data (just like the previous statisical results)
        # average R, dR/Ravg, dR(std. dev.), midian, < 100k %, < 20Ohm %
        _df_temp.loc[_df_temp > 1e5] = nan   # exclude R> 100k
        _df_temp.loc[_df_temp < 0] = nan
        df_results = DataFrame(data={
            'filename': filename,
            'avg':nanmean(_df_temp), 
            'std':nanstd(_df_temp),
            'std/avg':nanstd(_df_temp)/nanmean(_df_temp)*100,
            'median':nanmedian(_df_temp),
            '<100k': len(_df_temp[_df_temp<1e5])/len(_df_temp)*100,
            '<20': len(_df_temp[_df_temp<20])/len(_df_temp)*100}, index=[0])
        return df_results

if __name__ == "__main__":
    root_tk = Tk()
    app = FileLoaderApp(root_tk)
    root_tk.mainloop()