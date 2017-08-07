from __future__ import print_function
import sys
import pickle

class correct:
    def __init__(self, debug):
        # self.corrected = {}
        self.wfgram = {}
        if debug:
            self.debug = True
        else:
            self.debug = False
        if self.debug:
            print("Initializing")
        self.sig2gabra = {
                'PRF' : '"perf",',
                'IPFV' : '"impf",',
                'IMP' : '"imp",'
                }

    def find_wordform(self, dataArray):
        i = 0
        # test to make sure there's only one
        # print('wordform data array', dataArray)
        wordforms = []
        for element in dataArray:
            if element == '"surface_form"': wordforms.append(dataArray[i+2])
            i += 1
        # print('data array:', dataArray)
        # print('wordform array', wordforms)
        # Sometimes there are blank entries in Gabra
        if len(wordforms) != 1:
            assert(len(wordforms)) == 0
            if self.debug:
                print('SKIPPED', dataArray)
            return 'SKIP'
        else:
            assert(len(wordforms) == 1)
            return wordforms[0]

    def pull_field(self, dataArray, start_i):
        """
        pull the data between the nearest { and }
        """
        # if self.debug:
        #     print("starting index", start_i)
        #     print('data array\n', dataArray)
        #     print('data array at starting index', dataArray[start_i])
        assert(dataArray[start_i] in ['{', 'null,', 'null'])
        featArray = []
        if dataArray[start_i] in ['null,', 'null']:
            featArray.append('null')
        else:
            for feat in dataArray[start_i:]:
                if feat not in ['},', '}']:
                    featArray.append(feat)
                elif feat in ['},', '}']:
                    break
        return featArray

    def find_args(self, dataArray):
        i = 0
        # test to make sure there's only one
        feats = {}
        for element in dataArray:
            if element in ['"subject"', '"ind_obj"', '"dir_obj"']:
                feats[element] = []
                # if self.debug:
                #     print('currently searching for',element, 'feats')
                for feat in self.pull_field(dataArray, i + 2):
                    feats[element].append(feat)
            i += 1
        # if self.debug:
        #     print('returning feats\n', feats, '\n')
        return feats

    def select(self, sigdata, gabradata):
        # egrep -o "ARG..[0-9][SPMF]+" ../test.maltese/data/maltese-task1-train | sort | uniq
        # ARGAC1P
        # ARGAC1S
        # ARGAC2P
        # ARGAC2S
        # ARGAC3P
        # ARGAC3SF
        # ARGAC3SM = '"dir_obj"', ':', '{', '"person"', ':', '"p3",', '"number"', ':', '"sg",', '"gender"', ':', '"m"'
        # ARGDA1P
        # ARGDA1S
        # ARGDA2P
        # ARGDA2S
        # ARGDA3P
        # ARGDA3SF
        # ARGDA3SM = '"ind_obj"', ':', '{', '"person"', ':', '"p3",', '"number"', ':', '"sg",', '"gender"', ':', '"m"'
        # ARGNO1P
        # ARGNO1S
        # ARGNO2P
        # ARGNO2S
        # ARGNO3P = '"subject"', ':', '{', '"person"', ':', '"p2",', '"number"', ':', '"pl"'
        # ARGNO3SF
        # ARGNO3SM
        """
                sep on ',' (args = 4), then on '+' (should be < 0)
        """
        # Parse sigdata string
        argparse = {
            "NO" : '"subject"',
            "AC" : '"dir_obj"',
            "DA" : '"ind_obj"',
            "1" : '"p1"',
            "2" : '"p2"',
            "3" : '"p3"',
            "M" : '"m"',
            "F" : '"f"',
            "P" : '"pl"',
            "S" : '"sg"'
        }
        # get aspect as default
        # for feats in sigdata[1].split(','):
            # if feats[0:6] == 'aspect':
                # aspect = feats.split('=')[1]
                # if self.debug:
                    # print("ASPECT:", aspect, self.sig2gabra[aspect])
        # notgab = []
        # for gd in gabradata:
            # if self.sig2gabra[aspect] not in gd:
                # notgab.append(gabradata.index(gd))
        # if self.debug:
            # print("SHOULD NOT BE", notgab)
        total_poss = len(gabradata)
        poss = {}
        for i in range(total_poss):
            poss[i] = self.find_args(gabradata[i])
        if self.debug:
            print("TOTAL POSSIBILITIES:", total_poss)
        # for maybe in poss:
        #     print('\t', maybe, poss[maybe])
        sigdata = sigdata[1].split(',')[3].replace('arg=', '').split('+')
        if self.debug:
            print("ARGS BEFORE PARSING", sigdata)
        assert(len(sigdata) > 0)
        args = []
        for arg in sigdata:
            arglist = []
            # remove ARG prefix
            arg = arg[3:]
            # print(arg)
            argtype = arg[0:2]
            arglist.append(argparse[argtype])
            argnum = arg[2]
            arglist.append(argparse[argnum])
            argsp = arg[3]
            arglist.append(argparse[argsp])
            # print(argtype, argnum, argsp)
            singular = False
            if argsp == 'S' and arg[3] != arg[-1]:
                arggen = arg[4]
                singular = True
                arglist.append(argparse[arggen])
            args.append(arglist)
        if self.debug:
            print("ARGS", args)
        # decide
        choice = 1000
        for maybe in poss:
            for arg in args:
                if arg[0] in poss[maybe]:
                    for all in arg[1:]:
                        if all in poss[maybe][arg[0]]:
                            # if maybe not in notgab:
                            # choice.append(maybe)
                            choice = maybe
        if self.debug:
            print("CHOICE IS:", choice)
        if choice == 1000:
             # -- default is 0
            choice = 0
        # return gabradata[0]
        return gabradata[choice]
            
    def correct(self, sigdata, gabradata):
        # sigdata = sigdata.split()
        gabradata = self.select(sigdata, gabradata)
        source = sigdata[0]
        targFeats = sigdata[1].split(',')
        targFeats = self.check_trans(targFeats, gabradata)
        target = sigdata[2]
        newFeats = []
        for tf in targFeats:
            if tf in ['aspect=PRF', 'aspect=IPFV', 'aspect=IMP']:
                change = False
                for gb in gabradata:
                    if gb == '"aspect"':
                        if self.debug:
                            print("GB = ", gb)
                            print("GB + 2 =", gabradata[gabradata.index(gb) + 2])
                        aspect  = gabradata[gabradata.index(gb) + 2].replace(",", '').strip()
                        if aspect in ['"Impf"', '"impf"']:
                            newFeats.append('aspect=IPFV')
                        elif aspect in ['"Imp"', '"imp"']:
                            newFeats.append('aspect=IMP')
                        elif aspect in ['"Perf"', '"perf"']:
                            newFeats.append('aspect=PRF')
                        else:
                            if self.debug:
                                print("going with original annotation")
                            newFeats.append(tf)
                    else:
                        if tf not in newFeats:
                            if self.debug:
                                print("ADDING", tf)
                            newFeats.append(tf)
            elif tf != 'mood=IMP':
                newFeats.append(tf)
        if self.debug:
            print('old feats', targFeats)
            print('new feats', newFeats)
        newfeats = ','.join(newFeats)
        return '\t'.join([source, newfeats, target])

    def check_trans(self, sigdata, gabradata):
        """Simple valence repair"""
        if self.debug:
            print("CHECKING VALENCE")
        for feat in sigdata:
            if feat[:3] == 'val':
                val = feat
        if self.debug:
            print("\tprevious valence", val)
        # args = self.find_args(gabradata)
        args = ','.join(sigdata).split('+')
        valence = len(args)
        if self.debug:
            print("\tvalence count =", valence)
        assert(valence > 0)
        if valence == 1:
            sigdata = self.list_replace(sigdata, 'val=INTR', val)
        elif valence == 2:
            sigdata = self.list_replace(sigdata, 'val=TR', val)
        elif valence == 3:
            sigdata = self.list_replace(sigdata, 'val=DITR', val)
        else:
            print("THIS IS AN ERROR! VALENCE > 3")
        if self.debug:
            print("\tnow outputting:", sigdata)
        return sigdata

    def list_replace(self, datalist, value, oldvalue):
        datalist = ','.join(datalist)
        if self.debug:
            print("\tbefore replacing", datalist)
        datalist = datalist.replace(oldvalue, value)
        if self.debug:
            print("\tafter replacing", datalist)
        return datalist.split(',')

    def readgab(self, gabradata):
        if gabradata[-4:] == '.pkl':
            self.wfgram = pickle.load(open(gabradata, 'rb'))
        else:
            for line in open(gabradata, 'r').readlines():
                dataArray = line.strip().split()
                wordform = self.find_wordform(dataArray).replace('"', '').replace(',', '')
                if wordform not in self.wfgram:
                    self.wfgram[wordform] = []
                # feats = self.find_args(dataArray)
                # self.wfgram[wordform].append(feats)
                self.wfgram[wordform].append(dataArray)
                # if self.debug:
                #     print('wordform', wordform)
                    # for feat in feats:
                    #     print('\tfeat:', feat)
                    #     print('\t', feats[feat])
            pickle.dump(self.wfgram, open('wordforms.pkl', 'wb'))

    def notfound(self, sigdata):
        # TODO 387 are not found. Not sure why. Still not sure how
        # the SIGMORPHON group build this data---not in wordforms.bson
        source = sigdata[0]
        feats = sigdata[1]
        target = sigdata[2]
        feats = feats.replace(',mood=IMP', '')
        return('\t'.join([source, feats, target]))


    def match(self, sigdata):
        oov = 0
        for line in open(sigdata, 'r'):
            line = line.split()
            sigwf = line[-1]
            if self.debug:
                print('sigwf', sigwf)
            if sigwf in self.wfgram:
                if self.debug:
                    print('line', line)
                    for candidate in self.wfgram[sigwf]:
                        print('\t', candidate)
                print(self.correct(line, self.wfgram[sigwf]))
            else:
                # this should always return 0
                # if it doesn't, figure out why
                oov += 0
                print(self.notfound(line))
        if self.debug:
            print("Total OOVs:", oov)

if __name__ == '__main__':
    if sys.argv[-1] == '--debug':
        debug = True
    else:
        debug = False
    c = correct(debug)
    c.readgab(sys.argv[1])
    c.match(sys.argv[2])
