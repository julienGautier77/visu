# Visu


Visu is an user interface library based on pyqtgraph to open and process data image .
It can make plot profile and data measurements analysis on live



<img width="400" alt="screeCapture" src="https://user-images.githubusercontent.com/29065484/108862985-08321480-75f1-11eb-9bf3-315b547b1c25.jpg">

<img width="800" aalt="screeCapture" src="https://user-images.githubusercontent.com/29065484/108864521-8fcc5300-75f2-11eb-914d-6588cb3d1575.jpg">

It can open .spe .SPE, .sif and .TIFF files



    https://github.com/julienGautier77/visu

## Requirements
*   python 3.x
*   Numpy
*   matplotlib
*   scipy
*   PyQt6
*   pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git) 
    * Pip install pyqtgraph
*   qdarkstyle (https://github.com/ColinDuquesnoy/QDarkStyleSheet.git)
    * pip install qdarkstyle
*  sifread.py
    *   https://github.com/lightingghost/sifreader/tree/master/sifreader
*  winspec.py 
    *   https://github.com/antonl/pyWinSpec
    
## Installation
*   from PyPi
    *   pip install git+https://github.com/julienGautier77/visu

## Usage
###  to use as  it:
    import visu
    visu.visual.runVisu()

Or :

    from PyQt6.QtWidgets import QApplication
    import sys
    import qdarkstyle
    import visu
    
    appli = QApplication(sys.argv)   
   
    e = visu.visual.SEE() 
    e.show()
    appli.exec_()
    
  ### To  insert in  a  code
  visu is a  QtWidgets it can be use like  a  widget :  
  from PyQt6.QtWidgets import QApplication,QWidget  
  widgetVisu=visu.visual.SEE()   
  
-----------------------------------------
-----------------------------------------
