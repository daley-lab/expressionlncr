#!/usr/bin/env python2
# Example ncbi e-utils job actually querying entrez/e-utils.
# Supports long parameters (e.g. id lists) via splitting across multiple requests.
# See test_job.py for a simpler test of the job manager.

from datetime import datetime
import sys
import time
import urllib

import downloader
from ncbi_job_manager import NCBIJobManager
from ncbi_job_interface import NCBIJobInterface

class NCBIJob(NCBIJobInterface):
	baseurl = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
	output = 'ncbijob_output.xml'
	uidList = []
	urlMax = 4000
	retmax = urlMax/2  #since comma if single character ids

	def __init__(self, output, uidList):
		self.output = output
		self.uidList = uidList

	def run(self):
		if (len(self.uidList) > 0):
			uidCount = 0
			queryCount = 0
			#iterate through our list of elements
			while (uidCount < len(self.uidList)):
				#build up our long parameter until it is as big as a url allows.
				# differs depending on webserver. limit to 4000 characters to be safe
				longparam = ''
				urlCount = 0
				while (uidCount < len(self.uidList) and urlCount < self.urlMax):
					uid = self.uidList[uidCount]
					#allow only rs numbers
					if (str(uid).lower()[:2] == 'rs'):
						uid = uid[2:]
						#snp id must be numeric
						if uid.isdigit():
							longparam += str(uid) + ','
							urlCount += len(str(uid)) + 1  # +1 for the comma
					uidCount += 1  #iterate through list regardless of whether element added
				#trim off last comma, build url, and get content
				longparam = longparam[:-1]
				params = urllib.urlencode({
					'db': 'snp',
					'id': longparam,
					'retmax': self.retmax,
					'retstart': '0',
					'usehistory': 'n',
					'version': '2.0',
					'email': 'genapha@hli.ubc.ca',
					'tool': 'ncbi_job.py'
				})
				url = self.baseurl + ('?%s' % params)
				print 'Querying NCBI eSearch: ' + str(url)
				xmlFileNumStr = '.' + str(queryCount) if queryCount > 0 else ''
				downloader.simpleDownload(url, self.output + xmlFileNumStr)
				queryCount += 1
				time.sleep(1)  #seconds

def __main__():
	manager = NCBIJobManager()
	snpList1 = [
			'rs1837253',
			'rs1873253',
			'rs3'
		]
	snpList2 = [
			'rs4',
			'rs3'
		]
	job1 = NCBIJob(output='data/job1.xml', uidList=snpList1)
	job2 = NCBIJob(output='data/job2.xml', uidList=snpList2)
	jobStart = datetime.now()
	print 'Start jobs @ ' + str(jobStart)
	manager.runJob(job1)
	job1Stop = datetime.now()
	print 'End job 1 @ ' + str(job1Stop) + ' (total t=' + str(job1Stop-jobStart) + ')'
	manager.runJob(job2)
	job2Stop = datetime.now()
	print 'End job 2 @ ' + str(job2Stop) + ' (total t=' + str(job2Stop-jobStart) + ')'
	manager.shutdown()
	print 'Finished testing NCBIJob'
	sys.exit(0)

if __name__ == '__main__':
	__main__()
