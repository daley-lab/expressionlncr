#!/usr/bin/env python2
#
#GUI wrapper for lncrna python scripts using PySide Qt bindings.
#


import signal
import sys

from PySide.QtCore import *
from PySide.QtGui import *

from forms import *
from gui_job import *
import constants as c


class App(QWidget):
  def __init__(self):
    super(App, self).__init__()
    self.initUI()

  def initUI(self):
    #application min size and title
    self.setMinimumSize(QSize(c.APP_MIN_WIDTH, c.APP_MIN_HEIGHT))
    self.setWindowTitle(c.APP_TITLE)
    #add a layout and a tab widget to hold all the forms
    layout = QVBoxLayout()
    tabs = QTabWidget(self)
    #add all the tabs to the tab widget
    greeterForm = GreeterForm(parent=tabs, continueCallback=self.onContinueButton)
    lncrnaForm = LncrnaForm(tabs, continueCallback=self.onContinueButton)
    probeForm = ProbeForm(tabs, continueCallback=self.onContinueButton)
    overlapForm = OverlapForm(tabs, continueCallback=self.onContinueButton)
    expressionForm = ExpressionForm(tabs, continueCallback=self.onContinueButton)
    resultsForm = ResultsForm(tabs, continueCallback=self.onContinueButton)
    tabs.addTab(greeterForm, c.GREETER_TAB_LABEL)
    tabs.addTab(lncrnaForm, c.LNCRNA_TAB_LABEL)
    tabs.addTab(probeForm, c.PROBE_TAB_LABEL)
    tabs.addTab(overlapForm, c.OVERLAP_TAB_LABEL)
    tabs.addTab(expressionForm, c.EXPRESSION_TAB_LABEL)
    tabs.addTab(resultsForm, c.RESULTS_TAB_LABEL)
    layout.addWidget(tabs)
    self.setLayout(layout)
    #expose tabs for continue button callback
    self.tabs = tabs
    #load gui default values
    self.guiVars = self.getGuiDefaults()
    #autofill all the forms. need to save state after autofilling since 
    # sometimes autofill intelligently changes settings away from the defaults.
    for form in [greeterForm, lncrnaForm, probeForm, overlapForm, expressionForm, resultsForm]:
      form.autofill(self.guiVars)
      self.guiVars.update(form.getGuiVars())

  def run(self):
    #show app window
    self.show()
    #set up global shortcuts
    self.setupShortcuts()
    #run main process
    qt.exec_()

  def setupShortcuts(self):
    ctrlQ = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Q), self)
    ctrlW = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_W), self)
    ctrlQ.activated.connect(self.onKeyboardQuit)
    ctrlW.activated.connect(self.onKeyboardQuit)

  def getGuiDefaults(self):
    #get the defaults from the constants file
    return {
      'lncrnaSource': c.LNCRNA_SOURCE_ITEMS[c.GET_LNCRNA_DEFAULTS['mode']],
      'lncrnaOrganism': c.LNCRNA_NONCODE_ORGANISMS[c.GET_LNCRNA_DEFAULTS['organism']],
      'lncrnaOutput': c.GET_LNCRNA_DEFAULTS['output'],
      'lncrnaSourceFile': None,
      'probeOrganism': c.PROBE_ENSEMBL_ORGANISMS[c.GET_ENSEMBL_PROBES_DEFAULTS['organism']],
      'probeDataDir': c.GET_ENSEMBL_PROBES_DEFAULTS['dataDir'],
      'probeOutput': c.GET_ENSEMBL_PROBES_DEFAULTS['output'],
      'overlapInputA': c.FIND_OVERLAP_DEFAULTS['inputA'],
      'overlapInputB': c.FIND_OVERLAP_DEFAULTS['inputA'],
      'overlapOutputA': c.FIND_OVERLAP_DEFAULTS['outputA'],
      'overlapOutputB': c.FIND_OVERLAP_DEFAULTS['outputB'],
      'overlapOutputXml': c.FIND_OVERLAP_DEFAULTS['output'],
      'expressionOrganism': c.PROBE_ENSEMBL_ORGANISMS[c.FIND_GEO_DATASERIES_DEFAULTS['organism']],
      'expressionInputF': c.FIND_OVERLAP_DEFAULTS['outputB'],
      'expressionOutDir': c.GET_GEO_DATASERIES_DEFAULTS['output'],
      'expressionSearchTerms': c.FIND_GEO_DATASERIES_DEFAULTS['searchTerms'],
      'expressionDataDir': c.GET_ENSEMBL_PROBES_DEFAULTS['dataDir'],
      'resultsDataDir': c.PARSE_GEO_DATASERIES_DEFAULTS['dataDir'],
      'resultsOutDir': c.PARSE_GEO_DATASERIES_DEFAULTS['outDir'],
      'resultsOverlapFile': c.PARSE_GEO_DATASERIES_DEFAULTS['overlapFile']
    }

  @Slot()
  def onContinueButton(self):
    #save the user-entered gui variables for this form before we transition
    # to the next form
    newGuiVars = self.tabs.currentWidget().getGuiVars()
    self.guiVars.update(newGuiVars)
    #change to the next form if we're not at the last one
    i = self.tabs.currentIndex()
    if i < self.tabs.count() - 1:
      self.tabs.setCurrentIndex(i + 1)
      #autofill the new form variables
      self.tabs.currentWidget().autofill(self.guiVars)

  @Slot()
  def onKeyboardQuit(self):
    if AppMessageBox.question(self, '', c.APP_QUIT_MESSAGE, 
        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
      QCoreApplication.quit()


#create instance of app and run
if __name__ == '__main__':
  #let ctrl-c (or o/s specific interrupt signal) close the application immediately
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  qt = QApplication(sys.argv) 
  app = App()
  sys.exit(app.run())
