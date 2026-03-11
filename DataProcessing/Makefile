# Include shared tools build fragment
include tools/Makefile.inc

# Compiler
CXX = g++

# ROOT Flags
ROOTCFLAGS  = $(shell root-config --cflags)
ROOTLIBS    = $(shell root-config --libs)

# Compilation Flags
CXXFLAGS = -Wall -Wextra -O2 -std=c++17 -I./include $(TOOLS_CXXFLAGS) $(ROOTCFLAGS)
LDFLAGS  = $(ROOTLIBS)

# Target Executable
TARGET = bin/Analyze.exe
SRC = src/Analyze.cxx

# Build Rule
all: $(TARGET)

$(TARGET): $(SRC) include/thrustCompute.h
	@mkdir -p bin
	$(CXX) $(CXXFLAGS) $(SRC) -o $@ $(LDFLAGS)

# Clean Rule
clean:
	rm -f $(TARGET)
