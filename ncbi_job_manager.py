#!/usr/bin/env python2
# A job manager for submitting NCBI Entrez e-utils jobs to ensure no more than 
# X job threads is submitted every T seconds.
# Only 1 job manager instance should be created at a time.
#
# Job rate limiting: 3 jobs per second, AND limit to (weekends or 9pm-5am EST) for large queries.
#
#
#NOTE similar software. eutils.queryservice seems overly complicated for our purposes.
# biocommons/eutils interprets NCBI guidelines (I feel incorrectly) as: 
#  Weekdays 0500-2100 => 0.333s between requests; no throttle otherwise
#http://pythonhosted.org/eutils/modules/eutils.queryservice.html
#https://bitbucket.org/biocommons/eutils/

from threading import BoundedSemaphore, Thread
import time

class NCBIJobManager(object):
	#be conservative and allow only 1 connection at a time to Entrez e-utils, 1 job / second
	maxConnections = 1
	minSecondsPerJob = 1
	jobSem = None
	watchdogSem = None
	watchdogThreadRunning = False

	def reset(self):
		print('NCBIJobManager reset')
		self.isShutdown = False
		#one thread can go. python semaphore is not fair (not FIFO)
		self.jobSem = BoundedSemaphore(self.maxConnections)
		#no threads can go. python semaphore is not fair (not FIFO)
		self.watchdogSem = BoundedSemaphore(self.maxConnections)  
		self.watchdogThreadRunning = False
		self.startWatchdogThread()

	#synchronized so only one thread can run at a time
	def startWatchdogThread(self):
		#create watchdog thread that allows one job every X seconds
		if not self.watchdogThreadRunning:
			#protect from starting more than one watchdog thread
			self.watchdogThreadRunning = True
			Thread(target=self.watchdog).start()

	def watchdog(self):
		try:
			while not self.isShutdown:
				self.watchdogSem.acquire()  #block (wait) allowing a new job to queue via job semaphore
				time.sleep(self.minSecondsPerJob)  #seconds
				if not self.isShutdown:
					self.jobSem.release()  #allow one more job to queue up
		except Exception as err:
			print(('watchdog() Error: ' + str(err)))
			self.watchdogThreadRunning = False  #watchdog thread died, allow restart

	#should take NCBIJobInterface job
	def runJob(self, job):
		if not self.watchdogThreadRunning:
			self.reset()
		try:
			#either get the job semaphore or block the thread, waiting for a turn to run
			self.jobSem.acquire()
			#let the job run, THEN wake the watchdog to release another job. this is 
			# important because the jobs can repeatedly call NCBI for long ID lists.
			job.run()
			self.watchdogSem.release()
			#don't release the job semaphore, that's for the watchdog to do
		except Exception as err:
			print(('runJob() Error: ' + str(err)))

	#need to shutdown the watchdog thread when we're done with the job manager
	def shutdown(self):
		self.isShutdown = True
