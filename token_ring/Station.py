import serial 
from bit_stuffing import*
from Hamming import*
from SocketWrapper import*

#station can't send message to self
class AddrError(Exception):
    pass

class Packet:
    '''
    FI - frame info             - 8 bit                              
    DA - destination Address    - 6 byte
    SA - source address         - 6 byte
    M - monitor bit
    A - address recognized bit    
    C - frame-copied bit
    '''
    # packet = FD + FI + DA + SA + payload + FD

    def __init__(self,frame = None):
        self.bitStuffing = bit_stuffing()
        self.hamming = Hamming()
        self.frame = frame
        self.frameInfoSize = 8 #bit
        self.addrSize = 6 #byte
        self.headerSize = 14 # byte
        if not frame:
            self.FI = bitarray(8)
            self.FI.setall(False)
            self.DA = None
            self.SA= None
        else:
            self.extractFrameInfo()

    @property
    def Frame(self):
        return self.frame
    @Frame.setter
    def Frame(self,frame):
        self.frame = frame
        self.extractFrameInfo()

    @property
    def monitor(self):
        return self.FI[2]

    @monitor.setter
    def monitor(self,value):
        self.FI[2] = value       

    @property
    def addrRecognized(self):
        return self.FI[1]

    @addrRecognized.setter
    def addrRecognized(self,value):
        self.FI[1] = value
    
    @property
    def frameCopied(self):
        return self.FI[0]

    @frameCopied.setter
    def frameCopied(self,value):
        self.FI[0] = value

   

    def pack(self,payload):
        #bit stuffing
        payload,pBitStuffed = self.bitStuffing.encode(payload) 
        #hamming encode
        payload  = self.hamming.encode(payload)
        # packet = FD + FI + DA + SA + payload + FD
        FD = self.bitStuffing.byteFD
        packet = FD + self.FI.tobytes() + self.DA.to_bytes(self.addrSize,byteorder = 'big') + self.SA.to_bytes(self.addrSize,byteorder = 'big') + payload + FD
        self.frame =  packet
        return self.frame

    def repack(self):
        FD = self.bitStuffing.byteFD
        self.frame = FD + self.FI.tobytes() + self.DA.to_bytes(self.addrSize,byteorder = 'big') + self.SA.to_bytes(self.addrSize,byteorder = 'big') + self.frame[self.headerSize : len(self.frame)-1] + FD

    def extractFrameInfo(self):
        self.FI = bitarray()
        self.FI.frombytes(self.frame[1:2])
        self.DA = int.from_bytes(self.frame[2:3],byteorder='big')
        self.SA = int.from_bytes(self.frame[3:4],byteorder='big')


    def unpack(self):
        payload = self.frame[4 : len(self.frame)-1]
        #hemming decode
        payload = self.hamming.decode(bytes(payload))
        #bit stuffing decode
        payload,pBitStuffed = self.bitStuffing.decode(payload)
        return payload

    def addrToBytes(self,addr):
        #4 + 2 bytes ASCII
        ip,port = addr
        str_quartet = ip.split('.')
        num_quartet = [int(byte) for byte in str_quartet]
        byte_quartet = [el.to_bytes(1,byteorder='big') for el in num_quartet]
        num_port = int(port)
        return b''.join(byte_quartet) + num_port.to_bytes(2,byteorder='big')
   
    def addrFromBytes(self,bAddr):
        int_quartet = list(bAddr[:4])
        port = int.from_bytes(bAddr[4:],byteorder='big')
        IP = '.'.join([str(el) for el in int_quartet])
        return (IP,str(port))

class Station:
   
    def __init__(self):
        #ports to communicate with circle
        self.prevPort = None
        self.nextPort = None
        self.isMonitor = False

    def run(self,servSock,clientSock,isMonitor):
        self.servSock = servSock
        self.clientSock = clientSock
        #if combobox is selected as monitor-> true else folse
        self.isMonitor = isMonitor
        #open ports
        '''
        The port is immediately opened on object creation, when a port is given.
        It is not opened when port is None and a successive call to open() will be needed.
        '''

    def send(self,destAddr,data):
        #station can't send message to self
        if self.servSock.inetAddr == destAddr:
            raise AddrError('fail to send a message to self')
        pack = Packet()
        #set frame monitor bit
        pack.monitor = self.isMonitor
        #dest address
        pack.SA = self.servSock.inetAddr
        pack.DA = destAddr
        pack.pack(data)
        self.clientSock.send(pack.frame)

    def transit(self):
        while True:
            #get packet (frame)
            pack = self.receive()
            #if cur station address == destination address
            if self.servSock.inetAddr == pack.DA:
                #get packet data
                payload = self.acceptPacket(pack)
                if payload is not None:
                    return payload
            else:
                self.redirectPacket(pack)


    def acceptPacket(self,pack):
        #check if the packet is from this station 
        #and receiver get data from it
        if not (pack.addrRecognized and pack.frameCopied): 
            #swap DA and SA and send pack to sender
            pack.DA , pack.SA = pack.SA , pack.DA 
            #if monitor station, set M bit
            pack.monitor |= self.isMonitor
            #set address_recognized and frame_copied bits
            pack.addrRecognized = True
            pack.frameCopied = True
            #apply changes
            pack.repack()
            self.clientSock.send(pack.frame)
            return pack.unpack()
        #else destroy packet
        else: return None

    def redirectPacket(self,pack):
        #if not monitor bit and station is monitor, set it
        if self.isMonitor and (not pack.monitor):
            pack.monitor = True
            self.clientSock.send(pack.frame)
            #else drop packet
        else:
            #if not monitor -> redirect always 
            self.clientSock.send(pack.frame)

    def receive(self):
        #read until the FD
        pack = Packet()
        FD = pack.bitStuffing.byteFD
        frame = []
        #finding packet beginning
        byte = None
        while byte != FD:
             byte = self.servSock.read(1)
        #put first FD
        frame.append(byte[0])
        byte = None
        while byte != FD:
            byte = self.servSock.read(1)
            frame.append(byte[0])
        pack.Frame = bytes(frame)
        return pack
         
         

