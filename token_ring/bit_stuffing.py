import math
from bitarray import*

def deleteExtraBytes(constBytes,nDelBits):
    #delete additional bytes added after bit operations 
    extraBytes = bits2bytes(nDelBits)
    return constBytes[:len(constBytes)-extraBytes]


class bit_stuffing:
    
    def __init__(self):
        
        self.FD = 0x7E
        self.byteFD = (self.FD).to_bytes(1,byteorder='big',signed=False)

        self.insertingBitVal = True
        self.bitFrameDelim = bitarray()
        self.bitFrameDelim.frombytes(self.byteFD)
        
        self.bitPattern = bitarray()
        self.__initBitPattern(self.bitPattern)

        
    def __initBitPattern(self,bitPattern):
        #bit pattern = bitFrameDelim without last bit
        #for i in range(beg,end,1):
        #    self.bitPattern.append(self.bitFrameDelim[i])

        self.bitPattern = self.bitFrameDelim.copy()
        self.bitPattern.pop()
        self.bitPattern.append('1')

    def encode(self,constBytes):

        bitArray = bitarray()
        bitArray.frombytes(constBytes)
        posList = bitArray.search(self.bitFrameDelim)

        counter = 0
        for pos in posList:
            bitArray.insert(pos+len(self.bitFrameDelim)-1+counter,self.insertingBitVal)
            counter += 1
        #add zero bits to the last incomplete
        bitArray.fill()
        
        return (bitArray.tobytes(), len(posList))        
        


    def decode(self,constBytes):

        bitArray = bitarray()
        bitArray.frombytes(constBytes)
        
        posList = bitArray.search(self.bitPattern)

        counter = 0
        for pos in posList:
            bitArray.pop(pos+len(self.bitPattern)-1-counter)
            counter +=1

        bitDeleted = len(posList)
        #extraBytes = math.ceil(bitDeleted/8)
        extraBytes = bits2bytes(bitDeleted)
        constBytes = bitArray.tobytes()
        constBytes = constBytes[:len(constBytes)-extraBytes]

        return (constBytes, bitDeleted)

