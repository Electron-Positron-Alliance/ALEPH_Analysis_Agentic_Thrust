# Compiler
CXX = g++

# ROOT Flags
ROOTCFLAGS  = $(shell root-config --cflags)
ROOTLIBS    = $(shell root-config --libs)

# Compilation Flags
CXXFLAGS = -Wall -Wextra -O2 -std=c++17 -I./include $(ROOTCFLAGS)
LDFLAGS  = $(ROOTLIBS)

# Target Executable
TARGET = bin/Analyze.exe
SRC = src/Analyze.cxx

# Build Rule
all: $(TARGET)

$(TARGET): $(SRC) \
	include/analysisCompute.h \
	include/analysisConfig.h \
	include/analysisEvent.h \
	include/analysisIO.h \
	include/analysisTypes.h \
	include/rivetThrust.h \
	include/sphericityTools.h \
	include/thrustTools.h
	@mkdir -p bin
	$(CXX) $(CXXFLAGS) $(SRC) -o $@ $(LDFLAGS)

# Clean Rule
clean:
	rm -f $(TARGET)
