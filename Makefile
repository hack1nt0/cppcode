

SOL = sol.cpp.exe
GEN = gen.py
CMP = cmp.cpp.exe
CHK = chk.cpp.exe
VIS = vis.py

%.cpp.exe: %.cpp $(wildcard include/*)
	c++ -std=c++2b -g -Wall -Wfatal-errors -DDEBUG -fsanitize=address -fsanitize=undefined -o $@ $<
	# c++ -std=c++2b -O3 -Wall -Wfatal-errors -DDEBUG -o $@ $<

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

runvis:
	source .venv/bin/activate; python3 $(VIS);

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
	task --new

show:
	task --currenttask

edit:
	code .

clean:
	rm -rf *.dSYM *.exe gv *.zip.* 

install:
	python3 -m venv .venv
	source .venv/bin/activate; pip3 install -e ./stdtestcl; 

gitpush:
	rm -rf *.dSYM *.exe gv *.zip.* 
	task --work 0
	# git remote add origin git@github.com:hack1nt0/cppcode.git
	# git branch -M main
	# convert ipynb to markdown
	source .venv/bin/activate; jupyter nbconvert --to markdown readme.ipynb; 
	git add .
	git commit -m "`date`"
	git push -u origin main
