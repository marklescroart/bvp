# Script to concatenate rendered prior files
# Usage: python ConcatenatePriorImages.py fName fDir imSzX imSzY imSzZ <AllImF>
# <AllImF> is either: 
#     a string file name containing all file names to be concatenated
#     arguments to fill in regular file names: String,firstSceneNum,nScenes,nFramesPerScene
#         These are used to create file names thus: 
#        imF = [String%(a,b) for a in range(1,int(nScenes)+int(firstSceneNum)) for b in range(1,int(nFramesPerScene)+1)])
# 

import bvp,tables,sys,os,copy
import numpy as np
import matplotlib.pyplot as plt



def ConcatenatePriorImages(fName,fDir,imF,imSz):
    """
    Create concatenated image files (hf5 tables) from many individual (.png)s 
    """
    S = np.zeros(imSz+(len(imF),))
    FoundImage = np.ones((len(imF),))
    for iF,f in enumerate(imF):
        ff = os.path.join(fDir,f)
        try:
            imTmp = plt.imread(ff)
            if imTmp.shape[2]>imSz[2]:
                # Drop alpha if 3rd dim of imSz is not rgba
                imTmp = imTmp[:,:,:imSz[2]]
            S[:,:,:,iF] = copy.copy(imTmp)
            FoundImage[iF] = 1
        except:
            print('Could not find file %s!'%f)
        if iF==100 and sum(FoundImage)<90:
            # If you don't find more than 90 of the first 100 images:
            raise Exception('Could not find any image files!')
    T = tables.openFile(fName,mode='w')
    T.createArray('/','S',S.T) # transpose makes reading this matlab-friendly
    T.close()
    print('Saved %s'%fName)
print(__name__)
if __name__=='__main__':
    fNm = sys.argv[1]
    fDir = sys.argv[2]
    imSz = tuple([int(x) for x in sys.argv[3:6]])
    AllImF = sys.argv[6:]    
    # 2 options: 
    # (1) provide a string file name for a text file with all files printed out in it
    # (2) provide a set of constraints for 
    if len(fNm)==1:
        with open(fNm[0]) as fid:
            AllImF = fid.readlines()
    else:
        ss,firstSc,nSc,nFr = AllImF
        imF = [ss%(a,b) for a in range(int(firstSc),int(nSc)+int(firstSc)) for b in range(1,int(nFr)+1)]
    # Works!
    #print(imF[0])
    #print(imF[1])
    #print(fDir)
    #print(imSz)
    print('--- Concatenating images from %s to %s (%d images) ---'%(imF[0],imF[-1],len(imF)))
    ConcatenatePriorImages(fNm,fDir,imF,imSz)
    print('\n\n--- Done! ---\n\n')
    print('Clearing concatenated files...')
    for f in imF:
        try:
            #print('removing (not really): %s'%os.path.join(fDir,f))
            os.remove(os.path.join(fDir,f))
        except:
            print('%d did not exist!'%(os.path.join(fDir,f)))