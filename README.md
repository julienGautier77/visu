# Visu


Visu is an user interface library based on pyqtgraph to open and process data image .
It can make plot profile and data measurements analysis on live



<img width="918" alt="screeCapture" src="https://user-images.githubusercontent.com/29065484/108862985-08321480-75f1-11eb-9bf3-315b547b1c25.jpg">



It can open .spe .SPE, .sif and .TIFF files



    https://github.com/julienGautier77/visu

## Requirements
*   python 3.x
*   Numpy
*   PyQt5
*   pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git) 
    * pip intall pyqtgraph
*   qdarkstyle (https://github.com/ColinDuquesnoy/QDarkStyleSheet.git)
    * pip install qdarkstyle
*  sifread.py
    *   https://github.com/lightingghost/sifreader/tree/master/sifreader
*  winspec.py 
    *   https://github.com/antonl/pyWinSpec
    
## Installation
*   from PyPi
    *   pip install visu

## Usage
###  to use as  it:
    import visu
    visu.visual2.runVisu()

Or :

    from PyQt5.QtWidgets import QApplication
    import sys
    import qdarkstyle
    import visu
    
    appli = QApplication(sys.argv)   
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = visu.visual2.SEE2() #new style
    #or e = visu.visual.SEE() 
    e.show()
    
  ### To  insert in  a  code
  visu is a  QtWidgets it can be use like  a  widget :  
  from PyQt5.QtWidgets import QApplication,QWidget  
  widgetVisu=visu.visual.SEE()   
  
-----------------------------------------
-----------------------------------------
