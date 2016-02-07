                    import sys  #for COM name
from bitarray import*
import threading
from bit_stuffing import bit_stuffing
from Station import*
from tkinter import*
from tkinter.ttk import*    #ovveride tkinter widgets
from Hamming import Hamming

class Application(Frame):
   
    def __init__(self,master = None):
        super().__init__(master)
        self.pack()
        self.station = Station()
        #binds station name and com ports for it
        self.portsDict = {1 : ('192.168.1.3','6000'),
                          2 : ('192.168.1.3','7000'),
                          3 : ('192.168.1.8','6000')} 
        self.__createWidgets()
        self.flPortsOpen = False

    def __del__(self):
        self.destroy()
        self.quit()

    def allocButton(self,col,line,callback,lbl,anchor='wesn'):
        #open port button
        but = Button(self,text=lbl,command=callback)
        but.grid(column=col,row=line,sticky=anchor)
        return but

    def allocLabel(self,col,line,lbl,anchor='wesn',text_font='Arial 8'):
        #current station label
        label = Label(self,text=lbl,font=text_font)
        label.grid(column=col,row=line,sticky=anchor)
        return label

    def allocStationAddress(self,col,line,lbl):
        #curent station address
        addr = Entry(self)
        addr.grid(column=col,row=line,sticky='nwes')
        label = self.allocLabel(col+1,line,lbl)
        return (addr,label)

    def allocCheckButton(self,col,line,txt):
        var = IntVar()
        checkBut = Checkbutton(self,text=txt,variable=var,onvalue=1,offvalue=0)
        checkBut.grid(column=col,row=line)
        return (checkBut,var)

    def __createWidgets(self):
        self.grid()
        self.curServAddrEntry,self.curLabel = self.allocStationAddress(0,0,'current station')
        self.nextServAddrEntry,self.nextLabel = self.allocStationAddress(0,1,'next station')
        self.dstServAddrEntry,self.destLabel = self.allocStationAddress(0,2,'dest station')
        #run server button
        self.runServerBut = self.allocButton(0,3,self.openServPortEvent,'run server')
        #connect client to next server button
        self.connectToNextServBut = self.allocButton(1,3,self.connectToNextServEvent,'connect to next server')
        #start button
        self.startBut = self.allocButton(2,3,self.startStationProc,'start')
        #send button
        self.sendBut = self.allocButton(0,4,self.sendEvent,'send')
        #monitor checkbox
        self.monitorCheckBox, self.monitorChboxVar = self.allocCheckButton(4,1,'is monitor?')
        #edit text
        self.textbox = Text(self,height=12,width=64,font='Arial 8',wrap=WORD)
        self.textbox.focus_set()
        self.textbox.grid(column=0,row=5,columnspan=5)
        #error Label
        self.allocLabel(0,12,'no error','w')
        

    def startStationProc(self):
        try:
            self.station.run(self.curServAddrEntry,self.nextServAddrEntry)
            #self.openPortLabel['text'] = 'opened: ' + stationAddr
            #self.flPortsOpen = True
            self.parallelShowPortData()
            self.errorLabel['text'] = 'no errors'
        except serial.SerialException as e:
            self.errorLabel['text'] = e 

    def connectToNextServEvent(self):
        IP,port = self.nextServAddrEntry.get().split(' ')
        self.clientSock = TCP_ClientSockWrapper(IP,port)

    def openServPortEvent(self):
        #split to [IP, port]
        IP,port =  self.curServAddrEntry.get().split(' ')
        self.servSock = TCP_ServSockWrapper(IP,port)
        
    def sendEvent(self):
        try:
            if not self.flPortsOpen:
                raise serial.SerialException('ports are close')
            msg = self.textbox.get('1.0',END)
            self.station.send(int(self.addressCombo.get()),msg.encode('utf-8'))
            #all is clear
            self.errorLabel['text'] = 'no errors'
        except (serial.SerialException, AddrError) as e:
            self.errorLabel['text'] = e
        

    def showPortData(self):
        while True:
            msg = self.station.transit().decode('utf-8')
            #show
            self.textbox.delete('1.0',END) 
            self.textbox.insert('1.0',msg)
        
    

    def parallelShowPortData(self):
        readThread = threading.Thread(target=self.showPortData)
        readThread.start()
        
  
def addrToBytes(addr):
    str_addr_list = addr[0].split('.')
    int_list = [int(el) for el in str_addr_list]
    byte_list = [el.to_bytes(2,byteorder='big') for el in int_list]
    port = int(addr[1])
    return b''.join(byte_list) + port.to_bytes(2,byteorder='big')
   
def addrFromBytes(bAddr):
    byte_list = splitBytesToList(bAddr,2)
    int_list = [int.from_bytes(el,byteorder='big') for el in byte_list]
    IP = '.'.join([str(el) for el in int_list])
    port = str(byte_list[4])
    return (PI,port)
        
if __name__ == "__main__":
    #root = Tk()
    #app = Application(master=root)
    #app.mainloop()

    #st = Station()
    #st.run(1,True,('COM2','COM3'))
    addr = ("192.168.1.3","6000")
    by = addrToBytes(addr)
    newAddr = addrFromBytes(by)