	
INCLUDE_PATH := /Users/dy/gits/cc/include
SOLVER := sol.cpp
COMP := cmp.cpp
solver:
	find ${SOLVER}
	cc -std=c++2b -I${INCLUDE_PATH} -g -Wall -Wfatal-errors -DDEBUG -fsanitize=address -fsanitize=undefined -o sol ${SOLVER}
	
cmp:
	find ${COMP}
	cc -std=c++2b -I${INCLUDE_PATH} -g -Wall -Wfatal-errors -DDEBUG -fsanitize=address -fsanitize=undefined -o cmp ${COMP}

gen:
	find gen.py

test: solver
	python3.11 testsync.py -T sol in*
	
run:
	./sol

compare: solver gen cmp
	python3.11 testsync.py -C "./sol" "python3.11 gen.py" "./cmp"

bruteforce: solver gen
	echo

check: solver cmp
	python3.11 testsync.py -I "./sol" "./cmp"

archive:
	echo

task:
	echo

listen:
	echo