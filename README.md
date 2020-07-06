##  Power modeling of complex designs


### Master thesis 2020, Embla Trasti Bygland


This is a repository containing the implementation of my masters project. The project is mainly implemented in Python.

* **parse\_elab.py** contains the parser for elaborated SystemVerilog and the implementation of the register-levelised structure trees
* **liberty\_data.py** contains the Liberty parser and cell\_library class implementation
* **treat\_structures.py** contains the power model generator

Some extra scripts were also made to process information

* **getModule.sh** goes through larger elaborated or synthesised files and retrieves a chosen top-module and all of its dependencies and stores them in a file.
* **count\_gates.py** counts cells in a synthesised file to compare it to count in elaborated file

The literary review done on different methods for **RTL** power estimation can be found in the file **literature\_review\_RTL\_power\_estimation.pdf**
