import matplotlib
matplotlib.use("Agg")
import numpy as np
import unittest
import lsst.sims.maf.metrics as metrics
import lsst.sims.maf.slicers as slicers
import lsst.sims.maf.metricBundles as metricBundle

# Test vector metrics

class Test2D(unittest.TestCase):

    def setUp(self):
        names = ['night', 'fieldID', 'fieldRA', 'fieldDec', 'fiveSigmaDepth', 'expMJD']
        types = [int,int,float,float,float,float]

        self.m5_1 = 25.
        self.m5_2 = 24.

        self.n1 = 50
        self.n2 = 49

        # Picking RA and Dec values that will hit nside=16 healpixels
        self.simData = np.zeros(self.n1+self.n2, dtype=zip(names,types))
        self.simData['night'][0:self.n1] = 1
        self.simData['fieldID'][0:self.n1] = 1
        self.simData['fieldRA'][0:self.n1] = np.radians(10.)
        self.simData['fieldDec'][0:self.n1] = 0
        self.simData['fiveSigmaDepth'][0:self.n1] = self.m5_1

        self.simData['night'][self.n1:] = 2
        self.simData['fieldID'][self.n1:] = 2
        self.simData['fieldRA'][self.n1:] = np.radians(190.)
        self.simData['fieldDec'][self.n1:] = np.radians(-20.)
        self.simData['fiveSigmaDepth'][self.n1:] = self.m5_2

        self.fieldData = np.zeros(2, dtype=zip(['fieldID', 'fieldRA', 'fieldDec'],[int,float,float]))
        self.fieldData['fieldID'] = [1,2]
        self.fieldData['fieldRA'] = np.radians([10.,190.])
        self.fieldData['fieldDec'] = np.radians([0.,-20.])

        self.simData['expMJD'] = self.simData['night']

    def testOpsim2dSlicer(self):
        metric = metrics.AccumulateCountMetric(bins=[0.5,1.5,2.5])
        slicer = slicers.OpsimFieldSlicer()
        sql = ''
        mb = metricBundle.MetricBundle(metric,slicer,sql)
        mbg = metricBundle.MetricBundleGroup({0:mb}, None)
        mbg.setCurrent('')
        mbg.fieldData = self.fieldData
        mbg.runCurrent('', simData=self.simData)
        expected = np.array( [[self.n1,   self.n1],
                              [-666.,   self.n2]])
        assert(np.array_equal(mb.metricValues.data, expected))

    def testHealpix2dSlicer(self):
        metric = metrics.AccumulateCountMetric(bins=[0.5,1.5,2.5])
        slicer = slicers.HealpixSlicer(nside=16)
        sql = ''
        mb = metricBundle.MetricBundle(metric,slicer,sql)
        mbg = metricBundle.MetricBundleGroup({0:mb}, None)
        mbg.setCurrent('')
        mbg.runCurrent('', simData=self.simData)

        good = np.where(mb.metricValues.mask[:,-1] == False)[0]
        expected =  np.array( [[self.n1,   self.n1],
                              [-666.,   self.n2]])
        assert(np.array_equal(mb.metricValues.data[good,:], expected))

    def testHistogramMetric(self):
        metric = metrics.HistogramMetric(bins=[0.5,1.5,2.5])
        slicer = slicers.HealpixSlicer(nside=16)
        sql = ''
        mb = metricBundle.MetricBundle(metric,slicer,sql)
        mbg = metricBundle.MetricBundleGroup({0:mb}, None)
        mbg.setCurrent('')
        mbg.runCurrent('', simData=self.simData)

        good = np.where(mb.metricValues.mask[:,-1] == False)[0]
        expected =  np.array( [[self.n1,   0.],
                              [0.,   self.n2]])

        assert(np.array_equal(mb.metricValues.data[good,:], expected))

        # Check that I can run a different statistic
        metric = metrics.HistogramMetric(col='fiveSigmaDepth',
                                         statistic='sum',
                                         bins=[0.5,1.5,2.5])
        mb = metricBundle.MetricBundle(metric,slicer,sql)
        mbg = metricBundle.MetricBundleGroup({0:mb}, None)
        mbg.setCurrent('')
        mbg.runCurrent('', simData=self.simData)
        expected = np.array( [[self.m5_1*self.n1, 0.],
                              [0., self.m5_2*self.n2]])
        assert(np.array_equal(mb.metricValues.data[good,:], expected))

    def testAccumulateMetric(self):
        metric=metrics.AccumulateMetric(col='fiveSigmaDepth', bins=[0.5,1.5,2.5])
        slicer = slicers.HealpixSlicer(nside=16)
        sql = ''
        mb = metricBundle.MetricBundle(metric,slicer,sql)
        mbg = metricBundle.MetricBundleGroup({0:mb}, None)
        mbg.setCurrent('')
        mbg.runCurrent('', simData=self.simData)
        good = np.where(mb.metricValues.mask[:,-1] == False)[0]
        expected =  np.array( [[self.n1*self.m5_1, self.n1*self.m5_1],
                              [-666.,  self.n2* self.m5_2]])
        assert(np.array_equal(mb.metricValues.data[good,:], expected))

    def testHistogramM5Metric(self):
        metric = metrics.HistogramM5Metric(bins=[0.5,1.5,2.5])
        slicer = slicers.HealpixSlicer(nside=16)
        sql = ''
        mb = metricBundle.MetricBundle(metric,slicer,sql)
        mbg = metricBundle.MetricBundleGroup({0:mb}, None)
        mbg.setCurrent('')
        mbg.runCurrent('', simData=self.simData)
        good = np.where( (mb.metricValues.mask[:,0] == False) |
                         (mb.metricValues.mask[:,1] == False))[0]

        checkMetric = metrics.Coaddm5Metric()
        tempSlice = np.zeros(self.n1, dtype=zip(['fiveSigmaDepth'],[float]))
        tempSlice['fiveSigmaDepth'] += self.m5_1
        val1 = checkMetric.run(tempSlice)
        tempSlice = np.zeros(self.n2, dtype=zip(['fiveSigmaDepth'],[float]))
        tempSlice['fiveSigmaDepth'] += self.m5_2
        val2 =  checkMetric.run(tempSlice)


        expected =  np.array( [[val1, -666.],
                              [-666.,  val2]])
        assert(np.array_equal(mb.metricValues.data[good,:], expected))

    def testAccumulateM5Metric(self):
        metric = metrics.AccumulateM5Metric(bins=[0.5,1.5,2.5])
        slicer = slicers.HealpixSlicer(nside=16)
        sql = ''
        mb = metricBundle.MetricBundle(metric,slicer,sql)
        mbg = metricBundle.MetricBundleGroup({0:mb}, None)
        mbg.setCurrent('')
        mbg.runCurrent('', simData=self.simData)
        good = np.where(mb.metricValues.mask[:,-1] == False)[0]

        checkMetric = metrics.Coaddm5Metric()
        tempSlice = np.zeros(self.n1, dtype=zip(['fiveSigmaDepth'],[float]))
        tempSlice['fiveSigmaDepth'] += self.m5_1
        val1 = checkMetric.run(tempSlice)
        tempSlice = np.zeros(self.n2, dtype=zip(['fiveSigmaDepth'],[float]))
        tempSlice['fiveSigmaDepth'] += self.m5_2
        val2 =  checkMetric.run(tempSlice)

        expected =  np.array( [[val1, val1],
                              [-666., val2 ]])
        assert(np.array_equal(mb.metricValues.data[good,:], expected))

    def testAccumulateUniformityMetric(self):
        names = ['night']
        types = ['float']
        dataSlice = np.zeros(3652, dtype=zip(names,types))

        # Test that a uniform distribution is very close to zero
        dataSlice['night'] = np.arange(1,dataSlice.size+1)
        metric=metrics.AccumulateUniformityMetric()
        result = metric.run(dataSlice)
        assert( np.max(result) < 1./365.25)
        assert(np.min(result) >= 0)

        # Test that if everythin on night 1 or last night, then result is ~1
        dataSlice['night'] = 1
        result = metric.run(dataSlice)
        assert(np.max(result) >= 1.-1./365.25)
        dataSlice['night'] = 3652
        result = metric.run(dataSlice)
        assert(np.max(result) >= 1.-1./365.25)

        # Test if all taken in the middle, result ~0.5
        dataSlice['night'] = 3652/2
        result = metric.run(dataSlice)
        assert(np.max(result) >= 0.5-1./365.25)


    def testRunRegularToo(self):
        """
        Test that a binned slicer and a regular slicer can run together
        """
        bundleList = []
        metric = metrics.AccumulateM5Metric(bins=[0.5,1.5,2.5])
        slicer = slicers.HealpixSlicer(nside=16)
        sql = ''
        bundleList.append(metricBundle.MetricBundle(metric,slicer,sql))
        metric = metrics.Coaddm5Metric()
        slicer = slicers.HealpixSlicer(nside=16)
        bundleList.append(metricBundle.MetricBundle(metric,slicer,sql))
        bd = metricBundle.makeBundlesDictFromList(bundleList)
        mbg = metricBundle.MetricBundleGroup(bd, None)
        mbg.setCurrent('')
        mbg.runCurrent('', simData=self.simData)

        assert(np.array_equal(bundleList[0].metricValues[:,1].compressed(),
                              bundleList[1].metricValues.compressed()))


if __name__ == "__main__":
    unittest.main()