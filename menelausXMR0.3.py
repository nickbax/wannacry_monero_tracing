# -*- coding: utf-8 -*-
"""
Menelaus v 0.3 XMR
reads in every transaction with a payment ID, checks if payment ID was used as shapeshift payment ID,
if it was used saves it to menelaus-xmr.txt
uses two parallel pools, 1 to scrape PIDs and a second to query shapeshift
@author: nick
"""

import urllib.request
import urllib.error
import csv
from multiprocessing.dummy import Pool  # This is a thread-based Pool
from multiprocessing import cpu_count
from multiprocessing import Pool
import time
import sys 
import requests
import json

OUTPUTFILE = 'shapeshift-menelaus-output1.txt'
def saveToFile(listToSave,output):
    with open(output, 'a+') as f:
        for item in listToSave:
            f.write(item+'\n')
    f.close()
    return
def getBlockTXIDs(height):
        # bitmonerod is running on the localhost and port of 18082
    url = "http://localhost:18081/json_rpc"

    # standard json header
    headers = {'content-type': 'application/json'}
    # bitmonerod' procedure/method to call
    rpc_input = {
           "method": "getblock",
           "params": {"height": height}
    }
    # add standard rpc values
    rpc_input.update({"jsonrpc": "2.0", "id": "0"})

    # execute the rpc request
    response = requests.post(
        url,
        data=json.dumps(rpc_input),
        headers=headers)
    # the response will contain binary blob. For some reason
    # python's json encoder will crash trying to parse such
    # response. Thus, its better to remove it from the response.
 #   response_json_clean = json.loads(
 #                           "\n".join(filter(
 #                               lambda l: "blob" not in l, response.text.split("\n")
  #                          )))
    # pretty print json output
    #print(json.dumps(response_json_clean, indent=4))
    response_json = response.json() 
    if "result" in response_json:
        if "tx_hashes" in response_json["result"]:
            txList = response_json["result"]["tx_hashes"] #list of txs in block
        else:
            return False            
    return txList

def findEOL( s , first):
    try:
        start = s.index ( first ) + len( first)
        end = len(s)
        return s[start:end]
    except ValueError:
        return ""
def getTransactionJSON(txid):
    PARAMS = {'txs_hashes' : [txid],'decode_as_json' : True}
    myTransaction = requests.post("http://localhost:18081/get_transactions", json = PARAMS)
    transactionJSON = myTransaction.json()
    return transactionJSON["txs_as_json"][0]    
def getTransaction(txid):
    PARAMS = {'txs_hashes' : [txid],'decode_as_json' : False}
    myTransaction = requests.post("http://localhost:18081/get_transactions", json = PARAMS)
    return myTransaction.json()['txs'][0]

def decToHex(dec_array):
    hex_array = [hex(x).replace('x','0')[-2:] for x in dec_array]
    return hex_array

def getPaymentID(transaction):
    txJson = getTransactionJSON(transaction)
    stringList = txJson.splitlines() 
    extraField = []
    for line in stringList: #find the line that contains the extra field
        if "extra" in line:  
            extraString = findEOL(line, 'extra\": [ ')
            if(extraString[0:1]=='1'):
                return False
            break
    extraDecArray = []
    
    extraList = extraString.split(',')
    for decimal in extraList: #convert extra field (which is string) to int so we can use hex()
        extraDecArray.append(int(decimal))
    if(extraDecArray[2]!=0):
        return False
    extraField = decToHex(extraDecArray[3:35])
    thingToReturn=''.join(extraField)
    return thingToReturn,transaction

def getShapeshiftData(pidTuple): #takes a tuple (pid,txid)
    #print(address)
    try:  
        url="https://shapeshift.io/txstat/"+pidTuple[0]
        with urllib.request.urlopen(url) as response:
            html = response.read()
            htmlString = html.decode("utf-8").replace('{','').replace('}','')
           # print(htmlString)
    
            #handles most of the errors encountered.
    except urllib.error.URLError as e:
            print('HtmlDownLoader download error:', e.reason)
            time.sleep(5)
            return(False)
    if htmlString[0]=='<':#this is a weird error that happens rarely. Just repeat
        time.sleep(1)
        print('weird < error')
        repeat= getShapeshiftData(pidTuple)
        return repeat
    return htmlString,pidTuple[1]
    
def main():
    #Goes through every block

    STARTBLOCK = 1429266#1065000-1068009 #1320000-1475211
    ENDBLOCK = 1500000

    numCores=23
    blockTXIDs=[]
    oldstylePidList = []
    blockList=[]
    superTxList =[]
    shapeshiftTxList=[]
    for block_height in range(STARTBLOCK,ENDBLOCK):#Goes through every block in the range
        print(block_height) 

        #make a list of 14 blocks
        blockList.append(block_height)
        
        #when we have 14 blocks, make a list of all the TXIDs in the blocks
        if len(blockList)%numCores==0:
            blockTxidPool=Pool(numCores)
            multiBlockTXIDs=blockTxidPool.imap(getBlockTXIDs,blockList)#gets txids for each block in blockList
            blockList=[]
            for blockTXIDs in multiBlockTXIDs:
                if blockTXIDs!=False:
                    for txid in blockTXIDs:
                        superTxList.append(txid)#super tx list is list of txs for multiple blocks
            blockTxidPool.close()

            if len(superTxList)>=numCores*4:#if we have a list of numCores*4 or more TXs
                    pool = Pool(numCores)
                    pidList = pool.imap(getPaymentID, superTxList) # gets PIDs for each txid
                    blockTXIDs=[]
                    superTxList =[]
                    for pid in pidList:
                        if pid!=False:#if there's an old-style PID, check if it's a shapeshift deposit
                            oldstylePidList.append(pid) #pids are a tuple (pid,txid)
                    pool.close()
                    if len(oldstylePidList)>=numCores*4:#if we have 14 or more oldstyle PIDs then do the shapeshift requests
                        pool = Pool(numCores)
                        shapeshiftResponses=pool.imap(getShapeshiftData,oldstylePidList)
                        oldstylePidList=[]
                        for response in shapeshiftResponses:
                            if response!= False:
                                if type(response[0])!=str:
                                    print('not string')
                                if response[0][10:12]!='er':#if shapeshift doesn't respond with an error
                                    shapeshiftTxList.append(response[0]+','+response[1])#add it to the list
                        pool.close()
        if len(shapeshiftTxList)>0:
            saveToFile(shapeshiftTxList,OUTPUTFILE)
            shapeshiftTxList=[]
            print('ooo000 *saving* 000ooo')
    #print(sorted(mixinDict))

if __name__ == "__main__":
    main()
    
