#!/usr/bin/env python3
#
#different forms and elements for the gui
#


#import pdb

import csv
import os
import re
import sys

from PySide6 import QtCore as qt
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

import constants as c
import gui_job as job
import get_ensembl_funcgen_organisms as funcgen
import org_array_gpl as org


# Need to convert unicode pretty print organism back to Ensembl funcgen database organism key.
# ref: https://ftp.ensembl.org/pub/current/mysql
# ex: 'homo_sapiens_funcgen_85_38': 'Homo sapiens v85.38 (Human)'
def getOrgKeyFromPrettyUnicode(organism, availableOrganisms={}):
  orgKey = None
  for (key, val) in availableOrganisms.items():
    # If the first word of the organism string is in the dictionary value good enough
    if organism.split(' ')[0] in val:
      orgKey = key.strip()
      return orgKey

#return human readable file size from a size in bytes
def getHumanReadableSize(size, suffix='B'):
  for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
    if abs(size) < float(1000):
      return '%3.1f %s%s' % (size, unit, suffix)
    size /= float(1000)
  return '%.1f %s%s' % (size, 'Y', suffix)


#ensure all message boxes have main app title
class AppMessageBox(qtw.QMessageBox):
  @staticmethod
  def question(*args, **kwargs):
    nargs = list(args)
    if len(nargs) > 1:
      nargs[1] = c.APP_TITLE
    elif kwargs:
      kwargs['title'] = c.APP_TITLE
    return qtw.QMessageBox.question(*nargs, **kwargs)


#convenience class to display an error message to the user
class ErrorMessageBox(AppMessageBox):
  @staticmethod
  def show(parent=None, error=None):
    if not error:
      error = c.ERROR_DEFAULT
    return AppMessageBox.question(parent, '', error, 
        qtw.QMessageBox.Ok, qtw.QMessageBox.Ok)


class HorizontalRule(qtw.QFrame):
  def __init__(self, parent=None):
    super(HorizontalRule, self).__init__(parent)
    self.setFrameShape(qtw.QFrame.HLine)
    self.setFrameShadow(qtw.QFrame.Sunken)


class WrappedLabel(qtw.QLabel):
  def __init__(self, parent=None):
    super(WrappedLabel, self).__init__(parent)
    self.setWordWrap(True)


#pair of file text field and choose button linked to QFileDialog
class FileChooser(qtw.QWidget):
  def __init__(self, parent=None, dialogType=None, fileTypes=None, title=None):
    super(FileChooser, self).__init__(parent)
    self.dialogType = dialogType
    self.fileTypes = fileTypes if fileTypes else c.CHOOSER_FILE_TYPES
    self.title = title if title else (c.CHOOSER_SAVE_TITLE if dialogType == 'save' else c.CHOOSER_TITLE)
    layout = qtw.QHBoxLayout()
    self.fileLabel = qtw.QLabel()
    if dialogType == c.SAVE_DIALOG_TYPE or dialogType == c.DIRECTORY_SAVE_DIALOG_TYPE:
      message = c.CHOOSER_SAVE_BUTTON_MSG
    else:
      message = c.CHOOSER_BUTTON_MSG
    chooseButton = qtw.QPushButton(message)
    chooseButton.clicked.connect(self.onClick)
    layout.addWidget(self.fileLabel)
    layout.addWidget(chooseButton)
    self.setLayout(layout)

  @qt.Slot()
  def onClick(self):
    if not self.fileLabel.text():
      currentDir = None
    else:
      currentDir = os.path.dirname(os.path.abspath(self.fileLabel.text()))
    startLocation = currentDir if currentDir else c.CHOOSER_START_LOCATION
    #open up the file choose dialogue
    if self.dialogType == c.SAVE_DIALOG_TYPE:
      (filename, selectedFilter) = qtw.QFileDialog.getSaveFileName(self, self.title,
        startLocation, self.fileTypes)
    elif self.dialogType == c.OPEN_DIALOG_TYPE:
      (filename, selectedFilter) = qtw.QFileDialog.getOpenFileName(self, self.title,
        startLocation, self.fileTypes)
    elif self.dialogType == c.DIRECTORY_OPEN_DIALOG_TYPE:
      filename = qtw.QFileDialog.getExistingDirectory(parent=self, caption=self.title,
        dir=startLocation, options=qtw.QFileDialog.ShowDirsOnly)
    else:
      print(sys.stderr, 'Invalid dialog type passed to FileChooser %s' % (self.dialogType))
    #if user cancels don't reset
    if filename:
      self.fileLabel.setText(filename)

  def setText(self, text):
    self.fileLabel.setText(text)

  def text(self):
    return self.fileLabel.text()


#adds method to set current index by label text not just by integer index
class ComboBox(qtw.QComboBox):
  def __init__(self, parent=None):
    super(ComboBox, self).__init__(parent)

  def setCurrentOption(self, label):
    labelIndex = -1
    for i in range(0, self.count()):
      if label.lower() in self.itemText(i).lower():
        labelIndex = i
        break
    self.setCurrentIndex(labelIndex)

  def setCurrentOptions(self, labels):
    flag = -1
    labelIndex = flag
    for i in range(0, self.count()):
      text = self.itemText(i).lower()
      for label in labels:
        if label in text:
          labelIndex = i
          break
      if labelIndex != flag:
        break
    self.setCurrentIndex(labelIndex)


#base class for all the tabbed widget forms
class GuiForm(qtw.QWidget):
  def __init__(self, parent=None, continueCallback=None):
    super(GuiForm, self).__init__(parent)
    self.continueCallback = continueCallback

  def getJobArgs(self):
    raise NotImplementedError('Needs to be implemented in each form')

  def getJobType(self):
    raise NotImplementedError('Needs to be implemented in each form')

  def getGuiVars(self):
    raise NotImplementedError('Needs to be implemented in each form')

  def autofill(self, guiVars):
    raise NotImplementedError('Needs to be implemented in each form')

  @qt.Slot()
  def onRunButton(self):
    print('Setting up job: %s...' % job.GuiJob.typeNames[self.getJobType()])
    self.jobArgs = self.getJobArgs()
    if not self.jobArgs:
      ErrorMessageBox.show(self, c.ERROR_INVALID_JOB)
      raise ValueError('No job arguments')
    self.jobType = self.getJobType()
    #call a new gui job process
    print('Job args: %s' % (' '.join(self.jobArgs)))
    self.job = job.GuiJob(jobArgs=self.jobArgs)
    self.job.started.connect(self.onJobStarted)
    self.job.finished.connect(self.onJobFinished)
    self.job.errorOccurred.connect(self.onJobError)
    self.job.start()

  @qt.Slot()
  def onJobStarted(self):
    #make cursor spinny in this frame and disable the run button
    self.setCursor(qtg.QCursor(qt.Qt.CursorShape.WaitCursor))
    self.runButton.setDisabled(True)

  @qt.Slot()
  def onJobFinished(self):
    #done. advance forward the current tab
    self.runButton.setEnabled(True)
    self.unsetCursor()
    self.continueCallback()

  @qt.Slot()
  def onJobError(self):
    print('Error: running job %s' % (job.GuiJob.typeNames[self.getJobType()]))
    ErrorMessageBox.show(self, c.ERROR_RUNNING_JOB)


#application entry form. should overview steps in application with shortcut to different 
# part of workflow.
class GreeterForm(GuiForm):
  def __init__(self, parent=None, continueCallback=None):
    super(GreeterForm, self).__init__(parent)
    #main layout for form
    layout = qtw.QVBoxLayout()
    #greeting label
    greeting = WrappedLabel(c.GREETER_TEXT)
    layout.addWidget(greeting)
    layout.addStretch()
    #add layout for button and push to far right
    buttonBox = qtw.QHBoxLayout()
    buttonBox.addStretch()
    #continue button to next tab
    continueButton = qtw.QPushButton(c.GREETER_BUTTON_MSG)
    continueButton.clicked.connect(continueCallback)
    buttonBox.addWidget(continueButton)
    layout.addLayout(buttonBox)
    #set layout
    self.setLayout(layout)

  def getGuiVars(self):
    return {}

  def autofill(self, guiVars):
    pass


#form to start up job to grab lncrna bed file
class LncrnaForm(GuiForm):
  def __init__(self, parent=None, continueCallback=None):
    super(LncrnaForm, self).__init__(parent, continueCallback)
    #form title and description
    layout = qtw.QVBoxLayout()
    title = qtw.QLabel(c.LNCRNA_TITLE)
    subtitle = WrappedLabel(c.LNCRNA_SUBTITLE)
    layout.addWidget(title)
    layout.addWidget(subtitle)
    layout.addStretch()
    #options form
    formLayout = qtw.QFormLayout()
    self.source = ComboBox()
    self.source.addItems([val for (key, val) in c.LNCRNA_SOURCE_ITEMS.items()])
    self.source.currentIndexChanged.connect(self.onChangeSource)
    self.sourceFile = FileChooser(dialogType=c.OPEN_DIALOG_TYPE, fileTypes=c.BED_FILE_TYPE)
    self.sourceFile.hide()
    self.organism = ComboBox()
    self.organism.addItems(sorted([val for (key, val) in c.LNCRNA_NONCODE_ORGANISMS.items()]))
    self.output = FileChooser(dialogType=c.SAVE_DIALOG_TYPE, fileTypes=c.BED_FILE_TYPE)
    formLayout.addRow(c.LNCRNA_SOURCE_MSG, self.source)
    formLayout.addRow(c.LNCRNA_SOURCE_FILE_MSG, self.sourceFile)
    formLayout.addRow(c.LNCRNA_ORGANISM_MSG, self.organism)
    formLayout.addRow(c.LNCRNA_OUTPUT_MSG, self.output)
    #run button
    runLayout = qtw.QHBoxLayout()
    runLayout.addStretch()
    self.runButton = qtw.QPushButton(c.LNCRNA_RUN_BUTTON_MSG)
    self.runButton.clicked.connect(self.onRunButton)
    runLayout.addWidget(self.runButton)
    #add the layouts
    layout.addLayout(formLayout)
    layout.addStretch()
    layout.addLayout(runLayout)
    self.setLayout(layout)
    
  @qt.Slot()
  def onChangeSource(self):
    #if source changed to custom show file chooser for custom file
    if self.source.currentText() == c.LNCRNA_SOURCE_ITEMS['custom']:
      self.sourceFile.show()
    else:
      self.sourceFile.hide()
    #if source changed to lncipedia set organism to human and grey out the field (user can't edit)
    if self.source.currentText() == c.LNCRNA_SOURCE_ITEMS['lncipedia']:
      #set to index of human option by default
      self.organism.setCurrentOptions(['homo', 'human'])
      self.organism.setDisabled(True)
    else:
      self.organism.setEnabled(True)

  def getJobArgs(self):
    jobArgs = None
    if self.source.currentText() == c.LNCRNA_SOURCE_ITEMS['custom']:
      if os.path.isfile(self.sourceFile.text()) and os.access(self.sourceFile.text(), os.R_OK):
        #file exists and we can read it
        jobArgs = ['get_lncrna.py', '--custom-bed', os.path.normpath(self.sourceFile.text()), \
            '--organism', self.organism.currentText(), os.path.normpath(self.output)]
      else:
        print(sys.stderr, 'Error: could not read file: %s' % self.sourceFile.text())
    elif self.source.currentText() == c.LNCRNA_SOURCE_ITEMS['lncipedia']:
      jobArgs = ['get_lncrna.py', '--lncipedia', '--organism', 'hg38', \
          os.path.normpath(self.output.text())]
    else:
      #convert organism from pretty print dictionary value to key needed for url.
      #ex. 'hg38': 'Human (hg38)'
      for (key, val) in c.LNCRNA_NONCODE_ORGANISMS.items():
        if val == self.organism.currentText():
          orgKey = key.strip()
      jobArgs = ['get_lncrna.py', '--noncode', '--organism', orgKey, \
          os.path.normpath(self.output.text())]
    return jobArgs

  def getJobType(self):
    return job.GuiJob.LNCRNA

  def getGuiVars(self):
    guiVars = {
        'lncrnaSource': self.source.currentText(),
        'lncrnaOrganism': self.organism.currentText(),
        'lncrnaOutput': os.path.normpath(self.output.text()),
        'lncrnaSourceFile': None
    }
    if self.source.currentText() == c.LNCRNA_SOURCE_ITEMS['custom']:
      guiVars['lncrnaSourceFile'] = os.path.normpath(self.sourceFile.text())
    return guiVars

  def autofill(self, guiVars):
    self.source.setCurrentOption(guiVars['lncrnaSource'])
    self.organism.setCurrentOption(guiVars['lncrnaOrganism'])
    self.output.setText(os.path.normpath(guiVars['lncrnaOutput']))


#form to get Ensembl (major) expression array probe information
class ProbeForm(GuiForm):
  def __init__(self, parent=None, continueCallback=None):
    super(ProbeForm, self).__init__(parent, continueCallback)
    #form title and description
    layout = qtw.QVBoxLayout()
    title = qtw.QLabel(c.PROBE_TITLE)
    subtitle = WrappedLabel(c.PROBE_SUBTITLE)
    layout.addWidget(title)
    layout.addWidget(subtitle)
    layout.addStretch()
    #options form
    formLayout = qtw.QFormLayout()
    self.organism = ComboBox()
    self.dataDir = FileChooser(dialogType=c.DIRECTORY_OPEN_DIALOG_TYPE)
    self.output = FileChooser(dialogType=c.SAVE_DIALOG_TYPE, fileTypes=c.BED_FILE_TYPE)
    self.refreshButton = qtw.QPushButton(c.PROBE_REFRESH_BUTTON_MSG)
    self.refreshButton.clicked.connect(lambda : self.refreshAvailableOrganisms(force=True))
    #organism combobox has smalll refresh button to right of it
    comboLayout = qtw.QHBoxLayout()
    comboLayout.addWidget(self.organism, stretch=4)
    comboLayout.addWidget(self.refreshButton, stretch=1)
    formLayout.addRow(c.PROBE_ORGANISM_MSG, comboLayout)
    #formLayout.addRow(c.PROBE_ORGANISM_MSG, self.organism)
    formLayout.addRow(c.PROBE_DATADIR_MSG, self.dataDir)
    formLayout.addRow(c.PROBE_OUTPUT_MSG, self.output)
    #run button
    runLayout = qtw.QHBoxLayout()
    runLayout.addStretch()
    self.runButton = qtw.QPushButton(c.PROBE_RUN_BUTTON_MSG)
    self.runButton.clicked.connect(self.onRunButton)
    runLayout.addWidget(self.runButton)
    #add the layouts
    layout.addLayout(formLayout)
    layout.addStretch()
    layout.addLayout(runLayout)
    self.setLayout(layout)
  
  #method to fetch the latest ensembl funcgen organisms available on the ftp server.
  #TODO: refactor to run in separate thread from GUI.
  def refreshAvailableOrganisms(self, force=False):
    d = c.GET_ENSEMBL_FUNCGEN_ORGANISMS_DEFAULTS
    if self.dataDir.text():
      availableOrganismsFileName = f'{self.dataDir.text()}/availableOrganisms.txt'
    else:
      availableOrganismsFileName = d['output']
    normalized = os.path.normpath(availableOrganismsFileName)
    self.availableOrganisms = funcgen.parseFtpIndexForOrganisms(
      url=d['url'], output=normalized, dataDir=self.dataDir, force=force
    )
    if self.availableOrganisms:
      orgIndex = self.organism.currentIndex()
      if orgIndex is None or orgIndex < 0:
        defaultOrg = c.GET_ENSEMBL_PROBES_DEFAULTS['organism']
        defaultOrgPos = sorted([key for (key, val) in self.availableOrganisms.items()]).index(defaultOrg)
        orgIndex = defaultOrgPos
      #clean out the default/old items
      self.organism.clear()
      #add the new
      self.organism.addItems(sorted([val for (key, val) in self.availableOrganisms.items()]))
      #set the index to the old one, or to the default
      self.organism.setCurrentIndex(orgIndex)

  def getJobArgs(self):
    jobArgs = ['get_ensembl_probes.py', '--organism', \
        getOrgKeyFromPrettyUnicode(self.organism.currentText(), self.availableOrganisms), \
        '--data-dir', os.path.normpath(self.dataDir.text()), os.path.normpath(self.output.text())]
    return jobArgs

  def getJobType(self):
    return job.GuiJob.PROBE

  def getGuiVars(self):
    return {
        'probeDataDir': os.path.normpath(self.dataDir.text()), 
        'probeOrganism': self.organism.currentText(),
        'probeOrganismKey': getOrgKeyFromPrettyUnicode(self.organism.currentText(), self.availableOrganisms),
        'probeOutput': os.path.normpath(self.output.text())
    }

  def autofill(self, guiVars):
    organism = guiVars['probeOrganism']
    if guiVars['lncrnaOrganism']:
      #setCurrentOption looks for matching string in options so chop off last 
      # bit of organism string e.g. Human (hg38) -> Human
      organism = guiVars['lncrnaOrganism'].split(' ')[0].strip()
    self.organism.setCurrentOption(organism)
    self.dataDir.setText(os.path.normpath(guiVars['probeDataDir']))
    self.output.setText(os.path.normpath(guiVars['probeOutput']))
    #automatically update avail. organisms at launch of expressionlncr
    self.refreshAvailableOrganisms()


class OverlapForm(GuiForm):
  def __init__(self, parent=None, continueCallback=None):
    super(OverlapForm, self).__init__(parent, continueCallback)
    #form title
    layout = qtw.QVBoxLayout()
    title = qtw.QLabel(c.OVERLAP_TITLE)
    subtitle = WrappedLabel(c.OVERLAP_SUBTITLE)
    layout.addWidget(title)
    layout.addWidget(subtitle)
    layout.addStretch()
    #options form
    formLayout = qtw.QFormLayout()
    self.inputA = FileChooser(dialogType=c.OPEN_DIALOG_TYPE, fileTypes=c.BED_FILE_TYPE)
    self.inputB = FileChooser(dialogType=c.OPEN_DIALOG_TYPE, fileTypes=c.BED_FILE_TYPE)
    self.outputA = FileChooser(dialogType=c.SAVE_DIALOG_TYPE, fileTypes=c.BED_FILE_TYPE)
    self.outputB = FileChooser(dialogType=c.SAVE_DIALOG_TYPE, fileTypes=c.BED_FILE_TYPE)
    self.outputXml = FileChooser(dialogType=c.SAVE_DIALOG_TYPE, fileTypes=c.XML_FILE_TYPE)
    formLayout.addRow(c.OVERLAP_INPUT_A_MSG, self.inputA)
    formLayout.addRow(c.OVERLAP_INPUT_B_MSG, self.inputB)
    formLayout.addRow(c.OVERLAP_OUTPUT_A_MSG, self.outputA)
    formLayout.addRow(c.OVERLAP_OUTPUT_B_MSG, self.outputB)
    formLayout.addRow(c.OVERLAP_OUTPUT_XML_MSG, self.outputXml)
    #run button
    runLayout = qtw.QHBoxLayout()
    runLayout.addStretch()
    self.runButton = qtw.QPushButton(c.OVERLAP_RUN_BUTTON_MSG)
    self.runButton.clicked.connect(self.onRunButton)
    runLayout.addWidget(self.runButton)
    #add layouts to main layout
    layout.addLayout(formLayout)
    layout.addStretch()
    layout.addLayout(runLayout)
    self.setLayout(layout)

  def getJobArgs(self):
    jobArgs = ['find_overlap.py', '-a', os.path.normpath(self.inputA.text()),
        '-b', os.path.normpath(self.inputB.text()), \
        '-A', os.path.normpath(self.outputA.text()), \
        '-B', os.path.normpath(self.outputB.text()), \
        os.path.normpath(self.outputXml.text())]
    return jobArgs

  def getJobType(self):
    return job.GuiJob.OVERLAP

  def getGuiVars(self):
    return {
        'overlapInputA': self.inputA.text(),
        'overlapInputB': self.inputB.text(),
        'overlapOutputA': self.outputA.text(),
        'overlapOutputB': self.outputB.text(),
        'overlapOutputXml': self.outputXml.text()
    }

  def autofill(self, guiVars):
    #strip the basename off default file overlapOutputA and use that as 
    # default directory for output
    dataDir = os.path.normpath('/'.join(re.split('/+', guiVars['overlapOutputA'])[:-1]))
    if guiVars['probeDataDir']:
      dataDir = os.path.normpath(guiVars['probeDataDir'])
    #construct input and output file name defaults intelligently.
    # use previous form values if present else use defaults.
    inputA = os.path.normpath(guiVars['overlapInputA'])
    outputA = os.path.normpath(guiVars['overlapOutputA'])
    inputB = os.path.normpath(guiVars['overlapInputB'])
    outputB = os.path.normpath(guiVars['overlapOutputB'])
    if guiVars['probeOutput']:
      inputA = os.path.normpath(guiVars['probeOutput'])
      outputA = os.path.normpath('%s/%s.overlap.bed' % (dataDir, inputA.split('/')[-1].split('.bed')[0]))
    if guiVars['lncrnaOutput']:
      inputB = os.path.normpath(guiVars['lncrnaOutput'])
      outputB = os.path.normpath('%s/%s.overlap.bed' % (dataDir, inputB.split('/')[-1].split('.bed')[0]))
    outputXml = os.path.normpath('%s/%s' % (dataDir, guiVars['overlapOutputXml'].split('/')[-1]))
    self.inputA.setText(inputA)
    self.inputB.setText(inputB)
    self.outputA.setText(outputA)
    self.outputB.setText(outputB)
    self.outputXml.setText(outputXml)


class ExpressionForm(GuiForm):
  def __init__(self, parent=None, continueCallback=None):
    super(ExpressionForm, self).__init__(parent, continueCallback)
    #form title
    layout = qtw.QVBoxLayout()
    title = qtw.QLabel(c.EXPRESSION_TITLE)
    subtitle = WrappedLabel(c.EXPRESSION_SUBTITLE)
    layout.addWidget(title)
    layout.addWidget(subtitle)
    layout.addStretch()
    #options form
    optionsLayout = qtw.QFormLayout()
    self.inputF = FileChooser(dialogType=c.OPEN_DIALOG_TYPE, fileTypes=c.BED_FILE_TYPE)
    self.outDir = FileChooser(dialogType=c.DIRECTORY_OPEN_DIALOG_TYPE)
    optionsLayout.addRow(c.EXPRESSION_INPUT_F_MSG, self.inputF)
    optionsLayout.addRow(c.EXPRESSION_OUTDIR_MSG, self.outDir)
    #search form
    searchLayout = qtw.QFormLayout()
    self.organism = ComboBox()
    self.organism.addItems(sorted(org.ORG_NAMES))
    self.searchTerms = qtw.QTextEdit()
    #TODO add default italicised, light grey example for search terms field
    self.searchButton = qtw.QPushButton(c.EXPRESSION_SEARCH_BUTTON_MSG)
    self.searchButton.clicked.connect(self.onSearchButton)
    searchLayout.addRow(c.EXPRESSION_ORGANISM_MSG, self.organism)
    searchLayout.addRow(c.EXPRESSION_SEARCH_TERMS_MSG, self.searchTerms)
    searchLayout.addRow(c.EXPRESSION_SEARCH_BUTTON_ROW_MSG, self.searchButton)
    #search results message and run button form
    runLayout = qtw.QHBoxLayout()
    self.searchResultsMessage = qtw.QLabel(c.EXPRESSION_SEARCH_NO_RESULTS)
    runLayout.addWidget(self.searchResultsMessage)
    runLayout.addStretch()
    self.runButton = qtw.QPushButton(c.EXPRESSION_RUN_BUTTON_MSG)
    self.runButton.clicked.connect(self.onRunButton)
    runLayout.addWidget(self.runButton)
    #add layouts to main layout
    layout.addLayout(optionsLayout)
    layout.addStretch()
    layout.addLayout(searchLayout)
    layout.addStretch()
    layout.addLayout(runLayout)
    self.setLayout(layout)

  @qt.Slot()
  def onSearchButton(self):
    self.jobType = job.GuiJob.EXPRESSION_SEARCH
    print('Setting up job: %s...' % job.GuiJob.typeNames[self.jobType])
    self.jobArgs = self.getSearchJobArgs()
    if not self.jobArgs:
      ErrorMessageBox.show(self, c.ERROR_INVALID_JOB)
    #call a new gui job process
    print('Job args: %s' % (' '.join(self.jobArgs)))
    self.job = job.GuiJob(jobArgs=self.jobArgs)
    self.job.started.connect(self.onJobStarted)
    self.job.finished.connect(self.onJobFinished)
    self.job.errorOccurred.connect(self.onJobError)
    self.job.start()

  @qt.Slot()
  def onJobStarted(self):
    self.setCursor(qtg.QCursor(qt.Qt.CursorShape.WaitCursor))
    self.searchButton.setDisabled(True)
    self.runButton.setDisabled(True)

  @qt.Slot()
  def onJobFinished(self):
    if self.jobType == job.GuiJob.EXPRESSION_SEARCH:
      #change the search results label to give user feedback.
      if ' '.join(self.getSearchJobArgs()).index('--skip-series-info'):
        seriesFile = os.path.normpath('%s/%s' % (self.outDir.text(), c.EXPRESSION_DEFAULT_SERIES_OUTPUT))
        print(f'Opening series file {seriesFile} ...')
        with open(seriesFile, 'r') as f:
          numSeries = len(f.readlines())
        text = f'Skipped downloading GEO series summary info for {numSeries} series.'
      else:
        #open the series matrix info file and count up the rows.
        numLines = 0
        fileSizeSum = 0
        prettySum = 'N/A'
        infoFile = os.path.normpath('%s/%s' % (self.outDir.text(), c.EXPRESSION_DEFAULT_INFO_OUTPUT))
        print(f'Opening expression series summary info file {infoFile} ...')
        with open(infoFile, 'r') as f:
          reader = csv.reader(f, delimiter='\t')
          for cols in reader:
            try:
              if len(cols) > 1:
                fileSizeSum += int(cols[1])
                numLines += 1
            except Exception:
              continue
        if fileSizeSum > 0:
          prettySum = getHumanReadableSize(fileSizeSum)
        if numLines > 0 and prettySum:
          text = 'Found %s series totalling %s.' % (numLines, prettySum)
        else:
          text = 'No GEO series summary info found.'
      print(text)
      self.searchResultsMessage.setText(text)
      self.searchButton.setEnabled(False)
      self.runButton.setEnabled(True)
      self.unsetCursor()
    else:  #job.GuiJob.EXPRESSION
      self.searchButton.setEnabled(True)
      self.runButton.setEnabled(False)
      self.unsetCursor()
      #only advance forward if run job was called
      self.continueCallback()

  def getSearchJobArgs(self):
    seriesOutput = c.EXPRESSION_DEFAULT_SERIES_OUTPUT
    infoOutput = c.EXPRESSION_DEFAULT_INFO_OUTPUT
    if not self.dataDir:
      self.dataDir = os.path.normpath(c.GET_ENSEMBL_PROBES_DEFAULTS['dataDir'])
    jobArgs = [
      'find_geo_dataseries.py', \
      '--organism', org.nameToKey(self.organism.currentText()), \
      '--data-dir', self.dataDir, \
      '--esearch', os.path.normpath('%s/%s.esearch' % (self.outDir.text(), infoOutput)), \
      '--esummary', os.path.normpath('%s/%s.esummary' % (self.outDir.text(), infoOutput)), \
      '--get-platforms-from-overlap', os.path.normpath(self.inputF.text()), \
      '--series-output', os.path.normpath('%s/%s' % (self.outDir.text(), seriesOutput)), \
      '--info-output', os.path.normpath('%s/%s' % (self.outDir.text(), infoOutput)), \
      '--skip-series-info'
    ]
    #only pass search terms if not empty
    terms = self.searchTerms.toPlainText().encode('utf8').strip()
    if terms and terms != '':
      jobArgs.append('--search-terms')
      jobArgs.append(self.searchTerms.toPlainText())
    return jobArgs

  def getJobArgs(self):
    seriesOutput = c.EXPRESSION_DEFAULT_SERIES_OUTPUT
    jobArgs = ['get_geo_dataseries.py', '-i', \
        os.path.normpath('%s/%s' % (self.outDir.text(), seriesOutput)), \
        '-o', os.path.normpath(self.outDir.text())]
    return jobArgs

  def getJobType(self):
    return job.GuiJob.EXPRESSION

  #don't technically have to define every var since only an .update() is called on the map.
  #note missing expressionDataDir here, which is not actually user-settable.
  def getGuiVars(self):
    return {
        'expressionOrganism': self.organism.currentText(),
        'expressionInputF': os.path.normpath(self.inputF.text()),
        'expressionOutDir': os.path.normpath(self.outDir.text()),
        'expressionSearchTerms': self.searchTerms.toPlainText()
    }

  def autofill(self, guiVars):
    #defaults from scripts
    inputF = os.path.normpath(guiVars['expressionInputF'])
    outDir = os.path.normpath(guiVars['expressionOutDir'])
    organism = guiVars['expressionOrganism']
    dataDir = os.path.normpath(guiVars['expressionDataDir'])
    searchTerms = guiVars['expressionSearchTerms']
    #now try to intelligently set based on previous gui forms
    if guiVars['overlapOutputA']:
      #output A should be the expression probe bed file
      inputF = os.path.normpath(guiVars['overlapOutputA'])
    if guiVars['probeDataDir']:
      dataDir = os.path.normpath(guiVars['probeDataDir'])
      outDir = os.path.normpath('%s/matrices' % guiVars['probeDataDir'])
    if guiVars['probeOrganism']:
      # setCurrentOption matches on sub strings so just take first two words
      organism = ' '.join(guiVars['probeOrganism'].split(' ')[:2])
    self.inputF.setText(inputF)
    self.organism.setCurrentOption(organism)
    self.outDir.setText(outDir)
    self.searchTerms.setText(searchTerms)
    #note dataDir is hidden non-user changeable field
    self.dataDir = dataDir


class ResultsForm(GuiForm):
  def __init__(self, parent=None, continueCallback=None):
    super(ResultsForm, self).__init__(parent, continueCallback)
    #form title
    layout = qtw.QVBoxLayout()
    title = qtw.QLabel(c.RESULTS_TITLE)
    subtitle = WrappedLabel(c.RESULTS_SUBTITLE)
    layout.addWidget(title)
    layout.addWidget(subtitle)
    layout.addStretch()
    #options form
    formLayout = qtw.QFormLayout()
    self.dataDir = FileChooser(dialogType=c.DIRECTORY_OPEN_DIALOG_TYPE)
    self.outDir = FileChooser(dialogType=c.DIRECTORY_OPEN_DIALOG_TYPE)
    self.overlapFile = FileChooser(dialogType=c.OPEN_DIALOG_TYPE, fileTypes=c.XML_FILE_TYPE)
    formLayout.addRow(c.RESULTS_DATADIR_MSG, self.dataDir)
    formLayout.addRow(c.RESULTS_OVERLAP_FILE_MSG, self.overlapFile)
    formLayout.addRow(c.RESULTS_OUTPUT_DIR_MSG, self.outDir)
    #run button
    runLayout = qtw.QHBoxLayout()
    runLayout.addStretch()
    self.runButton = qtw.QPushButton(c.LNCRNA_RUN_BUTTON_MSG)
    self.runButton.clicked.connect(self.onRunButton)
    runLayout.addWidget(self.runButton)
    #add layouts to main layout
    layout.addLayout(formLayout)
    layout.addStretch()
    layout.addLayout(runLayout)
    self.setLayout(layout)

  def getJobArgs(self):
    if not self.lncrnaFile:
      self.lncrnaFile = os.path.normpath(c.GET_LNCRNA_DEFAULTS['output'])
    # Here, organism is the Ensembl funcgen "homo_sapiens_funcgen"-like name,
    #  not any prettified version.
    if not self.organism:
      self.organism = c.GET_ENSEMBL_PROBES_DEFAULTS['organism']
    jobArgs = ['parse_geo_dataseries.py', \
      '--data-dir', os.path.normpath(self.dataDir.text()), \
      '--out-dir', os.path.normpath(self.outDir.text()), \
      '--overlap-file', os.path.normpath(self.overlapFile.text()), \
      '--lncrna-file', os.path.normpath(self.lncrnaFile), \
      '--organism', self.organism]
    return jobArgs

  def getJobType(self):
    return job.GuiJob.RESULTS

  def getGuiVars(self):
    return {
        'resultsDataDir': os.path.normpath(self.dataDir.text()),
        'resultsOutDir': os.path.normpath(self.outDir.text()),
        'resultsOverlapFile': os.path.normpath(self.overlapFile.text())
    }

  def autofill(self, guiVars):
    #script defaults
    dataDir = os.path.normpath(guiVars['resultsDataDir'])
    outDir = os.path.normpath(guiVars['resultsOutDir'])
    overlapFile = os.path.normpath(guiVars['resultsOverlapFile'])
    self.lncrnaFile = os.path.normpath(guiVars['lncrnaOutput'])
    #try to intelligently set
    if guiVars['expressionOutDir']:
      dataDir = os.path.normpath(guiVars['expressionOutDir'])
    if guiVars['expressionDataDir']:
      outDir = os.path.normpath('%s/results' % guiVars['expressionDataDir'])
    if guiVars['overlapOutputXml']:
      overlapFile = os.path.normpath(guiVars['overlapOutputXml'])
    self.dataDir.setText(dataDir)
    self.outDir.setText(outDir)
    self.overlapFile.setText(overlapFile)
    self.organism = guiVars['probeOrganismKey']


#navigation footer form with next/prev buttons to navigate through all the gui actions.
#NOTE: currently using a tabbed widget instead.
class NavigationForm(qtw.QWidget):
  def __init__(self, parent=None):
    super(NavigationForm, self).__init__(parent)
    #main layout for form and separate layout for buttons
    layout = qtw.QVBoxLayout()
    buttonBox = qtw.QHBoxLayout()
    #create next and prev button and add to button layout
    prevButton = qtw.QPushButton(c.NAV_PREV_BUTTON_MSG)
    nextButton = qtw.QPushButton(c.NAV_NEXT_BUTTON_MSG)
    buttonBox.addWidget(prevButton)
    buttonBox.addStretch()
    buttonBox.addWidget(nextButton)
    #add action listeners to buttons
    prevButton.clicked.connect(self.onNextButton)
    nextButton.clicked.connect(self.onPrevButton)
    #add horizontal rule above buttons
    rule = HorizontalRule()
    layout.addWidget(rule)
    layout.addLayout(buttonBox)
    #set layout
    self.setLayout(layout)

  @qt.Slot()
  def onNextButton(self):
    print('next clicked')
    pass

  @qt.Slot()
  def onPrevButton(self):
    print('prev clicked')
    pass
