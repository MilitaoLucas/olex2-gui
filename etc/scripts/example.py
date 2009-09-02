import olex
import olx
from olexFunctions import OlexFunctions
OV = OlexFunctions()


'''
To run this example script, type spy.example("Hello") in Olex2
'''

def example(text="No Text Provided"):
  print "Example Function is now printing your text: %s" %text

OV.registerFunction(example)
