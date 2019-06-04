# P300
A tool for teaching P300 by showing the ongoing averaging process and continuous classification. The main purpose 
of this tool is to visually show how the averaging in in a P300 paradigm works.

## Packages
It is split up into three packages, one presenting a P300 speller,one analysing the output of the speller and 
incoming EEG to perform classification and the third providing a testserver in case no amplifier equipment is present 
for testing. Connections are made via the [LSL](https://github.com/sccn/labstreaminglayer) 
interface. Technically, this package supports all EEG recorders capable of streaming to LSL, however, at the moment 
it is optimized to work with [eego sports](https://www.ant-neuro.com/products/eego_sports) by ANT neuro. If the 
amplifier is changed, one wants to make sure the correct reference is chosen. As the ANT neuro has an intenal
reference subtraction this is not necessary, but can easily be activated for other amplifiers changing the two 
indicated lines in analyzer.data.RecordsData (lines are commented at the moment).

## Getting started
The simplest way to start one of the packages is to use the start_[package_name] script. The setup should work out 
of the box, however, one needs to know the number of the electrode (in the LSL stream) that should be observed. 
Watch out, indexing for the electrodes starts at 0. 


## Questions and Issues
If there are any questions or you run into an issue, please file a 'Issue' at the top.

## Contributing
If you want to contribute, please file also file an issue first where the new feature can be discussed, in general
contribution is welcome!

# Acknowledgement
This tool was developed by myself as part of a project done at the 
[Institute of Neural Engineering](https://www.tugraz.at/institutes/ine/home/).
The work was supervised by Assoc.Prof. Dipl.-Ing. Dr.techn. Reinhold Scherer.
