# Compiler
CXX = g++

# ROOT Flags
ROOTCFLAGS = $(shell root-config --cflags)
ROOTLIBS   = $(shell root-config --libs)

# Compilation Flags
CXXFLAGS = -Wall -Wextra -O2 $(ROOTCFLAGS)

# Target Executable
TARGET = Analyze.exe

# Build Rule
all: $(TARGET)

$(TARGET): Analyze.cxx
	$(CXX) $(CXXFLAGS) $^ -o $@ $(ROOTLIBS)

# Clean Rule
clean:
	rm -f $(TARGET)
