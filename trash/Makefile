

SOL = sol.cpp.exe
GEN = gen.py
CMP = cmp.cpp.exe
CHK = chk.cpp.exe

%.cpp.exe: %.cpp $(wildcard include/*)
	# c++ -std=c++2b -g -Wall -Wfatal-errors -DDEBUG -fsanitize=address -fsanitize=undefined -o $@ $<
	c++ -std=c++2b -O3 -Wall -Wfatal-errors -DDEBUG -o $@ $<

# %.java.exe: %.java $(wildcard include/*)
# 	javac -o $@ $<

runsol: $(SOL)
	@/usr/bin/time -al ./$(SOL)

rungen: $(GEN)
	@python3 $(GEN)

runcmp: $(CMP)
	@./$(CMP)

runchk: $(CHK)
	@./$(CHK)

tst: $(SOL) $(wildcard in-*)
	task --runtests

gen: $(SOL) $(GEN)
	task --bruteforce 

cmp: $(SOL) $(GEN) $(CMP)
	task --compare 

chk: $(SOL) $(CHK)
	task --check

copy:
	task --submit | pbcopy

list:
	task --list

new:
	taks --new

clean:
	rm -rf *.dSYM *.exe gv *.zip.* in-*

install:
	pip3 install --break-system-packages -e ./stdtestcl
