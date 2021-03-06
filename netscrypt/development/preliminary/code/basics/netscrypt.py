import json
import asyncio
import websockets

class JsonSocket:
    def __init__ (self, socket):
        self.socket = socket
        
    async def send (self, anObject):
        return await socket.send (json.dumps (anObject))
        
    async def recv (self):
        return json.loads (await socket.recv ())
        
class Handler:
    def __init__ (self, socket):
        self.socket = socket
        
class Call (Handler):
    def __init__ (self, socket):
        super () .__init__ (socket)
        
    def __call__ ():
        command = self.socket.recv ()
        self.socket.send ()

class CallBack (Handler):
    def __init__ (self, socket):
        super () .__init__ (socket)
        
    def __call__ ():
        pass

class Party:
    def __init__ (self, hostName = 'localhost', portNumber = '6666')
        self.hostName = hostName
        self.portNumber = portNumber
        
        
        
    def loop (self):
        

class Client (Party):
    def __init__ (self, *args, **kwargs):
        super () .__init__ (*args, **kwargs)
        self.hostUrl = f'ws://{self.hostName}:{self.portNumber}'
        asyncio.run (self.clientLoopCreator ())

    async def clientLoopCreator (self):
        ''' Initiates master and slave connections
        - The master connection is used call server functions from the client
        - The slave connection is used to call client functions from the server
        '''
        
        async def clientLoop (socket, role, action):
            await socket.send (['register', role])
            if await socket.recv ():
                print (f'Registration of {role} accepted by server at {self.hostUrl}')   
                while True:
                    await action ()
            else:
                self.print (f'Registration of {role} rejected by server at {self.hostUrl}')
        
        async with websockets.connect (self.hostUrl) as masterSocket:
             print ('Master connection accepted by server at {self.hostUrl}')
             masterJsonSocket = JsonSocket (masterSocket)
             async with websockets.connect (self.hostUrl) as slaveSocket:
                print ('Slave connection accepted by server at {self.hostUrl}')
                slaveJsonSocket = JsonSocket (slaveSocket)
                await asyncio.gather (
                    clientLoop (masterJsonSocket, 'master', Call (masterJsonSocket))
                    clientLoop (slaveJsonSocket, 'slave', CallBack (slaveJsonSocket)),
                )
                
class Server (Party):
    def __init__ (self, *args, **kwargs):
        super.__init__ (*args, **kwargs)
        
        async def serverLoop (socket, dummy):
            '''
            Role communication handler
            - Called once for each master and once for each slave
            - Handles the socket belonging to the master or slave that it's called for
            - Remains looping for that master or slave until connection is closed
            - So several calls of this coroutine run concurrently, one per master and one per slave
            '''
            
            try:
                self.print (f'Instantiated socket: {socket}')
                
                jsonSocket = JsonSocket (socket)

                command, role, clientId = None, None, None                  # Init, since the recv may already trigger an exception that needs this info
                command, role, clientId = await jsonSocket.recv (socket)
                
                if command == 'register':
                    await self.send (jsonSocket, True)                      # Confirm successful registration

                    if role == 'master':
                        self.commandQueues [clientId] = asyncio.Queue ()    # This will also replace an abandoned queue by an empty one
                        await self.created (clientId, self.replyQueues)
                        
                        while True:
                            # Receive command from own master
                            message = await self.recv (socket, role)
                            
                            # Put it in the queue belonging to the right slave
                            try:
                                await self.commandQueues [message [0]] .put ([bankCode] + message [1:])
                                
                                # Get reply of slave from own master queue and send it to master
                                # The master gives a command to only one slave at a time, so he knows who answered
                                await self.send (socket, role, await self.replyQueues [bankCode] .get ())                            
                            except KeyError:
                               self.reportUnknownBankCode (message [0])
                               await self.send (socket, role, False)                            
                    else:
                        self.replyQueues [bankCode] = asyncio.Queue ()      # This will also replace an abandoned queue by an empty one
                        await self.created (bankCode, self.commandQueues)
                        
                        while True:                     
                            # Wait until command in own slave queue
                            message = await self.commandQueues [bankCode] .get ()
                            
                            # Send it to own slave
                            await self.send (socket, role, message [1:])
                                                   
                            # Get reply from own slave and put it in the right reply queue
                            try:
                                await self.replyQueues [message [0]] .put (await self.recv (socket, role))
                            except:
                                self.reportUnknownBankCode (message [0])
                else:
                    raise self.RegistrationError ()
            except self.RegistrationError:
                try:
                    await socket.send (json.dumps (False), role)            # Try to notify client
                except:
                    pass                                                    # Escape if client closed connection
                    
                self.print (f'Error: registration expected, got command: {command}')
            except websockets.exceptions.ConnectionClosed:
                self.print (f'Error: connection closed by {bankCode} as {role}')
            except Exception:
                self.print (f'Error: in serving {bankCode} as {role}\n{traceback.format_exc ()}')
    
    
    
    
        async def serverLoop (socket):
            '''
            - Called once for each client
            - Handles the socket belonging to the client that it's called for
            - Remains looping for that client until connection is closed
            - So several calls of this coroutine run concurrently, one per client
            '''  
            try:
                jsonSocket = JsonSocket (socket) 
                while True:
                    self.command = await jsonSocket.recv ()
                    self.handleCommand ()
                    await jsonSocket.send (self.reply ())                            
            except websockets.exceptions.ConnectionClosed:
                print (f'Error: connection closed by client')
            except Exception as exception:
                print (f'Error: {exception}')

        
        # Create message queue dicts
        self.commandQueues = {}        
        self.replyQueues = {} 
        
        # Start server loop creator and keep it running forever, waiting for new clients
        serverFuture = websockets.server (self.serverLoop, self.hostName, self.portNr)
        asyncio.get_event_loop () .run_until_complete (serverFuture)
        
        # Prevent termination of event loop, since server loops are subscribed to it
        syncio.get_event_loop () .run_forever ()
    
class Proxy:
    ''' A generalized proxy class
    
    Proxies locally represent remote objects.
    Any attribute (method or data) access on them is passed on to the remote object.
    If the remote object doesn't support the attribute, a local exception is raised.
    
    Remote objects are never locally instantiated directly.
    They just are obtained from the exchange.
    While they seem to have a class identical to the remote one,
    this local proxy class is a mere dummy (for now).
    
    It's not yet completely clear where this may make the ship strand.
    Things like 'isinstance' are bound to be influenced by it.
    This bridge will be crossed when experiments or practical demands take us there.
    '''  
    
    def __init__ (self, exchange, jsock, uol):                  # uol ('jewel') == universal object locator
        self.__ns_exchange__ = exchange
        self.__ns_jsock__ = jsock
        self.__ns_uol__ = uol
        
    def __setattr__ (self, name, value):
        self.__ns_jsock__.send (['set', name, value])
        self.__ns_jsock__.recv ()
        
    def __getattr__ (self, name):
        self.__ns_jsock__.send (['get', name])                  # Get attribute
        reply = self.__ns_jsock__.recv ()
        if reply [0] == 'ret':                                  # Attribute is field or parameterless method
            return reply [1:]                                   # Reply is return value of parameterless method
        elif reply [0] == 'par':                                # Attribute is method with parameters
            def bound (args, kwargs):
                self.__ns_jsock__.send ('arg', args, kwargs)    # Send args
                if reply [0] == 'ret':                          # Reply is return value of method with parameters
                    return reply [1:]
                else:
                    raise Exception ("Expected reply 'ret', got '{reply [0]}' instead")
            return bound
        else:
            raise Exception  ("Expected reply 'ret' or 'par', got '{reply [0]}' instead")
        '''
        All other reactions of the counter party are not received directly, but according to the following possibilities:
        - via a recursive call to __getattr__ of this object, e.g. if a different attribute is retrieved
        - via a call to __setattr__ of this object, if an attribute is stored
        - not directed towards this object at all, but to a different object $$$
        
        Note that a recursive call to __getattr__ may be the result of retrieving a different attribute on this same object.
        '''
            


class Client:
            
class Server:



    ''' A server deals with requests from a Proxy
    
    First it locates the object using the uol.
    Then it uses the object to set or get the attribute
    Then, if the attribute is a method, it will receive the arguments
    '''
    
    def __init__ (self):
        self.objects = {}   # Should become a remotely available dictionary
        self.listen ()      # Shouldn't block, of course...
        
    def register (self, anObject, qualifiedName):
        self.objects [qualifiedName]
        
    def resolve (self, qualifiedName):
        self.objects [qualifiedName]
        
    def listen (self):
        message = await self.recv ()
        anObject = self.resolve (message [0])
        if message [1] == 'set':
            setattr (anObject, message [2], message [3])
        elif message [1] == 'get':
            attribute = getattr (anObject, message [2]):
            if callable (attribute):
                await self.send (False, None)
            else:
                await self.send (True, attribute)
        elif message [1] == 'arg':
            await self.send (True, attribute (*args, **kwargs))

delegator = Delegator ()    # Class, despite singleton, for future flexibility a.o.

def register (*args, **kwargs):
    delegator.register (*args, **kwargs)

def resolve (*args, **kwargs):
    delegator.resolve (*args, **kwargs)
    