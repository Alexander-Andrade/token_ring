from bitarray import*
from functools import reduce
import math
from enum import*

def theLowNearestMultipleOf(n,number):
    return n*math.floor(number/n)

def invertBit(bitArray,i):
    bitArray[i] = False if bitArray[i]== True else True

class Hamming:

    class ControlBitsAction(Enum):
        Insert = 1
        Delete = 2
        Traverse = 3
       
    def __init__(self,wordsize=8):
        
        self.wordsize = wordsize
        self.ctrlBitPosList = list(self.__getInsertionPositions(self.wordsize))
        self.wordAdditionalBits = len(self.ctrlBitPosList)
        self.newWordSize = self.wordsize + self.wordAdditionalBits
        self.delWordBitsPos = list(self.__delWordBitsPos())

    def __getInsertionPositions(self,wordsize):
        #0,1,3,7,15...
        num = 1
        newWordSize = wordsize
        while num < newWordSize:
            yield (num - 1)    
            num <<= 1 # num*2
            newWordSize += 1

    def __getNextWordPos(self,bitArrayLen,dir):
        wordPos = 0
        if dir == self.ControlBitsAction.Insert:   
            while  wordPos < bitArrayLen:
                yield wordPos
                wordPos += self.newWordSize
                bitArrayLen += self.wordAdditionalBits

        elif dir == self.ControlBitsAction.Traverse:
            while  wordPos < bitArrayLen:
               yield wordPos
               wordPos += self.newWordSize

        elif dir == self.ControlBitsAction.Delete:
            while  wordPos < bitArrayLen:
                yield wordPos
                wordPos += self.wordsize
                bitArrayLen -= self.wordAdditionalBits

    def __traversUnderControlBits(self,n):

        pos = 0
        counter = 0
        N = n + 1
        i = n
        while True:
            if(counter >= N):
                i += (N + counter)
                counter = 0
                
            pos = counter + i
            if pos >= self.newWordSize :
                break
            yield pos
            counter += 1

    def __delWordBitsPos(self):

        counter = 0
        for pos in self.ctrlBitPosList:
            yield pos - counter
            counter += 1  

    def __wordCalculate(self,bitArray,wordPos):
        for ctrlBitPos in self.ctrlBitPosList:
            sum = 0
            underControlBits = self.__traversUnderControlBits(ctrlBitPos)
            for underControlBitsPos in underControlBits:
                sum += bitArray[wordPos + underControlBitsPos]
            bitArray[wordPos + ctrlBitPos] = self.__calcControlBitValue(sum)
    
    def __wordRecalculate(self,bitArray,wordPos):
        errorValPosList = []
        for ctrlBitPos in self.ctrlBitPosList:
            nSetBit = 0
            underControlBits = self.__traversUnderControlBits(ctrlBitPos)
            for underControlBitsPos in underControlBits:
                #assume that the control bits have a value of zero
                if underControlBitsPos != ctrlBitPos:
                    nSetBit += bitArray[wordPos + underControlBitsPos]
            if bitArray[wordPos + ctrlBitPos] != self.__calcControlBitValue(nSetBit):
                errorValPosList.append(ctrlBitPos)

        if errorValPosList:
            errorBitPos = sum(errorValPosList)
            #correct (invert) spoiled bit
            invertBit(bitArray,wordPos + errorBitPos)

    def __calcControlBitValue(self,sum):
        #accurate control bit value (0 or 1)
        return sum % 2 == 0
    
    def __evaluateControlBits(self,bitArray,wordCalcFunc):
        genWordPos = self.__getNextWordPos(len(bitArray),self.ControlBitsAction.Traverse)
        #evaluate control bits
        for wordPos in genWordPos: 
            wordCalcFunc(bitArray,wordPos)
                             
    
    def __insertControlBits(self,bitArray):
        #generator of the next word position
        genWordPos = self.__getNextWordPos(len(bitArray),self.ControlBitsAction.Insert)
        #insert control bits
        for wordPos in genWordPos: 
            #insert zero control bits
            for insertPos in self.ctrlBitPosList:
                bitArray.insert(wordPos + insertPos,False)
    
    def __delControlBits(self,bitArray):
        #generator of the next word position
        genWordPos = self.__getNextWordPos(len(bitArray),self.ControlBitsAction.Delete)
        for wordPos in genWordPos: 
            for delPos in self.delWordBitsPos:
                bitArray.pop(wordPos + delPos)


    def __editEntryBytesLength(self,constBytes):
        length = len(constBytes)
        byteWordSize = int(self.wordsize / 8)
        nWords = int(ceil(float(length) / byteWordSize))
        newLen = nWords * byteWordSize
        #add emty bytes to parity
        return constBytes + bytes(newLen - length)

    def encode(self,constBytes):
        bitArray = bitarray()
        bitArray.frombytes(constBytes)
        self.__insertControlBits(bitArray)
        self.__evaluateControlBits(bitArray,self.__wordCalculate)
        return bitArray.tobytes()

    def decode(self,constBytes):
        bitArray = bitarray()
        bitArray.frombytes(constBytes)
        #cut waste residue 
        cutPos = theLowNearestMultipleOf(self.newWordSize,len(constBytes)*8)
        bitArray = bitArray[:cutPos]
        self.__evaluateControlBits(bitArray,self.__wordRecalculate)
        #delete control bits
        self.__delControlBits(bitArray)
        return bitArray.tobytes()