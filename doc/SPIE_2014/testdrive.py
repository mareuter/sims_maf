from lsst.sims.maf.driver.mafConfig import makeBinnerConfig, makeMetricConfig, makeDict
import lsst.sims.maf.utils as utils

# Configure the output directory.
root.outputDir = './Mafout'


# Configure our database access information.
root.dbAddress= {'dbAddress':'mysql://lsst:lsst@localhost/opsim?unix_socket=/opt/local/var/run/mariadb/mysqld.sock',
                   'outputTable':'output_opsim3_61'}
root.opsimName = 'opsim3.61'
#root.dbAddress = {'dbAddress':'sqlite:///opsimblitz2_1060_sqlite.db'}
#root.opsimName = 'opsimblitz2_1060'

# Some parameters to help control the plotting ranges below.
nVisits_plotRange = {'g':[50,220], 'r':[150, 310]}

# Use a MAF utility to determine the expected design and stretch goals for number of visits, etc.
design, stretch = utils.scaleStretchDesign(10)
mag_zpoints = design['coaddedDepth']

# Some parameters we're using below.
nside = 128
nvisits = 10

# A list to save the configuration parameters for our Slicers + Metrics.
binList=[]

# Loop through r and i filters, to do some simple analysis.
filters = ['r', 'i']
colors = {'r':'b', 'i':'y'}
linestyles = {'r':':', 'i':'-'}
for f in filters:
    # Configure a metric that will calculate the mean of the seeing and print the result to our summary stats file.
    m1 = makeMetricConfig('MeanMetric', params=['seeing'], summaryStats={'IdentityMetric':{}})
    # Configure a metric that will calculate the rms of the seeing and print the result to our summary stats file.
    m2 = makeMetricConfig('RmsMetric', params=['seeing'], summaryStats={'IdentityMetric':{}})
    # Combine these metrics with the UniSlicer and a SQL constraint based on the filter, so
    #  that we will now calculate the mean and rms of the seeing for all r band visits
    #  (and then the mean and rms of the seeing for all i band visits).
    binner = makeBinnerConfig('UniBinner', metricDict=makeDict(m1, m2), constraints=['filter = "%s"' %(f)])
    # Add this configured binner (carrying the metric information and the sql constraint) into a list.
    binList.append(binner)
    # Configure a metric + a OneDSlicer so that we can count how many visits have seeing in each interval of
    #  the OneDSlicer. 
    m1 = makeMetricConfig('CountMetric', params=['airmass'], kwargs={'metricName':'Airmass'},
                          plotDict={'xlabel':'Airmass'},
                          # Set up a additional histogram so that the outputs of these count metrics in each
                          #   filter get combined into a single plot (with both r and i band). 
                          histMerge = {'histNum':1, 'legendloc':'upper right', 'label':'%s band' %(f),
                                       'xlabel':'Airmass', 'color':colors[f], 'linestyle':linestyles[f]})
    # Set up the OneDSlicer, including setting the interval size.
    binner = makeBinnerConfig('OneDBinner', kwargs={'sliceDataColName':'airmass'},
                              setupKwargs={'binsize':.02},
                              metricDict=makeDict(m1), constraints=['filter = "%s"' %(f)])
    binList.append(binner)


# Loop through the different dither options.
dithlabels = [' No dithering', ' Random dithering', ' Hex dithering']
binnerNames = ['HealpixBinner' ,'HealpixBinnerRandom', 'HealpixBinnerDither'] 
for dithlabel, binnerName in zip(dithlabels, binnerNames):
    # Set up parameters for binner, depending on what dither pattern we're using.
    if binnerName == 'HealpixBinner':
        binnerName = 'HealpixBinner'
        binnerkwargs = {'nside':nside}
        binnermetadata = 'No dither'
    elif binnerName == 'HealpixBinnerDither':
        binnerName = 'HealpixBinner'
        binnerkwargs = {'nside':nside, 'spatialkey1':'hexdithra', 'spatialkey2':'hexdithdec'}
        binnermetadata = 'Hex dither'
    elif binnerName == 'HealpixBinnerRandom':
        binnerName = 'HealpixBinner'
        binnerkwargs = {'nside':nside, 'spatialkey1':'randomRADither', 'spatialkey2':'randomDecDither'}
        binnermetadata = 'Random dither'
    # Configure QuickRevisit metric to count number times we have more than X visits within a night.
    m1 = makeMetricConfig('QuickRevisitMetric', kwargs={'nVisitsInNight':nvisits}, 
                        plotDict={'plotMin':0, 'plotMax':20, 'histMin':0, 'histMax':100,
                                  'xlabel':'Number of nights with more than %d visits' %(nvisits)},
                        summaryStats={'MeanMetric':{}, 'MedianMetric':{}, 'RobustRmsMetric':{}, 'RmsMetric':{}},
                        # Add it to a 'merged' histogram, which will combine metric values from
                        #  all dither patterns.
                        histMerge={'histNum':2, 'legendloc':'upper right', 'label':dithlabel,
                                    'histMin':0, 'histMax':50, 
                                    'xlabel':'Number of Nights with more than %d visits' %(nvisits),
                                    'bins':50})
    # Configure Proper motion metric to analyze expected proper motion accuracy.
    m2 = makeMetricConfig('ProperMotionMetric', kwargs={'m5Col':'5sigma_modified', 'seeingCol':'seeing',
                                                        'metricName':'Proper Motion @20 mag'},
                        plotDict={'percentileClip':95, 'plotMin':0, 'plotMax':2.0},
                        summaryStats={'MeanMetric':{}, 'MedianMetric':{}, 'RobustRmsMetric':{}, 'RmsMetric':{}},
                        histMerge={'histNum':3, 'legendloc':'upper right', 'label':dithlabel,
                                   'histMin':0, 'histMax':1.5}
    # Configure another proper motion metric where input star is r=24 rather than r=20.
    m3 = makeMetricConfig('ProperMotionMetric', kwargs={'m5Col':'5sigma_modified', 'seeingCol':'seeing',
                                                        'rmag':24, 'metricName':'Proper Motion @24 mag'},
                        plotDict={'percentileClip':95, 'plotMin':0, 'plotMax':2.0},
                        summaryStats={'MeanMetric':{}, 'MedianMetric':{}, 'RobustRmsMetric':{}, 'RmsMetric':{}},
                        histMerge={'histNum':4, 'legendloc':'upper left', 'label':dithlabel,
                                   'histMin':0, 'histMax':1.5}
    # Configure a Healpix slicer that uses either the opsim original pointing, or one of the dithered RA/Dec values.
    binner = makeBinnerConfig(binnerName, kwargs=binnerkwargs, 
                          metricDict=makeDict(m1, m2, m3), constraints=[''], metadata = dithlabel)
    # Add this configured binner (which carries the metrics and sql constraints with it) to our list.
    binList.append(binner)

    # Loop through filters g and r and calculate number of visits and coadded depth in these filters
    for f in ['g', 'r']:
        # Reset histNum to be 5 or 6 depending on filter
        #   (so same filter, different dithered slicers end in same merged histogram)
        if f == 'g':
            histNum = 5
        elif f == 'r':
            histNum = 7
        # Configure a metric to count the number of visits in this band.
        m1 = makeMetricConfig('CountMetric', params=['expMJD'], kwargs={'metricName':'Nvisits %s band' %(f)},
                              plotDict={'units':'Number of Visits', 'cbarFormat':'%d',
                                      'plotMin':nVisits_plotRange[f][0],
                                      'plotMax':nVisits_plotRange[f][1],
                                      'histMin':nVisits_plotRange[f][0],
                                      'histMax':nVisits_plotRange[f][1]},
                                summaryStats={'MeanMetric':{}, 'MedianMetric':{}, 'RobustRmsMetric':{}, 'RmsMetric':{}},
                                histMerge={'histNum':histNum, 'legendloc':'upper right',
                                           'histMin':nVisits_plotRange[f][0],
                                           'histMax':nVisits_plotRange[f][1],
                                           'label':dithlabel,
                                           'bins':(nVisits_plotRange[f][1]-nVisits_plotRange[f][0])})
        histNum += 1
        # Configure a metric to count the coadded m5 depth in this band.
        m2 = makeMetricConfig('Coaddm5Metric', kwargs={'m5col':'5sigma_modified',
                                                       'metricName':'Coadded m5 %s band' %(f)},
                                plotDict={'zp':mag_zpoints[f],
                                          'percentileClip':95., 'plotMin':-1.5, 'plotMax':0.75,
                                          'units':'Co-add (m5 - %.1f)'%mag_zpoints[f]},
                                summaryStats={'MeanMetric':{}, 'MedianMetric':{}, 'RobustRmsMetric':{}, 'RmsMetric':{}},
                                histMerge={'histNum':histNum, 'legendloc':'upper left', 'bins':150,
                                            'label':dithlabel, 'histMin':24.5, 'histMax':28.5})
        # Configure the binner for these two metrics
        #  (separate from healpix slicer above because of filter constraint).
        binner = makeBinnerConfig(binnerName, kwargs=binnerkwargs, 
                            metricDict=makeDict(m1, m2), constraints=['filter="%s"'%(f)],
                            metadata = dithlabel)
        binList.append(binner)

root.binners=makeDict(*binList)
