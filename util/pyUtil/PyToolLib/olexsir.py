#!/usr/bin/python
# -*- coding: utf8 -*-
######## LICENCE ################################################################{{{
##
## olexsir.py is licenced under 3-Clause BSD license for olex2.
## 
##    1. Redistributions of source code must retain the above copyright notice,
##       this list of conditions and the following disclaimer.
##    2. Redistributions in binary form must reproduce the above copyright 
##       notice, this list of conditions and the following disclaimer in the 
##       documentation and/or other materials provided with the distribution.
##    3. The name of the author may not be used to endorse or promote products 
##       derived from this software without specific prior written permission.
## 
## THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED 
## WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
## MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO 
## EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##
################################################################################
#}}}

from os import path

class Sir(object):#{{{

    def __init__(self):#{{{
        self._sirgui = True
        self._data = {}
        self._invariants = {}
        self._phase = {}
#}}}
    def _ckDirects(self):#{{{
        import re
        from cctbx import sgtbx

        data = self._data.copy()
        inv = self._invariants.copy()
        phase = self._phase.copy()
        isFileHasExt = lambda filepath, ext: path.isfile(filepath)\
                and filepath.lower().split('.')[-1] in ext
        validTrue = (True, 'true', 'True', 1, '1')
        sizestr = ('xs', 's', 'm', 'l', 'xl', 'xxl')
#        spcgrs = ('P1', 'C1', 'P-1', 'P2', 'P112', 'P211', 'P21', 'P1121',
#                'P2111', 'C2', 'A2', 'I2', 'A112', 'B112', 'I112', 'B211', 'C211', 'I211', 'Pm',
#                'P11m', 'Pm11', 'Pc', 'Pn', 'Pa', 'P11a', 'P11n', 'P11b', 'Pb11', 'Pn11',
#                'Pc11', 'Cm', 'Am', 'Im', 'A11m', 'B11m', 'I11m', 'Bm11', 'Cm11', 'Im11', 'Cc',
#                'An', 'Ia', 'Aa', 'Cn', 'Ic', 'A11a', 'B11n', 'I11b', 'B11b', 'A11n', 'I11a',
#                'Bb11', 'Cn11', 'Ic11', 'Cc11', 'Bn11', 'Ib11', 'P2/m', 'P112/m', 'P2/m11',
#                'P21/m', 'P1121/m', 'P21/m11', 'C2/m', 'A2/m', 'I2/m', 'A112/m', 'B112/m',
#                'I112/m', 'B2/m11', 'C2/m11', 'I2/m11', 'P2/c', 'P2/n', 'P2/a', 'P112/a',
#                'P112/n', 'P112/b', 'P2/b11', 'P2/n11', 'P2/c11', 'P21/c', 'P21/n', 'P21/a',
#                'P1121/a', 'P1121/n', 'P1121/b', 'P21/b11', 'P21/n11', 'P21/c11', 'C2/c',
#                'A2/n', 'I2/a', 'A2/a', 'C2/n', 'I2/c', 'A112/a', 'B112/n', 'I112/b', 'B112/b',
#                'A112/n', 'I112/a', 'B2/b11', 'C2/n11', 'I2/c11', 'C2/c11', 'B2/n11', 'I2/b11',
#                'P222', 'P2221', 'P2122', 'P2212', 'P21212', 'P22121', 'P21221', 'P212121',
#                'C2221', 'A2122', 'B2212', 'C222', 'A222', 'B222', 'F222', 'I222', 'I212121',
#                'Pmm2', 'P2mm', 'Pm2m', 'Pmc21', 'Pcm21', 'P21ma', 'P21am', 'Pb21m', 'Pm21b',
#                'Pcc2', 'P2aa', 'Pb2b', 'Pma2', 'Pbm2', 'P2mb', 'P2cm', 'Pc2m', 'Pm2a', 'Pca21',
#                'Pbc21', 'P21ab', 'P21ca', 'Pc21b', 'Pb21a', 'Pnc2', 'Pcn2', 'P2na', 'P2an',
#                'Pb2n', 'Pn2b', 'Pmn21', 'Pnm21', 'P21mn', 'P21nm', 'Pn21m', 'Pm21n', 'Pba2',
#                'P2cb', 'Pc2a', 'Pna21', 'Pbn21', 'P21nb', 'P21cn', 'Pc21n', 'Pn21a', 'Pnn2',
#                'P2nn', 'Pn2n', 'Cmm2', 'A2mm', 'Bm2m', 'Cmc21', 'Ccm21', 'A21ma', 'A21am',
#                'Bb21m', 'Bm21b', 'Ccc2', 'A2aa', 'Bb2b', 'Amm2', 'Bmm2', 'B2mm', 'C2mm',
#                'Cm2m', 'Am2m', 'Abm2', 'Bma2', 'B2cm', 'C2mb', 'Cm2a', 'Ac2m', 'Ama2', 'Bbm2',
#                'B2mb', 'C2cm', 'Cc2m', 'Am2a', 'Aba2', 'Bba2', 'B2cb', 'C2cb', 'Cc2a', 'Ac2a',
#                'Fmm2', 'F2mm', 'Fm2m', 'Fdd2', 'F2dd', 'Fd2d', 'Imm2', 'I2mm', 'Im2m', 'Iba2',
#                'I2cb', 'Ic2a', 'Ima2', 'Ibm2', 'I2mb', 'I2cm', 'Ic2m', 'Im2a', 'Pmmm', 'Pnnn',
#                'Pccm', 'Pmaa', 'Pbmb', 'Pban', 'Pncb', 'Pcna', 'Pmma', 'Pmmb', 'Pbmm', 'Pcmm',
#                'Pmcm', 'Pmam', 'Pnna', 'Pnnb', 'Pbnn', 'Pcnn', 'Pncn', 'Pnan', 'Pmna', 'Pnmb',
#                'Pbmn', 'Pcnm', 'Pncm', 'Pman', 'Pcca', 'Pccb', 'Pbaa', 'Pcaa', 'Pbcb', 'Pbab',
#                'Pbam', 'Pmcb', 'Pcma', 'Pccn', 'Pnaa', 'Pbnb', 'Pbcm', 'Pcam', 'Pmca', 'Pmab',
#                'Pbma', 'Pcmb', 'Pnnm', 'Pmnn', 'Pnmn', 'Pmmn', 'Pnmm', 'Pmnm', 'Pbcn', 'Pcan',
#                'Pnca', 'Pnab', 'Pbna', 'Pcnb', 'Pbca', 'Pcab', 'Pnma', 'Pmnb', 'Pbnm', 'Pcmn',
#                'Pmcn', 'Pnam', 'Cmcm', 'Ccmm', 'Amma', 'Amam', 'Bbmm', 'Bmmb', 'Cmca', 'Ccmb',
#                'Abma', 'Acam', 'Bbcm', 'Bmab', 'Cmmm', 'Ammm', 'Bmmm', 'Cccm', 'Amaa', 'Bbmb',
#                'Cmma', 'Cmmb', 'Abmm', 'Acmm', 'Bmcm', 'Bmam', 'Ccca', 'Cccb', 'Abaa', 'Acaa',
#                'Bbcb', 'Bbab', 'Fmmm', 'Fddd', 'Immm', 'Ibam', 'Imcb', 'Icma', 'Ibca', 'Icab',
#                'Imma', 'Immb', 'Ibmm', 'Icmm', 'Imcm', 'Imam', 'P4', 'P41', 'P42', 'P43', 'I4',
#                'I41', 'P-4', 'I-4', 'P4/m', 'P42/m', 'P4/n', 'P42/n', 'I4/m', 'I41/a', 'P422',
#                'P4212', 'P4122', 'P41212', 'P4222', 'P42212', 'P4322', 'P43212', 'I422',
#                'I4122', 'P4mm', 'P4bm', 'P42cm', 'P42nm', 'P4cc', 'P4nc', 'P42mc', 'P42bc',
#                'I4mm', 'I4cm', 'I41md', 'I41cd', 'P-42m', 'P-42c', 'P-421m', 'P-421c', 'P-4m2',
#                'P-4c2', 'P-4b2', 'P-4n2', 'I-4m2', 'I-4c2', 'I-42m', 'I-42d', 'P4/mmm',
#                'P4/mcc', 'P4/nbm', 'P4/nnc', 'P4/mbm', 'P4/mnc', 'P4/nmm', 'P4/ncc', 'P42/mmc',
#                'P42/mcm', 'P42/nbc', 'P42/nnm', 'P42/mbc', 'P42/mnm', 'P42/nmc', 'P42/ncm',
#                'I4/mmm', 'I4/mcm', 'I41/amd', 'I41/acd', 'P3', 'P31', 'P32', 'R3', 'R3:r',
#                'P-3', 'R-3', 'R-3:r', 'P312', 'P321', 'P3112', 'P3121', 'P3212', 'P3221',
#                'R32', 'R32:r', 'P3m1', 'P31m', 'P3c1', 'P31c', 'R3m', 'R3m:r', 'R3c', 'R3c:r',
#                'P-31m', 'P-31c', 'P-3m1', 'P-3c1', 'R-3m', 'R-3m:r', 'R-3c', 'R-3c:r', 'P6',
#                'P61', 'P65', 'P62', 'P64', 'P63', 'P-6', 'P6/m', 'P63/m', 'P622', 'P6122',
#                'P6522', 'P6222', 'P6422', 'P6322', 'P6mm', 'P6cc', 'P63cm', 'P63mc', 'P-6m2',
#                'P-6c2', 'P-62m', 'P-62c', 'P6/mmm', 'P6/mcc', 'P63/mcm', 'P63/mmc', 'P23',
#                'F23', 'I23', 'P213', 'I213', 'Pm-3', 'Pn-3', 'Fm-3', 'Fd-3', 'Im-3', 'Pa-3',
#                'Ia-3', 'P432', 'P4232', 'F432', 'F4132', 'I432', 'P4332', 'P4132', 'I4132',
#                'P-43m', 'F-43m', 'I-43m', 'P-43n', 'F-43c', 'I-43d', 'Pm-3m', 'Pn-3n', 'Pm-3n',
#                'Pn-3m', 'Fm-3m', 'Fm-3c', 'Fd-3m', 'Fd-3c', 'Im-3m', 'Ia-3d')

        for item in data.items():
            invalid_val = 'Invalid value "%s" for Key "%s".\nDeleting Key %s!'%(item[1], item[0], item[0])

            if item[0] in ('CHECK', 'NOSIGMA', 'FOBS', 'FOSQUARED',
                  'ELECTRONS') and item[1] is not True:
                if item[1] in validTrue:
                    self._data[item[0]] = True
                else:
                    print invalid_val
                    del self._data[item[0]]

            elif item[0] in ('RHOMAX', 'RESMAX', 'RECORD', 'NREFLECTION',
                  'BFACTOR', 'GENER', 'EXPAND'):
                try:
                    val = float(item[1])
                except ValueError:
                    print invalid_val
                    del self._data[item[0]]
                else:
                    self._data[item[0]] = val

            elif item[0] in ('SPACEGROUP'):
#                if re.sub(r'\s', '', item[1]) in spcgrs:
#                    # Regex to split space groups into lattice and symmetry ops
#                    spcgr = ' '.join(re.findall(r'^[ABCFIPR]|'\
#                                                r'[2346]*[123456]/[abcdmn]'\
#                                                r'|-[1346]|'\
#                                                r'[abcdmn]|'\
#                                                r'(?<!32|31|P3)21(?!1$)|'\
#                                                r'31(?!2$|[mc])|'\
#                                                r'(?<![R1234])32(?=12$|21$|$)|'\
#                                                r'41|'\
#                                                r'42(?!2$|12$)|'\
#                                                r'43(?!2$)|'\
#                                                r'62(?=22$|$)|'\
#                                                r'6[1345]|'\
#                                                r'[123456]',
#                                                re.sub(r'\s', '', item[1]))[0:4])
                try:
                    sg = sgtbx.space_group_info(str(item[1])).type().lookup_symbol()
                    self._data[item[0]] = sg
                except RuntimeError:
                    print invalid_val
                    del self._data[item[0]]

            elif item[0] in ('WAVE') and item[1] not in ('Mo', 'Cu'):
                print invalid_val
                del self._data[item[0]]

            elif item[0] in ('CELL', 'ERRORS', 'CONTENTS', 'SFACTORS', 'ANOMALOUS',
                    'FORMAT', 'REFLECTIONS') and type(item[1]) not in (str,unicode):
                    print invalid_val
                    del self._data[item[0]]

        for item in inv.items():
            invalid_val = 'Invalid value "%s" for Key "%s".\nDeleting Key %s!'%(item[1], item[0], item[0])

            if item[0] in ('COCHRAN', 'NQUARTETS') and item[1] is not True:
                if item[1] in validTrue:
                    self._invariants[item[0]] = True
                else:
                    print invalid_val
                    del self._invariants[item[0]]

            elif item[0] in ('GMIN'):
                try:
                    val = float(item[1])
                except ValueError:
                    print invalid_val
                    del self._invariants[item[0]]
                else:
                    self._invariants[item[0]] = val

        for item in phase.items():
            invalid_val = 'Invalid value "%s" for Key "%s".\nDeleting Key %s!'%(item[1], item[0], item[0])

            if item[0] in ('TANGENT', 'PATTERSON', 'RELAX', 'UNRELAX', 'NOLSQ',
                  'RECYCLE') and item[1] is not True:
                if item[1] in validTrue:
                    self._phase[item[0]] = True
                else:
                    print invalid_val
                    del self._phase[item[0]]

            elif item[0] in ('ITERATION','TRIAL', 'STRIAL', 'PEAKS', 'CYCLE',
                  'RESIDUAL'):
                try:
                    val = float(item[1])
                except ValueError:
                    print invalid_val
                    del self._phase[item[0]]
                else:
                    self._phase[item[0]] = val

            elif item[0] in ('SIZE') and str(item[1]).lower() not in sizestr:
                    print invalid_val
                    del self._phase[item[0]]

            elif item[0] in ('FRAGMENT') and not isFileHasExt(item[1],'fra'):
                    print invalid_val
                    del self._phase[item[0]]

            elif item[0] in ('BLOCK') and type(item[1]) not in (str,unicode):
                    print invalid_val
                    del self._phase[item[0]]

        return True
#}}}
    def getGui(self):#{{{
        return self._sirgui
    #}}}
    def setGui(self, sirgui):#{{{
        if sirgui == True:
            self._sirgui = True
        elif sirgui == False:
            self._sirgui = False
        else:
            print 'Invalid value for GUI: True or False'
#}}}
    def setDirectives(self, **kwargs):#{{{
        '''
        Sets a Dict of SIR directives
        '''
        for value in kwargs.values():
            if type(value) not in (unicode,str,int,float,bool):
                print type(value)
                print 'ERROR: Invalid type for Value %s!'%value
                return False
        data = kwargs.copy()
        invariants = kwargs.copy()
        phase = kwargs.copy()
        valid_data_direc = ('CELL', 'ERRORS', 'SPACEGROUP', 'CONTENTS',
                            'CHECK', 'SFACTORS', 'ANOMALOUS', 'RHOMAX',
                            'RESMAX', 'FORMAT', 'RECORD', 'REFLECTIONS',
                            'NOSIGMA', 'FOBS', 'FOSQUARED', 'WAVE',
                            'NREFLECTION', 'BFACTOR', 'ELECTRONS',
                            'GENER', 'EXPAND')
        valid_inv_direc =  ('GMIN', 'COCHRAN', 'NQUARTETS')
        valid_phase_direc = ('SIZE', 'BLOCK', 'ITERATION',
                             'TANGENT', 'PATTERSON', 'TRIAL', 'STRIAL',
                             'RELAX', 'UNRELAX', 'PEAKS', 'NOLSQ',
                             'CYCLE', 'RESIDUAL', 'FRAGMENT', 'RECYCLE')
        for key in kwargs.keys():
            if key.upper() not in valid_data_direc:
                del data[key]
            else:
                data[key.upper()] = data.pop(key)

            if key.upper() not in valid_inv_direc:
                del invariants[key]
            else:
                invariants[key.upper()] = invariants.pop(key)

            if key.upper() not in valid_phase_direc:
                del phase[key]
            else:
                phase[key.upper()] = phase.pop(key)

            if key.upper() not in valid_data_direc and key.upper() not in\
            valid_inv_direc and key.upper() not in valid_phase_direc:
                print 'Key %s not allowed in any directive!\nDeleting %s!'%(key.upper(), key.upper())

        self._data.update(data)
        self._invariants.update(invariants)
        self._phase.update(phase)
        self._ckDirects()
        return True
#}}}
    def getDirectives(self):#{{{
        '''
        Returns Dicts of SIR directives
        '''
        return self._data, self._invariants, self._phase
#}}}
    def delDirectives(self, *args):#{{{
        '''
        Delete SIR directives
        '''
        data = self._data.copy()
        inv = self._invariants.copy()
        phase = self._phase.copy()
        for arg in args:
            if arg.upper() in data.keys():
                del self._data[arg.upper()]
            if arg.upper() in inv.keys():
                del self._invariants[arg.upper()]
            if arg.upper() in phase.keys():
                del self._phase[arg.upper()]
        return True
#}}}
    def write(self, filename, data=None, invariants=None, phase=None):#{{{
        '''
        Writes the *.sir inputfile and returns True
        on success.
        '''
        import codecs

        SIROUT = codecs.open(filename+'.sir', 'w', encoding='latin1')
        if self._sirgui:
            SIROUT.write('%WINDOW\n')
        else:
            SIROUT.write('%NOWINDOW\n')
        SIROUT.write('%%STRUCTURE %s\n'%(filename))
        SIROUT.write('%%JOB %s\n'%(filename))
        SIROUT.write('%INIT\n')
        if not data == None:
            SIROUT.write('%DATA\n')
            for key in data.keys():
                if data[key] == True and isinstance(data[key], bool):
                    SIROUT.write('\t%s\n'%(key))
                else:
                    SIROUT.write('\t%s %s\n'%(key, data[key]))
        if not invariants == None:
            SIROUT.write('%INVARIANTS\n')
            for key in invariants.keys():
                if invariants[key] == True and isinstance(invariants[key], bool):
                    SIROUT.write('\t%s\n'%(key))
                else:
                    SIROUT.write('\t%s %s\n'%(key, invariants[key]))
        if not phase == None:
            SIROUT.write('%PHASE\n')
            for key in phase.keys():
                if phase[key] == True and isinstance(phase[key], bool):
                    SIROUT.write('\t%s\n'%(key))
                else:
                    SIROUT.write('\t%s %s\n'%(key, phase[key]))
        SIROUT.write('%END')
        SIROUT.close()
        return True
#}}}
    def Exec(self, sirfile, sirversion=2008):#{{{
        '''
        Executes Sir
        '''
        import olx

        isFileHasExt = lambda filepath, ext: path.isfile(filepath)\
                and filepath.lower().split('.')[-1] in ext

        if not isFileHasExt(sirfile, 'sir'):
            print 'Invalid Path for Sir Input'
            return False
        if self._sirgui:
            olx.Exec('sir%s'%sirversion, sirfile, o=True)
        else:
            olx.Exec('sir%s'%sirversion, sirfile)
        olx.WaitFor('process')
        return True
#}}}

    Gui = property(getGui, setGui)
#}}}

# Some code for testing the Sir class#{{{
if __name__ == '__main__':
    name = 'testee'
    oxs = Sir()
    (data, inv, phase) = oxs.getDirectives()
    directs = {'cell':'7 7 7 90 90 90', 'SPACEGROUP':'P 5', 'contents':'C H 4',
                      'blobb':'bllla', 'Resmax':u'8', 'size':'M', 'rhomax':'1',
                      'reflections':u'tästee.hkl', 'check':1, 'gmin':0.5, 'cochran':True}
    oxs.setDirectives(**directs)
    print 'DATA',data
    print 'INV',inv
    print 'PHASE',phase
    oxs.write('%s'%name,data,inv,phase)
#    for key in data.keys():
#        if data[key] == True:
#            print key
#        else:
#            print key, data[key]
#    for key in inv.keys():
#        if inv[key] == True:
#            print key
#        else:
#            print key, inv[key]
#    for key in phase.keys():
#        if phase[key] == True:
#            print key
#        else:
#            print key, phase[key]
#}}}
