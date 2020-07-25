import os
import json

# setup command line parser to control execution
from optparse import OptionParser
parser = OptionParser()
parser.add_option( "--initialize",
                  action="store_true", dest="initialize", default=False,
                  help="build initial sql file ", metavar = "BOOL")
parser.add_option( "--setuptestset",
                  action="store_true", dest="setuptestset", default=False,
                  help="cross validate test set", metavar="FILE")
parser.add_option( "--kfolds",
                  type="int", dest="kfolds", default=5,
                  help="setup info", metavar="int")
parser.add_option( "--trainingloss",
                  action="store", dest="trainingloss", default='dscimg',
                  help="setup info", metavar="string")
parser.add_option( "--sampleweight",
                  action="store", dest="sampleweight", default=None,
                  help="setup info", metavar="string")
parser.add_option( "--trainingbatch",
                  type="int", dest="trainingbatch", default=5,
                  help="setup info", metavar="int")
parser.add_option( "--validationbatch",
                  type="int", dest="validationbatch", default=20,
                  help="setup info", metavar="int")
parser.add_option( "--trainingsolver",
                  action="store", dest="trainingsolver", default='adadelta',
                  help="setup info", metavar="string")
parser.add_option( "--databaseid",
                  action="store", dest="databaseid", default='hccmri',
                  help="available data: hcc, crc", metavar="string")
(options, args) = parser.parse_args()

# current datasets
trainingdictionary = {'hccmri':{'dbfile':'./trainingdata.csv','rootlocation':'/rsrch2/ip/dtfuentes/github/hccdetection','delimiter':','},
                      'hccfollowup':{'dbfile':'/rsrch1/ip/dtfuentes/github/RandomForestHCCResponse/datalocation/TACE_final_2_2.csv','rootlocation':'/rsrch1/ip/dtfuentes/github/RandomForestHCCResponse'},
                      'crc':{'dbfile':'./crctrainingdata.csv','rootlocation':'/rsrch1/ip/jacctor/LiTS/LiTS' ,'delimiter':'\t'},
                      'hccct':{'dbfile':'datalocation/cthccdatakey.csv','rootlocation':'/rsrch1/ip/dtfuentes/github/RandomForestHCCResponse','delimiter':'\t'}}

# options dependency 
options.sqlitefile   = 'livermodel.sqlite'
_xstr = lambda s: s or ""
print(options.sqlitefile)

# build data base from CSV file
def GetDataDictionary():
  import sqlite3
  CSVDictionary = {}
  tagsconn = sqlite3.connect(options.sqlitefile)
  cursor = tagsconn.execute(' SELECT aq.* from trainingdata aq ;' )
  names = [description[0] for description in cursor.description]
  sqlStudyList = [ dict(zip(names,xtmp)) for xtmp in cursor ]
  for rowid,row in enumerate(sqlStudyList) :
       CSVDictionary[rowid]  =  {'dataid':row['dataid'],'image':row['image'], 'label':row['label'], 'uid':"%s" %row['uid']}  
  return CSVDictionary 

# setup kfolds
def GetSetupKfolds(numfolds,idfold,dataidsfull ):
  from sklearn.model_selection import KFold, train_test_split

  if (numfolds < idfold or numfolds < 1):
     raise("data input error")
  # split in folds
  if (numfolds > 1):
     kf = KFold(n_splits=numfolds)
     allkfolds = [ (list(map(lambda iii: dataidsfull[iii], trainval_index)), list(map(lambda iii: dataidsfull[iii], test_index))) for trainval_index, test_index in kf.split(dataidsfull )]
     trainval_index = allkfolds[idfold][0]
     (train_index,validation_index) = train_test_split(trainval_index,test_size =.125) # .125*.8 = .1
     test_index     = allkfolds[idfold][1]
  else:
     train_index       = dataidsfull 
     validation_index  = None  
     test_index        = None  
  return (train_index,validation_index,test_index)
## Borrowed from
## $(SLICER_DIR)/CTK/Libs/DICOM/Core/Resources/dicom-schema.sql
## 
## --
## -- A simple SQLITE3 database schema for modelling locally stored DICOM files
## --
## -- Note: the semicolon at the end is necessary for the simple parser to separate
## --       the statements since the SQlite driver does not handle multiple
## --       commands per QSqlQuery::exec call!
## -- ;
## TODO note that SQLite does not enforce the length of a VARCHAR. 
## TODO (9) What is the maximum size of a VARCHAR in SQLite?
##
## TODO http://www.sqlite.org/faq.html#q9
##
## TODO SQLite does not enforce the length of a VARCHAR. You can declare a VARCHAR(10) and SQLite will be happy to store a 500-million character string there. And it will keep all 500-million characters intact. Your content is never truncated. SQLite understands the column type of "VARCHAR(N)" to be the same as "TEXT", regardless of the value of N.
initializedb = """
DROP TABLE IF EXISTS 'Images' ;
DROP TABLE IF EXISTS 'Patients' ;
DROP TABLE IF EXISTS 'Series' ;
DROP TABLE IF EXISTS 'Studies' ;
DROP TABLE IF EXISTS 'Directories' ;
DROP TABLE IF EXISTS 'lstat' ;
DROP TABLE IF EXISTS 'overlap' ;

CREATE TABLE 'Images' (
 'SOPInstanceUID' VARCHAR(64) NOT NULL,
 'Filename' VARCHAR(1024) NOT NULL ,
 'SeriesInstanceUID' VARCHAR(64) NOT NULL ,
 'InsertTimestamp' VARCHAR(20) NOT NULL ,
 PRIMARY KEY ('SOPInstanceUID') );
CREATE TABLE 'Patients' (
 'PatientsUID' INT PRIMARY KEY NOT NULL ,
 'StdOut'     varchar(1024) NULL ,
 'StdErr'     varchar(1024) NULL ,
 'ReturnCode' INT   NULL ,
 'FindStudiesCMD' VARCHAR(1024)  NULL );
CREATE TABLE 'Series' (
 'SeriesInstanceUID' VARCHAR(64) NOT NULL ,
 'StudyInstanceUID' VARCHAR(64) NOT NULL ,
 'Modality'         VARCHAR(64) NOT NULL ,
 'SeriesDescription' VARCHAR(255) NULL ,
 'StdOut'     varchar(1024) NULL ,
 'StdErr'     varchar(1024) NULL ,
 'ReturnCode' INT   NULL ,
 'MoveSeriesCMD'    VARCHAR(1024) NULL ,
 PRIMARY KEY ('SeriesInstanceUID','StudyInstanceUID') );
CREATE TABLE 'Studies' (
 'StudyInstanceUID' VARCHAR(64) NOT NULL ,
 'PatientsUID' INT NOT NULL ,
 'StudyDate' DATE NULL ,
 'StudyTime' VARCHAR(20) NULL ,
 'AccessionNumber' INT NULL ,
 'StdOut'     varchar(1024) NULL ,
 'StdErr'     varchar(1024) NULL ,
 'ReturnCode' INT   NULL ,
 'FindSeriesCMD'    VARCHAR(1024) NULL ,
 'StudyDescription' VARCHAR(255) NULL ,
 PRIMARY KEY ('StudyInstanceUID') );

CREATE TABLE 'Directories' (
 'Dirname' VARCHAR(1024) ,
 PRIMARY KEY ('Dirname') );

CREATE TABLE lstat  (
   InstanceUID        VARCHAR(255)  NOT NULL,  --  'studyuid *OR* seriesUID'
   SegmentationID     VARCHAR(80)   NOT NULL,  -- UID for segmentation file 
   FeatureID          VARCHAR(80)   NOT NULL,  -- UID for image feature     
   LabelID            INT           NOT NULL,  -- label id for LabelSOPUID statistics of FeatureSOPUID
   Mean               REAL              NULL,
   StdD               REAL              NULL,
   Max                REAL              NULL,
   Min                REAL              NULL,
   Count              INT               NULL,
   Volume             REAL              NULL,
   ExtentX            INT               NULL,
   ExtentY            INT               NULL,
   ExtentZ            INT               NULL,
   PRIMARY KEY (InstanceUID,SegmentationID,FeatureID,LabelID) );

-- expected csv format
-- FirstImage,SecondImage,LabelID,InstanceUID,MatchingFirst,MatchingSecond,SizeOverlap,DiceSimilarity,IntersectionRatio
CREATE TABLE overlap(
   FirstImage         VARCHAR(80)   NOT NULL,  -- UID for  FirstImage  
   SecondImage        VARCHAR(80)   NOT NULL,  -- UID for  SecondImage 
   LabelID            INT           NOT NULL,  -- label id for LabelSOPUID statistics of FeatureSOPUID 
   InstanceUID        VARCHAR(255)  NOT NULL,  --  'studyuid *OR* seriesUID',  
   -- output of c3d firstimage.nii.gz secondimage.nii.gz -overlap LabelID
   -- Computing overlap #1 and #2
   -- OVL: 6, 11703, 7362, 4648, 0.487595, 0.322397  
   MatchingFirst      int           DEFAULT NULL,     --   Matching voxels in first image:  11703
   MatchingSecond     int           DEFAULT NULL,     --   Matching voxels in second image: 7362
   SizeOverlap        int           DEFAULT NULL,     --   Size of overlap region:          4648
   DiceSimilarity     real          DEFAULT NULL,     --   Dice similarity coefficient:     0.487595
   IntersectionRatio  real          DEFAULT NULL,     --   Intersection / ratio:            0.322397
   PRIMARY KEY (InstanceUID,FirstImage,SecondImage,LabelID) );
"""

#############################################################
# build initial sql file 
#############################################################
if (options.initialize ):
  import sqlite3
  import pandas
  import time
  # build new database
  os.system('rm %s'  % options.sqlitefile )
  tagsconn = sqlite3.connect(options.sqlitefile )
  for sqlcmd in initializedb.split(";"):
     tagsconn.execute(sqlcmd );
  # load csv file
  df = pandas.read_csv(trainingdictionary['hccct']['dbfile'],delimiter=trainingdictionary['hccct']['delimiter'])
  df.to_sql('trainingdata', tagsconn , if_exists='append', index=False)
  df = pandas.read_csv(trainingdictionary['crc']['dbfile'],delimiter=trainingdictionary['crc']['delimiter'])
  df.to_sql('trainingdata', tagsconn , if_exists='append', index=False)
  df = pandas.read_csv(trainingdictionary['hccmri']['dbfile'],delimiter=trainingdictionary['hccmri']['delimiter'])
  df.to_sql('trainingdata', tagsconn , if_exists='append', index=False)

##########################
# apply model to test set
##########################
elif (options.setuptestset):
  # get id from setupfiles
  databaseinfo = GetDataDictionary()

  # get each data subset
  hccmriids={ key:value for key, value in databaseinfo.items() if value['dataid'] == 'hccmri' }
  crcids=   { key:value for key, value in databaseinfo.items() if value['dataid'] == 'crc' }
  hccctids= { key:value for key, value in databaseinfo.items() if value['dataid'] == 'hccct' }

  # setup partitions
  kfolddictionary = {}
  for iii in range(options.kfolds):
    (train_set,validation_set,test_set) = GetSetupKfolds(options.kfolds,iii,hccmriids.keys())
    kfolddictionary[iii] ={'kfolds':options.kfolds, 'dataid': 'run_a','train_set':train_set,'validation_set':validation_set,'test_set':test_set}
  kfolddictionary[5] ={'kfolds':1, 'dataid': 'crc','train_set':crcids.keys()[:100],'validation_set':crcids.keys()[100:],'test_set':hccmriids.keys()+hccctids.keys()}
  #kfolddictionary[6] ={'train_set':hccctids.keys()[:100],'validation_set':hccctids.keys()[100:],'test_set':hccmriids.keys()}

  # initialize lists partitions
  uiddictionary = {}
  modeltargetlist = []
  nnlist = ['densenet2d','densenet3d','unet2d','unet3d']
  normalizationlist = ['scaled']
  resolutionlist = [256,512]

  makefilename = '%skfold%03d.makefile' % (options.databaseid,options.kfolds) 
  # open makefile
  with open(makefilename ,'w') as fileHandle:
    for normalizationid in normalizationlist :
     for resolutionid in resolutionlist :
      for nnid in nnlist:
       for iii, kfoldset in kfolddictionary.items():
         (train_set,validation_set,test_set) = ( kfoldset['train_set'], kfoldset['validation_set'], kfoldset['test_set'])
         uidoutputdir= 'Processed/%slog/%s/%s/%s/%d/%s/%03d%03d/%03d/%03d' % (options.databaseid,options.trainingloss+ _xstr(options.sampleweight),nnid ,options.trainingsolver,resolutionid,kfoldset['dataid'],options.trainingbatch,options.validationbatch,kfoldset['kfolds'],iii)
         setupconfig = {'normalization':normalizationid,'resolution':resolutionid,'nnmodel':nnid, 'kfold':iii, 'testset':[  databaseinfo[idtest]['uid'] for idtest in test_set], 'validationset': [  databaseinfo[idtrain]['uid'] for idtrain in validation_set],'trainset': [  databaseinfo[idtrain]['uid'] for idtrain in train_set], 'stoFoldername': '%slog' % options.databaseid, 'uidoutputdir':uidoutputdir}
         modelprereq    = '%s/trainedNet.mat' % uidoutputdir
         setupprereq    = '%s/setup.json' % uidoutputdir
         os.system ('mkdir -p %s' % uidoutputdir)
         with open(setupprereq, 'w') as json_file:
           json.dump(setupconfig , json_file)
         fileHandle.write("""%s: %s \n\tmatlab -nodesktop -r "livermodel('$<');exit"\n""" % (modelprereq,setupprereq )    )
         modeltargetlist.append(modelprereq    )
         uiddictionary[iii]=[]
         for idtest in test_set:
            # write target
            imageprereq    = 'anonymize/%s/%s/%s/Art.nii' % (databaseinfo[idtest]['uid'], normalizationid,resolutionid)
            maskprereq     = 'anonymize/%s/%s/%s/%s/label.nii.gz' % (databaseinfo[idtest]['uid'], normalizationid,resolutionid, nnid)
            segmaketarget  = 'anonymize/%s/%s/%s/%s/tumor.nii.gz' % (databaseinfo[idtest]['uid'], normalizationid,resolutionid, nnid)
            uiddictionary[iii].append(databaseinfo[idtest]['uid'] )
            cvtestcmd = "python ./applymodel.py --predictimage=$< --modelpath=$(word 3, $^) --maskimage=$(word 2, $^) --segmentation=$@"  
            fileHandle.write('%s: %s %s %s\n' % (segmaketarget ,imageprereq,maskprereq,    modelprereq  ) )
            fileHandle.write('\t%s\n' % cvtestcmd)
            fileHandle.write('%s: %s %s\n' % (maskprereq,imageprereq,modelprereq  ) )
            cvtestcmd = "mkdir -p $(@D);./run_applymodel.sh $(MATLABROOT) $^ $(@D) 1 gpu"  
            fileHandle.write('\t%s\n' % cvtestcmd)


  # build job list
  with open(makefilename , 'r') as original: datastream = original.read()
  with open(makefilename , 'w') as modified:
     modified.write( 'DATABASEID=unet%s\n' % options.databaseid + 'SQLITEDB=%s\n' % options.sqlitefile + "models: %s \n" % ' '.join(modeltargetlist))
     for idkey in uiddictionary.keys():
        modified.write("UIDLIST%d=%s \n" % (idkey,' '.join(uiddictionary[idkey])))
     modified.write("UIDLIST=%s \n" % " ".join(map(lambda x : "$(UIDLIST%d)" % x, uiddictionary.keys()))    +datastream)

