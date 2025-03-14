CC=c++
CFLAGS1=-std=c++2b -Wl,-stack_size -Wl,0x10000000 -g -Wall -Wfatal-errors -DDEBUG -fsanitize=address -fsanitize=undefined 
CFLAGS2=-std=c++2b -O3 -Wl,-stack_size -Wl,0x10000000 -DDEBUG -Wall -Wfatal-errors -o
SRC=.
BIN=bin

SRCS=$(wildcard $(SRC)/*.cpp)
BINS=$(SRCS:$(SRC)/%.cpp=$(BIN)/%)

test:
	echo $(SRCS)
	echo $(BINS)

all: $(BINS)

$(BIN)/%: $(SRC)/%.cpp
	mkdir -p $(BIN)
	$(CC) $(CFLAGS1) -o $@ $<

clean:
	rm -rf $(BIN)
