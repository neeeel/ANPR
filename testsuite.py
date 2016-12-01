import unittest2
import utilities
import datetime
import anprregex

class utilitiesTest(unittest2.TestCase):

    def testUtilities(self):
        self.assertTrue(utilities.bin_time(datetime.timedelta(seconds=100))==datetime.timedelta(seconds=90))
        self.assertTrue(utilities.bin_time(datetime.timedelta(seconds=0)) == datetime.timedelta(seconds=0))


    def testOther(self):
        pass

class regexTest(unittest2.TestCase):

    def setUp(self):
        self.plate1 = ['Plate 1', 'Car', [('13:22:45', '9', 'I'), ('13:25:17', '18', 'B'), ('14:03:22', '10', 'B'), ('18:15:44', '18', 'O'), ('18:15:44', '12', 'I')]]
        self.plate2 = ["Plate 2", "Car",[('18:15:44', '18', 'B'), ('13:25:15', '18', 'B'), ('14:03:51', '10', 'I')]]
        self.plate3 = ["Plate 2", "Car", [('18:15:44', '18', 'I'), ('13:25:15', '18', 'B'), ('14:03:51', '10', 'I'),('18:15:44', '18', 'B'), ('13:25:15', '18', 'B'), ('14:03:51', '10', 'O')]]
        self.plate4 = ["Plate 2", "Car", [('18:15:44', '18', 'B'), ('13:25:15', '18', 'B')]]
        self.regexes = ["I-B-O","I-B*-O","I-B-B*-O","¬I-B*-I","I-B-¬O","I-¬I*","I-18-10|9","I-18|10*","^B-B!"]

    def test_matches(self):
        ### plate1
        self.assertTrue(len(anprregex.match(self.plate1[2],self.regexes[0])) ==0)
        self.assertTrue(len(anprregex.match(self.plate1[2],self.regexes[1])) == 1)
        self.assertTrue(len(anprregex.match(self.plate1[2], self.regexes[2])) == 1)
        self.assertTrue(len(anprregex.match(self.plate1[2], self.regexes[3])) == 1)
        self.assertTrue(len(anprregex.match(self.plate1[2], self.regexes[4])) == 1)
        self.assertTrue(len(anprregex.match(self.plate1[2], self.regexes[5])) == 3)
        self.assertTrue(len(anprregex.match(self.plate1[2], self.regexes[6])) == 1)
        self.assertTrue(len(anprregex.match(self.plate1[2], self.regexes[7])) == 3)


        ### plate2
        self.assertTrue(len(anprregex.match(self.plate2[2], self.regexes[0])) == 0)
        self.assertTrue(len(anprregex.match(self.plate2[2], self.regexes[1])) == 0)
        self.assertTrue(len(anprregex.match(self.plate2[2], self.regexes[2])) == 0)
        self.assertTrue(len(anprregex.match(self.plate2[2], self.regexes[3])) == 2)
        self.assertTrue(len(anprregex.match(self.plate2[2], self.regexes[4])) == 0)
        self.assertTrue(len(anprregex.match(self.plate2[2], self.regexes[5])) == 0)
        self.assertTrue(len(anprregex.match(self.plate2[2], self.regexes[6])) == 0)

        ### plate3
        self.assertTrue(len(anprregex.match(self.plate3[2], self.regexes[0])) == 0)
        self.assertTrue(len(anprregex.match(self.plate3[2], self.regexes[1])) == 1)
        self.assertTrue(len(anprregex.match(self.plate3[2], self.regexes[2])) == 1)
        self.assertTrue(len(anprregex.match(self.plate3[2], self.regexes[3])) == 1)
        self.assertTrue(len(anprregex.match(self.plate3[2], self.regexes[4])) == 2)
        self.assertTrue(len(anprregex.match(self.plate3[2], self.regexes[5])) == 4)
        self.assertTrue(len(anprregex.match(self.plate3[2], self.regexes[6])) == 1)
        self.assertTrue(len(anprregex.match(self.plate3[2], self.regexes[7])) == 8)

        #plate4

        self.assertTrue(len(anprregex.match(self.plate4[2], self.regexes[8])) == 1)



if __name__ == '__main__':
    unittest2.main()