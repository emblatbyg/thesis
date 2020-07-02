#!/bin/bash

#input is name of module to extract = $1 ($0 is filename of script)

echo "Looking for module: $1 in elaborated and synthesised file"

FIRSTLINE="module $1" 
echo $FIRSTLINE
if [ "$2" -eq 1 ]
then
	#to remove nordic semiconductor file paths from this file parsepath is now third argument to file instead of being given
	PARSEPATH=$3
	FILENAME="data/$1_elab.v"
elif [ "$2" -eq 2 ] 
then
	#to remove nordic semiconductor file paths from this file parsepath is now third argument to file instead of being given
	PARSEPATH=$3
	FILENAME="data/$1_syn.v"
else
	echo "Specify 1 for elab or 2 for syn as second argument"
	exit -1
fi
PARSEPATH=$3

#go from module declaration to endmodule and put text in textfile NB: DO NOT CONSIDER NESTED MODULE DECLARATIONS
sed -n "/module $1/,/endmodule/p" "$PARSEPATH" > "$FILENAME"

# now we also want to add modules instantiated in top module

#modules to append to file $1 
MODULELIST=$(sed -n "/^\s*\S*\s\S*u_/p" "$FILENAME" | awk '{ print $1 }')
echo "modulelist found by sed regex: $MODULELIST"
echo "$MODULELIST" | sort -u > modules.txt

if [ -z "$(grep '[^[:space:]]' modules.txt)" ] 
then
	echo "Module has no dependencies, quitting..."
	rm modules.txt
	exit -1
fi

while read -r line
do
	#append next level modules to file 
	echo "appending module	$line"
	sed -n "/module $line/,/endmodule/p" $PARSEPATH >> "$FILENAME"

	#need some recursivity because now were not getting deep enough
done < modules.txt

#update modules added to text file
ADDEDMODULES="$1
$MODULELIST"


breakloop=0
loopcount=0
#loop until break
until [ "$breakloop" -eq 1 ]
do
	((loopcount++))
	echo "Depth level:	$loopcount"

	#update module list again
	MODULELIST=$(sed -n "/^\s*\S*\s\S*u_/p" "$FILENAME" | awk '{ print $1 }')
	echo "$ADDEDMODULES" | sort -u > addedmodules.txt
	echo "$MODULELIST" | sort -u > modulelist.txt


	#finding only new modules
	comm -13 addedmodules.txt modulelist.txt > modules.txt
	#echo "using comm"
	#comm -13 addedmodules.txt modulelist.txt
	#echo "new modules "
	#echo modules.txt
	#need to keep parsing elab file until all modules are added to the input module file. then all dependencies are in the file
	while read -r line
	do
		#append next level modules to file 
		echo "appending module	$line"
		sed -n "/module $line/,/endmodule/p" "$PARSEPATH" >> "$FILENAME"
		ADDEDMODULES="$ADDEDMODULES
$line"
		#need some recursivity because now were not getting deep enough
	done < modules.txt
	
	#if compare yields empty list set break to true
	if [ -s modules.txt ] 
	then
		echo "Continuing"
	else 
		breakloop=1 
		echo "No more modules to append. Quitting"
		rm modules.txt addedmodules.txt modulelist.txt
	fi
	

done
