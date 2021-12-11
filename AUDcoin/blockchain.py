import hashlib
import json
import jsonpickle
from flask import Flask		# This library is used for backend Web Development
from urllib.parse import urlparse
from Crypto.PublicKey import RSA # We import the RSA & PublicKey functions from Crypto library
from Crypto.Signature import *	# We import the Signature functions from Crypto library
from datetime import datetime
import requests
import time
import random


class Blockchain (object):
    
	def __init__(self):
		self.chain = [self.addGenesisBlock()];
		self.pendingTransactions = [];
		self.difficulty = 5;
		self.minerRewards = 50;
		self.blockSize = 15;
		self.nodes = set();
  
	def addGenesisBlock(self):
		tArr = [];	#Transaction Array
		tArr.append(Transaction("me", "you", 10));
		genesis = Block(tArr, datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), 0);
		genesis.prev = "None";
		return genesis;

	def minePendingTransactions(self, miner):
		
		lenPT = len(self.pendingTransactions);
		if(lenPT <= 2):
			print("Not enough transactions to mine! (Must be > 2)")
			return False;
		else:
			for i in range(0, lenPT, self.blockSize):

				end = i + self.blockSize;
				if i >= lenPT:
					end = lenPT;
				
				transactionSlice = self.pendingTransactions[i:end];
				newBlock = Block(transactionSlice, datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), len(self.chain));
				print(type(self.getLastBlock()));

				hashVal = self.getLastBlock().hash;
				newBlock.prev = hashVal;
				newBlock.mineBlock(self.difficulty);
				self.chain.append(newBlock);
			print("Mining Transactions Success!");

			payMiner = Transaction("Miner Rewards", miner, self.minerRewards);
			self.pendingTransactions = [payMiner];
		return True;

	def addTransaction(self, sender, reciever, amt, keyString, senderKey):
		keyByte = keyString.encode("ASCII");
		senderKeyByte = senderKey.encode("ASCII");
		print(type(keyByte), keyByte);
		key = RSA.importKey(keyByte);
		senderKey = RSA.importKey(senderKeyByte);
		if not sender or not reciever or not amt:
			print("transaction error 1");
			return False;

		transaction = Transaction(sender, reciever, amt);
		transaction.signTransaction(reciever,sender);

		if not transaction.isValidTransaction():
			print("transaction error 2");
			return False;
		self.pendingTransactions.append(transaction);
		return len(self.chain) + 1;

	def getLastBlock(self):

		return self.chain[-1];

	def isValidChain(self):
		for i in range(1, len(self.chain)):
			b1 = self.chain[i-1];
			b2 = self.chain[i];

			if not b2.hasValidTransactions():
				print("error 3");
				return False;

			if b2.hash != b2.calculateHash():
				print("error 4");
				return False;


			if b2.prev != b1.hash:
				print("error 5");
				return False;
		return True;

	def generateKeys(self):
		key = RSA.generate(2048)
		private_key = key.exportKey()
		file_out = open("private.pem", "wb")
		file_out.write(private_key)

		public_key = key.publickey().exportKey()
		file_out = open("receiver.pem", "wb")
		file_out.write(public_key)
		
		print(public_key.decode('ASCII'));
		return key.publickey().exportKey().decode('ASCII');

	def getBalance(self, person):
		balance = 0
		for i in range(1, len(self.chain)):
			block = self.chain[i];
			try:
				for j in range(0, len(block.transactions)):
					transaction = block.transactions[j];
					if(transaction.sender == person):
						balance -= transaction.amt;
					if(transaction.reciever == person):
						balance += transaction.amt;
			except AttributeError:
				print("no transaction")
		return balance + 1000;

	def chainJSONencode(self):

		blockArrJSON = [];
		for block in self.chain:
			blockJSON = {};
			blockJSON['hash'] = block.hash;
			blockJSON['index'] = block.index;
			blockJSON['prev'] = block.prev;
			blockJSON['time'] = block.time;
			blockJSON['nonse'] = block.nonse;


			transactionsJSON = [];
			tJSON = {};
			for transaction in block.transactions:
				tJSON['time'] = transaction.time;
				tJSON['sender'] = transaction.sender;
				tJSON['reciever'] = transaction.reciever;
				tJSON['amt'] = transaction.amt;
				tJSON['hash'] = transaction.hash;
				transactionsJSON.append(tJSON);

			blockJSON['transactions'] = transactionsJSON;

			blockArrJSON.append(blockJSON);

		return blockArrJSON;

	def chainJSONdecode(self, chainJSON):
		chain=[];
		for blockJSON in chainJSON:

			tArr = [];
			for tJSON in blockJSON['transactions']:
				transaction = Transaction(tJSON['sender'], tJSON['reciever'], tJSON['amt']);
				transaction.time = tJSON['time'];
				transaction.hash = tJSON['hash'];
				tArr.append(transaction);


			block = Block(tArr, blockJSON['time'], blockJSON['index']);
			block.hash = blockJSON['hash'];
			block.prev =blockJSON['prev'];
			block.nonse = blockJSON['nonse'];

			chain.append(block);
		return chain;
		
	def register_node(self, address):
		parsedUrl = urlparse(address)
		self.nodes.add(parsedUrl.netloc)


class Block (object):
	def __init__(self, transactions, time, index):
		self.index = index;
		self.transactions = transactions;
		self.time = time;
		self.prev = '';
		self.nonse = random.randint(1,1000000000);
		self.hash = self.calculateHash();


	def calculateHash(self):
		hashTransactions = "";
		for transaction in self.transactions:
			hashTransactions += transaction.hash;
		hashString = str(self.time) + hashTransactions + "24 hr" + self.prev + str(self.nonse);
		hashEncoded = json.dumps(hashString, sort_keys=True).encode();
		return hashlib.sha256(hashEncoded).hexdigest();

	def mineBlock(self, difficulty):
		arr = [];
		for i in range(0, difficulty):
			arr.append(i);
		
		#compute until the beginning of the hash = 0123..difficulty
		arrStr = map(str, arr);
		hashPuzzle = ''.join(arrStr);
		print(len(hashPuzzle));
		while self.hash[0:difficulty] != hashPuzzle:
			self.nonse += 1;
			self.hash = self.calculateHash();
			#print(len(hashPuzzle));
			#print(self.hash[0:difficulty]);
		print("Block Mined!");
		return True;

	def hasValidTransactions(self):
		for i in range(0, len(self.transactions)):
			transaction = self.transactions[i];
			if not transaction.isValidTransaction():
				return False;
			return True;
	
	def JSONencode(self):
		return jsonpickle.encode(self);
	
class Transaction (object):
	def __init__(self, sender, reciever, amt):
		self.sender = sender;
		self.reciever = reciever;
		self.amt = amt;
		self.time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"); #change to current date
		self.hash = self.calculateHash();


	def calculateHash(self):
		hashString = self.sender + self.reciever + str(self.amt) + str(self.time);
		hashEncoded = json.dumps(hashString, sort_keys=True).encode();
		return hashlib.sha256(hashEncoded).hexdigest();

		
	def isValidTransaction(self):

		if(self.hash != self.calculateHash()):
			return False;
		if(self.sender == self.reciever):
			return False;
		if(self.sender == "Miner Rewards"):
			#security : unfinished
			return True;
		if not self.signature or len(self.signature) == 0:
			print("No Signature!")
			return False;
		return True;
		#needs work!

	def signTransaction(self, key, senderKey):
		if(self.hash != self.calculateHash()):
			print("transaction tampered error");
			return False;
		#print(str(key.publickey().exportKey()));
		#print(self.sender);
		#if(str(key.publickey().exportKey()) != str(senderKey.publickey().exportKey())):
			print("Transaction attempt to be signed from another wallet");
			return False;
		#h = MD5.new(self.hash).digest();
		#pkcs1_15.new(key);
		self.signature = "made";
		#print(key.sign(self.hash, ""));
		print("made signature!");
		return True;