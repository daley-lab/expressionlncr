#!/usr/bin/env python2
# Example job to test the NCBI job manager

from datetime import datetime
import time

from ncbi_job_manager import NCBIJobManager
from ncbi_job_interface import NCBIJobInterface

class TestJob(NCBIJobInterface):
	uidList = []
	minSecondsPerJob = 1

	def __init__(self, uidList):
		self.uidList = uidList
	
	def run(self):
		for uid in self.uidList:
			print('got item: ' + str(uid))
			time.sleep(self.minSecondsPerJob)

def __main__():
	print('Testing TestJob...')
	manager = NCBIJobManager()
	list1 = [
			'mary',
			'had',
			'a'
		]
	list2 = [
			'little',
			'lamb'
		]
	job1 = TestJob(uidList=list1)
	job2 = TestJob(uidList=list2)
	jobStart = datetime.now()
	print('Start jobs @ ' + str(jobStart))
	manager.runJob(job1)
	job1Stop = datetime.now()
	print('End job 1 @ ' + str(job1Stop) + ' (total t=' + str(job1Stop-jobStart) + ')')
	manager.runJob(job2)
	job2Stop = datetime.now()
	print('End job 2 @ ' + str(job2Stop) + ' (total t=' + str(job2Stop-jobStart) + ')')
	manager.shutdown()
	print('Finished testing TestJob')

if __name__ == '__main__':
	__main__()
