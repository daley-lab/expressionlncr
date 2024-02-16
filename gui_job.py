#!/usr/bin/env python2
#
#Classes for running python scripts from the GUI
#


import datetime
import os
import sys
import PySide
from PySide.QtCore import *


#class that starts a new process for a python job.
class GuiJob(QObject):
  types = (LNCRNA, PROBE, OVERLAP, EXPRESSION, EXPRESSION_SEARCH, RESULTS) = range(6)
  typeNames = ['Downloading lncRNA', 'Downloading Ensembl probe information',
      'Finding lncRNA/probe overlap', 'Downloading expression probes',
      'Searching for expression probes', 'Parsing results'
  ]
  started = Signal()
  finished = Signal()
  error = Signal()
  jobProgram = 'python'  #python2 causes problems on Windows default python install

  #job is [] of args
  def __init__(self, jobArgs=None, jobProgram=None):
    super(GuiJob, self).__init__()
    if jobProgram:
      self.jobProgram = jobProgram
    self.jobArgs = jobArgs

  #start up the job
  def start(self):
    self.process = QProcess()
    self.process.started.connect(self.__onStarted)
    self.process.finished.connect(self.__onFinished)
    self.process.error.connect(self.__onError)
    self.process.readyReadStandardOutput.connect(self.__onReadyReadStandardOutput)
    self.process.readyReadStandardError.connect(self.__onReadyReadStandardError)
    self.process.start(self.jobProgram, self.jobArgs)

  #emit gui updates at certain stages of task.
  def __onStarted(self):
    print 'Started job @ %s' % datetime.datetime.now()
    self.started.emit()

  def __onFinished(self):
    print 'Finished job @ %s' % datetime.datetime.now()
    self.finished.emit()

  def __onError(self):
    print sys.stderr, 'Error running job @ %s:\n\t%s %s' % (datetime.datetime.now(),
        self.jobProgram, self.jobArgs)
    self.error.emit()

  def __onReadyReadStandardOutput(self):
    output = self.process.readAllStandardOutput()
    print '%s' % output.__str__()

  def __onReadyReadStandardError(self):
    error = self.process.readAllStandardError()
    print 'Error: %s' % error.__str__()


##Class to communicate between the GUI jobs and the GUI.
##Contains signals to all buttons / UI elements to be enabled/disabled.
##Custom signals in PySide have some gotchas, see here:
## http://stackoverflow.com/questions/2970312/pyqt4-qtcore-pyqtsignal-object-has-no-attribute-connect
#class GuiJobCommunicator(QObject):
#  started = [Signal() for job in GuiJob.types]
#  finished = [Signal() for job in GuiJob.types]
#  error = [Signal() for job in GuiJob.types]
#
#  def __init__(self):
#    QObject.__init__(self)
#  
#  #note: only one of each job type per signal
#  def start(self, jobType):
#    self.started[GuiJob.types[jobType]].emit()
#    
#  def finish(self, jobType):
#    self.finished[GuiJob.types[jobType]].emit()
#    
#  def errored(self, jobType):
#    self.error[GuiJob.types[jobType]].emit()
    

def __main__():
  sys.exit(0)

if __name__ == '__main__':
  __main__()
