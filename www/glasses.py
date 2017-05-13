#coding=utf-8
'''
    ▅▅▅▅▅▅▅	       ▅▅▅▅▅▅▅
	█			  █▂▂▂▂█		    █
	█			  █	       █		    █
	█			  █	       █		    █		
	▅▅▅▅▅▅▅	       ▅▅▅▅▅▅▅ 
'''
import time
		
glasses=[ 

		'    xxxxxxxxxxxxxxx        xxxxxxxxxxxxxxx\n',
		'    x             x        x             x\n',
		'    x             xxxxxxxxxx             x\n',
		'    x             x        x             x\n',
		'    xxxxxxxxxxxxxxx        xxxxxxxxxxxxxxx\n'
	   ]
def priGlasses():
	for x in range(len(glasses)):
		for y in range(len(glasses[x])):
			print(glasses[x][y],end="",flush=True)
			time.sleep(0.01)
