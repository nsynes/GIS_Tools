# Nick Synes
# 22 Aug 2016
#
# Habitat network tool for Forest Research
# A number of parameters are currently greyed out.
# These will be added in future versions, and relate to
# within and between network connectivity and corridors.
#
# The tool currently relies entirely on arcpy (ESRI ArcGIS),
# and must be run from a version of Python with the arcpy
# library. ESRI usually installs its own ArcGIS version
# of Python here: C:\Python27
#
#########################################################


import Tkinter, Tkconstants, tkFileDialog, tkMessageBox
import os, numpy, tempfile
import arcpy

arcpy.env.overwriteOutput = True

class BeetleGUI(Tkinter.Tk):
    def __init__(self,parent):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        # initialise the grid system to keep GUI organised
        self.grid()

        # Dictionary to store user selected filenames
        self.dFileName = {}

        # Initial directory for file selection
        self.directory = None

        # Parameter label names and text for GUI
        # Use list lLabs to determine order
        # Use dictionary dText to store the actual GUI text
        lLabs = ["VectorRaster","HabFile","LandFile","LandField","CellSize","Neighbourhood","MinHabArea","MaxDist",
                 "WithinNet","BetweenNet","MinNetArea","Corridors","PercentLCP",
                 "HabOutFname","NetOutFname","OutAreaCsv"]
        dText = {"VectorRaster":"Vector or raster input files",
                 "HabFile":"Home habitat file",
                 "LandFile":"Landcover file",
                 "LandField":"Landcover variable",
                 "CellSize":"Cell size",
                 "Neighbourhood":"Neighbourhood",
                 "MinHabArea":"Minimum viable habitat area",
                 "MaxDist":"Maximum dispersal distance",
                 "WithinNet":"Within network",
                 "BetweenNet":"Between network",
                 "MinNetArea":"Minimum network area",
                 "Corridors":"Corridors between network",
                 "PercentLCP":"% of least-cost path",
                 "HabOutFname":"Home habitat output filename",
                 "NetOutFname":"Network output filename",
                 "OutAreaCsv":"Output area csv file"}
        
        # Put list into dictionary of labels and order
        dLabOrder = {}
        for i in range(len(lLabs)):
            dLabOrder[lLabs[i]] = i

        self.dLabelText = {} # stores label text
        self.dLabel = {} # store the actual label
        # Create the labels for each parameter
        for key in dLabOrder.keys():
            self.dLabelText[key] = Tkinter.StringVar()
            self.dLabelText[key].set(dText[key])
            self.dLabel[key] = Tkinter.Label(self,textvariable=self.dLabelText[key])
            self.dLabel[key].grid(column=0,row=dLabOrder[key],padx=5,pady=5,sticky=Tkinter.E)

        self.dEntryValue = {} # stores the entry value
        self.dEntryField = {} # stores the field into which the user enters the value
        # Create the integer based entry fields
        keys = ["CellSize","MinHabArea","MaxDist","MinNetArea","PercentLCP"]
        for key in keys:
            self.dEntryValue[key] = Tkinter.IntVar()
            self.dEntryField[key] = Tkinter.Entry(self,textvariable=self.dEntryValue[key])
            self.dEntryField[key].grid(column=1,row=dLabOrder[key],padx=5,pady=5,sticky=Tkinter.W)
        # Default(s)
        self.dEntryValue["CellSize"].set(10)

        # Option menus
        key = "Neighbourhood"
        self.dEntryValue[key] = Tkinter.IntVar()
        self.dEntryValue[key].set(8)
        self.dEntryField[key] = Tkinter.OptionMenu(self, self.dEntryValue[key], 4, 8)
        self.dEntryField[key].grid(column=1,row=dLabOrder[key],padx=5,pady=5,sticky=Tkinter.W)
        key = "VectorRaster"
        self.dEntryValue[key] = Tkinter.StringVar()
        self.dEntryValue[key].set("Vector")
        self.dEntryField[key] = Tkinter.OptionMenu(self, self.dEntryValue[key], "Vector", "Raster")
        self.dEntryField[key].grid(column=1,row=dLabOrder[key],padx=5,pady=5,sticky=Tkinter.W)
        key = "LandField"
        self.dEntryValue[key] = Tkinter.StringVar()
        self.LandFieldOpt = Tkinter.OptionMenu(self, self.dEntryValue[key],"")
        self.LandFieldOpt.grid(column=1,row=dLabOrder[key],padx=5,pady=5,sticky=Tkinter.W)

        # Create fields for input files
        for key in ["HabFile","LandFile"]:
            self.dEntryValue[key] = Tkinter.StringVar()
            self.dEntryField[key] = Tkinter.Entry(self,textvariable=self.dEntryValue[key],width=60)
            self.dEntryField[key].grid(column=1,row=dLabOrder[key],padx=5,pady=5,sticky=Tkinter.W)
            Tkinter.Button(self,text="...", command=lambda key=key:  self.OnFileButtonClick(key)).grid(column=2,row=dLabOrder[key],padx=5,pady=5,sticky=Tkinter.W)

        # Create fields for "save as" files
        for key in ["HabOutFname","NetOutFname"]:
            self.dEntryValue[key] = Tkinter.StringVar()
            self.dEntryField[key] = Tkinter.Entry(self,textvariable=self.dEntryValue[key],width=60)
            self.dEntryField[key].grid(column=1,row=dLabOrder[key],padx=5,pady=5,sticky=Tkinter.W)
            Tkinter.Button(self,text="...", command=lambda key=key:  self.OnSaveAsButtonClick(key)).grid(column=2,row=dLabOrder[key],padx=5,pady=5,sticky=Tkinter.W)

        # Create check button fields
        keys = ["WithinNet","BetweenNet","Corridors","OutAreaCsv"]
        for key in keys:
            self.dEntryValue[key] = Tkinter.IntVar()
            self.dEntryField[key] = Tkinter.Checkbutton(self, text="", variable=self.dEntryValue[key])
            self.dEntryField[key].grid(column=1,row=dLabOrder[key],padx=5,pady=5,sticky=Tkinter.W)

        # DISABLED Entry fields until functionality coded in
        # Grey-out/DISABLED until functionality coded in
        for key in ["WithinNet","BetweenNet","MinNetArea","Corridors","PercentLCP"]:
            self.dLabel[key].configure(fg="grey")
            self.dEntryField[key].configure(state="disabled")

        # Set a trace on the VectorRaster option menu to disable fields when not required
        self.dEntryValue["VectorRaster"].trace('w', self.ChangeVectorRaster)

        # Set a trace of the landcover field option menu
        self.dEntryValue["LandFile"].trace('w', self.UpdateLandField)
    
        # Final button to run the tool
        Tkinter.Button(self,text="Run", command=self.OnOkButtonClick).grid(column=1,row=len(lLabs)+1,padx=5,pady=5)

        # Controls for the geometry of the app window
        self.grid_columnconfigure(0,weight=1)
        self.resizable(False,False)
        self.update()
        self.geometry(self.geometry())       

        # Settings for the accepted raster and vector file types
        # Currently limited to tif and shp, but can add others here...
        self.raster_opt = options = {}
        options["defaultextension"] = ".tif"
        options["filetypes"] = [("GeoTIFF files", ".tif")]
        options["initialdir"] = r"C:\\"
        self.vector_opt = options = {}
        options["defaultextension"] = ".shp"
        options["filetypes"] = [("Shape files", ".shp")]
        options["initialdir"] = r"C:\\"

    def OnFileButtonClick(self, key):
        """Open a filename selection dialogue, with file options dependent on whether vector or
        raster has been chosen in the option menu"""
        VectorRaster = self.dEntryValue["VectorRaster"].get()
        if VectorRaster == "Vector":
            self.dFileName[key] = tkFileDialog.askopenfilename(title="Choose a %s file..." %VectorRaster, **self.vector_opt)
        elif VectorRaster == "Raster":
            self.dFileName[key] = tkFileDialog.askopenfilename(title="Choose a %s file..." %VectorRaster, **self.raster_opt)
        self.vector_opt["initialdir"] = os.path.split(self.dFileName[key])[0]
        self.raster_opt["initialdir"] = os.path.split(self.dFileName[key])[0]
        # If a new filename was selected, set it as the new filename
        if self.dFileName[key]:
            self.dEntryValue[key].set(self.dFileName[key])

    def OnSaveAsButtonClick(self, key):
        self.dFileName[key] = tkFileDialog.asksaveasfilename(title="Save file as...", **self.vector_opt)
        self.vector_opt["initialdir"] = os.path.split(self.dFileName[key])[0]
        # If a new filename was selected, set it as the new filename
        if self.dFileName[key]:
            self.dEntryValue[key].set(self.dFileName[key])
        
    def OnOkButtonClick(self):
        """Collect all the parameter values then call the main function"""
        VectorRaster = self.dEntryValue["VectorRaster"].get()
        HabFile = self.dEntryValue["HabFile"].get()
        LandFile = self.dEntryValue["LandFile"].get()
        LandField = self.dEntryValue["LandField"].get()
        MinHabArea = self.dEntryValue["MinHabArea"].get()
        MaxDist = self.dEntryValue["MaxDist"].get()
        Neighbourhood = self.dEntryValue["Neighbourhood"].get()
        if VectorRaster == "Vector":
            CellSize = self.dEntryValue["CellSize"].get()
        else:
            CellSize = arcpy.GetRasterProperties_management(HabFile, "CELLSIZEX").getOutput(0)
        HabOutFile = self.dEntryValue["HabOutFname"].get()
        NetOutFile = self.dEntryValue["NetOutFname"].get()
        OutCsvFile = self.dEntryValue["OutAreaCsv"].get()
        RunLCN(VectorRaster, HabFile, LandFile, LandField, MinHabArea, MaxDist, Neighbourhood, CellSize, HabOutFile, NetOutFile, OutCsvFile)

    def UpdateLandField(self, *args):
        """Called from a trace on the land file entry box. Updates the option menu of landcover vector fields"""
        if self.dEntryValue["VectorRaster"].get() == "Vector":
            fields = arcpy.Describe(self.dFileName["LandFile"]).fields
            menu = self.LandFieldOpt['menu']
            menu.delete(0, 'end')
            # Add each identified shapefile field to the landfile field option menu
            for field in fields:
                menu.add_command(label=field.name, command=lambda value=field.name: self.dEntryValue["LandField"].set(value))

    def ChangeVectorRaster(self, *args):
        """Called from a trace on VectorRaster option menu. Hides Landcover field and cellsize parameter if "raster" option chosen."""
        if self.dEntryValue["VectorRaster"].get() == "Vector":
            # Display and enable fields if working with shapefiles
            self.LandFieldOpt.configure(state="normal")
            self.dLabel["LandField"].configure(fg="black")
            self.dEntryValue["CellSize"].set(10)
            self.dEntryField["CellSize"].configure(state="normal")
            self.dEntryField["CellSize"].configure(fg="black")
        else:
            # Grey out and disable fields if working with rasters
            self.LandFieldOpt.configure(state="disabled")
            self.dLabel["LandField"].configure(fg="grey")
            self.dEntryValue["CellSize"].set("")
            self.dEntryField["CellSize"].configure(state="disabled")
            self.dEntryField["CellSize"].configure(fg="grey")



def RunLCN(VecOrRast, HabFname, LandFname, Field, MinHabArea, MaxCost, Nhood, CellSize, fnHabOut, fnNetOut, intCsv):

    arcpy.CheckOutExtension("spatial")
    
    # Dictionary to convert to ArcGIS syntax for neighbourhoods
    dicNeighbours = {4: "FOUR", 8: "EIGHT"}
    
    # If vector files have been chosen, convert them to rasters first
    if VecOrRast == "Vector":
        # Convert vector files to rasters
        fnGivenHab = tmp("tif")
        arcpy.PolygonToRaster_conversion(HabFname, arcpy.ListFields(HabFname)[0].name, fnGivenHab, "", "", CellSize) # DEBUG tmp.tif
        fnGivenLand = tmp("tif")
        arcpy.PolygonToRaster_conversion(LandFname, Field, fnGivenLand, "", "", CellSize) # DEBUG tmp0.tif
    else:
        # If the user started with raster files, just use those original raster files
        fnGivenHab = HabFname
        fnGivenLand = LandFname

    # If a minimum habitat area has been set, calculate the area of each patch
    if MinHabArea > 0:
        RegionGroupHab = arcpy.sa.RegionGroup(fnGivenHab, dicNeighbours[Nhood]) # DEBUG tmp1.tif
        fnRegionGroup = tmp("tif")
        RegionGroupHab.save(fnRegionGroup)
        fnVecRegionGroup = tmp("shp")
        arcpy.RasterToPolygon_conversion(fnRegionGroup, fnVecRegionGroup, "NO_SIMPLIFY", "VALUE") # DEBUG tmp.shp (GRIDCODE field)
        fnVecRegionGroupByGridCode = tmp("shp")
        arcpy.Dissolve_management(fnVecRegionGroup, fnVecRegionGroupByGridCode, "GRIDCODE") # DEBUG tmp0.shp
        # Does not work in ArcGIS 10.0
        #arcpy.AddGeometryAttributes_management(fnVecRegionGroupByGridCode, "AREA")
        # So do it manually below:
        arcpy.AddField_management(fnVecRegionGroupByGridCode, "POLY_AREA", "DOUBLE")
        geometryField = arcpy.Describe(fnVecRegionGroupByGridCode).shapeFieldName
        cursor = arcpy.UpdateCursor(fnVecRegionGroupByGridCode)
        for row in cursor:
            row.setValue("POLY_AREA", row.getValue(geometryField).area)
            cursor.updateRow(row)
        del row, cursor
        fnVecSelectedHab = tmp("shp")
        arcpy.Select_analysis(fnVecRegionGroupByGridCode, fnVecSelectedHab, '"POLY_AREA" >= %s' %MinHabArea) # DEBUG tmp1.shp
        fnSelectedHab = tmp("tif")
        arcpy.PolygonToRaster_conversion(fnVecSelectedHab, arcpy.ListFields(fnVecSelectedHab)[0].name, fnSelectedHab, "", "", CellSize) # DEBUG tmp2.tif
    else:
        # If no minimum habitat area was set, just just use the habitat as given
        fnSelectedHab = fnGivenHab
    
    # Quick way to reclassify all values in habitat raster to zero
    Habs = arcpy.sa.Plus(fnSelectedHab, 1)# DEBUG tmp3.tif
    fnHabs = tmp("tif")
    Habs.save(fnHabs)
        
    # Cost distance
    fnCostDist = tmp("tif")
    arcpy.gp.CostDistance_sa(fnHabs, fnGivenLand, fnCostDist, MaxCost, "") # DEBUG tmp4.tif
    
    # Reclassify everything within the cost distance to zero
    fnWithinCost = tmp("tif")
    arcpy.gp.Reclassify_sa(fnCostDist, "VALUE", "0 " + str(MaxCost) + " 0", fnWithinCost) # DEBUG tmp5.tif
    
    # Region group networks to identify contiguous areas
    Networks = arcpy.sa.RegionGroup(fnWithinCost, dicNeighbours[Nhood]) # DEBUG tmp6.tif
    fnNetworks = tmp("tif")
    Networks.save(fnNetworks)
    
    # Convert original habitat raster to all zeros and add to network raster
    # to relabel habitat patches that are in the same network, and to remove habitat patches
    # that are outside of the network (i.e. those less than the minimum patch size)
    OrigHabRasterZero = arcpy.sa.Con(arcpy.sa.Raster(fnGivenHab) >= 0, 0, fnGivenHab) # DEBUG tmp7.tif
    fnOrigHabRasterZero = tmp("tif")
    OrigHabRasterZero.save(fnOrigHabRasterZero)
    HabNetworks = arcpy.sa.Plus(fnNetworks, fnOrigHabRasterZero) # DEBUG tmp8.tif
    fnHabNetworks = tmp("tif")
    HabNetworks.save(fnHabNetworks)

    # The output hab file
    fnHabPoly = tmp("shp")
    arcpy.RasterToPolygon_conversion(fnHabNetworks, fnHabPoly, "NO_SIMPLIFY", "VALUE")
    arcpy.Dissolve_management(fnHabPoly, fnHabOut, "GRIDCODE")

    # Region group the habitat patches...
    HabRegions = arcpy.sa.RegionGroup(fnHabNetworks, dicNeighbours[Nhood]) # DEBUG tmp9.tif
    fnHabRegions = tmp("tif")
    HabRegions.save(fnHabRegions)

    # Prepare shapefiles to allow habitat patches to be counted within each network
    if Nhood == 4:
        fnHabForPartCount = tmp("shp")
        arcpy.RasterToPolygon_conversion(fnHabRegions, fnHabForPartCount, "NO_SIMPLIFY", "VALUE") # DEBUG tmp2.shp
    else:
        fnHabPoly = tmp("shp")
        arcpy.RasterToPolygon_conversion(fnHabRegions, fnHabPoly, "NO_SIMPLIFY", "VALUE")
        fnHabForPartCount = tmp("shp")
        arcpy.Dissolve_management(fnHabPoly, fnHabForPartCount, "GRIDCODE")
        fnHabDissolve = tmp("shp")
    
    # Output networks as vector (shape) file
    fnNetSeparate = tmp("shp")
    arcpy.RasterToPolygon_conversion(fnNetworks, fnNetSeparate, "NO_SIMPLIFY", "VALUE")
    fnNetDissolve = tmp("shp")
    arcpy.Dissolve_management(fnNetSeparate, fnNetDissolve, "GRIDCODE")

    # Network polygons can become separated from habitats when considering a 4 cell neighbourhood,
    # so remove these when the neighbourhood has been set as 4
    # NETWORK SHAPEFILE FINAL OUTPUT
    if Nhood == 4:
        arcpy.MakeFeatureLayer_management(fnNetDissolve, "NetLyr")
        arcpy.SelectLayerByLocation_management("NetLyr", "contains", fnHabOut)
        arcpy.Select_analysis("NetLyr", fnNetOut)
        arcpy.Delete_management("NetLyr")
    else:
        arcpy.CopyFeatures_management(fnNetDissolve, fnNetOut)


    # If user wanted a csv of the habitat and network areas, then calculate and output this
    if intCsv:
        # Calculate polygon areas for networks and habitats
        # Should work for ArcGIS 10.0+
        # area
        for FinalShapeFile in (fnNetOut, fnHabOut):
            arcpy.AddField_management(FinalShapeFile, "POLY_AREA", "DOUBLE")
            geometryField = arcpy.Describe(FinalShapeFile).shapeFieldName
            cursor = arcpy.UpdateCursor(FinalShapeFile)
            for row in cursor:
                row.setValue("POLY_AREA", row.getValue(geometryField).area)
                cursor.updateRow(row)
            del row, cursor
            
        # count patches
        arcpy.MakeFeatureLayer_management(fnNetOut, "NetworkLyr")
        arcpy.MakeFeatureLayer_management(fnHabForPartCount, "HabitatLyr")
        cursor = arcpy.SearchCursor(fnNetOut)
        dicPartCount = {}
        for row in cursor:
            FID = row.getValue("FID")
            arcpy.SelectLayerByAttribute_management("NetworkLyr", "NEW_SELECTION", "\"FID\" = %s" %FID)
            arcpy.SelectLayerByLocation_management("HabitatLyr", "WITHIN", "NetworkLyr", selection_type="NEW_SELECTION")
            dicPartCount[FID] = int(arcpy.GetCount_management("HabitatLyr").getOutput(0))
        del row, cursor

        arcpy.AddField_management(fnHabOut, "PART_COUNT", "LONG")
        cursor = arcpy.UpdateCursor(fnHabOut)
        for row in cursor:
            row.setValue("PART_COUNT", dicPartCount[row.getValue("FID")])
            cursor.updateRow(row)
        del row, cursor
    
        # Create a path and filename for the csv file based on the other output files
        # Note: could add extra filename parameter for this...
        [pthOut, strNet] = os.path.split(fnNetOut)
        strHab = os.path.split(fnHabOut)[1]
        pthCsv = os.path.join(pthOut, "%s%s.csv" %(strNet.split(".")[0], strHab.split(".")[0]))

        # Use cursor to collect the area info
        dicNet = {}
        dicHab = {}
        cursor = arcpy.SearchCursor(fnNetOut)
        for row in cursor:
            dicNet[row.getValue("FID")] = row.getValue("POLY_AREA")
        del row, cursor
        cursor = arcpy.SearchCursor(fnHabOut)
        for row in cursor:
            dicHab[row.getValue("FID")] = [row.getValue("PART_COUNT"), row.getValue("POLY_AREA")]
        del row, cursor

        # Get the linear units of the shapefiles being used
        strHabUnit = arcpy.Describe(fnHabOut).spatialReference.linearUnitName
        strNetUnit = arcpy.Describe(fnNetOut).spatialReference.linearUnitName
        if strHabUnit == "":
            strHabUnit = "undefined"
        if strNetUnit == "":
            strNetUnit = "undefined"
        
        # Write the habitat and network area info to a csv file
        fOut = open(pthCsv, "w")
        fOut.write("Network,,Home,\nID,Area (%s^2),Count,Area (%s^2)\n" %(strHabUnit,strNetUnit))
        for ID in dicNet.keys():
            fOut.write("%s,%s,%s\n" %(ID,dicNet[ID],",".join([str(x) for x in dicHab[ID]])))
        fOut.close()

    # Message box to confirm that the analysis is complete
    tkMessageBox.showinfo("Finised", "Habitat network tool has finished running")
    
    return



def tmp(extension):
    """Generates a unique filename in the scratch folder using arcpy"""
    try:
        # Only works for ArcGIS 10.1+
        scratch = arcpy.env.scratchFolder
    except:
        # Should be a fix for ArcGIS 10.0
        scratch = os.path.join(tempfile.gettempdir(), "scratch")
        if not os.path.exists(scratch):
            os.mkdir(scratch)
    return arcpy.CreateUniqueName("tmp." + extension, scratch)



# Run the app
if __name__ == "__main__":
    app = BeetleGUI(None)
    app.title('Habitat network tool')
    app.mainloop()
    
